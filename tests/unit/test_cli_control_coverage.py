"""Comprehensive coverage tests for ttadev/cli/control.py.

Targets the 308 missing lines that leave control.py at 49% coverage.
Focuses on:
  - workflow step {start,done,fail,gate}
  - run {show,heartbeat,release}
  - lock {acquire-workspace,acquire-file,list with scope filter}
  - task list with --status / --project filters
  - run list with --status filter
  - workflow start with existing_task_id (attach path)
  - workflow status gates section
  - _step_duration helper
  - _parse_gate_spec / _parse_gate_assignment_spec / _apply_gate_assignments helpers
  - usage / no-subcommand paths for every dispatcher
  - error branches not yet exercised
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ttadev.cli.control import (
    _apply_gate_assignments,
    _parse_gate_assignment_spec,
    _parse_gate_spec,
    _step_duration,
    handle_control_command,
)
from ttadev.control_plane import (
    ControlPlaneError,
    ControlPlaneService,
)
from ttadev.control_plane.models import (
    GateStatus,
    WorkflowStepStatus,
    WorkflowTrackingStatus,
)
from ttadev.observability import agent_identity

# ── helpers ───────────────────────────────────────────────────────────────────


def _set_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str = "agent-test",
    agent_tool: str = "copilot",
) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


def _ns(**kwargs) -> argparse.Namespace:  # type: ignore[no-untyped-def]
    """Build a minimal Namespace; callers supply only the relevant fields."""
    return argparse.Namespace(**kwargs)


def _start_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    agents: list[str] | None = None,
    name: str = "test-wf",
    goal: str = "prove coverage",
) -> tuple[ControlPlaneService, str, str]:
    """Return (service, task_id, run_id) for a freshly started workflow."""
    _set_identity(monkeypatch)
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name=name,
        workflow_goal=goal,
        step_agents=agents or ["architect", "developer"],
    )
    return service, claim.run.task_id, claim.run.id


def _claim_plain_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    title: str = "plain task",
) -> tuple[ControlPlaneService, str, str]:
    """Return (service, task_id, run_id) for a claimed plain task."""
    _set_identity(monkeypatch)
    service = ControlPlaneService(tmp_path)
    task = service.create_task(title)
    claim = service.claim_task(task.id)
    return service, task.id, claim.run.id


# ═══════════════════════════════════════════════════════════════════════════════
# _step_duration helper
# ═══════════════════════════════════════════════════════════════════════════════


class TestStepDuration:
    """Unit tests for _step_duration()."""

    def test_no_started_at_returns_dash(self) -> None:
        assert _step_duration(None, None) == "-"

    def test_no_started_at_with_completed_returns_dash(self) -> None:
        assert _step_duration(None, datetime.now(UTC).isoformat()) == "-"

    def test_started_and_completed_returns_duration(self) -> None:
        start = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()
        end = datetime.now(UTC).isoformat()
        result = _step_duration(start, end)
        assert result.endswith("s")
        assert float(result[:-1]) >= 4.5

    def test_started_no_completed_uses_current_time(self) -> None:
        start = (datetime.now(UTC) - timedelta(seconds=3)).isoformat()
        result = _step_duration(start, None)
        assert result.endswith("s")
        assert float(result[:-1]) >= 2.5


# ═══════════════════════════════════════════════════════════════════════════════
# _parse_gate_spec helper
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseGateSpec:
    """Unit tests for _parse_gate_spec()."""

    def test_valid_required_gate(self) -> None:
        result = _parse_gate_spec("g1:approval:required:Human approval")
        assert result == {
            "id": "g1",
            "gate_type": "approval",
            "required": True,
            "label": "Human approval",
        }

    def test_valid_optional_gate(self) -> None:
        result = _parse_gate_spec("g2:review:optional:Code review")
        assert result["required"] is False

    def test_label_with_colons_preserved(self) -> None:
        """Label portion may contain colons — split(3) must protect them."""
        result = _parse_gate_spec("g3:policy:required:check: foo:bar")
        assert result["label"] == "check: foo:bar"

    def test_too_few_parts_raises(self) -> None:
        with pytest.raises(ControlPlaneError, match="Gate spec must use the form"):
            _parse_gate_spec("g1:approval:required")

    def test_invalid_required_flag_raises(self) -> None:
        with pytest.raises(ControlPlaneError, match=r"required|optional"):
            _parse_gate_spec("g1:approval:maybe:label")


# ═══════════════════════════════════════════════════════════════════════════════
# _parse_gate_assignment_spec helper
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseGateAssignmentSpec:
    """Unit tests for _parse_gate_assignment_spec()."""

    def test_valid_spec(self) -> None:
        gate_id, value = _parse_gate_assignment_spec("g1:reviewer", "--gate-assign-role")
        assert gate_id == "g1"
        assert value == "reviewer"

    def test_missing_colon_raises(self) -> None:
        with pytest.raises(ControlPlaneError, match="must use the form"):
            _parse_gate_assignment_spec("nocolon", "--gate-assign-role")

    def test_empty_gate_id_raises(self) -> None:
        with pytest.raises(ControlPlaneError, match="must use the form"):
            _parse_gate_assignment_spec(":value", "--gate-assign-role")

    def test_empty_value_raises(self) -> None:
        with pytest.raises(ControlPlaneError, match="must use the form"):
            _parse_gate_assignment_spec("gate_id:", "--gate-assign-role")


# ═══════════════════════════════════════════════════════════════════════════════
# _apply_gate_assignments helper
# ═══════════════════════════════════════════════════════════════════════════════


class TestApplyGateAssignments:
    """Unit tests for _apply_gate_assignments()."""

    def _make_gates(self) -> list[dict]:  # type: ignore[type-arg]
        return [{"id": "g1", "gate_type": "approval", "required": True, "label": "L"}]

    def test_assigns_role(self) -> None:
        gates = self._make_gates()
        _apply_gate_assignments(gates, role_specs=["g1:reviewer"], agent_specs=[], decider_specs=[])
        assert gates[0]["assigned_role"] == "reviewer"

    def test_assigns_agent(self) -> None:
        gates = self._make_gates()
        _apply_gate_assignments(gates, role_specs=[], agent_specs=["g1:agent-7"], decider_specs=[])
        assert gates[0]["assigned_agent_id"] == "agent-7"

    def test_assigns_decider(self) -> None:
        gates = self._make_gates()
        _apply_gate_assignments(
            gates, role_specs=[], agent_specs=[], decider_specs=["g1:decider-x"]
        )
        assert gates[0]["assigned_decider"] == "decider-x"

    def test_unknown_gate_id_raises(self) -> None:
        gates = self._make_gates()
        with pytest.raises(ControlPlaneError, match="Unknown gate ID"):
            _apply_gate_assignments(
                gates, role_specs=["g99:reviewer"], agent_specs=[], decider_specs=[]
            )

    def test_duplicate_assignment_raises(self) -> None:
        gates = self._make_gates()
        with pytest.raises(ControlPlaneError, match="Duplicate"):
            _apply_gate_assignments(
                gates,
                role_specs=["g1:reviewer", "g1:admin"],
                agent_specs=[],
                decider_specs=[],
            )


# ═══════════════════════════════════════════════════════════════════════════════
# task list with filters
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskListFilters:
    """task list --status / --project filtering."""

    def test_list_empty_shows_no_tasks(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="task",
            control_task_command="list",
            status=None,
            project_name=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        assert "No tasks found" in capsys.readouterr().out

    def test_list_filters_by_status(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        service.create_task("pending-task")
        args = _ns(
            control_command="task",
            control_task_command="list",
            status="pending",
            project_name=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "pending-task" in out

    def test_list_filters_by_project(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        service.create_task("alpha-task", project_name="alpha")
        service.create_task("beta-task", project_name="beta")
        args = _ns(
            control_command="task",
            control_task_command="list",
            status=None,
            project_name="alpha",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "alpha-task" in out
        assert "beta-task" not in out

    def test_list_status_filter_returns_empty_if_no_match(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        service.create_task("pending-only")
        args = _ns(
            control_command="task",
            control_task_command="list",
            status="completed",
            project_name=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        assert "No tasks found" in capsys.readouterr().out

    def test_task_create_with_priority_and_role(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="task",
            control_task_command="create",
            title="important task",
            description="desc",
            project_name="proj",
            requested_role="backend-engineer",
            priority="high",
            gate=[],
            gate_assign_role=[],
            gate_assign_agent=[],
            gate_assign_decider=[],
            workspace_locks=[],
            file_locks=[],
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "important task" in out
        assert "proj" in out
        assert "backend-engineer" in out

    def test_task_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="task",
            control_task_command=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════════
# run show / heartbeat / release
# ═══════════════════════════════════════════════════════════════════════════════


class TestRunCommands:
    """run show, heartbeat, release, list with filter."""

    def test_run_show_active(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        args = _ns(
            control_command="run",
            control_run_command="show",
            run_id=run_id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert run_id in out
        assert task_id in out
        assert "active" in out

    def test_run_show_with_trace(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """run show includes trace: line when run has a trace_id."""
        _set_identity(monkeypatch)
        monkeypatch.setenv("TRACEPARENT", "00-abcdef1234567890abcdef1234567890-0011223344556677-01")
        service = ControlPlaneService(tmp_path)
        task = service.create_task("task with trace")
        claim = service.claim_task(task.id)
        run_id = claim.run.id

        args = _ns(control_command="run", control_run_command="show", run_id=run_id)
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert run_id in out

    def test_run_heartbeat(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, _task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        args = _ns(
            control_command="run",
            control_run_command="heartbeat",
            run_id=run_id,
            ttl=120.0,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert run_id in out
        assert "expires_at" in out

    def test_run_release(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, _task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        args = _ns(
            control_command="run",
            control_run_command="release",
            run_id=run_id,
            reason="no longer needed",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Released run" in out
        assert run_id in out

    def test_run_list_with_status_filter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, _task_id, run_id = _claim_plain_task(tmp_path, monkeypatch, title="list-me")
        args = _ns(
            control_command="run",
            control_run_command="list",
            status="active",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert run_id in out

    def test_run_list_status_filter_no_match(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="run",
            control_run_command="list",
            status="completed",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        assert "No runs found" in capsys.readouterr().out

    def test_run_complete_with_summary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, _task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        args = _ns(
            control_command="run",
            control_run_command="complete",
            run_id=run_id,
            summary="all done",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Completed run" in out
        assert "all done" in out

    def test_run_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(control_command="run", control_run_command=None)
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════════
# lock commands
# ═══════════════════════════════════════════════════════════════════════════════


class TestLockCommands:
    """lock acquire-workspace, acquire-file, list with scope-type filter."""

    def test_acquire_workspace_lock(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, run_id = _claim_plain_task(tmp_path, monkeypatch, title="ws-lock-task")
        args = _ns(
            control_command="lock",
            control_lock_command="acquire-workspace",
            task_id=task_id,
            run_id=run_id,
            workspace_name="my-workspace",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Lock:" in out
        assert "workspace" in out
        assert "my-workspace" in out

    def test_acquire_file_lock(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, run_id = _claim_plain_task(tmp_path, monkeypatch, title="file-lock-task")
        args = _ns(
            control_command="lock",
            control_lock_command="acquire-file",
            task_id=task_id,
            run_id=run_id,
            file_path="src/main.py",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Lock:" in out
        assert "file" in out
        assert "src/main.py" in out

    def test_lock_list_no_filter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="lock",
            control_lock_command="list",
            scope_type=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        assert "No locks found" in capsys.readouterr().out

    def test_lock_list_scope_type_filter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, run_id = _claim_plain_task(tmp_path, monkeypatch, title="scope-filter")
        # Acquire a workspace lock and a file lock
        service.acquire_workspace_lock(task_id, run_id, "ws-alpha")
        service.acquire_file_lock(task_id, run_id, "src/app.py")

        args = _ns(
            control_command="lock",
            control_lock_command="list",
            scope_type="workspace",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "ws-alpha" in out
        assert "src/app.py" not in out

    def test_lock_release(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, run_id = _claim_plain_task(tmp_path, monkeypatch, title="release-lock")
        lock = service.acquire_workspace_lock(task_id, run_id, "temp-ws")
        args = _ns(
            control_command="lock",
            control_lock_command="release",
            lock_id=lock.id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Released lock" in out
        assert lock.id in out

    def test_lock_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(control_command="lock", control_lock_command=None)
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════════
# workflow step commands
# ═══════════════════════════════════════════════════════════════════════════════


class TestWorkflowStepCommands:
    """workflow step {start,done,fail,gate}."""

    def test_workflow_step_start(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="start",
            task_id=task_id,
            step_index=0,
            trace_id=None,
            span_id=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Step 0 started" in out
        assert "architect" in out

    def test_workflow_step_start_with_trace(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="start",
            task_id=task_id,
            step_index=0,
            trace_id="abcdef1234567890abcdef1234567890",
            span_id="0011223344556677",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "trace:" in out

    def test_workflow_step_done(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        service.mark_workflow_step_running(task_id, step_index=0)
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="done",
            task_id=task_id,
            step_index=0,
            result="feature complete",
            confidence=0.92,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Step 0 completed" in out
        assert "feature complete" in out
        assert "0.92" in out

    def test_workflow_step_fail(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        service.mark_workflow_step_running(task_id, step_index=0)
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="fail",
            task_id=task_id,
            step_index=0,
            error="compilation error",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Step 0 marked failed" in out
        assert "compilation error" in out

        # Verify step status persisted
        task = service.get_task(task_id)
        assert task.workflow.steps[0].status == WorkflowStepStatus.FAILED

    def test_workflow_step_gate_continue(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        service.mark_workflow_step_running(task_id, step_index=0)
        service.record_workflow_step_result(
            task_id, step_index=0, result_summary="done", confidence=0.9
        )
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="gate",
            task_id=task_id,
            step_index=0,
            decision="continue",
            summary="looks great",
            policy_name=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Step 0 gate outcome recorded" in out
        assert "continue" in out

    def test_workflow_step_gate_quit(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        service.mark_workflow_step_running(task_id, step_index=0)
        service.record_workflow_step_result(
            task_id, step_index=0, result_summary="gave up", confidence=0.2
        )
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="gate",
            task_id=task_id,
            step_index=0,
            decision="quit",
            summary="",
            policy_name=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "workflow status" in out.lower()

        task = service.get_task(task_id)
        assert task.workflow.status == WorkflowTrackingStatus.QUIT

    def test_workflow_step_gate_with_policy_name(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, task_id, _run_id = _start_workflow(tmp_path, monkeypatch)
        service.mark_workflow_step_running(task_id, step_index=0)
        service.record_workflow_step_result(
            task_id, step_index=0, result_summary="auto-approved", confidence=0.95
        )
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command="gate",
            task_id=task_id,
            step_index=0,
            decision="continue",
            summary="auto",
            policy_name="auto:confidence>=0.9",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0

    def test_workflow_step_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="workflow",
            control_workflow_command="step",
            control_workflow_step_command=None,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════════
# workflow start: attach to existing task
# ═══════════════════════════════════════════════════════════════════════════════


class TestWorkflowStartAttach:
    """workflow start --task-id attaches to an existing task."""

    def test_attach_workflow_to_existing_task(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        # Create a plain task first
        task = service.create_task("existing task")
        existing_task_id = task.id

        args = _ns(
            control_command="workflow",
            control_workflow_command="start",
            name="attached-wf",
            goal="attach to existing",
            agents="developer,reviewer",
            existing_task_id=existing_task_id,
            project_name=None,
            policy_gates=[],
            ttl=300.0,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Workflow started" in out
        assert "developer → reviewer" in out

        # Verify workflow was attached to the existing task
        updated = service.get_task(existing_task_id)
        assert updated.workflow is not None
        assert updated.workflow.workflow_name == "attached-wf"


# ═══════════════════════════════════════════════════════════════════════════════
# workflow status: with gates section
# ═══════════════════════════════════════════════════════════════════════════════


class TestWorkflowStatusGates:
    """workflow status displays the gates section when gates are present."""

    def test_workflow_status_shows_gates_section(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        claim = service.start_tracked_workflow(
            workflow_name="gated-wf",
            workflow_goal="with gates",
            step_agents=["developer"],
            extra_gates=[
                {
                    "id": "ci-gate",
                    "gate_type": "policy",
                    "label": "CI gate",
                    "required": True,
                    "policy_name": "auto:always",
                }
            ],
        )
        task_id = claim.run.task_id
        args = _ns(
            control_command="workflow",
            control_workflow_command="status",
            task_id=task_id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gates" in out
        assert "ci-gate" in out

    def test_workflow_status_trace_in_step_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        claim = service.start_tracked_workflow(
            workflow_name="trace-wf",
            workflow_goal="check trace in status",
            step_agents=["developer"],
        )
        task_id = claim.run.task_id
        monkeypatch.setenv("TRACEPARENT", "00-abcdef1234567890abcdef1234567890-0011223344556677-01")
        service.mark_workflow_step_running(task_id, step_index=0)

        args = _ns(
            control_command="workflow",
            control_workflow_command="status",
            task_id=task_id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        # trace_id column should show abbreviated trace (first 8 chars + …)
        assert "abcdef12" in out


# ═══════════════════════════════════════════════════════════════════════════════
# workflow no-subcommand usage messages
# ═══════════════════════════════════════════════════════════════════════════════


class TestUsageMessages:
    """All dispatchers return 1 + usage hint when no subcommand is given."""

    def test_control_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(control_command=None)
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err

    def test_workflow_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(control_command="workflow", control_workflow_command=None)
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err

    def test_gate_no_subcommand_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(control_command="gate", control_gate_command=None)
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Usage" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════════
# gate command error paths
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateErrorPaths:
    """Error branches in _handle_gate_command."""

    def test_gate_list_task_with_no_gates(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        task = service.create_task("no-gates task")
        args = _ns(
            control_command="gate",
            control_gate_command="list",
            task_id=task.id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        assert "No gates" in capsys.readouterr().out

    def test_gate_approve_task_not_found(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="gate",
            control_gate_command="approve",
            task_id="task_nonexistent",
            gate_id="g1",
            note="",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Error" in capsys.readouterr().err

    def test_gate_reject_task_not_found(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="gate",
            control_gate_command="reject",
            task_id="task_nonexistent",
            gate_id="g1",
            note="",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 1

    def test_gate_quit_non_workflow_gate_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """gate quit on already-rejected gate produces TaskGateError → exit 1."""
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        task = service.create_task(
            "gated",
            gates=[{"id": "g1", "gate_type": "review", "label": "Review", "required": False}],
        )
        # Pre-reject so a second decide_gate call raises TaskGateError
        service.decide_gate(task.id, "g1", status=GateStatus.REJECTED)

        args = _ns(
            control_command="gate",
            control_gate_command="quit",
            task_id=task.id,
            gate_id="g1",
            note="stopping",
        )
        rc = handle_control_command(args, tmp_path)
        # Already decided → TaskGateError path → exit 1
        assert rc == 1
        assert "Error" in capsys.readouterr().err

    def test_gate_quit_task_not_found(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="gate",
            control_gate_command="quit",
            task_id="task_nonexistent",
            gate_id="g1",
            note="",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 1
        assert "Error" in capsys.readouterr().err

    def test_gate_approve_task_gate_error_non_already(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """TaskGateError without 'already' in message → exit 1 with error."""
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        task = service.create_task(
            "changes-req",
            gates=[{"id": "g1", "gate_type": "review", "label": "Review", "required": True}],
        )
        # Set gate to changes_requested first so approve raises about missing reopen
        service.decide_gate(task.id, "g1", status=GateStatus.CHANGES_REQUESTED)

        args = _ns(
            control_command="gate",
            control_gate_command="approve",
            task_id=task.id,
            gate_id="g1",
            note="",
        )
        rc = handle_control_command(args, tmp_path)
        # Should fail because cannot approve after changes_requested without reopen
        assert rc == 1
        assert "Error" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════════
# task create with workspace/file locks
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskCreateLocks:
    """task create --workspace-lock / --file-lock shows lock fields in output."""

    def test_create_with_workspace_lock(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="task",
            control_task_command="create",
            title="locked task",
            description="",
            project_name=None,
            requested_role=None,
            priority="normal",
            gate=[],
            gate_assign_role=[],
            gate_assign_agent=[],
            gate_assign_decider=[],
            workspace_locks=["my-ws"],
            file_locks=[],
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "workspace_locks: my-ws" in out

    def test_create_with_file_lock(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="task",
            control_task_command="create",
            title="file locked task",
            description="",
            project_name=None,
            requested_role=None,
            priority="normal",
            gate=[],
            gate_assign_role=[],
            gate_assign_agent=[],
            gate_assign_decider=[],
            workspace_locks=[],
            file_locks=["src/foo.py"],
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "file_locks:" in out

    def test_create_with_gate_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _set_identity(monkeypatch)
        args = _ns(
            control_command="task",
            control_task_command="create",
            title="gated create",
            description="",
            project_name=None,
            requested_role=None,
            priority="normal",
            gate=["g1:approval:required:Human review"],
            gate_assign_role=["g1:reviewer"],
            gate_assign_agent=[],
            gate_assign_decider=[],
            workspace_locks=[],
            file_locks=[],
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "gates:    1" in out


# ═══════════════════════════════════════════════════════════════════════════════
# task show with workflow and gates
# ═══════════════════════════════════════════════════════════════════════════════


class TestTaskShowWorkflow:
    """task show renders workflow tracking details."""

    def test_task_show_workflow_with_span_id(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Workflow step with trace_id + span_id shows trace_ref in task show."""
        _set_identity(monkeypatch)
        service = ControlPlaneService(tmp_path)
        claim = service.start_tracked_workflow(
            workflow_name="span-wf",
            workflow_goal="test span",
            step_agents=["developer"],
        )
        task_id = claim.task.id
        monkeypatch.setenv("TRACEPARENT", "00-abcdef1234567890abcdef1234567890-0011223344556677-01")
        service.mark_workflow_step_running(task_id, step_index=0)

        args = _ns(
            control_command="task",
            control_task_command="show",
            task_id=task_id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "trace=" in out

    def test_task_show_with_completed_at(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Completed task shows completed_at field."""
        service, task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        service.complete_run(run_id, summary="done")

        args = _ns(
            control_command="task",
            control_task_command="show",
            task_id=task_id,
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "completed_at" in out


# ═══════════════════════════════════════════════════════════════════════════════
# run show: summary line
# ═══════════════════════════════════════════════════════════════════════════════


class TestRunShowSummary:
    """run show displays summary for completed runs."""

    def test_run_show_completed_with_summary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, _task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        service.complete_run(run_id, summary="finished successfully")

        args = _ns(control_command="run", control_run_command="show", run_id=run_id)
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "finished successfully" in out
        assert "completed" in out

    def test_run_release_with_no_reason(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        service, _task_id, run_id = _claim_plain_task(tmp_path, monkeypatch)
        args = _ns(
            control_command="run",
            control_run_command="release",
            run_id=run_id,
            reason="",
        )
        rc = handle_control_command(args, tmp_path)
        assert rc == 0
        assert "Released run" in capsys.readouterr().out
