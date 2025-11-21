import asyncio

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.recovery.timeout import TimeoutPrimitive
from tta_dev_primitives.testing import MockPrimitive


async def slow_primitive_task(delay, result):
    await asyncio.sleep(delay)
    return result


@pytest.mark.asyncio
async def test_full_recovery_chain():
    """
    Tests a full chain of recovery primitives: Retry -> Timeout -> Fallback -> Cache.
    """
    # A primitive that is slow and fails once
    flaky_slow_primitive = MockPrimitive(name="flaky_slow")
    side_effects = [ValueError("fail"), "success"]

    async def side_effect_handler(*args, **kwargs):
        effect = side_effects.pop(0)
        await asyncio.sleep(0.05)
        if isinstance(effect, Exception):
            raise effect
        return effect

    flaky_slow_primitive.side_effect = side_effect_handler

    # A fast fallback primitive
    fast_fallback = MockPrimitive(name="fast_fallback", return_value="fallback_success")

    # A cache to wrap the whole workflow
    cache_key_fn = lambda data, ctx: "test_key"

    # Build the workflow
    retry_primitive = RetryPrimitive(
        flaky_slow_primitive, strategy=RetryStrategy(max_retries=1, backoff_base=0.01)
    )
    timeout_primitive = TimeoutPrimitive(
        retry_primitive, timeout_seconds=0.1, fallback=fast_fallback
    )
    cached_workflow = CachePrimitive(timeout_primitive, cache_key_fn, ttl_seconds=10)

    context = WorkflowContext()

    # First run: The flaky primitive will fail, retry, then succeed. The result will be cached.
    result1 = await cached_workflow.execute({}, context)
    assert result1 == "success"
    assert flaky_slow_primitive.call_count == 2
    assert fast_fallback.call_count == 0

    # Second run: The result should be served from the cache
    result2 = await cached_workflow.execute({}, context)
    assert result2 == "success"
    assert flaky_slow_primitive.call_count == 2  # No change
    assert fast_fallback.call_count == 0  # No change
