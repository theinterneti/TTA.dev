import asyncio

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_parallel_basic_execution():
    """Tests basic parallel execution with multiple successful mock primitives."""
    mock1 = MockPrimitive(name="mock1", return_value="result1")
    mock2 = MockPrimitive(name="mock2", return_value="result2")
    mock3 = MockPrimitive(name="mock3", return_value="result3")

    parallel_workflow = ParallelPrimitive([mock1, mock2, mock3])
    context = WorkflowContext()
    input_data = {"key": "value"}

    results = await parallel_workflow.execute(input_data, context)

    assert results == ["result1", "result2", "result3"]
    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1


@pytest.mark.asyncio
async def test_parallel_input_data_distribution():
    """Tests that all parallel branches receive the same input data."""
    mock1 = MockPrimitive(name="mock1")
    mock2 = MockPrimitive(name="mock2")

    parallel_workflow = ParallelPrimitive([mock1, mock2])
    context = WorkflowContext()
    input_data = {"data": "shared"}

    await parallel_workflow.execute(input_data, context)

    assert mock1.calls[0][0] == input_data
    assert mock2.calls[0][0] == input_data


@pytest.mark.asyncio
async def test_parallel_exception_handling():
    """Tests that if one primitive fails, the entire workflow fails."""
    mock_success = MockPrimitive(name="mock_success", return_value="success")
    mock_failure = MockPrimitive(name="mock_failure", raise_error=ValueError("Branch failed"))

    parallel_workflow = ParallelPrimitive([mock_success, mock_failure])
    context = WorkflowContext()
    input_data = {}

    with pytest.raises(ValueError, match="Branch failed"):
        await parallel_workflow.execute(input_data, context)

    assert mock_success.call_count == 1
    assert mock_failure.call_count == 1


@pytest.mark.asyncio
async def test_parallel_or_operator():
    """Tests the `|` operator for composing a ParallelPrimitive."""
    mock1 = MockPrimitive(name="mock1", return_value=1)
    mock2 = MockPrimitive(name="mock2", return_value=2)
    mock3 = MockPrimitive(name="mock3", return_value=3)

    parallel_workflow = mock1 | mock2 | mock3
    context = WorkflowContext()
    input_data = {}

    results = await parallel_workflow.execute(input_data, context)

    assert isinstance(parallel_workflow, ParallelPrimitive)
    assert len(parallel_workflow.primitives) == 3
    assert results == [1, 2, 3]


@pytest.mark.asyncio
async def test_parallel_flattening_nested_primitives():
    """Tests the flattening of nested ParallelPrimitives."""
    mock1 = MockPrimitive(name="mock1", return_value=1)
    mock2 = MockPrimitive(name="mock2", return_value=2)
    mock3 = MockPrimitive(name="mock3", return_value=3)
    mock4 = MockPrimitive(name="mock4", return_value=4)

    nested_parallel = mock1 | mock2
    workflow = nested_parallel | mock3 | mock4

    assert isinstance(workflow, ParallelPrimitive)
    assert len(workflow.primitives) == 4

    context = WorkflowContext()
    results = await workflow.execute({}, context)
    assert results == [1, 2, 3, 4]


def test_parallel_empty_initialization():
    """Tests that initializing with an empty list raises a ValueError."""
    with pytest.raises(ValueError, match="ParallelPrimitive requires at least one primitive"):
        ParallelPrimitive([])


@pytest.mark.asyncio
async def test_parallel_workflow_context_children():
    """Verify that a unique WorkflowContext child is passed to each branch."""
    mock1 = MockPrimitive(name="mock1")
    mock2 = MockPrimitive(name="mock2")

    parallel_workflow = ParallelPrimitive([mock1, mock2])
    parent_context = WorkflowContext(workflow_id="parent")

    await parallel_workflow.execute({}, parent_context)

    context1 = mock1.calls[0][1]
    context2 = mock2.calls[0][1]

    assert isinstance(context1, WorkflowContext)
    assert isinstance(context2, WorkflowContext)
    assert context1 is not context2
    assert context1.workflow_id == "parent"
    assert context2.workflow_id == "parent"
    assert context1.parent_span_id == parent_context.span_id
    assert context2.parent_span_id == parent_context.span_id
    assert context1.causation_id == parent_context.correlation_id
    assert context2.causation_id == parent_context.correlation_id


@pytest.mark.asyncio
async def test_parallel_with_async_primitives():
    """Tests parallel execution with primitives that have async delays."""

    async def slow_primitive(delay, result):
        await asyncio.sleep(delay)
        return result

    mock1 = MockPrimitive(
        name="mock1", side_effect=lambda *args, **kwargs: slow_primitive(0.02, "fast")
    )
    mock2 = MockPrimitive(
        name="mock2", side_effect=lambda *args, **kwargs: slow_primitive(0.01, "faster")
    )

    workflow = mock1 | mock2
    context = WorkflowContext()

    start_time = asyncio.get_event_loop().time()
    results = await workflow.execute({}, context)
    end_time = asyncio.get_event_loop().time()

    # The total time should be slightly more than the longest delay, not the sum
    assert (end_time - start_time) < 0.03
    assert set(results) == {"fast", "faster"}
