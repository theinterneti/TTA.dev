#!/bin/bash
set -e

echo "🔄 Phase 1: Consolidating into ttadev package"

# Create new consolidated structure
mkdir -p ttadev/{primitives,observability,agents,ui}

# Move primitives (core functionality)
if [ -d "tta-dev/primitives" ]; then
    echo "📦 Moving primitives..."
    cp -r tta-dev/primitives/* ttadev/primitives/
fi

# Move observability
if [ -d "tta-dev/observability" ]; then
    echo "📊 Moving observability..."
    cp -r tta-dev/observability/* ttadev/observability/
fi

# Move UI
if [ -d "tta-dev/ui" ]; then
    echo "🎨 Moving UI..."
    cp -r tta-dev/ui/* ttadev/ui/
fi

# Create proper __init__.py files
echo "📝 Creating package structure..."
cat > ttadev/__init__.py << 'INIT'
"""TTA.dev - Batteries-included AI workflow primitives with observability."""

__version__ = "0.1.0"

# Auto-initialize observability
from ttadev.observability.auto_instrument import setup_observability
setup_observability()

# Export main primitives
from ttadev.primitives.core import (
    WorkflowPrimitive,
    LambdaPrimitive,
    SequentialPrimitive,
    ParallelPrimitive,
)
from ttadev.primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    CircuitBreakerPrimitive,
)

__all__ = [
    "WorkflowPrimitive",
    "LambdaPrimitive",
    "SequentialPrimitive",
    "ParallelPrimitive",
    "RetryPrimitive",
    "FallbackPrimitive",
    "CircuitBreakerPrimitive",
    "setup_observability",
]
INIT

# Create subpackage __init__.py files
for dir in primitives observability agents ui; do
    touch ttadev/$dir/__init__.py
done

echo "✅ Phase 1 structure created"
