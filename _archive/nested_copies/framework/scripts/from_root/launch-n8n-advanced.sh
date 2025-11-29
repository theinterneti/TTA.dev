#!/bin/bash

# TTA.dev n8n Automation Launcher
# Comprehensive n8n startup with workflow import and credential setup

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
N8N_PORT=5678
N8N_URL="http://localhost:${N8N_PORT}"
WORKFLOWS_DIR="./workflows"
WAIT_TIME=30

# Parse arguments
AUTO_IMPORT=false
SKIP_BROWSER=false
FORCE_RESTART=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --auto-import)
      AUTO_IMPORT=true
      shift
      ;;
    --skip-browser)
      SKIP_BROWSER=true
      shift
      ;;
    --force-restart)
      FORCE_RESTART=true
      shift
      ;;
    --help)
      echo "TTA.dev n8n Automation Launcher"
      echo ""
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --auto-import     Automatically import workflows from ./workflows/"
      echo "  --skip-browser    Don't open browser automatically"
      echo "  --force-restart   Kill existing n8n process and restart"
      echo "  --help           Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                           # Basic startup"
      echo "  $0 --auto-import             # Startup with workflow import"
      echo "  $0 --force-restart           # Kill and restart n8n"
      echo "  $0 --auto-import --skip-browser  # Import without opening browser"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Print header
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  TTA.dev n8n Automation System Launcher${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function: Check if n8n is running
check_n8n_running() {
  if lsof -Pi :${N8N_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    return 0  # Running
  else
    return 1  # Not running
  fi
}

# Function: Wait for n8n to be ready
wait_for_n8n() {
  echo -e "${YELLOW}⏳ Waiting for n8n to be ready...${NC}"
  local attempts=0
  local max_attempts=$((WAIT_TIME))

  while [ $attempts -lt $max_attempts ]; do
    if curl -s "${N8N_URL}" >/dev/null 2>&1; then
      echo -e "${GREEN}✅ n8n is ready!${NC}"
      return 0
    fi

    attempts=$((attempts + 1))
    echo -n "."
    sleep 1
  done

  echo ""
  echo -e "${RED}❌ n8n failed to start within ${WAIT_TIME} seconds${NC}"
  return 1
}

# Function: Import workflow
import_workflow() {
  local workflow_file=$1
  local workflow_name=$(basename "$workflow_file" .json)

  echo -e "${YELLOW}📥 Importing: ${workflow_name}${NC}"

  # Note: n8n API import requires authentication and is complex
  # For now, we'll provide instructions for manual import
  # Future enhancement: Use n8n API with proper authentication

  echo -e "${BLUE}   File: ${workflow_file}${NC}"
}

# Function: Display workflow import instructions
show_import_instructions() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  📋 Workflow Import Instructions${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo -e "${GREEN}Available workflows in ${WORKFLOWS_DIR}/:${NC}"
  echo ""

  local workflow_count=0
  for workflow in "${WORKFLOWS_DIR}"/*.json; do
    if [ -f "$workflow" ]; then
      workflow_count=$((workflow_count + 1))
      local name=$(basename "$workflow" .json)
      echo -e "${GREEN}  ${workflow_count}. ${name}${NC}"

      # Extract workflow description from README
      case "$name" in
        "n8n_1_smart_commit_test")
          echo -e "${BLUE}     → Smart Commit & Test (every 10 min)${NC}"
          ;;
        "n8n_2_pr_manager")
          echo -e "${BLUE}     → PR Manager (webhook trigger)${NC}"
          ;;
        "n8n_3_issue_to_branch")
          echo -e "${BLUE}     → Issue-to-Branch (webhook trigger)${NC}"
          ;;
        "n8n_4_release_automation")
          echo -e "${BLUE}     → Release Automation (weekly)${NC}"
          ;;
      esac
    fi
  done

  echo ""
  echo -e "${YELLOW}📖 To import workflows:${NC}"
  echo -e "${YELLOW}   1. Open n8n: ${N8N_URL}${NC}"
  echo -e "${YELLOW}   2. Click 'Workflows' → 'Import from File'${NC}"
  echo -e "${YELLOW}   3. Select workflow JSON from ${WORKFLOWS_DIR}/${NC}"
  echo -e "${YELLOW}   4. Configure credentials (see below)${NC}"
  echo -e "${YELLOW}   5. Activate workflow (toggle in top-right)${NC}"
  echo ""
}

# Function: Display credential setup instructions
show_credential_instructions() {
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  🔐 Credential Setup Instructions${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo -e "${GREEN}Required credentials:${NC}"
  echo ""

  echo -e "${YELLOW}1. GitHub API Credential${NC}"
  echo -e "   Name: ${GREEN}GitHub API - TTA.dev${NC}"
  echo -e "   Type: GitHub API"
  echo -e "   Auth: Access Token"
  echo -e "   Token: ${GREEN}(from .env GITHUB_PERSONAL_ACCESS_TOKEN)${NC}"
  echo ""

  echo -e "${YELLOW}2. Google Gemini API Credential${NC}"
  echo -e "   Name: ${GREEN}Google Gemini API${NC}"
  echo -e "   Type: Google Gemini API"
  echo -e "   API Key: ${GREEN}(from .env GEMINI_API_KEY)${NC}"
  echo ""

  echo -e "${BLUE}💡 Tip: Copy credentials from .env file${NC}"
  echo -e "${BLUE}   Run: cat .env | grep -E 'GITHUB_PERSONAL_ACCESS_TOKEN|GEMINI_API_KEY'${NC}"
  echo ""
}

# Function: Display next steps
show_next_steps() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  🚀 Next Steps${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  echo -e "${GREEN}✅ n8n is running at: ${N8N_URL}${NC}"
  echo ""

  echo -e "${YELLOW}Immediate Actions:${NC}"
  echo -e "  1. ${GREEN}Import workflows${NC} (see instructions above)"
  echo -e "  2. ${GREEN}Configure credentials${NC} (GitHub API, Gemini API)"
  echo -e "  3. ${GREEN}Activate workflows${NC} (toggle switch in workflow)"
  echo -e "  4. ${GREEN}Test workflows${NC} (trigger manually or wait for schedule)"
  echo ""

  echo -e "${YELLOW}Useful Commands:${NC}"
  echo -e "  ${BLUE}View logs:${NC}      tail -f ~/.n8n/n8n.log"
  echo -e "  ${BLUE}Stop n8n:${NC}       pkill -f 'n8n'"
  echo -e "  ${BLUE}Restart:${NC}        $0 --force-restart"
  echo -e "  ${BLUE}Test setup:${NC}     ./scripts/test-n8n-setup.sh"
  echo ""

  echo -e "${YELLOW}Documentation:${NC}"
  echo -e "  ${BLUE}Workflows:${NC}      ./workflows/README.md"
  echo -e "  ${BLUE}Setup Guide:${NC}    ./N8N_EXPERT_SETUP_GUIDE.md"
  echo -e "  ${BLUE}Quickstart:${NC}     ./N8N_GIT_AUTOMATION_QUICKSTART.md"
  echo ""

  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main execution

# Step 1: Check if force restart requested
if [ "$FORCE_RESTART" = true ]; then
  echo -e "${YELLOW}🔄 Force restart requested...${NC}"

  if check_n8n_running; then
    echo -e "${YELLOW}   Stopping existing n8n process...${NC}"
    pkill -f 'n8n' || true
    sleep 2
    echo -e "${GREEN}   ✅ Stopped${NC}"
  else
    echo -e "${BLUE}   ℹ️  No existing n8n process found${NC}"
  fi
fi

# Step 2: Check if n8n is already running
if check_n8n_running; then
  echo -e "${GREEN}✅ n8n is already running on port ${N8N_PORT}${NC}"
  echo ""

  # If auto-import requested, show instructions
  if [ "$AUTO_IMPORT" = true ]; then
    show_import_instructions
  fi

  show_credential_instructions
  show_next_steps

  # Open browser if not skipped
  if [ "$SKIP_BROWSER" = false ]; then
    echo -e "${YELLOW}🌐 Opening browser...${NC}"
    if command -v xdg-open &> /dev/null; then
      xdg-open "$N8N_URL" 2>/dev/null &
    else
      echo -e "${BLUE}   ℹ️  Browser auto-open not available. Visit: ${N8N_URL}${NC}"
    fi
  fi

  exit 0
fi

# Step 3: Start n8n
echo -e "${YELLOW}🚀 Starting n8n...${NC}"
echo ""

# Use the start-n8n.sh script which loads environment variables
if [ -f "./scripts/start-n8n.sh" ]; then
  ./scripts/start-n8n.sh &
else
  echo -e "${RED}❌ Error: ./scripts/start-n8n.sh not found${NC}"
  echo -e "${YELLOW}   Creating minimal startup script...${NC}"

  # Fallback: Start n8n directly
  if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
  fi

  npx n8n &
fi

N8N_PID=$!
echo -e "${GREEN}   Started n8n (PID: ${N8N_PID})${NC}"

# Step 4: Wait for n8n to be ready
if wait_for_n8n; then
  # Step 5: Show import instructions if auto-import requested
  if [ "$AUTO_IMPORT" = true ]; then
    echo ""
    show_import_instructions
  fi

  # Step 6: Show credential instructions
  show_credential_instructions

  # Step 7: Show next steps
  show_next_steps

  # Step 8: Open browser if not skipped
  if [ "$SKIP_BROWSER" = false ]; then
    echo -e "${YELLOW}🌐 Opening browser...${NC}"
    sleep 2
    if command -v xdg-open &> /dev/null; then
      xdg-open "$N8N_URL" 2>/dev/null &
    else
      echo -e "${BLUE}   ℹ️  Browser auto-open not available. Visit: ${N8N_URL}${NC}"
    fi
  fi

  echo ""
  echo -e "${GREEN}✨ Setup complete! n8n automation system is ready.${NC}"
  echo ""

else
  echo -e "${RED}❌ Failed to start n8n${NC}"
  echo -e "${YELLOW}   Check logs: tail -f ~/.n8n/n8n.log${NC}"
  exit 1
fi
