"""Unit tests for CacheBackend protocol, InMemoryBackend, RedisBackend, CachePrimitive.

Uses fakeredis for Redis tests — no live Redis required.
"""

from __future__ import annotations

import pickle
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.performance.cache import (
    CacheBackend,
    CachePrimitive,
    InMemoryBackend,
    RedisBackend,
)


def _ctx() -> WorkflowContext:
    return WorkflowContext()


def _primitive(return_value: Any = "computed") -> MagicMock:
    p = MagicMock()
    p.execute = AsyncMock(return_value=return_value)
    return p


class TestInMemoryBackend:
    """InMemoryBackend: in-process dict cache with lazy TTL eviction."""

    async def test_in_memory_backend_get_miss(self) -> None:
        """Returns None for a key that was never set."""
        backend = InMemoryBackend()
        assert await backend.get("nonexistent") is None

    async def test_in_memory_backend_set_and_get(self) -> None:
        """Stored values are retrievable before TTL elapses."""
        backend = InMemoryBackend()
        await backend.set("greeting", {"msg": "hello"}, ttl_seconds=60.0)
        result = await backend.get("greeting")
        assert result == {"msg": "hello"}

    async def test_in_memory_backend_ttl_expiry(self) -> None:
        """Values expire when monotonic time advances past the TTL boundary."""
        backend = InMemoryBackend()
        base = 1_000.0

        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("key", "value", ttl_seconds=5.0)

            mock_time.monotonic.return_value = base + 4.9
            assert await backend.get("key") == "value"

            mock_time.monotonic.return_value = base + 5.0
            assert await backend.get("key") is None


class TestRedisBackend:
    """RedisBackend: async Redis cache via fakeredis (no live Redis required)."""

    @pytest.fixture
    def fake_client(self):
        fakeredis = pytest.importorskip("fakeredis")
        return fakeredis.FakeAsyncRedis()

    @pytest.fixture
    def backend(self, fake_client) -> RedisBackend:
        """RedisBackend instance wired to a fakeredis async client."""
        b = RedisBackend.__new__(RedisBackend)
        b._prefix = "tta:"
        b._client = fake_client
        return b

    async def test_redis_backend_get_miss(self, backend: RedisBackend) -> None:
        """Returns None for a key absent from Redis."""
        assert await backend.get("does_not_exist") is None

    async def test_redis_backend_set_and_get(self, backend: RedisBackend) -> None:
        """Round-trip through fakeredis preserves the value."""
        await backend.set("score", {"points": 100}, ttl_seconds=30.0)
        result = await backend.get("score")
        assert result == {"points": 100}

    async def test_redis_backend_prefix(self, backend: RedisBackend, fake_client) -> None:
        """The physical Redis key is stored with the configured prefix."""
        await backend.set("mykey", "myvalue", ttl_seconds=60.0)
        raw_bytes: bytes | None = await fake_client.get("tta:mykey")
        assert raw_bytes is not None
        assert pickle.loads(raw_bytes) == "myvalue"  # noqa: S301


class TestCachePrimitive:
    """CachePrimitive: high-level primitive orchestrating a CacheBackend."""

    async def test_cache_primitive_uses_backend(self) -> None:
        """CachePrimitive calls backend.get on lookup and backend.set on miss."""
        mock_backend = AsyncMock(spec=CacheBackend)
        mock_backend.get.return_value = None
        mock_backend.set.return_value = None

        inner = _primitive("fresh_result")
        prim = CachePrimitive(
            primitive=inner,
            cache_key_fn=lambda data, ctx: "test_key",
            ttl_seconds=10.0,
            backend=mock_backend,
        )
        result = await prim.execute("input", _ctx())

        assert result == "fresh_result"
        mock_backend.get.assert_called_once_with("test_key")
        mock_backend.set.assert_called_once_with("test_key", "fresh_result", 10.0)

    async def test_cache_hit_skips_inner_execute(self) -> None:
        """On a cache hit the inner primitive is never called."""
        mock_backend = AsyncMock(spec=CacheBackend)
        mock_backend.get.return_value = "cached_value"

        inner = _primitive("should_not_be_called")
        prim = CachePrimitive(
            primitive=inner,
            cache_key_fn=lambda data, ctx: "k",
            backend=mock_backend,
        )
        result = await prim.execute("input", _ctx())

        assert result == "cached_value"
        inner.execute.assert_not_called()

    def test_cache_primitive_default_backend_is_in_memory(self) -> None:
        """When no backend kwarg is supplied, InMemoryBackend is used."""
        prim = CachePrimitive(
            primitive=_primitive(),
            cache_key_fn=lambda d, c: "k",
        )
        assert isinstance(prim._backend, InMemoryBackend)
