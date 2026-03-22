#!/bin/bash
set -e

echo "🚀 Setting up TTA.dev..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📥 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✅ uv installed"

# Install TTA.dev
echo "📦 Installing TTA.dev..."
uv sync --all-extras

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Verified proof path:"
echo "   # Terminal 1: start the observability server"
echo "   uv run python -m ttadev.observability"
echo ""
echo "   # Terminal 2: generate traces"
echo "   uv run python scripts/test_realtime_traces.py"
echo ""
echo "   # Optional: inspect the current v2 APIs"
echo "   curl http://localhost:8000/api/v2/health"
echo "   curl http://localhost:8000/api/v2/spans | head"
echo ""
