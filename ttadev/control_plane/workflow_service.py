"""Tracked workflow step and gate management for the L0 control plane."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

from ttadev.control_plane.exceptions import ControlPlaneError
from ttadev.control_plane.lease_service import LeaseService
from ttadev.control_plane.models import (
    ClaimResult,
    GateHistoryAction,
    GateHistoryEntry,
    GateRecord,
    GateStatus,
    GateType,
    WorkflowGateDecisionOutcome,
    WorkflowGateDecisionRecord,
    WorkflowStepRecord,
    WorkflowStepStatus,
    WorkflowTrackingRecord,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.run_service import RunService
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.control_plane.task_service import TaskService


def _get_active_otel_context() -> tuple[str | None, str | None]:
    """Return (trace_id_hex, span_id_hex) from the current OTel span, or (None, None)."""
    try:
        from opentelemetry import trace as _otel_trace  # local import to avoid cost at import time
    except ImportError:
        return None, None

    span = _otel_trace.get_current_span()
    ctx = span.get_span_context()
    if ctx is not None and ctx.is_valid:
        return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")

    # Fallback: parse W3C traceparent header from environment.
    # Format: 00-<trace_id_32hex>-<span_id_16hex>-<flags>
    traceparent = os.environ.get("TRACEPARENT", "")
    if traceparent:
        parts = traceparent.split("-")
        if len(parts) == 4 and parts[0] == "00":
            trace_id_hex, span_id_hex = parts[1], parts[2]
            if len(trace_id_hex) == 32 and len(span_id_hex) == 16:
                return trace_id_hex, span_id_hex

    return None, None


@contextlib.contextmanager
def _emit_control_plane_span(
    span_name: str,
    attrs: dict[str, str | int | float | bool] | None = None,
) -> Generator[Any, None, None]:
    """Emit an OTel span for a control-plane operation; yields None when OTel unavailable."""
    try:
        from opentelemetry import trace as _otel_trace

        tracer = _otel_trace.get_tracer("ttadev.control_plane")
        with tracer.start_as_current_span(span_name, attributes=attrs or {}) as span:
            yield span
    except Exception:  # OTel not installed or not initialised — degrade gracefully
        yield None


class WorkflowService:
    """Tracked workflow step creation, execution, gate outcomes, and completion."""

    def __init__(
        self,
        store: ControlPlaneStore,
        task_service: TaskService,
        run_service: RunService,
        lease_service: LeaseService,
    ) -> None:
        self._store = store
        self._task = task_service
        self._run = run_service
        self._lease = lease_service

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _now_iso(self) -> str:
        return self._now().isoformat()

    def _make_workflow_gate_id(self, *, step_index: int, agent_name: str) -> str:
        """Build a stable optional gate ID for a tracked workflow step."""
        normalized_agent = agent_name.strip().replace("_", "-")
        return f"workflow-step-{step_index + 1}-{normalized_agent}"

    def _get_workflow_tracking(self, task_id: str) -> tuple[Any, WorkflowTrackingRecord]:
        """Return (task, workflow) or raise if the task has no workflow."""
        task = self._task.get_task(task_id)
        if task.workflow is None:
            raise ControlPlaneError(f"Task {task.id} is not tracking a workflow")
        return task, task.workflow

    def _get_workflow_step(
        self,
        task_id: str,
        step_index: int,
    ) -> tuple[Any, WorkflowTrackingRecord, WorkflowStepRecord]:
        """Return (task, workflow, step) or raise if step_index is out of range."""
        task, workflow = self._get_workflow_tracking(task_id)
        if step_index < 0 or step_index >= len(workflow.steps):
            raise ControlPlaneError(
                f"Workflow step index {step_index} is out of range for task {task.id}"
            )
        return task, workflow, workflow.steps[step_index]

    def _build_workflow_gate_decision_record(
        self,
        *,
        decision: WorkflowGateDecisionOutcome,
        occurred_at: str,
        summary: str = "",
        policy_name: str | None = None,
    ) -> WorkflowGateDecisionRecord:
        """Create a normalized workflow gate-decision record."""
        return WorkflowGateDecisionRecord(
            decision=decision,
            occurred_at=occurred_at,
            summary=summary or None,
            policy_name=policy_name,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def start_tracked_workflow(
        self,
        *,
        workflow_name: str,
        workflow_goal: str,
        step_agents: list[str],
        project_name: str | None = None,
        extra_gates: list[dict[str, Any]] | None = None,
        lease_ttl_seconds: float = 300.0,
    ) -> ClaimResult:
        """Create and claim a top-level task for a tracked workflow run."""
        if not step_agents:
            raise ControlPlaneError("Tracked workflow must include at least one step")

        with _emit_control_plane_span(
            "tta.l0.workflow.start",
            {
                "l0.workflow_name": workflow_name,
                "l0.total_steps": len(step_agents),
            },
        ) as _span:
            gates: list[dict[str, Any]] = [
                {
                    "id": self._make_workflow_gate_id(step_index=index, agent_name=agent_name),
                    "gate_type": GateType.APPROVAL.value,
                    "label": f"{workflow_name} step {index + 1}: {agent_name}",
                    "required": False,
                }
                for index, agent_name in enumerate(step_agents)
            ]
            if extra_gates:
                gates.extend(extra_gates)
            task = self._task.create_task(
                title=f"Workflow {workflow_name}: {workflow_goal.strip() or workflow_name}",
                description=f"Tracked workflow run for {workflow_name}: {workflow_goal}",
                project_name=project_name,
                requested_role="workflow-orchestrator",
                gates=gates,
            )
            if _span is not None:
                _span.set_attribute("l0.task_id", task.id)
            stored_task = self._store.get_task(task.id)
            if stored_task is None:
                from ttadev.control_plane.exceptions import TaskNotFoundError  # noqa: PLC0415

                raise TaskNotFoundError(f"Task not found after workflow creation: {task.id}")

            stored_task.workflow = WorkflowTrackingRecord(
                workflow_name=workflow_name,
                workflow_goal=workflow_goal,
                total_steps=len(step_agents),
                steps=[
                    WorkflowStepRecord(
                        step_index=index,
                        agent_name=agent_name,
                        linked_gate_id=self._make_workflow_gate_id(
                            step_index=index,
                            agent_name=agent_name,
                        ),
                    )
                    for index, agent_name in enumerate(step_agents)
                ],
            )
            stored_task.updated_at = self._now_iso()
            self._store.put_task(stored_task)
            return self._run.claim_task(
                stored_task.id,
                agent_role="workflow-orchestrator",
                lease_ttl_seconds=lease_ttl_seconds,
            )

    def attach_workflow_to_task(
        self,
        task_id: str,
        *,
        workflow_name: str,
        workflow_goal: str,
        step_agents: list[str],
        extra_gates: list[dict[str, Any]] | None = None,
        lease_ttl_seconds: float = 300.0,
    ) -> ClaimResult:
        """Attach workflow tracking to an existing task and claim it."""
        if not step_agents:
            raise ControlPlaneError("Tracked workflow must include at least one step")

        task = self._task.get_task(task_id)
        if task is None:
            from ttadev.control_plane.exceptions import TaskNotFoundError  # noqa: PLC0415

            raise TaskNotFoundError(f"Task not found: {task_id}")
        if task.workflow is not None:
            raise ControlPlaneError(f"Task {task_id} already has workflow tracking attached.")

        now_iso = self._now_iso()
        step_gates: list[dict[str, Any]] = [
            {
                "id": self._make_workflow_gate_id(step_index=index, agent_name=agent_name),
                "gate_type": GateType.APPROVAL.value,
                "label": f"{workflow_name} step {index + 1}: {agent_name}",
                "required": False,
            }
            for index, agent_name in enumerate(step_agents)
        ]
        all_extra = list(step_gates) + (extra_gates or [])
        for gate_spec in all_extra:
            new_gate = GateRecord(
                id=str(gate_spec["id"]),
                gate_type=GateType(str(gate_spec["gate_type"])),
                label=str(gate_spec.get("label", gate_spec["id"])),
                required=bool(gate_spec.get("required", False)),
            )
            if task.gates is None:
                task.gates = []
            task.gates.append(new_gate)

        task.workflow = WorkflowTrackingRecord(
            workflow_name=workflow_name,
            workflow_goal=workflow_goal,
            total_steps=len(step_agents),
            steps=[
                WorkflowStepRecord(
                    step_index=index,
                    agent_name=agent_name,
                    linked_gate_id=self._make_workflow_gate_id(
                        step_index=index,
                        agent_name=agent_name,
                    ),
                )
                for index, agent_name in enumerate(step_agents)
            ],
        )
        task.updated_at = now_iso
        self._store.put_task(task)
        return self._run.claim_task(
            task_id,
            agent_role="workflow-orchestrator",
            lease_ttl_seconds=lease_ttl_seconds,
        )

    def mark_workflow_step_running(
        self,
        task_id: str,
        *,
        step_index: int,
        trace_id: str | None = None,
        span_id: str | None = None,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
    ) -> Any:
        """Mark a tracked workflow step as running."""
        self._lease._sweep_expired_leases()
        task, workflow, step = self._get_workflow_step(task_id, step_index)

        # Capture the caller's OTel context BEFORE we start the control-plane
        # span — the step attribution should reflect the caller's trace, not ours.
        if trace_id is None and span_id is None:
            trace_id, span_id = _get_active_otel_context()

        with _emit_control_plane_span(
            "tta.l0.step.running",
            {
                "l0.task_id": task_id,
                "l0.step_index": step_index,
                "l0.step_agent": step.agent_name,
            },
        ):
            now_iso = self._now_iso()
            workflow.status = WorkflowTrackingStatus.RUNNING
            workflow.current_step_index = step_index
            workflow.current_agent = step.agent_name
            step.status = WorkflowStepStatus.RUNNING
            step.started_at = now_iso
            step.completed_at = None
            step.attempts += 1
            step.trace_id = trace_id
            step.span_id = span_id
            step.hindsight_bank_id = hindsight_bank_id
            step.hindsight_document_id = hindsight_document_id
            task.updated_at = now_iso
            self._store.put_task(task)
        return task

    def record_workflow_step_result(
        self,
        task_id: str,
        *,
        step_index: int,
        result_summary: str,
        confidence: float,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
    ) -> Any:
        """Store a short summary of the latest workflow step result."""
        self._lease._sweep_expired_leases()
        task, _, step = self._get_workflow_step(task_id, step_index)

        with _emit_control_plane_span(
            "tta.l0.step.completed",
            {
                "l0.task_id": task_id,
                "l0.step_index": step_index,
                "l0.confidence": confidence,
            },
        ):
            now_iso = self._now_iso()
            step.last_result_summary = result_summary or None
            step.last_confidence = confidence
            step.completed_at = now_iso
            step.status = WorkflowStepStatus.COMPLETED
            if hindsight_bank_id is not None:
                step.hindsight_bank_id = hindsight_bank_id
            if hindsight_document_id is not None:
                step.hindsight_document_id = hindsight_document_id
            task.updated_at = now_iso
            # Auto-evaluate any pending POLICY gates now that a confidence value is available.
            self._task._auto_evaluate_policy_gates(task, confidence=confidence, now_iso=now_iso)
            self._store.put_task(task)
        return task

    def record_workflow_gate_outcome(
        self,
        task_id: str,
        *,
        step_index: int,
        decision: WorkflowGateDecisionOutcome,
        summary: str = "",
        policy_name: str | None = None,
    ) -> Any:
        """Record the approval-gate outcome for a tracked workflow step."""
        self._lease._sweep_expired_leases()
        task, workflow, step = self._get_workflow_step(task_id, step_index)

        now_iso = self._now_iso()
        step.gate_decision = decision
        step.gate_history.append(
            self._build_workflow_gate_decision_record(
                decision=decision,
                occurred_at=now_iso,
                summary=summary,
                policy_name=policy_name,
            )
        )

        if decision == WorkflowGateDecisionOutcome.CONTINUE:
            step.status = WorkflowStepStatus.COMPLETED
            step.completed_at = now_iso
            if step.linked_gate_id is not None:
                gate = self._task._find_gate(task, step.linked_gate_id)
                if gate.status == GateStatus.PENDING:
                    actor = self._task._current_agent_id()
                    approval_summary = (
                        summary or f"Workflow step {step.step_index + 1} approved to continue"
                    )
                    gate.history.append(
                        GateHistoryEntry(
                            action=GateHistoryAction.DECISION,
                            from_status=gate.status,
                            to_status=GateStatus.APPROVED,
                            actor=actor,
                            occurred_at=now_iso,
                            summary=approval_summary or None,
                        )
                    )
                    gate.status = GateStatus.APPROVED
                    gate.decided_by = actor
                    gate.decided_at = now_iso
                    gate.summary = approval_summary
        elif decision == WorkflowGateDecisionOutcome.SKIP:
            step.status = WorkflowStepStatus.COMPLETED
            step.completed_at = now_iso
            next_step_index = step_index + 1
            if next_step_index < len(workflow.steps):
                skipped_step = workflow.steps[next_step_index]
                skipped_step.status = WorkflowStepStatus.SKIPPED
                skipped_step.completed_at = now_iso
                skipped_step.gate_decision = WorkflowGateDecisionOutcome.SKIP
                skipped_step.gate_history.append(
                    self._build_workflow_gate_decision_record(
                        decision=WorkflowGateDecisionOutcome.SKIP,
                        occurred_at=now_iso,
                        summary=(
                            summary or f"Skipped by gate decision after step {step_index + 1}"
                        ),
                    )
                )
        elif decision == WorkflowGateDecisionOutcome.EDIT:
            step.status = WorkflowStepStatus.PENDING
            step.completed_at = None
            workflow.current_step_index = step_index
            workflow.current_agent = step.agent_name
        elif decision == WorkflowGateDecisionOutcome.QUIT:
            step.status = WorkflowStepStatus.QUIT
            step.completed_at = now_iso
            workflow.status = WorkflowTrackingStatus.QUIT
            workflow.current_step_index = step_index
            workflow.current_agent = step.agent_name
        elif decision == WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN:
            # Pause the workflow — do not advance to the next step.
            # The step remains RUNNING until a human approves the linked gate.
            step.status = WorkflowStepStatus.RUNNING
            step.completed_at = None
            workflow.status = WorkflowTrackingStatus.ESCALATED
            workflow.current_step_index = step_index
            workflow.current_agent = step.agent_name

        task.updated_at = now_iso
        with _emit_control_plane_span(
            "tta.l0.gate.outcome",
            {
                "l0.task_id": task_id,
                "l0.step_index": step_index,
                "l0.gate_decision": decision.value,
            },
        ):
            self._store.put_task(task)
        return task

    def mark_workflow_step_failed(
        self,
        task_id: str,
        *,
        step_index: int,
        error_summary: str,
    ) -> Any:
        """Mark the current tracked workflow step as failed."""
        self._lease._sweep_expired_leases()
        task, workflow, step = self._get_workflow_step(task_id, step_index)

        with _emit_control_plane_span(
            "tta.l0.step.failed",
            {
                "l0.task_id": task_id,
                "l0.step_index": step_index,
                "l0.step_agent": step.agent_name,
                "l0.error_summary": error_summary,
            },
        ) as _span:
            now_iso = self._now_iso()
            workflow.status = WorkflowTrackingStatus.FAILED
            workflow.current_step_index = step_index
            workflow.current_agent = step.agent_name
            step.status = WorkflowStepStatus.FAILED
            step.completed_at = now_iso
            step.last_result_summary = error_summary
            task.updated_at = now_iso
            self._store.put_task(task)
            if _span is not None:
                try:
                    from opentelemetry.trace import Status, StatusCode

                    _span.set_status(Status(StatusCode.ERROR, error_summary))
                except Exception:
                    pass
        return task
