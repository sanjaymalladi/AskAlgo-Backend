import os
import google.generativeai as genai  # Updated import for Gemini SDK
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
from uuid import uuid4
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://askalgo.vercel.app"}})

# Verify GEMINI_API_KEY is set
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logging.error("GEMINI_API_KEY is not set. Please check your .env file.")
    raise EnvironmentError("GEMINI_API_KEY is not set.")
else:
    logging.info("GEMINI_API_KEY is set.")

# Configure Gemini API once at startup
try:
    genai.configure(api_key=gemini_api_key)
    logging.info("Gemini API configured successfully")
except Exception as e:
    logging.error(f"Failed to configure Gemini API: {str(e)}")
    raise

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
        
        logging.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        raise

init_firebase()

def verify_firebase_token(id_token_str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token_str)
        return decoded_token['uid']
    except firebase_admin.auth.InvalidIdTokenError:
        logging.warning("Invalid ID token")
        return None
    except firebase_admin.auth.ExpiredIdTokenError:
        logging.warning("Expired ID token")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during token verification: {str(e)}")
        return None

@app.route('/ask', methods=['POST'])
def ask():
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        logging.warning("Invalid Authorization header format")
        return jsonify({"error": "Invalid Authorization header format"}), 401

    id_token_str = auth_header.split('Bearer ')[-1]
    
    if not id_token_str:
        logging.warning("Authorization token is missing")
        return jsonify({"error": "Authorization token is missing"}), 401

    uid = verify_firebase_token(id_token_str)
    
    if not uid:
        logging.warning("Invalid or expired token")
        return jsonify({"error": "Invalid or expired token"}), 401

    data = request.json
    question = data.get('question')
    conversation_id = data.get('conversationId')

    if not question:
        logging.warning("Question is required")
        return jsonify({"error": "Question is required"}), 400

    # Generate a new conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid4())

    # Get the reference for the user's conversation
    conversation_ref = db.reference(f'users/{uid}/conversations/{conversation_id}')
    
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

        # Get AI response
        ai_response = get_ai_response(question, context)
        
        # Add AI's response to the conversation history
        conversation_data["messages"].append({"role": "ai", "content": ai_response})

        # Save the updated conversation data back to Firebase
        conversation_ref.set(conversation_data)

        logging.info(f"AI response generated for user {uid} in conversation {conversation_id}")
        return jsonify({"response": ai_response, "conversationId": conversation_id}), 200
    except Exception as e:
        logging.error(f"Error in /ask endpoint: {str(e)}")
        return jsonify({"error": f"Failed to get AI response: {str(e)}"}), 500

def get_ai_response(user_input, context=None):
    # Simplify prompt for debugging
    # For production, you might want to use the detailed prompt as before
    prompt = f"User: {user_input}\nAI:"
    
    try:
        logging.info("Generating AI response using Gemini API")
        # Initialize the Gemini Generative Model
        model = genai.GenerativeModel('gemini-1.5-pro-exp-0827')
        
        # Generate content using the prompt
        response = model.generate_content(prompt)
        logging.info(f"Received response from Gemini: {response.text}")
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error generating AI response: {str(e)}")
        return "I'm sorry, but I couldn't process your request at the moment."

# Other routes (signin, register, verify_token, get_conversations)
@app.route('/signin', methods=['POST'])
def signin():
    id_token_str = request.json.get('idToken')
    uid = verify_firebase_token(id_token_str)
    
    if not uid:
        logging.warning("Signin failed: Invalid or expired token")
        return jsonify({"error": "Invalid or expired token"}), 401
    
    # Additional signin logic can be added here
    logging.info(f"User {uid} signed in successfully")
    return jsonify({"message": "Signin successful"}), 200

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    
    try:
        user = firebase_auth.create_user(email=email, password=password)
        logging.info(f"User created successfully: {user.uid}")
        return jsonify({"message": "User created successfully", "uid": user.uid}), 201
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        return jsonify({"error": "Failed to create user"}), 500

@app.route('/verify_token', methods=['POST'])
def verify_token():
    id_token_str = request.json.get('idToken')
    uid = verify_firebase_token(id_token_str)
    
    if not uid:
        logging.warning("Token verification failed: Invalid or expired token")
        return jsonify({"error": "Invalid or expired token"}), 401
    
    logging.info(f"Token verified successfully for user {uid}")
    return jsonify({"message": "Token verified successfully", "uid": uid}), 200

@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        logging.warning("Invalid Authorization header format for get_conversations")
        return jsonify({"error": "Invalid Authorization header format"}), 401

    id_token_str = auth_header.split('Bearer ')[-1]
    
    if not id_token_str:
        logging.warning("Authorization token is missing for get_conversations")
        return jsonify({"error": "Authorization token is missing"}), 401

    uid = verify_firebase_token(id_token_str)
    
    if not uid:
        logging.warning("Invalid or expired token for get_conversations")
        return jsonify({"error": "Invalid or expired token"}), 401

    try:
        conversations_ref = db.reference(f'users/{uid}/conversations')
        conversations_data = conversations_ref.get()
        
        if conversations_data is None:
            logging.info(f"No conversations found for user {uid}")
            return jsonify({"message": "No conversations found"}), 200
        
        logging.info(f"Conversations fetched for user {uid}")
        return jsonify(conversations_data), 200
    except Exception as e:
        logging.error(f"Error fetching conversations for user {uid}: {str(e)}")
        return jsonify({"error": "Failed to fetch conversations"}), 500

if __name__ == '__main__':
    app.run(debug=True)
