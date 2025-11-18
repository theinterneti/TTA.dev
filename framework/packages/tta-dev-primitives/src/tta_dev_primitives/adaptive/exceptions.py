"""Custom exceptions for adaptive/self-improving primitives.

This module defines domain-specific exceptions that provide clear error
messages and enable proper error handling in adaptive primitive workflows.

Exception Hierarchy:
    AdaptiveError (base)
    ├── LearningError - Issues during learning process
    │   ├── StrategyValidationError - Strategy validation failures
    │   └── StrategyAdaptationError - Strategy adaptation failures
    ├── CircuitBreakerError - Circuit breaker activation
    └── ContextExtractionError - Context extraction failures

Usage:
    from tta_dev_primitives.adaptive.exceptions import (
        LearningError,
        CircuitBreakerError,
        StrategyValidationError
    )

    # Raise when learning fails
    raise LearningError("Failed to learn new strategy: insufficient data")

    # Raise when circuit breaker activates
    raise CircuitBreakerError("Circuit breaker active: too many failures")

    # Raise when strategy validation fails
    raise StrategyValidationError(
        "Strategy validation failed: success rate below threshold"
    )
"""

from __future__ import annotations


class AdaptiveError(Exception):
    """Base exception for all adaptive primitive errors.

    All custom exceptions in the adaptive module inherit from this base class,
    making it easy to catch all adaptive-related errors with a single except clause.
    """

    pass


class LearningError(AdaptiveError):
    """Raised when the learning process encounters an error.

    This exception indicates that the adaptive primitive failed to learn
    from observability data, create new strategies, or update existing strategies.

    Examples:
        - Insufficient training data
        - Invalid performance metrics
        - Learning algorithm failure
        - Strategy creation errors
    """

    pass


class StrategyValidationError(LearningError):
    """Raised when strategy validation fails.

    This exception is raised when a learned strategy fails validation checks
    before being adopted for production use.

    Examples:
        - Success rate below threshold
        - Performance worse than baseline
        - Insufficient validation attempts
        - Context mismatch
    """

    pass


class StrategyAdaptationError(LearningError):
    """Raised when strategy adaptation fails.

    This exception indicates that the primitive failed to adapt an existing
    strategy based on new observability data.

    Examples:
        - Parameter adjustment failure
        - Invalid strategy parameters
        - Conflicting performance metrics
        - Adaptation threshold not met
    """

    pass


class CircuitBreakerError(AdaptiveError):
    """Raised when the circuit breaker is activated.

    This exception is raised when the circuit breaker detects too many
    failures and temporarily disables learning to prevent cascade failures.

    The circuit breaker activates when:
    - Failure rate exceeds threshold (default 50%)
    - Too many consecutive failures
    - System resource exhaustion
    - Learning overhead too high

    The circuit breaker will reset automatically after a cooldown period.
    """

    def __init__(
        self,
        message: str = "Circuit breaker active",
        failure_rate: float | None = None,
        cooldown_seconds: float | None = None,
    ) -> None:
        """Initialize circuit breaker error with additional context.

        Args:
            message: Error message
            failure_rate: The failure rate that triggered the circuit breaker
            cooldown_seconds: How long until the circuit breaker resets
        """
        self.failure_rate = failure_rate
        self.cooldown_seconds = cooldown_seconds

        # Enhance message with context if available
        if failure_rate is not None:
            message = f"{message} (failure_rate={failure_rate:.1%})"
        if cooldown_seconds is not None:
            message = f"{message} (resets in {cooldown_seconds}s)"

        super().__init__(message)


class ContextExtractionError(AdaptiveError):
    """Raised when context extraction fails.

    This exception is raised when the context extractor function fails to
    extract a valid context key from input data and workflow context.

    Examples:
        - Missing required metadata
        - Invalid context extractor function
        - Context extractor raised exception
        - Malformed context key
    """

    pass


class StrategyNotFoundError(AdaptiveError):
    """Raised when a requested strategy cannot be found.

    This exception is raised when attempting to retrieve a strategy by name
    that doesn't exist in the strategy registry.

    Examples:
        - Strategy name doesn't exist
        - Strategy was removed/expired
        - Typo in strategy name
        - Strategy not yet learned
    """

    def __init__(self, strategy_name: str, available_strategies: list[str] | None = None) -> None:
        """Initialize strategy not found error with helpful context.

        Args:
            strategy_name: The name of the strategy that wasn't found
            available_strategies: Optional list of available strategy names
        """
        self.strategy_name = strategy_name
        self.available_strategies = available_strategies

        message = f"Strategy '{strategy_name}' not found"
        if available_strategies:
            message = f"{message}. Available strategies: {', '.join(available_strategies)}"

        super().__init__(message)


class ValidationWindowError(LearningError):
    """Raised when validation window requirements are not met.

    This exception is raised when there's insufficient data in the validation
    window to make reliable decisions about strategy performance.

    Examples:
        - Not enough executions in window
        - Window size too small
        - All executions failed
        - Inconsistent validation results
    """

    pass


class PerformanceRegressionError(StrategyValidationError):
    """Raised when a new strategy performs worse than the baseline.

    This exception is raised when validation detects that a learned strategy
    has worse performance characteristics than the baseline strategy.

    Examples:
        - Higher latency than baseline
        - Lower success rate than baseline
        - Increased resource usage
        - Failed performance comparison
    """

    def __init__(
        self,
        strategy_name: str,
        metric_name: str,
        strategy_value: float,
        baseline_value: float,
    ) -> None:
        """Initialize performance regression error with metric details.

        Args:
            strategy_name: Name of the underperforming strategy
            metric_name: The metric that regressed (e.g., "success_rate")
            strategy_value: The strategy's metric value
            baseline_value: The baseline's metric value
        """
        self.strategy_name = strategy_name
        self.metric_name = metric_name
        self.strategy_value = strategy_value
        self.baseline_value = baseline_value

        message = (
            f"Strategy '{strategy_name}' shows performance regression: "
            f"{metric_name}={strategy_value:.3f} < baseline={baseline_value:.3f}"
        )

        super().__init__(message)


# Export all exceptions
__all__ = [
    "AdaptiveError",
    "LearningError",
    "StrategyValidationError",
    "StrategyAdaptationError",
    "CircuitBreakerError",
    "ContextExtractionError",
    "StrategyNotFoundError",
    "ValidationWindowError",
    "PerformanceRegressionError",
]
