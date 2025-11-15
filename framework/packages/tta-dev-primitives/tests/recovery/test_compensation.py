import pytest

from tta_dev_primitives.recovery.compensation import SagaPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_saga_forward_succeeds():
    """Tests that the forward primitive's result is returned and compensation is not called."""
    forward = MockPrimitive(name="forward", return_value="forward_success")
    compensation = MockPrimitive(name="compensation")

    saga_primitive = SagaPrimitive(forward=forward, compensation=compensation)
    context = WorkflowContext()

    result = await saga_primitive.execute({}, context)

    assert result == "forward_success"
    assert forward.call_count == 1
    assert compensation.call_count == 0

@pytest.mark.asyncio
async def test_saga_forward_fails_compensation_succeeds():
    """Tests that the compensation primitive is called when the forward primitive fails."""
    forward = MockPrimitive(name="forward", raise_error=ValueError("Forward failed"))
    compensation = MockPrimitive(name="compensation")

    saga_primitive = SagaPrimitive(forward=forward, compensation=compensation)
    context = WorkflowContext()

    with pytest.raises(ValueError, match="Forward failed"):
        await saga_primitive.execute({}, context)

    assert forward.call_count == 1
    assert compensation.call_count == 1

@pytest.mark.asyncio
async def test_saga_forward_and_compensation_fail():
    """Tests that the original exception is raised when both forward and compensation fail."""
    forward = MockPrimitive(name="forward", raise_error=ValueError("Forward failed"))
    compensation = MockPrimitive(name="compensation", raise_error=RuntimeError("Compensation failed"))

    saga_primitive = SagaPrimitive(forward=forward, compensation=compensation)
    context = WorkflowContext()

    with pytest.raises(ValueError, match="Forward failed"):
        await saga_primitive.execute({}, context)

    assert forward.call_count == 1
    assert compensation.call_count == 1

@pytest.mark.asyncio
async def test_saga_context_and_data_passed_correctly():
    """Tests that context and input data are passed correctly to both primitives."""
    forward = MockPrimitive(name="forward", raise_error=ValueError("Forward failed"))
    compensation = MockPrimitive(name="compensation")

    saga_primitive = SagaPrimitive(forward=forward, compensation=compensation)
    context = WorkflowContext(workflow_id="test_workflow")
    input_data = {"key": "value"}

    with pytest.raises(ValueError, match="Forward failed"):
        await saga_primitive.execute(input_data, context)

    assert forward.calls[0][0] == input_data
    assert forward.calls[0][1] is context
    assert compensation.calls[0][0] == input_data
    assert compensation.calls[0][1] is context
