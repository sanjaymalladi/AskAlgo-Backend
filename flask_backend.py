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
import google.generativeai as genai

def get_ai_response(user_input, context=None):
    prompt = f"""You are an advanced AI tutor specializing in data structures and algorithms. Your primary method is the Socratic approach, but you're also adaptive to the student's needs. Your goal is to guide students towards understanding and critical thinking.

Context: {context if context else 'No prior context available.'}

User's latest input: '{user_input}'

Follow these guidelines in your response:
1. Briefly acknowledge the user's input.
2. Ask a thought-provoking question related to the topic.
3. If appropriate, provide a real-world analogy to illustrate the concept.
4. Offer a hint or guiding statement to nudge the student in the right direction.
5. If the student seems stuck, break down the problem into smaller steps.
6. Encourage thinking about edge cases or potential issues.
7. If the student has progressed, challenge them with a more advanced question.
8. Maintain a supportive and encouraging tone.
9. If relevant, suggest a small coding exercise to reinforce the concept.
10. End with an open-ended question to continue the dialogue.

Limit your response to 3-4 sentences, focusing on the most relevant points based on the user's input and context.
"""
    
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
