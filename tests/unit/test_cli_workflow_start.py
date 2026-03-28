"""Unit tests for `tta control workflow start` CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest

from ttadev.cli.control import _parse_policy_gate_spec, handle_control_command
from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import GateType, WorkflowTrackingStatus
from ttadev.observability import agent_identity


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str = "agent-test",
    agent_tool: str = "copilot",
) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


def _make_args(tmp_path: Path, **kwargs):  # type: ignore[no-untyped-def]
    """Build a minimal argparse.Namespace for workflow start."""
    import argparse

    defaults = {
        "control_command": "workflow",
        "control_workflow_command": "start",
        "name": "test-wf",
        "goal": "ship it",
        "agents": "architect,backend-engineer",
        "project_name": None,
        "policy_gates": [],
        "ttl": 300.0,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ── _parse_policy_gate_spec unit tests ────────────────────────────────────────


def test_parse_policy_gate_spec_basic() -> None:
    """Valid spec parses into expected gate payload."""
    result = _parse_policy_gate_spec("id=quality,label=Quality gate,policy=auto:always")
    assert result["id"] == "quality"
    assert result["label"] == "Quality gate"
    assert result["policy_name"] == "auto:always"
    assert result["gate_type"] == "policy"
    assert result["required"] is True


def test_parse_policy_gate_spec_with_threshold() -> None:
    """Policy pattern containing >= parses correctly (= not confused with key separator)."""
    result = _parse_policy_gate_spec("id=ci,label=CI gate,policy=auto:confidence>=0.85")
    assert result["policy_name"] == "auto:confidence>=0.85"


def test_parse_policy_gate_spec_missing_key_raises() -> None:
    """Missing required key raises ControlPlaneError."""
    from ttadev.control_plane import ControlPlaneError

    with pytest.raises(ControlPlaneError, match="missing required key"):
        _parse_policy_gate_spec("id=x,label=y")  # no policy=


def test_parse_policy_gate_spec_bad_token_raises() -> None:
    """Token without = raises ControlPlaneError."""
    from ttadev.control_plane import ControlPlaneError

    with pytest.raises(ControlPlaneError, match="key=value form"):
        _parse_policy_gate_spec("id=x,badtoken,policy=auto:always")


# ── handle_control_command integration tests ─────────────────────────────────


def test_workflow_start_basic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: creates task, run, and prints expected fields."""
    _set_agent_identity(monkeypatch)
    args = _make_args(tmp_path, agents="architect,backend-engineer,reviewer")

    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert "Workflow started." in out
    assert "task_id:" in out
    assert "run_id:" in out
    assert "architect → backend-engineer → reviewer" in out
    assert "expires" in out

    # Verify state was persisted
    service = ControlPlaneService(tmp_path)
    tasks = service.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].workflow is not None
    assert tasks[0].workflow.status == WorkflowTrackingStatus.RUNNING
    assert tasks[0].workflow.total_steps == 3


def test_workflow_start_with_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--project is passed through and stored on the task."""
    _set_agent_identity(monkeypatch)
    args = _make_args(tmp_path, project_name="my-project")

    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    service = ControlPlaneService(tmp_path)
    task = service.list_tasks()[0]
    assert task.project_name == "my-project"


def test_workflow_start_with_policy_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--policy-gate produces an extra POLICY gate on the task."""
    _set_agent_identity(monkeypatch)
    args = _make_args(
        tmp_path,
        policy_gates=["id=quality,label=Quality gate,policy=auto:confidence>=0.85"],
    )

    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    service = ControlPlaneService(tmp_path)
    task = service.list_tasks()[0]
    policy_gates = [g for g in task.gates if g.gate_type == GateType.POLICY]
    assert len(policy_gates) == 1
    assert policy_gates[0].id == "quality"
    assert policy_gates[0].policy_name == "auto:confidence>=0.85"


def test_workflow_start_missing_agents_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty --agents string prints error and exits non-zero."""
    _set_agent_identity(monkeypatch)
    args = _make_args(tmp_path, agents="   ")

    rc = handle_control_command(args, tmp_path)

    assert rc != 0
    assert "Error" in capsys.readouterr().err


def test_workflow_start_service_error_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Service error is caught, printed to stderr, and returns non-zero."""
    _set_agent_identity(monkeypatch)
    # Pass no step_agents via monkeypatching the service method to raise
    from ttadev.control_plane import ControlPlaneError

    def _raise(*a, **kw):
        raise ControlPlaneError("simulated failure")

    monkeypatch.setattr(ControlPlaneService, "start_tracked_workflow", _raise)
    args = _make_args(tmp_path)

    rc = handle_control_command(args, tmp_path)

    assert rc != 0
    assert "simulated failure" in capsys.readouterr().err
