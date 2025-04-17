# AskAlgo Backend

A FastAPI-based backend for AskAlgo, a Socratic method AI tutor for data structures and algorithms using Gemini AI.

## Features

- RESTful API with FastAPI
- Simple JWT-based authentication
- Local JSON file storage for user data and conversations
- Gemini AI integration for generating responses
- Conversation history tracking
- User management
- Production-ready configuration

## Tech Stack

- FastAPI - Modern, high-performance web framework
- Uvicorn - ASGI server implementation
- JWT - Simple and secure token-based authentication
- Google Generative AI - Gemini API integration
- Pydantic - Data validation and settings management
- Docker - Containerization

## Getting Started

### Prerequisites

- Python 3.8+
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

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key

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
| `/token` | POST | Login to get access token | No |
| `/ask` | POST | Ask a question to the AI tutor | Yes |
| `/register` | POST | Register a new user | No |
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