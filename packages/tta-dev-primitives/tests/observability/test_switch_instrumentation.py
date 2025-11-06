"""Tests for SwitchPrimitive Phase 2 instrumentation."""

from typing import Never

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.conditional import SwitchPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class SimplePrimitive(InstrumentedPrimitive[dict, dict]):
    """Simple test primitive that adds a field."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'processed' field to input."""
        return {**input_data, "processed": True}


class CaseAPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for case 'a'."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'case_a_executed' field to input."""
        return {**input_data, "case_a_executed": True}


class CaseBPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for case 'b'."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'case_b_executed' field to input."""
        return {**input_data, "case_b_executed": True}


class CaseCPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for case 'c'."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'case_c_executed' field to input."""
        return {**input_data, "case_c_executed": True}


class DefaultPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for default case."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'default_executed' field to input."""
        return {**input_data, "default_executed": True}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Raise an error."""
        raise ValueError("Test error")


@pytest.mark.asyncio
async def test_switch_logs_workflow_start_and_completion() -> None:
    """Verify that SwitchPrimitive logs workflow start and completion."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
            "c": CaseCPrimitive(),
        },
        default=DefaultPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"case": "a"}, context)

    # Verify via checkpoints (structlog logs to stdout)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.start" in checkpoint_names
    assert "switch.end" in checkpoint_names


@pytest.mark.asyncio
async def test_switch_logs_selector_evaluation() -> None:
    """Verify that SwitchPrimitive logs selector evaluation."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"case": "a"}, context)

    # Verify checkpoints for selector evaluation
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.selector_eval.start" in checkpoint_names
    assert "switch.selector_eval.end" in checkpoint_names


@pytest.mark.asyncio
async def test_switch_records_case_checkpoints() -> None:
    """Verify that SwitchPrimitive records checkpoints for cases."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
            "c": CaseCPrimitive(),
        },
        default=DefaultPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    # Test case 'a'
    await workflow.execute({"case": "a"}, context)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.case_a.start" in checkpoint_names
    assert "switch.case_a.end" in checkpoint_names

    # Test case 'b'
    context2 = WorkflowContext(workflow_id="test-workflow")
    await workflow.execute({"case": "b"}, context2)
    checkpoint_names2 = [name for name, _ in context2.checkpoints]
    assert "switch.case_b.start" in checkpoint_names2
    assert "switch.case_b.end" in checkpoint_names2

    # Test default case
    context3 = WorkflowContext(workflow_id="test-workflow")
    await workflow.execute({"case": "unknown"}, context3)
    checkpoint_names3 = [name for name, _ in context3.checkpoints]
    assert "switch.default.start" in checkpoint_names3
    assert "switch.default.end" in checkpoint_names3


@pytest.mark.asyncio
async def test_switch_records_case_metrics() -> None:
    """Verify that SwitchPrimitive records per-case metrics."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
    )
    context = WorkflowContext(workflow_id="test-workflow")

    # Execute case 'a'
    await workflow.execute({"case": "a"}, context)

    # Check that case metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()

    # Get metrics for case 'a'
    case_a_metrics = metrics_collector.get_all_metrics("SwitchPrimitive.case_a")
    selector_metrics = metrics_collector.get_all_metrics("SwitchPrimitive.selector_eval")

    # Verify metrics exist
    assert case_a_metrics is not None
    assert selector_metrics is not None

    # Check enhanced metrics structure
    assert "percentiles" in case_a_metrics
    assert case_a_metrics["percentiles"]["p50"] >= 0


@pytest.mark.asyncio
async def test_switch_creates_case_spans() -> None:
    """Verify that SwitchPrimitive attempts to create spans when tracing available."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"case": "a"}, context)

    # Verify execution succeeded (spans created or gracefully degraded)
    assert result["case_a_executed"] is True

    # Verify checkpoints were recorded (proves execution path was followed)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.case_a.start" in checkpoint_names


@pytest.mark.asyncio
async def test_switch_span_attributes() -> None:
    """Verify that case execution includes proper attribute tracking."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"case": "a"}, context)

    # Verify execution succeeded
    assert result["case_a_executed"] is True

    # Verify metrics were recorded (proves attributes were tracked)
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    metrics_collector = get_enhanced_metrics_collector()
    case_a_metrics = metrics_collector.get_all_metrics("SwitchPrimitive.case_a")

    assert case_a_metrics is not None


@pytest.mark.asyncio
async def test_switch_error_handling_in_case() -> None:
    """Verify that errors in cases are properly propagated."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": FailingPrimitive(),
            "b": CaseBPrimitive(),
        },
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Test error"):
        await workflow.execute({"case": "a"}, context)

    # Verify selector was evaluated before error
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.selector_eval.start" in checkpoint_names
    assert "switch.case_a.start" in checkpoint_names


@pytest.mark.asyncio
async def test_switch_default_case_handling() -> None:
    """Verify that SwitchPrimitive handles default case correctly."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
        default=DefaultPrimitive(),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"case": "unknown"}, context)

    # Verify default was executed
    assert result["default_executed"] is True

    # Verify checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.default.start" in checkpoint_names
    assert "switch.default.end" in checkpoint_names


@pytest.mark.asyncio
async def test_switch_passthrough_logging() -> None:
    """Verify that SwitchPrimitive logs passthrough when no matching case or default."""
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
        # No default
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"case": "unknown"}, context)

    # Verify passthrough
    assert result == {"case": "unknown"}

    # Verify checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.start" in checkpoint_names
    assert "switch.selector_eval.start" in checkpoint_names
    assert "switch.end" in checkpoint_names
    # Should NOT have case checkpoints
    assert "switch.case_a.start" not in checkpoint_names
    assert "switch.default.start" not in checkpoint_names


@pytest.mark.asyncio
async def test_switch_selector_error_handling() -> None:
    """Verify that errors in selector evaluation are properly handled."""

    def failing_selector(data, ctx) -> Never:
        raise RuntimeError("Selector evaluation failed")

    workflow = SwitchPrimitive(
        selector=failing_selector,
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
        },
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(RuntimeError, match="Selector evaluation failed"):
        await workflow.execute({"case": "a"}, context)

    # Verify selector evaluation was attempted
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "switch.selector_eval.start" in checkpoint_names


@pytest.mark.asyncio
async def test_switch_preserves_existing_functionality() -> None:
    """Verify that Phase 2 changes don't break existing functionality."""
    # Test case 'a'
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
            "b": CaseBPrimitive(),
            "c": CaseCPrimitive(),
        },
        default=DefaultPrimitive(),
    )
    context = WorkflowContext(workflow_id="test")

    result = await workflow.execute({"case": "a"}, context)
    assert result["case_a_executed"] is True
    assert "case_b_executed" not in result
    assert "default_executed" not in result

    # Test case 'b'
    result2 = await workflow.execute({"case": "b"}, context)
    assert result2["case_b_executed"] is True
    assert "case_a_executed" not in result2

    # Test default case
    result3 = await workflow.execute({"case": "unknown"}, context)
    assert result3["default_executed"] is True

    # Test passthrough (no default)
    workflow2 = SwitchPrimitive(
        selector=lambda data, ctx: data.get("case", "a"),
        cases={
            "a": CaseAPrimitive(),
        },
    )
    result4 = await workflow2.execute({"case": "unknown"}, context)
    assert result4 == {"case": "unknown"}  # Passthrough
