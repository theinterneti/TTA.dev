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
echo "   source .venv/bin/activate     # Activate environment"
echo "   python -m tta-dev.ui.app      # Start observability UI"
echo "   python demo_working_tta.py    # Run example"
echo ""
