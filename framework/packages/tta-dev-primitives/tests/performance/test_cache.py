import asyncio
import pytest

from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.fixture
def mock_primitive():
    return MockPrimitive(name="mock_primitive", return_value="mock_result")

@pytest.fixture
def cache_key_fn():
    return lambda data, ctx: str(data)

@pytest.mark.asyncio
async def test_cache_basic_caching(mock_primitive, cache_key_fn):
    """Tests that a result is returned from the cache on a second call."""
    cached_primitive = CachePrimitive(mock_primitive, cache_key_fn)
    context = WorkflowContext()
    input_data = {"key": "value"}

    # First call, should be a miss
    result1 = await cached_primitive.execute(input_data, context)
    assert result1 == "mock_result"
    assert mock_primitive.call_count == 1
    stats = cached_primitive.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    # Second call, should be a hit
    result2 = await cached_primitive.execute(input_data, context)
    assert result2 == "mock_result"
    assert mock_primitive.call_count == 1  # Should not be called again
    stats = cached_primitive.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 1

@pytest.mark.asyncio
async def test_cache_miss(mock_primitive, cache_key_fn):
    """Tests that the underlying primitive is called on a cache miss."""
    cached_primitive = CachePrimitive(mock_primitive, cache_key_fn)
    context = WorkflowContext()

    await cached_primitive.execute({"key": "value1"}, context)
    assert mock_primitive.call_count == 1

    await cached_primitive.execute({"key": "value2"}, context)
    assert mock_primitive.call_count == 2

@pytest.mark.asyncio
async def test_cache_ttl_expiration(mock_primitive, cache_key_fn):
    """Tests that a cached item is evicted after its TTL has passed."""
    cached_primitive = CachePrimitive(mock_primitive, cache_key_fn, ttl_seconds=0.01)
    context = WorkflowContext()
    input_data = {"key": "value"}

    await cached_primitive.execute(input_data, context)
    assert mock_primitive.call_count == 1

    await asyncio.sleep(0.02)

    await cached_primitive.execute(input_data, context)
    assert mock_primitive.call_count == 2
    stats = cached_primitive.get_stats()
    assert stats["expirations"] == 1

@pytest.mark.asyncio
async def test_cache_key_function(mock_primitive):
    """Tests that the cache key is generated correctly."""
    key_fn = lambda data, ctx: f"{data['user']}:{ctx.session_id}"
    cached_primitive = CachePrimitive(mock_primitive, key_fn)

    context1 = WorkflowContext(session_id="session1")
    context2 = WorkflowContext(session_id="session2")

    await cached_primitive.execute({"user": "test"}, context1)
    assert mock_primitive.call_count == 1

    await cached_primitive.execute({"user": "test"}, context2)
    assert mock_primitive.call_count == 2

@pytest.mark.asyncio
async def test_cache_exception_handling(cache_key_fn):
    """Tests that exceptions are propagated and not cached."""
    failing_primitive = MockPrimitive(name="failing", raise_error=ValueError("Failed"))
    cached_primitive = CachePrimitive(failing_primitive, cache_key_fn)
    context = WorkflowContext()
    input_data = {"key": "value"}

    with pytest.raises(ValueError, match="Failed"):
        await cached_primitive.execute(input_data, context)

    assert failing_primitive.call_count == 1
    stats = cached_primitive.get_stats()
    assert stats["misses"] == 1
    assert stats["size"] == 0 # Should not cache failures

    # Second call should still fail and not hit a cache
    with pytest.raises(ValueError, match="Failed"):
        await cached_primitive.execute(input_data, context)
    assert failing_primitive.call_count == 2

def test_cache_clear(mock_primitive, cache_key_fn):
    """Tests that the cache is cleared when clear_cache is called."""
    cached_primitive = CachePrimitive(mock_primitive, cache_key_fn)
    context = WorkflowContext()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(cached_primitive.execute({"key": "value"}, context))

    assert cached_primitive.get_stats()["size"] == 1
    cached_primitive.clear_cache()
    assert cached_primitive.get_stats()["size"] == 0

@pytest.mark.asyncio
async def test_cache_evict_expired(mock_primitive, cache_key_fn):
    """Tests that expired items are evicted."""
    cached_primitive = CachePrimitive(mock_primitive, cache_key_fn, ttl_seconds=0.01)
    context = WorkflowContext()

    # Add two items that will expire
    await cached_primitive.execute({"key": "value1"}, context)
    await cached_primitive.execute({"key": "value2"}, context)

    # Wait for them to expire
    await asyncio.sleep(0.02)

    # Add a third item that will not be expired
    await cached_primitive.execute({"key": "value3"}, context)

    # At this point, size is 3, but 2 are expired
    assert cached_primitive.get_stats()["size"] == 3

    # Manually evict the expired items
    evicted_count = cached_primitive.evict_expired()

    # Assert that the two expired items were evicted
    assert evicted_count == 2

    # Assert that the final cache size is 1
    assert cached_primitive.get_stats()["size"] == 1
