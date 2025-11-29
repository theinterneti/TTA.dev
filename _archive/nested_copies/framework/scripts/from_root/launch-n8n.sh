#!/bin/bash
# Quick n8n Launcher for TTA.dev
# One-command n8n startup with credential reminder

echo "🚀 n8n Quick Launch for TTA.dev"
echo "=================================="
echo ""

# Check if n8n is already running
if lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  n8n is already running on port 5678"
    echo ""
    echo "Options:"
    echo "  1. Open browser: http://localhost:5678"
    echo "  2. Stop existing instance: kill \$(lsof -t -i:5678)"
    echo ""
    exit 1
fi

# Start n8n
./scripts/start-n8n.sh &
N8N_PID=$!

# Wait for n8n to start
echo ""
echo "⏳ Waiting for n8n to start..."
sleep 5

# Check if n8n started successfully
if lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✅ n8n is running!"
    echo ""
    echo "📋 Next Steps:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1️⃣  Open n8n in browser:"
    echo "   👉 http://localhost:5678"
    echo ""
    echo "2️⃣  Add GitHub credential:"
    echo "   • Settings → Credentials → Add credential"
    echo "   • Search: 'GitHub API'"
    echo "   • Token: github_pat_11BIKGFRY0rMloGEXcuYX5_..."
    echo ""
    echo "3️⃣  Import workflow:"
    echo "   • New workflow → ... menu → Import from file"
    echo "   • File: n8n_git_automation_workflow.json"
    echo ""
    echo "4️⃣  Configure & Activate:"
    echo "   • Update node credentials"
    echo "   • Toggle workflow to 'Active'"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📖 Full Guide: N8N_READY_TO_LAUNCH.md"
    echo ""
    echo "⏹️  To stop n8n: Press Ctrl+C or run: kill $N8N_PID"
    echo ""

    # Open browser if xdg-open is available
    if command -v xdg-open >/dev/null 2>&1; then
        echo "🌐 Opening browser..."
        xdg-open http://localhost:5678 >/dev/null 2>&1 &
    fi

    # Keep script running
    wait $N8N_PID
else
    echo "❌ Failed to start n8n"
    echo "Check ./scripts/start-n8n.sh for errors"
    exit 1
fi
