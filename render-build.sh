#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip
python -m pip install --upgrade pip

# Try to install tokenizers binary first
pip install --only-binary=:all: tokenizers==0.12.1 || {
  echo "Binary tokenizers installation failed, will try to build from source"
  # If binary installation fails, ensure we have cargo/rust
  if ! command -v cargo &> /dev/null; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
  fi
}

# Install dependencies
pip install -r requirements.txt

echo "Build completed successfully!" 