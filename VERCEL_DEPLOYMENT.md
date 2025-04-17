# Deploying AskAlgo Backend to Vercel

This guide provides step-by-step instructions for pushing your AskAlgo backend code to GitHub and deploying it on Vercel.

## 1. Push Repository to GitHub

### Initialize Git Repository (if not already done)
```bash
git init
```

### Add all files to the repository
```bash
git add .
```

### Commit the changes
```bash
git commit -m "FastAPI backend implementation for AskAlgo"
```

### Create a new repository on GitHub
1. Go to [GitHub](https://github.com/)
2. Click on "New repository"
3. Name your repository (e.g., "askalgo-backend")
4. Choose visibility (public or private)
5. Click "Create repository"

### Link local repository to GitHub
```bash
git remote add origin https://github.com/YOUR-USERNAME/askalgo-backend.git
```

### Push code to GitHub
```bash
git push -u origin main
```
Note: If your default branch is called `master` instead of `main`, use `master` in the command.

## 2. Deploy to Vercel

### Prerequisites
- A Vercel account (sign up at [vercel.com](https://vercel.com))
- The GitHub repository with your AskAlgo backend code

### Deployment Steps

1. **Log in to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Log in with your account

2. **Import Project**
   - Click "Add New" → "Project"
   - Select your GitHub repository (askalgo-backend)
   - Click "Import"

3. **Configure Project**
   - In the configuration page:
     - **Framework Preset**: Select "Other"
     - **Build and Output Settings**: Leave defaults
     - **Root Directory**: ./
     - **Install Command**: `pip install -r requirements-vercel.txt`

4. **Environment Variables**
   - Add the following environment variables from your .env file:
     - `GEMINI_API_KEY`
     - `FIREBASE_TYPE`
     - `FIREBASE_PROJECT_ID`
     - `FIREBASE_PRIVATE_KEY_ID`
     - `FIREBASE_PRIVATE_KEY` (make sure to add with quotes as it contains newlines)
     - `FIREBASE_CLIENT_EMAIL`
     - `FIREBASE_CLIENT_ID`
     - `FIREBASE_AUTH_URI`
     - `FIREBASE_TOKEN_URI`
     - `FIREBASE_AUTH_PROVIDER_X509_CERT_URL`
     - `FIREBASE_CLIENT_X509_CERT_URL`
     - `FIREBASE_UNIVERSE_DOMAIN`
     - `FIREBASE_DATABASE_URL`
     - `FRONTEND_URL`

5. **Deploy**
   - Click "Deploy"
   - Wait for the deployment to complete

6. **Verify Deployment**
   - Once deployment is complete, Vercel will provide a URL to your application
   - Test the API endpoints using the provided URL
   - Visit `https://your-deployment-url/docs` to access the FastAPI documentation

## 3. Setting Up Custom Domain (Optional)

1. In your Vercel dashboard, select your AskAlgo backend project
2. Go to "Settings" → "Domains"
3. Add your custom domain and follow the verification instructions

## 4. Continuous Deployment

Vercel automatically sets up continuous deployment from your GitHub repository:
- Any push to the main branch will trigger a new deployment
- You can configure preview deployments for pull requests in the Vercel project settings

## 5. Monitoring and Logs

1. Access deployment logs from your Vercel dashboard
2. Go to your project → "Deployments" → select a deployment → "View Logs"
3. Use the "Functions" tab to see serverless function metrics and logs

## Troubleshooting

### Common Issues

1. **Deployment Fails**:
   - Check if all environment variables are correctly set
   - Verify your `vercel.json` configuration is correct
   - Look at build logs for specific errors

2. **Runtime Errors**:
   - Check function logs in the Vercel dashboard
   - Ensure Firebase credentials are correct
   - Verify Gemini API key is valid

3. **CORS Issues**:
   - Make sure FRONTEND_URL is properly set in environment variables
   - Check CORS middleware configuration in your FastAPI application

4. **Cold Start Latency**:
   - Serverless functions on Vercel may experience cold starts, which can cause initial request latency
   - Consider upgrading to a paid plan for improved performance

### Keeping Secrets Secure

- Never commit `.env` files to your repository
- Always use Vercel's environment variables feature for secrets
- Consider using Vercel's integration with secret management services for production 