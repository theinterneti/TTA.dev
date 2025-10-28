"""Tests for cache primitive."""

import time

import pytest

from tta_workflow_primitives.core.base import WorkflowContext
from tta_workflow_primitives.performance.cache import CachePrimitive
from tta_workflow_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_cache_hit() -> None:
    """Test cache hit on second call."""
    mock = MockPrimitive("test", return_value={"result": "cached"})

    cached = CachePrimitive(
        primitive=mock, cache_key_fn=lambda data, ctx: data["key"], ttl_seconds=60.0
    )

    # First call - cache miss
    result1 = await cached.execute({"key": "test"}, WorkflowContext())
    assert result1 == {"result": "cached"}
    assert mock.call_count == 1

    # Second call - cache hit
    result2 = await cached.execute({"key": "test"}, WorkflowContext())
    assert result2 == {"result": "cached"}
    assert mock.call_count == 1  # Not called again


@pytest.mark.asyncio
async def test_cache_miss_different_keys() -> None:
    """Test cache miss with different keys."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock, cache_key_fn=lambda data, ctx: data["key"], ttl_seconds=60.0
    )

    await cached.execute({"key": "a"}, WorkflowContext())
    await cached.execute({"key": "b"}, WorkflowContext())

    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_cache_expiration() -> None:
    """Test cache expiration after TTL."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock,
        cache_key_fn=lambda data, ctx: "key",
        ttl_seconds=0.1,  # Very short TTL
    )

    # First call
    await cached.execute({}, WorkflowContext())
    assert mock.call_count == 1

    # Wait for expiration
    time.sleep(0.2)

    # Second call after expiration
    await cached.execute({}, WorkflowContext())
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_cache_clear() -> None:
    """Test cache clearing."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(primitive=mock, cache_key_fn=lambda data, ctx: "key", ttl_seconds=60.0)

    await cached.execute({}, WorkflowContext())
    assert cached.get_stats()["size"] == 1

    cached.clear_cache()
    assert cached.get_stats()["size"] == 0


@pytest.mark.asyncio
async def test_cache_stats() -> None:
    """Test cache statistics."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock, cache_key_fn=lambda data, ctx: data.get("key", "default"), ttl_seconds=60.0
    )

    # Initial stats
    stats = cached.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["hit_rate"] == 0.0

    # First call - miss
    await cached.execute({"key": "a"}, WorkflowContext())
    stats = cached.get_stats()
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.0

    # Second call same key - hit
    await cached.execute({"key": "a"}, WorkflowContext())
    stats = cached.get_stats()
    assert stats["hits"] == 1
    assert stats["hit_rate"] == 50.0

    # Third call same key - hit
    await cached.execute({"key": "a"}, WorkflowContext())
    stats = cached.get_stats()
    assert stats["hits"] == 2
    assert stats["hit_rate"] == 66.67


@pytest.mark.asyncio
async def test_cache_context_tracking() -> None:
    """Test cache hit/miss tracking in context."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(primitive=mock, cache_key_fn=lambda data, ctx: "key", ttl_seconds=60.0)

    context = WorkflowContext()

    # First call - miss
    await cached.execute({}, context)
    assert context.state["cache_misses"] == 1
    assert "cache_hits" not in context.state

    # Second call - hit
    await cached.execute({}, context)
    assert context.state["cache_hits"] == 1
    assert context.state["cache_misses"] == 1


@pytest.mark.asyncio
async def test_cache_eviction() -> None:
    """Test manual cache eviction."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock, cache_key_fn=lambda data, ctx: data["key"], ttl_seconds=0.1
    )

    # Add some entries
    await cached.execute({"key": "a"}, WorkflowContext())
    await cached.execute({"key": "b"}, WorkflowContext())

    assert cached.get_stats()["size"] == 2

    # Wait for expiration
    time.sleep(0.2)

    # Manually evict
    evicted = cached.evict_expired()
    assert evicted == 2
    assert cached.get_stats()["size"] == 0


@pytest.mark.asyncio
async def test_cache_realistic_llm_scenario() -> None:
    """Test realistic LLM caching scenario."""
    call_count = 0

    def llm_mock(name, response):
        async def llm_call(data, ctx):
            nonlocal call_count
            call_count += 1
            return {"response": response, "call": call_count}

        from tta_workflow_primitives.core.base import LambdaPrimitive

        return LambdaPrimitive(llm_call)

    llm = llm_mock("llm", "Generated story")

    # Cache based on prompt + player
    cached_llm = CachePrimitive(
        primitive=llm,
        cache_key_fn=lambda data, ctx: f"{data['prompt'][:50]}:{ctx.player_id}",
        ttl_seconds=3600.0,
    )

    # Player 1, prompt 1
    ctx1 = WorkflowContext(player_id="player1")
    result = await cached_llm.execute({"prompt": "Tell me a story"}, ctx1)
    assert result["call"] == 1

    # Same player, same prompt - cache hit
    result = await cached_llm.execute({"prompt": "Tell me a story"}, ctx1)
    assert result["call"] == 1  # Same call number
    assert call_count == 1  # LLM not called again

    # Different player, same prompt - cache miss (different key)
    ctx2 = WorkflowContext(player_id="player2")
    result = await cached_llm.execute({"prompt": "Tell me a story"}, ctx2)
    assert result["call"] == 2
    assert call_count == 2

    # Same player, different prompt - cache miss
    result = await cached_llm.execute({"prompt": "Different story"}, ctx1)
    assert result["call"] == 3
    assert call_count == 3

    # Check hit rate
    stats = cached_llm.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 3
    assert stats["hit_rate"] == 25.0


@pytest.mark.asyncio
async def test_cache_key_generation() -> None:
    """Test various cache key generation strategies."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    # Simple hash-based key
    cached1 = CachePrimitive(
        primitive=mock, cache_key_fn=lambda data, ctx: str(hash(str(data))), ttl_seconds=60.0
    )

    # Composite key with context
    cached2 = CachePrimitive(
        primitive=mock,
        cache_key_fn=lambda data, ctx: f"{data.get('type')}:{ctx.session_id}",
        ttl_seconds=60.0,
    )

    # Test both
    await cached1.execute({"x": 1}, WorkflowContext())
    await cached2.execute({"type": "story"}, WorkflowContext(session_id="s1"))

    assert cached1.get_stats()["size"] == 1
    assert cached2.get_stats()["size"] == 1
