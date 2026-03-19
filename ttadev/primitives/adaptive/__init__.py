"""Adaptive/Self-Improving Primitives Module.

This module provides primitives that learn from observability data and adapt
their strategies over time while maintaining safety and validation.

Key Components:
    AdaptivePrimitive: Base class for self-improving primitives
    AdaptiveRetryPrimitive: Retry primitive that learns optimal strategies
    LearningStrategy: Represents a learned strategy with metrics
    StrategyMetrics: Performance tracking for strategies
    LearningMode: Controls learning behavior and safety
Example - Basic Adaptive Retry:
    ```python
    from ttadev.primitives.adaptive import (
        AdaptiveRetryPrimitive,
        LearningMode,
    )
    from ttadev.primitives.core.base import WorkflowContext

    # Create adaptive retry that learns from execution patterns
    adaptive_retry = AdaptiveRetryPrimitive(
        target_primitive=my_api_service,
        learning_mode=LearningMode.VALIDATE,  # Only use validated strategies
    )

    # Use it - learning happens automatically
    context = WorkflowContext(
        correlation_id="req-123",
        metadata={"environment": "production", "priority": "high"}
    )
    result = await adaptive_retry.execute(input_data, context)

    # Strategies are automatically learned and validated before adoption
    ```

Example - Custom Adaptive Primitive:
    ```python
    from ttadev.primitives.adaptive import AdaptivePrimitive, LearningMode
    from ttadev.primitives.core.base import WorkflowContext

    class AdaptiveCachePrimitive(AdaptivePrimitive[dict, dict]):
        \"\"\"Cache primitive that learns optimal TTL and size.\"\"\"

        async def _execute_impl(
            self,
            input_data: dict,
            context: WorkflowContext
        ) -> dict:
            # Your caching logic with adaptive TTL/size
            strategy = await self._select_strategy(context)
            ttl = strategy.parameters.get("ttl", 3600)
            # ... use learned TTL
            return result

        async def _consider_new_strategy(
            self,
            context: WorkflowContext,
            execution_time: float,
            success: bool
        ) -> None:
            # Learn optimal TTL from cache hit rates
            if success and execution_time < 0.1:  # Fast = good cache
                await self._create_strategy(
                    "fast_cache",
                    {"ttl": 7200},  # Increase TTL
                    context
                )
    ```
"""

from .base import AdaptivePrimitive, LearningMode, LearningStrategy, StrategyMetrics
from .cache import AdaptiveCachePrimitive
from .exceptions import (
    AdaptiveError,
    CircuitBreakerError,
    ContextExtractionError,
    LearningError,
    PerformanceRegressionError,
    StrategyAdaptationError,
    StrategyNotFoundError,
    StrategyValidationError,
    ValidationWindowError,
)
from .fallback import AdaptiveFallbackPrimitive
from .metrics import AdaptiveMetrics, get_adaptive_metrics, reset_adaptive_metrics
from .retry import AdaptiveRetryPrimitive
from .timeout import AdaptiveTimeoutPrimitive

__all__ = [
    # Core classes
    "AdaptivePrimitive",
    "AdaptiveRetryPrimitive",
    "AdaptiveCachePrimitive",
    "AdaptiveFallbackPrimitive",
    "AdaptiveTimeoutPrimitive",
    "LearningStrategy",
    "StrategyMetrics",
    "LearningMode",
    # Custom exceptions
    "AdaptiveError",
    "LearningError",
    "StrategyValidationError",
    "StrategyAdaptationError",
    "CircuitBreakerError",
    "ContextExtractionError",
    "StrategyNotFoundError",
    "ValidationWindowError",
    "PerformanceRegressionError",
    # Metrics
    "AdaptiveMetrics",
    "get_adaptive_metrics",
    "reset_adaptive_metrics",
]

__version__ = "0.1.0"
