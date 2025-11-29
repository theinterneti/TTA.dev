#!/bin/bash
set -e

echo "Initializing development environment..."

# Ensure we're in the app directory
cd /app

# Set up pre-commit hooks if applicable
if [ -f .pre-commit-config.yaml ]; then
    echo "Setting up pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi


echo "Development environment initialized successfully!"
