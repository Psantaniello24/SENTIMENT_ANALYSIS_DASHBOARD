#!/bin/bash
# Custom deployment script for Render

echo "Starting deployment process..."

# Upgrade pip
python -m pip install --upgrade pip

# Install tokenizers binary first
echo "Installing tokenizers binary..."
pip install --only-binary=:all: tokenizers==0.12.1

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Deployment setup complete!" 