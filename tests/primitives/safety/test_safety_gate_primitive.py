"""Tests for SafetyGatePrimitive — severity routing and CRITICAL escalation."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.safety import (
    SafetyGateEscalatedError,
    SafetyGatePrimitive,
    SeverityLevel,
)
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(workflow_id: str = "wf-test") -> WorkflowContext:
    return WorkflowContext(workflow_id=workflow_id)


def _scorer(level: SeverityLevel):
    """Return an async scorer that always returns *level*."""

    async def scorer(input_data: Any, ctx: WorkflowContext) -> SeverityLevel:
        return level

    return scorer


def _raising_scorer(exc: Exception):
    """Return an async scorer that always raises *exc*."""

    async def scorer(input_data: Any, ctx: WorkflowContext) -> SeverityLevel:
        raise exc

    return scorer


# ---------------------------------------------------------------------------
# SeverityLevel enum
# ---------------------------------------------------------------------------


class TestSeverityLevel:
    def test_ordering(self):
        assert SeverityLevel.NONE < SeverityLevel.LOW < SeverityLevel.MEDIUM
        assert SeverityLevel.MEDIUM < SeverityLevel.HIGH < SeverityLevel.CRITICAL

    def test_values(self):
        assert SeverityLevel.NONE == 0
        assert SeverityLevel.CRITICAL == 4


# ---------------------------------------------------------------------------
# Pass-through behaviour (NONE, no handler)
# ---------------------------------------------------------------------------


class TestPassThrough:
    @pytest.mark.asyncio
    async def test_none_severity_returns_input_unchanged(self):
        gate = SafetyGatePrimitive(scorer=_scorer(SeverityLevel.NONE))
        result = await gate.execute("hello", _ctx())
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_low_without_handler_returns_input_unchanged(self):
        gate = SafetyGatePrimitive(scorer=_scorer(SeverityLevel.LOW))
        result = await gate.execute({"key": "val"}, _ctx())
        assert result == {"key": "val"}

    @pytest.mark.asyncio
    async def test_high_without_handler_returns_input_unchanged(self):
        gate = SafetyGatePrimitive(scorer=_scorer(SeverityLevel.HIGH))
        result = await gate.execute(42, _ctx())
        assert result == 42

    @pytest.mark.asyncio
    async def test_critical_without_block_returns_input_when_no_handler(self):
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            block_on_critical=False,
        )
        result = await gate.execute("safe", _ctx())
        assert result == "safe"


# ---------------------------------------------------------------------------
# Handler routing
# ---------------------------------------------------------------------------


class TestHandlerRouting:
    @pytest.mark.asyncio
    async def test_low_handler_called_with_correct_input(self):
        handler = MockPrimitive("low-handler", return_value="low-response")
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.LOW),
            handlers={SeverityLevel.LOW: handler},
        )
        result = await gate.execute("input", _ctx())
        assert result == "low-response"
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_medium_handler_receives_original_input(self):
        captured: list[Any] = []

        async def capture(data: Any, ctx: WorkflowContext) -> Any:
            captured.append(data)
            return "medium-out"

        handler = MockPrimitive("medium-handler", side_effect=capture)
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.MEDIUM),
            handlers={SeverityLevel.MEDIUM: handler},
        )
        await gate.execute("original", _ctx())
        assert captured == ["original"]

    @pytest.mark.asyncio
    async def test_only_matching_handler_is_called(self):
        low_handler = MockPrimitive("low", return_value="from-low")
        high_handler = MockPrimitive("high", return_value="from-high")
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.LOW),
            handlers={
                SeverityLevel.LOW: low_handler,
                SeverityLevel.HIGH: high_handler,
            },
        )
        result = await gate.execute("x", _ctx())
        assert result == "from-low"
        assert low_handler.call_count == 1
        assert high_handler.call_count == 0

    @pytest.mark.asyncio
    async def test_unregistered_severity_skips_all_handlers(self):
        high_handler = MockPrimitive("high", return_value="high-out")
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.LOW),  # scorer returns LOW, no LOW handler
            handlers={SeverityLevel.HIGH: high_handler},
        )
        result = await gate.execute("pass", _ctx())
        assert result == "pass"
        assert high_handler.call_count == 0


# ---------------------------------------------------------------------------
# CRITICAL + block_on_critical
# ---------------------------------------------------------------------------


class TestCriticalBlocking:
    @pytest.mark.asyncio
    async def test_critical_with_block_raises_escalated_error(self):
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            block_on_critical=True,
        )
        with pytest.raises(SafetyGateEscalatedError) as exc_info:
            await gate.execute("input", _ctx("wf-123"))

        err = exc_info.value
        assert err.severity == SeverityLevel.CRITICAL
        assert err.task_id == "wf-123"

    @pytest.mark.asyncio
    async def test_critical_handler_called_before_raise(self):
        handler = MockPrimitive("critical-handler", return_value="formatted-escalation")
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            handlers={SeverityLevel.CRITICAL: handler},
            block_on_critical=True,
        )
        with pytest.raises(SafetyGateEscalatedError):
            await gate.execute("x", _ctx())

        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_critical_no_block_returns_handler_result(self):
        handler = MockPrimitive("critical-handler", return_value="escalation-msg")
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            handlers={SeverityLevel.CRITICAL: handler},
            block_on_critical=False,
        )
        result = await gate.execute("x", _ctx())
        assert result == "escalation-msg"
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_lower_severities_never_raise(self):
        for level in (
            SeverityLevel.NONE,
            SeverityLevel.LOW,
            SeverityLevel.MEDIUM,
            SeverityLevel.HIGH,
        ):
            gate = SafetyGatePrimitive(scorer=_scorer(level), block_on_critical=True)
            result = await gate.execute("input", _ctx())
            assert result == "input"


# ---------------------------------------------------------------------------
# SafetyGateEscalatedError attributes
# ---------------------------------------------------------------------------


class TestEscalatedError:
    def test_message_contains_severity_name(self):
        err = SafetyGateEscalatedError(severity=SeverityLevel.CRITICAL)
        assert "CRITICAL" in str(err)
        assert err.task_id is None

    def test_message_contains_task_id_when_provided(self):
        err = SafetyGateEscalatedError(severity=SeverityLevel.CRITICAL, task_id="t-42")
        assert "t-42" in str(err)
        assert err.task_id == "t-42"

    def test_is_exception_subclass(self):
        assert issubclass(SafetyGateEscalatedError, Exception)


# ---------------------------------------------------------------------------
# L0 control-plane integration
# ---------------------------------------------------------------------------


class TestControlPlaneIntegration:
    @pytest.mark.asyncio
    async def test_service_record_called_on_critical(self):
        service = MagicMock()
        service.record_workflow_gate_outcome = MagicMock()

        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            block_on_critical=True,
            service=service,
        )

        with pytest.raises(SafetyGateEscalatedError):
            await gate.execute("data", _ctx("wf-abc"))

        service.record_workflow_gate_outcome.assert_called_once()
        call_kwargs = service.record_workflow_gate_outcome.call_args
        assert call_kwargs.args[0] == "wf-abc"

    @pytest.mark.asyncio
    async def test_service_failure_does_not_suppress_escalation(self):
        """L0 write errors must never mask the SafetyGateEscalatedError."""
        service = MagicMock()
        service.record_workflow_gate_outcome.side_effect = RuntimeError("db down")

        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            block_on_critical=True,
            service=service,
        )

        with pytest.raises(SafetyGateEscalatedError):
            await gate.execute("x", _ctx())

    @pytest.mark.asyncio
    async def test_no_service_call_on_non_critical(self):
        service = MagicMock()
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.HIGH),
            block_on_critical=True,
            service=service,
        )
        result = await gate.execute("y", _ctx())
        assert result == "y"
        service.record_workflow_gate_outcome.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_service_does_not_raise_on_critical(self):
        """Absence of service is fine — escalation error still raised."""
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            block_on_critical=True,
            service=None,
        )
        with pytest.raises(SafetyGateEscalatedError):
            await gate.execute("x", _ctx())


# ---------------------------------------------------------------------------
# Scorer exceptions propagate
# ---------------------------------------------------------------------------


class TestScorerExceptions:
    @pytest.mark.asyncio
    async def test_scorer_exception_propagates(self):
        gate = SafetyGatePrimitive(scorer=_raising_scorer(ValueError("bad input")))
        with pytest.raises(ValueError, match="bad input"):
            await gate.execute("x", _ctx())

    @pytest.mark.asyncio
    async def test_handler_exception_propagates(self):
        async def bad_handler(data: Any, ctx: WorkflowContext) -> Any:
            raise RuntimeError("handler boom")

        handler = MockPrimitive("bad", side_effect=bad_handler)
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.LOW),
            handlers={SeverityLevel.LOW: handler},
        )
        with pytest.raises(RuntimeError, match="handler boom"):
            await gate.execute("x", _ctx())


# ---------------------------------------------------------------------------
# Composability with >> operator
# ---------------------------------------------------------------------------


class TestComposability:
    @pytest.mark.asyncio
    async def test_pipeline_passes_through_on_safe_input(self):
        downstream = MockPrimitive("downstream", return_value="final")
        gate = SafetyGatePrimitive(scorer=_scorer(SeverityLevel.NONE))

        pipeline = gate >> downstream
        result = await pipeline.execute("input", _ctx())
        assert result == "final"
        assert downstream.call_count == 1

    @pytest.mark.asyncio
    async def test_pipeline_halts_on_critical(self):
        downstream = MockPrimitive("downstream", return_value="should-not-reach")
        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.CRITICAL),
            block_on_critical=True,
        )
        pipeline = gate >> downstream

        with pytest.raises(SafetyGateEscalatedError):
            await pipeline.execute("input", _ctx())

        assert downstream.call_count == 0

    @pytest.mark.asyncio
    async def test_handler_result_forwarded_to_downstream(self):
        """Handler transforms input; downstream receives the transformed value."""
        transform = MockPrimitive("transform", return_value="transformed")
        downstream = MockPrimitive("downstream", return_value="done")

        gate = SafetyGatePrimitive(
            scorer=_scorer(SeverityLevel.LOW),
            handlers={SeverityLevel.LOW: transform},
        )
        pipeline = gate >> downstream

        result = await pipeline.execute("raw", _ctx())
        assert result == "done"
        assert transform.call_count == 1
        assert downstream.calls[0][0] == "transformed"
