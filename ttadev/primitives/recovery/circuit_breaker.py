"""Backward-compatibility shim for circuit_breaker utilities.

All symbols are now defined in :mod:`ttadev.primitives.recovery.circuit_breaker_primitive`.
Import from there directly for new code.

.. deprecated::
    This module will be removed in a future release.
    Use ``ttadev.primitives.recovery.circuit_breaker_primitive`` instead.
"""

from ttadev.primitives.recovery.circuit_breaker_primitive import (  # noqa: F401
    CircuitBreaker,
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    calculate_delay,
    classify_error,
    should_retry,
    with_retry,
    with_retry_async,
)

__all__ = [
    "CircuitBreaker",
    "ErrorCategory",
    "ErrorSeverity",
    "RetryConfig",
    "calculate_delay",
    "classify_error",
    "should_retry",
    "with_retry",
    "with_retry_async",
]
