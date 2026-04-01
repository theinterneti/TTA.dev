"""Error recovery patterns for workflow primitives."""

from .circuit_breaker_primitive import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerPrimitive,
    CircuitState,
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    calculate_delay,
    classify_error,
    should_retry,
    with_retry,
    with_retry_async,
)
from .compensation import CompensationStrategy, SagaPrimitive
from .fallback import FallbackPrimitive, FallbackStrategy
from .retry import RetryPrimitive, RetryStrategy
from .timeout import TimeoutError, TimeoutPrimitive

__all__ = [
    # Circuit breaker and error classification (from dev-primitives)
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerPrimitive",
    "CircuitState",
    "ErrorCategory",
    "ErrorSeverity",
    "RetryConfig",
    "calculate_delay",
    "classify_error",
    "should_retry",
    "with_retry",
    "with_retry_async",
    # Workflow primitives
    "CompensationStrategy",
    "FallbackPrimitive",
    "FallbackStrategy",
    "RetryPrimitive",
    "RetryStrategy",
    "SagaPrimitive",
    "TimeoutPrimitive",
    "TimeoutError",
]
