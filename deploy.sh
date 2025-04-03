#!/bin/bash
# Custom deployment script for Render

echo "Starting deployment process..."

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies with special handling for tokenizers
echo "Installing dependencies..."
pip install --only-binary=:all: tokenizers
pip install -r requirements.txt

echo "Deployment setup complete!" 