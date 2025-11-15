#!/bin/bash

# Fix GitHub Credentials in n8n
# This guide helps you configure GitHub authentication

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Fix GitHub Credentials in n8n                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "🔧 ISSUE: 'Credentials not found' error in GitHub node"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  SOLUTION: Configure GitHub Credential in n8n"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Step 1: Get Your GitHub Personal Access Token"
echo "───────────────────────────────────────────────────────────────"
echo ""
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token' → 'Generate new token (classic)'"
echo "3. Give it a name: 'n8n workflow access'"
echo "4. Select scopes:"
echo "   ✓ repo (Full control of private repositories)"
echo "   ✓ read:org (Read org and team membership)"
echo "5. Click 'Generate token'"
echo "6. Copy the token (you won't see it again!)"
echo ""

echo "Step 2: Add Credential to n8n"
echo "───────────────────────────────────────────────────────────────"
echo ""
echo "1. Open n8n: http://localhost:5678"
echo "2. Click 'Credentials' in left sidebar"
echo "3. Click 'Add Credential'"
echo "4. Search for 'GitHub' and select 'GitHub API'"
echo "5. Fill in:"
echo "   • Name: 'GitHub API'"
echo "   • Access Token: [paste your token from Step 1]"
echo "6. Click 'Save'"
echo ""

echo "Step 3: Update Your Workflow Node"
echo "───────────────────────────────────────────────────────────────"
echo ""
echo "1. Go back to your workflow"
echo "2. Click on 'Get GitHub Repository Stats' node"
echo "3. In 'Credential to connect with' dropdown:"
echo "   • Select the 'GitHub API' credential you just created"
echo "4. Click 'Execute Node' or 'Execute Workflow'"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  ALTERNATIVE: Use HTTP Request Node Instead"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "If you don't want to use the GitHub node, use HTTP Request:"
echo ""
echo "Node Configuration:"
echo "  • Method: GET"
echo "  • URL: https://api.github.com/repos/theinterneti/TTA.dev"
echo "  • Authentication: Generic Credential Type"
echo "  • Generic Auth Type: Header Auth"
echo "  • Header Auth:"
echo "    - Name: Authorization"
echo "    - Value: token YOUR_GITHUB_TOKEN"
echo ""

echo "This will return the same repository data without using the GitHub node."
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  QUICK TEST"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if GitHub token exists in environment
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ GitHub token found in environment: GITHUB_TOKEN"
    echo ""
    echo "Testing GitHub API access..."
    RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/theinterneti/TTA.dev)

    if echo "$RESPONSE" | grep -q "full_name"; then
        echo "✅ GitHub API access working!"
        echo ""
        STARS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stargazers_count', 'N/A'))" 2>/dev/null || echo "N/A")
        FORKS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('forks_count', 'N/A'))" 2>/dev/null || echo "N/A")
        ISSUES=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('open_issues_count', 'N/A'))" 2>/dev/null || echo "N/A")

        echo "Repository Stats:"
        echo "  • Stars: $STARS"
        echo "  • Forks: $FORKS"
        echo "  • Open Issues: $ISSUES"
        echo ""
        echo "You can use this token in n8n!"
    else
        echo "❌ GitHub API access failed"
        echo "Response: $RESPONSE"
    fi
else
    echo "⚠️  No GitHub token found in environment"
    echo ""
    echo "To test GitHub API access, export your token:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo "  ./scripts/n8n/fix_github_credentials.sh"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📚 More Info:"
echo "  • GitHub Tokens: https://github.com/settings/tokens"
echo "  • n8n Credentials: http://localhost:5678/credentials"
echo "  • GitHub API Docs: https://docs.github.com/en/rest"
echo ""
