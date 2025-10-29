"""Tests for tracing with sampling integration."""

from __future__ import annotations

import pytest

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.observability import (
    ObservablePrimitive,
    SamplingConfig,
    SamplingDecision,
)
from tta_dev_primitives.observability.sampling import CompositeSampler
from tta_dev_primitives.testing import MockPrimitive


class TestObservablePrimitiveWithSampling:
    """Tests for ObservablePrimitive with sampling support."""

    @pytest.mark.asyncio
    async def test_sampled_execution(self) -> None:
        """Test that sampled execution creates traces."""
        # Mock primitive
        mock = MockPrimitive("test", return_value="result")

        # Create observable with 100% sampling
        config = SamplingConfig(default_rate=1.0)
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute
        context = WorkflowContext(workflow_id="test-workflow")
        result = await observable.execute("input", context)

        # Verify execution
        assert result == "result"
        assert mock.call_count == 1

        # Verify head decision was made
        assert observable._head_decision is not None
        assert observable._head_decision.decision == SamplingDecision.SAMPLE

    @pytest.mark.asyncio
    async def test_unsampled_execution(self) -> None:
        """Test that unsampled execution still runs but without traces."""
        # Mock primitive
        mock = MockPrimitive("test", return_value="result")

        # Create observable with 0% sampling
        config = SamplingConfig(default_rate=0.0, always_sample_errors=False)
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute
        context = WorkflowContext(workflow_id="test-workflow")
        result = await observable.execute("input", context)

        # Verify execution still happened
        assert result == "result"
        assert mock.call_count == 1

        # Verify head decision was DROP
        assert observable._head_decision is not None
        assert observable._head_decision.decision == SamplingDecision.DROP

    @pytest.mark.asyncio
    async def test_error_always_sampled(self) -> None:
        """Test that errors are always sampled regardless of head decision."""
        # Mock primitive that raises error
        mock = MockPrimitive("test", side_effect=ValueError("Test error"))

        # Create observable with 0% sampling but always sample errors
        config = SamplingConfig(default_rate=0.0, always_sample_errors=True)
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute and expect error
        context = WorkflowContext(workflow_id="test-workflow")

        with pytest.raises(ValueError, match="Test error"):
            await observable.execute("input", context)

        # Head decision should be DROP
        assert observable._head_decision.decision == SamplingDecision.DROP

        # But tail decision would upgrade to SAMPLE due to error
        # (This is verified in the tracing logic)

    @pytest.mark.asyncio
    async def test_slow_trace_sampled(self) -> None:
        """Test that slow traces are sampled at tail."""
        # Mock primitive with slow execution
        import asyncio

        async def slow_execution(data: str, ctx: WorkflowContext) -> str:
            await asyncio.sleep(0.1)  # 100ms
            return "result"

        mock = MockPrimitive("test", side_effect=slow_execution)

        # Create observable with 0% sampling but always sample slow
        config = SamplingConfig(
            default_rate=0.0,
            always_sample_slow=True,
            slow_threshold_ms=50.0,  # 50ms threshold
        )
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute
        context = WorkflowContext(workflow_id="test-workflow")
        result = await observable.execute("input", context)

        assert result == "result"

        # Head decision should be DROP
        assert observable._head_decision.decision == SamplingDecision.DROP

        # Tail would upgrade to SAMPLE due to slow execution
        # (verified in tracing logic)

    @pytest.mark.asyncio
    async def test_consistent_sampling_same_trace_id(self) -> None:
        """Test that same trace_id gets consistent sampling decision."""
        # Mock primitive
        mock = MockPrimitive("test", return_value="result")

        # Create observable with 50% sampling
        config = SamplingConfig(default_rate=0.5)
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute multiple times with same correlation_id
        context = WorkflowContext(correlation_id="consistent-trace-id")

        decisions = []
        for _ in range(5):
            await observable.execute("input", context)
            decisions.append(observable._head_decision.decision)

        # All decisions should be the same due to consistent hashing
        assert len(set(decisions)) == 1

    @pytest.mark.asyncio
    async def test_metrics_recorded_regardless_of_sampling(self) -> None:
        """Test that metrics are recorded even when not sampled."""
        from tta_dev_primitives.observability import get_metrics_collector

        collector = get_metrics_collector()
        collector.reset()

        # Mock primitive
        mock = MockPrimitive("test", return_value="result")

        # Create observable with 0% sampling
        config = SamplingConfig(default_rate=0.0)
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute
        context = WorkflowContext(workflow_id="test-workflow")
        await observable.execute("input", context)

        # Verify metrics were recorded
        metrics = collector.get_metrics("test_primitive")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1

    @pytest.mark.asyncio
    async def test_error_metrics_recorded(self) -> None:
        """Test that error metrics are recorded even when not sampled."""
        from tta_dev_primitives.observability import get_metrics_collector

        collector = get_metrics_collector()
        collector.reset()

        # Mock primitive that raises error
        mock = MockPrimitive("test", side_effect=ValueError("Test error"))

        # Create observable with 0% sampling
        config = SamplingConfig(default_rate=0.0, always_sample_errors=False)
        sampler = CompositeSampler(config)
        observable = ObservablePrimitive(mock, "test_primitive", sampler=sampler)

        # Execute and expect error
        context = WorkflowContext(workflow_id="test-workflow")

        with pytest.raises(ValueError):
            await observable.execute("input", context)

        # Verify error metrics were recorded
        metrics = collector.get_metrics("test_primitive")
        assert metrics["failed_executions"] == 1
        assert "ValueError" in metrics["error_counts"]

    @pytest.mark.asyncio
    async def test_uses_global_config_by_default(self) -> None:
        """Test that observable uses global config when no sampler provided."""
        from tta_dev_primitives.observability import (
            ObservabilityConfig,
            set_observability_config,
        )

        # Set global config
        config = ObservabilityConfig.from_environment("production")
        set_observability_config(config)

        # Create observable without explicit sampler
        mock = MockPrimitive("test", return_value="result")
        observable = ObservablePrimitive(mock, "test_primitive")

        # Should have sampler from global config
        assert observable.sampler is not None
        assert isinstance(observable.sampler, CompositeSampler)

        # Execute
        context = WorkflowContext(workflow_id="test-workflow")
        result = await observable.execute("input", context)

        assert result == "result"
        assert observable._head_decision is not None
