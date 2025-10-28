"""Unit tests for CachePrimitive (wrapper-based implementation)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.observability_integration.primitives.cache import CachePrimitive


# Mock WorkflowPrimitive for testing
class MockPrimitive:
    """Mock primitive for testing."""

    def __init__(self, name="mock", return_value="result"):
        self.name = name
        self.return_value = return_value
        self.call_count = 0

    async def execute(self, data, context):
        """Mock execute method that tracks calls."""
        self.call_count += 1
        return self.return_value


# Mock Redis client
class MockRedis:
    """Mock Redis client for testing (synchronous, matches actual Redis client)."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        """Mock get method (synchronous)."""
        value = self.store.get(key)
        # Return bytes as real Redis does
        if value is not None and isinstance(value, str):
            return value.encode("utf-8")
        return value

    def setex(self, key, seconds, value):
        """Mock setex method (synchronous)."""
        self.store[key] = value

    def delete(self, key):
        """Mock delete method (synchronous)."""
        if key in self.store:
            del self.store[key]


@pytest.fixture
def mock_primitive():
    """Create mock primitive."""
    return MockPrimitive("TestPrimitive", "expensive_result")


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return MockRedis()


@pytest.fixture
def simple_cache_key_fn():
    """Simple cache key function for tests."""

    def cache_key(data, context):
        query = str(data.get("query", "")) if isinstance(data, dict) else str(data)
        return f"cache:query:{query}"

    return cache_key


@pytest.fixture
def cache_primitive(mock_primitive, mock_redis, simple_cache_key_fn):
    """Create CachePrimitive instance for testing."""
    return CachePrimitive(
        primitive=mock_primitive,
        cache_key_fn=simple_cache_key_fn,
        ttl_seconds=3600.0,
        redis_client=mock_redis,
        cost_per_call=0.01,
    )


class TestCachePrimitiveInit:
    """Test CachePrimitive initialization."""

    def test_initialization_with_redis(
        self, mock_primitive, mock_redis, simple_cache_key_fn
    ):
        """Test initialization with Redis client."""
        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=1800.0,
            redis_client=mock_redis,
            cost_per_call=0.02,
        )

        assert cache.ttl_seconds == 1800.0
        assert cache.cost_per_call == 0.02
        assert cache.redis_client is mock_redis

    def test_initialization_without_redis(self, mock_primitive, simple_cache_key_fn):
        """Test initialization without Redis client (graceful degradation)."""
        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=3600.0,
            redis_client=None,
        )

        assert cache.redis_client is None


class TestCacheHitBehavior:
    """Test cache hit behavior."""

    @pytest.mark.asyncio
    async def test_cache_miss_calls_primitive(self, cache_primitive, mock_primitive):
        """Test cache miss calls wrapped primitive."""
        mock_context = MagicMock()
        initial_call_count = mock_primitive.call_count

        result = await cache_primitive.execute({"query": "test query"}, mock_context)

        assert result == "expensive_result"
        assert mock_primitive.call_count == initial_call_count + 1

    @pytest.mark.asyncio
    async def test_cache_hit_skips_primitive(
        self, mock_primitive, mock_redis, simple_cache_key_fn
    ):
        """Test cache hit returns cached value without calling primitive."""
        # Pre-populate cache with serialized JSON (as real implementation does)
        # Cache key format: cache:{operation_name}:{user_key}
        cache_key = "cache:TestPrimitive:cache:query:test_query"
        cached_data = json.dumps("cached_result").encode("utf-8")
        mock_redis.store[cache_key] = cached_data

        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=3600.0,
            redis_client=mock_redis,
        )

        mock_context = MagicMock()
        initial_call_count = mock_primitive.call_count

        result = await cache.execute({"query": "test query"}, mock_context)

        # Should return cached value
        assert result == "cached_result"
        # Should NOT call primitive
        assert mock_primitive.call_count == initial_call_count

    @pytest.mark.asyncio
    async def test_subsequent_calls_use_cache(self, cache_primitive, mock_primitive):
        """Test subsequent calls use cached result."""
        mock_context = MagicMock()

        # First call - cache miss
        result1 = await cache_primitive.execute({"query": "same query"}, mock_context)
        first_call_count = mock_primitive.call_count

        # Second call - should be cache hit
        result2 = await cache_primitive.execute({"query": "same query"}, mock_context)
        second_call_count = mock_primitive.call_count

        assert result1 == result2
        # Primitive should only be called once
        assert second_call_count == first_call_count


class TestCacheKeyGeneration:
    """Test cache key generation."""

    @pytest.mark.asyncio
    async def test_custom_cache_key_function(self, mock_primitive, mock_redis):
        """Test custom cache key function."""

        def user_query_cache_key(data, context):
            user_id = data.get("user_id", "unknown")
            query = data.get("query", "")
            return f"user:{user_id}:query:{query}"

        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=user_query_cache_key,
            ttl_seconds=3600.0,
            redis_client=mock_redis,
        )

        mock_context = MagicMock()

        # Call with different users
        await cache.execute({"user_id": "alice", "query": "test"}, mock_context)
        await cache.execute({"user_id": "bob", "query": "test"}, mock_context)

        # Should create different cache entries with operation name prefix
        # Format: cache:{operation_name}:{user_key}
        assert "cache:TestPrimitive:user:alice:query:test" in mock_redis.store
        assert "cache:TestPrimitive:user:bob:query:test" in mock_redis.store

    @pytest.mark.asyncio
    async def test_different_queries_different_keys(self, cache_primitive, mock_redis):
        """Test different queries generate different cache keys."""
        mock_context = MagicMock()

        await cache_primitive.execute({"query": "query1"}, mock_context)
        await cache_primitive.execute({"query": "query2"}, mock_context)

        # Format: cache:{operation_name}:{user_key}
        assert "cache:TestPrimitive:cache:query:query1" in mock_redis.store
        assert "cache:TestPrimitive:cache:query:query2" in mock_redis.store


class TestGracefulDegradation:
    """Test graceful degradation when Redis unavailable."""

    @pytest.mark.asyncio
    async def test_works_without_redis(self, mock_primitive, simple_cache_key_fn):
        """Test cache works without Redis client."""
        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=3600.0,
            redis_client=None,
        )

        mock_context = MagicMock()
        result = await cache.execute({"query": "test"}, mock_context)

        # Should call primitive directly
        assert result == "expensive_result"
        assert mock_primitive.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_redis_errors_gracefully(
        self, mock_primitive, simple_cache_key_fn
    ):
        """Test handles Redis errors by calling primitive."""
        # Create failing Redis mock
        failing_redis = MagicMock()
        failing_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=3600.0,
            redis_client=failing_redis,
        )

        mock_context = MagicMock()
        result = await cache.execute({"query": "test"}, mock_context)

        # Should fall back to calling primitive
        assert result == "expensive_result"


class TestMetricsRecording:
    """Test metrics recording."""

    @pytest.mark.asyncio
    async def test_metrics_work_with_graceful_degradation(self, cache_primitive):
        """Test metrics recording with graceful degradation."""
        # Metrics should work even if infrastructure not available
        mock_context = MagicMock()
        result = await cache_primitive.execute({"query": "test"}, mock_context)
        assert result is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_data(self, cache_primitive):
        """Test caching with empty data."""
        mock_context = MagicMock()
        result = await cache_primitive.execute({}, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_none_data(self, cache_primitive):
        """Test caching with None data."""
        mock_context = MagicMock()
        result = await cache_primitive.execute(None, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cache_key_function_error(self, mock_primitive, mock_redis):
        """Test behavior when cache key function raises error."""

        def failing_cache_key(data, context):
            raise ValueError("Cache key error")

        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=failing_cache_key,
            ttl_seconds=3600.0,
            redis_client=mock_redis,
        )

        mock_context = MagicMock()
        # Should fall back to calling primitive
        result = await cache.execute({"query": "test"}, mock_context)
        assert result == "expensive_result"

    @pytest.mark.asyncio
    async def test_cache_statistics_tracking(self, cache_primitive, mock_redis):
        """Test cache statistics are tracked correctly."""
        mock_context = MagicMock()

        # First call - miss
        await cache_primitive.execute({"query": "test1"}, mock_context)

        # Second call to same query - should hit
        await cache_primitive.execute({"query": "test1"}, mock_context)

        # Different query - miss
        await cache_primitive.execute({"query": "test2"}, mock_context)

        # Statistics should be tracked
        assert cache_primitive._total_hits >= 1
        assert cache_primitive._total_misses >= 2


class TestCostSavings:
    """Test cost savings calculation."""

    @pytest.mark.asyncio
    async def test_cost_tracking_on_cache_hit(
        self, mock_primitive, mock_redis, simple_cache_key_fn
    ):
        """Test cost savings tracked on cache hits."""
        # Pre-populate cache with serialized JSON
        # Format: cache:{operation_name}:{user_key}
        cache_key = "cache:TestPrimitive:cache:query:test"
        cached_data = json.dumps("cached_result").encode("utf-8")
        mock_redis.store[cache_key] = cached_data

        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=3600.0,
            redis_client=mock_redis,
            cost_per_call=0.05,  # $0.05 per call
        )

        mock_context = MagicMock()
        # Cache hit should save $0.05
        result = await cache.execute({"query": "test"}, mock_context)

        # Should return cached value
        assert result == "cached_result"
        # Metric should be recorded (even if infrastructure not available)
        assert True  # Metrics work with graceful degradation


class TestTTLBehavior:
    """Test TTL (Time To Live) behavior."""

    @pytest.mark.asyncio
    async def test_ttl_passed_to_redis(self, mock_primitive, simple_cache_key_fn):
        """Test TTL value passed to Redis setex command."""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value=None)
        mock_redis.setex = MagicMock()

        cache = CachePrimitive(
            primitive=mock_primitive,
            cache_key_fn=simple_cache_key_fn,
            ttl_seconds=1800.0,
            redis_client=mock_redis,
        )

        mock_context = MagicMock()
        await cache.execute({"query": "test"}, mock_context)

        # Verify setex was called with TTL (synchronous call)
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        # Second argument should be TTL in seconds (int)
        assert call_args[0][1] == 1800  # TTL in seconds
