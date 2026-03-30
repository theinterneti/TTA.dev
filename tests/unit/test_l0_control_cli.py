"""Unit tests for the ``tta control`` CLI surface."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run(
    args: list[str], tmp_path: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parents[2]
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = f"{repo_root}:{merged_env.get('PYTHONPATH', '')}".rstrip(":")
    merged_env["PYTHONUTF8"] = "1"  # PEP 540: force UTF-8 stdout on Windows (cp1252 breaks ≥/emoji)
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", "--data-dir", str(tmp_path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=merged_env,
        cwd=repo_root,
    )


def _parse_prefixed_value(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"Missing line with prefix {prefix!r} in output: {output}")


def test_control_help_lists_task_and_run(tmp_path: Path) -> None:
    result = _run(["control", "--help"], tmp_path)
    assert result.returncode == 0
    assert "task" in result.stdout
    assert "run" in result.stdout


def test_task_create_and_list(tmp_path: Path) -> None:
    created = _run(
        [
            "control",
            "task",
            "create",
            "Build L0 queue",
            "--description",
            "Create the first local queue",
            "--project",
            "alpha",
        ],
        tmp_path,
    )
    assert created.returncode == 0
    assert "Task:" in created.stdout

    listed = _run(["control", "task", "list"], tmp_path)
    assert listed.returncode == 0
    assert "Build L0 queue" in listed.stdout
    assert "alpha" in listed.stdout


def test_task_show_and_claim_then_complete(tmp_path: Path) -> None:
    created = _run(["control", "task", "create", "Claim me"], tmp_path)
    task_id = _parse_prefixed_value(created.stdout, "Task")

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert task_id in shown.stdout

    claimed = _run(
        ["control", "task", "claim", task_id, "--role", "developer"],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert claimed.returncode == 0
    run_id = _parse_prefixed_value(claimed.stdout, "Run")

    runs = _run(["control", "run", "list"], tmp_path)
    assert runs.returncode == 0
    assert run_id in runs.stdout

    completed = _run(
        ["control", "run", "complete", run_id, "--summary", "done"],
        tmp_path,
    )
    assert completed.returncode == 0

    shown_again = _run(["control", "task", "show", task_id], tmp_path)
    assert shown_again.returncode == 0
    assert "completed" in shown_again.stdout


def test_gated_task_requires_decision_before_completion(tmp_path: Path) -> None:
    created = _run(
        [
            "control",
            "task",
            "create",
            "Ship gated change",
            "--gate",
            "approval:approval:required:Human approval",
        ],
        tmp_path,
    )
    assert created.returncode == 0
    task_id = _parse_prefixed_value(created.stdout, "Task")

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert "Human approval" in shown.stdout
    assert "pending" in shown.stdout

    claimed = _run(
        ["control", "task", "claim", task_id],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert claimed.returncode == 0
    run_id = _parse_prefixed_value(claimed.stdout, "Run")

    blocked = _run(["control", "run", "complete", run_id], tmp_path)
    assert blocked.returncode == 1
    assert "approval" in blocked.stderr.lower()

    decided = _run(
        [
            "control",
            "task",
            "decide-gate",
            task_id,
            "approval",
            "--status",
            "approved",
            "--by",
            "reviewer-1",
            "--summary",
            "looks good",
        ],
        tmp_path,
    )
    assert decided.returncode == 0
    assert "approved" in decided.stdout

    completed = _run(
        ["control", "run", "complete", run_id, "--summary", "done"],
        tmp_path,
    )
    assert completed.returncode == 0


def test_assigned_gate_requires_matching_cli_identity_or_role(tmp_path: Path) -> None:
    """Show gate assignments and reject unauthorized CLI gate decisions."""
    created = _run(
        [
            "control",
            "task",
            "create",
            "Assigned gated change",
            "--gate",
            "review:review:required:Code review",
            "--gate-assign-role",
            "review:reviewer",
            "--gate-assign-decider",
            "review:reviewer-1",
        ],
        tmp_path,
    )
    assert created.returncode == 0
    task_id = _parse_prefixed_value(created.stdout, "Task")

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert "assigned_role=reviewer" in shown.stdout
    assert "assigned_decider=reviewer-1" in shown.stdout

    blocked = _run(
        [
            "control",
            "task",
            "decide-gate",
            task_id,
            "review",
            "--status",
            "approved",
        ],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert blocked.returncode == 1
    assert "reviewer-1" in blocked.stderr or "reviewer" in blocked.stderr

    decided = _run(
        [
            "control",
            "task",
            "decide-gate",
            task_id,
            "review",
            "--status",
            "approved",
            "--by",
            "reviewer-1",
            "--role",
            "reviewer",
        ],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert decided.returncode == 0
    assert "approved" in decided.stdout


def test_changes_requested_requires_reopen_before_cli_completion(tmp_path: Path) -> None:
    """Gate lifecycle supports changes_requested and explicit reopen on the CLI."""
    created = _run(
        [
            "control",
            "task",
            "create",
            "Lifecycle gated change",
            "--gate",
            "review:review:required:Code review",
        ],
        tmp_path,
    )
    assert created.returncode == 0
    task_id = _parse_prefixed_value(created.stdout, "Task")

    claimed = _run(
        ["control", "task", "claim", task_id],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert claimed.returncode == 0
    run_id = _parse_prefixed_value(claimed.stdout, "Run")

    changes = _run(
        [
            "control",
            "task",
            "decide-gate",
            task_id,
            "review",
            "--status",
            "changes_requested",
            "--summary",
            "needs updates",
        ],
        tmp_path,
    )
    assert changes.returncode == 0
    assert "changes_requested" in changes.stdout

    blocked_completion = _run(["control", "run", "complete", run_id], tmp_path)
    assert blocked_completion.returncode == 1
    assert "review" in blocked_completion.stderr.lower()

    blocked_direct_approve = _run(
        [
            "control",
            "task",
            "decide-gate",
            task_id,
            "review",
            "--status",
            "approved",
        ],
        tmp_path,
    )
    assert blocked_direct_approve.returncode == 1
    assert "without reopen" in blocked_direct_approve.stderr

    reopened = _run(
        ["control", "task", "reopen-gate", task_id, "review"],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert reopened.returncode == 0
    assert "pending" in reopened.stdout

    approved = _run(
        [
            "control",
            "task",
            "decide-gate",
            task_id,
            "review",
            "--status",
            "approved",
        ],
        tmp_path,
    )
    assert approved.returncode == 0

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert "history:" in shown.stdout
    assert "decision pending -> changes_requested" in shown.stdout
    assert "reopened changes_requested -> pending" in shown.stdout
    assert "decision pending -> approved" in shown.stdout

    completed = _run(["control", "run", "complete", run_id, "--summary", "done"], tmp_path)
    assert completed.returncode == 0


def test_task_show_renders_tracked_workflow_metadata(tmp_path: Path) -> None:
    """Tracked workflow tasks show per-step state in the control CLI."""
    from ttadev.control_plane import ControlPlaneService
    from ttadev.control_plane.models import WorkflowGateDecisionOutcome

    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="ship auth",
        step_agents=["developer", "qa"],
    )
    service.mark_workflow_step_running(claim.task.id, step_index=0)
    service.record_workflow_step_result(
        claim.task.id,
        step_index=0,
        result_summary="developer output",
        confidence=0.9,
    )
    service.record_workflow_gate_outcome(
        claim.task.id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.CONTINUE,
        summary="approved",
    )

    shown = _run(["control", "task", "show", claim.task.id], tmp_path)
    assert shown.returncode == 0
    assert "workflow:" in shown.stdout
    assert "name:              feature_dev" in shown.stdout
    assert "1. developer status=completed" in shown.stdout
    assert "gate_history:" in shown.stdout


def test_task_show_renders_step_duration(tmp_path: Path) -> None:
    """Completed steps include a non-zero duration= field in task show output."""
    from ttadev.control_plane import ControlPlaneService

    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="add auth",
        step_agents=["developer"],
    )
    service.mark_workflow_step_running(claim.task.id, step_index=0)
    service.record_workflow_step_result(
        claim.task.id,
        step_index=0,
        result_summary="done",
        confidence=0.85,
    )

    shown = _run(["control", "task", "show", claim.task.id], tmp_path)
    assert shown.returncode == 0
    # duration= should appear and end with 's' (e.g. "0.0s", "0.1s")
    assert "duration=" in shown.stdout
    duration_token = next(tok for tok in shown.stdout.split() if tok.startswith("duration="))
    duration_val = duration_token.split("=", 1)[1]
    assert duration_val.endswith("s")
    assert float(duration_val[:-1]) >= 0.0


def test_task_show_renders_running_step_duration(tmp_path: Path) -> None:
    """Running steps show an elapsed duration= (not '-') in task show output."""
    from ttadev.control_plane import ControlPlaneService

    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="add search",
        step_agents=["qa"],
    )
    service.mark_workflow_step_running(claim.task.id, step_index=0)

    shown = _run(["control", "task", "show", claim.task.id], tmp_path)
    assert shown.returncode == 0
    assert "duration=" in shown.stdout
    duration_token = next(tok for tok in shown.stdout.split() if tok.startswith("duration="))
    duration_val = duration_token.split("=", 1)[1]
    assert duration_val.endswith("s")
    assert float(duration_val[:-1]) >= 0.0


def test_task_show_renders_policy_name_for_auto_gate(tmp_path: Path) -> None:
    """AC5/AC6: gate_history entry with policy_name shows policy= in task show output."""
    from ttadev.control_plane import ControlPlaneService
    from ttadev.control_plane.models import WorkflowGateDecisionOutcome

    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="add metrics",
        step_agents=["developer"],
    )
    task_id = claim.task.id
    service.mark_workflow_step_running(task_id, step_index=0)
    service.record_workflow_step_result(
        task_id, step_index=0, result_summary="done", confidence=0.92
    )
    # Record gate outcome with an auto policy_name (as the orchestrator would)
    service.record_workflow_gate_outcome(
        task_id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.CONTINUE,
        policy_name="auto:confidence≥0.9",
    )

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert "policy=auto:confidence≥0.9" in shown.stdout


def test_task_show_no_policy_for_human_gate(tmp_path: Path) -> None:
    """Human gate decisions do not include policy= in task show output."""
    from ttadev.control_plane import ControlPlaneService
    from ttadev.control_plane.models import WorkflowGateDecisionOutcome

    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="add search",
        step_agents=["developer"],
    )
    task_id = claim.task.id
    service.mark_workflow_step_running(task_id, step_index=0)
    service.record_workflow_step_result(
        task_id, step_index=0, result_summary="done", confidence=0.7
    )
    # Human decision — no policy_name
    service.record_workflow_gate_outcome(
        task_id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.CONTINUE,
    )

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert "gate_history:" in shown.stdout
    assert "policy=" not in shown.stdout


def test_lock_declared_task_claims_and_lists_locks(tmp_path: Path) -> None:
    """Declare task locks, auto-acquire on claim, then inspect and release them."""
    created = _run(
        [
            "control",
            "task",
            "create",
            "Lock me",
            "--workspace-lock",
            "alpha-workspace",
            "--file-lock",
            "./src\\main.py",
        ],
        tmp_path,
    )
    assert created.returncode == 0
    task_id = _parse_prefixed_value(created.stdout, "Task")
    assert "workspace_locks: alpha-workspace" in created.stdout
    assert "file_locks: src/main.py" in created.stdout

    claimed = _run(
        ["control", "task", "claim", task_id],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert claimed.returncode == 0
    run_id = _parse_prefixed_value(claimed.stdout, "Run")

    listed = _run(["control", "lock", "list"], tmp_path)
    assert listed.returncode == 0
    assert "alpha-workspace" in listed.stdout
    assert "src/main.py" in listed.stdout
    assert run_id in listed.stdout

    workspace_lock_id = next(
        line.split()[0]
        for line in listed.stdout.splitlines()
        if "alpha-workspace" in line and "workspace" in line
    )
    released = _run(["control", "lock", "release", workspace_lock_id], tmp_path)
    assert released.returncode == 0
    assert workspace_lock_id in released.stdout


def test_claim_fails_when_declared_lock_conflicts(tmp_path: Path) -> None:
    """Reject a second claim when a declared workspace lock is already held."""
    first = _run(
        [
            "control",
            "task",
            "create",
            "First lock holder",
            "--workspace-lock",
            "shared-workspace",
        ],
        tmp_path,
    )
    first_task_id = _parse_prefixed_value(first.stdout, "Task")
    first_claim = _run(
        ["control", "task", "claim", first_task_id],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-1", "TTA_AGENT_TOOL": "copilot"},
    )
    assert first_claim.returncode == 0

    second = _run(
        [
            "control",
            "task",
            "create",
            "Second lock holder",
            "--workspace-lock",
            "shared-workspace",
        ],
        tmp_path,
    )
    second_task_id = _parse_prefixed_value(second.stdout, "Task")

    blocked = _run(
        ["control", "task", "claim", second_task_id],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-2", "TTA_AGENT_TOOL": "copilot"},
    )
    assert blocked.returncode == 1
    assert "shared-workspace" in blocked.stderr

    shown = _run(["control", "task", "show", second_task_id], tmp_path)
    assert shown.returncode == 0
    assert "status:         pending" in shown.stdout
