#!/bin/bash

# n8n GitHub Health Dashboard Setup Script
# This script sets up the n8n workflow with GitHub and Gemini credentials

set -e

echo "🚀 Setting up n8n GitHub Health Dashboard..."

# Check if n8n is running
if ! pgrep -f "n8n" > /dev/null; then
    echo "⚠️  n8n is not running. Please start n8n first:"
    echo "   npx n8n"
    exit 1
fi

# Get n8n default port (usually 5678)
N8N_PORT=${N8N_PORT:-5678}
N8N_BASE_URL="http://localhost:${N8N_PORT}"

echo "📡 Testing n8n connectivity at ${N8N_BASE_URL}..."

# Test n8n API connectivity
if curl -f "${N8N_BASE_URL}/api/v1/active-workflows" > /dev/null 2>&1; then
    echo "✅ n8n is accessible"
else
    echo "❌ n8n is not accessible. Please ensure it's running on port ${N8N_PORT}"
    exit 1
fi

# Test GitHub API with provided credentials
echo "🔑 Testing GitHub API access..."
GITHUB_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN:-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}"
GITHUB_RESPONSE=$(curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
    "https://api.github.com/repos/theinterneti/TTA.dev" | jq -r '.full_name' 2>/dev/null || echo "")

if [ "$GITHUB_RESPONSE" = "theinterneti/TTA.dev" ]; then
    echo "✅ GitHub API access working"
else
    echo "❌ GitHub API access failed"
    exit 1
fi

# Test Gemini API
echo "🤖 Testing Gemini API access..."
GEMINI_KEY="${GEMINI_API_KEY:-AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE}"
GEMINI_RESPONSE=$(curl -s -H "Content-Type: application/json" \
    -d '{"contents":[{"parts":[{"text":"Test"}]}]}' \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_KEY}" | jq -r '.candidates[0].content.parts[0].text' 2>/dev/null || echo "")

if [ -n "$GEMINI_RESPONSE" ]; then
    echo "✅ Gemini API access working"
else
    echo "❌ Gemini API access failed"
    exit 1
fi

echo "🎉 All API connections successful!"

# Load the workflow into n8n
echo "📥 Importing workflow to n8n..."
WORKFLOW_FILE="n8n_github_health_dashboard.json"

# Read the workflow file and import it
WORKFLOW_JSON=$(cat "$WORKFLOW_FILE")
IMPORT_RESPONSE=$(curl -s -X POST "${N8N_BASE_URL}/api/v1/workflows" \
    -H "Content-Type: application/json" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4NzEzNzFkMy1iYzI5LTQ4OTEtYWMyMS04NjA0MjgzMWUwN2EiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyNjYzNjMwfQ.YceFmOj8L3ZXumqHq_KlBgGpNzbRRG-OUehX8yRjPfw}" \
    -d "$WORKFLOW_JSON" 2>/dev/null || echo "")

if echo "$IMPORT_RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
    WORKFLOW_ID=$(echo "$IMPORT_RESPONSE" | jq -r '.id')
    echo "✅ Workflow imported successfully with ID: $WORKFLOW_ID"

    # Activate the workflow
    echo "🔄 Activating workflow..."
    ACTIVATE_RESPONSE=$(curl -s -X PATCH "${N8N_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/activate" \
        -H "Content-Type: application/json" \
        -H "X-N8N-API-KEY: ${N8N_API_KEY:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4NzEzNzFkMy1iYzI5LTQ4OTEtYWMyMS04NjA0MjgzMWUwN2EiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyNjYzNjMwfQ.YceFmOj8L3ZXumqHq_KlBgGpNzbRRG-OUehX8yRjPfw}" \
        2>/dev/null || echo "")

    if echo "$ACTIVATE_RESPONSE" | jq -e '.active' > /dev/null 2>&1; then
        echo "✅ Workflow activated successfully"
    else
        echo "❌ Failed to activate workflow"
        exit 1
    fi

    echo ""
    echo "🎊 n8n GitHub Health Dashboard setup complete!"
    echo ""
    echo "📊 Dashboard Details:"
    echo "   - Repository: theinterneti/TTA.dev"
    echo "   - Schedule: Every 6 hours"
    echo "   - Health Score: AI-calculated using Gemini"
    echo "   - Features: Repository metrics, AI insights, alerts"
    echo ""
    echo "🔗 Access your dashboard:"
    echo "   n8n Interface: ${N8N_BASE_URL}"
    echo "   API: Use workflow trigger to get dashboard data"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Open n8n interface in browser"
    echo "   2. Configure GitHub API credentials in n8n"
    echo "   3. Test the workflow manually"
    echo "   4. Monitor the dashboard for insights"
    echo ""
    echo "🐛 Troubleshooting:"
    echo "   - Check workflow logs in n8n interface"
    echo "   - Verify API keys in n8n credentials"
    echo "   - Test individual GitHub API calls"

else
    echo "❌ Failed to import workflow"
    echo "Response: $IMPORT_RESPONSE"
    exit 1
fi

echo ""
echo "🔧 Manual Setup Instructions (if API import failed):"
echo "1. Open n8n interface: ${N8N_BASE_URL}"
echo "2. Create new workflow"
echo "3. Import the JSON file: ${WORKFLOW_FILE}"
echo "4. Configure GitHub API credentials"
echo "5. Configure environment variables for Gemini API"
echo "6. Test the workflow"
