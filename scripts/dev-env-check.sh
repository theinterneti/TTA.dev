#!/bin/bash

# TTA.dev Development Environment Check
# Ensures both observability and dependencies are ready

set -e

echo "🔍 TTA.dev Development Environment Status"
echo "========================================="

# Check Python/UV
if command -v uv &> /dev/null; then
    echo "✅ UV package manager available"
else
    echo "❌ UV not found - install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Check dependencies
if uv sync --dry-run &> /dev/null; then
    echo "✅ Dependencies are synced"
else
    echo "⚠️  Dependencies need syncing - run: uv sync --all-extras"
fi

# Check observability
if docker ps | grep -q tta-prometheus; then
    echo "✅ Observability stack is running"
    echo "   📊 Prometheus: http://localhost:9090"
    echo "   🔍 Jaeger: http://localhost:16686"
    echo "   📈 Grafana: http://localhost:3000"
else
    echo "❌ Observability stack not running"
    echo "   🚀 Start with: ./scripts/setup-observability.sh"
fi

# Check if tests pass
echo ""
echo "🧪 Running quick health check..."
if uv run python -c "from tta_dev_primitives import WorkflowContext; print('✅ TTA.dev primitives importable')" 2>/dev/null; then
    echo "✅ Core packages are working"
else
    echo "❌ Package import failed - check dependencies"
fi

echo ""
echo "🎯 Ready to develop with TTA.dev!"
echo "   • Run observability demo: uv run python packages/tta-dev-primitives/examples/observability_demo.py"
echo "   • Run tests: uv run pytest -v"
echo "   • Check observability: ./scripts/observability-status.sh"
echo ""
