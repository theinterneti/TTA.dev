#!/bin/bash
# Create a safe test workflow to verify LangChain Gemini nodes work

set -e

echo "🧪 Creating Safe LangChain Test Workflow..."
echo ""

# Check if n8n is running
if ! lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ n8n is not running. Please start n8n first:"
    echo "   npx n8n"
    exit 1
fi

# Create safe test workflow JSON
cat > /tmp/n8n_safe_langchain_test.json <<'EOF'
{
  "active": false,
  "name": "LangChain Gemini Test - Safe",
  "nodes": [
    {
      "parameters": {},
      "id": "manual-trigger",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [240, 400]
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "test-prompt",
              "name": "prompt",
              "value": "What is 2 + 2? Respond with just the number.",
              "type": "string"
            }
          ]
        }
      },
      "id": "set-test-prompt",
      "name": "Set Test Prompt",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3,
      "position": [460, 400]
    },
    {
      "parameters": {
        "prompt": "={{ $json.prompt }}",
        "options": {
          "maxTokens": 10,
          "temperature": 0
        }
      },
      "id": "langchain-gemini",
      "name": "LangChain Chat Gemini",
      "type": "@n8n/n8n-nodes-langchain.lmChatGemini",
      "typeVersion": 1,
      "position": [680, 400],
      "credentials": {
        "googlePalmApi": {
          "id": "gemini-api",
          "name": "Google Gemini API"
        }
      }
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "result",
              "name": "gemini_response",
              "value": "={{ $json.output }}",
              "type": "string"
            },
            {
              "id": "timestamp",
              "name": "test_timestamp",
              "value": "={{ $now.toISO() }}",
              "type": "string"
            }
          ]
        }
      },
      "id": "format-result",
      "name": "Format Result",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3,
      "position": [900, 400]
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [[{ "node": "Set Test Prompt", "type": "main", "index": 0 }]]
    },
    "Set Test Prompt": {
      "main": [[{ "node": "LangChain Chat Gemini", "type": "main", "index": 0 }]]
    },
    "LangChain Chat Gemini": {
      "main": [[{ "node": "Format Result", "type": "main", "index": 0 }]]
    }
  },
  "settings": {
    "executionOrder": "v1"
  }
}
EOF

echo "✅ Created safe test workflow JSON"
echo ""
echo "📥 Importing workflow..."

if npx n8n import:workflow --input /tmp/n8n_safe_langchain_test.json 2>&1 | grep -q "Successfully imported"; then
    echo "✅ Test workflow imported successfully!"
else
    echo "⚠️  Import completed (check for warnings)"
fi

echo ""
echo "📋 Next Steps for Manual Testing:"
echo ""
echo "1. Open n8n UI: http://localhost:5678"
echo ""
echo "2. Find workflow: 'LangChain Gemini Test - Safe'"
echo ""
echo "3. Configure Gemini credentials (if not already done):"
echo "   - Settings → Credentials"
echo "   - Add 'Google Gemini API' credential"
echo "   - Enter your Gemini API key"
echo ""
echo "4. Open the test workflow"
echo ""
echo "5. Verify the LangChain Chat Gemini node appears (not 'Unrecognized')"
echo ""
echo "6. (Optional) Execute the workflow manually:"
echo "   - Click 'Execute Workflow' button"
echo "   - Should respond with '4'"
echo "   - Verifies LangChain → Gemini integration works"
echo ""
echo "⚠️  This workflow is SAFE to run:"
echo "   - No git operations"
echo "   - No GitHub API calls"
echo "   - No file modifications"
echo "   - Just a simple math question to Gemini"
echo "   - Max 10 tokens (minimal cost)"
echo ""
echo "🔒 Remember: DO NOT activate or run workflows that:"
echo "   - Make git commits/pushes"
echo "   - Create PRs or issues"
echo "   - Modify files or repositories"
echo ""
