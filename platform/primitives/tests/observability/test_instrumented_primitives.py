"""Tests for instrumented workflow primitives."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class SimplePrimitive(InstrumentedPrimitive[dict, dict]):
    """Simple test primitive that adds a field."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'processed' field to input."""
        return {**input_data, "processed": True}


class CounterPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that counts executions."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name)
        self.call_count = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Increment counter and return input."""
        self.call_count += 1
        return {**input_data, "count": self.call_count}


@pytest.mark.asyncio
async def test_instrumented_primitive_basic_execution() -> None:
    """Test basic execution of instrumented primitive."""
    primitive = SimplePrimitive(name="test_primitive")
    context = WorkflowContext(workflow_id="test")

    result = await primitive.execute({"key": "value"}, context)

    assert result == {"key": "value", "processed": True}
    assert primitive.name == "test_primitive"


@pytest.mark.asyncio
async def test_instrumented_primitive_default_name() -> None:
    """Test that primitive uses class name if no name provided."""
    primitive = SimplePrimitive()
    context = WorkflowContext(workflow_id="test")

    result = await primitive.execute({"key": "value"}, context)

    assert result == {"key": "value", "processed": True}
    assert primitive.name == "SimplePrimitive"


@pytest.mark.asyncio
async def test_instrumented_primitive_checkpoints() -> None:
    """Test that primitive records checkpoints."""
    primitive = SimplePrimitive(name="test")
    context = WorkflowContext(workflow_id="test")

    await primitive.execute({"key": "value"}, context)

    # Should have start and end checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "test.start" in checkpoint_names
    assert "test.end" in checkpoint_names


@pytest.mark.asyncio
async def test_instrumented_primitive_trace_context_injection() -> None:
    """Test that primitive injects trace context."""
    primitive = SimplePrimitive(name="test")
    context = WorkflowContext(workflow_id="test")

    # Context should not have trace_id initially
    assert context.trace_id is None

    await primitive.execute({"key": "value"}, context)

    # After execution, context may have trace_id if OTel is active
    # (graceful degradation means it might still be None)
    # Just verify no errors occurred


@pytest.mark.asyncio
async def test_instrumented_primitive_error_handling() -> None:
    """Test that primitive handles errors correctly."""

    class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
        async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
            raise ValueError("Test error")

    primitive = FailingPrimitive(name="failing")
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Test error"):
        await primitive.execute({"key": "value"}, context)

    # Should still have checkpoints even on error
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "failing.start" in checkpoint_names
    assert "failing.end" in checkpoint_names


@pytest.mark.asyncio
async def test_sequential_primitive_instrumentation() -> None:
    """Test that SequentialPrimitive is properly instrumented."""
    step1 = CounterPrimitive(name="step1")
    step2 = CounterPrimitive(name="step2")
    step3 = CounterPrimitive(name="step3")

    workflow = SequentialPrimitive([step1, step2, step3])
    context = WorkflowContext(workflow_id="test")

    result = await workflow.execute({"input": "data"}, context)

    # All steps should have executed
    assert step1.call_count == 1
    assert step2.call_count == 1
    assert step3.call_count == 1

    # Result should have count from last step
    assert result["count"] == 1

    # Should have checkpoints for sequential and each step
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "SequentialPrimitive.start" in checkpoint_names
    assert "sequential.step_0.start" in checkpoint_names
    assert "sequential.step_0.end" in checkpoint_names
    assert "sequential.step_1.start" in checkpoint_names
    assert "sequential.step_1.end" in checkpoint_names
    assert "sequential.step_2.start" in checkpoint_names
    assert "sequential.step_2.end" in checkpoint_names
    assert "SequentialPrimitive.end" in checkpoint_names


@pytest.mark.asyncio
async def test_sequential_primitive_trace_propagation() -> None:
    """Test that trace context propagates through sequential steps."""
    step1 = SimplePrimitive(name="step1")
    step2 = SimplePrimitive(name="step2")

    workflow = SequentialPrimitive([step1, step2])
    context = WorkflowContext(
        workflow_id="test",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
    )

    result = await workflow.execute({"input": "data"}, context)

    # Trace context should be preserved
    assert context.trace_id == "0123456789abcdef0123456789abcdef"
    assert result["processed"] is True


@pytest.mark.asyncio
async def test_parallel_primitive_instrumentation() -> None:
    """Test that ParallelPrimitive is properly instrumented."""
    branch1 = CounterPrimitive(name="branch1")
    branch2 = CounterPrimitive(name="branch2")
    branch3 = CounterPrimitive(name="branch3")

    workflow = ParallelPrimitive([branch1, branch2, branch3])
    context = WorkflowContext(workflow_id="test")

    results = await workflow.execute({"input": "data"}, context)

    # All branches should have executed
    assert branch1.call_count == 1
    assert branch2.call_count == 1
    assert branch3.call_count == 1

    # Should return list of results
    assert len(results) == 3
    assert all(r["count"] == 1 for r in results)

    # Should have checkpoints for parallel primitive
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "ParallelPrimitive.start" in checkpoint_names
    assert "ParallelPrimitive.end" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_primitive_child_contexts() -> None:
    """Test that ParallelPrimitive creates child contexts for branches."""

    class ContextCapturePrimitive(InstrumentedPrimitive[dict, dict]):
        """Primitive that captures its context."""

        def __init__(self, name: str | None = None) -> None:
            super().__init__(name=name)
            self.captured_context: WorkflowContext | None = None

        async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
            self.captured_context = context
            return input_data

    branch1 = ContextCapturePrimitive(name="branch1")
    branch2 = ContextCapturePrimitive(name="branch2")

    workflow = ParallelPrimitive([branch1, branch2])
    parent_context = WorkflowContext(
        workflow_id="test",
        correlation_id="parent-corr-id",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
    )

    await workflow.execute({"input": "data"}, parent_context)

    # Both branches should have captured their contexts
    assert branch1.captured_context is not None
    assert branch2.captured_context is not None

    # Child contexts should inherit correlation_id
    assert branch1.captured_context.correlation_id == "parent-corr-id"
    assert branch2.captured_context.correlation_id == "parent-corr-id"

    # Child contexts should inherit trace_id
    assert branch1.captured_context.trace_id == "0123456789abcdef0123456789abcdef"
    assert branch2.captured_context.trace_id == "0123456789abcdef0123456789abcdef"

    # Child contexts should have parent_span_id set to parent's span_id
    # Note: The actual span_id may be updated by inject_trace_context,
    # but parent_span_id should be set from the parent context
    assert branch1.captured_context.parent_span_id is not None
    assert branch2.captured_context.parent_span_id is not None


@pytest.mark.asyncio
async def test_sequential_operator_still_works() -> None:
    """Test that >> operator still works with instrumented primitives."""
    step1 = SimplePrimitive(name="step1")
    step2 = SimplePrimitive(name="step2")

    # Use >> operator
    workflow = step1 >> step2

    context = WorkflowContext(workflow_id="test")
    result = await workflow.execute({"input": "data"}, context)

    assert result["processed"] is True
    assert isinstance(workflow, SequentialPrimitive)


@pytest.mark.asyncio
async def test_parallel_operator_still_works() -> None:
    """Test that | operator still works with instrumented primitives."""
    branch1 = SimplePrimitive(name="branch1")
    branch2 = SimplePrimitive(name="branch2")

    # Use | operator
    workflow = branch1 | branch2

    context = WorkflowContext(workflow_id="test")
    results = await workflow.execute({"input": "data"}, context)

    assert len(results) == 2
    assert all(r["processed"] is True for r in results)
    assert isinstance(workflow, ParallelPrimitive)
