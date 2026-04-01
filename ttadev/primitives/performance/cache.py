"""Caching primitive for workflow results.

# See: [[TTA.dev/Primitives/CachePrimitive]]
"""

from __future__ import annotations

import pickle
import time
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


# ── Backend Protocol ──────────────────────────────────────────────────────────


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol for pluggable cache storage backends.

    Any object implementing ``get``, ``set``, and ``delete`` with the
    correct signatures satisfies this protocol.
    """

    async def get(self, key: str) -> Any | None:
        """Return cached value for *key*, or ``None`` on miss / expiry."""
        ...

    async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Store *value* under *key* for at most *ttl_seconds* seconds."""
        ...

    async def delete(self, key: str) -> None:
        """Remove *key* from the store (no-op if absent)."""
        ...


# ── InMemoryBackend ───────────────────────────────────────────────────────────


class InMemoryBackend:
    """Pure in-memory cache backend — no external dependencies.

    Entries expire lazily on ``get`` once their TTL has elapsed.
    Uses :func:`time.monotonic` for reliable duration measurement.
    """

    def __init__(self) -> None:
        # Maps key -> (value, expiry_monotonic)
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Any | None:
        """Return value if present and not expired, else ``None``."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.monotonic() >= expiry:
            del self._store[key]
            return None
        return value

    def has_expired(self, key: str) -> bool:
        """Return True if *key* exists in the store but is past its TTL."""
        entry = self._store.get(key)
        if entry is None:
            return False
        _, expiry = entry
        return time.monotonic() >= expiry

    async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Store *value* with an expiry derived from the current monotonic clock."""
        self._store[key] = (value, time.monotonic() + ttl_seconds)

    async def delete(self, key: str) -> None:
        """Remove *key* (no-op if absent)."""
        self._store.pop(key, None)

    def clear(self) -> int:
        """Remove all entries. Returns the count that was cleared."""
        count = len(self._store)
        self._store.clear()
        return count

    def size(self) -> int:
        """Current number of stored entries (may include not-yet-evicted items)."""
        return len(self._store)

    def evict_expired(self) -> int:
        """Proactively remove all expired entries. Returns number evicted."""
        now = time.monotonic()
        expired = [k for k, (_, expiry) in self._store.items() if now >= expiry]
        for k in expired:
            del self._store[k]
        return len(expired)


# ── RedisBackend ──────────────────────────────────────────────────────────────


class RedisBackend:
    """Async Redis cache backend using ``redis.asyncio``.

    Requires the optional ``redis`` dependency::

        pip install "ttadev[redis]"

    Values are serialised with :mod:`pickle` so arbitrary Python objects are
    supported.  All keys are prefixed to avoid collisions with other Redis
    consumers.

    Example:
        ```python
        from ttadev.primitives.performance.cache import RedisBackend, CachePrimitive

        backend = RedisBackend("redis://localhost:6379", prefix="myapp:")
        cached = CachePrimitive(
            primitive=my_primitive,
            cache_key_fn=lambda d, ctx: str(d),
            ttl_seconds=300.0,
            backend=backend,
        )
        ```
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "tta:",
    ) -> None:
        """Initialise the Redis backend.

        Args:
            url: Redis connection URL (e.g. ``redis://host:port/db``).
            prefix: Prefix prepended to every key to avoid namespace collisions.

        Raises:
            ImportError: If the ``redis`` package is not installed.
        """
        try:
            import redis.asyncio as aioredis
        except ImportError as exc:
            raise ImportError(
                "RedisBackend requires the 'redis' package. "
                "Install with: pip install 'ttadev[redis]'"
            ) from exc

        self._prefix = prefix
        self._client = aioredis.from_url(url, decode_responses=False)

    def _prefixed(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Fetch and deserialise a value from Redis."""
        data: bytes | None = await self._client.get(self._prefixed(key))
        if data is None:
            return None
        return pickle.loads(data)  # noqa: S301

    async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Serialise *value* and store it in Redis with a TTL."""
        data = pickle.dumps(value)
        ttl = max(1, int(ttl_seconds))
        await self._client.setex(self._prefixed(key), ttl, data)

    async def delete(self, key: str) -> None:
        """Remove *key* from Redis."""
        await self._client.delete(self._prefixed(key))


# ── CachePrimitive ────────────────────────────────────────────────────────────


class CachePrimitive(WorkflowPrimitive[Any, Any]):
    """Cache primitive execution results with a pluggable backend.

    Dramatically reduces costs and latency by caching expensive operations
    like LLM calls.  Typical cache hit rates of 60–80 % translate to 40 %+
    cost reduction in production.

    The default backend is :class:`InMemoryBackend` (same behaviour as before
    this change — backward compatible).  Pass a :class:`RedisBackend` instance
    for shared, persistent caching across processes.

    Example:
        ```python
        # In-memory (default) — zero configuration
        cached_llm = CachePrimitive(
            primitive=expensive_llm_call,
            cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.player_id}",
            ttl_seconds=3600.0,
        )

        # Redis-backed — shared across workers
        from ttadev.primitives.performance.cache import RedisBackend
        cached_llm = CachePrimitive(
            primitive=expensive_llm_call,
            cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.player_id}",
            ttl_seconds=3600.0,
            backend=RedisBackend("redis://localhost:6379"),
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        cache_key_fn: Callable[[Any, WorkflowContext], str],
        ttl_seconds: float = 3600.0,
        backend: CacheBackend | None = None,
    ) -> None:
        """Initialise the cache primitive.

        Args:
            primitive: Primitive whose results will be cached.
            cache_key_fn: Callable that maps ``(input_data, context)`` to a
                string cache key.
            ttl_seconds: Time-to-live for cached values (default: 1 hour).
            backend: Storage backend.  Defaults to a fresh
                :class:`InMemoryBackend` when ``None``.
        """
        self.primitive = primitive
        self.cache_key_fn = cache_key_fn
        self.ttl_seconds = ttl_seconds
        self._backend: CacheBackend = backend if backend is not None else InMemoryBackend()
        self._stats: dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "expirations": 0,
        }

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute with caching.

        Args:
            input_data: Input forwarded to the wrapped primitive on a miss.
            context: Workflow context.

        Returns:
            Cached or freshly computed result.
        """
        cache_key = self.cache_key_fn(input_data, context)

        # Check expiry before get() so we can track the expiration stat.
        if isinstance(self._backend, InMemoryBackend) and self._backend.has_expired(cache_key):
            self._stats["expirations"] += 1

        cached = await self._backend.get(cache_key)

        if cached is not None:
            self._stats["hits"] += 1
            logger.info(
                "cache_hit",
                key=cache_key[:50],
                hit_rate=self.get_hit_rate(),
                workflow_id=context.workflow_id,
            )
            if "cache_hits" not in context.state:
                context.state["cache_hits"] = 0
            context.state["cache_hits"] += 1
            return cached

        self._stats["misses"] += 1
        logger.info(
            "cache_miss",
            key=cache_key[:50],
            hit_rate=self.get_hit_rate(),
            workflow_id=context.workflow_id,
        )
        if "cache_misses" not in context.state:
            context.state["cache_misses"] = 0
        context.state["cache_misses"] += 1

        result = await self.primitive.execute(input_data, context)
        await self._backend.set(cache_key, result, self.ttl_seconds)

        logger.debug("cache_store", key=cache_key[:50])
        return result

    def clear_cache(self) -> None:
        """Clear all cached values (only effective for InMemoryBackend)."""
        if isinstance(self._backend, InMemoryBackend):
            size = self._backend.clear()
            logger.info("cache_cleared", previous_size=size)
        else:
            logger.warning(
                "clear_cache_unsupported",
                backend=type(self._backend).__name__,
            )

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        size = self._backend.size() if isinstance(self._backend, InMemoryBackend) else -1
        return {
            "size": size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "expirations": self._stats["expirations"],
            "hit_rate": self.get_hit_rate(),
        }

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage (0–100)."""
        total = self._stats["hits"] + self._stats["misses"]
        if total == 0:
            return 0.0
        return round((self._stats["hits"] / total) * 100, 2)

    def evict_expired(self) -> int:
        """Manually evict expired entries (only meaningful for InMemoryBackend)."""
        if isinstance(self._backend, InMemoryBackend):
            count = self._backend.evict_expired()
            self._stats["expirations"] += count
            if count:
                logger.info("cache_eviction", count=count)
            return count
        return 0
