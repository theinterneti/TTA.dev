"""Adaptive/Self-Improving Primitives Module.

This module provides primitives that learn from observability data and adapt
their strategies over time while maintaining safety and validation.

Classes:
    AdaptivePrimitive: Base class for self-improving primitives
    LearningStrategy: Represents a learned strategy with metrics
    StrategyMetrics: Performance tracking for strategies
    LearningMode: Controls learning behavior and safety

Example:
    ```python
    from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive, LearningMode

    # Create an adaptive retry primitive that learns from failures
    adaptive_retry = AdaptiveRetryPrimitive(
        learning_mode=LearningMode.VALIDATE,  # Only use validated strategies
        max_strategies=5,  # Limit strategy collection
        circuit_breaker_threshold=0.7  # Fall back if >70% failures
    )

    # It will learn optimal retry strategies based on:
    # - Error types and patterns
    # - Success rates by context
    # - Latency patterns
    # - Resource usage data from observability
    ```
"""

from .base import AdaptivePrimitive, LearningMode, LearningStrategy, StrategyMetrics

__all__ = [
    "AdaptivePrimitive",
    "LearningStrategy",
    "StrategyMetrics",
    "LearningMode",
]

__version__ = "0.1.0"
