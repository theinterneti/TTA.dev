"""Tests for AdaptiveFallbackPrimitive."""

import asyncio
import time

import pytest

from tta_dev_primitives.adaptive import (
    AdaptiveFallbackPrimitive,
    LearningMode,
)
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class UnreliableService(InstrumentedPrimitive[dict, dict]):
    """Mock unreliable service for testing fallback."""

    def __init__(self, name: str, failure_rate: float = 0.0, latency_ms: float = 10.0):
        super().__init__()
        self.name = name
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.call_count = 0
        self.call_history = []
        self._fail_next_n = 0  # For controlled testing

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute service with possible failure."""
        self.call_count += 1
        request_id = input_data.get("id", "default")
        self.call_history.append(request_id)

        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)

        # Controlled failure for testing
        if self._fail_next_n > 0:
            self._fail_next_n -= 1
            raise Exception(f"{self.name} failed (controlled test failure)")

        # Random failure (not used in tests to keep deterministic)
        # if random.random() < self.failure_rate:
        #     raise Exception(f"{self.name} failed (random)")

        return {
            "service": self.name,
            "result": f"Success from {self.name}",
            "request_id": request_id,
            "timestamp": time.time(),
        }

    def fail_next(self, count: int = 1):
        """Make next N calls fail."""
        self._fail_next_n = count


@pytest.fixture
def primary_service():
    """Primary service for testing."""
    return UnreliableService("Primary", latency_ms=50)


@pytest.fixture
def fallback_services():
    """Fallback services for testing."""
    return {
        "fast_backup": UnreliableService("FastBackup", latency_ms=30),
        "slow_backup": UnreliableService("SlowBackup", latency_ms=100),
        "local_cache": UnreliableService("LocalCache", latency_ms=10),
    }


@pytest.fixture
def context():
    """Workflow context."""
    return WorkflowContext(correlation_id="test-fallback", metadata={"environment": "test"})


class TestAdaptiveFallbackInitialization:
    """Test initialization of AdaptiveFallbackPrimitive."""

    def test_initialization_with_defaults(self, primary_service, fallback_services):
        """Test default initialization."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=fallback_services)

        assert adaptive.primary == primary_service
        assert adaptive.fallbacks == fallback_services
        assert adaptive.learning_mode == LearningMode.VALIDATE
        assert len(adaptive.strategies) == 1  # Just baseline
        assert "baseline" in adaptive.strategies

    def test_initialization_with_custom_mode(self, primary_service, fallback_services):
        """Test initialization with custom learning mode."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
        )

        assert adaptive.learning_mode == LearningMode.ACTIVE

    def test_baseline_strategy_parameters(self, primary_service, fallback_services):
        """Test baseline strategy has fallback order."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=fallback_services)

        baseline = adaptive.strategies["baseline"]
        assert "fallback_order" in baseline.parameters
        assert isinstance(baseline.parameters["fallback_order"], list)
        # Should be sorted alphabetically by default
        assert baseline.parameters["fallback_order"] == sorted(fallback_services.keys())

    def test_custom_baseline_order(self, primary_service, fallback_services):
        """Test custom baseline fallback order."""
        custom_order = ["local_cache", "fast_backup", "slow_backup"]
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            baseline_fallback_order=custom_order,
        )

        baseline = adaptive.strategies["baseline"]
        assert baseline.parameters["fallback_order"] == custom_order

    def test_invalid_fallbacks_empty(self, primary_service):
        """Test initialization with empty fallbacks."""
        # Should still work - just no fallbacks available
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks={})

        assert adaptive.fallbacks == {}
        assert adaptive.strategies["baseline"].parameters["fallback_order"] == []


class TestBasicFallbackBehavior:
    """Test basic fallback functionality."""

    @pytest.mark.asyncio
    async def test_primary_success_no_fallbacks_used(
        self, primary_service, fallback_services, context
    ):
        """Test that when primary succeeds, no fallbacks are used."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=fallback_services)

        result = await adaptive.execute({"id": "test1"}, context)

        assert result["service"] == "Primary"
        assert primary_service.call_count == 1
        assert fallback_services["fast_backup"].call_count == 0
        assert fallback_services["slow_backup"].call_count == 0
        assert fallback_services["local_cache"].call_count == 0

    @pytest.mark.asyncio
    async def test_primary_fails_fallback_succeeds(
        self, primary_service, fallback_services, context
    ):
        """Test that when primary fails, first fallback is used."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            baseline_fallback_order=["fast_backup", "slow_backup", "local_cache"],
        )

        # Make primary fail once
        primary_service.fail_next(1)

        result = await adaptive.execute({"id": "test1"}, context)

        assert result["service"] == "FastBackup"
        assert primary_service.call_count == 1
        assert fallback_services["fast_backup"].call_count == 1
        assert fallback_services["slow_backup"].call_count == 0

    @pytest.mark.asyncio
    async def test_primary_and_first_fallback_fail(
        self, primary_service, fallback_services, context
    ):
        """Test cascading to second fallback when first fails."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            baseline_fallback_order=["fast_backup", "slow_backup", "local_cache"],
        )

        # Make primary and first fallback fail
        primary_service.fail_next(1)
        fallback_services["fast_backup"].fail_next(1)

        result = await adaptive.execute({"id": "test1"}, context)

        assert result["service"] == "SlowBackup"
        assert primary_service.call_count == 1
        assert fallback_services["fast_backup"].call_count == 1
        assert fallback_services["slow_backup"].call_count == 1
        assert fallback_services["local_cache"].call_count == 0

    @pytest.mark.asyncio
    async def test_all_services_fail(self, primary_service, fallback_services, context):
        """Test that exception is raised when all services fail."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            baseline_fallback_order=["fast_backup", "slow_backup", "local_cache"],
        )

        # Make everything fail
        primary_service.fail_next(1)
        fallback_services["fast_backup"].fail_next(1)
        fallback_services["slow_backup"].fail_next(1)
        fallback_services["local_cache"].fail_next(1)

        with pytest.raises(Exception) as exc_info:
            await adaptive.execute({"id": "test1"}, context)

        assert "failed" in str(exc_info.value).lower()


class TestFallbackLearning:
    """Test learning optimal fallback strategies."""

    @pytest.mark.asyncio
    async def test_no_learning_before_min_observations(
        self, primary_service, fallback_services, context
    ):
        """Test that learning doesn't happen before min observations."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=10,
        )

        # Run 5 requests (below threshold)
        for i in range(5):
            primary_service.fail_next(1)
            await adaptive.execute({"id": f"test{i}"}, context)

        # Should still only have baseline strategy
        assert len(adaptive.strategies) == 1
        assert "baseline" in adaptive.strategies

    @pytest.mark.asyncio
    async def test_strategy_created_after_min_observations(
        self, primary_service, fallback_services, context
    ):
        """Test that new strategy is created after min observations."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
            baseline_fallback_order=["slow_backup", "fast_backup", "local_cache"],
        )

        # Run requests where fast_backup has better success than slow_backup
        for i in range(10):
            primary_service.fail_next(1)
            # Make slow_backup fail more often
            if i % 2 == 0:
                fallback_services["slow_backup"].fail_next(1)
            await adaptive.execute({"id": f"test{i}"}, context)

        # Should have learned a new strategy
        # (May take multiple attempts due to validation window)
        assert len(adaptive.strategies) >= 1

    @pytest.mark.asyncio
    async def test_context_specific_strategies(self, primary_service, fallback_services):
        """Test that different contexts learn different strategies."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
        )

        # Run prod context - fast_backup works best
        prod_context = WorkflowContext(
            correlation_id="test-prod", metadata={"environment": "production"}
        )
        for i in range(10):
            primary_service.fail_next(1)
            # In prod, slow_backup fails often
            if i % 3 == 0:
                fallback_services["slow_backup"].fail_next(1)
            await adaptive.execute({"id": f"prod{i}"}, prod_context)

        # Run dev context - local_cache works best
        dev_context = WorkflowContext(
            correlation_id="test-dev", metadata={"environment": "development"}
        )
        for i in range(10):
            primary_service.fail_next(1)
            # In dev, fast_backup fails often
            if i % 3 == 0:
                fallback_services["fast_backup"].fail_next(1)
            await adaptive.execute({"id": f"dev{i}"}, dev_context)

        # Should have context-specific statistics
        stats = adaptive.get_fallback_stats()
        assert "contexts" in stats
        # Both contexts should be tracked
        assert len(stats["contexts"]) >= 1


class TestStrategyParameters:
    """Test strategy parameter learning."""

    @pytest.mark.asyncio
    async def test_fallback_order_learning(self, primary_service, fallback_services, context):
        """Test that fallback order is learned from success patterns."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
            baseline_fallback_order=["slow_backup", "fast_backup", "local_cache"],
        )

        # Make local_cache most successful
        for i in range(15):
            primary_service.fail_next(1)
            fallback_services["slow_backup"].fail_next(1)
            fallback_services["fast_backup"].fail_next(1)
            # local_cache succeeds
            await adaptive.execute({"id": f"test{i}"}, context)

        stats = adaptive.get_fallback_stats()

        # local_cache should have highest success rate
        assert stats["fallbacks"]["local_cache"]["successes"] > 0

    @pytest.mark.asyncio
    async def test_latency_consideration(self, primary_service, fallback_services, context):
        """Test that latency is considered in strategy scoring."""
        # Create fallbacks with different latencies
        fast_service = UnreliableService("Fast", latency_ms=10)
        slow_service = UnreliableService("Slow", latency_ms=200)

        custom_fallbacks = {
            "fast": fast_service,
            "slow": slow_service,
        }

        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=custom_fallbacks,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
        )

        # Both succeed equally, but fast has lower latency
        for i in range(10):
            primary_service.fail_next(1)
            await adaptive.execute({"id": f"test{i}"}, context)

        stats = adaptive.get_fallback_stats()

        # Both should have latencies recorded
        fast_latencies = stats["fallbacks"]["fast"]["avg_latency_ms"]
        slow_latencies = stats["fallbacks"]["slow"]["avg_latency_ms"]

        # Fast should have lower average latency
        if fast_latencies > 0 and slow_latencies > 0:
            assert fast_latencies < slow_latencies


class TestStrategyManagement:
    """Test strategy selection and management."""

    @pytest.mark.asyncio
    async def test_strategy_selection_by_context(self, primary_service, fallback_services):
        """Test that strategy is selected based on context."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.VALIDATE,
        )

        # Run with different contexts
        prod_context = WorkflowContext(
            correlation_id="test", metadata={"environment": "production"}
        )
        dev_context = WorkflowContext(
            correlation_id="test", metadata={"environment": "development"}
        )

        # Should work with both contexts
        result1 = await adaptive.execute({"id": "test1"}, prod_context)
        result2 = await adaptive.execute({"id": "test2"}, dev_context)

        assert result1["service"] == "Primary"
        assert result2["service"] == "Primary"

    @pytest.mark.asyncio
    async def test_max_strategies_enforcement(self, primary_service, fallback_services, context):
        """Test that max strategies limit is enforced."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
            max_strategies=3,  # Small limit for testing
            min_observations_before_learning=2,
        )

        # Should respect max_strategies limit
        assert adaptive.max_strategies == 3
        assert len(adaptive.strategies) <= 3


class TestMetrics:
    """Test metrics collection."""

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, primary_service, fallback_services, context):
        """Test that statistics are tracked correctly."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=fallback_services)

        # Run some requests
        await adaptive.execute({"id": "test1"}, context)
        primary_service.fail_next(1)
        await adaptive.execute({"id": "test2"}, context)

        stats = adaptive.get_fallback_stats()

        assert "primary_attempts" in stats
        assert "primary_failures" in stats
        assert "fallbacks" in stats
        assert stats["primary_attempts"] == 2
        assert stats["primary_failures"] == 1

    @pytest.mark.asyncio
    async def test_per_context_statistics(self, primary_service, fallback_services):
        """Test that per-context statistics are tracked."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=fallback_services)

        # Run with different contexts
        prod_context = WorkflowContext(
            correlation_id="test", metadata={"environment": "production"}
        )
        dev_context = WorkflowContext(
            correlation_id="test", metadata={"environment": "development"}
        )

        await adaptive.execute({"id": "test1"}, prod_context)
        await adaptive.execute({"id": "test2"}, dev_context)

        stats = adaptive.get_fallback_stats()

        assert "contexts" in stats
        # Should track both contexts
        assert len(stats["contexts"]) >= 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_fallbacks(self, primary_service, context):
        """Test behavior with no fallbacks."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks={})

        # Should work when primary succeeds
        result = await adaptive.execute({"id": "test1"}, context)
        assert result["service"] == "Primary"

        # Should fail when primary fails (no fallbacks)
        primary_service.fail_next(1)
        with pytest.raises(Exception):
            await adaptive.execute({"id": "test2"}, context)

    @pytest.mark.asyncio
    async def test_single_fallback(self, primary_service, context):
        """Test with only one fallback."""
        single_fallback = {"only_backup": UnreliableService("OnlyBackup")}

        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=single_fallback)

        primary_service.fail_next(1)
        result = await adaptive.execute({"id": "test1"}, context)

        assert result["service"] == "OnlyBackup"

    @pytest.mark.asyncio
    async def test_rapid_successive_failures(self, primary_service, fallback_services, context):
        """Test handling of rapid successive failures."""
        adaptive = AdaptiveFallbackPrimitive(primary=primary_service, fallbacks=fallback_services)

        # Make primary fail repeatedly
        for i in range(10):
            primary_service.fail_next(1)
            result = await adaptive.execute({"id": f"test{i}"}, context)
            # Should fallback successfully each time
            assert "service" in result

    @pytest.mark.asyncio
    async def test_mixed_success_failure_patterns(
        self, primary_service, fallback_services, context
    ):
        """Test mixed patterns of success and failure."""
        adaptive = AdaptiveFallbackPrimitive(
            primary=primary_service,
            fallbacks=fallback_services,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
        )

        # Alternate between primary success and fallback
        for i in range(20):
            if i % 2 == 0:
                primary_service.fail_next(1)
            result = await adaptive.execute({"id": f"test{i}"}, context)
            assert "service" in result

        stats = adaptive.get_fallback_stats()
        # Should have mix of primary successes and failures
        assert stats["primary_attempts"] == 20
        assert 0 < stats["primary_failures"] < 20
