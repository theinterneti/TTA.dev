"""Caching primitive for workflow results."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
U = TypeVar("U")


class CachePrimitive(WorkflowPrimitive[T, U]):
    """
    Cache primitive execution results.

    Dramatically reduces costs and latency by caching expensive operations
    like LLM calls. Typical cache hit rates of 60-80% translate to 40%+ cost
    reduction in production.

    Example:
        ```python
        # Cache expensive LLM calls
        cached_llm = CachePrimitive(
            primitive=expensive_llm_call,
            cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.state.get('player_id')}",
            ttl_seconds=3600.0  # 1 hour TTL
        )

        # Cache with custom key generation
        cached = CachePrimitive(
            primitive=world_builder,
            cache_key_fn=lambda data, ctx: (
                f"{data['theme']}:{data['setting']}:{ctx.session_id}"
            ),
            ttl_seconds=1800.0  # 30 minutes
        )

        # Short-lived cache for rapid iterations
        cached = CachePrimitive(
            primitive=validation_check,
            cache_key_fn=lambda data, ctx: str(hash(str(data))),
            ttl_seconds=60.0  # 1 minute
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive[T, U],
        ttl_seconds: int,
        cache_key_fn: Callable[[T, WorkflowContext], str] | None = None,
    ) -> None:
        """
        Initialize cache primitive.

        Args:
            primitive: Primitive to cache
            cache_key_fn: Function to generate cache key from input/context
            ttl_seconds: Time-to-live for cached values (default 1 hour)
        """
        self.primitive = primitive
        if cache_key_fn is None:
            # Default cache key fn, updated to use state
            self.cache_key_fn = (
                lambda data,
                ctx: f"{data.get('prompt', '')}:{ctx.state.get('player_id', 'unknown')}"
            )
        else:
            self.cache_key_fn = cache_key_fn
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "expirations": 0,
        }

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute with caching.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Cached or freshly computed result
        """
        # Generate cache key
        cache_key = self.cache_key_fn(input_data, context)

        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            age = time.time() - timestamp

            if age < self.ttl_seconds:
                # Cache hit
                self._stats["hits"] += 1

                logger.info(
                    "cache_hit",
                    key=cache_key[:50],  # Truncate long keys
                    age_seconds=round(age, 2),
                    ttl=self.ttl_seconds,
                    hit_rate=self.get_hit_rate(),
                    workflow_id=context.workflow_id,
                )

                # Track cache hits in context
                if "cache_hits" not in context.state:
                    context.state["cache_hits"] = 0
                context.state["cache_hits"] += 1

                return result
            else:
                # Cache expired
                self._stats["expirations"] += 1
                logger.debug(
                    "cache_expired",
                    key=cache_key[:50],
                    age=round(age, 2),
                    ttl=self.ttl_seconds,
                )
                del self._cache[cache_key]

        # Cache miss - execute and store
        self._stats["misses"] += 1

        logger.info(
            "cache_miss",
            key=cache_key[:50],
            cache_size=len(self._cache),
            hit_rate=self.get_hit_rate(),
            workflow_id=context.workflow_id,
        )

        # Track cache misses in context
        if "cache_misses" not in context.state:
            context.state["cache_misses"] = 0
        context.state["cache_misses"] += 1

        # Execute primitive
        result = await self.primitive.execute(input_data, context)

        # Store in cache
        self._cache[cache_key] = (result, time.time())

        logger.debug(
            "cache_store",
            key=cache_key[:50],
            cache_size=len(self._cache),
        )

        return result

    def clear_cache(self) -> None:
        """Clear all cached values."""
        size = len(self._cache)
        self._cache.clear()
        logger.info("cache_cleared", previous_size=size)

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        return {
            "size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "expirations": self._stats["expirations"],
            "hit_rate": self.get_hit_rate(),
        }

    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Hit rate as percentage (0-100)
        """
        total = self._stats["hits"] + self._stats["misses"]
        if total == 0:
            return 0.0
        return round((self._stats["hits"] / total) * 100, 2)

    def evict_expired(self) -> int:
        """
        Manually evict expired cache entries.

        Returns:
            Number of entries evicted
        """
        now = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._cache.items()
            if now - timestamp >= self.ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1

        if expired_keys:
            logger.info("cache_eviction", count=len(expired_keys))

        return len(expired_keys)
