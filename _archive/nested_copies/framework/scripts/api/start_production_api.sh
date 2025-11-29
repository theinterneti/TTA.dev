#!/bin/bash

# Start TTA.dev API Server - Production Version
# With real Gemini integration and TTA.dev primitives

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       TTA.dev API Server - Production Startup                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running from TTA.dev root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from TTA.dev repository root"
    echo "   cd /path/to/TTA.dev"
    exit 1
fi

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv not installed"
    echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "📦 Installing dependencies..."
uv pip install fastapi "uvicorn[standard]" pydantic google-generativeai python-dotenv

# Check for .env file
echo ""
echo "🔑 Checking for .env file..."
if [ -f ".env" ]; then
    echo "✅ .env file found"

    # Check for Gemini API key in .env
    if grep -q "GEMINI_API_KEY=" .env; then
        GEMINI_KEY=$(grep "GEMINI_API_KEY=" .env | cut -d'=' -f2 | tr -d ' ' | head -c 20)
        if [ -n "$GEMINI_KEY" ] && [ "$GEMINI_KEY" != "your-google-ai-studio-key-here" ]; then
            echo "✅ GEMINI_API_KEY found in .env: ${GEMINI_KEY}..."
        else
            echo "⚠️  GEMINI_API_KEY in .env but not configured"
            echo "   Edit .env and add your key from: https://ai.google.dev/"
            echo "   Will run in MOCK MODE for now"
        fi
    else
        echo "⚠️  GEMINI_API_KEY not in .env"
        echo "   Add to .env: GEMINI_API_KEY=your_key_here"
        echo "   Will run in MOCK MODE for now"
    fi
else
    echo "⚠️  .env file not found"
    echo "   Copy .env.example to .env and add your keys"
    echo "   cp .env.example .env"
    echo "   Will run in MOCK MODE for now"
fi

echo ""
echo "🔧 Configuring environment..."

# Set PYTHONPATH to include our packages
export PYTHONPATH="$PWD/packages/tta-dev-primitives/src:$PWD/packages/tta-rebuild/src:$PYTHONPATH"

# Stop old server if running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 already in use"
    OLD_PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "   Stopping old server (PID: $OLD_PID)..."
    kill $OLD_PID 2>/dev/null
    sleep 2
fi

echo ""
echo "🚀 Starting TTA.dev API Server..."
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   SERVER STARTING                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Start server with uv run (ensures dependencies are available)
uv run python scripts/api/tta_api_server_production.py

# If we get here, server stopped
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   SERVER STOPPED                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
