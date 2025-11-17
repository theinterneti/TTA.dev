import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_sequential_primitive_init_empty_primitives_raises_error():
    """
    Test that SequentialPrimitive raises ValueError if initialized with an empty list.
    """
    with pytest.raises(
        ValueError, match="SequentialPrimitive requires at least one primitive"
    ):
        SequentialPrimitive([])


@pytest.mark.asyncio
async def test_sequential_primitive_single_primitive_execution():
    """
    Test that SequentialPrimitive executes a single primitive correctly.
    """
    mock_primitive = MockPrimitive(name="Mock1", return_value="output1")
    workflow = SequentialPrimitive([mock_primitive])
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute("input1", context)

    assert result == "output1"
    assert mock_primitive.call_count == 1
    assert mock_primitive.calls[-1][0] == "input1"
    assert mock_primitive.calls[-1][1] == context


@pytest.mark.asyncio
async def test_sequential_primitive_multiple_primitives_execution():
    """
    Test that SequentialPrimitive executes multiple primitives in sequence,
    passing output as input.
    """
    mock_primitive1 = MockPrimitive(name="Mock1", return_value="output1")
    mock_primitive2 = MockPrimitive(name="Mock2", return_value="output2")
    mock_primitive3 = MockPrimitive(name="Mock3", return_value="output3")

    workflow = SequentialPrimitive([mock_primitive1, mock_primitive2, mock_primitive3])
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute("initial_input", context)

    assert result == "output3"

    assert mock_primitive1.call_count == 1
    assert mock_primitive1.calls[-1][0] == "initial_input"

    assert mock_primitive2.call_count == 1
    assert mock_primitive2.calls[-1][0] == "output1"

    assert mock_primitive3.call_count == 1
    assert mock_primitive3.calls[-1][0] == "output2"


@pytest.mark.asyncio
async def test_sequential_primitive_chaining_operator():
    """
    Test that the >> operator correctly chains primitives.
    """
    mock_primitive1 = MockPrimitive(name="Mock1", return_value="output1")
    mock_primitive2 = MockPrimitive(name="Mock2", return_value="output2")

    workflow = mock_primitive1 >> mock_primitive2
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute("initial_input", context)

    assert result == "output2"
    assert mock_primitive1.call_count == 1
    assert mock_primitive1.calls[-1][0] == "initial_input"
    assert mock_primitive2.call_count == 1
    assert mock_primitive2.calls[-1][0] == "output1"


@pytest.mark.asyncio
async def test_sequential_primitive_chaining_with_nested_sequential():
    """
    Test that chaining with a nested SequentialPrimitive flattens correctly.
    """
    mock_primitive1 = MockPrimitive(name="Mock1", return_value="output1")
    nested_sequential = SequentialPrimitive(
        [
            MockPrimitive(name="Nested1", return_value="nested_output1"),
            MockPrimitive(name="Nested2", return_value="nested_output2"),
        ]
    )
    mock_primitive3 = MockPrimitive(name="Mock3", return_value="output3")

    workflow = mock_primitive1 >> nested_sequential >> mock_primitive3
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute("initial_input", context)

    assert result == "output3"
    assert len(workflow.primitives) == 3  # Should be flattened

    # Verify execution order and inputs
    assert workflow.primitives[0].call_count == 1
    assert workflow.primitives[0].calls[-1][0] == "initial_input"
    # The second primitive in the flattened list is the first MockPrimitive from nested_sequential
    assert nested_sequential.primitives[0].call_count == 1
    assert nested_sequential.primitives[0].calls[-1][0] == "output1"
    # The third primitive in the flattened list is the second MockPrimitive from nested_sequential
    assert nested_sequential.primitives[1].call_count == 1
    assert nested_sequential.primitives[1].calls[-1][0] == "nested_output1"


@pytest.mark.asyncio
async def test_sequential_primitive_error_handling():
    """
    Test that SequentialPrimitive correctly propagates exceptions from a failing primitive.
    """
    mock_primitive1 = MockPrimitive(name="Mock1", return_value="output1")
    failing_primitive = MockPrimitive(
        name="FailingMock", raise_error=Exception("Test error")
    )
    mock_primitive3 = MockPrimitive(name="Mock3", return_value="output3")

    workflow = SequentialPrimitive(
        [mock_primitive1, failing_primitive, mock_primitive3]
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(Exception, match="Test error"):
        await workflow.execute("initial_input", context)

    assert mock_primitive1.call_count == 1
    assert failing_primitive.call_count == 1
    assert mock_primitive3.call_count == 0  # Should not be called after failure
