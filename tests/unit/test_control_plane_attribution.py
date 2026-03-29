"""Unit tests for ControlPlaneService.explain_active_step() and ActiveStepInfo."""

from __future__ import annotations

from pathlib import Path

import pytest

from ttadev.control_plane import ActiveStepInfo, ControlPlaneService
from ttadev.control_plane.models import (
    GateStatus,
    GateType,
    WorkflowStepStatus,
)
from ttadev.control_plane.service import ControlPlaneError, TaskNotFoundError
from ttadev.observability import agent_identity


def _set_agent(monkeypatch: pytest.MonkeyPatch, agent_id: str = "test-agent") -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", "test-tool")


def _make_service(tmp_path: Path) -> ControlPlaneService:
    return ControlPlaneService(tmp_path)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_explain_active_step_task_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raises TaskNotFoundError when the task ID is unknown."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)

    # Act / Assert
    with pytest.raises(TaskNotFoundError, match="not found"):
        service.explain_active_step("task_nonexistent")


def test_explain_active_step_no_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises ControlPlaneError when the task has no associated workflow."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    task = service.create_task("Plain task")

    # Act / Assert
    with pytest.raises(ControlPlaneError, match="no workflow"):
        service.explain_active_step(task.id)


# ---------------------------------------------------------------------------
# Returns None cases
# ---------------------------------------------------------------------------


def test_explain_active_step_no_running_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Returns None when all steps are PENDING (none running yet)."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["agent-a", "agent-b"],
    )
    task_id = claim.run.task_id

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# Happy-path cases
# ---------------------------------------------------------------------------


def test_explain_active_step_running_step_with_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Returns correct ActiveStepInfo with trace_id and span_id when present."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["claude"],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(
        task_id,
        step_index=0,
        trace_id="aabbccdd" * 4,
        span_id="11223344" * 2,
    )

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert isinstance(result, ActiveStepInfo)
    assert result.task_id == task_id
    assert result.step_index == 0
    assert result.agent_name == "claude"
    assert result.trace_id == "aabbccdd" * 4
    assert result.span_id == "11223344" * 2
    assert result.started_at is not None


def test_explain_active_step_running_step_no_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """trace_id and span_id are None when not stamped on the step."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["copilot"],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is not None
    assert result.trace_id is None
    assert result.span_id is None


def test_explain_active_step_started_at_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """duration_s is None when started_at is absent on the step."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["agent-x"],
    )
    task_id = claim.run.task_id

    # Directly mutate the stored step to force status=RUNNING with no started_at
    task = service.get_task(task_id)
    assert task.workflow is not None
    task.workflow.steps[0].status = WorkflowStepStatus.RUNNING
    task.workflow.steps[0].started_at = None
    service._store.put_task(task)

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is not None
    assert result.started_at is None
    assert result.duration_s is None


def test_explain_active_step_duration_positive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """duration_s is a non-negative float when started_at is set."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["agent-y"],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is not None
    assert result.started_at is not None
    assert result.duration_s is not None
    assert result.duration_s >= 0.0


def test_explain_active_step_with_pending_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pending_gate_ids is populated from task-level gates in PENDING state."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["agent-z"],
        extra_gates=[
            {
                "id": "human-review",
                "gate_type": GateType.APPROVAL.value,
                "label": "Human review",
                "required": True,
            }
        ],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is not None
    assert "human-review" in result.pending_gate_ids


def test_explain_active_step_no_pending_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pending_gate_ids is empty when all gates are approved."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["agent-w"],
        extra_gates=[
            {
                "id": "policy-gate",
                "gate_type": GateType.POLICY.value,
                "label": "Policy gate",
                "required": True,
                "policy_name": "auto:always",
            }
        ],
    )
    task_id = claim.run.task_id
    service.mark_workflow_step_running(task_id, step_index=0)
    # record_workflow_step_result triggers policy auto-approval
    service.record_workflow_step_result(
        task_id,
        step_index=0,
        result_summary="done",
        confidence=1.0,
    )
    # Set step back to RUNNING to test the active-step path with no pending gates
    task = service.get_task(task_id)
    assert task.workflow is not None
    task.workflow.steps[0].status = WorkflowStepStatus.RUNNING
    service._store.put_task(task)

    # Verify no gates are pending
    updated_task = service.get_task(task_id)
    assert all(g.status == GateStatus.APPROVED for g in updated_task.gates if g.id == "policy-gate")

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is not None
    # The per-step workflow gate (workflow-step-1-agent-w) was auto-approved too,
    # so none remain pending.
    assert "policy-gate" not in result.pending_gate_ids


def test_explain_active_step_multiple_running_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When multiple steps are RUNNING, returns the one with the highest step_index."""
    # Arrange
    _set_agent(monkeypatch)
    service = _make_service(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="wf",
        workflow_goal="goal",
        step_agents=["agent-1", "agent-2", "agent-3"],
    )
    task_id = claim.run.task_id

    # Force both step 0 and step 2 into RUNNING (abnormal but guarded case)
    task = service.get_task(task_id)
    assert task.workflow is not None
    task.workflow.steps[0].status = WorkflowStepStatus.RUNNING
    task.workflow.steps[0].started_at = "2026-03-28T10:00:00+00:00"
    task.workflow.steps[2].status = WorkflowStepStatus.RUNNING
    task.workflow.steps[2].started_at = "2026-03-28T10:01:00+00:00"
    service._store.put_task(task)

    # Act
    result = service.explain_active_step(task_id)

    # Assert
    assert result is not None
    assert result.step_index == 2
    assert result.agent_name == "agent-3"
