#!/bin/sh

# Clone the repository with submodules
git clone --recurse-submodules <repository-url> /app

# Navigate to the app directory
cd /app

# Ensure submodules are updated
git submodule update --init --recursive
