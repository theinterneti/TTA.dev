"""Unit tests for SafetyGatePrimitive multi-level ThreatLevel detection (issue-252).

Tests cover:
- ThreatLevel enum values (MINIMAL=1 … IMMINENT=5)
- detect_level default implementation (keyword match → IMMINENT, else MINIMAL)
- detect_level override for custom gradient scoring
- Threshold filtering: gate only fires when detect_level >= threshold
- IMMINENT calls control_plane escalation (mocked)
- SafetyViolationError carries correct metadata
- Existing SeverityLevel / SafetyGateEscalatedError path is unbroken
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.safety import (
    SafetyGateEscalatedError,
    SafetyGatePrimitive,
    SafetyViolationError,
    SeverityLevel,
    ThreatLevel,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _ctx(wid: str = "test-workflow") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


async def _safe_scorer(input_data: object, ctx: WorkflowContext) -> SeverityLevel:
    """Always returns NONE — keeps Track 1 out of the way for Track 2 tests."""
    return SeverityLevel.NONE


async def _critical_scorer(input_data: object, ctx: WorkflowContext) -> SeverityLevel:
    """Always returns CRITICAL — for Track 1 regression tests."""
    return SeverityLevel.CRITICAL


def _make_gate(
    threshold: ThreatLevel = ThreatLevel.MODERATE,
    service: object | None = None,
    block_on_critical: bool = False,
) -> SafetyGatePrimitive:
    """Build a gate with NONE scorer so Track 2 tests are isolated."""
    return SafetyGatePrimitive(
        scorer=_safe_scorer,
        threshold=threshold,
        service=service,
        block_on_critical=block_on_critical,
    )


# ---------------------------------------------------------------------------
# ThreatLevel enum
# ---------------------------------------------------------------------------


class TestThreatLevelEnum:
    def test_values(self) -> None:
        assert ThreatLevel.MINIMAL == 1
        assert ThreatLevel.MILD == 2
        assert ThreatLevel.MODERATE == 3
        assert ThreatLevel.SEVERE == 4
        assert ThreatLevel.IMMINENT == 5

    def test_ordering(self) -> None:
        levels = [
            ThreatLevel.MINIMAL,
            ThreatLevel.MILD,
            ThreatLevel.MODERATE,
            ThreatLevel.SEVERE,
            ThreatLevel.IMMINENT,
        ]
        assert levels == sorted(levels)

    def test_all_five_members(self) -> None:
        assert len(ThreatLevel) == 5

    def test_names(self) -> None:
        names = {lvl.name for lvl in ThreatLevel}
        assert names == {"MINIMAL", "MILD", "MODERATE", "SEVERE", "IMMINENT"}

    def test_int_comparison(self) -> None:
        assert ThreatLevel.IMMINENT > ThreatLevel.SEVERE
        assert ThreatLevel.MINIMAL < ThreatLevel.MODERATE


# ---------------------------------------------------------------------------
# detect_level — default implementation
# ---------------------------------------------------------------------------


class TestDetectLevelDefault:
    def test_safe_text_returns_minimal(self) -> None:
        gate = _make_gate()
        assert gate.detect_level("The hero rescued the dragon.") == ThreatLevel.MINIMAL

    def test_unsafe_keyword_harm_returns_imminent(self) -> None:
        gate = _make_gate()
        assert gate.detect_level("I want to harm myself") == ThreatLevel.IMMINENT

    def test_unsafe_keyword_suicide_returns_imminent(self) -> None:
        gate = _make_gate()
        assert gate.detect_level("thinking about suicide") == ThreatLevel.IMMINENT

    def test_unsafe_keyword_kill_returns_imminent(self) -> None:
        gate = _make_gate()
        assert gate.detect_level("I will kill the monster") == ThreatLevel.IMMINENT

    def test_case_insensitive(self) -> None:
        gate = _make_gate()
        assert gate.detect_level("SUICIDE note") == ThreatLevel.IMMINENT

    def test_empty_string_is_minimal(self) -> None:
        gate = _make_gate()
        assert gate.detect_level("") == ThreatLevel.MINIMAL

    def test_check_false_for_safe_text(self) -> None:
        gate = _make_gate()
        assert gate._check("everything is fine") is False

    def test_check_true_for_unsafe_text(self) -> None:
        gate = _make_gate()
        assert gate._check("end it all") is True


# ---------------------------------------------------------------------------
# detect_level override
# ---------------------------------------------------------------------------


class TestDetectLevelOverride:
    def _make_gradient_gate(
        self, threshold: ThreatLevel = ThreatLevel.MODERATE
    ) -> SafetyGatePrimitive:
        """Gate with a custom detect_level that maps word count to ThreatLevel."""

        class GradientGate(SafetyGatePrimitive):
            def detect_level(self, text: str) -> ThreatLevel:
                word_count = len(text.split())
                if word_count <= 2:
                    return ThreatLevel.MINIMAL
                if word_count <= 4:
                    return ThreatLevel.MILD
                if word_count <= 6:
                    return ThreatLevel.MODERATE
                if word_count <= 8:
                    return ThreatLevel.SEVERE
                return ThreatLevel.IMMINENT

        return GradientGate(scorer=_safe_scorer, threshold=threshold)

    @pytest.mark.asyncio
    async def test_custom_detect_level_minimal_passes(self) -> None:
        gate = self._make_gradient_gate(threshold=ThreatLevel.MODERATE)
        # 2 words → MINIMAL < MODERATE → no error
        result = await gate.execute("hello world", _ctx())
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_custom_detect_level_mild_passes_when_threshold_moderate(self) -> None:
        gate = self._make_gradient_gate(threshold=ThreatLevel.MODERATE)
        # 4 words → MILD < MODERATE → no error
        result = await gate.execute("one two three four", _ctx())
        assert result == "one two three four"

    @pytest.mark.asyncio
    async def test_custom_detect_level_moderate_fires(self) -> None:
        gate = self._make_gradient_gate(threshold=ThreatLevel.MODERATE)
        # 6 words → MODERATE >= MODERATE → SafetyViolationError
        with pytest.raises(SafetyViolationError) as exc_info:
            await gate.execute("one two three four five six", _ctx())
        assert exc_info.value.threat_level == ThreatLevel.MODERATE

    @pytest.mark.asyncio
    async def test_custom_detect_level_imminent_fires(self) -> None:
        gate = self._make_gradient_gate(threshold=ThreatLevel.MODERATE)
        # 10 words → IMMINENT >= MODERATE → SafetyViolationError
        with pytest.raises(SafetyViolationError) as exc_info:
            await gate.execute("a b c d e f g h i j", _ctx())
        assert exc_info.value.threat_level == ThreatLevel.IMMINENT


# ---------------------------------------------------------------------------
# Threshold filtering
# ---------------------------------------------------------------------------


class TestThresholdFiltering:
    @pytest.mark.asyncio
    async def test_threshold_severe_mild_passes(self) -> None:
        """With threshold=SEVERE, MILD text passes without error."""
        gate = _make_gate(threshold=ThreatLevel.SEVERE)
        # Safe text → MINIMAL → no error
        result = await gate.execute("all is well", _ctx())
        assert result == "all is well"

    @pytest.mark.asyncio
    async def test_threshold_severe_moderate_passes(self) -> None:
        """MODERATE < SEVERE so no violation raised."""

        class ModerateGate(SafetyGatePrimitive):
            def detect_level(self, text: str) -> ThreatLevel:
                return ThreatLevel.MODERATE

        gate = ModerateGate(scorer=_safe_scorer, threshold=ThreatLevel.SEVERE)
        result = await gate.execute("input", _ctx())
        assert result == "input"

    @pytest.mark.asyncio
    async def test_threshold_severe_severe_fires(self) -> None:
        """SEVERE >= SEVERE raises SafetyViolationError."""

        class SevereGate(SafetyGatePrimitive):
            def detect_level(self, text: str) -> ThreatLevel:
                return ThreatLevel.SEVERE

        gate = SevereGate(scorer=_safe_scorer, threshold=ThreatLevel.SEVERE)
        with pytest.raises(SafetyViolationError) as exc_info:
            await gate.execute("input", _ctx())
        assert exc_info.value.threat_level == ThreatLevel.SEVERE
        assert exc_info.value.threshold == ThreatLevel.SEVERE

    @pytest.mark.asyncio
    async def test_threshold_imminent_only_imminent_fires(self) -> None:
        """With threshold=IMMINENT, only IMMINENT triggers."""

        class SevereGate(SafetyGatePrimitive):
            def detect_level(self, text: str) -> ThreatLevel:
                return ThreatLevel.SEVERE

        gate = SevereGate(scorer=_safe_scorer, threshold=ThreatLevel.IMMINENT)
        # SEVERE < IMMINENT → no error
        result = await gate.execute("input", _ctx())
        assert result == "input"

    @pytest.mark.asyncio
    async def test_threshold_minimal_everything_fires(self) -> None:
        """With threshold=MINIMAL, even MINIMAL triggers."""
        gate = _make_gate(threshold=ThreatLevel.MINIMAL)
        # safe text → MINIMAL >= MINIMAL → fires
        with pytest.raises(SafetyViolationError) as exc_info:
            await gate.execute("totally fine text", _ctx())
        assert exc_info.value.threat_level == ThreatLevel.MINIMAL

    @pytest.mark.asyncio
    async def test_default_threshold_is_moderate(self) -> None:
        """Default threshold=MODERATE: MINIMAL/MILD pass, MODERATE fires."""
        gate = SafetyGatePrimitive(scorer=_safe_scorer)
        assert gate.threshold == ThreatLevel.MODERATE

    @pytest.mark.asyncio
    async def test_violation_error_carries_task_id(self) -> None:
        gate = _make_gate(threshold=ThreatLevel.MINIMAL)
        ctx = _ctx("session-abc")
        with pytest.raises(SafetyViolationError) as exc_info:
            await gate.execute("fine text", ctx)
        assert exc_info.value.task_id == "session-abc"


# ---------------------------------------------------------------------------
# IMMINENT fires control_plane
# ---------------------------------------------------------------------------


class TestImminentControlPlane:
    def _imminent_gate(self, service: object | None = None) -> SafetyGatePrimitive:
        """Gate whose detect_level always returns IMMINENT."""

        class AlwaysImminent(SafetyGatePrimitive):
            def detect_level(self, text: str) -> ThreatLevel:
                return ThreatLevel.IMMINENT

        return AlwaysImminent(
            scorer=_safe_scorer,
            threshold=ThreatLevel.MODERATE,
            service=service,
        )

    @pytest.mark.asyncio
    async def test_imminent_calls_record_workflow_gate_outcome(self) -> None:
        """When threat=IMMINENT and service is set, control-plane is called."""
        mock_service = MagicMock()
        gate = self._imminent_gate(service=mock_service)

        with patch(
            "ttadev.primitives.safety.safety_gate_primitive.WorkflowGateDecisionOutcome",
            create=True,
        ):
            # The real import path is guarded by try/except — patch the models module
            with patch("ttadev.control_plane.models.WorkflowGateDecisionOutcome") as mock_outcome:
                mock_outcome.ESCALATE_TO_HUMAN = "escalate_to_human"
                with pytest.raises(SafetyViolationError):
                    await gate.execute("some text", _ctx("wf-123"))

        mock_service.record_workflow_gate_outcome.assert_called_once()
        call_kwargs = mock_service.record_workflow_gate_outcome.call_args
        assert call_kwargs[0][0] == "wf-123"  # positional: workflow_id

    @pytest.mark.asyncio
    async def test_imminent_without_service_logs_warning(self) -> None:
        """IMMINENT without service logs a warning; no error from missing service."""
        gate = self._imminent_gate(service=None)

        with patch("ttadev.primitives.safety.safety_gate_primitive.logger") as mock_logger:
            with pytest.raises(SafetyViolationError):
                await gate.execute("text", _ctx())

        # Warning should be called (for missing service), not error
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args_list[0]
        assert (
            "imminent" in warning_call[0][0].lower()
            or "control_plane" in warning_call[0][0].lower()
        )

    @pytest.mark.asyncio
    async def test_imminent_service_exception_does_not_propagate(self) -> None:
        """If control-plane call raises, SafetyViolationError still fires (not the service exc)."""
        mock_service = MagicMock()
        mock_service.record_workflow_gate_outcome.side_effect = RuntimeError("db down")
        gate = self._imminent_gate(service=mock_service)

        # Should raise SafetyViolationError, not RuntimeError
        with pytest.raises(SafetyViolationError):
            await gate.execute("text", _ctx())

    @pytest.mark.asyncio
    async def test_severe_does_not_call_control_plane(self) -> None:
        """SEVERE threshold breach does NOT call control_plane (only IMMINENT does)."""
        mock_service = MagicMock()

        class AlwaysSevere(SafetyGatePrimitive):
            def detect_level(self, text: str) -> ThreatLevel:
                return ThreatLevel.SEVERE

        gate = AlwaysSevere(
            scorer=_safe_scorer,
            threshold=ThreatLevel.MODERATE,
            service=mock_service,
        )
        with pytest.raises(SafetyViolationError):
            await gate.execute("text", _ctx())

        mock_service.record_workflow_gate_outcome.assert_not_called()


# ---------------------------------------------------------------------------
# SafetyViolationError shape
# ---------------------------------------------------------------------------


class TestSafetyViolationError:
    def test_attributes(self) -> None:
        exc = SafetyViolationError(
            threat_level=ThreatLevel.IMMINENT,
            threshold=ThreatLevel.MODERATE,
            task_id="t-99",
        )
        assert exc.threat_level == ThreatLevel.IMMINENT
        assert exc.threshold == ThreatLevel.MODERATE
        assert exc.task_id == "t-99"

    def test_str_contains_names(self) -> None:
        exc = SafetyViolationError(
            threat_level=ThreatLevel.SEVERE,
            threshold=ThreatLevel.MODERATE,
        )
        msg = str(exc)
        assert "SEVERE" in msg
        assert "MODERATE" in msg

    def test_no_task_id(self) -> None:
        exc = SafetyViolationError(
            threat_level=ThreatLevel.MILD,
            threshold=ThreatLevel.MILD,
        )
        assert exc.task_id is None
        assert "task_id" not in str(exc)


# ---------------------------------------------------------------------------
# Regression: existing SeverityLevel track is unbroken
# ---------------------------------------------------------------------------


class TestSeverityLevelRegression:
    @pytest.mark.asyncio
    async def test_critical_still_raises_escalated_error(self) -> None:
        """SeverityLevel.CRITICAL + block_on_critical still raises SafetyGateEscalatedError."""
        gate = SafetyGatePrimitive(
            scorer=_critical_scorer,
            block_on_critical=True,
            threshold=ThreatLevel.IMMINENT,  # high threshold so Track 2 won't fire
        )
        with pytest.raises(SafetyGateEscalatedError) as exc_info:
            await gate.execute("safe text", _ctx("wf-crit"))
        assert exc_info.value.severity == SeverityLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_non_critical_passes_through(self) -> None:
        """SeverityLevel.NONE passes through with safe text."""
        gate = SafetyGatePrimitive(scorer=_safe_scorer, threshold=ThreatLevel.IMMINENT)
        result = await gate.execute("safe text", _ctx())
        assert result == "safe text"

    @pytest.mark.asyncio
    async def test_handler_called_for_severity_level(self) -> None:
        """Handler registered for SeverityLevel.NONE is called."""
        handler = MagicMock()
        handler.execute = AsyncMock(return_value="handled")

        gate = SafetyGatePrimitive(
            scorer=_safe_scorer,
            handlers={SeverityLevel.NONE: handler},
            threshold=ThreatLevel.IMMINENT,
        )
        result = await gate.execute("safe text", _ctx())
        assert result == "handled"
        handler.execute.assert_called_once()
