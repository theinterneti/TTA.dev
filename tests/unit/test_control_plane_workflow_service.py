"""Unit tests for tracked workflow control-plane behavior."""

from __future__ import annotations

from pathlib import Path

from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import (
    GateStatus,
    RunStatus,
    TaskRecord,
    WorkflowGateDecisionOutcome,
    WorkflowStepStatus,
    WorkflowTrackingStatus,
)


def test_tracked_workflow_round_trips_on_task_serialization() -> None:
    """Workflow metadata survives task JSON serialization."""
    task_payload = {
        "id": "task_workflow",
        "title": "Workflow task",
        "description": "Tracked workflow",
        "created_at": "2026-03-24T00:00:00+00:00",
        "updated_at": "2026-03-24T00:00:00+00:00",
        "status": "in_progress",
        "priority": "normal",
        "workflow": {
            "workflow_name": "feature_dev",
            "workflow_goal": "ship auth",
            "total_steps": 2,
            "status": "running",
            "current_step_index": 0,
            "current_agent": "developer",
            "steps": [
                {
                    "step_index": 0,
                    "agent_name": "developer",
                    "status": "completed",
                    "linked_gate_id": "workflow-step-1-developer",
                    "attempts": 1,
                    "started_at": "2026-03-24T00:00:00+00:00",
                    "completed_at": "2026-03-24T00:01:00+00:00",
                    "last_result_summary": "developer output",
                    "last_confidence": 0.8,
                    "gate_decision": "continue",
                    "gate_history": [
                        {
                            "decision": "continue",
                            "occurred_at": "2026-03-24T00:01:00+00:00",
                            "summary": "approved",
                        }
                    ],
                }
            ],
        },
        "gates": [],
    }

    round_tripped = TaskRecord.from_dict(task_payload).to_dict()

    assert round_tripped["workflow"]["workflow_name"] == "feature_dev"
    assert round_tripped["workflow"]["steps"][0]["gate_decision"] == "continue"
    assert round_tripped["workflow"]["steps"][0]["gate_history"][0]["decision"] == "continue"


def test_start_and_finalize_tracked_workflow(tmp_path: Path) -> None:
    """Tracked workflow helpers create one task/run pair and persist step state."""
    service = ControlPlaneService(tmp_path)

    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="ship auth",
        step_agents=["developer", "qa"],
    )
    assert claim.task.workflow is not None
    assert claim.task.workflow.workflow_name == "feature_dev"
    assert claim.task.workflow.total_steps == 2
    assert claim.run.status == RunStatus.ACTIVE

    task = service.mark_workflow_step_running(claim.task.id, step_index=0)
    assert task.workflow is not None
    assert task.workflow.current_step_index == 0
    assert task.workflow.steps[0].status.value == "running"
    assert task.workflow.steps[0].attempts == 1

    task = service.record_workflow_step_result(
        claim.task.id,
        step_index=0,
        result_summary="developer output",
        confidence=0.9,
    )
    assert task.workflow is not None
    assert task.workflow.steps[0].last_result_summary == "developer output"
    assert task.workflow.steps[0].last_confidence == 0.9

    task = service.record_workflow_gate_outcome(
        claim.task.id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.CONTINUE,
        summary="looks good",
    )
    assert task.workflow is not None
    assert task.workflow.steps[0].status.value == "completed"
    assert task.workflow.steps[0].gate_decision == WorkflowGateDecisionOutcome.CONTINUE
    assert task.workflow.steps[0].gate_history[-1].decision == WorkflowGateDecisionOutcome.CONTINUE
    assert task.gates[0].status.value == "approved"

    run = service.finalize_tracked_workflow(
        claim.task.id,
        claim.run.id,
        status=WorkflowTrackingStatus.COMPLETED,
        summary="workflow done",
    )
    assert run.status == RunStatus.COMPLETED

    persisted_task = service.get_task(claim.task.id)
    assert persisted_task.status.value == "completed"
    assert persisted_task.workflow is not None
    assert persisted_task.workflow.status == WorkflowTrackingStatus.COMPLETED
    assert persisted_task.workflow.current_step_index is None


def test_quit_tracked_workflow_releases_run_without_gate_completion(tmp_path: Path) -> None:
    """Quit finalization keeps workflow state inspectable without forcing gate completion."""
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="feature_dev",
        workflow_goal="ship auth",
        step_agents=["developer", "qa"],
    )

    task = service.record_workflow_gate_outcome(
        claim.task.id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.QUIT,
        summary="stop here",
    )
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.QUIT
    assert task.workflow.steps[0].status.value == "quit"

    run = service.finalize_tracked_workflow(
        claim.task.id,
        claim.run.id,
        status=WorkflowTrackingStatus.QUIT,
        summary="workflow quit",
    )
    assert run.status == RunStatus.RELEASED

    persisted_task = service.get_task(claim.task.id)
    assert persisted_task.status.value == "pending"
    assert persisted_task.workflow is not None
    assert persisted_task.workflow.status == WorkflowTrackingStatus.QUIT


def test_escalate_to_human_is_a_valid_gate_outcome() -> None:
    """ESCALATE_TO_HUMAN gate outcome enum value exists."""
    assert WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN is not None
    assert WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN.value == "escalate_to_human"


def test_escalated_is_a_valid_workflow_status() -> None:
    """ESCALATED workflow status enum value exists."""
    assert WorkflowTrackingStatus.ESCALATED is not None
    assert WorkflowTrackingStatus.ESCALATED.value == "escalated"


async def test_escalate_to_human_pauses_workflow(tmp_path: Path) -> None:
    """ESCALATE_TO_HUMAN gate outcome pauses the workflow without advancing the step."""
    # Arrange
    svc = ControlPlaneService(data_dir=tmp_path)
    claim = svc.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="test escalation",
        step_agents=["agent-a", "agent-b"],
    )
    task_id = claim.task.id

    svc.mark_workflow_step_running(task_id, step_index=0)
    svc.record_workflow_step_result(task_id, step_index=0, result_summary="done", confidence=0.5)

    # Act — record ESCALATE_TO_HUMAN outcome
    task = svc.record_workflow_gate_outcome(
        task_id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN,
        summary="Low confidence — needs human review",
    )

    # Assert — workflow is paused, not advanced
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.ESCALATED
    assert task.workflow.steps[0].status == WorkflowStepStatus.RUNNING
    # Step 1 has NOT started
    assert task.workflow.steps[1].status == WorkflowStepStatus.PENDING


async def test_workflow_resumes_after_human_approves_escalated_gate(tmp_path: Path) -> None:
    """Workflow status returns to RUNNING when a human approves the gate after escalation."""
    # Arrange
    svc = ControlPlaneService(data_dir=tmp_path)
    claim = svc.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="test escalation resume",
        step_agents=["agent-a", "agent-b"],
    )
    task_id = claim.task.id

    svc.mark_workflow_step_running(task_id, step_index=0)
    svc.record_workflow_step_result(task_id, step_index=0, result_summary="done", confidence=0.5)
    svc.record_workflow_gate_outcome(
        task_id,
        step_index=0,
        decision=WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN,
        summary="needs human",
    )

    # Act — human approves via the standard gate mechanism
    task = svc.get_task(task_id)
    assert task.workflow is not None
    gate_id = task.workflow.steps[0].linked_gate_id
    assert gate_id is not None  # narrow str | None → str for type checker
    task = svc.decide_gate(
        task_id,
        gate_id,
        status=GateStatus.APPROVED,
        decided_by="human-reviewer",
        summary="Looks good",
    )

    # Assert — workflow status restored to RUNNING after human approval; step still RUNNING
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.RUNNING
    assert task.workflow.steps[0].status == WorkflowStepStatus.RUNNING


async def test_expire_abandoned_workflow_marks_step_and_workflow_failed(tmp_path: Path) -> None:
    # Arrange
    import asyncio

    svc = ControlPlaneService(data_dir=tmp_path)
    claim = svc.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="test abandonment",
        step_agents=["agent-a"],
        lease_ttl_seconds=0.01,
    )
    task_id = claim.task.id

    svc.mark_workflow_step_running(task_id, step_index=0)

    # Wait for lease to expire
    await asyncio.sleep(0.05)

    # Act — expire abandoned workflows
    affected = svc.expire_abandoned_workflows()

    # Assert
    assert task_id in affected
    task = svc.get_task(task_id)
    assert task is not None
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.FAILED
    assert task.workflow.steps[0].status == WorkflowStepStatus.FAILED
