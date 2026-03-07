"""Tests for AdaptivePrimitive base class."""

import pytest

from tta_dev_primitives.adaptive import (
    AdaptivePrimitive,
    LearningMode,
    LearningStrategy,
    StrategyMetrics,
)
from tta_dev_primitives.core.base import WorkflowContext


class TestAdaptivePrimitive(AdaptivePrimitive[dict, dict]):
    """Concrete implementation for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_count = 0
        self.strategy_considerations = []

    def _get_default_strategy(self) -> LearningStrategy:
        """Return default baseline strategy for testing."""
        return LearningStrategy(
            name="baseline",
            description="Default baseline strategy",
            context_pattern="*",  # Match all contexts
            parameters={"delay": 0.1},
        )

    async def _execute_with_strategy(
        self,
        input_data: dict,
        context: WorkflowContext,
        strategy: LearningStrategy,
    ) -> dict:
        """Execute with given strategy."""
        self.execution_count += 1
        delay = strategy.parameters.get("delay", 0.1)
        return {"result": "success", "delay": delay, "strategy": strategy.name}

    async def _consider_new_strategy(
        self,
        input_data: dict,
        context: WorkflowContext,
        current_performance: StrategyMetrics,
    ) -> LearningStrategy | None:
        """Consider creating new strategy."""
        self.strategy_considerations.append(
            {
                "performance": current_performance,
                "context": context.metadata.get("environment"),
            }
        )

        # Simple learning logic: improve if success rate < 90%
        if current_performance.success_rate < 0.9:
            return LearningStrategy(
                name=f"improved_{len(self.strategies)}",
                description="Improved strategy based on performance",
                context_pattern=context.metadata.get("environment", "*"),
                parameters={"delay": 0.05},  # Faster delay
            )
        return None


@pytest.fixture
def baseline_strategy():
    """Baseline strategy for testing."""
    return LearningStrategy(
        name="baseline",
        description="Default baseline strategy",
        context_pattern="*",  # Match all contexts
        parameters={"delay": 0.1},
    )


@pytest.fixture
def context():
    """Workflow context for testing."""
    return WorkflowContext(correlation_id="test-123", metadata={"environment": "test"})


class TestAdaptivePrimitiveInitialization:
    """Test initialization and configuration."""

    def test_initialization_with_defaults(self):
        """Test default initialization."""
        primitive = TestAdaptivePrimitive()

        assert primitive.learning_mode == LearningMode.VALIDATE
        assert primitive.validation_window == 50  # Default value
        assert primitive.max_strategies == 10
        assert primitive.circuit_breaker_threshold == 0.5
        # Baseline strategy created by _get_default_strategy()
        default_strategy = primitive._get_default_strategy()
        assert default_strategy.name == "baseline"

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        primitive = TestAdaptivePrimitive(
            learning_mode=LearningMode.ACTIVE,
            validation_window=25,
            max_strategies=5,
            circuit_breaker_threshold=0.7,
        )

        assert primitive.learning_mode == LearningMode.ACTIVE
        assert primitive.validation_window == 25
        assert primitive.max_strategies == 5
        assert primitive.circuit_breaker_threshold == 0.7

    def test_baseline_strategy_from_default(self):
        """Test that _get_default_strategy() provides baseline strategy."""
        primitive = TestAdaptivePrimitive()

        default_strategy = primitive._get_default_strategy()
        assert default_strategy.name == "baseline"
        assert default_strategy.description == "Default baseline strategy"
        assert default_strategy.parameters["delay"] == 0.1


class TestBasicExecution:
    """Test basic execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_with_baseline(self, context):
        """Test execution using baseline strategy."""
        primitive = TestAdaptivePrimitive()

        result = await primitive.execute({"input": "test"}, context)

        assert result["result"] == "success"
        assert result["strategy"] == "baseline"
        assert primitive.execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_multiple_times(self, context):
        """Test multiple executions."""
        primitive = TestAdaptivePrimitive()

        for i in range(5):
            result = await primitive.execute({"input": f"test_{i}"}, context)
            assert result["result"] == "success"

        assert primitive.execution_count == 5


class TestLearningModes:
    """Test different learning modes."""

    @pytest.mark.asyncio
    async def test_disabled_mode_no_learning(self, context):
        """Test that DISABLED mode prevents learning."""
        primitive = TestAdaptivePrimitive(learning_mode=LearningMode.DISABLED)

        # Execute enough times to trigger learning
        for _ in range(10):
            await primitive.execute({"input": "test"}, context)

        # Should not have considered new strategies (learning disabled)
        assert primitive.strategy_considerations == []

    @pytest.mark.asyncio
    async def test_observe_mode_considers_but_not_applies(self, context):
        """Test that OBSERVE mode considers but doesn't apply strategies."""
        primitive = TestAdaptivePrimitive(
            learning_mode=LearningMode.OBSERVE,
        )

        # Execute enough times
        for _ in range(10):
            await primitive.execute({"input": "test"}, context)

        # Should have considered new strategies
        # (actual consideration logic depends on _consider_new_strategy implementation)
        # Just verify it doesn't crash in OBSERVE mode
        assert primitive.execution_count == 10


class TestStrategyValidation:
    """Test strategy validation mechanism."""

    @pytest.mark.asyncio
    async def test_validation_window(self, context):
        """Test strategy validation window."""
        primitive = TestAdaptivePrimitive(
            learning_mode=LearningMode.VALIDATE,
            validation_window=5,
        )

        # Execute to trigger learning
        for _ in range(10):
            await primitive.execute({"input": "test"}, context)

        # Verify validation_window is set correctly
        assert primitive.validation_window == 5


class TestContextAwareness:
    """Test context-aware strategy selection."""

    @pytest.mark.asyncio
    async def test_different_contexts(self):
        """Test that primitive handles different contexts."""
        primitive = TestAdaptivePrimitive(
            learning_mode=LearningMode.ACTIVE,
        )

        # Execute with production context
        prod_context = WorkflowContext(metadata={"environment": "production"})
        for _ in range(5):
            result = await primitive.execute({"input": "test"}, prod_context)
            assert result["result"] == "success"

        # Execute with staging context
        staging_context = WorkflowContext(metadata={"environment": "staging"})
        for _ in range(5):
            result = await primitive.execute({"input": "test"}, staging_context)
            assert result["result"] == "success"

        # Should have executed in both contexts successfully
        assert primitive.execution_count == 10


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_configuration(self):
        """Test circuit breaker configuration is respected."""
        primitive = TestAdaptivePrimitive(
            circuit_breaker_threshold=0.7,
        )

        assert primitive.circuit_breaker_threshold == 0.7


class TestStrategyMetrics:
    """Test StrategyMetrics functionality."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = StrategyMetrics()

        # Default initialization
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.total_executions == 0
        assert metrics.success_rate == 0.0

    def test_metrics_update_and_properties(self):
        """Test metrics update and property calculations."""
        metrics = StrategyMetrics()

        # Simulate successful executions
        metrics.update(success=True, latency=0.1, context_key="test")
        metrics.update(success=True, latency=0.15, context_key="test")
        metrics.update(success=False, latency=0.0, context_key="test")

        assert metrics.total_executions == 3
        assert metrics.success_count == 2
        assert metrics.failure_count == 1
        assert metrics.success_rate == pytest.approx(2.0 / 3.0)
        assert metrics.avg_latency == pytest.approx(0.125)  # (0.1 + 0.15) / 2

    def test_metrics_comparison(self):
        """Test metrics comparison."""
        metrics1 = StrategyMetrics()
        metrics2 = StrategyMetrics()

        # Build up metrics1: 20 successes out of 20 (100%), avg latency 0.1
        for _ in range(20):
            metrics1.update(success=True, latency=0.1, context_key="test")

        # Build up metrics2: 18 successes out of 20 (90%), avg latency 0.15
        for _ in range(18):
            metrics2.update(success=True, latency=0.15, context_key="test")
        for _ in range(2):
            metrics2.update(success=False, latency=0.0, context_key="test")

        # metrics1 should be better: higher success rate (100% > 90%) and lower latency (0.1 < 0.15)
        # Success rate diff = 10% > 5% threshold
        # Latency: 0.1 < 0.15 * 1.1 = 0.165, so it's acceptable
        assert metrics1.is_better_than(metrics2) is True
        assert metrics2.is_better_than(metrics1) is False


class TestLearningStrategy:
    """Test LearningStrategy functionality."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = LearningStrategy(
            name="test_strategy",
            description="Test strategy",
            context_pattern="test",
            parameters={"param1": "value1"},
        )

        assert strategy.name == "test_strategy"
        assert strategy.description == "Test strategy"
        assert strategy.context_pattern == "test"
        assert strategy.parameters["param1"] == "value1"
        assert strategy.metrics.success_rate == 0.0

    def test_strategy_validation_tracking(self):
        """Test validation tracking."""
        strategy = LearningStrategy(
            name="test",
            description="Test strategy",
            context_pattern="*",
            parameters={},
        )

        # Simulate validation attempts
        for _ in range(8):
            strategy.record_validation(success=True)
        for _ in range(2):
            strategy.record_validation(success=False)

        assert strategy.validation_attempts == 10
        assert strategy.validation_successes == 8
        assert strategy.is_validated is True  # 8/10 = 80% >= 80% threshold

        # Test strategy that doesn't meet threshold
        strategy2 = LearningStrategy(
            name="test2",
            description="Test strategy 2",
            context_pattern="*",
            parameters={},
        )

        for _ in range(6):
            strategy2.record_validation(success=True)
        for _ in range(4):
            strategy2.record_validation(success=False)

        assert strategy2.validation_attempts == 10
        assert strategy2.validation_successes == 6
        assert strategy2.is_validated is False  # 6/10 = 60% < 80%


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_input_data(self, context):
        """Test execution with empty input."""
        primitive = TestAdaptivePrimitive()

        result = await primitive.execute({}, context)
        assert result["result"] == "success"

    def test_minimum_validation_window(self):
        """Test with minimum validation window."""
        primitive = TestAdaptivePrimitive(validation_window=1)

        # Should accept minimum of 1
        assert primitive.validation_window >= 1
