#!/bin/bash
# TTA.dev Batteries-Included Setup
# Run this after cloning: ./setup.sh

set -e

echo "🚀 Setting up TTA.dev..."
echo

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv installed"
echo

# Install dependencies
echo "📦 Installing dependencies..."
cd tta-dev
uv sync --all-extras
echo "✅ Dependencies installed"
echo

# Create .env if it doesn't exist
if [ ! -f "../.env" ]; then
    echo "🔧 Creating .env file..."
    cat > ../.env << 'EOF'
# TTA.dev Configuration
TTA_ENV=development

# Observability (Optional)
# LANGFUSE_PUBLIC_KEY=your-public-key
# LANGFUSE_SECRET_KEY=your-secret-key
# LANGFUSE_HOST=https://cloud.langfuse.com

# OpenTelemetry (Optional)
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
EOF
    echo "✅ Created .env file"
    echo
fi

echo "🎉 TTA.dev is ready!"
echo
echo "Next steps:"
echo "  1. Point your CLI agent (Copilot/Claude/Cline) at this directory"
echo "  2. Your agent will auto-detect AGENTS.md and use TTA.dev primitives"
echo "  3. Run 'tta-dev-ui' to see observability dashboard"
echo
echo "Documentation:"
echo "  - AGENTS.md - Quick reference for agents"
echo "  - PRIMITIVES_CATALOG.md - Complete API docs"
echo "  - USER_JOURNEY.md - End-to-end walkthrough"
echo
echo "Happy coding! 🚀"
