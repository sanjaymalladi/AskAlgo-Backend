from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
from uuid import uuid4
import firebase_admin
from firebase_admin import credentials, db, auth
import requests
import json

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Load Firebase configuration from JSON file
with open('auth.json') as config_file:
    firebase_config = json.load(config_file)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
FIREBASE_API_KEY = firebase_config['apiKey']
cred = credentials.Certificate("../google-service-account.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': firebase_config['databaseURL']
})

# Check if the API keys are loaded correctly
if not GOOGLE_API_KEY or not FIREBASE_API_KEY:
    raise ValueError("API keys not found. Please set GOOGLE_API_KEY in .env and ensure Firebase config is correct")

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

def get_ai_response(user_input, conversation_history):
    # AI response generation logic remains the same
    pass

def verify_firebase_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']
    except:
        return None

@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Sign in with email and password
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        sign_in_data = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(auth_url, json=sign_in_data)
        data = response.json()

        if 'idToken' in data:
            return jsonify({"token": data['idToken']})
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            return jsonify({"error": "Email, password, and name are required"}), 400

        # Create user with email and password
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
        sign_up_data = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(auth_url, json=sign_up_data)
        data = response.json()

        if 'idToken' in data:
            # Update user profile with name
            user = auth.get_user_by_email(email)
            auth.update_user(
                user.uid,
                display_name=name
            )
            return jsonify({"token": data['idToken']})
        else:
            return jsonify({"error": "Failed to create user"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/signin/google', methods=['POST'])
def signin_google():
    try:
        data = request.json
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "Google ID token is required"}), 400

        # Verify the Google ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']

        # Create a custom token
        custom_token = auth.create_custom_token(uid)

        return jsonify({"token": custom_token.decode('utf-8')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/signin/github', methods=['POST'])
def signin_github():
    try:
        data = request.json
        access_token = data.get('accessToken')

        if not access_token:
            return jsonify({"error": "GitHub access token is required"}), 400

        # Exchange the GitHub access token for a Firebase custom token
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
        sign_in_data = {
            "postBody": f"access_token={access_token}&providerId=github.com",
            "requestUri": "http://localhost",
            "returnIdpCredential": True,
            "returnSecureToken": True
        }
        response = requests.post(auth_url, json=sign_in_data)
        data = response.json()

        if 'idToken' in data:
            return jsonify({"token": data['idToken']})
        else:
            return jsonify({"error": "Failed to authenticate with GitHub"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/signout', methods=['POST'])
def signout():
    # Firebase doesn't have a server-side sign-out mechanism
    # Client-side token removal is sufficient
    return jsonify({"message": "Signed out successfully"})

@app.route('/ask', methods=['POST'])
def ask():
    # Get the Firebase ID token from the Authorization header
    id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    user_id = verify_firebase_token(id_token)

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    user_input = data.get('question')
    conversation_id = data.get('conversationId')

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    if not conversation_id:
        conversation_id = str(uuid4())

    conversation_ref = db.reference(f'users/{user_id}/conversations/{conversation_id}')
    conversation_data = conversation_ref.get()

    if not conversation_data:
        conversation_data = {"messages": []}

    conversation_data["messages"].append({"role": "user", "content": user_input})

    try:
        ai_response = get_ai_response(user_input, conversation_data["messages"])
        time.sleep(1)  # Simulate AI thinking time
        conversation_data["messages"].append({"role": "ai", "content": ai_response})
        conversation_ref.set(conversation_data)
        return jsonify({"response": ai_response, "conversationId": conversation_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "Welcome to the AI Teaching Assistant."

if __name__ == '__main__':
    app.run(debug=True)
