"""Integration test — multi-agent SDD workflow end-to-end via L0 control plane.

Exercises the full happy-path described in docs/workflows/multi-agent-sdd.md:
  1. Start workflow (creates task + run + gates)
  2. Activate step 0 (architect)
  3. Record step 0 result
  4. Record gate decision (continue)
  5. Repeat for steps 1–3
  6. Final status shows all steps DONE

Also verifies the ``attach_workflow_to_task`` path (``--task-id`` flag):
  - Create a task first
  - Attach workflow tracking to it
  - Confirm workflow is present and steps/gates are wired

All storage is in a temp directory; no external services required.
"""

from __future__ import annotations

import pytest

from ttadev.control_plane.models import (
    WorkflowGateDecisionOutcome,
    WorkflowStepStatus,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.service import ControlPlaneService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def svc(tmp_path: pytest.TempPathFactory) -> ControlPlaneService:
    """Return a ControlPlaneService backed by an isolated temp store."""
    return ControlPlaneService(data_dir=str(tmp_path))


_AGENTS = ["architect", "backend-engineer", "testing-specialist", "devops-engineer"]


# ---------------------------------------------------------------------------
# Happy path (start_tracked_workflow)
# ---------------------------------------------------------------------------


def test_full_sdd_workflow_happy_path(svc: ControlPlaneService) -> None:
    """Walk through all four SDD steps and verify final status."""
    claim = svc.start_tracked_workflow(
        workflow_name="sdd-example",
        workflow_goal="Add CachePrimitive metrics integration",
        step_agents=_AGENTS,
    )
    task_id = claim.run.task_id

    wf = svc.get_task(task_id)
    assert wf is not None
    assert wf.workflow is not None
    assert wf.workflow.total_steps == 4
    assert wf.workflow.status == WorkflowTrackingStatus.RUNNING

    for step_index in range(len(_AGENTS)):
        # Activate step
        svc.mark_workflow_step_running(task_id, step_index=step_index)
        info = svc.explain_active_step(task_id)
        assert info is not None
        assert info.step_index == step_index
        assert info.agent_name == _AGENTS[step_index]

        # Record result
        svc.record_workflow_step_result(
            task_id,
            step_index=step_index,
            result_summary=f"step {step_index} done",
            confidence=0.9,
        )

        # Approve the gate for this step
        svc.record_workflow_gate_outcome(
            task_id,
            step_index=step_index,
            decision=WorkflowGateDecisionOutcome.CONTINUE,
            summary="approved",
        )

    # All steps should be DONE
    final_task = svc.get_task(task_id)
    assert final_task is not None
    assert final_task.workflow is not None
    for step in final_task.workflow.steps:
        assert step.status == WorkflowStepStatus.COMPLETED, f"Step {step.step_index} not COMPLETED"


# ---------------------------------------------------------------------------
# attach_workflow_to_task path
# ---------------------------------------------------------------------------


def test_attach_workflow_to_existing_task(svc: ControlPlaneService) -> None:
    """Attaching workflow tracking to a pre-existing task wires steps and gates."""
    # Create a task first (simulates user-created task before knowing workflow shape)
    task = svc.create_task(
        title="Add CachePrimitive metrics integration",
        description="Full feature work from spec to deploy",
        gates=[
            {"id": "initial-review", "gate_type": "approval", "label": "Initial review"},
        ],
    )
    task_id = task.id

    # Attach workflow tracking
    claim = svc.attach_workflow_to_task(
        task_id,
        workflow_name="sdd-example",
        workflow_goal="Add CachePrimitive metrics integration",
        step_agents=_AGENTS,
    )
    assert claim.run.task_id == task_id

    updated_task = svc.get_task(task_id)
    assert updated_task is not None
    assert updated_task.workflow is not None
    assert updated_task.workflow.total_steps == 4
    assert len(updated_task.workflow.steps) == 4

    # Activating step 0 should work
    svc.mark_workflow_step_running(task_id, step_index=0)
    info = svc.explain_active_step(task_id)
    assert info is not None
    assert info.agent_name == "architect"


def test_attach_workflow_prevents_double_attach(svc: ControlPlaneService) -> None:
    """Attaching twice to the same task raises an error."""
    from ttadev.control_plane.service import ControlPlaneError

    task = svc.create_task(title="Double attach test", description="")
    svc.attach_workflow_to_task(
        task.id,
        workflow_name="wf1",
        workflow_goal="goal",
        step_agents=["architect"],
    )
    with pytest.raises(ControlPlaneError, match="already has workflow"):
        svc.attach_workflow_to_task(
            task.id,
            workflow_name="wf2",
            workflow_goal="goal2",
            step_agents=["backend-engineer"],
        )


# ---------------------------------------------------------------------------
# Abort path
# ---------------------------------------------------------------------------


def test_workflow_step_fail_marks_step_failed(svc: ControlPlaneService) -> None:
    """Failing a step records the error and marks the step as FAILED."""
    claim = svc.start_tracked_workflow(
        workflow_name="abort-test",
        workflow_goal="test abort",
        step_agents=["architect", "backend-engineer"],
    )
    task_id = claim.run.task_id

    svc.mark_workflow_step_running(task_id, step_index=0)
    svc.mark_workflow_step_failed(task_id, step_index=0, error_summary="Spec review blocked")

    task = svc.get_task(task_id)
    assert task is not None
    assert task.workflow is not None
    assert task.workflow.steps[0].status == WorkflowStepStatus.FAILED
    assert "Spec review blocked" in (task.workflow.steps[0].last_result_summary or "")
