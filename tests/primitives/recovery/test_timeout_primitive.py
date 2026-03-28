"""Unit tests for TimeoutPrimitive — AAA pattern throughout."""

import asyncio

import pytest

from ttadev.primitives import LambdaPrimitive, TimeoutPrimitive, WorkflowContext
from ttadev.primitives.recovery.timeout import TimeoutError as TTATimeoutError


async def test_timeout_returns_result_when_operation_completes_in_time():
    # Arrange
    async def fast_op(inp, ctx):
        return "done"

    primitive = TimeoutPrimitive(LambdaPrimitive(fast_op), timeout_seconds=5.0)
    ctx = WorkflowContext()

    # Act
    result = await primitive.execute("input", ctx)

    # Assert
    assert result == "done"


async def test_timeout_raises_when_operation_exceeds_limit_and_no_fallback():
    # Arrange
    async def slow_op(inp, ctx):
        await asyncio.sleep(10.0)
        return "never"

    primitive = TimeoutPrimitive(
        LambdaPrimitive(slow_op), timeout_seconds=0.01, track_timeouts=False
    )
    ctx = WorkflowContext()

    # Act / Assert
    with pytest.raises(TTATimeoutError, match=r"0\.01s timeout"):
        await primitive.execute("input", ctx)


async def test_timeout_uses_fallback_when_operation_times_out():
    # Arrange — covers lines 133-137 (fallback execution path)
    async def slow_op(inp, ctx):
        await asyncio.sleep(10.0)
        return "never"

    async def fallback_op(inp, ctx):
        return "fallback-result"

    primitive = TimeoutPrimitive(
        LambdaPrimitive(slow_op),
        timeout_seconds=0.01,
        fallback=LambdaPrimitive(fallback_op),
    )
    ctx = WorkflowContext()

    # Act
    result = await primitive.execute("input", ctx)

    # Assert
    assert result == "fallback-result"


async def test_timeout_tracks_timeout_count_in_context():
    # Arrange
    async def slow_op(inp, ctx):
        await asyncio.sleep(10.0)
        return "never"

    primitive = TimeoutPrimitive(
        LambdaPrimitive(slow_op),
        timeout_seconds=0.01,
        track_timeouts=True,
    )
    ctx = WorkflowContext()

    # Act / Assert
    with pytest.raises(TTATimeoutError):
        await primitive.execute("input", ctx)

    assert ctx.state["timeout_count"] == 1
    assert len(ctx.state["timeout_history"]) == 1


async def test_timeout_increments_existing_timeout_count_in_context():
    # Arrange — covers the branch where timeout_count already exists in state
    async def slow_op(inp, ctx):
        await asyncio.sleep(10.0)
        return "never"

    primitive = TimeoutPrimitive(
        LambdaPrimitive(slow_op),
        timeout_seconds=0.01,
        track_timeouts=True,
    )
    ctx = WorkflowContext()
    ctx.state["timeout_count"] = 5
    ctx.state["timeout_history"] = ["existing"]

    # Act / Assert
    with pytest.raises(TTATimeoutError):
        await primitive.execute("input", ctx)

    assert ctx.state["timeout_count"] == 6
    assert len(ctx.state["timeout_history"]) == 2


async def test_timeout_does_not_track_when_track_timeouts_is_false():
    # Arrange — covers the track_timeouts=False branch
    async def slow_op(inp, ctx):
        await asyncio.sleep(10.0)
        return "never"

    primitive = TimeoutPrimitive(
        LambdaPrimitive(slow_op),
        timeout_seconds=0.01,
        track_timeouts=False,
    )
    ctx = WorkflowContext()

    # Act / Assert
    with pytest.raises(TTATimeoutError):
        await primitive.execute("input", ctx)

    assert "timeout_count" not in ctx.state
    assert "timeout_history" not in ctx.state
