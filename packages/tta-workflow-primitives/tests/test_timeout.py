"""Tests for timeout primitive."""

import asyncio

import pytest

from tta_workflow_primitives.core.base import LambdaPrimitive, WorkflowContext
from tta_workflow_primitives.recovery.timeout import TimeoutError, TimeoutPrimitive
from tta_workflow_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_timeout_success() -> None:
    """Test successful execution within timeout."""
    fast = LambdaPrimitive(lambda data, ctx: {"result": "fast"})

    timeout_prim = TimeoutPrimitive(primitive=fast, timeout_seconds=1.0)

    result = await timeout_prim.execute({}, WorkflowContext())
    assert result == {"result": "fast"}


@pytest.mark.asyncio
async def test_timeout_exceeded() -> None:
    """Test timeout exceeded without fallback."""

    async def slow(data, ctx):
        await asyncio.sleep(2.0)
        return {"result": "slow"}

    slow_prim = LambdaPrimitive(slow)
    timeout_prim = TimeoutPrimitive(primitive=slow_prim, timeout_seconds=0.1)

    with pytest.raises(TimeoutError, match="exceeded 0.1s timeout"):
        await timeout_prim.execute({}, WorkflowContext())


@pytest.mark.asyncio
async def test_timeout_with_fallback() -> None:
    """Test fallback on timeout."""

    async def slow(data, ctx):
        await asyncio.sleep(2.0)
        return {"result": "slow"}

    slow_prim = LambdaPrimitive(slow)
    fallback = MockPrimitive("fallback", return_value={"result": "fallback"})

    timeout_prim = TimeoutPrimitive(primitive=slow_prim, timeout_seconds=0.1, fallback=fallback)

    result = await timeout_prim.execute({}, WorkflowContext())
    assert result == {"result": "fallback"}
    assert fallback.call_count == 1


@pytest.mark.asyncio
async def test_timeout_tracking() -> None:
    """Test timeout tracking in context."""

    async def slow(data, ctx):
        await asyncio.sleep(2.0)
        return {"result": "slow"}

    slow_prim = LambdaPrimitive(slow)
    fallback = MockPrimitive("fallback", return_value={"result": "fallback"})

    timeout_prim = TimeoutPrimitive(
        primitive=slow_prim, timeout_seconds=0.1, fallback=fallback, track_timeouts=True
    )

    context = WorkflowContext()
    await timeout_prim.execute({}, context)

    # Check tracking
    assert context.state["timeout_count"] == 1
    assert len(context.state["timeout_history"]) == 1
    assert context.state["timeout_history"][0]["timeout"] == 0.1


@pytest.mark.asyncio
async def test_timeout_multiple_calls() -> None:
    """Test multiple timeout scenarios."""

    async def sometimes_slow(data, ctx):
        delay = data.get("delay", 0)
        await asyncio.sleep(delay)
        return {"result": f"delayed_{delay}s"}

    slow_prim = LambdaPrimitive(sometimes_slow)
    fallback = MockPrimitive("fallback", return_value={"result": "fallback"})

    timeout_prim = TimeoutPrimitive(
        primitive=slow_prim, timeout_seconds=0.2, fallback=fallback, track_timeouts=True
    )

    context = WorkflowContext()

    # Fast call - no timeout
    result = await timeout_prim.execute({"delay": 0.05}, context)
    assert result == {"result": "delayed_0.05s"}
    assert "timeout_count" not in context.state

    # Slow call - timeout
    result = await timeout_prim.execute({"delay": 1.0}, context)
    assert result == {"result": "fallback"}
    assert context.state["timeout_count"] == 1

    # Another slow call
    result = await timeout_prim.execute({"delay": 1.0}, context)
    assert context.state["timeout_count"] == 2


@pytest.mark.asyncio
async def test_timeout_no_tracking() -> None:
    """Test timeout without tracking."""

    async def slow(data, ctx):
        await asyncio.sleep(2.0)
        return {"result": "slow"}

    slow_prim = LambdaPrimitive(slow)
    fallback = MockPrimitive("fallback", return_value={"result": "fallback"})

    timeout_prim = TimeoutPrimitive(
        primitive=slow_prim, timeout_seconds=0.1, fallback=fallback, track_timeouts=False
    )

    context = WorkflowContext()
    await timeout_prim.execute({}, context)

    # Should not track
    assert "timeout_count" not in context.state
    assert "timeout_history" not in context.state


@pytest.mark.asyncio
async def test_timeout_realistic_scenario() -> None:
    """Test realistic LLM call with timeout."""
    call_count = 0

    async def llm_call(data, ctx):
        nonlocal call_count
        call_count += 1
        # Simulate occasional slow response
        if call_count == 2:
            await asyncio.sleep(2.0)  # Slow call
        else:
            await asyncio.sleep(0.1)  # Normal call
        return {"result": f"response_{call_count}"}

    llm_prim = LambdaPrimitive(llm_call)
    cached_fallback = MockPrimitive("cache", return_value={"result": "cached"})

    timeout_prim = TimeoutPrimitive(
        primitive=llm_prim, timeout_seconds=0.5, fallback=cached_fallback
    )

    context = WorkflowContext()

    # First call succeeds
    result = await timeout_prim.execute({}, context)
    assert result == {"result": "response_1"}

    # Second call times out, uses fallback
    result = await timeout_prim.execute({}, context)
    assert result == {"result": "cached"}
    assert cached_fallback.call_count == 1

    # Third call succeeds
    result = await timeout_prim.execute({}, context)
    assert result == {"result": "response_3"}
