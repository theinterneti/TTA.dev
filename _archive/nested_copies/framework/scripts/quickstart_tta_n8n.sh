#!/bin/bash

# TTA.dev API + n8n Integration - Quick Start
# This script verifies everything is ready and guides you through the final steps

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     TTA.dev API + n8n Integration - Quick Start                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ TTA.dev API is running on port 8000"
else
    echo "❌ TTA.dev API is NOT running"
    echo "   Starting it now..."
    ./scripts/api/start_tta_api.sh &
    sleep 3
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ TTA.dev API started successfully"
    else
        echo "❌ Failed to start API. Check logs: tail -f /tmp/tta_api.log"
        exit 1
    fi
fi

# Check if n8n is running
if curl -s http://localhost:5678 > /dev/null 2>&1; then
    echo "✅ n8n is running on port 5678"
else
    echo "❌ n8n is NOT running"
    echo "   Please start n8n first: npx n8n"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  System Status: ALL SYSTEMS OPERATIONAL ✅"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Run tests
echo "Running quick health check..."
echo ""

HEALTH=$(curl -s http://localhost:8000/health)
STATUS=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")

if [ "$STATUS" = "healthy" ]; then
    echo "✅ API Health: $STATUS"
    echo ""
    echo "$HEALTH" | python3 -m json.tool
else
    echo "❌ API Health: $STATUS"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🎯 READY FOR WORKFLOW IMPORT"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Your TTA.dev API is ready! Now import the workflow to n8n:"
echo ""
echo "📋 Option 1 - Browser Import (Recommended):"
echo "   1. Open n8n: http://localhost:5678"
echo "   2. Click 'Workflows' → '...' menu → 'Import from File'"
echo "   3. Select: workflows/n8n_tta_api_github_health.json"
echo "   4. Click 'Execute Workflow' to test"
echo ""
echo "📋 Option 2 - Drag and Drop:"
echo "   1. Open n8n: http://localhost:5678"
echo "   2. Drag workflows/n8n_tta_api_github_health.json into browser"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📚 Documentation:"
echo "   • Complete Guide: TTA_API_COMPLETE.md"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Integration Guide: TTA_API_N8N_INTEGRATION_GUIDE.md"
echo ""
echo "🧪 Test Commands:"
echo "   • Run all tests: ./scripts/api/test_tta_api.sh"
echo "   • View API logs: tail -f /tmp/tta_api.log"
echo "   • Health check: curl http://localhost:8000/health"
echo ""

# Try to open n8n in browser
if command -v wslview > /dev/null 2>&1; then
    echo "🌐 Opening n8n in your browser..."
    wslview http://localhost:5678 2>/dev/null &
elif command -v xdg-open > /dev/null 2>&1; then
    echo "🌐 Opening n8n in your browser..."
    xdg-open http://localhost:5678 2>/dev/null &
fi

echo ""
echo "✨ Everything is ready! Import the workflow and start testing."
echo ""
