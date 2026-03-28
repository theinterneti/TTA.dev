"""Unit tests for `tta control gate` CLI subcommands."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from ttadev.cli.control import handle_control_command
from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import GateStatus, WorkflowGateDecisionOutcome, WorkflowStepStatus
from ttadev.observability import agent_identity


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str = "agent-test",
    agent_tool: str = "copilot",
) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


def _make_args(tmp_path: Path, **kwargs) -> argparse.Namespace:  # type: ignore[no-untyped-def]
    """Build a minimal argparse.Namespace for gate commands."""
    defaults = {
        "control_command": "gate",
        "control_gate_command": "list",
        "task_id": "task_placeholder",
        "gate_id": None,
        "note": "",
        "project_name": None,
        "data_dir": str(tmp_path),
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _setup_workflow_task(
    service: ControlPlaneService,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[str, str]:
    """Create a workflow task with a policy gate; return (task_id, gate_id)."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="prove gate CLI",
        step_agents=["agent-test", "reviewer"],
        extra_gates=[
            {
                "id": "quality",
                "gate_type": "policy",
                "label": "Quality gate",
                "required": True,
                "policy_name": "auto:confidence>=0.8",
            }
        ],
    )
    return claim.run.task_id, "quality"


# ── gate list ────────────────────────────────────────────────────────────────


def test_gate_list_shows_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """gate list prints a table of all gates for the task."""
    service = ControlPlaneService(tmp_path)
    task_id, gate_id = _setup_workflow_task(service, monkeypatch)

    args = _make_args(tmp_path, control_gate_command="list", task_id=task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert gate_id in out
    assert "POLICY" in out or "policy" in out


def test_gate_list_unknown_task_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """gate list exits 1 when task_id does not exist."""
    _set_agent_identity(monkeypatch)
    args = _make_args(tmp_path, control_gate_command="list", task_id="task_nonexistent")
    rc = handle_control_command(args, tmp_path)
    assert rc == 1


# ── gate approve ─────────────────────────────────────────────────────────────


def test_gate_approve_sets_gate_approved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """gate approve transitions a PENDING gate to APPROVED."""
    service = ControlPlaneService(tmp_path)
    task_id, gate_id = _setup_workflow_task(service, monkeypatch)

    args = _make_args(tmp_path, control_gate_command="approve", task_id=task_id, gate_id=gate_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    task = service.get_task(task_id)
    gate = next(g for g in task.gates if g.id == gate_id)
    assert gate.status == GateStatus.APPROVED


def test_gate_approve_with_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """gate approve stores the --note in the gate summary."""
    service = ControlPlaneService(tmp_path)
    task_id, gate_id = _setup_workflow_task(service, monkeypatch)

    args = _make_args(
        tmp_path,
        control_gate_command="approve",
        task_id=task_id,
        gate_id=gate_id,
        note="LGTM!",
    )
    handle_control_command(args, tmp_path)

    task = service.get_task(task_id)
    gate = next(g for g in task.gates if g.id == gate_id)
    assert gate.summary == "LGTM!"


def test_gate_approve_already_decided_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """gate approve on an already-decided gate exits 0 with a warning."""
    service = ControlPlaneService(tmp_path)
    task_id, gate_id = _setup_workflow_task(service, monkeypatch)
    service.decide_gate(task_id, gate_id, status=GateStatus.APPROVED)

    args = _make_args(tmp_path, control_gate_command="approve", task_id=task_id, gate_id=gate_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out + capsys.readouterr().err
    # Should indicate already decided (some output about the gate state)
    assert "already" in out.lower() or "approved" in out.lower()


# ── gate reject ──────────────────────────────────────────────────────────────


def test_gate_reject_sets_gate_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """gate reject transitions a PENDING gate to REJECTED."""
    service = ControlPlaneService(tmp_path)
    task_id, gate_id = _setup_workflow_task(service, monkeypatch)

    args = _make_args(
        tmp_path,
        control_gate_command="reject",
        task_id=task_id,
        gate_id=gate_id,
        note="Needs more tests",
    )
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    task = service.get_task(task_id)
    gate = next(g for g in task.gates if g.id == gate_id)
    assert gate.status == GateStatus.REJECTED


# ── gate quit ────────────────────────────────────────────────────────────────


def test_gate_quit_on_workflow_aborts_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gate quit on a workflow task sets step gate_decision=QUIT and aborts the workflow."""
    service = ControlPlaneService(tmp_path)
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="prove quit",
        step_agents=["agent-test", "reviewer"],
    )
    task_id = claim.run.task_id
    # The per-step APPROVAL gate for step 0
    task = service.get_task(task_id)
    approval_gate_id = task.workflow.steps[0].linked_gate_id
    assert approval_gate_id is not None

    service.mark_workflow_step_running(task_id, step_index=0)

    args = _make_args(
        tmp_path,
        control_gate_command="quit",
        task_id=task_id,
        gate_id=approval_gate_id,
        note="Stop here",
    )
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    task = service.get_task(task_id)
    step0 = task.workflow.steps[0]
    assert step0.gate_decision == WorkflowGateDecisionOutcome.QUIT
    assert step0.status == WorkflowStepStatus.QUIT


def test_gate_quit_on_non_workflow_gate_falls_back_to_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gate quit on a plain (non-workflow) gate falls back to REJECTED."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        title="plain task",
        gates=[{"id": "review", "gate_type": "review", "label": "Review", "required": False}],
    )

    args = _make_args(
        tmp_path,
        control_gate_command="quit",
        task_id=task.id,
        gate_id="review",
        note="Stopping",
    )
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    updated = service.get_task(task.id)
    gate = next(g for g in updated.gates if g.id == "review")
    assert gate.status == GateStatus.REJECTED
