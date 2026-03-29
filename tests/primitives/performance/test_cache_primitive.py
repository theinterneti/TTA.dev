"""Unit tests for CachePrimitive — AAA pattern throughout."""

import asyncio

from ttadev.primitives import CachePrimitive, LambdaPrimitive, WorkflowContext


async def test_cache_returns_result_on_first_call():
    # Arrange
    async def compute(_inp, _ctx):
        return f"result-{_inp}"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    # Act
    result = await cache.execute("key1", ctx)
    # Assert
    assert result == "result-key1"


async def test_cache_returns_cached_result_on_second_call():
    # Arrange
    call_count = 0

    async def compute(_inp, _ctx):
        nonlocal call_count
        call_count += 1
        return f"result-{_inp}"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    # Act
    await cache.execute("key1", ctx)
    result = await cache.execute("key1", ctx)
    # Assert
    assert result == "result-key1"
    assert call_count == 1


async def test_cache_computes_fresh_result_after_ttl_expires():
    # Arrange
    call_count = 0

    async def compute(_inp, _ctx):
        nonlocal call_count
        call_count += 1
        return f"result-{call_count}"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=0.01,
    )
    ctx = WorkflowContext()
    # Act
    await cache.execute("key1", ctx)
    await asyncio.sleep(0.02)
    result = await cache.execute("key1", ctx)
    # Assert
    assert call_count == 2
    assert result == "result-2"


async def test_cache_uses_custom_key_function():
    # Arrange
    seen_keys = []

    async def compute(inp, _ctx):
        return inp

    def custom_key(inp, _ctx):
        key = f"custom:{inp}"
        seen_keys.append(key)
        return key

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=custom_key,
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    # Act
    await cache.execute("hello", ctx)
    # Assert
    assert "custom:hello" in seen_keys


async def test_cache_treats_different_inputs_as_separate_keys():
    # Arrange
    call_count = 0

    async def compute(_inp, _ctx):
        nonlocal call_count
        call_count += 1
        return f"result-{_inp}"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    # Act
    await cache.execute("key1", ctx)
    await cache.execute("key2", ctx)
    # Assert
    assert call_count == 2


async def test_cache_hit_increments_context_state():
    # Arrange
    async def compute(_inp, _ctx):
        return "value"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    # Act — first call is a miss, second is a hit
    await cache.execute("k", ctx)
    await cache.execute("k", ctx)
    # Assert
    assert ctx.state.get("cache_hits") == 1
    assert ctx.state.get("cache_misses") == 1


async def test_clear_cache_empties_all_entries():
    # Arrange
    async def compute(_inp, _ctx):
        return "v"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    await cache.execute("k1", ctx)
    await cache.execute("k2", ctx)
    # Act
    cache.clear_cache()
    # Assert — cache is empty; next call recomputes
    stats = cache.get_stats()
    assert stats["size"] == 0


async def test_get_stats_returns_correct_metrics():
    # Arrange
    async def compute(_inp, _ctx):
        return "v"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    ctx = WorkflowContext()
    await cache.execute("k", ctx)  # miss
    await cache.execute("k", ctx)  # hit
    # Act
    stats = cache.get_stats()
    # Assert
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["hit_rate"] == 50.0
    assert "expirations" in stats


async def test_get_hit_rate_returns_zero_when_no_calls():
    # Arrange
    async def compute(_inp, _ctx):
        return "v"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=60,
    )
    # Act — no execute calls
    rate = cache.get_hit_rate()
    # Assert
    assert rate == 0.0


async def test_evict_expired_removes_stale_entries():
    # Arrange
    async def compute(_inp, _ctx):
        return "v"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=0.01,
    )
    ctx = WorkflowContext()
    await cache.execute("k1", ctx)
    await cache.execute("k2", ctx)
    await asyncio.sleep(0.02)
    # Act
    evicted = cache.evict_expired()
    # Assert
    assert evicted == 2
    assert cache.get_stats()["size"] == 0


async def test_evict_expired_returns_zero_when_nothing_expires():
    # Arrange
    async def compute(_inp, _ctx):
        return "v"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=3600,
    )
    ctx = WorkflowContext()
    await cache.execute("k", ctx)
    # Act
    evicted = cache.evict_expired()
    # Assert
    assert evicted == 0
    assert cache.get_stats()["size"] == 1


async def test_expiration_increments_expiration_stat():
    # Arrange — TTL expires between calls, verifying expirations counter
    async def compute(_inp, _ctx):
        return "v"

    cache = CachePrimitive(
        LambdaPrimitive(compute),
        cache_key_fn=lambda inp, _ctx: str(inp),
        ttl_seconds=0.01,
    )
    ctx = WorkflowContext()
    await cache.execute("k", ctx)
    await asyncio.sleep(0.02)
    # Trigger re-execution so the expired branch runs
    await cache.execute("k", ctx)
    # Assert
    stats = cache.get_stats()
    assert stats["expirations"] >= 1
