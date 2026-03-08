#!/bin/bash
set -e

echo "=== Phase 1: Architecture Consolidation ==="

# Create unified structure
mkdir -p tta_dev/{core,observability,ui,cli}

# Move primitives to core
echo "Moving primitives..."
if [ -d "packages/tta-dev-primitives" ]; then
    cp -r packages/tta-dev-primitives/src/tta_dev_primitives/* tta_dev/core/
fi
if [ -d "platform/primitives" ]; then
    cp -r platform/primitives/src/* tta_dev/core/
fi

# Move observability
echo "Moving observability..."
if [ -d "platform/observability" ]; then
    cp -r platform/observability/src/observability_integration/* tta_dev/observability/
fi

# Move UI
echo "Moving UI..."
if [ -d "apps/observability-ui" ]; then
    cp -r apps/observability-ui/ui/* tta_dev/ui/
fi

# Create __init__.py files
find tta_dev -type d -exec touch {}/__init__.py \;

echo "Phase 1 complete! Review tta_dev/ directory before removing old structure."
