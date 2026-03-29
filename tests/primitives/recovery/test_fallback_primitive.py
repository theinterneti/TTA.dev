"""Unit tests for FallbackPrimitive — AAA pattern throughout.

Coverage targets:
- FallbackStrategy.__init__ (line 31)
- FallbackPrimitive primary-succeeds with tracer (lines 114-171)
- FallbackPrimitive primary-succeeds without tracer (line 131)
- FallbackPrimitive primary-fails, fallback-succeeds with tracer (lines 173-274)
- FallbackPrimitive primary-fails, fallback-fails with tracer (lines 227-234, 276-324)
- FallbackPrimitive primary-fails, fallback-fails without tracer (lines 232-234, 276-324)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ttadev.primitives import FallbackPrimitive, LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery.fallback import FallbackStrategy

# ---------------------------------------------------------------------------
# FallbackStrategy (covers line 31)
# ---------------------------------------------------------------------------


def test_fallback_strategy_stores_primitive():
    # Arrange
    async def noop(inp, ctx):
        return inp

    inner = LambdaPrimitive(noop)

    # Act
    strategy = FallbackStrategy(inner)

    # Assert
    assert strategy.fallback_primitive is inner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx() -> WorkflowContext:
    return WorkflowContext()


def _ok(value: str):
    async def _fn(inp, ctx):
        return value

    return LambdaPrimitive(_fn)


def _fail(exc: Exception):
    async def _fn(inp, ctx):
        raise exc

    return LambdaPrimitive(_fn)


# ---------------------------------------------------------------------------
# With tracing available (TRACING_AVAILABLE=True, default in test env)
# ---------------------------------------------------------------------------


async def test_primary_succeeds_returns_primary_result_with_tracer():
    # Arrange
    primitive = FallbackPrimitive(_ok("primary-ok"), _ok("fallback-ok"))
    ctx = _make_ctx()

    # Act
    result = await primitive.execute("input", ctx)

    # Assert
    assert result == "primary-ok"


async def test_fallback_invoked_when_primary_fails_with_tracer():
    # Arrange
    primitive = FallbackPrimitive(_fail(RuntimeError("primary down")), _ok("fallback-ok"))
    ctx = _make_ctx()

    # Act
    result = await primitive.execute("input", ctx)

    # Assert
    assert result == "fallback-ok"


async def test_raises_primary_error_when_both_fail_with_tracer():
    # Arrange
    primary_err = RuntimeError("primary failed")
    primitive = FallbackPrimitive(_fail(primary_err), _fail(RuntimeError("fallback also failed")))
    ctx = _make_ctx()

    # Act / Assert — original primary error is re-raised
    with pytest.raises(RuntimeError, match="primary failed"):
        await primitive.execute("input", ctx)


async def test_fallback_not_called_when_primary_succeeds_with_tracer():
    # Arrange
    fallback_calls: list[str] = []

    async def tracking_fallback(inp, ctx):
        fallback_calls.append("called")
        return "fallback-ok"

    primitive = FallbackPrimitive(_ok("primary-ok"), LambdaPrimitive(tracking_fallback))
    ctx = _make_ctx()

    # Act
    await primitive.execute("input", ctx)

    # Assert
    assert fallback_calls == []


# ---------------------------------------------------------------------------
# Without tracing (TRACING_AVAILABLE=False) — covers lines 131, 234
# ---------------------------------------------------------------------------


async def test_primary_succeeds_returns_primary_result_without_tracer():
    # Arrange
    primitive = FallbackPrimitive(_ok("primary-no-trace"), _ok("fallback-ok"))
    ctx = _make_ctx()

    # Act — patch TRACING_AVAILABLE to False so the else-branch executes
    with patch("ttadev.primitives.recovery.fallback.TRACING_AVAILABLE", False):
        result = await primitive.execute("input", ctx)

    # Assert
    assert result == "primary-no-trace"


async def test_fallback_invoked_when_primary_fails_without_tracer():
    # Arrange
    primitive = FallbackPrimitive(_fail(RuntimeError("primary down")), _ok("fallback-no-trace"))
    ctx = _make_ctx()

    # Act
    with patch("ttadev.primitives.recovery.fallback.TRACING_AVAILABLE", False):
        result = await primitive.execute("input", ctx)

    # Assert
    assert result == "fallback-no-trace"


async def test_raises_primary_error_when_both_fail_without_tracer():
    # Arrange
    primary_err = RuntimeError("primary failed no trace")
    primitive = FallbackPrimitive(
        _fail(primary_err), _fail(RuntimeError("fallback failed no trace"))
    )
    ctx = _make_ctx()

    # Act / Assert
    with patch("ttadev.primitives.recovery.fallback.TRACING_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="primary failed no trace"):
            await primitive.execute("input", ctx)


# ---------------------------------------------------------------------------
# Context checkpoint recording
# ---------------------------------------------------------------------------


async def test_checkpoints_recorded_on_primary_success():
    # Arrange
    primitive = FallbackPrimitive(_ok("ok"), _ok("fb"))
    ctx = _make_ctx()

    # Act
    await primitive.execute("input", ctx)

    # Assert — all start/end checkpoints present
    checkpoint_names = [cp[0] for cp in ctx.checkpoints]
    assert "fallback.start" in checkpoint_names
    assert "fallback.primary.start" in checkpoint_names
    assert "fallback.primary.end" in checkpoint_names
    assert "fallback.end" in checkpoint_names


async def test_checkpoints_recorded_on_fallback_path():
    # Arrange
    primitive = FallbackPrimitive(_fail(RuntimeError("boom")), _ok("fb"))
    ctx = _make_ctx()

    # Act
    await primitive.execute("input", ctx)

    # Assert — fallback-specific checkpoints present
    checkpoint_names = [cp[0] for cp in ctx.checkpoints]
    assert "fallback.fallback.start" in checkpoint_names
    assert "fallback.fallback.end" in checkpoint_names
    assert "fallback.end" in checkpoint_names


async def test_checkpoints_recorded_on_both_fail():
    # Arrange
    primitive = FallbackPrimitive(_fail(RuntimeError("p")), _fail(RuntimeError("f")))
    ctx = _make_ctx()

    # Act / Assert
    with pytest.raises(RuntimeError):
        await primitive.execute("input", ctx)

    checkpoint_names = [cp[0] for cp in ctx.checkpoints]
    assert "fallback.fallback.end" in checkpoint_names
    assert "fallback.end" in checkpoint_names
