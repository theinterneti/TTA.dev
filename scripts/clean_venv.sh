#!/bin/bash

# Create archive directory
mkdir -p archive/old_venvs

# Archive any non-standard venv names
[ -d "venv" ] && mv venv archive/old_venvs/
[ -d ".venv_old_backup" ] && mv .venv_old_backup archive/old_venvs/

# Remove existing symlinks if they exist
if [ -L "/app/.venv" ]; then
    rm /app/.venv
fi

if [ -L "/app/tta/.venv" ]; then
    rm /app/tta/.venv
fi

# Move .venv_new to archive if it exists in /app
[ -d "/app/.venv_new" ] && mv /app/.venv_new archive/old_venvs/

# Archive the existing .venv_new in /app/tta if it exists
if [ -d "/app/tta/.venv_new" ]; then
    mv /app/tta/.venv_new archive/old_venvs/tta_venv_new_$(date +%Y%m%d_%H%M%S)
fi

# Create a new .venv in /app if it doesn't exist
if [ ! -d "/app/.venv" ]; then
    echo "Creating new virtual environment in /app/.venv"
    python3 -m venv /app/.venv
fi

# Create a symlink in /app/tta/.venv pointing to /app/.venv
if [ -d "/app/tta" ]; then
    echo "Creating symlink from /app/tta/.venv to /app/.venv"
    ln -sf /app/.venv /app/tta/.venv
fi

echo "Virtual environment structure cleaned and standardized"
echo "Using single .venv across all locations"