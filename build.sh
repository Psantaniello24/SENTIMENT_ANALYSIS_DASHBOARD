#!/bin/bash
set -e

echo "Installing pre-built wheels for tokenizers and transformers..."
pip install --upgrade pip

# Install tokenizers from a pre-built wheel
pip install --no-build-isolation tokenizers==0.12.1

# Install all other dependencies
pip install -r requirements.txt

echo "Installation complete!" 