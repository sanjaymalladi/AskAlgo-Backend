# app.py
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
import os
import time
from uuid import uuid4
from google.auth.transport import requests
from google.oauth2 import id_token

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from your frontend origin
CORS(app, resources={r"/*": {"origins": "https://askalgo.vercel.app"}})

# Initialize Firebase Admin SDK
cred = credentials.Certificate('google-service-account.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://askalgo-6ed80-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# Helper function to verify Firebase ID Token
def verify_firebase_token(id_token_str):
    try:
        # Use google-auth library to verify the token
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(id_token_str, request, audience=None)
        
        if id_info['iss'] not in ['https://securetoken.google.com/askalgo-6ed80', 'accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        # ID token is valid. Get the user's UID from the decoded token.
        uid = id_info['sub']
        return uid
    except ValueError as e:
        print(f"Token verification failed: {e}")
        return None

@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    id_token_str = data.get('idToken')

    if id_token_str:
        uid = verify_firebase_token(id_token_str)
        if uid:
            try:
                user = firebase_auth.get_user(uid)
                return jsonify({"uid": uid, "email": user.email}), 200
            except firebase_admin.exceptions.FirebaseError as e:
                return jsonify({"error": f"Firebase error: {str(e)}"}), 500
        else:
            return jsonify({"error": "Invalid ID token"}), 401
    else:
        return jsonify({"error": "ID token is required"}), 400

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name are required"}), 400

    try:
        user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        return jsonify({"uid": user.uid, "email": user.email}), 201
    except firebase_admin.exceptions.FirebaseError as e:
        return jsonify({"error": f"Firebase error: {str(e)}"}), 400

@app.route('/verify_token', methods=['POST'])
def verify_token():
    data = request.json
    id_token_str = data.get('idToken')

    if not id_token_str:
        return jsonify({"error": "ID token is required"}), 400

    uid = verify_firebase_token(id_token_str)
    if uid:
        try:
            user = firebase_auth.get_user(uid)
            return jsonify({"uid": uid, "email": user.email}), 200
        except firebase_admin.exceptions.FirebaseError as e:
            return jsonify({"error": f"Firebase error: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid ID token"}), 401

@app.route('/ask', methods=['POST'])
def ask():
    auth_header = request.headers.get('Authorization', '')
    id_token_str = auth_header.split('Bearer ')[-1]

    if not id_token_str:
        return jsonify({"error": "Authorization token is missing"}), 401

    uid = verify_firebase_token(id_token_str)
    if not uid:
        return jsonify({"error": "Invalid or expired token"}), 401

    data = request.json
    question = data.get('question')
    conversation_id = data.get('conversationId')

    if not question:
        return jsonify({"error": "Question is required"}), 400

    if not conversation_id:
        conversation_id = str(uuid4())

    conversation_ref = db.reference(f'users/{uid}/conversations/{conversation_id}')
    
    try:
        conversation_data = conversation_ref.get() or {"messages": []}
        conversation_data["messages"].append({"role": "user", "content": question})

        ai_response = get_ai_response(question, conversation_data["messages"])
        
        conversation_data["messages"].append({"role": "ai", "content": ai_response})
        conversation_ref.set(conversation_data)
        
        return jsonify({"response": ai_response, "conversationId": conversation_id}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get AI response: {str(e)}"}), 500

@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    auth_header = request.headers.get('Authorization', '')
    id_token_str = auth_header.split('Bearer ')[-1]

    if not id_token_str:
        return jsonify({"error": "Authorization token is missing"}), 401

    uid = verify_firebase_token(id_token_str)
    if not uid:
        return jsonify({"error": "Invalid or expired token"}), 401

    try:
        conversations_ref = db.reference(f'users/{uid}/conversations')
        conversations = conversations_ref.get()
        return jsonify(conversations), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve conversations: {str(e)}"}), 500

def get_ai_response(user_input, conversation_history):
    # TODO: Implement your AI response logic here
    # For now, we'll return a simple response
    return f"AI response to: {user_input}"

if __name__ == '__main__':
    app.run(debug=True)
