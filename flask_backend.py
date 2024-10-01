import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
import os
from uuid import uuid4

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://askalgo.vercel.app"}})

# Initialize Firebase Admin SDK only if not already initialized
if not firebase_admin._apps:
    try:
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-service-account.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://askalgo-6ed80-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
    except Exception as e:
        print(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        raise

def verify_firebase_token(id_token_str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token_str)
        return decoded_token['uid']
    except firebase_auth.InvalidIdTokenError:
        print("Invalid ID token")
        return None
    except firebase_auth.ExpiredIdTokenError:
        print("Expired ID token")
        return None
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return None

@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    id_token_str = data.get('idToken')

    if not id_token_str:
        return jsonify({"error": "ID token is required"}), 400

    uid = verify_firebase_token(id_token_str)
    if not uid:
        return jsonify({"error": "Invalid ID token"}), 401

    try:
        user = firebase_auth.get_user(uid)
        return jsonify({"uid": uid, "email": user.email}), 200
    except firebase_admin.exceptions.FirebaseError as e:
        return jsonify({"error": f"Firebase error: {str(e)}"}), 500

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
    
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Invalid Authorization header format"}), 401

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

        # Get AI response (dummy function, replace with actual AI logic)
        ai_response = get_ai_response(question, conversation_data["messages"])
        
        # Add AI's response to the conversation history
        conversation_data["messages"].append({"role": "ai", "content": ai_response})

        # Save the updated conversation data back to Firebase
        conversation_ref.set(conversation_data)

        return jsonify({"response": ai_response, "conversationId": conversation_id}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
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
