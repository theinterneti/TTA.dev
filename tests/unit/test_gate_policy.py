"""Unit tests for GatePolicy-driven ApprovalGate decisions (l0-approval-depth)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ttadev.workflows.gate import ApprovalGate, GateDecision, GatePolicy


def _make_step_result(confidence: float, quality_gates_passed: bool = True) -> MagicMock:
    """Build a minimal StepResult mock."""
    result = MagicMock()
    result.confidence = confidence
    result.quality_gates_passed = quality_gates_passed
    result.response = "mock response"
    sr = MagicMock()
    sr.result = result
    sr.step_index = 0
    sr.agent_name = "developer"
    return sr


# ---------------------------------------------------------------------------
# AC1 — confidence meets threshold → auto-approve, no prompt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_approve_when_confidence_meets_threshold() -> None:
    """AC1: step confidence=0.95 >= min_confidence=0.9 → CONTINUE, policy_name set."""
    gate = ApprovalGate(policy=GatePolicy(min_confidence=0.9))
    sr = _make_step_result(confidence=0.95, quality_gates_passed=True)

    decision, edited, policy_name = await gate.check(sr, total_steps=3, next_agent="qa")

    assert decision == GateDecision.CONTINUE
    assert edited is None
    assert policy_name == "auto:confidence≥0.9"


# ---------------------------------------------------------------------------
# AC2 — confidence below threshold → must prompt (mocked as non-TTY → CONTINUE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_halts_when_confidence_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC2: confidence=0.7 < min_confidence=0.9 → falls through to human prompt."""
    gate = ApprovalGate(policy=GatePolicy(min_confidence=0.9))
    sr = _make_step_result(confidence=0.7, quality_gates_passed=True)

    # Simulate non-TTY stdin so _prompt_user returns "" (→ CONTINUE by human)
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    decision, edited, policy_name = await gate.check(sr, total_steps=3, next_agent="qa")

    # Decision is still CONTINUE but policy_name is None (human path)
    assert decision == GateDecision.CONTINUE
    assert policy_name is None  # human path, not policy


# ---------------------------------------------------------------------------
# AC3 — quality gates failed blocks auto-approval even at high confidence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_gate_failure_blocks_auto_approve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC3: quality_gates_passed=False blocks auto-approve even when confidence=0.95."""
    gate = ApprovalGate(policy=GatePolicy(min_confidence=0.9, require_quality_gates=True))
    sr = _make_step_result(confidence=0.95, quality_gates_passed=False)

    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    decision, edited, policy_name = await gate.check(sr, total_steps=3, next_agent=None)

    assert decision == GateDecision.CONTINUE  # non-TTY fallback
    assert policy_name is None  # blocked auto-approve → human path


# ---------------------------------------------------------------------------
# AC3b — require_quality_gates=False lets auto-approve through despite failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_gate_failure_ignored_when_not_required() -> None:
    """require_quality_gates=False: auto-approve proceeds even if QG failed."""
    gate = ApprovalGate(policy=GatePolicy(min_confidence=0.9, require_quality_gates=False))
    sr = _make_step_result(confidence=0.95, quality_gates_passed=False)

    decision, edited, policy_name = await gate.check(sr, total_steps=2, next_agent=None)

    assert decision == GateDecision.CONTINUE
    assert policy_name == "auto:confidence≥0.9"


# ---------------------------------------------------------------------------
# AC4 — always_manual overrides even a very high confidence threshold
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_always_manual_overrides_high_confidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC4: always_manual=True forces human prompt regardless of confidence."""
    gate = ApprovalGate(policy=GatePolicy(min_confidence=0.9, always_manual=True))
    sr = _make_step_result(confidence=1.0, quality_gates_passed=True)

    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    decision, edited, policy_name = await gate.check(sr, total_steps=1, next_agent=None)

    assert decision == GateDecision.CONTINUE
    assert policy_name is None  # human path


# ---------------------------------------------------------------------------
# AC4b — per-call policy override supersedes instance policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_per_call_policy_overrides_instance_policy() -> None:
    """Per-call policy=GatePolicy(always_manual=True) beats instance min_confidence=0.9."""
    gate = ApprovalGate(policy=GatePolicy(min_confidence=0.9))
    sr = _make_step_result(confidence=1.0, quality_gates_passed=True)

    # per-call override: always_manual
    import sys

    import pytest as _pytest

    with _pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys.stdin, "isatty", lambda: False)
        decision, edited, policy_name = await gate.check(
            sr,
            total_steps=1,
            next_agent=None,
            policy=GatePolicy(always_manual=True),
        )

    assert policy_name is None


# ---------------------------------------------------------------------------
# AC7 — auto_approve=True backward compat always auto-approves
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_approve_true_always_approves() -> None:
    """AC7: auto_approve=True maps to always-auto policy (backward compat)."""
    gate = ApprovalGate(auto_approve=True)
    sr = _make_step_result(confidence=0.0, quality_gates_passed=False)

    decision, edited, policy_name = await gate.check(sr, total_steps=1, next_agent=None)

    assert decision == GateDecision.CONTINUE
    assert policy_name is not None  # auto path


# ---------------------------------------------------------------------------
# Baseline — min_confidence=0.0 (default) never auto-approves
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_default_policy_never_auto_approves(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default GatePolicy (min_confidence=0.0) always falls through to human prompt."""
    gate = ApprovalGate()
    sr = _make_step_result(confidence=1.0, quality_gates_passed=True)

    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    decision, edited, policy_name = await gate.check(sr, total_steps=1, next_agent=None)

    assert decision == GateDecision.CONTINUE
    assert policy_name is None
