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
