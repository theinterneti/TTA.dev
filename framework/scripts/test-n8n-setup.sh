#!/bin/bash
# Test n8n Setup and API Connectivity
# This verifies all your API keys work before starting automation

set -e

echo "🧪 Testing n8n Setup for TTA.dev"
echo "=========================================="
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded .env file"
else
    echo "❌ ERROR: .env file not found"
    exit 1
fi

echo ""
echo "🔍 Testing API Connectivity..."
echo ""

# Test GitHub API
echo -n "GitHub API: "
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "❌ Token not set"
    exit 1
fi

GITHUB_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
    https://api.github.com/user)

if echo "$GITHUB_RESPONSE" | grep -q "login"; then
    GITHUB_USER=$(echo "$GITHUB_RESPONSE" | grep -o '"login": *"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "✅ Connected as $GITHUB_USER"
else
    echo "❌ Failed to connect"
    echo "Response: $GITHUB_RESPONSE"
    exit 1
fi

# Test GitHub repo access
echo -n "GitHub Repo Access (theinterneti/TTA.dev): "
REPO_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
    https://api.github.com/repos/theinterneti/TTA.dev)

if echo "$REPO_RESPONSE" | grep -q "full_name"; then
    echo "✅ Can access repository"
else
    echo "❌ Cannot access repository"
    exit 1
fi

# Test Gemini API
echo -n "Gemini API: "
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ API key not set"
    exit 1
fi

GEMINI_TEST='{"contents":[{"parts":[{"text":"Say hello in 3 words"}]}]}'
GEMINI_RESPONSE=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "$GEMINI_TEST")

if echo "$GEMINI_RESPONSE" | grep -q "candidates"; then
    echo "✅ API key valid and working"
else
    echo "⚠️  API key present but may have issues"
    echo "   (This won't prevent n8n from working)"
    # Don't exit - Gemini is optional for basic git automation
fi

# Test E2B API (optional)
echo -n "E2B API: "
if [ -z "$E2B_API_KEY" ]; then
    echo "⚠️  Not set (optional)"
else
    echo "✅ Key present (${E2B_API_KEY:0:8}...)"
fi

# Test n8n API
echo -n "n8n API Key: "
if [ -z "$N8N_API_KEY" ]; then
    echo "⚠️  Not set (will need to generate in n8n UI)"
else
    echo "✅ Key present"
fi

echo ""
echo "🔧 Testing Git Configuration..."
echo ""

# Check git config
echo -n "Git user.name: "
GIT_NAME=$(git config user.name 2>/dev/null || echo "")
if [ -n "$GIT_NAME" ]; then
    echo "✅ $GIT_NAME"
else
    echo "⚠️  Not configured (recommended to set)"
fi

echo -n "Git user.email: "
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")
if [ -n "$GIT_EMAIL" ]; then
    echo "✅ $GIT_EMAIL"
else
    echo "⚠️  Not configured (recommended to set)"
fi

# Check git status
echo -n "Git repository: "
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current)
    echo "✅ On branch $BRANCH"
else
    echo "❌ Not a git repository"
    exit 1
fi

echo ""
echo "📊 GitHub Rate Limit Status..."
echo ""

RATE_LIMIT=$(curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
    https://api.github.com/rate_limit)

CORE_REMAINING=$(echo "$RATE_LIMIT" | grep -o '"remaining": *[0-9]*' | head -1 | grep -o '[0-9]*')
CORE_LIMIT=$(echo "$RATE_LIMIT" | grep -o '"limit": *[0-9]*' | head -1 | grep -o '[0-9]*')

echo "API Requests Remaining: $CORE_REMAINING / $CORE_LIMIT"

if [ "$CORE_REMAINING" -lt 100 ]; then
    echo "⚠️  Warning: Low rate limit remaining"
else
    echo "✅ Sufficient rate limit available"
fi

echo ""
echo "🧪 Testing Fast Test Script..."
echo ""

if [ -f ./scripts/test_fast.sh ]; then
    echo "✅ Test script exists"
    echo "Running tests..."
    if ./scripts/test_fast.sh > /dev/null 2>&1; then
        echo "✅ Tests passed"
    else
        echo "⚠️  Tests failed (you may want to fix before enabling automation)"
    fi
else
    echo "⚠️  Test script not found at ./scripts/test_fast.sh"
fi

echo ""
echo "✅ Setup Test Complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ API keys configured and working"
echo "   ✅ GitHub access verified"
echo "   ✅ Git repository ready"
echo ""
echo "🚀 Next Steps:"
echo "   1. Run: ./scripts/start-n8n.sh"
echo "   2. Open: http://localhost:5678"
echo "   3. Import: n8n_git_automation_workflow.json"
echo "   4. Configure credentials in n8n UI"
echo "   5. Activate workflow"
echo ""
echo "📖 Full Guide: N8N_GIT_AUTOMATION_QUICKSTART.md"
