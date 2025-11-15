#!/bin/bash

# Import TTA.dev API workflow to n8n
# This script helps you import the workflow via the n8n UI

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Import TTA.dev API Workflow to n8n                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if n8n is running
if ! curl -s http://localhost:5678 > /dev/null 2>&1; then
    echo "❌ Error: n8n is not running on port 5678"
    echo "   Start n8n first: npx n8n"
    exit 1
fi

echo "✅ n8n is running on http://localhost:5678"

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Error: TTA.dev API is not running on port 8000"
    echo "   Start the API: ./scripts/api/start_tta_api.sh"
    exit 1
fi

echo "✅ TTA.dev API is running on http://localhost:8000"
echo ""

# Get the workflow file path
WORKFLOW_FILE="workflows/n8n_tta_api_github_health.json"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Error: Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

echo "📄 Workflow file: $WORKFLOW_FILE"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  MANUAL IMPORT INSTRUCTIONS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Open n8n in your browser:"
echo "   → http://localhost:5678"
echo ""
echo "2. Click on 'Workflows' in the left sidebar"
echo ""
echo "3. Click the '...' menu button (top right)"
echo ""
echo "4. Select 'Import from File'"
echo ""
echo "5. Choose this file:"
echo "   → $(realpath $WORKFLOW_FILE)"
echo ""
echo "6. The workflow 'GitHub Health Dashboard - TTA.dev API' will be imported"
echo ""
echo "7. Click 'Execute Workflow' to test it"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💡 TIP: You can also drag and drop the JSON file into the n8n UI"
echo ""

# Try to open browser (works on WSL with Windows browser)
if command -v wslview > /dev/null 2>&1; then
    echo "🌐 Opening n8n in your browser..."
    wslview http://localhost:5678 2>/dev/null &
elif command -v xdg-open > /dev/null 2>&1; then
    echo "🌐 Opening n8n in your browser..."
    xdg-open http://localhost:5678 2>/dev/null &
fi

echo ""
echo "Ready to import! Follow the steps above."
echo ""
