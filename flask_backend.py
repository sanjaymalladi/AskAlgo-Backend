from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}})

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Check if the API key is loaded correctly
if not GOOGLE_API_KEY:
    raise ValueError("No API key found. Please set GOOGLE_API_KEY in .env")

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# Function to get AI response
def get_ai_response(user_input):
    prompt = f"You are a Socratic method AI tutor. Your job is to ask questions and guide students to learn data structures and algorithms. User asked: '{user_input}'. Respond with a question or guiding comment."
    
    # Call Gemini API
    model = genai.GenerativeModel('gemini-1.5-pro-exp-0827')
    response = model.generate_content(prompt)
    
    return response.text

# API route to get user input and respond with Socratic method question
@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        return '', 204
    
    user_input = request.json.get('question')
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    
    # Get AI-generated question from Gemini
    try:
        ai_response = get_ai_response(user_input)
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Home route (optional)
@app.route('/')
def index():
    return "Welcome to the AI Teaching Assistant."

if __name__ == '__main__':
    # Instead of app.run(debug=True), use this:
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)