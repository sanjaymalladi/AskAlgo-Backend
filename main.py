import os
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import uuid4
import google.generativeai as genai
from dotenv import load_dotenv
from functools import lru_cache
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import json

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

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = str(uuid4())
    logger.warning("JWT_SECRET_KEY not set! Using a random key for this session only.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token URL for OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

# User database - In a production app, use a real database
# This is a simple in-memory store for demonstration
USERS_DB_FILE = "users.json"
CONVERSATIONS_DB_FILE = "conversations.json"

# Storage functions
def load_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {str(e)}")
        return {}

def save_json_file(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {str(e)}")

# Load data at startup
USERS_DB = load_json_file(USERS_DB_FILE)
CONVERSATIONS_DB = load_json_file(CONVERSATIONS_DB_FILE)

# Pydantic Models
class Question(BaseModel):
    question: str
    conversationId: Optional[str] = None

class TokenData(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegistration(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    email: str
    hashed_password: str
    user_id: str

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    messages: List[Message] = []

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(email: str):
    if email in USERS_DB:
        user_dict = USERS_DB[email]
        return UserInDB(**user_dict)
    return None

def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(token_data.email)
    if user is None:
        raise credentials_exception
    return user

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
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "I'm sorry, but I couldn't process your request at the moment. Please try again later."

# API Endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    if user_data.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    try:
        user_id = str(uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        USERS_DB[user_data.email] = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "user_id": user_id
        }
        save_json_file(USERS_DB_FILE, USERS_DB)
        
        return {"message": "User created successfully", "uid": user_id}
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )

@app.post("/ask", status_code=status.HTTP_200_OK)
async def ask(question_data: Question, user: UserInDB = Depends(get_current_user)):
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

    # Initialize user conversations if needed
    if user.user_id not in CONVERSATIONS_DB:
        CONVERSATIONS_DB[user.user_id] = {}
    
    if conversation_id not in CONVERSATIONS_DB[user.user_id]:
        CONVERSATIONS_DB[user.user_id][conversation_id] = {"messages": []}
    
    try:
        conversation_data = CONVERSATIONS_DB[user.user_id][conversation_id]
        
        # Add the user's question to the conversation
        conversation_data["messages"].append({"role": "user", "content": question})

        # Extract context from conversation history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_data["messages"]])

        # Get AI response
        ai_response = get_ai_response(question, context)
        
        # Add AI's response to the conversation
        conversation_data["messages"].append({"role": "ai", "content": ai_response})

        # Save the updated conversation
        save_json_file(CONVERSATIONS_DB_FILE, CONVERSATIONS_DB)

        return {"response": ai_response, "conversationId": conversation_id}
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI response: {str(e)}",
        )

@app.get("/conversations", status_code=status.HTTP_200_OK)
async def get_conversations(user: UserInDB = Depends(get_current_user)):
    if user.user_id not in CONVERSATIONS_DB:
        return {"message": "No conversations found"}
    
    return CONVERSATIONS_DB[user.user_id]

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