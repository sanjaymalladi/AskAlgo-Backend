import os
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from uuid import uuid4
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AskAlgo API",
    description="API for AskAlgo - Socratic method AI tutor for data structures and algorithms",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "https://askalgo.vercel.app")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
@lru_cache()
def get_gemini_api_key():
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY is not set in the environment variables")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key configuration error"
        )
    return gemini_api_key

def configure_gemini():
    try:
        genai.configure(api_key=get_gemini_api_key())
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure Gemini API"
        )

configure_gemini()

# Initialize Firebase Admin SDK
def init_firebase():
    try:
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
        }
        
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
        })
        
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase initialization error: {str(e)}"
        )

# Initialize Firebase only if not already initialized
if not firebase_admin._apps:
    init_firebase()

# Pydantic Models for request/response validation
class Question(BaseModel):
    question: str
    conversationId: Optional[str] = None

class TokenVerification(BaseModel):
    idToken: str

class UserRegistration(BaseModel):
    email: str
    password: str

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    messages: List[Message] = []

# Authentication dependency
async def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    id_token_str = auth_header.split("Bearer ")[-1]
    
    if not id_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing",
        )

    uid = verify_firebase_token(id_token_str)
    
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    return uid

def verify_firebase_token(id_token_str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token_str)
        return decoded_token['uid']
    except firebase_admin.auth.InvalidIdTokenError:
        logger.warning("Invalid ID token")
        return None
    except firebase_admin.auth.ExpiredIdTokenError:
        logger.warning("Expired ID token")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        return None

def get_ai_response(question: str, context: str) -> str:
    prompt = f"""You are a Socratic method AI tutor. Your job is to ask questions and guide students to learn data structures and algorithms. 
    
Context of the conversation:
{context}

User asked: '{question}'

Respond with a question or guiding comment to help the user learn about data structures and algorithms."""

    try:
        logger.info("Generating AI response using Gemini API")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        logger.info(f"Received response from Gemini: {response.text}")
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "I'm sorry, but I couldn't process your request at the moment. Please try again later."

# API Endpoints
@app.post("/ask", status_code=status.HTTP_200_OK)
async def ask(question_data: Question, user_id: str = Depends(get_current_user)):
    question = question_data.question
    conversation_id = question_data.conversationId

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required",
        )

    # Generate a new conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid4())

    # Get the reference for the user's conversation
    conversation_ref = db.reference(f'users/{user_id}/conversations/{conversation_id}')
    
    try:
        # Fetch conversation data
        conversation_data = conversation_ref.get()
        
        # Handle case where no conversation exists yet
        if conversation_data is None:
            conversation_data = {"messages": []}
        
        # Add the user's question to the conversation history
        conversation_data["messages"].append({"role": "user", "content": question})

        # Extract context from conversation history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_data["messages"]])

        # Get AI response using Gemini
        ai_response = get_ai_response(question, context)
        
        # Add AI's response to the conversation history
        conversation_data["messages"].append({"role": "ai", "content": ai_response})

        # Save the updated conversation data back to Firebase
        conversation_ref.set(conversation_data)

        logger.info(f"AI response generated for user {user_id} in conversation {conversation_id}")
        return {"response": ai_response, "conversationId": conversation_id}
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI response: {str(e)}",
        )

@app.post("/signin", status_code=status.HTTP_200_OK)
async def signin(token_data: TokenVerification):
    uid = verify_firebase_token(token_data.idToken)
    
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    logger.info(f"User {uid} signed in successfully")
    return {"message": "Signin successful"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    try:
        user = firebase_auth.create_user(email=user_data.email, password=user_data.password)
        logger.info(f"User created successfully: {user.uid}")
        return {"message": "User created successfully", "uid": user.uid}
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )

@app.post("/verify_token", status_code=status.HTTP_200_OK)
async def verify_token(token_data: TokenVerification):
    uid = verify_firebase_token(token_data.idToken)
    
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    logger.info(f"Token verified successfully for user {uid}")
    return {"message": "Token verified successfully", "uid": uid}

@app.get("/conversations", status_code=status.HTTP_200_OK)
async def get_conversations(user_id: str = Depends(get_current_user)):
    try:
        conversations_ref = db.reference(f'users/{user_id}/conversations')
        conversations_data = conversations_ref.get()
        
        if conversations_data is None:
            logger.info(f"No conversations found for user {user_id}")
            return {"message": "No conversations found"}
        
        logger.info(f"Conversations fetched for user {user_id}")
        return conversations_data
    except Exception as e:
        logger.error(f"Error fetching conversations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}",
        )

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred"},
    )

# Main entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    log_level = os.environ.get("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=False,
        workers=int(os.environ.get("WORKERS", 1)),
    ) 