"""Unit tests for RetryPrimitive — AAA pattern throughout."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import ttadev.primitives.recovery.retry as retry_module
from ttadev.primitives import (
    LambdaPrimitive,
    RetryPrimitive,
    RetryStrategy,
    WorkflowContext,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_primitive(fn):
    """Wrap an async callable in a LambdaPrimitive."""
    return LambdaPrimitive(fn)


def _ctx():
    return WorkflowContext()


# ---------------------------------------------------------------------------
# RetryStrategy.calculate_delay
# ---------------------------------------------------------------------------


def test_calculate_delay_with_jitter():
    # Arrange
    strategy = RetryStrategy(backoff_base=2.0, max_backoff=60.0, jitter=True)

    # Act
    delay = strategy.calculate_delay(attempt=0)

    # Assert — with jitter, delay is in range [0.5*base^attempt, 1.5*base^attempt]
    assert 0.5 <= delay <= 1.5


def test_calculate_delay_without_jitter():
    # Arrange
    strategy = RetryStrategy(backoff_base=2.0, max_backoff=60.0, jitter=False)

    # Act
    delay = strategy.calculate_delay(attempt=3)

    # Assert — 2.0^3 = 8.0, no jitter
    assert delay == pytest.approx(8.0)


def test_calculate_delay_caps_at_max_backoff():
    # Arrange
    strategy = RetryStrategy(backoff_base=2.0, max_backoff=5.0, jitter=False)

    # Act — 2^10 = 1024, far above max_backoff
    delay = strategy.calculate_delay(attempt=10)

    # Assert — capped at max_backoff
    assert delay == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# RetryPrimitive.__init__
# ---------------------------------------------------------------------------


def test_default_strategy_is_used_when_none_provided():
    # Arrange
    async def noop(inp, ctx):
        return inp

    # Act
    primitive = RetryPrimitive(_make_primitive(noop))

    # Assert
    assert isinstance(primitive.strategy, RetryStrategy)
    assert primitive.strategy.max_retries == 3  # dataclass default


def test_explicit_strategy_is_stored():
    # Arrange
    async def noop(inp, ctx):
        return inp

    strategy = RetryStrategy(max_retries=7)

    # Act
    primitive = RetryPrimitive(_make_primitive(noop), strategy=strategy)

    # Assert
    assert primitive.strategy is strategy


# ---------------------------------------------------------------------------
# RetryPrimitive.execute — success paths
# ---------------------------------------------------------------------------


async def test_succeeds_on_first_attempt(monkeypatch):
    # Arrange
    calls = []

    async def operation(inp, ctx):
        calls.append(inp)
        return "ok"

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(operation), RetryStrategy(max_retries=3))
    ctx = _ctx()

    # Act
    result = await primitive.execute("input", ctx)

    # Assert
    assert result == "ok"
    assert len(calls) == 1


async def test_succeeds_on_nth_attempt(monkeypatch):
    # Arrange
    calls = []

    async def flaky(inp, ctx):
        calls.append(inp)
        if len(calls) < 3:
            raise ValueError("transient error")
        return "recovered"

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(flaky), RetryStrategy(max_retries=5))
    ctx = _ctx()

    # Act
    result = await primitive.execute("input", ctx)

    # Assert
    assert result == "recovered"
    assert len(calls) == 3


async def test_passes_context_to_wrapped_primitive(monkeypatch):
    # Arrange
    received_contexts = []

    async def capture_ctx(inp, ctx):
        received_contexts.append(ctx)
        return "ok"

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(capture_ctx), RetryStrategy(max_retries=1))
    ctx = _ctx()

    # Act
    await primitive.execute("input", ctx)

    # Assert
    assert len(received_contexts) == 1
    assert received_contexts[0] is ctx


async def test_passes_input_data_unchanged(monkeypatch):
    # Arrange
    received_inputs = []

    async def capture_input(inp, ctx):
        received_inputs.append(inp)
        return "done"

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(capture_input), RetryStrategy(max_retries=1))

    # Act
    await primitive.execute({"key": "value"}, _ctx())

    # Assert
    assert received_inputs[0] == {"key": "value"}


# ---------------------------------------------------------------------------
# RetryPrimitive.execute — failure / exhaustion paths
# ---------------------------------------------------------------------------


async def test_raises_after_max_retries_exceeded(monkeypatch):
    # Arrange
    async def always_fails(inp, ctx):
        raise ValueError("permanent error")

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(always_fails), RetryStrategy(max_retries=2))

    # Act / Assert
    with pytest.raises(ValueError, match="permanent error"):
        await primitive.execute("input", _ctx())


async def test_respects_max_retries_count(monkeypatch):
    # Arrange
    call_count = 0

    async def always_fails(inp, ctx):
        nonlocal call_count
        call_count += 1
        raise ValueError("always fails")

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(always_fails), RetryStrategy(max_retries=3))

    # Act
    with pytest.raises(ValueError):
        await primitive.execute("input", _ctx())

    # Assert — 1 initial attempt + 3 retries
    assert call_count == 4


async def test_zero_retries_fails_immediately(monkeypatch):
    # Arrange
    call_count = 0

    async def always_fails(inp, ctx):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("instant fail")

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(always_fails), RetryStrategy(max_retries=0))

    # Act / Assert
    with pytest.raises(RuntimeError, match="instant fail"):
        await primitive.execute("input", _ctx())

    assert call_count == 1


async def test_raises_original_exception_type(monkeypatch):
    # Arrange
    class CustomError(Exception):
        pass

    async def fails_with_custom(inp, ctx):
        raise CustomError("specific error")

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    primitive = RetryPrimitive(_make_primitive(fails_with_custom), RetryStrategy(max_retries=1))

    # Act / Assert
    with pytest.raises(CustomError):
        await primitive.execute("input", _ctx())


async def test_sleep_called_between_retries(monkeypatch):
    # Arrange
    mock_sleep = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", mock_sleep)

    async def always_fails(inp, ctx):
        raise ValueError("fail")

    primitive = RetryPrimitive(_make_primitive(always_fails), RetryStrategy(max_retries=2))

    # Act
    with pytest.raises(ValueError):
        await primitive.execute("input", _ctx())

    # Assert — sleep called once per retry gap (max_retries times)
    assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# Branch: TRACING_AVAILABLE = False (graceful degradation / else branch)
# ---------------------------------------------------------------------------


async def test_executes_without_tracer_when_tracing_unavailable(monkeypatch):
    # Arrange
    monkeypatch.setattr(retry_module, "TRACING_AVAILABLE", False)
    monkeypatch.setattr("asyncio.sleep", AsyncMock())

    calls = []

    async def operation(inp, ctx):
        calls.append(inp)
        return "no-trace"

    primitive = RetryPrimitive(_make_primitive(operation), RetryStrategy(max_retries=2))

    # Act
    result = await primitive.execute("input", _ctx())

    # Assert — runs through the else branch (no span)
    assert result == "no-trace"
    assert len(calls) == 1


async def test_retries_without_tracer_when_tracing_unavailable(monkeypatch):
    # Arrange — failure path also exercises the else branch
    monkeypatch.setattr(retry_module, "TRACING_AVAILABLE", False)
    monkeypatch.setattr("asyncio.sleep", AsyncMock())

    call_count = 0

    async def flaky(inp, ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("first fail")
        return "recovered"

    primitive = RetryPrimitive(_make_primitive(flaky), RetryStrategy(max_retries=3))

    # Act
    result = await primitive.execute("input", _ctx())

    # Assert
    assert result == "recovered"
    assert call_count == 2


# ---------------------------------------------------------------------------
# Defensive guard: RuntimeError when last_error is None after all attempts
# This is structurally unreachable via normal API; exercised by patching.
# ---------------------------------------------------------------------------


async def test_defensive_runtime_error_when_last_error_is_none(monkeypatch):
    # Arrange — patch the execute to simulate the impossible state by making
    # the for-loop do nothing (total_attempts = 0), so last_error stays None.
    # We achieve this by patching max_retries to -1 so total_attempts = 0.
    monkeypatch.setattr("asyncio.sleep", AsyncMock())

    async def noop(inp, ctx):
        return "should not run"

    primitive = RetryPrimitive(_make_primitive(noop), RetryStrategy(max_retries=-1))

    # Act / Assert — loop runs 0 times, last_error is None → RuntimeError
    with pytest.raises(RuntimeError, match="Retry failed without capturing an error"):
        await primitive.execute("input", _ctx())
