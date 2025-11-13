#!/usr/bin/env bash
# Fast unit tests - safe for local development
# Runs only unit tests, skipping integration and slow tests
# Safe for WSL and resource-constrained environments

set -e

echo "🧪 Running fast unit tests (skipping integration and slow tests)..."
echo ""

# Run unit tests only, excluding integration and slow tests
uv run pytest -q \
    -m "not integration and not slow and not external" \
    --maxfail=5 \
    --timeout=60 \
    "$@"

echo ""
echo "✅ Fast unit tests complete!"
