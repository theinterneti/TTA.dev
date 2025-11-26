"""In-memory storage for MemoryPrimitive fallback.

Simple LRU cache with keyword search. Works immediately without any setup.
No Redis, no Docker, no dependencies beyond stdlib.
"""

import hashlib
import json
import logging
from collections import OrderedDict
from typing import Any, cast

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Simple LRU cache for working memory.

    Perfect for:
    - Learning TTA.dev
    - Running examples
    - Local development
    - When Docker isn't available

    Limitations:
    - No persistence (data lost on restart)
    - No semantic search (keyword matching only)
    - Not shared across processes
    - Limited by available RAM

    For production or semantic search, use Redis backend.
    """

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize in-memory store.

        Args:
            max_size: Maximum number of items to store (LRU eviction)
        """
        self.store: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.max_size = max_size
        logger.info(f"📦 InMemoryStore initialized (max_size={max_size})")

    def add(self, key: str, value: dict[str, Any]) -> None:
        """Add or update item in store.

        If key exists, moves to end (most recently used).
        If store is full, evicts least recently used item.

        Args:
            key: Unique identifier for this memory
            value: Data to store (must be JSON-serializable)
        """
        # Update existing or add new
        if key in self.store:
            self.store.move_to_end(key)
            logger.debug(f"Updated memory: {key}")
        else:
            logger.debug(f"Added memory: {key}")

        self.store[key] = value

        # Evict LRU if over capacity
        if len(self.store) > self.max_size:
            evicted_key = next(iter(self.store))
            self.store.popitem(last=False)
            logger.debug(f"Evicted LRU memory: {evicted_key}")

    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve item from store.

        Moves item to end (marks as recently used).

        Args:
            key: Identifier for memory to retrieve

        Returns:
            Stored value if found, None otherwise
        """
        if key in self.store:
            self.store.move_to_end(key)
            logger.debug(f"Retrieved memory: {key}")
            return self.store[key]

        logger.debug(f"Memory not found: {key}")
        return None

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search memories by keyword matching.

        Simple substring search across all stored values.
        For semantic search, use Redis backend.

        Args:
            query: Search term (case-insensitive)
            limit: Maximum results to return

        Returns:
            List of matching memories (most recent first)
        """
        if not query:
            return []

        results = []
        query_lower = query.lower()

        # Search from most recent to oldest
        for item in reversed(list(self.store.values())):
            # Convert to string for searching
            item_str = json.dumps(item, default=str).lower()

            if query_lower in item_str:
                results.append(item)
                if len(results) >= limit:
                    break

        logger.debug(f"Search '{query}' found {len(results)} results")
        return results

    def clear(self) -> None:
        """Remove all items from store."""
        count = len(self.store)
        self.store.clear()
        logger.info(f"Cleared {count} memories")

    def size(self) -> int:
        """Get current number of items in store."""
        return len(self.store)

    def keys(self) -> list[str]:
        """Get all keys in store (most recent last)."""
        return list(self.store.keys())


def create_memory_key(
    user_id: str,
    session_id: str,
    context: dict[str, Any] | None = None,
) -> str:
    """Create a unique key for memory storage.

    Args:
        user_id: User identifier
        session_id: Session identifier
        context: Optional context dict for additional uniqueness

    Returns:
        Unique key string
    """
    base = f"{user_id}:{session_id}"

    if context:
        # Hash context for deterministic key
        context_str = json.dumps(context, sort_keys=True, default=str)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{base}:{context_hash}"

    return base


# ============================================================================
# MemoryPrimitive - Hybrid Implementation
# ============================================================================


class MemoryPrimitive:
    """Hybrid memory primitive with automatic fallback.

    Works immediately with in-memory storage, enhanced with Redis when available.

    Basic usage (no setup required):
        >>> memory = MemoryPrimitive()  # Uses InMemoryStore
        >>> await memory.add("user:123:session:abc", {"context": "data"})
        >>> result = await memory.get("user:123:session:abc")

    With Redis (optional enhancement):
        >>> memory = MemoryPrimitive(redis_url="redis://localhost:6379")
        >>> # Automatically falls back to InMemoryStore if Redis unavailable

    The API is identical regardless of backend. Your code works the same way.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        max_size: int = 1000,
        enable_redis: bool = True,
    ) -> None:
        """Initialize memory primitive.

        Args:
            redis_url: Optional Redis connection URL. If None, uses in-memory only.
            max_size: Maximum size for in-memory fallback store
            enable_redis: Whether to attempt Redis connection (for testing)
        """
        # Always create fallback store
        self.fallback = InMemoryStore(max_size=max_size)
        self.redis_client = None
        self.using_redis = False

        # Attempt Redis connection if URL provided
        if redis_url and enable_redis:
            try:
                # Import here to avoid hard dependency
                from redis import Redis

                self.redis_client = Redis.from_url(
                    redis_url, decode_responses=True, socket_connect_timeout=2
                )

                # Test connection
                self.redis_client.ping()
                self.using_redis = True
                logger.info(f"✅ Connected to Redis: {redis_url}")

            except ImportError:
                logger.warning(
                    "📦 redis-py not installed. Using in-memory fallback. "
                    "Install with: pip install redis"
                )
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory fallback.")

        if not self.using_redis:
            logger.info("📦 Using InMemoryStore (no Redis)")

    async def add(self, key: str, value: dict[str, Any], ttl: int | None = None) -> None:
        """Add or update memory.

        Args:
            key: Unique identifier for this memory
            value: Data to store (must be JSON-serializable)
            ttl: Optional time-to-live in seconds (Redis only, ignored in fallback)
        """
        if self.using_redis and self.redis_client:
            try:
                # Store in Redis with optional TTL
                value_str = json.dumps(value, default=str)
                if ttl:
                    self.redis_client.setex(key, ttl, value_str)
                else:
                    self.redis_client.set(key, value_str)
                logger.debug(f"Stored in Redis: {key}")
                return
            except Exception as e:
                logger.warning(f"Redis add failed: {e}. Falling back to in-memory.")
                self.using_redis = False  # Disable Redis after failure

        # Fallback to in-memory
        self.fallback.add(key, value)

    async def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve memory by key.

        Args:
            key: Identifier for memory to retrieve

        Returns:
            Stored value if found, None otherwise
        """
        if self.using_redis and self.redis_client:
            try:
                value_str = self.redis_client.get(key)  # type: ignore
                if value_str:
                    logger.debug(f"Retrieved from Redis: {key}")
                    return json.loads(str(value_str))
                return None
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Falling back to in-memory.")
                self.using_redis = False

        # Fallback to in-memory
        return self.fallback.get(key)

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search memories by query.

        Args:
            query: Search term
            limit: Maximum results to return

        Returns:
            List of matching memories

        Note:
            - In-memory: Simple keyword matching
            - Redis: Could use RediSearch for semantic search (future enhancement)
        """
        if self.using_redis and self.redis_client:
            try:
                # For now, just use fallback search (Redis search needs RediSearch module)
                # Future: Implement semantic search with RediSearch
                logger.debug("Search using in-memory (Redis search not implemented)")
            except Exception as e:
                logger.warning(f"Redis search failed: {e}. Using in-memory.")
                self.using_redis = False

        # Use in-memory search
        return self.fallback.search(query, limit)

    async def clear(self) -> None:
        """Clear all memories."""
        if self.using_redis and self.redis_client:
            try:
                # Note: This would clear ALL keys in Redis DB
                # In production, you'd want namespacing
                logger.warning("Redis clear not implemented (would clear entire DB)")
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        self.fallback.clear()

    def size(self) -> int:
        """Get current number of memories stored."""
        if self.using_redis and self.redis_client:
            try:
                # This counts ALL keys in Redis DB
                # In production, you'd want namespaced counting
                db_size = cast(int, self.redis_client.dbsize())
                return db_size if db_size else 0
            except Exception:
                pass

        return self.fallback.size()

    def is_using_redis(self) -> bool:
        """Check if currently using Redis backend."""
        return self.using_redis

    def get_backend_info(self) -> dict[str, Any]:
        """Get information about current backend."""
        return {
            "backend": "redis" if self.using_redis else "in-memory",
            "fallback_available": True,
            "size": self.size(),
        }
