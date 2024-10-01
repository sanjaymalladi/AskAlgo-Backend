import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, db
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://askalgo.vercel.app"}})

# Initialize Firebase Admin SDK only if not already initialized
if not firebase_admin._apps:
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
    except Exception as e:
        print(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        raise

def verify_firebase_token(id_token_str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token_str)
        return decoded_token['uid']
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return None

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

def get_ai_response(user_input, conversation_history):
    # TODO: Implement your AI response logic here
    # For now, we'll return a simple response
    return f"AI response to: {user_input}"

# Keep other routes (signin, register, verify_token, get_conversations) as they are

if __name__ == '__main__':
    app.run(debug=True)
