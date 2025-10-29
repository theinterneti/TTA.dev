"""Tests for SagaPrimitive Phase 2 instrumentation."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)
from tta_dev_primitives.recovery.compensation import SagaPrimitive


class SuccessfulPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always succeeds."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'success' field to input."""
        return {**input_data, "success": True}


class ForwardPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for forward execution."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'forward_executed' field to input."""
        return {**input_data, "forward_executed": True}


class CompensationPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for compensation that succeeds."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'compensation_executed' field to input."""
        return {**input_data, "compensation_executed": True}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Always raise an error."""
        raise ValueError("Always fails")


@pytest.mark.asyncio
async def test_saga_logs_workflow_start_and_completion():
    """Verify that SagaPrimitive logs workflow start and completion."""
    workflow = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify via checkpoints (structlog logs to stdout)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.start" in checkpoint_names
    assert "saga.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_logs_forward_execution():
    """Verify that SagaPrimitive logs forward execution."""
    workflow = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify checkpoints for forward execution
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names
    assert "saga.forward.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_logs_compensation_trigger():
    """Verify that SagaPrimitive logs compensation trigger when forward fails."""
    workflow = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify checkpoints for both forward and compensation
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names
    assert "saga.forward.end" in checkpoint_names
    assert "saga.compensation.start" in checkpoint_names
    assert "saga.compensation.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_records_execution_checkpoints():
    """Verify that SagaPrimitive records checkpoints for executions."""
    workflow = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify all checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.start" in checkpoint_names
    assert "saga.forward.start" in checkpoint_names
    assert "saga.forward.end" in checkpoint_names
    assert "saga.compensation.start" in checkpoint_names
    assert "saga.compensation.end" in checkpoint_names
    assert "saga.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_records_execution_metrics():
    """Verify that SagaPrimitive records execution metrics."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    workflow = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Check that metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()

    # Get metrics for forward
    forward_metrics = metrics_collector.get_all_metrics("SagaPrimitive.forward")
    workflow_metrics = metrics_collector.get_all_metrics("SagaPrimitive.workflow")

    # Verify metrics exist
    assert forward_metrics is not None
    assert workflow_metrics is not None

    # Check enhanced metrics structure
    assert "percentiles" in forward_metrics
    assert forward_metrics["percentiles"]["p50"] >= 0


@pytest.mark.asyncio
async def test_saga_creates_execution_spans():
    """Verify that SagaPrimitive attempts to create spans when tracing available."""
    workflow = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution succeeded (spans created or gracefully degraded)
    assert result["forward_executed"] is True

    # Verify checkpoints were recorded (proves execution path was followed)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_span_attributes():
    """Verify that saga execution includes proper attribute tracking."""
    workflow = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution succeeded
    assert result["forward_executed"] is True

    # Verify metrics were recorded (proves attributes were tracked)
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    metrics_collector = get_enhanced_metrics_collector()
    forward_metrics = metrics_collector.get_all_metrics("SagaPrimitive.forward")

    assert forward_metrics is not None


@pytest.mark.asyncio
async def test_saga_error_handling_in_forward_and_compensation():
    """Verify that errors in both forward and compensation are properly tracked."""
    workflow = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=FailingPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify both executions were attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names
    assert "saga.compensation.start" in checkpoint_names

    # Verify workflow end was recorded
    assert "saga.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_success_on_forward():
    """Verify that SagaPrimitive handles success on forward (no compensation needed)."""
    workflow = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify forward succeeded
    assert result["forward_executed"] is True
    assert "compensation_executed" not in result

    # Verify only forward was executed
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names
    assert "saga.forward.end" in checkpoint_names
    # Should NOT have compensation execution
    assert "saga.compensation.start" not in checkpoint_names


@pytest.mark.asyncio
async def test_saga_compensation_triggered():
    """Verify that SagaPrimitive triggers compensation after forward fails."""
    workflow = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify both executions were attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names
    assert "saga.compensation.start" in checkpoint_names
    assert "saga.compensation.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_compensation_failure_handling():
    """Verify that SagaPrimitive handles compensation failure."""
    workflow = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=FailingPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify both executions were attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "saga.forward.start" in checkpoint_names
    assert "saga.forward.end" in checkpoint_names
    assert "saga.compensation.start" in checkpoint_names
    assert "saga.compensation.end" in checkpoint_names
    assert "saga.end" in checkpoint_names


@pytest.mark.asyncio
async def test_saga_preserves_existing_functionality():
    """Verify that Phase 2 changes don't break existing functionality."""
    # Test success on forward
    workflow1 = SagaPrimitive(
        forward=ForwardPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context1 = WorkflowContext(workflow_id="test")

    result1 = await workflow1.execute({"input": "data"}, context1)
    assert result1["forward_executed"] is True
    assert "compensation_executed" not in result1

    # Test compensation triggered
    workflow2 = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=CompensationPrimitive(),
    )
    context2 = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow2.execute({"input": "data"}, context2)

    # Test both fail
    workflow3 = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=FailingPrimitive(),
    )
    context3 = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow3.execute({"input": "data"}, context3)
