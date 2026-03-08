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
echo "🎯 Quick Start:"
echo "   # Start observability UI"
echo "   uv run uvicorn tta-dev.ui.observability_server:app --port 5001"
echo ""
echo "   # Then visit: http://localhost:5001"
echo ""
echo "   # Run demo (in another terminal)"
echo "   uv run python demo_working_tta.py"
echo ""
