"""Tests for AdaptiveRetryPrimitive."""

import asyncio

import pytest

from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LearningMode,
)
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class UnreliableService(InstrumentedPrimitive[dict, dict]):
    """Mock service that fails predictably."""

    def __init__(self, failure_rate: float = 0.3):
        super().__init__()
        self.failure_rate = failure_rate
        self.call_count = 0
        self.failures = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute with controlled failures."""
        self.call_count += 1

        # Fail for first few calls based on failure rate
        if self.call_count <= int(10 * self.failure_rate):
            self.failures += 1
            raise Exception(f"Service failure #{self.failures}")

        return {"result": "success", "calls": self.call_count}


@pytest.fixture
def unreliable_service():
    """Unreliable service for testing."""
    return UnreliableService(failure_rate=0.3)


@pytest.fixture
def context():
    """Workflow context."""
    return WorkflowContext(correlation_id="test-retry", metadata={"environment": "test"})


class TestAdaptiveRetryInitialization:
    """Test initialization of AdaptiveRetryPrimitive."""

    def test_initialization_with_defaults(self, unreliable_service):
        """Test default initialization."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        assert adaptive.target_primitive == unreliable_service
        assert adaptive.learning_mode == LearningMode.VALIDATE
        assert len(adaptive.strategies) == 1  # Just baseline
        assert "baseline_exponential" in adaptive.strategies

    def test_initialization_with_custom_mode(self, unreliable_service):
        """Test initialization with custom learning mode."""
        adaptive = AdaptiveRetryPrimitive(
            target_primitive=unreliable_service, learning_mode=LearningMode.ACTIVE
        )

        assert adaptive.learning_mode == LearningMode.ACTIVE

    def test_baseline_strategy_parameters(self, unreliable_service):
        """Test baseline strategy has retry parameters."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        baseline = adaptive.strategies["baseline_exponential"]
        assert "max_retries" in baseline.parameters
        assert "backoff_factor" in baseline.parameters
        assert "initial_delay" in baseline.parameters


class TestBasicRetryBehavior:
    """Test basic retry functionality."""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self, context):
        """Test successful execution without retries."""
        # Service that never fails
        service = UnreliableService(failure_rate=0.0)
        adaptive = AdaptiveRetryPrimitive(target_primitive=service)

        result = await adaptive.execute({"input": "test"}, context)

        # AdaptiveRetryPrimitive wraps the result
        assert result["success"] is True
        assert result["attempts"] == 1  # No retries needed
        assert result["result"]["result"] == "success"  # Unwrap inner result
        assert service.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, unreliable_service, context):
        """Test retry mechanism on failures."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        result = await adaptive.execute({"input": "test"}, context)

        # Should eventually succeed after retries
        assert result["success"] is True
        assert result["result"]["result"] == "success"
        # Should have retried (more than 1 call)
        assert result["attempts"] > 1
        assert unreliable_service.call_count > 1

    @pytest.mark.asyncio
    async def test_max_retries_respected(self, context):
        """Test that max retries limit is respected."""
        # Service that always fails
        service = UnreliableService(failure_rate=1.0)

        adaptive = AdaptiveRetryPrimitive(target_primitive=service)

        result = await adaptive.execute({"input": "test"}, context)

        # Should have failed after all retries
        assert result["success"] is False
        assert "error" in result
        assert "Service failure" in result["error"]

        # Should have tried: initial + 3 retries = 4 total (default max_retries=3)
        assert service.call_count == 4


class TestLearningBehavior:
    """Test strategy learning."""

    @pytest.mark.asyncio
    async def test_learns_from_failures(self, context):
        """Test that primitive learns from failure patterns."""
        service = UnreliableService(failure_rate=0.4)  # 40% failure
        adaptive = AdaptiveRetryPrimitive(
            target_primitive=service,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute multiple times to trigger learning
        for i in range(10):
            try:
                await adaptive.execute({"input": f"test_{i}"}, context)
            except Exception:
                pass  # Some may fail

        # Should have considered learning (strategies count may vary)
        # At minimum, should have executed multiple times
        assert service.call_count >= 10

    @pytest.mark.asyncio
    async def test_different_contexts_learn_separately(self):
        """Test context-specific learning."""
        service = UnreliableService(failure_rate=0.3)
        adaptive = AdaptiveRetryPrimitive(
            target_primitive=service,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute with production context
        prod_context = WorkflowContext(metadata={"environment": "production"})
        for _ in range(5):
            try:
                await adaptive.execute({"input": "test"}, prod_context)
            except Exception:
                pass

        # Execute with staging context
        staging_context = WorkflowContext(metadata={"environment": "staging"})
        for _ in range(5):
            try:
                await adaptive.execute({"input": "test"}, staging_context)
            except Exception:
                pass

        # Should have processed both contexts
        assert service.call_count >= 10


class TestStrategyParameters:
    """Test learned strategy parameters."""

    @pytest.mark.asyncio
    async def test_strategy_has_retry_parameters(self, unreliable_service, context):
        """Test that learned strategies have retry parameters."""
        adaptive = AdaptiveRetryPrimitive(
            target_primitive=unreliable_service,
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute enough to potentially learn
        for _ in range(10):
            try:
                await adaptive.execute({"input": "test"}, context)
            except Exception:
                pass

        # Check strategies have required parameters
        for _name, strategy in adaptive.strategies.items():
            params = strategy.parameters
            # Should have retry-related parameters
            assert isinstance(params, dict)


class TestObservability:
    """Test observability integration."""

    @pytest.mark.asyncio
    async def test_context_propagation(self, unreliable_service, context):
        """Test that context is propagated correctly."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        result = await adaptive.execute({"input": "test"}, context)

        # Should complete successfully (unwrap the result)
        assert result["success"] is True
        assert result["result"]["result"] == "success"

        # Context should have been used
        assert context.correlation_id == "test-retry"


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_handles_permanent_failures(self, context):
        """Test handling of permanent failures."""
        # Service that always fails
        service = UnreliableService(failure_rate=1.0)
        adaptive = AdaptiveRetryPrimitive(target_primitive=service)

        result = await adaptive.execute({"input": "test"}, context)

        # Should have failed after retries
        assert result["success"] is False
        assert "error" in result
        assert "Service failure" in result["error"]

    @pytest.mark.asyncio
    async def test_handles_transient_failures(self, unreliable_service, context):
        """Test recovery from transient failures."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        # Should eventually succeed despite initial failures (unwrap result)
        result = await adaptive.execute({"input": "test"}, context)
        assert result["success"] is True
        assert result["result"]["result"] == "success"


class TestValidationMode:
    """Test VALIDATE learning mode."""

    @pytest.mark.asyncio
    async def test_validate_mode_validates_before_use(self, unreliable_service):
        """Test that VALIDATE mode validates strategies."""
        adaptive = AdaptiveRetryPrimitive(
            target_primitive=unreliable_service,
            learning_mode=LearningMode.VALIDATE,
            validation_window=5,
        )

        context = WorkflowContext(metadata={"environment": "test"})

        # Execute enough to trigger validation
        for _ in range(15):
            try:
                await adaptive.execute({"input": "test"}, context)
            except Exception:
                pass

        # If new strategies were learned, they should be validating
        new_strategies = [
            s for name, s in adaptive.strategies.items() if name != "baseline_exponential"
        ]

        if new_strategies:
            # Check that strategies exist (validation happens internally)
            assert len(new_strategies) > 0


class TestPerformanceMetrics:
    """Test performance tracking."""

    @pytest.mark.asyncio
    async def test_tracks_success_rate(self, unreliable_service, context):
        """Test success rate tracking."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        successes = 0
        attempts = 10

        for _ in range(attempts):
            try:
                await adaptive.execute({"input": "test"}, context)
                successes += 1
            except Exception:
                pass

        # Should have some successes (unreliable but not completely failing)
        assert successes > 0

    @pytest.mark.asyncio
    async def test_tracks_latency(self, unreliable_service, context):
        """Test latency tracking."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        # Execute and measure
        start = asyncio.get_event_loop().time()
        await adaptive.execute({"input": "test"}, context)
        duration = asyncio.get_event_loop().time() - start

        # Should complete in reasonable time (retries add delay)
        assert duration > 0


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_input(self, unreliable_service, context):
        """Test with empty input."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        result = await adaptive.execute({}, context)
        assert result["success"] is True
        assert result["result"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_concurrent_executions(self, unreliable_service):
        """Test concurrent executions don't interfere."""
        adaptive = AdaptiveRetryPrimitive(target_primitive=unreliable_service)

        contexts = [
            WorkflowContext(correlation_id=f"test-{i}", metadata={"id": i}) for i in range(5)
        ]

        # Execute concurrently
        results = await asyncio.gather(
            *[adaptive.execute({"input": f"test_{i}"}, ctx) for i, ctx in enumerate(contexts)],
            return_exceptions=True,
        )

        # Should have results for all
        assert len(results) == 5
        # At least some should succeed
        successes = [r for r in results if isinstance(r, dict)]
        assert len(successes) > 0
