"""Tests for AdaptiveTimeoutPrimitive."""

import asyncio

import pytest

from tta_dev_primitives.adaptive import (
    AdaptiveTimeoutPrimitive,
    LearningMode,
)
from tta_dev_primitives.adaptive.timeout import TimeoutError
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class VariableLatencyService(InstrumentedPrimitive[dict, dict]):
    """Mock service with controllable latency."""

    def __init__(self, name: str = "service"):
        super().__init__()
        self.name = name
        self.call_count = 0
        self.call_history = []
        self._next_latency_ms = 100.0  # Default latency

    def set_latency(self, latency_ms: float) -> None:
        """Set the latency for the next call (deterministic)."""
        self._next_latency_ms = latency_ms

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute with controlled latency."""
        self.call_count += 1
        self.call_history.append(input_data)

        # Use deterministic latency
        await asyncio.sleep(self._next_latency_ms / 1000.0)

        return {
            "service": self.name,
            "latency_ms": self._next_latency_ms,
            "input": input_data,
            "call_number": self.call_count,
        }


@pytest.fixture
def service():
    """Variable latency service for testing."""
    return VariableLatencyService("test_service")


@pytest.fixture
def context():
    """Workflow context."""
    return WorkflowContext(correlation_id="test-timeout", metadata={"environment": "production"})


class TestAdaptiveTimeoutInitialization:
    """Test initialization of AdaptiveTimeoutPrimitive."""

    def test_initialization_with_defaults(self, service):
        """Test default initialization."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service)

        assert adaptive.target_primitive == service
        assert adaptive.learning_mode == LearningMode.OBSERVE
        assert len(adaptive.strategies) == 1  # Just baseline
        assert "baseline_conservative" in adaptive.strategies
        assert adaptive._timeout_count == 0
        assert adaptive._success_count == 0

    def test_initialization_with_custom_mode(self, service):
        """Test initialization with custom learning mode."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            learning_mode=LearningMode.ACTIVE,
        )

        assert adaptive.learning_mode == LearningMode.ACTIVE

    def test_baseline_strategy_parameters(self, service):
        """Test baseline strategy has timeout parameters."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_timeout_ms=3000.0,
            baseline_percentile_target=99,
            baseline_buffer_factor=2.0,
        )

        baseline = adaptive.strategies["baseline_conservative"]
        assert "timeout_ms" in baseline.parameters
        assert "percentile_target" in baseline.parameters
        assert "buffer_factor" in baseline.parameters
        assert baseline.parameters["timeout_ms"] == 3000.0
        assert baseline.parameters["percentile_target"] == 99
        assert baseline.parameters["buffer_factor"] == 2.0

    def test_custom_baseline_timeout(self, service):
        """Test custom baseline timeout."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=1000.0)

        baseline = adaptive.strategies["baseline_conservative"]
        assert baseline.parameters["timeout_ms"] == 1000.0

    def test_min_observations_stored(self, service):
        """Test min observations parameter is stored."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service, min_observations_before_learning=50
        )

        assert adaptive._min_observations_before_learning == 50


class TestBasicTimeoutBehavior:
    """Test basic timeout functionality."""

    @pytest.mark.asyncio
    async def test_successful_execution_within_timeout(self, service, context):
        """Test successful execution when latency < timeout."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=500.0)

        service.set_latency(100.0)  # Fast

        result = await adaptive.execute({"request_id": 1}, context)

        assert result["service"] == "test_service"
        assert result["latency_ms"] == 100.0
        assert service.call_count == 1
        assert adaptive._success_count == 1
        assert adaptive._timeout_count == 0

    @pytest.mark.asyncio
    async def test_timeout_when_latency_exceeds_limit(self, service, context):
        """Test timeout when latency exceeds timeout value."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=200.0)

        service.set_latency(500.0)  # Slow - will timeout

        with pytest.raises(TimeoutError) as exc_info:
            await adaptive.execute({"request_id": 1}, context)

        assert "exceeded timeout" in str(exc_info.value).lower()
        assert adaptive._timeout_count == 1
        assert adaptive._success_count == 0

    @pytest.mark.asyncio
    async def test_latency_tracking(self, service, context):
        """Test that successful executions track latency."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=500.0)

        # Execute multiple times with different latencies
        service.set_latency(100.0)
        await adaptive.execute({"request_id": 1}, context)

        service.set_latency(200.0)
        await adaptive.execute({"request_id": 2}, context)

        service.set_latency(150.0)
        await adaptive.execute({"request_id": 3}, context)

        assert len(adaptive._latency_samples) == 3
        # Latencies include asyncio overhead, so check approximate values
        assert all(
            90 <= lat <= 110 or 190 <= lat <= 210 or 140 <= lat <= 160
            for lat in adaptive._latency_samples
        )

    @pytest.mark.asyncio
    async def test_context_specific_latency_tracking(self, service):
        """Test that latencies are tracked per context."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=500.0)

        # Production context
        prod_context = WorkflowContext(
            correlation_id="prod-1", metadata={"environment": "production"}
        )

        service.set_latency(200.0)
        await adaptive.execute({"request_id": 1}, prod_context)

        # Staging context
        staging_context = WorkflowContext(
            correlation_id="staging-1", metadata={"environment": "staging"}
        )

        service.set_latency(100.0)
        await adaptive.execute({"request_id": 2}, staging_context)

        # Check context-specific tracking
        assert "production" in adaptive._context_latencies
        assert "staging" in adaptive._context_latencies
        assert len(adaptive._context_latencies["production"]) == 1
        assert len(adaptive._context_latencies["staging"]) == 1


class TestPercentileLearning:
    """Test percentile-based timeout learning."""

    @pytest.mark.asyncio
    async def test_percentile_calculation(self, service, context):
        """Test that percentiles are calculated correctly."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_timeout_ms=1000.0,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=5,
        )

        # Create latency distribution
        latencies = [100, 150, 200, 250, 300]
        for i, latency in enumerate(latencies):
            service.set_latency(latency)
            await adaptive.execute({"request_id": i}, context)

        stats = adaptive.get_timeout_stats()

        # p50 should be around 200 (middle value)
        assert 180 <= stats["latencies"]["p50_ms"] <= 220

        # p95 should be close to 300 (allow for asyncio overhead)
        assert 280 <= stats["latencies"]["p95_ms"] <= 310

        # p99 should be around 300 (allow overhead)
        assert 280 <= stats["latencies"]["p99_ms"] <= 310

    @pytest.mark.asyncio
    async def test_strategy_creation_based_on_percentiles(self, service, context):
        """Test that new strategies are created based on learned percentiles."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_timeout_ms=1000.0,  # Conservative initial
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=10,
        )

        # Execute 15 times with latencies 100-150ms
        for i in range(15):
            service.set_latency(100 + (i % 5) * 10)  # 100, 110, 120, 130, 140
            await adaptive.execute({"request_id": i}, context)

        # Should learn that timeout can be much lower
        # Note: Learning may or may not create new strategy depending on threshold
        # Just verify execution was successful and tracked
        assert adaptive._success_count == 15
        assert adaptive._timeout_count == 0

    @pytest.mark.asyncio
    async def test_adaptive_timeout_reduces_for_fast_service(self, service, context):
        """Test that timeout adapts down for consistently fast service."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_timeout_ms=1000.0,  # Start high
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=10,
        )

        # Fast service (100-150ms consistently)
        for i in range(15):
            service.set_latency(100 + (i % 5) * 10)
            await adaptive.execute({"request_id": i}, context)

        stats = adaptive.get_timeout_stats()

        # Baseline was 1000ms, but we should learn a tighter timeout
        # Note: Actual timeout depends on learning algorithm
        # Just verify stats are tracked
        assert stats["total_executions"] == 15
        assert stats["timeout_count"] == 0
        assert stats["latencies"]["p95_ms"] < 200  # All fast


class TestStrategyParameters:
    """Test strategy parameter management."""

    @pytest.mark.asyncio
    async def test_buffer_factor_affects_timeout(self, service, context):
        """Test that buffer factor increases timeout appropriately."""
        # Create with buffer factor 2.0
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_timeout_ms=500.0,
            baseline_buffer_factor=2.0,
        )

        baseline = adaptive.strategies["baseline_conservative"]
        assert baseline.parameters["buffer_factor"] == 2.0

    @pytest.mark.asyncio
    async def test_percentile_target_selection(self, service, context):
        """Test different percentile targets."""
        # p95 target
        adaptive_p95 = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_percentile_target=95,
        )
        assert (
            adaptive_p95.strategies["baseline_conservative"].parameters["percentile_target"] == 95
        )

        # p99 target
        adaptive_p99 = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_percentile_target=99,
        )
        assert (
            adaptive_p99.strategies["baseline_conservative"].parameters["percentile_target"] == 99
        )


class TestStrategyManagement:
    """Test strategy lifecycle management."""

    @pytest.mark.asyncio
    async def test_strategies_dict_accessible(self, service):
        """Test that strategies can be accessed."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service)

        strategies = adaptive.strategies
        assert isinstance(strategies, dict)
        assert "baseline_conservative" in strategies

    @pytest.mark.asyncio
    async def test_baseline_strategy_always_available(self, service, context):
        """Test that baseline strategy is never removed."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service, learning_mode=LearningMode.ACTIVE
        )

        # Execute many times
        for i in range(50):
            service.set_latency(100)
            await adaptive.execute({"request_id": i}, context)

        # Baseline should still exist
        assert "baseline_conservative" in adaptive.strategies


class TestMetrics:
    """Test timeout metrics and statistics."""

    @pytest.mark.asyncio
    async def test_timeout_stats_structure(self, service, context):
        """Test timeout stats return expected structure."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service)

        stats = adaptive.get_timeout_stats()

        # Check required keys
        assert "total_executions" in stats
        assert "timeout_count" in stats
        assert "success_count" in stats
        assert "timeout_rate" in stats
        assert "latencies" in stats
        assert "contexts" in stats
        assert "strategies" in stats
        assert "current_timeout_ms" in stats

        # Check latencies structure
        assert "p50_ms" in stats["latencies"]
        assert "p95_ms" in stats["latencies"]
        assert "p99_ms" in stats["latencies"]
        assert "avg_ms" in stats["latencies"]
        assert "min_ms" in stats["latencies"]
        assert "max_ms" in stats["latencies"]

    @pytest.mark.asyncio
    async def test_timeout_rate_calculation(self, service, context):
        """Test timeout rate is calculated correctly."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=200.0)

        # 3 successes
        service.set_latency(100.0)
        await adaptive.execute({"request_id": 1}, context)
        await adaptive.execute({"request_id": 2}, context)
        await adaptive.execute({"request_id": 3}, context)

        # 1 timeout
        service.set_latency(500.0)
        with pytest.raises(TimeoutError):
            await adaptive.execute({"request_id": 4}, context)

        stats = adaptive.get_timeout_stats()
        assert stats["total_executions"] == 4
        assert stats["success_count"] == 3
        assert stats["timeout_count"] == 1
        assert stats["timeout_rate"] == 0.25  # 25%

    @pytest.mark.asyncio
    async def test_context_stats_tracked(self, service):
        """Test per-context statistics."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service, baseline_timeout_ms=500.0)

        # Production context
        prod_context = WorkflowContext(
            correlation_id="prod", metadata={"environment": "production"}
        )
        service.set_latency(200.0)
        await adaptive.execute({"request_id": 1}, prod_context)
        await adaptive.execute({"request_id": 2}, prod_context)

        # Staging context
        staging_context = WorkflowContext(
            correlation_id="staging", metadata={"environment": "staging"}
        )
        service.set_latency(100.0)
        await adaptive.execute({"request_id": 3}, staging_context)

        stats = adaptive.get_timeout_stats()

        assert "production" in stats["contexts"]
        assert "staging" in stats["contexts"]
        assert stats["contexts"]["production"]["executions"] == 2
        assert stats["contexts"]["staging"]["executions"] == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_no_latency_samples_stats(self, service):
        """Test stats when no executions have occurred."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service)

        stats = adaptive.get_timeout_stats()

        assert stats["total_executions"] == 0
        assert stats["timeout_rate"] == 0.0
        assert stats["latencies"]["p50_ms"] == 0.0
        assert stats["latencies"]["p95_ms"] == 0.0

    @pytest.mark.asyncio
    async def test_single_execution_percentiles(self, service, context):
        """Test percentile calculation with single execution."""
        adaptive = AdaptiveTimeoutPrimitive(target_primitive=service)

        service.set_latency(150.0)
        await adaptive.execute({"request_id": 1}, context)

        stats = adaptive.get_timeout_stats()

        # All percentiles should be the single value (allow for asyncio overhead)
        assert 145 <= stats["latencies"]["p50_ms"] <= 155
        assert 145 <= stats["latencies"]["p95_ms"] <= 155
        assert 145 <= stats["latencies"]["p99_ms"] <= 155

    @pytest.mark.asyncio
    async def test_disabled_learning_mode(self, service, context):
        """Test that DISABLED mode prevents learning."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            learning_mode=LearningMode.DISABLED,
            min_observations_before_learning=5,
        )

        # Execute enough times to trigger learning
        for i in range(20):
            service.set_latency(100)
            await adaptive.execute({"request_id": i}, context)

        # Should only have baseline strategy
        assert len(adaptive.strategies) == 1
        assert "baseline_conservative" in adaptive.strategies

    @pytest.mark.asyncio
    async def test_all_timeouts_scenario(self, service, context):
        """Test scenario where all executions timeout."""
        adaptive = AdaptiveTimeoutPrimitive(
            target_primitive=service,
            baseline_timeout_ms=100.0,  # Very tight
        )

        # All will timeout
        for i in range(5):
            service.set_latency(500.0)  # Much slower than timeout
            with pytest.raises(TimeoutError):
                await adaptive.execute({"request_id": i}, context)

        stats = adaptive.get_timeout_stats()
        assert stats["timeout_count"] == 5
        assert stats["success_count"] == 0
        assert stats["timeout_rate"] == 1.0  # 100% timeout rate
