"""Unit tests for gate-aware L0 control-plane service behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import GateHistoryAction, GateStatus, GateType, TaskRecord
from ttadev.control_plane.service import ControlPlaneService as _CPService
from ttadev.observability import agent_identity


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str,
    agent_tool: str = "copilot",
) -> None:
    """Pin the process agent identity for control-plane tests."""
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


def test_task_record_defaults_missing_gates_to_empty() -> None:
    """Deserialize legacy task payloads without gate state."""
    task = TaskRecord.from_dict(
        {
            "id": "task_legacy",
            "title": "Legacy task",
            "description": "",
            "created_at": "2026-03-23T00:00:00+00:00",
            "updated_at": "2026-03-23T00:00:00+00:00",
            "status": "pending",
            "priority": "normal",
        }
    )

    assert task.gates == []


def test_gate_record_defaults_missing_or_malformed_history_to_empty() -> None:
    """Ignore missing or malformed embedded history entries during deserialization."""
    gate = TaskRecord.from_dict(
        {
            "id": "task_history",
            "title": "History task",
            "description": "",
            "created_at": "2026-03-24T00:00:00+00:00",
            "updated_at": "2026-03-24T00:00:00+00:00",
            "status": "pending",
            "priority": "normal",
            "gates": [
                {
                    "id": "review",
                    "gate_type": GateType.REVIEW.value,
                    "label": "Code review",
                    "history": [
                        "bad-entry",
                        {"action": "decision"},
                    ],
                }
            ],
        }
    ).gates[0]

    assert gate.history == []


def test_complete_run_requires_approved_required_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Block completion until required gates are approved."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Gated task",
        gates=[
            {
                "id": "human-approval",
                "gate_type": "approval",
                "label": "Human approval",
                "required": True,
            }
        ],
    )
    claim = service.claim_task(task.id)

    with pytest.raises(Exception, match="human-approval"):
        service.complete_run(claim.run.id, summary="done")

    updated = service.decide_gate(
        task.id,
        "human-approval",
        status=GateStatus.APPROVED,
        decided_by="reviewer-1",
        summary="approved",
    )
    assert updated.gates[0].status == GateStatus.APPROVED
    assert updated.gates[0].decided_by == "reviewer-1"

    completed = service.complete_run(claim.run.id, summary="done")
    assert completed.status.value == "completed"


def test_release_run_ignores_optional_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Allow release when only optional gates remain unresolved."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Optional gate task",
        gates=[
            {
                "id": "optional-review",
                "gate_type": "review",
                "label": "Optional review",
                "required": False,
            }
        ],
    )
    claim = service.claim_task(task.id)

    released = service.release_run(claim.run.id, reason="handoff")
    assert released.status.value == "released"


def test_decide_gate_rejects_unknown_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise an explicit error when a gate ID is unknown."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Unknown gate task")

    with pytest.raises(Exception, match="missing-gate"):
        service.decide_gate(
            task.id,
            "missing-gate",
            status=GateStatus.REJECTED,
        )

    assert service.get_task(task.id).gates == []


def test_gate_records_round_trip_on_task_serialization() -> None:
    """Serialize and deserialize task gate records safely."""
    task = TaskRecord.from_dict(
        {
            "id": "task_gated",
            "title": "Gated",
            "description": "desc",
            "created_at": "2026-03-23T00:00:00+00:00",
            "updated_at": "2026-03-23T00:00:00+00:00",
            "status": "pending",
            "priority": "normal",
            "gates": [
                {
                    "id": "policy-check",
                    "gate_type": GateType.POLICY.value,
                    "label": "Policy check",
                    "required": True,
                    "assigned_role": "reviewer",
                    "assigned_agent_id": "agent-123",
                    "assigned_decider": "reviewer-1",
                    "status": GateStatus.PENDING.value,
                    "decided_by": None,
                    "decided_at": None,
                    "summary": None,
                    "history": [
                        {
                            "action": GateHistoryAction.DECISION.value,
                            "from_status": GateStatus.PENDING.value,
                            "to_status": GateStatus.CHANGES_REQUESTED.value,
                            "actor": "reviewer-1",
                            "occurred_at": "2026-03-24T00:00:00+00:00",
                            "summary": "needs updates",
                        }
                    ],
                }
            ],
        }
    )

    serialized = task.to_dict()

    assert serialized["gates"][0]["id"] == "policy-check"
    assert serialized["gates"][0]["gate_type"] == GateType.POLICY.value
    assert serialized["gates"][0]["assigned_role"] == "reviewer"
    assert serialized["gates"][0]["assigned_agent_id"] == "agent-123"
    assert serialized["gates"][0]["assigned_decider"] == "reviewer-1"
    assert serialized["gates"][0]["history"][0]["action"] == GateHistoryAction.DECISION.value
    assert serialized["gates"][0]["history"][0]["from_status"] == GateStatus.PENDING.value
    assert serialized["gates"][0]["history"][0]["to_status"] == GateStatus.CHANGES_REQUESTED.value


def test_decide_gate_rejects_wrong_assigned_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject a gate decision from the wrong active agent."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Assigned agent gate",
        gates=[
            {
                "id": "approval",
                "gate_type": "approval",
                "label": "Assigned approval",
                "assigned_agent_id": "agent-owner",
            }
        ],
    )

    with pytest.raises(Exception, match="agent-owner"):
        service.decide_gate(task.id, "approval", status=GateStatus.APPROVED)

    assert service.get_task(task.id).gates[0].status == GateStatus.PENDING


def test_decide_gate_rejects_wrong_assigned_decider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject a gate decision when the decider identity does not match."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Assigned decider gate",
        gates=[
            {
                "id": "review",
                "gate_type": "review",
                "label": "Assigned review",
                "assigned_decider": "reviewer-1",
            }
        ],
    )

    with pytest.raises(Exception, match="reviewer-1"):
        service.decide_gate(task.id, "review", status=GateStatus.APPROVED)

    updated = service.decide_gate(
        task.id,
        "review",
        status=GateStatus.APPROVED,
        decided_by="reviewer-1",
    )
    assert updated.gates[0].status == GateStatus.APPROVED


def test_decide_gate_rejects_wrong_assigned_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject a gate decision when the acting role does not match."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Assigned role gate",
        gates=[
            {
                "id": "review",
                "gate_type": "review",
                "label": "Reviewer gate",
                "assigned_role": "reviewer",
            }
        ],
    )

    with pytest.raises(Exception, match="reviewer"):
        service.decide_gate(task.id, "review", status=GateStatus.APPROVED)

    updated = service.decide_gate(
        task.id,
        "review",
        status=GateStatus.APPROVED,
        decision_role="reviewer",
    )
    assert updated.gates[0].status == GateStatus.APPROVED


def test_changes_requested_blocks_completion_until_gate_reopened_and_approved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Required gates in changes_requested stay blocking until reopened and approved."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Lifecycle gate task",
        gates=[
            {
                "id": "review",
                "gate_type": "review",
                "label": "Code review",
                "required": True,
            }
        ],
    )
    claim = service.claim_task(task.id)

    changed = service.decide_gate(
        task.id,
        "review",
        status=GateStatus.CHANGES_REQUESTED,
        summary="needs revision",
    )
    assert changed.gates[0].status == GateStatus.CHANGES_REQUESTED
    assert len(changed.gates[0].history) == 1
    assert changed.gates[0].history[0].action == GateHistoryAction.DECISION
    assert changed.gates[0].history[0].from_status == GateStatus.PENDING
    assert changed.gates[0].history[0].to_status == GateStatus.CHANGES_REQUESTED

    with pytest.raises(Exception, match="review"):
        service.complete_run(claim.run.id, summary="done")

    with pytest.raises(Exception, match="without reopen"):
        service.decide_gate(task.id, "review", status=GateStatus.APPROVED)

    still_changed = service.get_task(task.id)
    assert len(still_changed.gates[0].history) == 1

    reopened = service.reopen_gate(task.id, "review")
    assert reopened.gates[0].status == GateStatus.PENDING
    assert reopened.gates[0].decided_by is None
    assert reopened.gates[0].decided_at is None
    assert reopened.gates[0].summary is None
    assert len(reopened.gates[0].history) == 2
    assert reopened.gates[0].history[1].action == GateHistoryAction.REOPENED
    assert reopened.gates[0].history[1].from_status == GateStatus.CHANGES_REQUESTED
    assert reopened.gates[0].history[1].to_status == GateStatus.PENDING

    approved = service.decide_gate(task.id, "review", status=GateStatus.APPROVED)
    assert approved.gates[0].status == GateStatus.APPROVED
    assert len(approved.gates[0].history) == 3
    assert approved.gates[0].history[2].action == GateHistoryAction.DECISION
    assert approved.gates[0].history[2].from_status == GateStatus.PENDING
    assert approved.gates[0].history[2].to_status == GateStatus.APPROVED

    completed = service.complete_run(claim.run.id, summary="done")
    assert completed.status.value == "completed"


def test_reopen_gate_preserves_assignments_and_rejects_invalid_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reopening preserves assignments and is limited to changes_requested gates."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Assigned lifecycle gate",
        gates=[
            {
                "id": "review",
                "gate_type": "review",
                "label": "Code review",
                "assigned_role": "reviewer",
                "assigned_agent_id": "agent-test",
                "assigned_decider": "reviewer-1",
            }
        ],
    )
    claim = service.claim_task(task.id)

    with pytest.raises(Exception, match="not in changes_requested"):
        service.reopen_gate(task.id, "review")

    changed = service.decide_gate(
        task.id,
        "review",
        status=GateStatus.CHANGES_REQUESTED,
        decided_by="reviewer-1",
        decision_role="reviewer",
    )
    assert changed.gates[0].status == GateStatus.CHANGES_REQUESTED
    assert len(changed.gates[0].history) == 1

    reopened = service.reopen_gate(task.id, "review")
    gate = reopened.gates[0]
    assert gate.status == GateStatus.PENDING
    assert gate.assigned_role == "reviewer"
    assert gate.assigned_agent_id == "agent-test"
    assert gate.assigned_decider == "reviewer-1"
    assert len(gate.history) == 2
    assert gate.history[1].action == GateHistoryAction.REOPENED

    approved = service.decide_gate(
        task.id,
        "review",
        status=GateStatus.APPROVED,
        decided_by="reviewer-1",
        decision_role="reviewer",
    )
    assert approved.gates[0].status == GateStatus.APPROVED
    assert len(approved.gates[0].history) == 3

    with pytest.raises(Exception, match="already approved"):
        service.decide_gate(
            task.id,
            "review",
            status=GateStatus.REJECTED,
            decided_by="reviewer-1",
            decision_role="reviewer",
        )

    assert len(service.get_task(task.id).gates[0].history) == 3

    with pytest.raises(Exception, match="not in changes_requested"):
        service.reopen_gate(task.id, "review", reopened_by=claim.run.agent_id)

    assert len(service.get_task(task.id).gates[0].history) == 3


# ── Policy gate auto-evaluation ───────────────────────────────────────────────


def test_parse_policy_decision_auto_always() -> None:
    """auto:always always returns APPROVED regardless of confidence."""
    result = _CPService._parse_policy_decision("auto:always", confidence=None)
    assert result is not None
    status, summary = result
    assert status == GateStatus.APPROVED
    assert "auto:always" in summary


def test_parse_policy_decision_confidence_threshold_met() -> None:
    """auto:confidence≥0.8 approves when confidence meets threshold."""
    result = _CPService._parse_policy_decision("auto:confidence≥0.8", confidence=0.9)
    assert result is not None
    status, _ = result
    assert status == GateStatus.APPROVED


def test_parse_policy_decision_confidence_threshold_not_met() -> None:
    """auto:confidence≥0.8 returns None (no auto-decision) when below threshold."""
    result = _CPService._parse_policy_decision("auto:confidence≥0.8", confidence=0.5)
    assert result is None


def test_parse_policy_decision_confidence_below_threshold() -> None:
    """auto:confidence<0.7 requests changes when confidence is below threshold."""
    result = _CPService._parse_policy_decision("auto:confidence<0.7", confidence=0.5)
    assert result is not None
    status, _ = result
    assert status == GateStatus.CHANGES_REQUESTED


def test_parse_policy_decision_confidence_not_below_threshold() -> None:
    """auto:confidence<0.7 returns None when confidence meets or exceeds threshold."""
    result = _CPService._parse_policy_decision("auto:confidence<0.7", confidence=0.8)
    assert result is None


def test_parse_policy_decision_no_confidence_for_threshold() -> None:
    """Threshold policies return None when confidence is not provided."""
    result = _CPService._parse_policy_decision("auto:confidence≥0.8", confidence=None)
    assert result is None


def test_parse_policy_decision_unknown_policy() -> None:
    """Unknown policy patterns return None."""
    result = _CPService._parse_policy_decision("auto:unknown", confidence=0.9)
    assert result is None


def test_policy_gate_auto_approves_on_high_confidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POLICY gate with auto:confidence≥0.8 approves when step result meets threshold."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="verify confidence gate",
        step_agents=["agent-test"],
        extra_gates=[
            {
                "id": "confidence-check",
                "gate_type": "policy",
                "label": "Confidence check",
                "required": True,
                "policy_name": "auto:confidence≥0.8",
            }
        ],
    )
    task_id = claim.run.task_id
    task = service.get_task(task_id)
    policy_gate = next(g for g in task.gates if g.id == "confidence-check")
    assert policy_gate.policy_name == "auto:confidence≥0.8"
    assert policy_gate.status == GateStatus.PENDING

    service.mark_workflow_step_running(task_id, step_index=0)
    updated = service.record_workflow_step_result(
        task_id,
        step_index=0,
        result_summary="step complete",
        confidence=0.9,
    )
    gate = next(g for g in updated.gates if g.id == "confidence-check")
    assert gate.status == GateStatus.APPROVED
    assert gate.decided_by == "policy:auto:confidence≥0.8"
    assert len(gate.history) == 1
    assert gate.history[0].action == GateHistoryAction.DECISION
    assert gate.history[0].from_status == GateStatus.PENDING
    assert gate.history[0].to_status == GateStatus.APPROVED

    completed = service.complete_run(claim.run.id, summary="done")
    assert completed.status.value == "completed"


def test_policy_gate_requests_changes_on_low_confidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POLICY gate with auto:confidence<0.7 requests changes when confidence is low."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="verify low-confidence gate",
        step_agents=["agent-test"],
        extra_gates=[
            {
                "id": "quality-gate",
                "gate_type": "policy",
                "label": "Quality gate",
                "required": True,
                "policy_name": "auto:confidence<0.7",
            }
        ],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)
    updated = service.record_workflow_step_result(
        task_id,
        step_index=0,
        result_summary="step complete",
        confidence=0.5,
    )
    gate = next(g for g in updated.gates if g.id == "quality-gate")
    assert gate.status == GateStatus.CHANGES_REQUESTED
    assert gate.decided_by == "policy:auto:confidence<0.7"

    with pytest.raises(Exception, match="quality-gate"):
        service.complete_run(claim.run.id, summary="done")


def test_policy_gate_auto_always_approves_immediately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POLICY gate with auto:always approves on first record_workflow_step_result call."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="verify auto:always gate",
        step_agents=["agent-test"],
        extra_gates=[
            {
                "id": "auto-gate",
                "gate_type": "policy",
                "label": "Auto gate",
                "required": True,
                "policy_name": "auto:always",
            }
        ],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)
    updated = service.record_workflow_step_result(
        task_id,
        step_index=0,
        result_summary="step complete",
        confidence=0.0,
    )
    gate = next(g for g in updated.gates if g.id == "auto-gate")
    assert gate.status == GateStatus.APPROVED

    completed = service.complete_run(claim.run.id, summary="done")
    assert completed.status.value == "completed"


def test_policy_gate_no_auto_decision_when_threshold_not_met(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POLICY gate stays pending when confidence does not meet the threshold."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="verify threshold not met",
        step_agents=["agent-test"],
        extra_gates=[
            {
                "id": "high-bar",
                "gate_type": "policy",
                "label": "High confidence bar",
                "required": True,
                "policy_name": "auto:confidence≥0.95",
            }
        ],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)
    updated = service.record_workflow_step_result(
        task_id,
        step_index=0,
        result_summary="step complete",
        confidence=0.8,
    )
    gate = next(g for g in updated.gates if g.id == "high-bar")
    assert gate.status == GateStatus.PENDING

    with pytest.raises(Exception, match="high-bar"):
        service.complete_run(claim.run.id, summary="done")
