"""WorkflowOrchestrator — executes a WorkflowDefinition step-by-step."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

from ttadev.agents.task import AgentTask
from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import WorkflowGateDecisionOutcome, WorkflowTrackingStatus
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability.instrumented_primitive import InstrumentedPrimitive
from ttadev.workflows.definition import (
    StepResult,
    WorkflowDefinition,
    WorkflowResult,
)
from ttadev.workflows.gate import ApprovalGate, GateDecision
from ttadev.workflows.memory import PersistentMemory, WorkflowMemory

_log = logging.getLogger(__name__)


@dataclass
class WorkflowGoal:
    """Input type for WorkflowOrchestrator."""

    goal: str
    context: dict[str, Any] = field(default_factory=dict)


class WorkflowOrchestrator(InstrumentedPrimitive[WorkflowGoal, WorkflowResult]):
    """Executes a WorkflowDefinition step by step with human approval gates.

    Extends InstrumentedPrimitive — fully composable with >> and |.

    Args:
        definition:        The workflow to run.
        gate:              ApprovalGate instance; defaults to one that respects
                           definition.auto_approve.
        persistent_memory: Optional Hindsight-backed persistent memory.
    """

    def __init__(
        self,
        definition: WorkflowDefinition,
        gate: ApprovalGate | None = None,
        persistent_memory: PersistentMemory | None = None,
        control_plane_service: ControlPlaneService | None = None,
        track_in_control_plane: bool = False,
        control_plane_project_name: str | None = None,
        model_factory: Callable[[], ChatPrimitive] | None = None,
    ) -> None:
        super().__init__(name=f"workflow.{definition.name}")
        self._definition = definition
        self._gate = gate or ApprovalGate(auto_approve=definition.auto_approve)
        self._persistent_memory = persistent_memory
        self._control_plane = control_plane_service
        self._track_in_control_plane = track_in_control_plane
        self._control_plane_project_name = control_plane_project_name
        self._model_factory = model_factory

    async def _execute_impl(self, goal: WorkflowGoal, context: WorkflowContext) -> WorkflowResult:
        defn = self._definition

        # Attach in-context memory to the workflow context
        wf_memory = WorkflowMemory()
        context.memory = wf_memory

        step_results: list[StepResult] = []
        all_artifacts = []
        tracked_task_id: str | None = None
        tracked_run_id: str | None = None

        if self._track_in_control_plane:
            if self._control_plane is None:
                raise RuntimeError(
                    "ControlPlaneService is required when track_in_control_plane=True"
                )
            claim = self._control_plane.start_tracked_workflow(
                workflow_name=defn.name,
                workflow_goal=goal.goal,
                step_agents=[step.agent for step in defn.steps],
                project_name=self._control_plane_project_name,
            )
            tracked_task_id = claim.task.id
            tracked_run_id = claim.run.id

        steps = list(defn.steps)
        i = 0
        try:
            while i < len(steps):
                step = steps[i]
                next_agent = steps[i + 1].agent if i + 1 < len(steps) else None

                if tracked_task_id is not None and self._control_plane is not None:
                    self._control_plane.mark_workflow_step_running(tracked_task_id, step_index=i)

                # Build task — use input_transform if provided, else default
                if step.input_transform is not None:
                    task = step.input_transform(wf_memory.snapshot())
                else:
                    task = AgentTask(
                        instruction=goal.goal,
                        context={**goal.context, "memory": wf_memory.snapshot()},
                        constraints=[],
                    )

                # Execute agent — build child context with memory attached
                from ttadev.agents.registry import get_registry  # deferred

                child_ctx = context.create_child_context()
                child_ctx.memory = wf_memory

                registry = get_registry()
                agent_class = registry.get(step.agent)
                if self._model_factory is not None:
                    agent = agent_class(model=self._model_factory())
                else:
                    agent = agent_class()
                agent_result = await agent.execute(task, child_ctx)

                if tracked_task_id is not None and self._control_plane is not None:
                    self._control_plane.record_workflow_step_result(
                        tracked_task_id,
                        step_index=i,
                        result_summary=agent_result.response[:200],
                        confidence=agent_result.confidence,
                    )

                sr = StepResult(
                    step_index=i,
                    agent_name=step.agent,
                    result=agent_result,
                    gate_decision="continue",
                )

                # Gate check
                if step.gate:
                    decision, edited_instruction = await self._gate.check(
                        sr, total_steps=len(steps), next_agent=next_agent
                    )
                    sr.gate_decision = decision.value

                    if tracked_task_id is not None and self._control_plane is not None:
                        self._control_plane.record_workflow_gate_outcome(
                            tracked_task_id,
                            step_index=i,
                            decision=WorkflowGateDecisionOutcome(decision.value),
                        )

                    if decision == GateDecision.QUIT:
                        step_results.append(sr)
                        break

                    if decision == GateDecision.SKIP:
                        sr.skipped = True
                        step_results.append(sr)
                        i += 1
                        # skip the *next* step
                        if i < len(steps):
                            skipped_step = steps[i]
                            skipped_sr = StepResult(
                                step_index=i,
                                agent_name=skipped_step.agent,
                                result=agent_result,  # carry forward last result
                                skipped=True,
                                gate_decision="skip",
                            )
                            step_results.append(skipped_sr)
                            i += 1
                        continue

                    if decision == GateDecision.EDIT and edited_instruction:
                        # Re-run same step with revised instruction
                        goal = WorkflowGoal(goal=edited_instruction, context=goal.context)
                        continue  # don't advance i

                # Store result and advance
                step_results.append(sr)
                wf_memory.append("step_results", agent_result.response)
                all_artifacts.extend(agent_result.artifacts)
                i += 1
        except Exception as exc:
            if tracked_task_id is not None and self._control_plane is not None:
                self._control_plane.mark_workflow_step_failed(
                    tracked_task_id,
                    step_index=i,
                    error_summary=str(exc),
                )
                if tracked_run_id is not None:
                    self._control_plane.finalize_tracked_workflow(
                        tracked_task_id,
                        tracked_run_id,
                        status=WorkflowTrackingStatus.FAILED,
                        summary=f"Workflow failed: {exc}",
                    )
            raise

        completed = not step_results or step_results[-1].gate_decision != "quit"

        if (
            tracked_task_id is not None
            and self._control_plane is not None
            and tracked_run_id is not None
        ):
            final_status = (
                WorkflowTrackingStatus.COMPLETED if completed else WorkflowTrackingStatus.QUIT
            )
            final_summary = (
                "Workflow completed successfully"
                if completed
                else "Workflow stopped early after quit gate decision"
            )
            self._control_plane.finalize_tracked_workflow(
                tracked_task_id,
                tracked_run_id,
                status=final_status,
                summary=final_summary,
            )

        # Flush to persistent memory if configured
        if defn.memory_config.flush_to_persistent and self._persistent_memory:
            bank_id = defn.memory_config.bank_id or f"tta.workflow.{defn.name}"
            snapshot_str = str(wf_memory.snapshot())
            self._persistent_memory.retain(bank_id, snapshot_str)

        confidences = [sr.result.confidence for sr in step_results if not sr.skipped]
        total_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return WorkflowResult(
            workflow_name=defn.name,
            goal=goal.goal,
            steps=step_results,
            artifacts=all_artifacts,
            memory_snapshot=wf_memory.snapshot(),
            completed=completed,
            total_confidence=total_confidence,
            tracked_task_id=tracked_task_id,
            tracked_run_id=tracked_run_id,
        )
