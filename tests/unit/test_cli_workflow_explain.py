"""Unit tests for `tta control workflow explain` CLI command."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from ttadev.cli.control import handle_control_command
from ttadev.control_plane import ControlPlaneService
from ttadev.observability import agent_identity


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str = "agent-test",
    agent_tool: str = "copilot",
) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


def _make_explain_args(tmp_path: Path, task_id: str) -> argparse.Namespace:
    return argparse.Namespace(
        control_command="workflow",
        control_workflow_command="explain",
        task_id=task_id,
        data_dir=str(tmp_path),
    )


# ── helpers ───────────────────────────────────────────────────────────────────


def _start_workflow(
    tmp_path: Path,
    *,
    name: str = "test-wf",
    goal: str = "prove it",
    agents: list[str] | None = None,
) -> tuple[ControlPlaneService, str]:
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name=name,
        workflow_goal=goal,
        step_agents=agents or ["architect", "developer"],
    )
    return service, claim.run.task_id


# ── test cases ────────────────────────────────────────────────────────────────


def test_workflow_explain_no_active_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Workflow with all steps PENDING → output contains 'No active step.'"""
    _set_agent_identity(monkeypatch)
    service, task_id = _start_workflow(tmp_path)

    args = _make_explain_args(tmp_path, task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert "No active step." in out
    assert "test-wf" in out


def test_workflow_explain_running_step_no_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running step without trace → output contains agent name and RUNNING; no Trace: line."""
    _set_agent_identity(monkeypatch)
    service, task_id = _start_workflow(tmp_path, agents=["architect", "developer"])
    service.mark_workflow_step_running(task_id, step_index=0)

    args = _make_explain_args(tmp_path, task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert "architect" in out
    assert "RUNNING" in out
    assert "Trace:" not in out


def test_workflow_explain_running_step_with_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Running step with trace_id set → output contains 'Trace:' and the value."""
    _set_agent_identity(monkeypatch)
    service, task_id = _start_workflow(tmp_path, agents=["backend-engineer"])

    # Stamp a trace ID before marking running
    monkeypatch.setenv("TRACEPARENT", "00-abcdef1234567890abcdef1234567890-0011223344556677-01")
    service.mark_workflow_step_running(task_id, step_index=0)

    # Retrieve the stored step to confirm trace was set
    task = service.get_task(task_id)
    step = task.workflow.steps[0]  # type: ignore[union-attr]

    args = _make_explain_args(tmp_path, task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    # TRACEPARENT env var is now picked up as a fallback when no active OTel span
    # exists, so trace_id must always be set in this test.
    assert step.trace_id is not None, "TRACEPARENT env var should have been parsed"
    assert "Trace:" in out
    assert step.trace_id in out


def test_workflow_explain_with_pending_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Task with a pending gate → output contains 'Pending Gates' and the gate ID."""
    _set_agent_identity(monkeypatch)
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="gated-wf",
        workflow_goal="test gates",
        step_agents=["developer"],
        extra_gates=[
            {
                "id": "quality-gate",
                "gate_type": "policy",
                "label": "Quality",
                "required": True,
                "policy_name": "auto:always",
            }
        ],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)

    args = _make_explain_args(tmp_path, task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert "Pending Gates" in out
    assert "quality-gate" in out


def test_workflow_explain_no_pending_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No pending gates → output does NOT contain 'Pending Gates' section."""
    _set_agent_identity(monkeypatch)
    service, task_id = _start_workflow(tmp_path, agents=["developer"])
    service.mark_workflow_step_running(task_id, step_index=0)

    args = _make_explain_args(tmp_path, task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert "Pending Gates" not in out


def test_workflow_explain_task_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unknown task_id → returns exit code 1 with an error on stderr."""
    _set_agent_identity(monkeypatch)
    args = _make_explain_args(tmp_path, "task_nonexistent_xyz")
    rc = handle_control_command(args, tmp_path)
    assert rc == 1
    err = capsys.readouterr().err
    assert "task_nonexistent_xyz" in err
