"""Adaptive/Self-Improving Primitives Module.

This module provides primitives that learn from observability data and adapt
their strategies over time while maintaining safety and validation.

Key Components:
    AdaptivePrimitive: Base class for self-improving primitives
    AdaptiveRetryPrimitive: Retry primitive that learns optimal strategies
    LearningStrategy: Represents a learned strategy with metrics
    StrategyMetrics: Performance tracking for strategies
    LearningMode: Controls learning behavior and safety
    LogseqStrategyIntegration: Persist strategies to knowledge base

Example - Basic Adaptive Retry:
    ```python
    from tta_dev_primitives.adaptive import (
        AdaptiveRetryPrimitive,
        LearningMode,
        LogseqStrategyIntegration
    )
    from tta_dev_primitives.core.base import WorkflowContext

    # Create Logseq integration for automatic knowledge base persistence
    logseq = LogseqStrategyIntegration("my_service")

    # Create adaptive retry that learns and persists strategies
    adaptive_retry = AdaptiveRetryPrimitive(
        target_primitive=my_api_service,
        learning_mode=LearningMode.VALIDATE,  # Only use validated strategies
        logseq_integration=logseq,
        enable_auto_persistence=True  # Auto-save learned strategies
    )

    # Use it - learning happens automatically
    context = WorkflowContext(
        correlation_id="req-123",
        metadata={"environment": "production", "priority": "high"}
    )
    result = await adaptive_retry.execute(input_data, context)

    # Strategies are automatically:
    # - Learned from execution patterns
    # - Validated before adoption
    # - Persisted to Logseq knowledge base
    # - Shared across instances via KB
    ```

Example - Custom Adaptive Primitive:
    ```python
    from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningMode
    from tta_dev_primitives.core.base import WorkflowContext

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
from .logseq_integration import LogseqStrategyIntegration
from .retry import AdaptiveRetryPrimitive

__all__ = [
    "AdaptivePrimitive",
    "AdaptiveRetryPrimitive",
    "LearningStrategy",
    "StrategyMetrics",
    "LearningMode",
    "LogseqStrategyIntegration",
]

__version__ = "0.1.0"
