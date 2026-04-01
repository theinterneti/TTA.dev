"""Unit tests for SagaPrimitive and CompensationPrimitive (Saga/compensation pattern).

Tests cover:
- Successful forward execution (compensation skipped)
- Forward failure triggers compensation
- Both forward AND compensation fail (critical failure, original exception re-raised)
- CompensationStrategy wrapper
- CompensationPrimitive alias behaviour
- Metrics, logging, and span integration surface
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.recovery.compensation import (
    CompensationPrimitive,
    CompensationStrategy,
    SagaPrimitive,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(wid: str = "test-saga") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


def _mock_primitive(return_value: object = "ok", raises: Exception | None = None) -> MagicMock:
    """Build a mock WorkflowPrimitive whose execute is an AsyncMock."""
    prim = MagicMock()
    if raises is not None:
        prim.execute = AsyncMock(side_effect=raises)
    else:
        prim.execute = AsyncMock(return_value=return_value)
    return prim


def _make_saga(
    forward_return: object = "forward_result",
    forward_raises: Exception | None = None,
    comp_return: object = "comp_result",
    comp_raises: Exception | None = None,
) -> tuple[SagaPrimitive, MagicMock, MagicMock]:
    forward = _mock_primitive(return_value=forward_return, raises=forward_raises)
    compensation = _mock_primitive(return_value=comp_return, raises=comp_raises)
    saga = SagaPrimitive(forward=forward, compensation=compensation)
    return saga, forward, compensation


# ---------------------------------------------------------------------------
# CompensationStrategy
# ---------------------------------------------------------------------------


class TestCompensationStrategy:
    def test_stores_primitive(self) -> None:
        prim = MagicMock()
        strategy = CompensationStrategy(compensation_primitive=prim)
        assert strategy.compensation_primitive is prim

    def test_stores_any_primitive_type(self) -> None:
        for val in [MagicMock(), object(), None]:
            strategy = CompensationStrategy(compensation_primitive=val)
            assert strategy.compensation_primitive is val


# ---------------------------------------------------------------------------
# SagaPrimitive — construction
# ---------------------------------------------------------------------------


class TestSagaPrimitiveInit:
    def test_stores_forward_and_compensation(self) -> None:
        fwd = MagicMock()
        comp = MagicMock()
        saga = SagaPrimitive(forward=fwd, compensation=comp)
        assert saga.forward is fwd
        assert saga.compensation is comp

    def test_is_workflow_primitive(self) -> None:
        from ttadev.primitives.core.base import WorkflowPrimitive

        saga, _, _ = _make_saga()
        assert isinstance(saga, WorkflowPrimitive)


# ---------------------------------------------------------------------------
# SagaPrimitive — happy path
# ---------------------------------------------------------------------------


class TestSagaSuccessPath:
    @pytest.mark.asyncio
    async def test_returns_forward_result_on_success(self) -> None:
        saga, forward, compensation = _make_saga(forward_return={"status": "done"})
        result = await saga.execute({"input": "data"}, _make_context())
        assert result == {"status": "done"}

    @pytest.mark.asyncio
    async def test_forward_called_with_input_and_context(self) -> None:
        ctx = _make_context("ctx-id")
        saga, forward, _ = _make_saga()
        await saga.execute("my-input", ctx)
        forward.execute.assert_awaited_once_with("my-input", ctx)

    @pytest.mark.asyncio
    async def test_compensation_not_called_on_success(self) -> None:
        saga, _, compensation = _make_saga()
        await saga.execute({}, _make_context())
        compensation.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_accepts_any_input_type(self) -> None:
        for inp in [None, 42, "string", [1, 2], {"key": "value"}]:
            saga, _, _ = _make_saga(forward_return=inp)
            result = await saga.execute(inp, _make_context())
            assert result == inp


# ---------------------------------------------------------------------------
# SagaPrimitive — failure path (forward fails, compensation succeeds)
# ---------------------------------------------------------------------------


class TestSagaForwardFailurePath:
    @pytest.mark.asyncio
    async def test_re_raises_original_exception(self) -> None:
        err = ValueError("forward failed")
        saga, _, _ = _make_saga(forward_raises=err)
        with pytest.raises(ValueError, match="forward failed"):
            await saga.execute({}, _make_context())

    @pytest.mark.asyncio
    async def test_compensation_called_on_forward_failure(self) -> None:
        saga, _, compensation = _make_saga(forward_raises=RuntimeError("boom"))
        with pytest.raises(RuntimeError):
            await saga.execute("data", _make_context())
        compensation.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compensation_receives_original_input(self) -> None:
        ctx = _make_context()
        saga, _, compensation = _make_saga(forward_raises=ValueError("fail"))
        with pytest.raises(ValueError):
            await saga.execute("original-input", ctx)
        compensation.execute.assert_awaited_once_with("original-input", ctx)

    @pytest.mark.asyncio
    async def test_different_exception_types_re_raised(self) -> None:
        for exc_class in [RuntimeError, TypeError, KeyError, OSError]:
            saga, _, _ = _make_saga(forward_raises=exc_class("msg"))
            with pytest.raises(exc_class):
                await saga.execute({}, _make_context())

    @pytest.mark.asyncio
    async def test_original_not_forward_result_returned(self) -> None:
        """Ensure we don't accidentally return compensation result."""
        saga, _, compensation = _make_saga(
            forward_raises=ValueError("fail"),
            comp_return="compensation_side_effect",
        )
        with pytest.raises(ValueError):
            await saga.execute({}, _make_context())


# ---------------------------------------------------------------------------
# SagaPrimitive — critical failure (both forward AND compensation fail)
# ---------------------------------------------------------------------------


class TestSagaCriticalFailurePath:
    @pytest.mark.asyncio
    async def test_re_raises_original_exception_when_both_fail(self) -> None:
        fwd_err = ValueError("original failure")
        comp_err = RuntimeError("compensation also failed")
        saga, _, _ = _make_saga(forward_raises=fwd_err, comp_raises=comp_err)
        with pytest.raises(ValueError, match="original failure"):
            await saga.execute({}, _make_context())

    @pytest.mark.asyncio
    async def test_compensation_exception_does_not_propagate(self) -> None:
        """Compensation error is swallowed — original error is what propagates."""
        saga, _, _ = _make_saga(
            forward_raises=TypeError("type error"),
            comp_raises=MemoryError("memory error"),
        )
        with pytest.raises(TypeError):
            await saga.execute({}, _make_context())

    @pytest.mark.asyncio
    async def test_compensation_still_attempted_when_it_will_fail(self) -> None:
        saga, _, compensation = _make_saga(
            forward_raises=ValueError("fwd"),
            comp_raises=RuntimeError("comp"),
        )
        with pytest.raises(ValueError):
            await saga.execute({}, _make_context())
        compensation.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# SagaPrimitive — with tracing disabled
# ---------------------------------------------------------------------------


class TestSagaWithTracingDisabled:
    @pytest.mark.asyncio
    async def test_executes_without_tracing(self) -> None:
        with patch("ttadev.primitives.recovery.compensation.TRACING_AVAILABLE", False):
            saga, _, _ = _make_saga(forward_return="traced_result")
            result = await saga.execute({}, _make_context())
        assert result == "traced_result"

    @pytest.mark.asyncio
    async def test_failure_without_tracing(self) -> None:
        with patch("ttadev.primitives.recovery.compensation.TRACING_AVAILABLE", False):
            saga, _, _ = _make_saga(forward_raises=ValueError("no trace"))
            with pytest.raises(ValueError):
                await saga.execute({}, _make_context())


# ---------------------------------------------------------------------------
# SagaPrimitive — metrics integration surface (not crashing)
# ---------------------------------------------------------------------------


class TestSagaMetricsIntegration:
    @pytest.mark.asyncio
    async def test_success_records_metrics(self) -> None:
        mock_collector = MagicMock()
        mock_collector.record_execution = MagicMock()
        with patch(
            "ttadev.primitives.recovery.compensation.get_enhanced_metrics_collector",
            return_value=mock_collector,
        ):
            saga, _, _ = _make_saga(forward_return="result")
            await saga.execute({}, _make_context())
        mock_collector.record_execution.assert_called()

    @pytest.mark.asyncio
    async def test_failure_records_metrics(self) -> None:
        mock_collector = MagicMock()
        mock_collector.record_execution = MagicMock()
        with patch(
            "ttadev.primitives.recovery.compensation.get_enhanced_metrics_collector",
            return_value=mock_collector,
        ):
            saga, _, _ = _make_saga(forward_raises=ValueError("fail"))
            with pytest.raises(ValueError):
                await saga.execute({}, _make_context())
        mock_collector.record_execution.assert_called()


# ---------------------------------------------------------------------------
# CompensationPrimitive — alias
# ---------------------------------------------------------------------------


class TestCompensationPrimitiveAlias:
    def test_is_subclass_of_saga(self) -> None:
        assert issubclass(CompensationPrimitive, SagaPrimitive)

    def test_instantiates_like_saga(self) -> None:
        fwd = MagicMock()
        comp = MagicMock()
        cp = CompensationPrimitive(forward=fwd, compensation=comp)
        assert cp.forward is fwd
        assert cp.compensation is comp

    @pytest.mark.asyncio
    async def test_executes_forward_on_success(self) -> None:
        fwd = _mock_primitive(return_value="alias_ok")
        comp = _mock_primitive()
        cp = CompensationPrimitive(forward=fwd, compensation=comp)
        result = await cp.execute({}, _make_context())
        assert result == "alias_ok"

    @pytest.mark.asyncio
    async def test_triggers_compensation_on_failure(self) -> None:
        fwd = _mock_primitive(raises=RuntimeError("alias fail"))
        comp = _mock_primitive()
        cp = CompensationPrimitive(forward=fwd, compensation=comp)
        with pytest.raises(RuntimeError):
            await cp.execute({}, _make_context())
        comp.execute.assert_awaited_once()
