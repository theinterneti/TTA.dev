"""Adaptive cache primitive that learns optimal caching parameters.

# See: [[TTA.dev/Primitives/AdaptiveCachePrimitive]]
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger
from .base import AdaptivePrimitive, LearningMode, LearningStrategy, StrategyMetrics
from .logseq_integration import LogseqStrategyIntegration

logger = get_logger(__name__)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class AdaptiveCachePrimitive(AdaptivePrimitive[TInput, TOutput], Generic[TInput, TOutput]):
    """
    Cache primitive that learns optimal TTL and size parameters.

    Learns from execution patterns to optimize:
    - TTL (time-to-live) for different contexts
    - Maximum cache size to balance memory vs hit rate
    - Eviction strategies

    Example:
        ```python
        from tta_dev_primitives.adaptive import (
            AdaptiveCachePrimitive,
            LogseqStrategyIntegration,
            LearningMode
        )

        # Create adaptive cache that learns optimal TTL
        logseq = LogseqStrategyIntegration("llm_service")
        adaptive_cache = AdaptiveCachePrimitive(
            target_primitive=expensive_llm,
            cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.user_id}",
            logseq_integration=logseq,
            enable_auto_persistence=True,
            learning_mode=LearningMode.ACTIVE
        )

        # Use it - will learn optimal TTL per context
        result = await adaptive_cache.execute({"prompt": "..."}, context)

        # Check learned strategies
        for name, strategy in adaptive_cache.strategies.items():
            print(f"{name}: TTL={strategy.parameters['ttl_seconds']}s")
        ```

    The primitive tracks:
    - Cache hit rate per context
    - Average age of cache hits
    - Memory usage vs performance trade-off

    And learns:
    - Optimal TTL values (queries that benefit from longer/shorter TTL)
    - Optimal cache size limits
    - Context-specific caching strategies
    """

    def __init__(
        self,
        target_primitive: WorkflowPrimitive[TInput, TOutput],
        cache_key_fn: Callable[[TInput, WorkflowContext], str],
        learning_mode: LearningMode = LearningMode.VALIDATE,
        max_strategies: int = 8,
        logseq_integration: LogseqStrategyIntegration | None = None,
        enable_auto_persistence: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize adaptive cache primitive.

        Args:
            target_primitive: Primitive to cache
            cache_key_fn: Function to generate cache key from input/context
            learning_mode: Learning mode (DISABLED, OBSERVE, VALIDATE, ACTIVE)
            max_strategies: Maximum number of strategies to maintain
            logseq_integration: Optional Logseq integration for persistence
            enable_auto_persistence: Auto-persist strategies to Logseq
            **kwargs: Additional arguments for AdaptivePrimitive
        """
        super().__init__(
            learning_mode=learning_mode,
            max_strategies=max_strategies,
            **kwargs,
        )

        self.target_primitive = target_primitive
        self.cache_key_fn = cache_key_fn
        self.logseq_integration = logseq_integration
        self.enable_auto_persistence = enable_auto_persistence

        # Cache storage: key -> (value, timestamp, context_key)
        self._cache: dict[str, tuple[TOutput, float, str]] = {}

        # Performance tracking per context
        self._context_metrics: dict[str, dict[str, Any]] = {}

        # Initialize baseline strategy
        self.baseline_strategy = self._get_default_strategy()
        self.strategies[self.baseline_strategy.name] = self.baseline_strategy

    def _get_default_strategy(self) -> LearningStrategy:
        """
        Get the default baseline caching strategy.

        Returns:
            Baseline strategy with conservative TTL and size limits
        """
        return LearningStrategy(
            name="baseline_conservative",
            description="Conservative caching with 1-hour TTL",
            parameters={
                "ttl_seconds": 3600.0,  # 1 hour default
                "max_cache_size": 1000,  # Reasonable default
                "min_hit_rate": 0.3,  # 30% hit rate minimum to keep caching
            },
            context_pattern="*",
        )

    async def _execute_with_strategy(
        self,
        input_data: TInput,
        context: WorkflowContext,
        strategy: LearningStrategy,
    ) -> TOutput:
        """
        Execute caching with the given strategy.

        Args:
            input_data: Input data
            context: Workflow context
            strategy: Strategy containing TTL and cache size parameters

        Returns:
            Cached or freshly computed result
        """
        start_time = time.time()

        # Extract strategy parameters
        ttl_seconds = strategy.parameters.get("ttl_seconds", 3600.0)
        max_cache_size = strategy.parameters.get("max_cache_size", 1000)

        # Generate cache key
        cache_key = self.cache_key_fn(input_data, context)
        context_key = self.context_extractor(input_data, context)

        # Initialize context metrics if needed
        if context_key not in self._context_metrics:
            self._context_metrics[context_key] = {
                "hits": 0,
                "misses": 0,
                "total_hit_age": 0.0,
                "executions": 0,
            }

        metrics = self._context_metrics[context_key]
        metrics["executions"] += 1

        # Check cache
        if cache_key in self._cache:
            cached_value, timestamp, _ = self._cache[cache_key]
            age = time.time() - timestamp

            if age < ttl_seconds:
                # Cache hit!
                metrics["hits"] += 1
                metrics["total_hit_age"] += age

                latency = time.time() - start_time

                logger.info(
                    "adaptive_cache_hit",
                    strategy=strategy.name,
                    cache_key=cache_key[:50],
                    age_seconds=round(age, 2),
                    ttl_seconds=ttl_seconds,
                    hit_rate=self._get_hit_rate(context_key),
                    context_key=context_key,
                )

                # Update strategy metrics
                strategy.metrics.update(success=True, latency=latency, context_key=context_key)

                return cached_value
            else:
                # Expired - remove from cache
                del self._cache[cache_key]
                logger.debug(
                    "adaptive_cache_expired",
                    cache_key=cache_key[:50],
                    age_seconds=round(age, 2),
                    ttl_seconds=ttl_seconds,
                )

        # Cache miss - execute primitive
        metrics["misses"] += 1

        logger.info(
            "adaptive_cache_miss",
            strategy=strategy.name,
            cache_key=cache_key[:50],
            cache_size=len(self._cache),
            context_key=context_key,
        )

        # Execute the target primitive
        result = await self.target_primitive.execute(input_data, context)
        execution_latency = time.time() - start_time

        # Update strategy metrics (miss counts as success if execution worked)
        strategy.metrics.update(success=True, latency=execution_latency, context_key=context_key)

        # Store in cache (with eviction if needed)
        if len(self._cache) >= max_cache_size:
            # Evict oldest entry
            oldest_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
            del self._cache[oldest_key]
            logger.debug("adaptive_cache_eviction", evicted_key=oldest_key[:50])

        self._cache[cache_key] = (result, time.time(), context_key)

        return result

    async def _consider_new_strategy(
        self,
        input_data: TInput,
        context: WorkflowContext,
        current_performance: StrategyMetrics,
    ) -> LearningStrategy | None:
        """
        Consider creating a new strategy based on cache performance.

        Analyzes:
        - Hit rate trends
        - Average age of cache hits (indicates if TTL is too long/short)
        - Memory pressure (cache size vs hit rate)

        Args:
            input_data: Current input data
            context: Current workflow context
            current_performance: Current strategy performance

        Returns:
            New strategy if improvement is possible, None otherwise
        """
        context_key = self.context_extractor(input_data, context)

        if context_key not in self._context_metrics:
            return None

        metrics = self._context_metrics[context_key]

        # Need enough data to make decisions
        if metrics["executions"] < 20:
            return None

        hit_rate = self._get_hit_rate(context_key)
        avg_hit_age = metrics["total_hit_age"] / metrics["hits"] if metrics["hits"] > 0 else 0.0

        # Current strategy TTL
        context_key = self.context_extractor(input_data, context)
        current_strategy = self._select_strategy(context_key)
        current_ttl = current_strategy.parameters.get("ttl_seconds", 3600.0)

        # Learning logic: Adjust TTL based on hit age patterns
        new_ttl = current_ttl
        reason = ""

        # If average hit age is very low (< 20% of TTL), items are reused quickly
        # -> Could use shorter TTL to save memory
        if avg_hit_age < current_ttl * 0.2 and hit_rate > 0.5:
            new_ttl = avg_hit_age * 3  # 3x the average age
            reason = f"High hit rate ({hit_rate:.1%}) with low avg age ({avg_hit_age:.0f}s) suggests shorter TTL"

        # If average hit age is high (> 60% of TTL), items are used near expiration
        # -> Could use longer TTL to improve hit rate
        elif avg_hit_age > current_ttl * 0.6 and hit_rate < 0.7:
            new_ttl = avg_hit_age * 2  # 2x the average age
            reason = f"Items used near TTL ({avg_hit_age:.0f}s) suggests longer TTL"

        # If hit rate is very low (< 30%), caching may not be beneficial
        elif hit_rate < 0.3:
            new_ttl = current_ttl * 0.5  # Reduce TTL to save memory
            reason = f"Low hit rate ({hit_rate:.1%}) suggests shorter TTL to reduce memory waste"

        # No change needed
        else:
            return None

        # Clamp TTL to reasonable bounds
        new_ttl = max(60.0, min(new_ttl, 86400.0))  # 1 minute to 24 hours

        # Only create new strategy if TTL change is significant (> 20%)
        ttl_change_ratio = abs(new_ttl - current_ttl) / current_ttl
        if ttl_change_ratio < 0.2:
            return None

        # Create new strategy
        strategy_name = f"{context_key}_ttl_{int(new_ttl)}s"
        current_cache_size = current_strategy.parameters.get("max_cache_size", 1000)
        return LearningStrategy(
            name=strategy_name,
            description=f"Learned for {context_key}: {reason}",
            parameters={
                "ttl_seconds": new_ttl,
                "max_cache_size": current_cache_size,
                "min_hit_rate": 0.3,
            },
            context_pattern=context_key,
        )

    def _get_hit_rate(self, context_key: str) -> float:
        """Calculate hit rate for a specific context."""
        if context_key not in self._context_metrics:
            return 0.0

        metrics = self._context_metrics[context_key]
        total = metrics["hits"] + metrics["misses"]
        if total == 0:
            return 0.0

        return metrics["hits"] / total

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with cache metrics including per-context stats
        """
        total_hits = sum(m["hits"] for m in self._context_metrics.values())
        total_misses = sum(m["misses"] for m in self._context_metrics.values())
        total_requests = total_hits + total_misses

        return {
            "total_size": len(self._cache),
            "total_requests": total_requests,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": total_hits / total_requests if total_requests > 0 else 0.0,
            "contexts": {
                context_key: {
                    "hits": metrics["hits"],
                    "misses": metrics["misses"],
                    "hit_rate": self._get_hit_rate(context_key),
                    "avg_hit_age": (
                        metrics["total_hit_age"] / metrics["hits"] if metrics["hits"] > 0 else 0.0
                    ),
                    "executions": metrics["executions"],
                }
                for context_key, metrics in self._context_metrics.items()
            },
            "strategies": {
                name: {
                    "ttl_seconds": strategy.parameters.get("ttl_seconds"),
                    "success_rate": strategy.metrics.success_rate,
                    "avg_latency": strategy.metrics.avg_latency,
                }
                for name, strategy in self.strategies.items()
            },
        }

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        size = len(self._cache)
        self._cache.clear()
        logger.info("adaptive_cache_cleared", previous_size=size)

    def evict_expired(self, strategy: LearningStrategy | None = None) -> int:
        """
        Evict expired cache entries based on strategy TTL.

        Args:
            strategy: Strategy to use for TTL (uses baseline if None)

        Returns:
            Number of entries evicted
        """
        if strategy is None:
            strategy = self.baseline_strategy

        ttl_seconds = strategy.parameters.get("ttl_seconds", 3600.0)
        now = time.time()

        expired_keys = [
            key for key, (_, timestamp, _) in self._cache.items() if now - timestamp >= ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info("adaptive_cache_eviction", count=len(expired_keys), ttl=ttl_seconds)

        return len(expired_keys)
