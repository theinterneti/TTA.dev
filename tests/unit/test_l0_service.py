"""Unit tests for the local L0 control-plane service."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ttadev.control_plane import ControlPlaneService, RunStatus, TaskClaimError, TaskStatus
from ttadev.control_plane.models import WorkflowGateDecisionOutcome
from ttadev.observability.session_manager import SessionManager
from ttadev.observability.span_processor import ProcessedSpan


def test_create_task_with_project(tmp_path) -> None:
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Create queue",
        description="Need a local queue",
        project_name="alpha",
        requested_role="developer",
    )
    assert task.project_name == "alpha"
    assert task.project_id is not None
    assert task.requested_role == "developer"


def test_claim_task_creates_run_and_lease(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Implement lease handling")

    claim = service.claim_task(task.id, agent_role="developer", lease_ttl_seconds=60)

    assert claim.task.status == TaskStatus.IN_PROGRESS
    assert claim.run.status == RunStatus.ACTIVE
    assert claim.run.agent_id == "agent-1"
    assert claim.lease.holder_agent_id == "agent-1"


def test_second_agent_cannot_claim_active_task(monkeypatch, tmp_path) -> None:
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Protect active lease")

    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service.claim_task(task.id, lease_ttl_seconds=60)

    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-2")
    with pytest.raises(TaskClaimError):
        service.claim_task(task.id, lease_ttl_seconds=60)


def test_heartbeat_extends_lease(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Keep lease alive")

    claim = service.claim_task(task.id, lease_ttl_seconds=30)
    renewed = service.heartbeat_run(claim.run.id, lease_ttl_seconds=60)

    assert renewed.expires_at >= claim.lease.expires_at


def test_complete_run_marks_task_completed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Finish work")

    claim = service.claim_task(task.id, lease_ttl_seconds=60)
    run = service.complete_run(claim.run.id, summary="Implemented control plane")
    updated_task = service.get_task(task.id)

    assert run.status == RunStatus.COMPLETED
    assert updated_task.status == TaskStatus.COMPLETED
    assert service.get_lease_for_run(claim.run.id) is None


def test_release_run_returns_task_to_pending(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Release for another agent")

    claim = service.claim_task(task.id, lease_ttl_seconds=60)
    run = service.release_run(claim.run.id, reason="Need another reviewer")
    updated_task = service.get_task(task.id)

    assert run.status == RunStatus.RELEASED
    assert updated_task.status == TaskStatus.PENDING
    assert updated_task.active_run_id is None


def test_claim_task_backfills_session_project_and_ownership(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    session_mgr = SessionManager(tmp_path)
    session = session_mgr.start_session()
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Project task", project_name="alpha", requested_role="developer")

    claim = service.claim_task(task.id, agent_role="developer", lease_ttl_seconds=60)
    ownership = service.list_active_ownership()

    refreshed_session = session_mgr.get_session(session.id)
    assert refreshed_session is not None
    assert refreshed_session.project_id == task.project_id
    assert claim.run.session_id == session.id
    assert len(ownership) == 1
    assert ownership[0]["task"]["id"] == task.id
    assert ownership[0]["run"]["id"] == claim.run.id
    assert ownership[0]["session"] is not None
    assert ownership[0]["session"]["id"] == session.id
    assert ownership[0]["project"] is not None
    assert ownership[0]["project"]["id"] == task.project_id


def test_active_ownership_keeps_partial_linkage_and_excludes_finished_runs(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    service._get_active_session = lambda: None  # type: ignore[method-assign]
    task = service.create_task("Unlinked task")

    claim = service.claim_task(task.id, lease_ttl_seconds=60)
    ownership = service.list_active_ownership()
    assert len(ownership) == 1
    assert ownership[0]["run"]["id"] == claim.run.id
    assert ownership[0]["session"] is None
    assert ownership[0]["project"] is None
    assert ownership[0]["workflow"] is None

    service.complete_run(claim.run.id, summary="done")
    assert service.list_active_ownership() == []


def test_active_ownership_includes_concise_session_telemetry(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    session_mgr = SessionManager(tmp_path)
    session = session_mgr.start_session()
    session_mgr.add_span(
        session.id,
        ProcessedSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            name="tool_call",
            provider="GitHub Copilot",
            model="claude-sonnet-4.5",
            agent_role="backend-engineer",
            workflow_id=None,
            primitive_type="RetryPrimitive",
            started_at=datetime.now(UTC).isoformat(),
            duration_ms=0.0,
            status="success",
        ),
    )

    service = ControlPlaneService(tmp_path)
    task = service.create_task("Telemetry task")
    claim = service.claim_task(task.id, lease_ttl_seconds=60)
    ownership = service.list_active_ownership()

    assert ownership[0]["run"]["id"] == claim.run.id
    assert ownership[0]["telemetry"] == {
        "has_recent_activity": True,
        "recent_span_count": 1,
        "recent_action_types": ["tool_call"],
        "recent_agent_roles": ["backend-engineer"],
        "recent_primitive_types": ["RetryPrimitive"],
    }


def test_active_ownership_includes_workflow_summary(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
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
        summary="looks good",
    )
    service.mark_workflow_step_running(claim.task.id, step_index=1)

    ownership = service.list_active_ownership()

    assert len(ownership) == 1
    workflow = ownership[0]["workflow"]
    assert workflow is not None
    assert workflow["workflow_name"] == "feature_dev"
    assert workflow["workflow_goal"] == "ship auth"
    assert workflow["workflow_status"] == "running"
    assert workflow["current_step_number"] == 2
    assert workflow["current_agent"] == "qa"
    assert workflow["current_step"]["agent_name"] == "qa"
    assert workflow["recent_steps"][0]["agent_name"] == "developer"


# ---------------------------------------------------------------------------
# Step timestamp + duration attribution
# ---------------------------------------------------------------------------


def test_step_timestamps_populated(tmp_path) -> None:
    """mark_workflow_step_running sets started_at; record_workflow_step_result sets completed_at."""
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="add login",
        step_agents=["developer"],
    )
    task_id = claim.task.id

    service.mark_workflow_step_running(task_id, step_index=0)
    task = service.get_task(task_id)
    assert task.workflow is not None
    step = task.workflow.steps[0]
    assert step.started_at is not None, "started_at should be set after mark_running"
    assert step.completed_at is None, "completed_at should be None while step is running"

    service.record_workflow_step_result(
        task_id, step_index=0, result_summary="done", confidence=0.9
    )
    task = service.get_task(task_id)
    step = task.workflow.steps[0]
    assert step.completed_at is not None, "completed_at should be set after record_result"


def test_step_duration_helper_known_timestamps() -> None:
    """_step_duration returns correctly formatted duration for known ISO timestamps."""
    from ttadev.cli.control import _step_duration

    started = "2026-03-26T10:00:00+00:00"
    completed = "2026-03-26T10:00:02.500000+00:00"
    assert _step_duration(started, completed) == "2.5s"


def test_step_duration_helper_missing_start() -> None:
    """_step_duration returns '-' when started_at is None."""
    from ttadev.cli.control import _step_duration

    assert _step_duration(None, None) == "-"
    assert _step_duration(None, "2026-03-26T10:00:00+00:00") == "-"


def test_step_duration_helper_in_progress() -> None:
    """_step_duration uses current time when completed_at is absent."""
    from ttadev.cli.control import _step_duration

    started = datetime.now(UTC).isoformat()
    result = _step_duration(started, None)
    assert result.endswith("s")
    assert float(result[:-1]) >= 0.0


# ── workflow auto-finalization ────────────────────────────────────────────────


def test_complete_run_auto_finalizes_workflow_when_all_steps_completed(
    tmp_path,
    monkeypatch,
) -> None:
    """complete_run sets workflow.status=COMPLETED when all steps are COMPLETED."""
    from ttadev.control_plane.models import WorkflowStepStatus, WorkflowTrackingStatus
    from ttadev.observability import agent_identity

    monkeypatch.setattr(agent_identity, "_AGENT_ID", "agent-a")
    monkeypatch.setenv("TTA_AGENT_TOOL", "copilot")

    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="auto-fin",
        workflow_goal="prove auto-finalize",
        step_agents=["agent-a"],
    )
    task_id = claim.run.task_id
    run_id = claim.run.id

    service.mark_workflow_step_running(task_id, step_index=0)
    service.record_workflow_step_result(
        task_id, step_index=0, result_summary="done", confidence=1.0
    )

    service.complete_run(run_id, summary="all done")

    task = service.get_task(task_id)
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.COMPLETED
    assert task.workflow.steps[0].status == WorkflowStepStatus.COMPLETED


def test_complete_run_does_not_auto_finalize_when_steps_not_all_terminal(
    tmp_path,
    monkeypatch,
) -> None:
    """complete_run leaves workflow.status=RUNNING when a step is still PENDING."""
    from ttadev.control_plane.models import WorkflowTrackingStatus
    from ttadev.observability import agent_identity

    monkeypatch.setattr(agent_identity, "_AGENT_ID", "agent-a")
    monkeypatch.setenv("TTA_AGENT_TOOL", "copilot")

    service = ControlPlaneService(tmp_path)
    # Two-step workflow — agent-a only completes step 0
    claim = service.start_tracked_workflow(
        workflow_name="partial",
        workflow_goal="two steps",
        step_agents=["agent-a", "agent-b"],
    )
    task_id = claim.run.task_id
    run_id = claim.run.id

    service.mark_workflow_step_running(task_id, step_index=0)
    service.record_workflow_step_result(
        task_id, step_index=0, result_summary="done", confidence=1.0
    )
    # Release rather than complete so agent-b can pick it up (not under test here)
    service.release_run(run_id, reason="handoff")

    # Simulate agent-b picking up and completing without touching step 1
    monkeypatch.setattr(agent_identity, "_AGENT_ID", "agent-b")
    claim2 = service.claim_task(task_id)
    # Complete without recording step 1 result (step 1 still PENDING)
    service.complete_run(claim2.run.id, summary="premature complete")

    task = service.get_task(task_id)
    assert task.workflow is not None
    # Step 1 is still PENDING — workflow should NOT be auto-finalized
    assert task.workflow.status == WorkflowTrackingStatus.RUNNING
