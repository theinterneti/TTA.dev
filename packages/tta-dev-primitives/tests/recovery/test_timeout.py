import asyncio
import pytest

from tta_dev_primitives.recovery.timeout import TimeoutPrimitive, TimeoutError
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

async def slow_primitive_task(delay, result):
    await asyncio.sleep(delay)
    return result

@pytest.mark.asyncio
async def test_timeout_succeeds_within_limit():
    """Tests that the primitive succeeds if it completes within the timeout."""
    primitive = MockPrimitive(name="fast_primitive")
    primitive.side_effect = lambda *args, **kwargs: slow_primitive_task(0.01, "success")

    timeout_primitive = TimeoutPrimitive(primitive, timeout_seconds=0.1)
    context = WorkflowContext()

    result = await timeout_primitive.execute({}, context)
    assert result == "success"
    assert primitive.call_count == 1

@pytest.mark.asyncio
async def test_timeout_exceeded_no_fallback():
    """Tests that a TimeoutError is raised when the timeout is exceeded and there is no fallback."""
    primitive = MockPrimitive(name="slow_primitive")
    primitive.side_effect = lambda *args, **kwargs: slow_primitive_task(0.2, "should_fail")

    timeout_primitive = TimeoutPrimitive(primitive, timeout_seconds=0.1)
    context = WorkflowContext()

    with pytest.raises(TimeoutError, match="Execution exceeded 0.1s timeout"):
        await timeout_primitive.execute({}, context)
    assert primitive.call_count == 1

@pytest.mark.asyncio
async def test_timeout_exceeded_with_fallback():
    """Tests that the fallback is executed when the timeout is exceeded."""
    primitive = MockPrimitive(name="slow_primitive")
    primitive.side_effect = lambda *args, **kwargs: slow_primitive_task(0.2, "should_fail")
    fallback = MockPrimitive(name="fallback", return_value="fallback_success")

    timeout_primitive = TimeoutPrimitive(primitive, timeout_seconds=0.1, fallback=fallback)
    context = WorkflowContext()

    result = await timeout_primitive.execute({}, context)
    assert result == "fallback_success"
    assert primitive.call_count == 1
    assert fallback.call_count == 1

@pytest.mark.asyncio
async def test_timeout_tracking_in_context():
    """Tests that timeout occurrences are tracked in the workflow context."""
    primitive = MockPrimitive(name="slow_primitive")
    primitive.side_effect = lambda *args, **kwargs: slow_primitive_task(0.2, "should_fail")
    fallback = MockPrimitive(name="fallback")

    timeout_primitive = TimeoutPrimitive(primitive, timeout_seconds=0.1, fallback=fallback, track_timeouts=True)
    context = WorkflowContext()

    await timeout_primitive.execute({}, context)

    assert context.state["timeout_count"] == 1
    assert len(context.state["timeout_history"]) == 1
    history_item = context.state["timeout_history"][0]
    assert history_item["primitive"] == "MockPrimitive"
    assert history_item["timeout"] == 0.1
    assert history_item["had_fallback"] is True

@pytest.mark.asyncio
async def test_timeout_no_tracking_in_context():
    """Tests that timeouts are not tracked when track_timeouts is False."""
    primitive = MockPrimitive(name="slow_primitive")
    primitive.side_effect = lambda *args, **kwargs: slow_primitive_task(0.2, "should_fail")
    fallback = MockPrimitive(name="fallback")

    timeout_primitive = TimeoutPrimitive(primitive, timeout_seconds=0.1, fallback=fallback, track_timeouts=False)
    context = WorkflowContext()

    await timeout_primitive.execute({}, context)

    assert "timeout_count" not in context.state
    assert "timeout_history" not in context.state
