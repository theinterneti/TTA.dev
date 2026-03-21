#!/bin/bash
set -e

echo "🔧 Final TTA.dev Consolidation"
echo "================================"

cd "$(dirname "$0")/.."

# Move root-level Python modules into tta-dev/
echo "📦 Moving root modules into tta-dev..."

# Create __init__.py if missing
touch tta-dev/__init__.py

# Update pyproject.toml to reflect single package
echo "📝 Updating root pyproject.toml..."
cat > pyproject.toml << 'EOF'
[project]
name = "tta-dev"
version = "0.1.0"
description = "TTA.dev - Batteries-included AI workflow framework"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp>=1.20.0",
    "flask>=3.0.0",
    "flask-cors>=4.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "ruff>=0.1.0",
    "pyright>=1.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tta-dev"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: Heavy integration tests (opt-in)",
    "slow: Slow-running tests",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pyright]
include = ["tta-dev"]
pythonVersion = "3.11"
typeCheckingMode = "basic"
EOF

# Update setup.sh to use simpler installation
echo "🛠️ Updating setup.sh..."
cat > setup.sh << 'EOF'
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
EOF

chmod +x setup.sh

# Clean up test structure
echo "🧹 Organizing tests..."
mkdir -p tests/{unit,integration,benchmarks}

# Move any root-level test files
if ls test_*.py 2>/dev/null; then
    mv test_*.py tests/unit/ 2>/dev/null || true
fi

# Update README to reflect single package
echo "📄 Updating README..."
cat > README.md << 'EOF'
# TTA.dev

**Batteries-included AI workflow framework with built-in observability**

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev
./setup.sh

# 2. Activate environment
source .venv/bin/activate

# 3. Start observability UI
python -m tta-dev.ui.app

# 4. Run demo
python demo_working_tta.py
```

Visit http://localhost:5001 to see your workflows in real-time!

## What You Get

✅ **Workflow Primitives** - Retry, timeout, cache, circuit breaker, fallback
✅ **Built-in Observability** - Auto-instrumented tracing with live UI
✅ **Production Ready** - Sampling, error tracking, performance metrics
✅ **AI-Native** - Works with any AI coding agent (Claude, Copilot, Cline)

## Architecture

```
tta-dev/
├── primitives/      # Workflow building blocks
├── observability/   # Auto-instrumentation
├── ui/             # Live dashboard
├── agents/         # AI agent configurations
├── skills/         # Reusable workflows
└── integrations/   # LLM providers (Ollama, OpenRouter, etc.)
```

## Documentation

- [User Journey](USER_JOURNEY.md) - Complete walkthrough
- [Primitives Catalog](PRIMITIVES_CATALOG.md) - API reference
- [Contributing](CONTRIBUTING.md) - Development guide

## License

MIT
EOF

echo ""
echo "✅ Consolidation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Review the changes: git status"
echo "   2. Test installation: ./setup.sh"
echo "   3. Run tests: uv run pytest"
echo "   4. Commit: git add -A && git commit -m 'feat: final consolidation'"
