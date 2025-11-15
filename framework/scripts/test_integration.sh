#!/usr/bin/env bash
# Integration tests - requires explicit opt-in
# These tests may start services, open ports, and consume significant resources
# Use this in CI or in a dedicated test environment with adequate resources

set -e

# Check for opt-in environment variable
if [ "$RUN_INTEGRATION" != "true" ]; then
    echo "⚠️  WARNING: Integration tests can consume significant resources!"
    echo ""
    echo "These tests may:"
    echo "  - Start network servers and open ports"
    echo "  - Spawn multiple processes"
    echo "  - Consume significant memory and CPU"
    echo "  - Run for several minutes"
    echo ""
    echo "On WSL or resource-constrained environments, this may cause instability."
    echo ""
    echo "To run integration tests, set RUN_INTEGRATION=true:"
    echo "  RUN_INTEGRATION=true $0"
    echo ""
    echo "Or use the VS Code task '🧪 Run Integration Tests (Safe)'"
    exit 1
fi

echo "🧪 Running integration tests..."
echo ""
echo "⚠️  Resource usage may be high. Monitor system resources."
echo ""

# Run integration tests with timeout and resource awareness
uv run pytest -v \
    -m "integration" \
    --timeout=300 \
    --maxfail=3 \
    "$@"

echo ""
echo "✅ Integration tests complete!"
