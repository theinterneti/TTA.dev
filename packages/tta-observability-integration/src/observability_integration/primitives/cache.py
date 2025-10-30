"""
CachePrimitive - Redis-based caching workflow primitive.

Implements caching layer for expensive LLM calls with TTL-based expiration,
hit/miss tracking, and cost savings calculations.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from typing import Any

try:
    from tta_dev_primitives.core.base import (
        WorkflowContext,
        WorkflowPrimitive,
    )
except ImportError:
    # Fallback for development/testing
    from typing import Protocol

    class WorkflowContext:  # type: ignore
        """Mock WorkflowContext for testing."""

        pass

    class WorkflowPrimitive(Protocol):  # type: ignore
        """Minimal WorkflowPrimitive protocol for testing."""

        pass


from ..apm_setup import get_meter

logger = logging.getLogger(__name__)


class CachePrimitive(WorkflowPrimitive[Any, Any]):
    """
    Cache primitive with Redis backend and comprehensive metrics tracking.

    Caches results from expensive LLM operations to reduce API costs.
    Tracks cache hit/miss rates, latencies, and cost savings.

    Example:
        >>> from observability_integration.primitives import CachePrimitive
        >>> import redis
        >>>
        >>> # Create cache wrapper
        >>> redis_client = redis.Redis.from_url("redis://localhost:6379")
        >>> cache = CachePrimitive(
        ...     primitive=GPT4Primitive(),
        ...     cache_key_fn=lambda data, ctx: data.get("prompt", "")[:50],
        ...     ttl_seconds=3600,  # 1 hour
        ...     redis_client=redis_client,
        ... )
        >>>
        >>> # Use in workflow
        >>> result = await cache.execute({"prompt": "Hello world"}, context)
        >>> # Second call with same prompt will be cached (instant, no cost)
        >>> result2 = await cache.execute({"prompt": "Hello world"}, context)

    Metrics:
        - cache_hits_total{operation}: Total cache hits
        - cache_misses_total{operation}: Total cache misses
        - cache_hit_rate{operation}: Cache hit rate (0.0-1.0)
        - cache_latency_seconds{operation, hit}: Cache operation latency
        - cache_cost_savings_usd{operation}: Estimated cost savings
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        cache_key_fn: Callable[[Any, WorkflowContext], str],
        ttl_seconds: float = 3600.0,
        redis_client: Any | None = None,
        cost_per_call: float = 0.01,  # Default: $0.01 per LLM call
        operation_name: str | None = None,
    ):
        """
        Initialize cache primitive.

        Args:
            primitive: Primitive to wrap with caching
            cache_key_fn: Function to generate cache key from input
            ttl_seconds: Time-to-live for cached values (default: 1 hour)
            redis_client: Redis client instance (None = no caching, pass-through)
            cost_per_call: Estimated cost per uncached call (for savings calc)
            operation_name: Name for metrics (default: primitive class name)

        Example:
            >>> def cache_key_from_prompt(data, context):
            ...     prompt = data.get("prompt", "")
            ...     # Use first 50 chars + hash for consistent keys
            ...     return f"llm:{prompt[:50]}:{hash(prompt)}"
        """
        self.primitive = primitive
        self.cache_key_fn = cache_key_fn
        self.ttl_seconds = ttl_seconds
        self.redis_client = redis_client
        self.cost_per_call = cost_per_call
        self.operation_name = operation_name or primitive.__class__.__name__

        # Track statistics for hit rate calculation
        self._total_hits = 0
        self._total_misses = 0

        # Initialize metrics (gracefully handles meter=None)
        meter = get_meter(__name__)
        if meter:
            self._hits_counter = meter.create_counter(
                name="cache_hits_total",
                description="Total cache hits",
                unit="1",
            )
            self._misses_counter = meter.create_counter(
                name="cache_misses_total",
                description="Total cache misses",
                unit="1",
            )
            self._latency_histogram = meter.create_histogram(
                name="cache_latency_seconds",
                description="Cache operation latency",
                unit="s",
            )
            self._cost_savings_counter = meter.create_counter(
                name="cache_cost_savings_usd",
                description="Estimated cost savings from caching",
                unit="USD",
            )

            # Observable gauge for hit rate (updated on each operation)
            def get_hit_rate() -> float:
                total = self._total_hits + self._total_misses
                return self._total_hits / total if total > 0 else 0.0

            self._hit_rate_gauge = meter.create_observable_gauge(
                name="cache_hit_rate",
                description="Cache hit rate (0.0-1.0)",
                callbacks=[lambda options: [(get_hit_rate(), {"operation": self.operation_name})]],
            )
        else:
            self._hits_counter = None
            self._misses_counter = None
            self._latency_histogram = None
            self._cost_savings_counter = None
            self._hit_rate_gauge = None

        if redis_client:
            logger.info(
                f"CachePrimitive initialized for '{self.operation_name}' "
                f"(TTL: {ttl_seconds}s, Redis: enabled)"
            )
        else:
            logger.warning(
                f"CachePrimitive initialized for '{self.operation_name}' "
                f"without Redis - caching disabled (pass-through mode)"
            )

    def _generate_cache_key(self, input_data: Any, context: WorkflowContext) -> str:
        """
        Generate cache key from input data.

        Args:
            input_data: Input data for the workflow
            context: Workflow execution context

        Returns:
            Cache key string (safe for Redis)
        """
        try:
            # Use provided cache key function
            base_key = self.cache_key_fn(input_data, context)

            # Ensure key is safe for Redis (no spaces, limited length)
            safe_key = base_key.replace(" ", "_").replace("\n", "_")

            # Add hash suffix if key is too long
            if len(safe_key) > 200:
                key_hash = hashlib.sha256(safe_key.encode()).hexdigest()[:16]
                safe_key = f"{safe_key[:180]}_{key_hash}"

            return f"cache:{self.operation_name}:{safe_key}"

        except Exception as e:
            logger.warning(
                f"Cache key generation failed: {e}, using fallback key",
                exc_info=True,
            )
            # Fallback: hash the entire input
            fallback = hashlib.sha256(str(input_data).encode()).hexdigest()
            return f"cache:{self.operation_name}:fallback:{fallback}"

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute with caching.

        Checks cache for existing result. On cache miss, executes wrapped
        primitive and stores result in cache.

        Args:
            input_data: Input data for the workflow
            context: Workflow execution context

        Returns:
            Cached result or result from wrapped primitive

        Raises:
            Exception: Any exception from the wrapped primitive
        """
        start_time = time.time()
        cache_hit = False

        # Generate cache key
        cache_key = self._generate_cache_key(input_data, context)

        # Try to get from cache (if Redis available)
        if self.redis_client:
            try:
                cached_value = self.redis_client.get(cache_key)
                if cached_value is not None:
                    # Cache hit!
                    cache_hit = True
                    self._total_hits += 1

                    if self._hits_counter:
                        self._hits_counter.add(1, {"operation": self.operation_name})

                    if self._cost_savings_counter:
                        self._cost_savings_counter.add(
                            self.cost_per_call, {"operation": self.operation_name}
                        )

                    # Deserialize cached result
                    result = json.loads(cached_value.decode("utf-8"))

                    duration = time.time() - start_time
                    if self._latency_histogram:
                        self._latency_histogram.record(
                            duration,
                            {"operation": self.operation_name, "hit": "true"},
                        )

                    logger.debug(
                        f"Cache HIT for '{self.operation_name}' "
                        f"(key: {cache_key[:50]}..., latency: {duration * 1000:.1f}ms)"
                    )

                    return result

            except Exception as e:
                logger.warning(
                    f"Cache read failed for '{self.operation_name}': {e}, "
                    f"falling through to primitive execution",
                    exc_info=True,
                )

        # Cache miss - execute wrapped primitive
        if not cache_hit:
            self._total_misses += 1

            if self._misses_counter:
                self._misses_counter.add(1, {"operation": self.operation_name})

            logger.debug(f"Cache MISS for '{self.operation_name}' (key: {cache_key[:50]}...)")

        # Execute wrapped primitive
        result = await self.primitive.execute(input_data, context)

        # Store in cache (if Redis available)
        if self.redis_client:
            try:
                # Serialize result
                serialized = json.dumps(result).encode("utf-8")

                # Store with TTL
                self.redis_client.setex(
                    cache_key,
                    int(self.ttl_seconds),
                    serialized,
                )

                logger.debug(
                    f"Cached result for '{self.operation_name}' (TTL: {self.ttl_seconds}s)"
                )

            except Exception as e:
                logger.warning(
                    f"Cache write failed for '{self.operation_name}': {e}",
                    exc_info=True,
                )

        # Record latency
        duration = time.time() - start_time
        if self._latency_histogram:
            self._latency_histogram.record(
                duration,
                {"operation": self.operation_name, "hit": "false"},
            )

        return result

    def get_stats(self) -> dict[str, Any]:
        """
        Get current cache statistics.

        Returns:
            Dictionary with hits, misses, hit_rate, and cost_savings
        """
        total = self._total_hits + self._total_misses
        hit_rate = self._total_hits / total if total > 0 else 0.0
        cost_savings = self._total_hits * self.cost_per_call

        return {
            "operation": self.operation_name,
            "hits": self._total_hits,
            "misses": self._total_misses,
            "total": total,
            "hit_rate": hit_rate,
            "cost_savings_usd": cost_savings,
        }

    def __repr__(self) -> str:
        """String representation of cache."""
        stats = self.get_stats()
        return (
            f"CachePrimitive(operation='{self.operation_name}', "
            f"hit_rate={stats['hit_rate']:.1%}, "
            f"hits={stats['hits']}, misses={stats['misses']})"
        )
