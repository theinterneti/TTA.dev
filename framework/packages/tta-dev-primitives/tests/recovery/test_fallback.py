import pytest

from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_fallback_primary_succeeds():
    """Tests that the primary primitive's result is returned when it succeeds."""
    primary = MockPrimitive(name="primary", return_value="primary_success")
    fallback = MockPrimitive(name="fallback", return_value="fallback_success")

    fallback_primitive = FallbackPrimitive(primary=primary, fallback=fallback)
    context = WorkflowContext()

    result = await fallback_primitive.execute({}, context)

    assert result == "primary_success"
    assert primary.call_count == 1
    assert fallback.call_count == 0

@pytest.mark.asyncio
async def test_fallback_uses_fallback_on_primary_failure():
    """Tests that the fallback primitive is executed when the primary fails."""
    primary = MockPrimitive(name="primary", raise_error=ValueError("Primary failed"))
    fallback = MockPrimitive(name="fallback", return_value="fallback_success")

    fallback_primitive = FallbackPrimitive(primary=primary, fallback=fallback)
    context = WorkflowContext()

    result = await fallback_primitive.execute({}, context)

    assert result == "fallback_success"
    assert primary.call_count == 1
    assert fallback.call_count == 1

@pytest.mark.asyncio
async def test_fallback_both_fail():
    """Tests that an exception is raised when both primary and fallback primitives fail."""
    primary = MockPrimitive(name="primary", raise_error=ValueError("Primary failed"))
    fallback = MockPrimitive(name="fallback", raise_error=RuntimeError("Fallback failed"))

    fallback_primitive = FallbackPrimitive(primary=primary, fallback=fallback)
    context = WorkflowContext()

    with pytest.raises(ValueError, match="Primary failed"):
        await fallback_primitive.execute({}, context)

    assert primary.call_count == 1
    assert fallback.call_count == 1

@pytest.mark.asyncio
async def test_fallback_context_and_data_passed_correctly():
    """Tests that the context and input data are passed correctly to both primitives."""
    primary = MockPrimitive(name="primary", raise_error=ValueError("Primary failed"))
    fallback = MockPrimitive(name="fallback", return_value="fallback_success")

    fallback_primitive = FallbackPrimitive(primary=primary, fallback=fallback)
    context = WorkflowContext(workflow_id="test_workflow")
    input_data = {"key": "value"}

    await fallback_primitive.execute(input_data, context)

    assert primary.calls[0][0] == input_data
    assert primary.calls[0][1] is context
    assert fallback.calls[0][0] == input_data
    assert fallback.calls[0][1] is context
