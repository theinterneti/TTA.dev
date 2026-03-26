"""Integration proof: 3-agent feature_dev workflow with L0 tracking.

This test is the Phase 2 success criterion:
  one documented, repeatable multi-agent workflow that stays green.

It mirrors the CLI path:
  tta workflow run feature_dev --goal "..." --track-l0 --no-confirm
  tta control task show <task_id>

Uses MockChatPrimitive so no API keys are required — CI-safe.
"""

from __future__ import annotations

import pytest

from tests.fakes import MockChatPrimitive
from ttadev.agents.developer import DeveloperAgent
from ttadev.agents.qa import QAAgent
from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.security import SecurityAgent
from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import WorkflowTrackingStatus
from ttadev.primitives.core.base import WorkflowContext
from ttadev.workflows.definition import MemoryConfig, WorkflowDefinition, WorkflowStep
from ttadev.workflows.orchestrator import WorkflowGoal, WorkflowOrchestrator


@pytest.mark.asyncio
async def test_feature_dev_with_l0_tracking(tmp_path: object) -> None:
    """3-agent workflow runs end-to-end with L0 task/step tracking."""
    mock = MockChatPrimitive("Feature implemented successfully.")

    # Register real agent classes with a mock model factory
    registry = AgentRegistry()
    for cls in (DeveloperAgent, QAAgent, SecurityAgent):
        registry.register(cls._class_spec.name, cls)

    service = ControlPlaneService(tmp_path)  # type: ignore[arg-type]

    defn = WorkflowDefinition(
        name="feature_dev",
        description="proof: 3-step multi-agent workflow",
        steps=[
            WorkflowStep(agent="developer"),
            WorkflowStep(agent="qa"),
            WorkflowStep(agent="security"),
        ],
        auto_approve=True,  # mirrors --no-confirm
        memory_config=MemoryConfig(flush_to_persistent=False),
    )

    with override_registry(registry):
        orch = WorkflowOrchestrator(
            defn,
            control_plane_service=service,
            track_in_control_plane=True,
            model_factory=lambda: mock,
        )
        result = await orch.execute(
            WorkflowGoal(goal="Add password reset flow"),
            WorkflowContext(),
        )

    # --- Workflow-level assertions ---
    assert result.completed, "workflow should complete all 3 steps"
    assert len(result.steps) == 3
    assert result.tracked_task_id is not None
    assert result.tracked_run_id is not None

    # --- L0 control plane assertions ---
    task = service.get_task(result.tracked_task_id)
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.COMPLETED
    assert len(task.workflow.steps) == 3

    agents_run = [s.agent_name for s in task.workflow.steps]
    assert agents_run == ["developer", "qa", "security"]

    for step in task.workflow.steps:
        assert step.last_result_summary is not None, (
            f"step {step.agent_name} missing result_summary"
        )
        assert step.last_confidence is not None and step.last_confidence > 0


@pytest.mark.asyncio
async def test_feature_dev_failed_step_recorded(tmp_path: object) -> None:
    """A step that raises records FAILED status on the L0 task."""
    from ttadev.agents.spec import AgentSpec
    from ttadev.agents.task import AgentResult, AgentTask

    class _BoomAgent:
        _class_spec = AgentSpec(
            name="developer",
            role="developer",
            system_prompt="",
            capabilities=[],
            tools=[],
            quality_gates=[],
            handoff_triggers=[],
        )

        def __init__(self, model: object = None) -> None:  # noqa: ARG002
            pass

        async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
            raise RuntimeError("simulated failure")

    registry = AgentRegistry()
    registry.register("developer", _BoomAgent)

    service = ControlPlaneService(tmp_path)  # type: ignore[arg-type]
    defn = WorkflowDefinition(
        name="feature_dev",
        description="failure proof",
        steps=[WorkflowStep(agent="developer")],
        auto_approve=True,
    )

    with override_registry(registry), pytest.raises(RuntimeError, match="simulated failure"):
        orch = WorkflowOrchestrator(
            defn,
            control_plane_service=service,
            track_in_control_plane=True,
        )
        await orch.execute(WorkflowGoal(goal="boom"), WorkflowContext())

    # L0 task should be finalized as FAILED
    tasks = service.list_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.workflow is not None
    assert task.workflow.status == WorkflowTrackingStatus.FAILED
