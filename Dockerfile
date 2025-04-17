FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8000
ENV WORKERS=4
ENV LOG_LEVEL=info

# Expose port
EXPOSE ${PORT}

# Run the application
CMD python main.py 