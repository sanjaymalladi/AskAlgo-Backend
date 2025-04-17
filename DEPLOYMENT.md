# AskAlgo Backend Deployment Guide

This guide explains how to deploy the AskAlgo FastAPI backend in a production environment.

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)
- Firebase project with Realtime Database
- Gemini API key from Google AI Studio

## Environment Variables

Create a `.env` file in the root directory with the following variables:

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

# Deployment Settings
PORT=8000
WORKERS=4
LOG_LEVEL=info
FRONTEND_URL=https://askalgo.vercel.app
```

## Direct Deployment

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   gunicorn -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000 main:app
   ```

## Docker Deployment

1. Build the Docker image:
   ```
   docker build -t askalgo-backend .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 --env-file .env askalgo-backend
   ```

## Cloud Deployment

### Google Cloud Run

1. Build and push your Docker image to Google Container Registry:
   ```
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/askalgo-backend
   ```

2. Deploy to Cloud Run:
   ```
   gcloud run deploy askalgo-backend \
     --image gcr.io/YOUR_PROJECT_ID/askalgo-backend \
     --platform managed \
     --allow-unauthenticated \
     --region us-central1 \
     --set-env-vars="$(cat .env | xargs)"
   ```

### AWS Elastic Beanstalk

1. Initialize Elastic Beanstalk application:
   ```
   eb init -p docker askalgo-backend
   ```

2. Deploy the application:
   ```
   eb create askalgo-production
   ```

## Security Considerations

1. Always use HTTPS in production
2. Store sensitive environment variables securely
3. Set proper CORS settings in the application
4. Implement rate limiting for API endpoints
5. Monitor your application for unusual activity

## Monitoring and Logging

1. Use a logging service like Google Cloud Logging or AWS CloudWatch
2. Consider implementing application performance monitoring (APM)
3. Set up alerts for critical application events

## Scaling

The application is designed to scale horizontally. You can:

1. Increase the number of workers in the gunicorn configuration
2. Use auto-scaling features of your cloud provider
3. Implement load balancing for high-traffic scenarios

## Health Checks

The application provides a `/health` endpoint that can be used for health checks by load balancers and monitoring services.

## Troubleshooting

If you encounter issues:

1. Check the application logs for errors
2. Verify all environment variables are set correctly
3. Ensure your Firebase service account has proper permissions
4. Confirm your Gemini API key is valid 