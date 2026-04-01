"""Circuit Breaker Primitive for fault tolerance.

Implements the circuit breaker pattern to prevent cascading failures in workflows.
Also provides legacy utility functions and classes (ErrorCategory, RetryConfig, etc.)
previously in ``circuit_breaker.py``.

# See: [[TTA.dev/Primitives/CircuitBreakerPrimitive]]
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any, ParamSpec, TypeVar

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)
_legacy_logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


# ---------------------------------------------------------------------------
# CircuitBreakerPrimitive (canonical WorkflowPrimitive-based implementation)
# ---------------------------------------------------------------------------


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing immediately
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5
    """Number of consecutive failures before opening circuit"""

    recovery_timeout: float = 60.0
    """Seconds to wait before testing recovery (OPEN -> HALF_OPEN)"""

    success_threshold: int = 2
    """Number of consecutive successes in HALF_OPEN to close circuit"""

    expected_exception: type[Exception] = Exception
    """Exception type to catch (others pass through)"""

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if self.success_threshold <= 0:
            raise ValueError("success_threshold must be positive")


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, failure_count: int, last_error: Exception | None = None):
        """Initialize error."""
        self.failure_count = failure_count
        self.last_error = last_error
        super().__init__(f"Circuit breaker is OPEN after {failure_count} consecutive failures")


class CircuitBreakerPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Implements circuit breaker pattern to prevent cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if the underlying service has recovered

    State transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN -> CLOSED: After success_threshold consecutive successes
    - HALF_OPEN -> OPEN: On any failure

    Example:
        ```python
        from ttadev.primitives import CircuitBreakerPrimitive, WorkflowContext
        from ttadev.primitives.recovery.circuit_breaker_primitive import (
            CircuitBreakerConfig,
        )

        # Wrap an unreliable primitive
        circuit = CircuitBreakerPrimitive(
            primitive=unreliable_service,
            config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                success_threshold=2
            )
        )

        # Execute through circuit breaker
        try:
            result = await circuit.execute(data, context)
        except CircuitBreakerError:
            print("Circuit is open, using fallback")
            result = fallback_value
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive[Any, Any],
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """
        Initialize circuit breaker primitive.

        Args:
            primitive: The primitive to protect with circuit breaker
            config: Circuit breaker configuration
        """
        self.primitive = primitive
        self.config = config or CircuitBreakerConfig()

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._last_error: Exception | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get consecutive failure count."""
        return self._failure_count

    @property
    def success_count(self) -> int:
        """Get consecutive success count in HALF_OPEN state."""
        return self._success_count

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitive through circuit breaker.

        Args:
            input_data: Input data for the primitive
            context: Workflow context

        Returns:
            Output from the primitive

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If primitive execution fails
        """
        # Check if we should attempt recovery (before acquiring lock)
        should_attempt = False
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            should_attempt = True

        async with self._lock:
            # Transition to HALF_OPEN if recovery timeout has passed
            if should_attempt and self._state == CircuitState.OPEN:
                logger.info("Circuit breaker transitioning to HALF_OPEN for testing")
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            elif self._state == CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker is OPEN, failing immediately "
                    f"(failures: {self._failure_count})"
                )
                raise CircuitBreakerError(self._failure_count, self._last_error)

        # Execute the primitive
        try:
            result = await self.primitive.execute(input_data, context)
            await self._on_success()
            return result
        except self.config.expected_exception as e:
            await self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.recovery_timeout

    async def _on_success(self) -> None:
        """Handle successful execution."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    f"Circuit breaker success in HALF_OPEN "
                    f"({self._success_count}/{self.config.success_threshold})"
                )

                if self._success_count >= self.config.success_threshold:
                    logger.info("Circuit breaker closing after successful recovery")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._last_error = None
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
                self._last_error = None

    async def _on_failure(self, error: Exception) -> None:
        """Handle failed execution."""
        async with self._lock:
            self._last_error = error
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN reopens the circuit
                logger.warning("Circuit breaker reopening after HALF_OPEN failure")
                self._state = CircuitState.OPEN
                self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                logger.warning(
                    f"Circuit breaker failure {self._failure_count}/{self.config.failure_threshold}"
                )

                if self._failure_count >= self.config.failure_threshold:
                    logger.error(
                        f"Circuit breaker opening after {self._failure_count} consecutive failures"
                    )
                    self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_error = None
        logger.info("Circuit breaker manually reset to CLOSED")


# ---------------------------------------------------------------------------
# Legacy utilities (formerly in circuit_breaker.py)
# ---------------------------------------------------------------------------


class ErrorCategory(Enum):
    """Categories of development errors."""

    NETWORK = "network"  # Network/API failures
    RATE_LIMIT = "rate_limit"  # Rate limiting
    RESOURCE = "resource"  # Resource exhaustion
    TRANSIENT = "transient"  # Temporary failures
    PERMANENT = "permanent"  # Permanent failures


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    LOW = "low"  # Minor issues, can continue
    MEDIUM = "medium"  # Significant but recoverable
    HIGH = "high"  # Critical, requires attention
    CRITICAL = "critical"  # System-breaking


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")


def classify_error(error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
    """
    Classify an error into category and severity.

    Args:
        error: The exception to classify

    Returns:
        Tuple of (category, severity)
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    if any(
        x in error_str or x in error_type
        for x in [
            "connection",
            "timeout",
            "network",
            "unreachable",
            "connectionerror",
            "timeouterror",
        ]
    ):
        return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM

    if any(x in error_str for x in ["rate limit", "too many requests", "429", "quota"]):
        return ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM

    if any(
        x in error_str or x in error_type
        for x in ["memory", "disk", "resource", "out of memory", "no space"]
    ):
        return ErrorCategory.RESOURCE, ErrorSeverity.HIGH

    if any(x in error_str for x in ["temporary", "unavailable", "503", "502", "504"]):
        return ErrorCategory.TRANSIENT, ErrorSeverity.MEDIUM

    return ErrorCategory.PERMANENT, ErrorSeverity.HIGH


def should_retry(error: Exception, attempt: int, max_retries: int) -> bool:
    """
    Determine if an error should be retried.

    Args:
        error: The exception that occurred
        attempt: Current attempt number (0-indexed)
        max_retries: Maximum number of retries allowed

    Returns:
        True if should retry, False otherwise
    """
    if attempt >= max_retries:
        return False

    category, severity = classify_error(error)

    if category == ErrorCategory.PERMANENT and severity == ErrorSeverity.CRITICAL:
        return False

    return category in [
        ErrorCategory.NETWORK,
        ErrorCategory.RATE_LIMIT,
        ErrorCategory.TRANSIENT,
    ]


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay before next retry using exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    import random

    delay = min(config.base_delay * (config.exponential_base**attempt), config.max_delay)
    if config.jitter:
        delay *= 0.5 + random.random()
    return delay


def with_retry(
    config: RetryConfig | None = None, fallback: Callable[..., T] | None = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to add retry logic to a function.

    Args:
        config: Retry configuration (uses defaults if None)
        fallback: Optional fallback function to call if all retries fail

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    category, severity = classify_error(e)

                    if not should_retry(e, attempt, config.max_retries):
                        _legacy_logger.error(
                            f"{func.__name__} failed permanently: {e} "
                            f"(category={category.value}, severity={severity.value})"
                        )
                        break

                    delay = calculate_delay(attempt, config)
                    _legacy_logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            if fallback:
                _legacy_logger.info(
                    f"{func.__name__} using fallback after {config.max_retries} retries"
                )
                return fallback(*args, **kwargs)

            if last_error is not None:
                raise last_error
            raise RuntimeError(f"{func.__name__} failed without capturing an error")

        return wrapper

    return decorator


def with_retry_async(
    config: RetryConfig | None = None, fallback: Callable[..., T] | None = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Async version of with_retry decorator.

    Args:
        config: Retry configuration (uses defaults if None)
        fallback: Optional async fallback function to call if all retries fail

    Returns:
        Decorated async function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)  # type: ignore[misc]
                except Exception as e:
                    last_error = e
                    category, severity = classify_error(e)

                    if not should_retry(e, attempt, config.max_retries):
                        _legacy_logger.error(
                            f"{func.__name__} failed permanently: {e} "
                            f"(category={category.value}, severity={severity.value})"
                        )
                        break

                    delay = calculate_delay(attempt, config)
                    _legacy_logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

            if fallback:
                _legacy_logger.info(
                    f"{func.__name__} using fallback after {config.max_retries} retries"
                )
                return await fallback(*args, **kwargs)  # type: ignore[misc]

            if last_error is not None:
                raise last_error
            raise RuntimeError(f"{func.__name__} failed without capturing an error")

        return wrapper  # type: ignore[return-value]

    return decorator


class CircuitBreaker:
    """
    Simple circuit breaker pattern for preventing cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service recovered

    For use in workflows, prefer :class:`CircuitBreakerPrimitive` instead.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"

    def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Call function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            _legacy_logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
