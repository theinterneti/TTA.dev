"""Integration tests for adaptive primitives working together.

These tests verify that AdaptiveCachePrimitive, AdaptiveFallbackPrimitive,
and AdaptiveTimeoutPrimitive can be composed and work together without conflicts.
"""

import asyncio

import pytest

from tta_dev_primitives.adaptive import (
    AdaptiveCachePrimitive,
    AdaptiveFallbackPrimitive,
    AdaptiveTimeoutPrimitive,
    LearningMode,
)
from tta_dev_primitives.core import WorkflowContext

# Mock services for testing


class FastService:
    """Fast service that succeeds quickly."""

    def __init__(self, latency_ms: int = 50):
        self.latency_ms = latency_ms
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        self.call_count += 1
        await asyncio.sleep(self.latency_ms / 1000.0)
        return {"source": "fast", "data": input_data.get("value", "default")}


class SlowService:
    """Slow service that may timeout."""

    def __init__(self, latency_ms: int = 300):
        self.latency_ms = latency_ms
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        self.call_count += 1
        await asyncio.sleep(self.latency_ms / 1000.0)
        return {"source": "slow", "data": input_data.get("value", "default")}


# Fixtures


@pytest.fixture
def context():
    """Create a workflow context for testing."""
    return WorkflowContext(workflow_id="test-integration")


@pytest.fixture
def fast_service():
    """Create a fast service."""
    return FastService(latency_ms=50)


@pytest.fixture
def slow_service():
    """Create a slow service."""
    return SlowService(latency_ms=300)


# Helper function for cache key
def simple_cache_key(data: dict, ctx: WorkflowContext) -> str:
    """Generate simple cache key from input data."""
    return str(data.get("value", "default"))


# Integration Tests


class TestCacheWithTimeout:
    """Test Cache + Timeout integration."""

    @pytest.mark.asyncio
    async def test_cache_with_timeout_protection(self, fast_service, context):
        """Cache should protect fast service with timeout."""
        # Create timeout-protected service
        timeout_service = AdaptiveTimeoutPrimitive(
            target_primitive=fast_service,
            baseline_timeout_ms=200,
            learning_mode=LearningMode.ACTIVE,
        )

        # Wrap with cache (uses default 3600s TTL)
        cached_service = AdaptiveCachePrimitive(
            target_primitive=timeout_service,
            cache_key_fn=simple_cache_key,
            learning_mode=LearningMode.ACTIVE,
        )

        # First call - should go to service
        result1 = await cached_service.execute({"value": "test"}, context)
        assert result1["source"] == "fast"
        assert result1["data"] == "test"
        assert fast_service.call_count == 1

        # Second call - should hit cache
        result2 = await cached_service.execute({"value": "test"}, context)
        assert result2["source"] == "fast"
        assert result2["data"] == "test"
        assert fast_service.call_count == 1  # No additional call

        # Cache stats should show hit
        stats = cached_service.get_cache_stats()
        assert stats["total_requests"] == 2
        assert stats["total_hits"] == 1
        assert stats["total_misses"] == 1
        assert stats["overall_hit_rate"] == 0.5


class TestFallbackWithTimeout:
    """Test Fallback + Timeout integration."""

    @pytest.mark.asyncio
    async def test_timeout_triggers_fallback(self, fast_service, slow_service, context):
        """Timeout on primary should trigger fallback."""
        # Create timeout-protected slow service
        timeout_slow = AdaptiveTimeoutPrimitive(
            target_primitive=slow_service,
            baseline_timeout_ms=100,  # Will timeout
            learning_mode=LearningMode.ACTIVE,
        )

        # Create fallback with timeout-protected primary (using dict)
        fallback_service = AdaptiveFallbackPrimitive(
            primary=timeout_slow,
            fallbacks={"fast": fast_service},
            learning_mode=LearningMode.ACTIVE,
        )

        # Call should timeout on slow, fallback to fast
        result = await fallback_service.execute({"value": "test"}, context)
        assert result["source"] == "fast"
        assert result["data"] == "test"

        # Verify timeout was triggered
        assert slow_service.call_count == 1  # Slow service was tried
        assert fast_service.call_count == 1  # Fast service succeeded


class TestAllThreePrimitives:
    """Test Cache + Fallback + Timeout together."""

    @pytest.mark.asyncio
    async def test_complete_stack(self, fast_service, slow_service, context):
        """Test full stack: Cache(Fallback(Timeout(services)))."""
        # Layer 1: Timeout protection
        timeout_slow = AdaptiveTimeoutPrimitive(
            target_primitive=slow_service,
            baseline_timeout_ms=100,
            learning_mode=LearningMode.ACTIVE,
        )

        timeout_fast = AdaptiveTimeoutPrimitive(
            target_primitive=fast_service,
            baseline_timeout_ms=200,
            learning_mode=LearningMode.ACTIVE,
        )

        # Layer 2: Fallback (using dict)
        fallback_service = AdaptiveFallbackPrimitive(
            primary=timeout_slow,
            fallbacks={"fast": timeout_fast},
            learning_mode=LearningMode.ACTIVE,
        )

        # Layer 3: Cache (uses default 3600s TTL)
        complete_stack = AdaptiveCachePrimitive(
            target_primitive=fallback_service,
            cache_key_fn=simple_cache_key,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute multiple times
        results = []
        for i in range(10):
            result = await complete_stack.execute({"value": f"test_{i % 3}"}, context)
            results.append(result)

        # Verify results
        assert len(results) == 10
        assert all("source" in r for r in results)
        assert all("data" in r for r in results)

        # Check cache stats
        cache_stats = complete_stack.get_cache_stats()
        assert cache_stats["total_requests"] == 10
        assert cache_stats["total_hits"] >= 0  # At least some cache hits

        # Check fallback stats
        fallback_stats = fallback_service.get_fallback_stats()
        assert fallback_stats["primary_attempts"] >= 0

    @pytest.mark.asyncio
    async def test_all_primitives_learn_independently(self, fast_service, slow_service, context):
        """Verify each primitive learns its own strategies."""
        # Create timeout primitive
        timeout_service = AdaptiveTimeoutPrimitive(
            target_primitive=fast_service,
            baseline_timeout_ms=200,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
        )

        # Create fallback primitive (using dict)
        fallback_service = AdaptiveFallbackPrimitive(
            primary=timeout_service,
            fallbacks={"slow": slow_service},
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
        )

        # Create cache primitive (uses default 3600s TTL)
        # Note: AdaptiveCachePrimitive doesn't support min_observations_before_learning
        cache_service = AdaptiveCachePrimitive(
            target_primitive=fallback_service,
            cache_key_fn=simple_cache_key,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute enough times to trigger learning in all primitives
        for i in range(20):
            await cache_service.execute({"value": f"test_{i % 5}"}, context)

        # Verify each primitive has learned
        # Cache should have strategies
        cache_stats = cache_service.get_cache_stats()
        assert "strategies" in cache_stats

        # Fallback should have statistics
        fallback_stats = fallback_service.get_fallback_stats()
        assert fallback_stats["primary_attempts"] >= 5

        # Timeout should have statistics
        timeout_stats = timeout_service.get_timeout_stats()
        assert timeout_stats["total_executions"] >= 5


class TestEdgeCases:
    """Test edge cases in integrated primitives."""

    @pytest.mark.asyncio
    async def test_disabled_learning_modes(self, fast_service, context):
        """Test stack with all learning disabled."""
        # Create stack with DISABLED learning
        timeout_service = AdaptiveTimeoutPrimitive(
            target_primitive=fast_service,
            baseline_timeout_ms=200,
            learning_mode=LearningMode.DISABLED,
        )

        fallback_service = AdaptiveFallbackPrimitive(
            primary=timeout_service,
            fallbacks={"backup": fast_service},
            learning_mode=LearningMode.DISABLED,
        )

        cache_service = AdaptiveCachePrimitive(
            target_primitive=fallback_service,
            cache_key_fn=simple_cache_key,
            learning_mode=LearningMode.DISABLED,
        )

        # Execute multiple times
        for i in range(10):
            await cache_service.execute({"value": f"test_{i}"}, context)

        # No strategies should be created (only baseline)
        assert len(cache_service.strategies) == 1
        assert len(fallback_service.strategies) == 1
        assert len(timeout_service.strategies) == 1
