"""TTA.dev - Batteries-included AI workflow primitives with observability."""

__version__ = "0.1.0"

# Auto-initialize observability
from ttadev.observability.auto_instrument import auto_initialize

auto_initialize()

# Export main primitives
from ttadev.primitives.core import (
    LambdaPrimitive,
    ParallelPrimitive,
    SequentialPrimitive,
    WorkflowPrimitive,
)
from ttadev.primitives.recovery import (
    CircuitBreakerPrimitive,
    FallbackPrimitive,
    RetryPrimitive,
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
