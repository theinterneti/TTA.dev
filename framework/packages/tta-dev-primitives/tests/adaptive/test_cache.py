"""Tests for AdaptiveCachePrimitive."""

import asyncio
import time

import pytest

from tta_dev_primitives.adaptive import (
    AdaptiveCachePrimitive,
    LearningMode,
)
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class ExpensiveQuery(InstrumentedPrimitive[dict, dict]):
    """Mock expensive query for testing caching."""

    def __init__(self, execution_time: float = 0.1):
        super().__init__()
        self.execution_time = execution_time
        self.call_count = 0
        self.call_history = []

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute expensive query."""
        self.call_count += 1
        query_id = input_data.get("id", "default")
        self.call_history.append(query_id)

        # Simulate expensive operation
        await asyncio.sleep(self.execution_time)

        return {
            "result": f"query_result_{query_id}",
            "timestamp": time.time(),
            "call_number": self.call_count,
        }


@pytest.fixture
def expensive_query():
    """Expensive query for testing."""
    return ExpensiveQuery(execution_time=0.05)


@pytest.fixture
def context():
    """Workflow context."""
    return WorkflowContext(correlation_id="test-cache", metadata={"environment": "test"})


@pytest.fixture
def cache_key_fn():
    """Simple cache key function."""
    return lambda data, ctx: f"key:{data.get('id', 'default')}"


class TestAdaptiveCacheInitialization:
    """Test initialization of AdaptiveCachePrimitive."""

    def test_initialization_with_defaults(self, expensive_query, cache_key_fn):
        """Test default initialization."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        assert adaptive.target_primitive == expensive_query
        assert adaptive.cache_key_fn == cache_key_fn
        assert adaptive.learning_mode == LearningMode.VALIDATE
        assert len(adaptive.strategies) == 1  # Just baseline
        assert "baseline_conservative" in adaptive.strategies

    def test_initialization_with_custom_mode(self, expensive_query, cache_key_fn):
        """Test initialization with custom learning mode."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query,
            cache_key_fn=cache_key_fn,
            learning_mode=LearningMode.ACTIVE,
        )

        assert adaptive.learning_mode == LearningMode.ACTIVE

    def test_baseline_strategy_parameters(self, expensive_query, cache_key_fn):
        """Test baseline strategy has cache parameters."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        baseline = adaptive.strategies["baseline_conservative"]
        assert "ttl_seconds" in baseline.parameters
        assert "max_cache_size" in baseline.parameters
        assert baseline.parameters["ttl_seconds"] == 3600.0  # Default 1 hour


class TestBasicCacheBehavior:
    """Test basic caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_hit_on_repeated_calls(self, expensive_query, cache_key_fn, context):
        """Test cache returns same result for same input."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # First call - cache miss
        result1 = await adaptive.execute({"id": "test1"}, context)
        assert result1["result"] == "query_result_test1"
        assert expensive_query.call_count == 1

        # Second call - should be cache hit
        result2 = await adaptive.execute({"id": "test1"}, context)
        assert result2["result"] == "query_result_test1"
        assert expensive_query.call_count == 1  # No additional call

        # Same timestamp means cache hit
        assert result1["timestamp"] == result2["timestamp"]

    @pytest.mark.asyncio
    async def test_different_keys_cached_separately(self, expensive_query, cache_key_fn, context):
        """Test different cache keys are stored separately."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # Call with different IDs
        result1 = await adaptive.execute({"id": "test1"}, context)
        result2 = await adaptive.execute({"id": "test2"}, context)
        result3 = await adaptive.execute({"id": "test1"}, context)  # Repeat test1

        assert expensive_query.call_count == 2  # Only test1 and test2
        assert result1["result"] == "query_result_test1"
        assert result2["result"] == "query_result_test2"
        assert result3["result"] == "query_result_test1"
        assert result1["timestamp"] == result3["timestamp"]  # Cache hit

    @pytest.mark.asyncio
    async def test_cache_statistics(self, expensive_query, cache_key_fn, context):
        """Test cache statistics tracking."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # Execute multiple queries
        await adaptive.execute({"id": "test1"}, context)
        await adaptive.execute({"id": "test1"}, context)  # Hit
        await adaptive.execute({"id": "test2"}, context)
        await adaptive.execute({"id": "test1"}, context)  # Hit

        stats = adaptive.get_cache_stats()

        assert stats["total_hits"] == 2
        assert stats["total_misses"] == 2
        assert stats["overall_hit_rate"] == 0.5  # 50%
        assert stats["total_size"] == 2  # Two unique keys

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, expensive_query, cache_key_fn, context):
        """Test that cache entries expire based on TTL."""
        # Use very short TTL for testing
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # Override baseline strategy with short TTL
        adaptive.baseline_strategy.parameters["ttl_seconds"] = 0.1

        # First call - cache miss
        result1 = await adaptive.execute({"id": "test1"}, context)
        assert expensive_query.call_count == 1

        # Immediate second call - cache hit
        result2 = await adaptive.execute({"id": "test1"}, context)
        assert expensive_query.call_count == 1
        assert result1["timestamp"] == result2["timestamp"]

        # Wait for TTL to expire
        await asyncio.sleep(0.15)

        # Third call after TTL - cache miss (fresh query)
        result3 = await adaptive.execute({"id": "test1"}, context)
        assert expensive_query.call_count == 2  # New call
        assert result1["timestamp"] != result3["timestamp"]  # Different timestamp


class TestCacheLearning:
    """Test TTL learning behavior."""

    @pytest.mark.asyncio
    async def test_learns_from_reuse_patterns(self, cache_key_fn):
        """Test learning optimal TTL from reuse patterns."""
        query = ExpensiveQuery(execution_time=0.01)
        adaptive = AdaptiveCachePrimitive(
            target_primitive=query,
            cache_key_fn=cache_key_fn,
            learning_mode=LearningMode.ACTIVE,
        )

        context = WorkflowContext(metadata={"environment": "production"})

        # Simulate high-reuse pattern (same IDs repeated)
        for _ in range(10):
            for id_num in range(5):
                await adaptive.execute({"id": f"user{id_num}"}, context)

        # Should have executed multiple times
        assert query.call_count >= 5  # At least the unique keys

        stats = adaptive.get_cache_stats()
        # Should have decent hit rate
        assert stats["overall_hit_rate"] > 0.5

    @pytest.mark.asyncio
    async def test_different_contexts_learn_separately(self, cache_key_fn):
        """Test context-specific learning."""
        query = ExpensiveQuery(execution_time=0.01)
        adaptive = AdaptiveCachePrimitive(
            target_primitive=query,
            cache_key_fn=cache_key_fn,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute with production context
        prod_context = WorkflowContext(metadata={"environment": "production"})
        for _ in range(5):
            await adaptive.execute({"id": "test1"}, prod_context)

        # Execute with staging context
        staging_context = WorkflowContext(metadata={"environment": "staging"})
        for _ in range(5):
            await adaptive.execute({"id": "test2"}, staging_context)

        # Should have tracked both contexts
        stats = adaptive.get_cache_stats()
        assert len(stats["contexts"]) >= 1  # At least one context tracked

    @pytest.mark.asyncio
    async def test_learning_mode_observe_only(self, expensive_query, cache_key_fn):
        """Test OBSERVE mode doesn't create new strategies."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query,
            cache_key_fn=cache_key_fn,
            learning_mode=LearningMode.OBSERVE,
        )

        context = WorkflowContext(metadata={"environment": "test"})

        # Execute many times to trigger potential learning
        for _ in range(30):
            await adaptive.execute({"id": "test1"}, context)

        # Should only have baseline strategy in OBSERVE mode
        assert len(adaptive.strategies) == 1
        assert "baseline_conservative" in adaptive.strategies


class TestStrategyParameters:
    """Test learned strategy parameters."""

    @pytest.mark.asyncio
    async def test_strategy_has_cache_parameters(self, expensive_query, cache_key_fn, context):
        """Test that strategies have cache parameters."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query,
            cache_key_fn=cache_key_fn,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute enough to potentially learn
        for i in range(25):
            await adaptive.execute({"id": f"test{i % 5}"}, context)

        # Check all strategies have required parameters
        for strategy in adaptive.strategies.values():
            assert "ttl_seconds" in strategy.parameters
            assert "max_cache_size" in strategy.parameters
            assert strategy.parameters["ttl_seconds"] > 0

    @pytest.mark.asyncio
    async def test_baseline_always_available(self, expensive_query, cache_key_fn):
        """Test baseline strategy is always available."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query,
            cache_key_fn=cache_key_fn,
            learning_mode=LearningMode.ACTIVE,
        )

        # Baseline should exist immediately
        assert "baseline_conservative" in adaptive.strategies

        context = WorkflowContext(metadata={"environment": "test"})

        # Should still exist after executions
        for _ in range(10):
            await adaptive.execute({"id": "test"}, context)

        assert "baseline_conservative" in adaptive.strategies


class TestCacheManagement:
    """Test cache management operations."""

    @pytest.mark.asyncio
    async def test_clear_cache(self, expensive_query, cache_key_fn, context):
        """Test cache clearing."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # Populate cache
        await adaptive.execute({"id": "test1"}, context)
        await adaptive.execute({"id": "test2"}, context)

        stats_before = adaptive.get_cache_stats()
        assert stats_before["total_size"] == 2

        # Clear cache
        adaptive.clear_cache()

        stats_after = adaptive.get_cache_stats()
        assert stats_after["total_size"] == 0

        # Next query should be cache miss
        await adaptive.execute({"id": "test1"}, context)
        assert expensive_query.call_count == 3  # 2 initial + 1 after clear

    @pytest.mark.asyncio
    async def test_evict_expired(self, expensive_query, cache_key_fn, context):
        """Test expired entry eviction."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # Override with short TTL
        adaptive.baseline_strategy.parameters["ttl_seconds"] = 0.1

        # Populate cache
        await adaptive.execute({"id": "test1"}, context)
        await adaptive.execute({"id": "test2"}, context)

        assert adaptive.get_cache_stats()["total_size"] == 2

        # Wait for expiration
        await asyncio.sleep(0.15)

        # Evict expired entries
        evicted_count = adaptive.evict_expired()
        assert evicted_count == 2

        stats = adaptive.get_cache_stats()
        assert stats["total_size"] == 0


class TestPerformanceMetrics:
    """Test cache performance tracking."""

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self, expensive_query, cache_key_fn, context):
        """Test hit rate is calculated correctly."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # 3 misses (unique keys)
        await adaptive.execute({"id": "test1"}, context)
        await adaptive.execute({"id": "test2"}, context)
        await adaptive.execute({"id": "test3"}, context)

        # 6 hits (2 hits per key)
        await adaptive.execute({"id": "test1"}, context)
        await adaptive.execute({"id": "test1"}, context)
        await adaptive.execute({"id": "test2"}, context)
        await adaptive.execute({"id": "test2"}, context)
        await adaptive.execute({"id": "test3"}, context)
        await adaptive.execute({"id": "test3"}, context)

        stats = adaptive.get_cache_stats()
        assert stats["total_hits"] == 6
        assert stats["total_misses"] == 3
        assert stats["overall_hit_rate"] == pytest.approx(0.666, abs=0.01)  # 6/9

    @pytest.mark.asyncio
    async def test_context_specific_metrics(self, expensive_query, cache_key_fn):
        """Test metrics are tracked per context."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        prod_context = WorkflowContext(metadata={"environment": "production"})
        staging_context = WorkflowContext(metadata={"environment": "staging"})

        # Production queries with high reuse
        await adaptive.execute({"id": "prod1"}, prod_context)
        await adaptive.execute({"id": "prod1"}, prod_context)
        await adaptive.execute({"id": "prod1"}, prod_context)

        # Staging queries with low reuse
        await adaptive.execute({"id": "staging1"}, staging_context)
        await adaptive.execute({"id": "staging2"}, staging_context)
        await adaptive.execute({"id": "staging3"}, staging_context)

        stats = adaptive.get_cache_stats()

        # Should have context-specific metrics
        assert "contexts" in stats
        assert len(stats["contexts"]) >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_cache_stats(self, expensive_query, cache_key_fn):
        """Test statistics on empty cache."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        stats = adaptive.get_cache_stats()
        assert stats["total_hits"] == 0
        assert stats["total_misses"] == 0
        assert stats["overall_hit_rate"] == 0.0
        assert stats["total_size"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_access(self, expensive_query, cache_key_fn, context):
        """Test cache handles concurrent access correctly."""
        adaptive = AdaptiveCachePrimitive(
            target_primitive=expensive_query, cache_key_fn=cache_key_fn
        )

        # First, prime the cache
        first_result = await adaptive.execute({"id": "test1"}, context)

        # Then execute same query concurrently (should all be cache hits)
        tasks = [adaptive.execute({"id": "test1"}, context) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All results should be identical (from cache)
        for result in results:
            assert result["timestamp"] == first_result["timestamp"]

        # Should have made only 1 call total (the initial one)
        assert expensive_query.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_with_none_values(self, cache_key_fn, context):
        """Test caching works with None return values."""

        class NullableQuery(InstrumentedPrimitive[dict, dict | None]):
            """Query that may return None."""

            def __init__(self):
                super().__init__()
                self.call_count = 0

            async def _execute_impl(
                self, input_data: dict, context: WorkflowContext
            ) -> dict | None:
                self.call_count += 1
                if input_data.get("id") == "missing":
                    return None
                return {"result": "found"}

        query = NullableQuery()
        adaptive = AdaptiveCachePrimitive(target_primitive=query, cache_key_fn=cache_key_fn)

        # First call - returns None
        result1 = await adaptive.execute({"id": "missing"}, context)
        assert result1 is None
        assert query.call_count == 1

        # Second call - should cache None
        result2 = await adaptive.execute({"id": "missing"}, context)
        assert result2 is None
        assert query.call_count == 1  # Cache hit, no new call
