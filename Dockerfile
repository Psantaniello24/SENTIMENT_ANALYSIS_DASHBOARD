FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install pre-built wheels
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-build-isolation tokenizers==0.12.1 && \
    pip install -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PORT=10000
ENV DEBUG=false
ENV SOCKETIO_ASYNC_MODE=threading

# Expose the port
EXPOSE $PORT

# Run the application with Gunicorn
CMD gunicorn -c gunicorn_config.py app:app 