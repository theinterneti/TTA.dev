import asyncio

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.recovery.timeout import TimeoutPrimitive
from tta_dev_primitives.testing import MockPrimitive


async def slow_primitive_task(delay, result):
    await asyncio.sleep(delay)
    return result


@pytest.mark.asyncio
async def test_retry_with_fallback():
    """
    Integration test for RetryPrimitive and FallbackPrimitive.
    - The primary primitive will fail multiple times.
    - The RetryPrimitive will exhaust its retries.
    - The FallbackPrimitive will then execute the fallback.
    """
    # A primitive that will always fail
    failing_primitive = MockPrimitive(
        name="failing_primitive", raise_error=ValueError("Always fails")
    )

    # A fallback primitive that will succeed
    fallback_primitive = MockPrimitive(name="fallback_primitive", return_value="fallback_success")

    # Wrap the failing primitive in a retry primitive
    retry_primitive = RetryPrimitive(
        failing_primitive, strategy=RetryStrategy(max_retries=2, backoff_base=0.01)
    )

    # Wrap the retry primitive in a fallback primitive
    workflow = FallbackPrimitive(primary=retry_primitive, fallback=fallback_primitive)

    context = WorkflowContext()
    result = await workflow.execute({}, context)

    # The final result should be from the fallback
    assert result == "fallback_success"

    # The failing primitive should have been called 3 times (1 initial + 2 retries)
    assert failing_primitive.call_count == 3

    # The fallback primitive should have been called once
    assert fallback_primitive.call_count == 1


@pytest.mark.asyncio
async def test_timeout_with_fallback():
    """
    Integration test for TimeoutPrimitive and FallbackPrimitive.
    - The primary primitive will exceed its timeout.
    - The TimeoutPrimitive will trigger the fallback.
    """
    # A primitive that will be too slow
    slow_primitive = MockPrimitive(name="slow_primitive")
    slow_primitive.side_effect = lambda *args, **kwargs: slow_primitive_task(0.2, "should_fail")

    # A fallback primitive that will succeed
    fallback_primitive = MockPrimitive(name="fallback_primitive", return_value="fallback_success")

    # Wrap the slow primitive in a timeout primitive
    timeout_primitive = TimeoutPrimitive(
        slow_primitive, timeout_seconds=0.1, fallback=fallback_primitive
    )

    context = WorkflowContext()
    result = await timeout_primitive.execute({}, context)

    # The final result should be from the fallback
    assert result == "fallback_success"

    # The slow primitive should have been called once
    assert slow_primitive.call_count == 1

    # The fallback primitive should have been called once
    assert fallback_primitive.call_count == 1
