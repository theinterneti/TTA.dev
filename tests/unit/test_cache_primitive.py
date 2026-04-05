"""Comprehensive unit tests for CachePrimitive and InMemoryBackend.

Covers the gaps left by test_cache_backend.py:
- InMemoryBackend.delete, .clear, .size, .evict_expired, .has_expired
- CachePrimitive stats tracking (hits, misses, expirations)
- CachePrimitive hit-rate calculation
- CachePrimitive context.state mutation (cache_hits / cache_misses)
- TTL expiry detection and expiration-stat increment
- clear_cache (InMemoryBackend path + generic-backend path)
- evict_expired (InMemoryBackend path + generic-backend path)
- get_stats structure and size field
- Errors from the wrapped primitive are NOT cached
- None result semantics (stored in backend, treated as miss by CachePrimitive)
- Custom cache_key_fn producing separate cache entries
- Composition via the >> operator (SequentialPrimitive)
- CacheBackend protocol runtime conformance

Not tested here (already in test_cache_backend.py):
- InMemoryBackend.get miss for never-set key
- InMemoryBackend.set + get round-trip
- InMemoryBackend.get lazy TTL eviction via time mock
- RedisBackend (all paths)
- CachePrimitive.execute miss path calling backend.get + backend.set
- CachePrimitive.execute hit path skipping inner execute
- CachePrimitive default backend is InMemoryBackend
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.performance.cache import (
    CacheBackend,
    CachePrimitive,
    InMemoryBackend,
)
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _ctx(workflow_id: str = "test-cache") -> WorkflowContext:
    return WorkflowContext(workflow_id=workflow_id)


def _make_cache(
    *,
    return_value: Any = "result",
    key_fn: Any = None,
    ttl: float = 60.0,
    backend: CacheBackend | None = None,
    raise_error: Exception | None = None,
    side_effect: Any = None,
) -> tuple[CachePrimitive, MockPrimitive]:
    """Build a (CachePrimitive, inner MockPrimitive) pair for use in tests."""
    mock = MockPrimitive(
        "inner",
        return_value=return_value,
        raise_error=raise_error,
        side_effect=side_effect,
    )
    if key_fn is None:
        key_fn = lambda data, ctx: "static_key"  # noqa: E731
    cache = CachePrimitive(
        primitive=mock,
        cache_key_fn=key_fn,
        ttl_seconds=ttl,
        backend=backend,
    )
    return cache, mock


def _non_in_memory_backend() -> AsyncMock:
    """Return an AsyncMock satisfying CacheBackend but not an InMemoryBackend instance."""
    backend = AsyncMock(spec=CacheBackend)
    backend.get = AsyncMock(return_value=None)
    backend.set = AsyncMock()
    backend.delete = AsyncMock()
    return backend


# ===========================================================================
# InMemoryBackend — delete
# ===========================================================================


class TestInMemoryBackendDelete:
    """InMemoryBackend.delete removes a key or is a no-op when absent."""

    @pytest.mark.asyncio
    async def test_delete_existing_key_removes_it(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        await backend.set("greeting", "hello", ttl_seconds=60.0)

        # Act
        await backend.delete("greeting")

        # Assert
        assert await backend.get("greeting") is None

    @pytest.mark.asyncio
    async def test_delete_absent_key_does_not_raise(self) -> None:
        # Arrange
        backend = InMemoryBackend()

        # Act & Assert — must not raise
        await backend.delete("nonexistent_key")

    @pytest.mark.asyncio
    async def test_delete_only_removes_targeted_key(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        await backend.set("keep_me", "value_a", ttl_seconds=60.0)
        await backend.set("remove_me", "value_b", ttl_seconds=60.0)

        # Act
        await backend.delete("remove_me")

        # Assert — sibling key unaffected
        assert await backend.get("keep_me") == "value_a"
        assert await backend.get("remove_me") is None


# ===========================================================================
# InMemoryBackend — clear
# ===========================================================================


class TestInMemoryBackendClear:
    """InMemoryBackend.clear empties the store and returns the previous count."""

    @pytest.mark.asyncio
    async def test_clear_returns_count_of_removed_entries(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        await backend.set("a", 1, ttl_seconds=60.0)
        await backend.set("b", 2, ttl_seconds=60.0)
        await backend.set("c", 3, ttl_seconds=60.0)

        # Act
        count = backend.clear()

        # Assert
        assert count == 3

    @pytest.mark.asyncio
    async def test_clear_empties_the_store(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        await backend.set("x", "val", ttl_seconds=60.0)

        # Act
        backend.clear()

        # Assert
        assert backend.size() == 0
        assert await backend.get("x") is None

    def test_clear_on_empty_store_returns_zero(self) -> None:
        # Arrange
        backend = InMemoryBackend()

        # Act
        count = backend.clear()

        # Assert
        assert count == 0


# ===========================================================================
# InMemoryBackend — size
# ===========================================================================


class TestInMemoryBackendSize:
    """InMemoryBackend.size reflects the raw number of stored entries."""

    def test_size_is_zero_on_fresh_backend(self) -> None:
        # Arrange / Act
        backend = InMemoryBackend()

        # Assert
        assert backend.size() == 0

    @pytest.mark.asyncio
    async def test_size_increments_on_each_set(self) -> None:
        # Arrange
        backend = InMemoryBackend()

        # Act
        await backend.set("k1", "v1", ttl_seconds=60.0)
        await backend.set("k2", "v2", ttl_seconds=60.0)

        # Assert
        assert backend.size() == 2

    @pytest.mark.asyncio
    async def test_size_decrements_after_delete(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        await backend.set("k", "v", ttl_seconds=60.0)

        # Act
        await backend.delete("k")

        # Assert
        assert backend.size() == 0

    @pytest.mark.asyncio
    async def test_size_includes_expired_entries_before_lazy_eviction(self) -> None:
        """Lazy eviction: expired entries still counted until get() or evict_expired()."""
        # Arrange
        backend = InMemoryBackend()
        base = 1_000.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("k", "v", ttl_seconds=1.0)

            # Advance past TTL — entry not yet evicted
            mock_time.monotonic.return_value = base + 10.0

            # Assert — raw size still 1 before any get()
            assert backend.size() == 1


# ===========================================================================
# InMemoryBackend — has_expired
# ===========================================================================


class TestInMemoryBackendHasExpired:
    """InMemoryBackend.has_expired accurately reflects TTL state."""

    def test_has_expired_returns_false_for_missing_key(self) -> None:
        # Arrange / Act / Assert
        backend = InMemoryBackend()
        assert backend.has_expired("no-such-key") is False

    @pytest.mark.asyncio
    async def test_has_expired_returns_false_for_fresh_entry(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        base = 500.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("k", "v", ttl_seconds=30.0)

            # Act — before TTL boundary
            mock_time.monotonic.return_value = base + 10.0
            result = backend.has_expired("k")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_has_expired_returns_true_at_ttl_boundary(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        base = 500.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("k", "v", ttl_seconds=5.0)

            # Act — exactly at the expiry boundary
            mock_time.monotonic.return_value = base + 5.0
            result = backend.has_expired("k")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_has_expired_returns_true_well_past_ttl(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        base = 100.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("k", "v", ttl_seconds=2.0)

            # Act — far past TTL
            mock_time.monotonic.return_value = base + 999.0
            result = backend.has_expired("k")

        # Assert
        assert result is True


# ===========================================================================
# InMemoryBackend — evict_expired
# ===========================================================================


class TestInMemoryBackendEvictExpired:
    """InMemoryBackend.evict_expired proactively removes stale entries."""

    @pytest.mark.asyncio
    async def test_evict_expired_returns_zero_when_nothing_expired(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        base = 200.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("fresh", "v", ttl_seconds=100.0)

            mock_time.monotonic.return_value = base + 10.0  # still fresh

            # Act
            count = backend.evict_expired()

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_evict_expired_removes_stale_entries_and_returns_count(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        base = 200.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("exp1", "a", ttl_seconds=5.0)
            await backend.set("exp2", "b", ttl_seconds=5.0)
            await backend.set("fresh", "c", ttl_seconds=1000.0)

            # Advance past the short TTL
            mock_time.monotonic.return_value = base + 6.0

            # Act
            count = backend.evict_expired()

        # Assert
        assert count == 2
        assert backend.size() == 1  # only "fresh" remains

    @pytest.mark.asyncio
    async def test_evict_expired_leaves_fresh_entries_accessible(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        base = 300.0
        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await backend.set("stale", "old", ttl_seconds=10.0)
            await backend.set("alive", "good", ttl_seconds=1000.0)

            mock_time.monotonic.return_value = base + 15.0
            backend.evict_expired()

            # Verify surviving entry is still accessible
            value = await backend.get("alive")

        # Assert
        assert value == "good"


# ===========================================================================
# CachePrimitive — stats tracking
# ===========================================================================


class TestCachePrimitiveStats:
    """_stats dict is updated correctly on hits, misses, and expirations."""

    @pytest.mark.asyncio
    async def test_initial_stats_are_all_zero(self) -> None:
        # Arrange / Act
        cache, _ = _make_cache()
        stats = cache.get_stats()

        # Assert
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["expirations"] == 0

    @pytest.mark.asyncio
    async def test_first_call_increments_misses_only(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")

        # Act
        await cache.execute("inp", _ctx())

        # Assert
        assert cache.get_stats()["misses"] == 1
        assert cache.get_stats()["hits"] == 0

    @pytest.mark.asyncio
    async def test_second_call_with_same_key_increments_hits(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")
        ctx = _ctx()

        # Act
        await cache.execute("inp", ctx)
        await cache.execute("inp", ctx)

        # Assert
        assert cache.get_stats()["hits"] == 1
        assert cache.get_stats()["misses"] == 1

    @pytest.mark.asyncio
    async def test_repeated_hits_accumulate_in_stats(self) -> None:
        # Arrange
        cache, mock = _make_cache(return_value="v")
        ctx = _ctx()

        # Act — one miss, three hits
        for _ in range(4):
            await cache.execute("inp", ctx)

        # Assert
        assert cache.get_stats()["misses"] == 1
        assert cache.get_stats()["hits"] == 3
        mock.assert_call_count(1)  # primitive called only once

    @pytest.mark.asyncio
    async def test_different_keys_each_produce_a_miss(self) -> None:
        # Arrange
        cache, mock = _make_cache(key_fn=lambda d, c: str(d))

        # Act
        await cache.execute("a", _ctx())
        await cache.execute("b", _ctx())
        await cache.execute("c", _ctx())

        # Assert
        assert cache.get_stats()["misses"] == 3
        mock.assert_call_count(3)


# ===========================================================================
# CachePrimitive — hit-rate calculation
# ===========================================================================


class TestCachePrimitiveHitRate:
    """get_hit_rate returns a float between 0.0 and 100.0."""

    def test_hit_rate_is_zero_before_any_calls(self) -> None:
        # Arrange / Act / Assert
        cache, _ = _make_cache()
        assert cache.get_hit_rate() == 0.0

    @pytest.mark.asyncio
    async def test_hit_rate_is_zero_with_only_misses(self) -> None:
        # Arrange
        cache, _ = _make_cache(key_fn=lambda d, c: str(d))

        # Act — three unique keys → three misses
        for key in ("alpha", "beta", "gamma"):
            await cache.execute(key, _ctx())

        # Assert
        assert cache.get_hit_rate() == 0.0

    @pytest.mark.asyncio
    async def test_hit_rate_fifty_percent_one_hit_one_miss(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")
        ctx = _ctx()

        # Act
        await cache.execute("k", ctx)  # miss
        await cache.execute("k", ctx)  # hit

        # Assert
        assert cache.get_hit_rate() == 50.0

    @pytest.mark.asyncio
    async def test_hit_rate_rounds_to_two_decimal_places(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")
        ctx = _ctx()

        # Act — 1 miss + 2 hits → 66.67 %
        for _ in range(3):
            await cache.execute("same", ctx)

        # Assert
        assert cache.get_hit_rate() == pytest.approx(66.67, abs=0.01)


# ===========================================================================
# CachePrimitive — context.state mutation
# ===========================================================================


class TestCachePrimitiveContextState:
    """CachePrimitive writes cache_hits / cache_misses into context.state."""

    @pytest.mark.asyncio
    async def test_miss_writes_cache_misses_into_context_state(self) -> None:
        # Arrange
        cache, _ = _make_cache()
        ctx = _ctx()

        # Act
        await cache.execute("data", ctx)

        # Assert
        assert ctx.state.get("cache_misses") == 1

    @pytest.mark.asyncio
    async def test_hit_writes_cache_hits_into_context_state(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")
        ctx = _ctx()

        # Act — miss then hit
        await cache.execute("d", ctx)
        await cache.execute("d", ctx)

        # Assert
        assert ctx.state.get("cache_hits") == 1

    @pytest.mark.asyncio
    async def test_context_state_counters_accumulate_across_calls(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")
        ctx = _ctx()

        # Act — 1 miss + 3 hits
        for _ in range(4):
            await cache.execute("key", ctx)

        # Assert
        assert ctx.state.get("cache_misses") == 1
        assert ctx.state.get("cache_hits") == 3

    @pytest.mark.asyncio
    async def test_separate_context_objects_have_independent_state(self) -> None:
        # Arrange — two distinct context objects sharing the same CachePrimitive
        cache, _ = _make_cache(return_value="v")
        ctx_a = WorkflowContext(workflow_id="ctx-a")
        ctx_b = WorkflowContext(workflow_id="ctx-b")

        # Act — ctx_a misses; ctx_b hits (same static key, shared InMemoryBackend)
        await cache.execute("k", ctx_a)  # miss
        await cache.execute("k", ctx_b)  # hit

        # Assert — state is independent per context object
        assert ctx_a.state.get("cache_misses") == 1
        assert ctx_a.state.get("cache_hits") is None  # no hit in ctx_a
        assert ctx_b.state.get("cache_hits") == 1
        assert ctx_b.state.get("cache_misses") is None  # no miss in ctx_b


# ===========================================================================
# CachePrimitive — TTL expiry detection
# ===========================================================================


class TestCachePrimitiveTTLExpiry:
    """CachePrimitive tracks expirations via has_expired() on InMemoryBackend."""

    @pytest.mark.asyncio
    async def test_expired_entry_causes_primitive_to_be_re_executed(self) -> None:
        # Arrange
        cache, mock = _make_cache(return_value="v", ttl=5.0)
        ctx = _ctx()
        base = 1_000.0

        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await cache.execute("inp", ctx)  # miss — stores entry

            # Advance past TTL
            mock_time.monotonic.return_value = base + 6.0
            await cache.execute("inp", ctx)  # expired — miss again

        # Assert — inner primitive called twice
        mock.assert_call_count(2)

    @pytest.mark.asyncio
    async def test_expiry_increments_expirations_stat(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", ttl=5.0)
        ctx = _ctx()
        base = 500.0

        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await cache.execute("k", ctx)  # miss — stores entry

            mock_time.monotonic.return_value = base + 10.0  # expired
            await cache.execute("k", ctx)  # detects expiry → increments stat

        # Assert
        assert cache.get_stats()["expirations"] == 1

    @pytest.mark.asyncio
    async def test_no_expiry_stat_increment_when_entry_is_still_valid(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", ttl=3600.0)
        ctx = _ctx()

        # Act — two rapid calls (no time advancement)
        await cache.execute("k", ctx)
        await cache.execute("k", ctx)

        # Assert
        assert cache.get_stats()["expirations"] == 0


# ===========================================================================
# CachePrimitive — get_stats structure
# ===========================================================================


class TestCachePrimitiveGetStats:
    """get_stats returns a complete dict with all required fields."""

    @pytest.mark.asyncio
    async def test_get_stats_contains_all_required_keys(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v")
        await cache.execute("x", _ctx())

        # Act
        stats = cache.get_stats()

        # Assert
        required = {"size", "hits", "misses", "expirations", "hit_rate"}
        assert required <= stats.keys()

    def test_get_stats_size_is_non_negative_for_in_memory_backend(self) -> None:
        # Arrange / Act / Assert
        cache, _ = _make_cache()
        assert cache.get_stats()["size"] >= 0

    def test_get_stats_size_is_minus_one_for_non_in_memory_backend(self) -> None:
        # Arrange
        cache, _ = _make_cache(backend=_non_in_memory_backend())

        # Act / Assert
        assert cache.get_stats()["size"] == -1

    @pytest.mark.asyncio
    async def test_get_stats_size_reflects_distinct_cached_keys(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", key_fn=lambda d, c: str(d))
        ctx = _ctx()

        # Act — store two distinct keys
        await cache.execute("key_one", ctx)
        await cache.execute("key_two", ctx)

        # Assert
        assert cache.get_stats()["size"] == 2


# ===========================================================================
# CachePrimitive — clear_cache
# ===========================================================================


class TestCachePrimitiveClearCache:
    """clear_cache empties InMemoryBackend; is a no-op for other backends."""

    @pytest.mark.asyncio
    async def test_clear_cache_removes_in_memory_entries(self) -> None:
        # Arrange
        cache, mock = _make_cache(return_value="v")
        ctx = _ctx()
        await cache.execute("input", ctx)  # populate cache

        # Act
        cache.clear_cache()

        # Assert — next call must miss (primitive called again)
        mock.reset()
        await cache.execute("input", ctx)
        mock.assert_called()

    @pytest.mark.asyncio
    async def test_clear_cache_resets_backend_size_to_zero(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", key_fn=lambda d, c: str(d))
        ctx = _ctx()
        await cache.execute("a", ctx)
        await cache.execute("b", ctx)

        # Act
        cache.clear_cache()

        # Assert
        assert cache.get_stats()["size"] == 0

    def test_clear_cache_on_non_in_memory_backend_does_not_raise(self) -> None:
        # Arrange
        cache, _ = _make_cache(backend=_non_in_memory_backend())

        # Act & Assert — must not raise
        cache.clear_cache()


# ===========================================================================
# CachePrimitive — evict_expired
# ===========================================================================


class TestCachePrimitiveEvictExpired:
    """evict_expired delegates to InMemoryBackend and updates expirations stat."""

    @pytest.mark.asyncio
    async def test_evict_expired_removes_stale_in_memory_entries(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", ttl=5.0)
        ctx = _ctx()
        base = 100.0

        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await cache.execute("inp", ctx)  # stores entry

            mock_time.monotonic.return_value = base + 10.0  # entry expired

            # Act
            count = cache.evict_expired()

        # Assert
        assert count == 1

    @pytest.mark.asyncio
    async def test_evict_expired_updates_expirations_stat(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", ttl=5.0)
        ctx = _ctx()
        base = 100.0

        with patch("ttadev.primitives.performance.cache.time") as mock_time:
            mock_time.monotonic.return_value = base
            await cache.execute("inp", ctx)

            mock_time.monotonic.return_value = base + 10.0

            # Act
            cache.evict_expired()

        # Assert
        assert cache.get_stats()["expirations"] == 1

    @pytest.mark.asyncio
    async def test_evict_expired_returns_zero_when_nothing_expired(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", ttl=3600.0)
        ctx = _ctx()
        await cache.execute("inp", ctx)

        # Act
        count = cache.evict_expired()

        # Assert
        assert count == 0
        assert cache.get_stats()["expirations"] == 0

    def test_evict_expired_returns_zero_for_non_in_memory_backend(self) -> None:
        # Arrange
        cache, _ = _make_cache(backend=_non_in_memory_backend())

        # Act / Assert
        assert cache.evict_expired() == 0

    @pytest.mark.asyncio
    async def test_evict_expired_does_not_change_stat_when_zero_evicted(self) -> None:
        # Arrange
        cache, _ = _make_cache(return_value="v", ttl=3600.0)
        ctx = _ctx()
        await cache.execute("inp", ctx)

        initial_expirations = cache.get_stats()["expirations"]

        # Act
        cache.evict_expired()

        # Assert — stat unchanged
        assert cache.get_stats()["expirations"] == initial_expirations


# ===========================================================================
# CachePrimitive — error handling (errors must not be cached)
# ===========================================================================


class TestCachePrimitiveErrorHandling:
    """Errors raised by the wrapped primitive propagate; backend.set is never called."""

    @pytest.mark.asyncio
    async def test_error_propagates_to_caller(self) -> None:
        # Arrange
        cache, _ = _make_cache(raise_error=ValueError("computation failed"))
        ctx = _ctx()

        # Act & Assert
        with pytest.raises(ValueError, match="computation failed"):
            await cache.execute("input", ctx)

    @pytest.mark.asyncio
    async def test_error_does_not_populate_in_memory_backend(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        mock = MockPrimitive("inner", raise_error=RuntimeError("boom"))
        cache = CachePrimitive(
            primitive=mock,
            cache_key_fn=lambda d, c: "error_key",
            ttl_seconds=60.0,
            backend=backend,
        )
        ctx = _ctx()

        # Act — call raises
        with pytest.raises(RuntimeError):
            await cache.execute("inp", ctx)

        # Assert — nothing stored
        assert backend.size() == 0
        assert await backend.get("error_key") is None

    @pytest.mark.asyncio
    async def test_error_not_cached_subsequent_success_is_cached(self) -> None:
        """After a failed call the next successful call stores the result."""
        # Arrange
        call_count: dict[str, int] = {"n": 0}

        def side_effect(data: Any, ctx: WorkflowContext) -> Any:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ValueError("first call fails")
            return "success"

        mock = MockPrimitive("inner", side_effect=side_effect)
        cache = CachePrimitive(
            primitive=mock,
            cache_key_fn=lambda d, c: "k",
            ttl_seconds=60.0,
        )
        ctx = _ctx()

        # Act — error, then success
        with pytest.raises(ValueError):
            await cache.execute("inp", ctx)

        result = await cache.execute("inp", ctx)  # success — now cached

        # Assert
        assert result == "success"
        assert mock.call_count == 2

        # Third call must be a cache hit (primitive not called again)
        result2 = await cache.execute("inp", ctx)
        assert result2 == "success"
        assert mock.call_count == 2  # still 2


# ===========================================================================
# CachePrimitive — None result semantics
# ===========================================================================


class TestCachePrimitiveNoneResult:
    """None results are stored in the backend but always cause cache-misses at
    the CachePrimitive level because ``if cached is not None`` is False.

    This is a known design characteristic: callers should avoid returning None
    from primitives they intend to cache.
    """

    @pytest.mark.asyncio
    async def test_none_result_is_stored_in_backend(self) -> None:
        # Arrange
        backend = InMemoryBackend()
        mock = MockPrimitive("inner", return_value=None)
        cache = CachePrimitive(
            primitive=mock,
            cache_key_fn=lambda d, c: "none_key",
            ttl_seconds=60.0,
            backend=backend,
        )
        ctx = _ctx()

        # Act
        result = await cache.execute("inp", ctx)

        # Assert — backend.set was called with None; entry is present
        assert result is None
        assert backend.size() == 1

    @pytest.mark.asyncio
    async def test_none_result_is_treated_as_miss_on_subsequent_calls(self) -> None:
        """Because CachePrimitive checks `if cached is not None`, a stored None
        value always registers as a miss, causing the primitive to be re-executed."""
        # Arrange
        mock = MockPrimitive("inner", return_value=None)
        cache = CachePrimitive(
            primitive=mock,
            cache_key_fn=lambda d, c: "k",
            ttl_seconds=60.0,
        )
        ctx = _ctx()

        # Act — two calls with None-returning primitive
        await cache.execute("inp", ctx)
        await cache.execute("inp", ctx)

        # Assert — primitive called both times (None never satisfies cache hit check)
        mock.assert_call_count(2)
        assert cache.get_stats()["hits"] == 0
        assert cache.get_stats()["misses"] == 2


# ===========================================================================
# CachePrimitive — custom cache_key_fn
# ===========================================================================


class TestCachePrimitiveCustomKeyFn:
    """Custom cache_key_fn controls which inputs share cached results."""

    @pytest.mark.asyncio
    async def test_different_inputs_with_per_input_key_produce_separate_entries(
        self,
    ) -> None:
        # Arrange
        cache, mock = _make_cache(
            return_value="dynamic",
            key_fn=lambda data, ctx: f"key:{data}",
        )
        ctx = _ctx()

        # Act
        result_a = await cache.execute("alpha", ctx)
        result_b = await cache.execute("beta", ctx)

        # Assert — two separate cache entries; inner called twice
        assert mock.call_count == 2
        assert result_a == "dynamic"
        assert result_b == "dynamic"
        assert cache.get_stats()["misses"] == 2

    @pytest.mark.asyncio
    async def test_same_key_for_different_inputs_shares_cached_result(self) -> None:
        # Arrange — key ignores input content (static)
        cache, mock = _make_cache(
            return_value="shared_value",
            key_fn=lambda data, ctx: "fixed_key",
        )
        ctx = _ctx()

        # Act — two different inputs share the same key
        result_a = await cache.execute("input_one", ctx)
        result_b = await cache.execute("input_two", ctx)

        # Assert — second call is a hit
        assert mock.call_count == 1
        assert result_a == "shared_value"
        assert result_b == "shared_value"
        assert cache.get_stats()["hits"] == 1

    @pytest.mark.asyncio
    async def test_key_fn_can_incorporate_context_player_id(self) -> None:
        # Arrange
        cache, mock = _make_cache(
            return_value="player_result",
            key_fn=lambda data, ctx: f"{data}:{ctx.player_id}",
        )
        ctx_p1 = WorkflowContext(player_id="player_1")
        ctx_p2 = WorkflowContext(player_id="player_2")

        # Act
        result_p1 = await cache.execute("quest", ctx_p1)
        result_p2 = await cache.execute("quest", ctx_p2)

        # Assert — different player_ids → separate entries
        assert mock.call_count == 2
        assert result_p1 == "player_result"
        assert result_p2 == "player_result"

    @pytest.mark.asyncio
    async def test_repr_key_fn_distinguishes_int_from_numeric_string(self) -> None:
        # Arrange — repr() makes integer 1 and string "1" produce different keys
        cache, mock = _make_cache(
            return_value="typed",
            key_fn=lambda data, ctx: repr(data),
        )
        ctx = _ctx()

        # Act
        await cache.execute(1, ctx)
        await cache.execute("1", ctx)

        # Assert — treated as distinct keys
        assert mock.call_count == 2


# ===========================================================================
# CachePrimitive — composition via >> operator
# ===========================================================================


class TestCachePrimitiveComposition:
    """CachePrimitive integrates correctly when composed with other primitives."""

    @pytest.mark.asyncio
    async def test_preprocess_then_cache_pipeline(self) -> None:
        """preprocess >> cache: preprocessed output is the input to CachePrimitive."""
        # Arrange
        doubler = MockPrimitive("double", side_effect=lambda d, c: d * 2)
        inner = MockPrimitive("compute", return_value="answer")
        cache = CachePrimitive(
            primitive=inner,
            cache_key_fn=lambda data, ctx: str(data),
            ttl_seconds=60.0,
        )
        pipeline = doubler >> cache
        ctx = _ctx()

        # Act — 3 → doubled to 6 → cache miss → inner returns "answer"
        result = await pipeline.execute(3, ctx)

        # Assert
        assert result == "answer"
        doubler.assert_called_once()
        inner.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_then_postprocess_pipeline(self) -> None:
        """cache >> postprocess: cached dict result is transformed downstream."""
        # Arrange
        inner = MockPrimitive("compute", return_value={"value": 42})
        cache = CachePrimitive(
            primitive=inner,
            cache_key_fn=lambda data, ctx: "k",
            ttl_seconds=60.0,
        )
        extractor = MockPrimitive("extract", side_effect=lambda d, c: d["value"])
        pipeline = cache >> extractor
        ctx = _ctx()

        # Act
        result = await pipeline.execute("any_input", ctx)

        # Assert
        assert result == 42
        inner.assert_called_once()
        extractor.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_in_composed_pipeline_skips_inner_only(self) -> None:
        """In preprocess >> cache: cache hit still runs preprocess but not inner."""
        # Arrange
        preprocess = MockPrimitive("pre", side_effect=lambda d, c: "preprocessed")
        inner = MockPrimitive("compute", return_value="cached_val")
        cache = CachePrimitive(
            primitive=inner,
            cache_key_fn=lambda data, ctx: str(data),
            ttl_seconds=60.0,
        )
        pipeline = preprocess >> cache
        ctx = _ctx()

        # Act — two calls with the same raw input
        result_1 = await pipeline.execute("raw", ctx)
        result_2 = await pipeline.execute("raw", ctx)

        # Assert — preprocess ran twice; inner only once (second is a cache hit)
        preprocess.assert_call_count(2)
        inner.assert_call_count(1)
        assert result_1 == "cached_val"
        assert result_2 == "cached_val"


# ===========================================================================
# CacheBackend Protocol conformance
# ===========================================================================


class TestCacheBackendProtocol:
    """CacheBackend is a runtime_checkable Protocol."""

    def test_in_memory_backend_satisfies_protocol(self) -> None:
        # Arrange / Act / Assert
        assert isinstance(InMemoryBackend(), CacheBackend)

    def test_minimal_duck_type_with_all_methods_satisfies_protocol(self) -> None:
        # Arrange
        class MinimalBackend:
            async def get(self, key: str) -> Any | None:
                return None

            async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
                pass

            async def delete(self, key: str) -> None:
                pass

        # Act / Assert
        assert isinstance(MinimalBackend(), CacheBackend)

    def test_object_missing_delete_does_not_satisfy_protocol(self) -> None:
        # Arrange — missing the required `delete` method
        class IncompleteBackend:
            async def get(self, key: str) -> Any | None:
                return None

            async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
                pass

        # Act / Assert
        assert not isinstance(IncompleteBackend(), CacheBackend)
