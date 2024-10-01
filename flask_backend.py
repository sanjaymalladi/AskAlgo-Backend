# app.py
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
import os
import time
from uuid import uuid4

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from your frontend origin
CORS(app, resources={r"/*": {"origins": "https://askalgo.vercel.app"}})  # Adjust origin as needed

# Initialize Firebase Admin SDK
cred = credentials.Certificate('google-service-account.json')  # Ensure this file is in the same directory
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://askalgo-6ed80-default-rtdb.asia-southeast1.firebasedatabase.app/'  # Replace with your actual databaseURL
})

# Helper function to verify Firebase ID Token
def verify_firebase_token(id_token):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token['uid']
    except firebase_admin.exceptions.FirebaseError as e:
        print(f"Firebase token verification failed: {e}")
        return None

# Route: Sign in (handles both email/password and OAuth sign-ins)
@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    id_token = data.get('idToken')
    email = data.get('email')
    password = data.get('password')

    if id_token:
        # Handle OAuth sign-in
        uid = verify_firebase_token(id_token)
        if uid:
            user = firebase_auth.get_user(uid)
            return jsonify({"uid": uid, "email": user.email}), 200
        else:
            return jsonify({"error": "Invalid ID token"}), 401
    elif email and password:
        # Handle email/password sign-in
        try:
            # Note: Firebase Admin SDK does not support email/password sign-in.
            # Typically, email/password sign-in is handled on the frontend.
            # For demonstration, we will assume the frontend sends the ID token after signing in.
            return jsonify({"error": "Email/password sign-in is not supported via Admin SDK"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid request parameters"}), 400

# Route: Register (email/password registration)
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
        return jsonify({"error": str(e)}), 400

# Route: Verify Token (for token-based authentication)
@app.route('/verify_token', methods=['POST'])
def verify_token():
    data = request.json
    id_token = data.get('idToken')

    if not id_token:
        return jsonify({"error": "ID token is required"}), 400

    uid = verify_firebase_token(id_token)
    if uid:
        user = firebase_auth.get_user(uid)
        return jsonify({"uid": uid, "email": user.email}), 200
    else:
        return jsonify({"error": "Invalid ID token"}), 401

# Route: Ask (handle AI chat)
@app.route('/ask', methods=['POST'])
def ask():
    auth_header = request.headers.get('Authorization', '')
    id_token = auth_header.split('Bearer ')[-1]

    if not id_token:
        return jsonify({"error": "Authorization token is missing"}), 401

    uid = verify_firebase_token(id_token)
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

        # TODO: Integrate with AI service (e.g., OpenAI, Google GenAI)
        ai_response = get_ai_response(question, conversation_data["messages"])
        time.sleep(1)  # Simulate AI processing time
        
        conversation_data["messages"].append({"role": "ai", "content": ai_response})
        conversation_ref.set(conversation_data)
        
        return jsonify({"response": ai_response, "conversationId": conversation_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route: Get Conversations (retrieve user's past conversations)
@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    auth_header = request.headers.get('Authorization', '')
    id_token = auth_header.split('Bearer ')[-1]

    if not id_token:
        return jsonify({"error": "Authorization token is missing"}), 401

    uid = verify_firebase_token(id_token)
    if not uid:
        return jsonify({"error": "Invalid or expired token"}), 401

    try:
        conversations_ref = db.reference(f'users/{uid}/conversations')
        conversations = conversations_ref.get()
        return jsonify(conversations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Placeholder function for AI response generation
def get_ai_response(user_input, conversation_history):
    # Implement your AI response logic here
    # For demonstration, we'll return a simple echo response
    return f"AI response to: {user_input}"

# Run the Flask app
if __name__ == '__main__':
    # For development purposes only. Use Gunicorn or another WSGI server in production.
    app.run(debug=True)
