#!/usr/bin/env bash
#
# TTA.dev Secrets Management Setup Script
#
# This script sets up centralized secrets management across all agent workspaces
# (GitHub Copilot, Augment, Cline)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}TTA.dev Secrets Management Setup${NC}"
echo "=================================="
echo ""

# Step 1: Check if centralized .env exists
if [ ! -f "$HOME/.env.tta-dev" ]; then
    echo -e "${YELLOW}⚠️  Centralized .env not found at ~/.env.tta-dev${NC}"
    
    if [ -f "/home/thein/recovered-tta-storytelling/.env" ]; then
        echo "Found .env at /home/thein/recovered-tta-storytelling/.env"
        read -p "Copy to ~/.env.tta-dev? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp /home/thein/recovered-tta-storytelling/.env "$HOME/.env.tta-dev"
            echo -e "${GREEN}✅ Copied .env to ~/.env.tta-dev${NC}"
        else
            echo -e "${RED}❌ Aborted. Please create ~/.env.tta-dev manually${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Source .env not found. Please create ~/.env.tta-dev manually${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Centralized .env found at ~/.env.tta-dev${NC}"
fi

# Step 2: Set up workspace symlinks
WORKSPACES=(
    "$HOME/repos/TTA.dev-copilot"
    "$HOME/repos/TTA.dev-copilot/.augment"
    "$HOME/repos/TTA.dev-copilot/.cline"
)

echo ""
echo "Setting up workspace .env symlinks..."
echo ""

for workspace in "${WORKSPACES[@]}"; do
    if [ -d "$workspace" ]; then
        env_link="$workspace/.env"
        
        # Check if .env already exists
        if [ -L "$env_link" ]; then
            # It's a symlink
            target=$(readlink "$env_link")
            if [ "$target" = "$HOME/.env.tta-dev" ]; then
                echo -e "${GREEN}✅ $workspace/.env${NC} → already linked correctly"
            else
                echo -e "${YELLOW}⚠️  $workspace/.env${NC} → points to wrong target ($target)"
                read -p "Update to ~/.env.tta-dev? (y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm "$env_link"
                    ln -s "$HOME/.env.tta-dev" "$env_link"
                    echo -e "${GREEN}✅ Updated symlink${NC}"
                fi
            fi
        elif [ -f "$env_link" ]; then
            # It's a real file
            echo -e "${YELLOW}⚠️  $workspace/.env${NC} → is a real file (not symlink)"
            read -p "Replace with symlink to ~/.env.tta-dev? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                # Backup existing file
                cp "$env_link" "$env_link.backup"
                echo "  → Backed up to .env.backup"
                rm "$env_link"
                ln -s "$HOME/.env.tta-dev" "$env_link"
                echo -e "${GREEN}✅ Created symlink${NC}"
            fi
        else
            # Doesn't exist
            ln -s "$HOME/.env.tta-dev" "$env_link"
            echo -e "${GREEN}✅ $workspace/.env${NC} → created symlink"
        fi
    else
        echo -e "${YELLOW}⚠️  Workspace not found: $workspace${NC}"
    fi
done

# Step 3: Verify setup
echo ""
echo "Verifying setup..."
echo ""

# Test Python import
if command -v python3 &> /dev/null; then
    cd "$HOME/repos/TTA.dev-copilot"
    if python3 -c "from tta_secrets import EnvLoader; print(f'✅ EnvLoader can load from: {EnvLoader.get(\"ENVIRONMENT\", \"not-set\")}')" 2>/dev/null; then
        echo -e "${GREEN}✅ Python tta_secrets package working${NC}"
    else
        echo -e "${YELLOW}⚠️  tta_secrets import failed (may need: uv sync)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Python3 not found, skipping import test${NC}"
fi

# Step 4: Create .gitignore entries
echo ""
echo "Ensuring .gitignore entries..."
echo ""

GITIGNORE_ENTRIES=(
    ".env"
    ".env.local"
    ".env.*.local"
    ".env.backup"
)

for workspace in "${WORKSPACES[@]}"; do
    if [ -d "$workspace" ]; then
        gitignore="$workspace/.gitignore"
        
        # Create .gitignore if it doesn't exist
        if [ ! -f "$gitignore" ]; then
            touch "$gitignore"
        fi
        
        # Add entries if missing
        for entry in "${GITIGNORE_ENTRIES[@]}"; do
            if ! grep -qxF "$entry" "$gitignore" 2>/dev/null; then
                echo "$entry" >> "$gitignore"
                echo "  → Added '$entry' to $workspace/.gitignore"
            fi
        done
    fi
done

echo -e "${GREEN}✅ .gitignore entries added${NC}"

# Step 5: Summary
echo ""
echo -e "${GREEN}Setup Complete!${NC}"
echo "==============="
echo ""
echo "Centralized .env location:"
echo "  → $HOME/.env.tta-dev"
echo ""
echo "Workspace symlinks created:"
for workspace in "${WORKSPACES[@]}"; do
    if [ -d "$workspace" ]; then
        if [ -L "$workspace/.env" ]; then
            echo "  → $workspace/.env"
        fi
    fi
done
echo ""
echo "Usage in Python:"
echo "  from tta_secrets import get_env, require_env"
echo "  api_key = get_env('GEMINI_API_KEY')"
echo "  required = require_env('OPENAI_API_KEY')  # Raises if not set"
echo ""
echo "To update secrets: Edit ~/.env.tta-dev (changes apply to all workspaces)"
echo ""
