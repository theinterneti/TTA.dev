#!/bin/bash
# n8n Startup Script with Environment Variables
# This script loads your .env file and starts n8n with all required API keys

set -e

echo "🚀 Starting n8n with TTA.dev environment..."
echo "=========================================="

# Load environment variables from .env
if [ -f .env ]; then
    echo "✅ Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ ERROR: .env file not found"
    echo "Please create .env file with your API keys"
    exit 1
fi

# Verify required environment variables
echo ""
echo "🔍 Verifying API keys..."
REQUIRED_VARS=("GEMINI_API_KEY" "GITHUB_PERSONAL_ACCESS_TOKEN" "E2B_API_KEY" "N8N_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        echo "❌ Missing: $var"
    else
        # Mask the key for security
        masked_value="${!var:0:4}...${!var: -4}"
        echo "✅ Found: $var = $masked_value"
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Missing required environment variables:"
    printf '   - %s\n' "${MISSING_VARS[@]}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All required API keys are configured${NC}"
echo ""

# Set n8n community nodes
export N8N_CUSTOM_EXTENSIONS="@n8n/n8n-nodes-langchain"

# Start n8n
echo -e "${BLUE}🚀 Starting n8n on port 5678...${NC}"
echo -e "${YELLOW}📦 Community nodes enabled: ${N8N_CUSTOM_EXTENSIONS}${NC}"
npx n8n
