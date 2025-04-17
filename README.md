# AskAlgo Backend

A FastAPI-based backend for AskAlgo, a Socratic method AI tutor for data structures and algorithms using Gemini AI.

## Features

- RESTful API with FastAPI
- Firebase authentication and database integration
- Gemini AI integration for generating responses
- Conversation history tracking
- User management
- Production-ready configuration

## Tech Stack

- FastAPI - Modern, high-performance web framework
- Uvicorn - ASGI server implementation
- Firebase Admin SDK - Authentication and database management
- Google Generative AI - Gemini API integration
- Pydantic - Data validation and settings management
- Docker - Containerization

## Getting Started

### Prerequisites

- Python 3.8+
- Firebase project with Realtime Database
- Gemini API key

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with required environment variables (see [Environment Variables](#environment-variables) section)
5. Run the application:
   ```
   python main.py
   ```

### Environment Variables

Create a `.env` file in the root directory with:

```
# API Keys
GEMINI_API_KEY=your-gemini-api-key

# Firebase Configuration
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-firebase-private-key-id
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email
FIREBASE_CLIENT_ID=your-firebase-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=your-firebase-client-cert-url
FIREBASE_UNIVERSE_DOMAIN=googleapis.com
FIREBASE_DATABASE_URL=https://your-firebase-project-id.firebaseio.com

# Frontend URL (for CORS)
FRONTEND_URL=https://askalgo.vercel.app
```

## API Documentation

When running the application, FastAPI automatically generates interactive API documentation available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

| Endpoint | Method | Description | Authentication Required |
|----------|--------|-------------|------------------------|
| `/ask` | POST | Ask a question to the AI tutor | Yes |
| `/signin` | POST | Verify firebase token for signin | No |
| `/register` | POST | Register a new user | No |
| `/verify_token` | POST | Verify a firebase token | No |
| `/conversations` | GET | Get user's conversation history | Yes |
| `/health` | GET | Health check endpoint | No |

## Development

For development mode with auto-reload:

```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.