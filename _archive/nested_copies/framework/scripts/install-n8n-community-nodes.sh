#!/bin/bash

# Install n8n Community Nodes
# This script installs the LangChain community nodes package into n8n

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Installing n8n Community Nodes${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if n8n is running
if ! curl -s http://localhost:5678 >/dev/null 2>&1; then
  echo -e "${RED}❌ n8n is not running!${NC}"
  echo -e "${YELLOW}   Start n8n first with: ./launch-n8n.sh${NC}"
  exit 1
fi

echo -e "${GREEN}✅ n8n is running${NC}"
echo ""

# Method 1: Install to n8n's node_modules
echo -e "${YELLOW}📦 Installing @n8n/n8n-nodes-langchain to n8n...${NC}"

# Find n8n installation directory
N8N_DIR=$(npm root -g)/n8n

if [ -d "$N8N_DIR" ]; then
  echo -e "${BLUE}   Found n8n at: $N8N_DIR${NC}"

  # Install LangChain nodes as a dependency of n8n
  cd "$N8N_DIR"
  npm install @n8n/n8n-nodes-langchain --save

  echo -e "${GREEN}✅ Installed @n8n/n8n-nodes-langchain${NC}"
else
  echo -e "${YELLOW}⚠️  Could not find global n8n installation${NC}"
  echo -e "${YELLOW}   Trying alternative installation method...${NC}"

  # Alternative: Install to ~/.n8n/custom
  mkdir -p ~/.n8n/custom
  cd ~/.n8n/custom

  if [ ! -f "package.json" ]; then
    npm init -y
  fi

  npm install @n8n/n8n-nodes-langchain

  echo -e "${GREEN}✅ Installed to ~/.n8n/custom/${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ⚠️  Important: Restart Required${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}You must restart n8n for the nodes to be available:${NC}"
echo ""
echo -e "${GREEN}  1. Stop n8n: ${NC}pkill -f n8n"
echo -e "${GREEN}  2. Start n8n: ${NC}./launch-n8n.sh"
echo ""
echo -e "${YELLOW}After restart, verify in n8n UI:${NC}"
echo -e "  - Settings → Community Nodes"
echo -e "  - Should show: @n8n/n8n-nodes-langchain"
echo ""
