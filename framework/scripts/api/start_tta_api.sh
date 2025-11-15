#!/bin/bash
# Setup and start TTA.dev API server for n8n integration

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         TTA.dev API Server Setup for n8n Integration          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running in TTA.dev directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from TTA.dev root directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Install FastAPI and uvicorn if not already installed
echo "📦 Installing API dependencies..."
uv pip install fastapi uvicorn[standard] pydantic

echo ""
echo "🚀 Starting TTA.dev API server..."
echo ""
echo "Server will run on: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set PYTHONPATH to include packages
export PYTHONPATH="$PWD/packages/tta-dev-primitives/src:$PWD/packages/tta-rebuild/src:$PYTHONPATH"

# Start the server
uv run python scripts/api/tta_api_server.py
