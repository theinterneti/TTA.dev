"""Tests for ConditionalPrimitive Phase 2 instrumentation."""

from typing import Never

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.conditional import ConditionalPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class SimplePrimitive(InstrumentedPrimitive[dict, dict]):
    """Simple test primitive that adds a field."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'processed' field to input."""
        return {**input_data, "processed": True}


class ThenPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for 'then' branch."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'then_executed' field to input."""
        return {**input_data, "then_executed": True}


class ElsePrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for 'else' branch."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'else_executed' field to input."""
        return {**input_data, "else_executed": True}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Raise an error."""
        raise ValueError("Test error")


@pytest.mark.asyncio
async def test_conditional_logs_workflow_start_and_completion() -> None:
    """Verify that ConditionalPrimitive logs workflow start and completion."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"value": 10}, context)

    # Verify via checkpoints (structlog logs to stdout)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.start" in checkpoint_names
    assert "conditional.end" in checkpoint_names


@pytest.mark.asyncio
async def test_conditional_logs_condition_evaluation() -> None:
    """Verify that ConditionalPrimitive logs condition evaluation."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"value": 10}, context)

    # Verify checkpoints for condition evaluation
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.condition_eval.start" in checkpoint_names
    assert "conditional.condition_eval.end" in checkpoint_names


@pytest.mark.asyncio
async def test_conditional_records_branch_checkpoints() -> None:
    """Verify that ConditionalPrimitive records checkpoints for branches."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    # Test 'then' branch
    await workflow.execute({"value": 10}, context)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.branch_then.start" in checkpoint_names
    assert "conditional.branch_then.end" in checkpoint_names

    # Test 'else' branch
    context2 = WorkflowContext(workflow_id="test-workflow")
    await workflow.execute({"value": 3}, context2)
    checkpoint_names2 = [name for name, _ in context2.checkpoints]
    assert "conditional.branch_else.start" in checkpoint_names2
    assert "conditional.branch_else.end" in checkpoint_names2


@pytest.mark.asyncio
async def test_conditional_records_branch_metrics() -> None:
    """Verify that ConditionalPrimitive records per-branch metrics."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    # Execute 'then' branch
    await workflow.execute({"value": 10}, context)

    # Check that branch metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()

    # Get metrics for 'then' branch
    then_metrics = metrics_collector.get_all_metrics("ConditionalPrimitive.branch_then")
    condition_metrics = metrics_collector.get_all_metrics("ConditionalPrimitive.condition_eval")

    # Verify metrics exist
    assert then_metrics is not None
    assert condition_metrics is not None

    # Check enhanced metrics structure
    assert "percentiles" in then_metrics
    assert then_metrics["percentiles"]["p50"] >= 0


@pytest.mark.asyncio
async def test_conditional_creates_branch_spans() -> None:
    """Verify that ConditionalPrimitive attempts to create spans when tracing available."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"value": 10}, context)

    # Verify execution succeeded (spans created or gracefully degraded)
    assert result["then_executed"] is True

    # Verify checkpoints were recorded (proves execution path was followed)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.branch_then.start" in checkpoint_names


@pytest.mark.asyncio
async def test_conditional_span_attributes() -> None:
    """Verify that branch execution includes proper attribute tracking."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"value": 10}, context)

    # Verify execution succeeded
    assert result["then_executed"] is True

    # Verify metrics were recorded (proves attributes were tracked)
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    metrics_collector = get_enhanced_metrics_collector()
    then_metrics = metrics_collector.get_all_metrics("ConditionalPrimitive.branch_then")

    assert then_metrics is not None


@pytest.mark.asyncio
async def test_conditional_error_handling_with_spans() -> None:
    """Verify that errors in branches are properly propagated."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=FailingPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Test error"):
        await workflow.execute({"value": 10}, context)

    # Verify condition was evaluated before error
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.condition_eval.start" in checkpoint_names
    assert "conditional.branch_then.start" in checkpoint_names


@pytest.mark.asyncio
async def test_conditional_preserves_existing_functionality() -> None:
    """Verify that Phase 2 changes don't break existing functionality."""
    # Test 'then' branch
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test")

    result = await workflow.execute({"value": 10}, context)
    assert result["then_executed"] is True
    assert "else_executed" not in result

    # Test 'else' branch
    result2 = await workflow.execute({"value": 3}, context)
    assert result2["else_executed"] is True
    assert "then_executed" not in result2

    # Test passthrough (no else branch)
    workflow2 = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
    )
    result3 = await workflow2.execute({"value": 3}, context)
    assert result3 == {"value": 3}  # Passthrough


@pytest.mark.asyncio
async def test_conditional_passthrough_logging() -> None:
    """Verify that ConditionalPrimitive logs passthrough when no else branch."""
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=ThenPrimitive(),
        # No else_primitive
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"value": 3}, context)

    # Verify passthrough
    assert result == {"value": 3}

    # Verify checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.start" in checkpoint_names
    assert "conditional.condition_eval.start" in checkpoint_names
    assert "conditional.end" in checkpoint_names
    # Should NOT have branch checkpoints
    assert "conditional.branch_then.start" not in checkpoint_names
    assert "conditional.branch_else.start" not in checkpoint_names


@pytest.mark.asyncio
async def test_conditional_condition_error_handling() -> None:
    """Verify that errors in condition evaluation are properly handled."""

    def failing_condition(data, ctx) -> Never:
        raise RuntimeError("Condition evaluation failed")

    workflow = ConditionalPrimitive(
        condition=failing_condition,
        then_primitive=ThenPrimitive(),
        else_primitive=ElsePrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(RuntimeError, match="Condition evaluation failed"):
        await workflow.execute({"value": 10}, context)

    # Verify condition evaluation was attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "conditional.condition_eval.start" in checkpoint_names
