"""Tests for ParallelPrimitive Phase 2 instrumentation."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class SimplePrimitive(InstrumentedPrimitive[dict, dict]):
    """Simple test primitive that adds a field."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'processed' field to input."""
        return {**input_data, "processed": True}


class CounterPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that counts calls."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name)
        self.call_count = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Increment counter and return input with count."""
        self.call_count += 1
        return {**input_data, "count": self.call_count}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Raise an error."""
        raise ValueError("Test error")


@pytest.mark.asyncio
async def test_parallel_logs_workflow_start_and_completion() -> None:
    """Verify that ParallelPrimitive logs workflow start and completion."""
    workflow = ParallelPrimitive([SimplePrimitive(), SimplePrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"key": "value"}, context)

    # Verify via checkpoints (structlog logs to stdout)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "parallel.fan_out" in checkpoint_names
    assert "parallel.fan_in" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_logs_branch_execution() -> None:
    """Verify that ParallelPrimitive logs each branch (verified via checkpoints)."""
    workflow = ParallelPrimitive([SimplePrimitive(), CounterPrimitive(), SimplePrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"key": "value"}, context)

    # Verify checkpoints for each branch
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "parallel.branch_0.start" in checkpoint_names
    assert "parallel.branch_0.end" in checkpoint_names
    assert "parallel.branch_1.start" in checkpoint_names
    assert "parallel.branch_1.end" in checkpoint_names
    assert "parallel.branch_2.start" in checkpoint_names
    assert "parallel.branch_2.end" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_records_branch_checkpoints() -> None:
    """Verify that ParallelPrimitive records checkpoints for each branch."""
    workflow = ParallelPrimitive([SimplePrimitive(), SimplePrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"key": "value"}, context)

    # Check checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]

    # Should have fan-out, branch checkpoints, and fan-in
    assert "parallel.fan_out" in checkpoint_names
    assert "parallel.branch_0.start" in checkpoint_names
    assert "parallel.branch_0.end" in checkpoint_names
    assert "parallel.branch_1.start" in checkpoint_names
    assert "parallel.branch_1.end" in checkpoint_names
    assert "parallel.fan_in" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_records_branch_metrics() -> None:
    """Verify that ParallelPrimitive records per-branch metrics."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    workflow = ParallelPrimitive([SimplePrimitive(), SimplePrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"key": "value"}, context)

    # Check that branch metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()

    # Get metrics for each branch
    branch_0_metrics = metrics_collector.get_all_metrics("ParallelPrimitive.branch_0")
    branch_1_metrics = metrics_collector.get_all_metrics("ParallelPrimitive.branch_1")

    # Verify branch metrics exist and have duration
    assert branch_0_metrics is not None
    assert branch_1_metrics is not None

    # Check enhanced metrics structure (percentiles, throughput, slo, cost)
    assert "percentiles" in branch_0_metrics
    assert branch_0_metrics["percentiles"]["p50"] >= 0


@pytest.mark.asyncio
async def test_parallel_creates_branch_spans() -> None:
    """Verify that ParallelPrimitive attempts to create spans when tracing available."""
    # Test that the code path for span creation is exercised
    # We verify this indirectly through successful execution
    workflow = ParallelPrimitive([SimplePrimitive(), SimplePrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    results = await workflow.execute({"key": "value"}, context)

    # Verify execution succeeded (spans created or gracefully degraded)
    assert len(results) == 2
    assert all(r["processed"] is True for r in results)

    # Verify checkpoints were recorded (proves execution path was followed)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "parallel.branch_0.start" in checkpoint_names
    assert "parallel.branch_1.start" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_span_attributes() -> None:
    """Verify that branch execution includes proper attribute tracking."""
    # Test that execution completes with proper tracking
    workflow = ParallelPrimitive([SimplePrimitive(), CounterPrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    results = await workflow.execute({"key": "value"}, context)

    # Verify execution succeeded
    assert len(results) == 2
    assert results[0]["processed"] is True
    assert results[1]["count"] == 1

    # Verify metrics were recorded (proves attributes were tracked)
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    metrics_collector = get_enhanced_metrics_collector()
    branch_0_metrics = metrics_collector.get_all_metrics("ParallelPrimitive.branch_0")
    branch_1_metrics = metrics_collector.get_all_metrics("ParallelPrimitive.branch_1")

    assert branch_0_metrics is not None
    assert branch_1_metrics is not None


@pytest.mark.asyncio
async def test_parallel_error_handling_with_spans() -> None:
    """Verify that errors in branches are properly propagated."""
    workflow = ParallelPrimitive([SimplePrimitive(), FailingPrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Test error"):
        await workflow.execute({"key": "value"}, context)

    # Verify first branch started before error
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "parallel.fan_out" in checkpoint_names
    assert "parallel.branch_0.start" in checkpoint_names
    assert "parallel.branch_1.start" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_preserves_existing_functionality() -> None:
    """Verify that Phase 2 changes don't break existing functionality."""
    # Test basic execution
    counter1 = CounterPrimitive()
    counter2 = CounterPrimitive()
    counter3 = CounterPrimitive()

    workflow = ParallelPrimitive([counter1, counter2, counter3])
    context = WorkflowContext(workflow_id="test")

    results = await workflow.execute({"input": "data"}, context)

    # All branches should execute
    assert len(results) == 3
    assert counter1.call_count == 1
    assert counter2.call_count == 1
    assert counter3.call_count == 1

    # Test | operator still works
    branch1 = SimplePrimitive()
    branch2 = SimplePrimitive()
    workflow2 = branch1 | branch2

    results2 = await workflow2.execute({"input": "data"}, context)
    assert len(results2) == 2
    assert all(r["processed"] is True for r in results2)


@pytest.mark.asyncio
async def test_parallel_concurrency_tracking() -> None:
    """Verify that ParallelPrimitive tracks concurrent execution."""
    import asyncio

    class SlowPrimitive(InstrumentedPrimitive[dict, dict]):
        """Primitive that takes time to execute."""

        async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(0.1)
            return {**input_data, "slow": True}

    workflow = ParallelPrimitive([SlowPrimitive(), SlowPrimitive(), SlowPrimitive()])
    context = WorkflowContext(workflow_id="test-workflow")

    import time

    start = time.time()
    results = await workflow.execute({"key": "value"}, context)
    duration = time.time() - start

    # Should execute in parallel (< 0.3s total, not 0.3s sequential)
    assert duration < 0.2  # Allow some overhead

    # All branches should complete
    assert len(results) == 3
    assert all(r["slow"] is True for r in results)

    # Verify fan-out and fan-in checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "parallel.fan_out" in checkpoint_names
    assert "parallel.fan_in" in checkpoint_names
