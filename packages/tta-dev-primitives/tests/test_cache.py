import asyncio

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_cache_primitive_hit():
    """Test cache hit."""
    llm_mock = MockPrimitive("llm", return_value="Generated story")
    cached_llm = CachePrimitive(
        primitive=llm_mock,
        cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.state.get('player_id')}",
        ttl_seconds=60,
    )

    context = WorkflowContext()
    context.state["player_id"] = "player1"

    # First call, cache miss
    result1 = await cached_llm.execute({"prompt": "Tell me a story"}, context)
    assert result1 == "Generated story"
    assert llm_mock.call_count == 1

    # Second call, cache hit
    result2 = await cached_llm.execute({"prompt": "Tell me a story"}, context)
    assert result2 == "Generated story"
    assert llm_mock.call_count == 1  # Should not be called again


@pytest.mark.asyncio
async def test_cache_primitive_miss():
    """Test cache miss."""
    llm_mock = MockPrimitive("llm", return_value="Generated story")
    cached_llm = CachePrimitive(
        primitive=llm_mock,
        cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.state.get('player_id')}",
        ttl_seconds=60,
    )

    context1 = WorkflowContext()
    context1.state["player_id"] = "player1"

    context2 = WorkflowContext()
    context2.state["player_id"] = "player2"

    # First call, cache miss
    await cached_llm.execute({"prompt": "Tell me a story"}, context1)
    assert llm_mock.call_count == 1

    # Different player, cache miss
    await cached_llm.execute({"prompt": "Tell me a story"}, context2)
    assert llm_mock.call_count == 2

    # Different prompt, cache miss
    await cached_llm.execute({"prompt": "Tell me another story"}, context1)
    assert llm_mock.call_count == 3


@pytest.mark.asyncio
async def test_cache_primitive_ttl():
    """Test cache TTL."""
    llm_mock = MockPrimitive("llm", return_value="Generated story")
    cached_llm = CachePrimitive(
        primitive=llm_mock,
        cache_key_fn=lambda data, ctx: f"{data['prompt']}",
        ttl_seconds=0.1,
    )

    context = WorkflowContext()

    # First call, cache miss
    await cached_llm.execute({"prompt": "Tell me a story"}, context)
    assert llm_mock.call_count == 1

    # Second call, cache hit
    await cached_llm.execute({"prompt": "Tell me a story"}, context)
    assert llm_mock.call_count == 1

    # Wait for TTL to expire
    await asyncio.sleep(0.2)

    # Third call, cache miss
    await cached_llm.execute({"prompt": "Tell me a story"}, context)
    assert llm_mock.call_count == 2
