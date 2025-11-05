#!/usr/bin/env python3
"""
Error Recovery Framework for Development Scripts.

This module provides error recovery patterns for development automation,
implementing the agentic primitive of error handling and recovery at the
meta-level (development process) before integrating into the product.

Features:
- Error classification (network, rate limit, transient, permanent)
- Automatic retry with exponential backoff
- Fallback strategies
- Circuit breaker pattern
- Comprehensive error logging
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


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

    def __post_init__(self):
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

    # Network errors
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

    # Rate limiting
    if any(x in error_str for x in ["rate limit", "too many requests", "429", "quota"]):
        return ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM

    # Resource errors
    if any(
        x in error_str or x in error_type
        for x in ["memory", "disk", "resource", "out of memory", "no space"]
    ):
        return ErrorCategory.RESOURCE, ErrorSeverity.HIGH

    # Transient errors
    if any(x in error_str for x in ["temporary", "unavailable", "503", "502", "504"]):
        return ErrorCategory.TRANSIENT, ErrorSeverity.MEDIUM

    # Default to permanent
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

    # Don't retry critical permanent errors
    if category == ErrorCategory.PERMANENT and severity == ErrorSeverity.CRITICAL:
        return False

    # Retry network, rate limit, and transient errors
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

    # Exponential backoff
    delay = min(
        config.base_delay * (config.exponential_base**attempt), config.max_delay
    )

    # Add jitter to prevent thundering herd
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

    Example:
        @with_retry(RetryConfig(max_retries=3))
        def flaky_function():
            # May fail transiently
            pass

        @with_retry(fallback=lambda: "default_value")
        def function_with_fallback():
            # Will return "default_value" if all retries fail
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    category, severity = classify_error(e)

                    if not should_retry(e, attempt, config.max_retries):
                        logger.error(
                            f"{func.__name__} failed permanently: {e} "
                            f"(category={category.value}, severity={severity.value})"
                        )
                        break

                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}. "
                        f"Category: {category.value}, Severity: {severity.value}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

            # All retries exhausted
            if fallback:
                logger.info(
                    f"{func.__name__} using fallback after {config.max_retries} retries"
                )
                return fallback(*args, **kwargs)

            # Re-raise the last error
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

    Example:
        @with_retry_async(RetryConfig(max_retries=3))
        async def async_flaky_function():
            # May fail transiently
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)  # type: ignore[misc]
                except Exception as e:
                    last_error = e
                    category, severity = classify_error(e)

                    if not should_retry(e, attempt, config.max_retries):
                        logger.error(
                            f"{func.__name__} failed permanently: {e} "
                            f"(category={category.value}, severity={severity.value})"
                        )
                        break

                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}. "
                        f"Category: {category.value}, Severity: {severity.value}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)

            # All retries exhausted
            if fallback:
                logger.info(
                    f"{func.__name__} using fallback after {config.max_retries} retries"
                )
                return await fallback(*args, **kwargs)  # type: ignore[misc]

            # Re-raise the last error
            if last_error is not None:
                raise last_error
            raise RuntimeError(f"{func.__name__} failed without capturing an error")

        return wrapper  # type: ignore[return-value]

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service recovered
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
                raise Exception(
                    f"Circuit breaker is OPEN (failures: {self.failure_count})"
                )

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
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
