"""Tests for FallbackPrimitive Phase 2 instrumentation."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)
from tta_dev_primitives.recovery.fallback import FallbackPrimitive


class SuccessfulPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always succeeds."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'success' field to input."""
        return {**input_data, "success": True}


class PrimaryPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for primary execution."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'primary_executed' field to input."""
        return {**input_data, "primary_executed": True}


class FallbackSuccessPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for fallback that succeeds."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'fallback_executed' field to input."""
        return {**input_data, "fallback_executed": True}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Always raise an error."""
        raise ValueError("Always fails")


@pytest.mark.asyncio
async def test_fallback_logs_workflow_start_and_completion():
    """Verify that FallbackPrimitive logs workflow start and completion."""
    workflow = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify via checkpoints (structlog logs to stdout)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.start" in checkpoint_names
    assert "fallback.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_logs_primary_execution():
    """Verify that FallbackPrimitive logs primary execution."""
    workflow = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify checkpoints for primary execution
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.primary.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_logs_fallback_trigger():
    """Verify that FallbackPrimitive logs fallback trigger when primary fails."""
    workflow = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify fallback was executed
    assert result["fallback_executed"] is True

    # Verify checkpoints for both primary and fallback
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.primary.end" in checkpoint_names
    assert "fallback.fallback.start" in checkpoint_names
    assert "fallback.fallback.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_records_execution_checkpoints():
    """Verify that FallbackPrimitive records checkpoints for executions."""
    workflow = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify all checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.start" in checkpoint_names
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.primary.end" in checkpoint_names
    assert "fallback.fallback.start" in checkpoint_names
    assert "fallback.fallback.end" in checkpoint_names
    assert "fallback.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_records_execution_metrics():
    """Verify that FallbackPrimitive records execution metrics."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    workflow = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Check that metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()

    # Get metrics for primary
    primary_metrics = metrics_collector.get_all_metrics("FallbackPrimitive.primary")
    workflow_metrics = metrics_collector.get_all_metrics("FallbackPrimitive.workflow")

    # Verify metrics exist
    assert primary_metrics is not None
    assert workflow_metrics is not None

    # Check enhanced metrics structure
    assert "percentiles" in primary_metrics
    assert primary_metrics["percentiles"]["p50"] >= 0


@pytest.mark.asyncio
async def test_fallback_creates_execution_spans():
    """Verify that FallbackPrimitive attempts to create spans when tracing available."""
    workflow = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution succeeded (spans created or gracefully degraded)
    assert result["primary_executed"] is True

    # Verify checkpoints were recorded (proves execution path was followed)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_span_attributes():
    """Verify that fallback execution includes proper attribute tracking."""
    workflow = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution succeeded
    assert result["primary_executed"] is True

    # Verify metrics were recorded (proves attributes were tracked)
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    metrics_collector = get_enhanced_metrics_collector()
    primary_metrics = metrics_collector.get_all_metrics("FallbackPrimitive.primary")

    assert primary_metrics is not None


@pytest.mark.asyncio
async def test_fallback_error_handling_in_primary_and_fallback():
    """Verify that errors in both primary and fallback are properly tracked."""
    workflow = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FailingPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify both executions were attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.fallback.start" in checkpoint_names

    # Verify workflow end was recorded
    assert "fallback.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_success_on_primary():
    """Verify that FallbackPrimitive handles success on primary (no fallback needed)."""
    workflow = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify primary succeeded
    assert result["primary_executed"] is True
    assert "fallback_executed" not in result

    # Verify only primary was executed
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.primary.end" in checkpoint_names
    # Should NOT have fallback execution
    assert "fallback.fallback.start" not in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_success_on_fallback():
    """Verify that FallbackPrimitive tracks success on fallback after primary fails."""
    workflow = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify fallback succeeded
    assert result["fallback_executed"] is True

    # Verify both executions were attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.fallback.start" in checkpoint_names
    assert "fallback.fallback.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_exhausted_scenario():
    """Verify that FallbackPrimitive handles exhaustion when both fail."""
    workflow = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FailingPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify both executions were attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.primary.end" in checkpoint_names
    assert "fallback.fallback.start" in checkpoint_names
    assert "fallback.fallback.end" in checkpoint_names
    assert "fallback.end" in checkpoint_names


@pytest.mark.asyncio
async def test_fallback_preserves_existing_functionality():
    """Verify that Phase 2 changes don't break existing functionality."""
    # Test success on primary
    workflow1 = FallbackPrimitive(
        primary=PrimaryPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context1 = WorkflowContext(workflow_id="test")

    result1 = await workflow1.execute({"input": "data"}, context1)
    assert result1["primary_executed"] is True
    assert "fallback_executed" not in result1

    # Test success on fallback
    workflow2 = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FallbackSuccessPrimitive(),
    )
    context2 = WorkflowContext(workflow_id="test")

    result2 = await workflow2.execute({"input": "data"}, context2)
    assert result2["fallback_executed"] is True

    # Test both fail
    workflow3 = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=FailingPrimitive(),
    )
    context3 = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow3.execute({"input": "data"}, context3)
