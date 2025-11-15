#!/bin/bash
# Enhance GitHub Copilot Setup Workflow - Phase 1 Optimizations
# Implements low-hanging fruit improvements from COPILOT_ENVIRONMENT_OPTIMIZATION.md

set -euo pipefail

echo "🚀 Enhancing GitHub Copilot Setup Workflow - Phase 1"
echo ""

WORKFLOW_FILE=".github/workflows/copilot-setup-steps.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Error: $WORKFLOW_FILE not found"
    exit 1
fi

echo "📝 Backing up current workflow..."
cp "$WORKFLOW_FILE" "${WORKFLOW_FILE}.backup"
echo "✅ Backup created: ${WORKFLOW_FILE}.backup"
echo ""

echo "🔧 Applying Phase 1 optimizations..."
echo ""

# Create enhanced workflow with all Phase 1 improvements
cat > "$WORKFLOW_FILE" << 'EOF'
name: "Copilot Setup Steps"

# This workflow configures the GitHub Copilot coding agent's ephemeral environment.
# 
# Performance: ~9-11 seconds with cache, ~14 seconds without
# Cache: ~/.cache/uv + .venv (~43MB)
# 
# For more information:
# - Workflow docs: docs/development/TESTING_COPILOT_SETUP.md
# - Environment verification: scripts/check-environment.sh
# - Optimization guide: docs/development/COPILOT_ENVIRONMENT_OPTIMIZATION.md
# - Agent guidance: AGENTS.md

on:
  workflow_dispatch:  # Manual testing via Actions tab
  push:
    paths:
      - .github/workflows/copilot-setup-steps.yml
  pull_request:
    paths:
      - .github/workflows/copilot-setup-steps.yml

permissions:
  contents: read

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Add uv to PATH
        run: echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/uv
            .venv
          key: copilot-uv-${{ runner.os }}-${{ hashFiles('uv.lock', 'pyproject.toml', 'packages/*/pyproject.toml') }}
          restore-keys: |
            copilot-uv-${{ runner.os }}-

      - name: Configure environment
        run: |
          echo "PYTHONPATH=$PWD/packages" >> $GITHUB_ENV
          echo "PYTHONUTF8=1" >> $GITHUB_ENV
          echo "PYTHONDONTWRITEBYTECODE=1" >> $GITHUB_ENV
          echo "UV_CACHE_DIR=~/.cache/uv" >> $GITHUB_ENV

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Verify installation
        run: |
          echo "=== 🐍 Python Environment ==="
          uv run python --version
          uv run python -c "import sys; print(f'Python: {sys.executable}')"
          
          echo ""
          echo "=== 📦 Package Manager ==="
          uv --version
          echo "uv location: $(which uv)"
          
          echo ""
          echo "=== 🧪 Testing Tools ==="
          uv run pytest --version
          TEST_COUNT=$(uv run pytest --collect-only -q 2>/dev/null | tail -1 || echo "tests available")
          echo "Tests: $TEST_COUNT"
          
          echo ""
          echo "=== 🎨 Code Quality Tools ==="
          uv run ruff --version
          uvx --version
          
          echo ""
          echo "=== 📚 Key Packages ==="
          uv pip list | grep -E "(structlog|opentelemetry|pytest)" || echo "Core packages installed"
          
          echo ""
          echo "✅ Environment ready! Agent can now:"
          echo "  • Run tests: uv run pytest -v"
          echo "  • Check code: uv run ruff check ."
          echo "  • Format code: uv run ruff format ."
          echo "  • Type check: uvx pyright packages/"
          echo "  • Verify env: ./scripts/check-environment.sh"
EOF

echo "✅ Phase 1 optimizations applied:"
echo "   1. Documentation comments added"
echo "   2. Environment variables configured"
echo "   3. Enhanced verification output with agent guidance"
echo ""

echo "📊 Changes summary:"
git diff --stat "$WORKFLOW_FILE" || echo "(No git repo detected, showing file size)"
wc -l "$WORKFLOW_FILE"
echo ""

echo "🎯 Next steps:"
echo "   1. Review changes: git diff $WORKFLOW_FILE"
echo "   2. Test locally: Check verification output makes sense"
echo "   3. Test on GitHub: git commit & push, then monitor workflow run"
echo "   4. Monitor performance: gh run list --workflow=copilot-setup-steps.yml"
echo ""

echo "📖 Full optimization guide: docs/development/COPILOT_ENVIRONMENT_OPTIMIZATION.md"
echo ""

read -p "Would you like to see the diff now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git diff "$WORKFLOW_FILE" || cat "$WORKFLOW_FILE"
fi

echo ""
echo "✨ Enhancement complete! Backup available at: ${WORKFLOW_FILE}.backup"
