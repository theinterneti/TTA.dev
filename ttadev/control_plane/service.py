"""Service layer for the local L0 control plane."""

from __future__ import annotations

import os
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from ttadev.control_plane.models import (
    ActiveStepInfo,
    ClaimResult,
    GateHistoryAction,
    GateHistoryEntry,
    GateRecord,
    GateStatus,
    GateType,
    LeaseRecord,
    LockRecord,
    LockScopeType,
    RunRecord,
    RunStatus,
    TaskRecord,
    TaskStatus,
    WorkflowGateDecisionOutcome,
    WorkflowGateDecisionRecord,
    WorkflowStepRecord,
    WorkflowStepStatus,
    WorkflowTrackingRecord,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.observability.agent_identity import get_agent_id, get_agent_tool
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import Session, SessionManager


def _get_active_otel_context() -> tuple[str | None, str | None]:
    """Return (trace_id_hex, span_id_hex) from the current OTel span, or (None, None).

    Falls back to parsing the W3C ``TRACEPARENT`` environment variable when no
    active span is present (e.g., CLI invocations that inherit a trace from a
    parent process).
    """
    from opentelemetry import trace as _otel_trace  # local import to avoid cost at import time

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


class ControlPlaneError(Exception):
    """Base control-plane error."""


class TaskNotFoundError(ControlPlaneError):
    """Raised when a task ID is unknown."""


class RunNotFoundError(ControlPlaneError):
    """Raised when a run ID is unknown."""


class TaskClaimError(ControlPlaneError):
    """Raised when a task cannot be claimed or mutated."""


class TaskGateError(ControlPlaneError):
    """Raised when gate state blocks a task mutation."""


class TaskLockError(ControlPlaneError):
    """Raised when lock state blocks a task mutation."""


class ControlPlaneService:
    """High-level operations for tasks, runs, and leases."""

    def __init__(self, data_dir: Path | str = ".tta") -> None:
        self._data_dir = Path(data_dir)
        self._store = ControlPlaneStore(self._data_dir)
        self._projects = ProjectSessionManager(self._data_dir)
        self._sessions = SessionManager(self._data_dir)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _now_iso(self) -> str:
        return self._now().isoformat()

    def _parse_dt(self, value: str) -> datetime:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    def _make_task_id(self) -> str:
        return f"task_{uuid.uuid4().hex[:12]}"

    def _make_run_id(self) -> str:
        return f"run_{uuid.uuid4().hex[:12]}"

    def _make_lock_id(self) -> str:
        return f"lock_{uuid.uuid4().hex[:12]}"

    def _current_agent_id(self) -> str:
        active_session = self._get_active_session()
        if active_session and active_session.agent_id:
            return active_session.agent_id
        return get_agent_id()

    def _normalize_gates(self, gates: list[dict[str, Any]] | None) -> list[GateRecord]:
        if gates is None:
            return []

        normalized: list[GateRecord] = []
        seen_gate_ids: set[str] = set()
        for gate in gates:
            gate_id = str(gate.get("id") or "").strip()
            label = str(gate.get("label") or "").strip()
            if not gate_id:
                raise TaskGateError("Gate ID must be non-empty")
            if gate_id in seen_gate_ids:
                raise TaskGateError(f"Duplicate gate ID: {gate_id}")
            if not label:
                raise TaskGateError(f"Gate {gate_id} must include a non-empty label")

            try:
                gate_type = GateType(str(gate.get("gate_type") or ""))
            except ValueError as exc:
                raise TaskGateError(f"Unsupported gate type for {gate_id}") from exc

            assigned_role = str(gate.get("assigned_role") or "").strip() or None
            assigned_agent_id = str(gate.get("assigned_agent_id") or "").strip() or None
            assigned_decider = str(gate.get("assigned_decider") or "").strip() or None
            policy_name = str(gate.get("policy_name") or "").strip() or None

            normalized.append(
                GateRecord(
                    id=gate_id,
                    gate_type=gate_type,
                    label=label,
                    required=bool(gate.get("required", True)),
                    assigned_role=assigned_role,
                    assigned_agent_id=assigned_agent_id,
                    assigned_decider=assigned_decider,
                    policy_name=policy_name,
                )
            )
            seen_gate_ids.add(gate_id)

        return normalized

    def _find_gate(self, task: TaskRecord, gate_id: str) -> GateRecord:
        for gate in task.gates:
            if gate.id == gate_id:
                return gate
        raise TaskGateError(f"Unknown gate ID: {gate_id}")

    # ── Policy gate auto-evaluation ───────────────────────────────────────────

    @staticmethod
    def _parse_policy_decision(
        policy_name: str,
        confidence: float | None,
    ) -> tuple[GateStatus, str] | None:
        """Return (outcome, summary) if policy_name can be evaluated, else None.

        Supported patterns:
          ``"auto:always"``             — always approve
          ``"auto:confidence≥{n}"``     — approve if confidence ≥ n
          ``"auto:confidence<{n}"``     — request changes if confidence < n
        """
        if not policy_name:
            return None
        if policy_name == "auto:always":
            return GateStatus.APPROVED, "Policy auto:always — automatically approved"

        # Handle both ASCII >= and the unicode ≥ character
        for op_str, op_char in ((">=", ">="), ("≥", "≥"), ("<", "<")):
            prefix = f"auto:confidence{op_char}"
            if policy_name.startswith(prefix):
                threshold_str = policy_name[len(prefix) :]
                try:
                    threshold = float(threshold_str)
                except ValueError:
                    return None
                if confidence is None:
                    return None
                if op_char in (">=", "≥"):
                    if confidence >= threshold:
                        return (
                            GateStatus.APPROVED,
                            f"Policy {policy_name} — confidence {confidence:.2f} ≥ {threshold}",
                        )
                    return None  # condition not met; do not auto-decide
                # op_char == "<"
                if confidence < threshold:
                    return (
                        GateStatus.CHANGES_REQUESTED,
                        f"Policy {policy_name} — confidence {confidence:.2f} < {threshold}",
                    )
                return None  # condition not met
        return None

    def _auto_evaluate_policy_gates(
        self,
        task: TaskRecord,
        *,
        confidence: float | None,
        now_iso: str,
    ) -> None:
        """Auto-decide any pending POLICY gates whose policy_name can be evaluated."""
        for gate in task.gates:
            if gate.gate_type != GateType.POLICY:
                continue
            if gate.status != GateStatus.PENDING:
                continue
            if not gate.policy_name:
                continue
            result = self._parse_policy_decision(gate.policy_name, confidence)
            if result is None:
                continue
            outcome, summary = result
            gate.history.append(
                self._build_gate_history_entry(
                    action=GateHistoryAction.DECISION,
                    from_status=GateStatus.PENDING,
                    to_status=outcome,
                    actor=f"policy:{gate.policy_name}",
                    occurred_at=now_iso,
                    summary=summary,
                )
            )
            gate.status = outcome
            gate.decided_at = now_iso
            gate.decided_by = f"policy:{gate.policy_name}"
            gate.summary = summary

    def _gate_has_assignments(self, gate: GateRecord) -> bool:
        return any(
            (
                gate.assigned_role,
                gate.assigned_agent_id,
                gate.assigned_decider,
            )
        )

    def _gate_role_matches(
        self,
        *,
        task: TaskRecord,
        required_role: str,
        current_agent_id: str,
        decision_role: str | None,
    ) -> bool:
        if decision_role is not None:
            return decision_role == required_role

        if task.active_run_id:
            run = self._store.get_run(task.active_run_id)
            if (
                run is not None
                and run.status == RunStatus.ACTIVE
                and run.agent_id == current_agent_id
                and run.agent_role == required_role
            ):
                return True

        if task.project_id:
            project = self._projects.get_by_id(task.project_id)
            if (
                project is not None
                and project.role_assignments.get(required_role) == current_agent_id
            ):
                return True

        return False

    def _ensure_gate_decider_allowed(
        self,
        *,
        task: TaskRecord,
        gate: GateRecord,
        current_agent_id: str,
        effective_decider: str,
        decision_role: str | None,
    ) -> None:
        if not self._gate_has_assignments(gate):
            return

        if gate.assigned_agent_id and gate.assigned_agent_id != current_agent_id:
            raise TaskGateError(f"Gate {gate.id} is assigned to agent {gate.assigned_agent_id}")

        if gate.assigned_decider and gate.assigned_decider != effective_decider:
            raise TaskGateError(f"Gate {gate.id} must be decided by {gate.assigned_decider}")

        if gate.assigned_role and not self._gate_role_matches(
            task=task,
            required_role=gate.assigned_role,
            current_agent_id=current_agent_id,
            decision_role=decision_role,
        ):
            if decision_role is None:
                raise TaskGateError(f"Gate {gate.id} requires role {gate.assigned_role}")
            raise TaskGateError(f"Gate {gate.id} requires role {gate.assigned_role}")

    def _ensure_gate_transition_allowed(
        self,
        *,
        gate: GateRecord,
        status: GateStatus,
    ) -> None:
        if gate.status == GateStatus.PENDING:
            return
        if gate.status == GateStatus.CHANGES_REQUESTED:
            raise TaskGateError(
                f"Gate {gate.id} cannot move from changes_requested to "
                f"{status.value} without reopen"
            )
        raise TaskGateError(
            f"Gate {gate.id} is already {gate.status.value} and cannot be decided again"
        )

    def _ensure_gate_reopen_allowed(
        self,
        *,
        task: TaskRecord,
        gate: GateRecord,
        effective_reopener: str,
    ) -> None:
        if gate.status != GateStatus.CHANGES_REQUESTED:
            raise TaskGateError(f"Gate {gate.id} is not in changes_requested")

        if not task.active_run_id:
            raise TaskGateError(f"Gate {gate.id} can only be reopened by the active run owner")

        run = self._store.get_run(task.active_run_id)
        if run is None or run.status != RunStatus.ACTIVE:
            raise TaskGateError(f"Gate {gate.id} can only be reopened by the active run owner")

        if effective_reopener != run.agent_id:
            raise TaskGateError(f"Gate {gate.id} can only be reopened by the active run owner")

    def _build_gate_history_entry(
        self,
        *,
        action: GateHistoryAction,
        from_status: GateStatus | None,
        to_status: GateStatus,
        actor: str,
        occurred_at: str,
        summary: str = "",
    ) -> GateHistoryEntry:
        """Create a normalized append-only history entry for a gate mutation."""
        return GateHistoryEntry(
            action=action,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            occurred_at=occurred_at,
            summary=summary or None,
        )

    def _make_workflow_gate_id(self, *, step_index: int, agent_name: str) -> str:
        """Build a stable optional gate ID for a tracked workflow step."""
        normalized_agent = agent_name.strip().replace("_", "-")
        return f"workflow-step-{step_index + 1}-{normalized_agent}"

    def _get_workflow_tracking(self, task: TaskRecord) -> WorkflowTrackingRecord:
        """Return workflow tracking metadata or raise if the task is not workflow-backed."""
        if task.workflow is None:
            raise ControlPlaneError(f"Task {task.id} is not tracking a workflow")
        return task.workflow

    def _get_workflow_step(
        self,
        task: TaskRecord,
        step_index: int,
    ) -> tuple[WorkflowTrackingRecord, WorkflowStepRecord]:
        """Return workflow tracking metadata and the requested step record."""
        workflow = self._get_workflow_tracking(task)
        if step_index < 0 or step_index >= len(workflow.steps):
            raise ControlPlaneError(
                f"Workflow step index {step_index} is out of range for task {task.id}"
            )
        return workflow, workflow.steps[step_index]

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

    def _build_workflow_ownership_summary(
        self,
        task: TaskRecord,
    ) -> dict[str, Any] | None:
        """Build a concise ownership summary for workflow-backed active tasks."""
        if task.workflow is None:
            return None

        workflow = task.workflow
        current_step: dict[str, Any] | None = None
        if workflow.current_step_index is not None and 0 <= workflow.current_step_index < len(
            workflow.steps
        ):
            step = workflow.steps[workflow.current_step_index]
            current_step = {
                "step_index": step.step_index,
                "step_number": step.step_index + 1,
                "agent_name": step.agent_name,
                "status": step.status.value,
                "gate_decision": step.gate_decision.value
                if step.gate_decision is not None
                else None,
                "linked_gate_id": step.linked_gate_id,
                "attempts": step.attempts,
                "started_at": step.started_at,
                "completed_at": step.completed_at,
                "last_result_summary": step.last_result_summary,
                "last_confidence": step.last_confidence,
            }

        recent_steps = [
            {
                "step_index": step.step_index,
                "step_number": step.step_index + 1,
                "agent_name": step.agent_name,
                "status": step.status.value,
                "gate_decision": (
                    step.gate_decision.value if step.gate_decision is not None else None
                ),
                "completed_at": step.completed_at,
                "last_result_summary": step.last_result_summary,
            }
            for step in workflow.steps
            if step.status != WorkflowStepStatus.PENDING
        ]
        recent_steps.sort(
            key=lambda step: (
                str(step["completed_at"] or ""),
                int(step["step_index"]),
            ),
            reverse=True,
        )

        return {
            "workflow_name": workflow.workflow_name,
            "workflow_goal": workflow.workflow_goal,
            "workflow_status": workflow.status.value,
            "total_steps": workflow.total_steps,
            "current_step_index": workflow.current_step_index,
            "current_step_number": (
                workflow.current_step_index + 1 if workflow.current_step_index is not None else None
            ),
            "current_agent": workflow.current_agent,
            "current_step": current_step,
            "recent_steps": recent_steps[:3],
        }

    def _normalize_workspace_lock(self, workspace_name: str) -> str:
        normalized = workspace_name.strip()
        if not normalized:
            raise TaskLockError("Workspace lock must be non-empty")
        return normalized

    def _normalize_file_lock(self, file_path: str) -> str:
        normalized_input = file_path.strip().replace("\\", "/")
        if not normalized_input:
            raise TaskLockError("File lock path must be non-empty")

        path = PurePosixPath(normalized_input)
        if path.is_absolute():
            raise TaskLockError(f"File lock path must be repo-relative: {file_path}")

        cleaned_parts: list[str] = []
        for part in path.parts:
            if part in {"", "."}:
                continue
            if part == "..":
                raise TaskLockError(f"File lock path must not escape the repo: {file_path}")
            if part.endswith(":"):
                raise TaskLockError(f"File lock path must be repo-relative: {file_path}")
            cleaned_parts.append(part)

        if not cleaned_parts:
            raise TaskLockError("File lock path must be non-empty")
        return str(PurePosixPath(*cleaned_parts))

    def _normalize_lock_values(
        self, values: list[str] | None, *, scope_type: LockScopeType
    ) -> list[str]:
        if values is None:
            return []

        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            candidate = str(value)
            normalized_value = (
                self._normalize_workspace_lock(candidate)
                if scope_type == LockScopeType.WORKSPACE
                else self._normalize_file_lock(candidate)
            )
            if normalized_value not in seen:
                normalized.append(normalized_value)
                seen.add(normalized_value)
        return normalized

    def _validate_lock_owner(self, task_id: str, run_id: str) -> tuple[TaskRecord, RunRecord]:
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.task_id != task.id:
            raise TaskLockError(f"Run {run_id} does not belong to task {task_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskLockError(f"Run {run_id} is not active")
        return task, run

    def _acquire_lock(
        self,
        *,
        task: TaskRecord,
        run: RunRecord,
        scope_type: LockScopeType,
        scope_value: str,
        now_iso: str,
    ) -> LockRecord:
        existing = self._store.get_lock_for_scope(scope_type, scope_value)
        if existing is not None:
            if existing.run_id == run.id:
                return existing
            raise TaskLockError(f"{scope_type.value} lock already held: {scope_value}")

        lock = LockRecord(
            id=self._make_lock_id(),
            scope_type=scope_type,
            scope_value=scope_value,
            task_id=task.id,
            run_id=run.id,
            agent_id=run.agent_id,
            acquired_at=now_iso,
            updated_at=now_iso,
        )
        self._store.put_lock(lock)
        return lock

    def _prepare_claim_locks(
        self, task: TaskRecord, run: RunRecord
    ) -> list[tuple[LockScopeType, str]]:
        requested_scopes: list[tuple[LockScopeType, str]] = []
        for workspace_name in task.workspace_locks:
            requested_scopes.append((LockScopeType.WORKSPACE, workspace_name))
        for file_path in task.file_locks:
            requested_scopes.append((LockScopeType.FILE, file_path))

        for scope_type, scope_value in requested_scopes:
            existing = self._store.get_lock_for_scope(scope_type, scope_value)
            if existing is not None and existing.run_id != run.id:
                raise TaskLockError(f"{scope_type.value} lock already held: {scope_value}")
        return requested_scopes

    def _ensure_required_gates_resolved(self, task: TaskRecord) -> None:
        unresolved = [
            gate.id for gate in task.gates if gate.required and gate.status != GateStatus.APPROVED
        ]
        if unresolved:
            unresolved_csv = ", ".join(unresolved)
            raise TaskGateError(f"Required gates unresolved: {unresolved_csv}")

    def _get_active_session(self) -> Session | None:
        for session in self._sessions.list_sessions():
            if session.ended_at is None:
                return session
        return None

    def _link_session_to_project_if_needed(
        self, session: Session | None, project_id: str | None
    ) -> Session | None:
        if session is None or not project_id or session.project_id:
            return session
        return self._sessions.update_session_project(session.id, project_id) or session

    def _expire_lease(self, lease: LeaseRecord, *, now_iso: str) -> None:
        run = self._store.get_run(lease.run_id)
        if run is not None and run.status == RunStatus.ACTIVE:
            run.status = RunStatus.EXPIRED
            run.updated_at = now_iso
            run.ended_at = now_iso
            self._store.put_run(run)

        task = self._store.get_task(lease.task_id)
        if (
            task is not None
            and task.active_run_id == lease.run_id
            and task.status != TaskStatus.COMPLETED
        ):
            task.status = TaskStatus.PENDING
            task.updated_at = now_iso
            task.active_run_id = None
            task.claimed_by_agent_id = None
            self._store.put_task(task)

        self.release_locks_for_run(lease.run_id)
        self._store.delete_lease(lease.task_id)

    def _sweep_expired_leases(self) -> None:
        now = self._now()
        now_iso = now.isoformat()
        for lease in self._store.list_leases():
            if self._parse_dt(lease.expires_at) <= now:
                self._expire_lease(lease, now_iso=now_iso)

    def create_task(
        self,
        title: str,
        description: str = "",
        *,
        project_name: str | None = None,
        requested_role: str | None = None,
        priority: str = "normal",
        gates: list[dict[str, Any]] | None = None,
        workspace_locks: list[str] | None = None,
        file_locks: list[str] | None = None,
    ) -> TaskRecord:
        now_iso = self._now_iso()
        project_id: str | None = None
        normalized_project_name: str | None = None
        if project_name:
            project = self._projects.join(project_name)
            project_id = project.id
            normalized_project_name = project.name
        normalized_gates = self._normalize_gates(gates)
        normalized_workspace_locks = self._normalize_lock_values(
            workspace_locks,
            scope_type=LockScopeType.WORKSPACE,
        )
        normalized_file_locks = self._normalize_lock_values(
            file_locks,
            scope_type=LockScopeType.FILE,
        )

        task = TaskRecord(
            id=self._make_task_id(),
            title=title,
            description=description,
            created_at=now_iso,
            updated_at=now_iso,
            priority=priority,
            project_id=project_id,
            project_name=normalized_project_name,
            requested_role=requested_role,
            gates=normalized_gates,
            workspace_locks=normalized_workspace_locks,
            file_locks=normalized_file_locks,
        )
        self._store.put_task(task)
        return task

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
        """Create and claim one top-level task for a tracked workflow run.

        ``extra_gates`` allows callers to attach additional L0 gates (e.g.
        POLICY-type auto-evaluation gates) alongside the per-step APPROVAL gates.
        """
        if not step_agents:
            raise ControlPlaneError("Tracked workflow must include at least one step")

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
        task = self.create_task(
            title=f"Workflow {workflow_name}: {workflow_goal.strip() or workflow_name}",
            description=f"Tracked workflow run for {workflow_name}: {workflow_goal}",
            project_name=project_name,
            requested_role="workflow-orchestrator",
            gates=gates,
        )
        stored_task = self._store.get_task(task.id)
        if stored_task is None:
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
        return self.claim_task(
            stored_task.id,
            agent_role="workflow-orchestrator",
            lease_ttl_seconds=lease_ttl_seconds,
        )

    def expire_abandoned_workflows(self) -> list[str]:
        """Find workflows whose active run lease has expired and mark them FAILED.

        Returns list of task IDs that were transitioned to FAILED.
        Call periodically (e.g., on session start or via a background process).
        """
        from datetime import datetime

        now = datetime.now(UTC)
        affected: list[str] = []

        for task in self._store.list_tasks():
            if task.workflow is None:
                continue
            if task.workflow.status != WorkflowTrackingStatus.RUNNING:
                continue
            if task.active_run_id is None:
                continue  # no active run — cleanly released, not abandoned

            lease = self._store.get_lease_for_run(task.active_run_id)
            if lease is None:
                continue  # no lease record — can't determine expiry
            lease_expires_at = datetime.fromisoformat(lease.expires_at)
            if lease_expires_at.tzinfo is None:
                lease_expires_at = lease_expires_at.replace(tzinfo=UTC)
            if lease_expires_at > now:
                continue  # lease still valid

            # Lease expired — mark current running step as FAILED
            current_step_idx = task.workflow.current_step_index
            if current_step_idx is not None:
                step = task.workflow.steps[current_step_idx]
                if step.status == WorkflowStepStatus.RUNNING:
                    step.status = WorkflowStepStatus.FAILED

            task.workflow.status = WorkflowTrackingStatus.FAILED
            self._store.put_task(task)
            affected.append(task.id)

        return affected

    def cleanup_orphaned_steps(self, task_id: str) -> int:
        """Mark any RUNNING steps as FAILED for a terminated workflow.

        Use when a workflow is QUIT/FAILED but steps were not cleanly transitioned.
        Returns count of steps cleaned up.
        """
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        if task.workflow is None:
            return 0

        terminal_statuses = {WorkflowTrackingStatus.QUIT, WorkflowTrackingStatus.FAILED}
        if task.workflow.status not in terminal_statuses:
            return 0

        cleaned = 0
        for step in task.workflow.steps:
            if step.status == WorkflowStepStatus.RUNNING:
                step.status = WorkflowStepStatus.FAILED
                cleaned += 1

        if cleaned > 0:
            self._store.put_task(task)

        return cleaned

    def mark_workflow_step_running(
        self,
        task_id: str,
        *,
        step_index: int,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> TaskRecord:
        """Mark a tracked workflow step as running."""
        self._sweep_expired_leases()
        task = self.get_task(task_id)
        workflow, step = self._get_workflow_step(task, step_index)

        now_iso = self._now_iso()
        workflow.status = WorkflowTrackingStatus.RUNNING
        workflow.current_step_index = step_index
        workflow.current_agent = step.agent_name
        step.status = WorkflowStepStatus.RUNNING
        step.started_at = now_iso
        step.completed_at = None
        step.attempts += 1
        if trace_id is None and span_id is None:
            trace_id, span_id = _get_active_otel_context()
        step.trace_id = trace_id
        step.span_id = span_id
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
    ) -> TaskRecord:
        """Store a short summary of the latest workflow step result."""
        self._sweep_expired_leases()
        task = self.get_task(task_id)
        _, step = self._get_workflow_step(task, step_index)

        now_iso = self._now_iso()
        step.last_result_summary = result_summary or None
        step.last_confidence = confidence
        step.completed_at = now_iso
        step.status = WorkflowStepStatus.COMPLETED
        task.updated_at = now_iso
        # Auto-evaluate any pending POLICY gates now that a confidence value is available.
        self._auto_evaluate_policy_gates(task, confidence=confidence, now_iso=now_iso)
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
    ) -> TaskRecord:
        """Record the approval-gate outcome for a tracked workflow step."""
        self._sweep_expired_leases()
        task = self.get_task(task_id)
        workflow, step = self._get_workflow_step(task, step_index)

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
                gate = self._find_gate(task, step.linked_gate_id)
                if gate.status == GateStatus.PENDING:
                    actor = self._current_agent_id()
                    approval_summary = (
                        summary or f"Workflow step {step.step_index + 1} approved to continue"
                    )
                    gate.history.append(
                        self._build_gate_history_entry(
                            action=GateHistoryAction.DECISION,
                            from_status=gate.status,
                            to_status=GateStatus.APPROVED,
                            actor=actor,
                            occurred_at=now_iso,
                            summary=approval_summary,
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
        self._store.put_task(task)
        return task

    def mark_workflow_step_failed(
        self,
        task_id: str,
        *,
        step_index: int,
        error_summary: str,
    ) -> TaskRecord:
        """Mark the current tracked workflow step as failed."""
        self._sweep_expired_leases()
        task = self.get_task(task_id)
        workflow, step = self._get_workflow_step(task, step_index)

        now_iso = self._now_iso()
        workflow.status = WorkflowTrackingStatus.FAILED
        workflow.current_step_index = step_index
        workflow.current_agent = step.agent_name
        step.status = WorkflowStepStatus.FAILED
        step.completed_at = now_iso
        step.last_result_summary = error_summary
        task.updated_at = now_iso
        self._store.put_task(task)
        return task

    def finalize_tracked_workflow(
        self,
        task_id: str,
        run_id: str,
        *,
        status: WorkflowTrackingStatus,
        summary: str = "",
    ) -> RunRecord:
        """Finalize a tracked workflow run and close the corresponding control-plane run."""
        self._sweep_expired_leases()
        if status not in {
            WorkflowTrackingStatus.COMPLETED,
            WorkflowTrackingStatus.QUIT,
            WorkflowTrackingStatus.FAILED,
        }:
            raise ControlPlaneError(
                "Tracked workflow finalization requires completed, quit, or failed status"
            )

        task = self.get_task(task_id)
        workflow = self._get_workflow_tracking(task)
        workflow.status = status
        workflow.current_step_index = None
        workflow.current_agent = None
        now_iso = self._now_iso()
        task.updated_at = now_iso

        if status == WorkflowTrackingStatus.COMPLETED:
            self._store.put_task(task)
            return self.complete_run(run_id, summary=summary)

        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskClaimError(f"Run {run_id} is not active")

        run.status = RunStatus.RELEASED
        run.updated_at = now_iso
        run.ended_at = now_iso
        run.summary = summary or None

        task.status = TaskStatus.PENDING
        task.active_run_id = None
        task.claimed_by_agent_id = None

        self._store.put_run(run)
        self._store.put_task(task)
        self.release_locks_for_run(run.id)
        self._store.delete_lease(task.id)
        return run

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_name: str | None = None,
    ) -> list[TaskRecord]:
        self._sweep_expired_leases()
        tasks = self._store.list_tasks()
        if status is not None:
            tasks = [task for task in tasks if task.status == status]
        if project_name is not None:
            tasks = [task for task in tasks if task.project_name == project_name]
        return sorted(tasks, key=lambda task: task.updated_at, reverse=True)

    def get_task(self, task_id: str) -> TaskRecord:
        self._sweep_expired_leases()
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task

    def explain_active_step(self, task_id: str) -> ActiveStepInfo | None:
        """Return a read-only view of the currently-running workflow step.

        Raises ``ControlPlaneError`` if the task is not found or has no
        associated workflow.  Returns ``None`` when no step is currently
        in RUNNING state.  If (unexpectedly) multiple steps are RUNNING,
        the one with the highest ``step_index`` is returned.
        """
        task = self.get_task(task_id)
        if task.workflow is None:
            raise ControlPlaneError(f"Task {task_id} has no workflow")

        running_steps = [
            step for step in task.workflow.steps if step.status == WorkflowStepStatus.RUNNING
        ]
        if not running_steps:
            return None

        step = max(running_steps, key=lambda s: s.step_index)

        started_at = step.started_at
        if started_at is not None:
            duration_s = (self._now() - self._parse_dt(started_at)).total_seconds()
        else:
            duration_s = None

        # Exclude the step's own linked approval gate — it is inherently PENDING
        # while the step is running and is not an external blocker.
        pending_gate_ids = tuple(
            gate.id
            for gate in task.gates
            if gate.status == GateStatus.PENDING and gate.id != step.linked_gate_id
        )

        return ActiveStepInfo(
            task_id=task_id,
            step_index=step.step_index,
            agent_name=step.agent_name,
            started_at=started_at,
            duration_s=duration_s,
            trace_id=step.trace_id,
            span_id=step.span_id,
            pending_gate_ids=pending_gate_ids,
        )

    def list_runs(self, *, status: RunStatus | None = None) -> list[RunRecord]:
        self._sweep_expired_leases()
        runs = self._store.list_runs()
        if status is not None:
            runs = [run for run in runs if run.status == status]
        return sorted(runs, key=lambda run: run.updated_at, reverse=True)

    def get_run(self, run_id: str) -> RunRecord:
        self._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        return run

    def get_lease_for_run(self, run_id: str) -> LeaseRecord | None:
        self._sweep_expired_leases()
        return self._store.get_lease_for_run(run_id)

    def list_locks(self, *, scope_type: LockScopeType | None = None) -> list[LockRecord]:
        self._sweep_expired_leases()
        locks = self._store.list_locks()
        if scope_type is not None:
            locks = [lock for lock in locks if lock.scope_type == scope_type]
        return sorted(locks, key=lambda lock: lock.updated_at, reverse=True)

    def list_active_ownership(
        self,
        *,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return active run ownership linked to task, lease, session, and project state."""
        self._sweep_expired_leases()
        active_runs = [run for run in self._store.list_runs() if run.status == RunStatus.ACTIVE]
        ownership: list[dict[str, Any]] = []

        for run in active_runs:
            task = self._store.get_task(run.task_id)
            if task is None:
                raise TaskNotFoundError(f"Task not found: {run.task_id}")
            if project_id is not None and task.project_id != project_id:
                continue
            if session_id is not None and run.session_id != session_id:
                continue

            lease = self._store.get_lease_for_run(run.id)
            session = self._sessions.get_session(run.session_id) if run.session_id else None
            project = self._projects.get_by_id(task.project_id) if task.project_id else None
            ownership.append(
                {
                    "task": task.to_dict(),
                    "run": run.to_dict(),
                    "lease": lease.to_dict() if lease is not None else None,
                    "session": asdict(session) if session is not None else None,
                    "project": asdict(project) if project is not None else None,
                    "workflow": self._build_workflow_ownership_summary(task),
                    "telemetry": (
                        self._sessions.get_recent_activity_summary(run.session_id)
                        if run.session_id and session is not None
                        else None
                    ),
                }
            )

        ownership.sort(key=lambda record: str(record["run"]["updated_at"]), reverse=True)
        return ownership

    def acquire_workspace_lock(self, task_id: str, run_id: str, workspace_name: str) -> LockRecord:
        self._sweep_expired_leases()
        task, run = self._validate_lock_owner(task_id, run_id)
        normalized_name = self._normalize_workspace_lock(workspace_name)
        return self._acquire_lock(
            task=task,
            run=run,
            scope_type=LockScopeType.WORKSPACE,
            scope_value=normalized_name,
            now_iso=self._now_iso(),
        )

    def acquire_file_lock(self, task_id: str, run_id: str, file_path: str) -> LockRecord:
        self._sweep_expired_leases()
        task, run = self._validate_lock_owner(task_id, run_id)
        normalized_path = self._normalize_file_lock(file_path)
        return self._acquire_lock(
            task=task,
            run=run,
            scope_type=LockScopeType.FILE,
            scope_value=normalized_path,
            now_iso=self._now_iso(),
        )

    def release_lock(self, lock_id: str) -> None:
        self._sweep_expired_leases()
        lock = self._store.get_lock(lock_id)
        if lock is None:
            raise TaskLockError(f"Lock not found: {lock_id}")
        self._store.delete_lock(lock_id)

    def release_locks_for_run(self, run_id: str) -> None:
        for lock in self._store.list_locks_for_run(run_id):
            self._store.delete_lock(lock.id)

    def claim_task(
        self,
        task_id: str,
        *,
        agent_role: str | None = None,
        lease_ttl_seconds: float = 300.0,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> ClaimResult:
        if lease_ttl_seconds <= 0:
            raise TaskClaimError("lease_ttl_seconds must be > 0")

        self._sweep_expired_leases()
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        if task.status == TaskStatus.COMPLETED:
            raise TaskClaimError(f"Task {task_id} is already completed")

        active_session = self._get_active_session()
        current_agent_id = (
            active_session.agent_id
            if active_session and active_session.agent_id
            else get_agent_id()
        )
        current_agent_tool = active_session.agent_tool if active_session else get_agent_tool()
        active_session = self._link_session_to_project_if_needed(active_session, task.project_id)

        lease = self._store.get_lease_for_task(task_id)
        if lease is not None:
            if lease.holder_agent_id == current_agent_id:
                existing_run = self._store.get_run(lease.run_id)
                if existing_run is not None:
                    return ClaimResult(task=task, run=existing_run, lease=lease)
            raise TaskClaimError(f"Task {task_id} is currently leased by another agent")

        now = self._now()
        now_iso = now.isoformat()
        expires_at = (now + timedelta(seconds=lease_ttl_seconds)).isoformat()

        run = RunRecord(
            id=self._make_run_id(),
            task_id=task.id,
            agent_id=current_agent_id,
            agent_tool=current_agent_tool,
            agent_role=agent_role,
            session_id=active_session.id if active_session else None,
            started_at=now_iso,
            updated_at=now_iso,
            trace_id=trace_id,
            span_id=span_id,
        )
        lease = LeaseRecord(
            task_id=task.id,
            run_id=run.id,
            holder_agent_id=current_agent_id,
            acquired_at=now_iso,
            last_heartbeat_at=now_iso,
            expires_at=expires_at,
        )
        claim_locks = self._prepare_claim_locks(task, run)

        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = now_iso
        task.active_run_id = run.id
        task.claimed_by_agent_id = current_agent_id

        self._store.put_run(run)
        self._store.put_lease(lease)
        self._store.put_task(task)
        for scope_type, scope_value in claim_locks:
            self._acquire_lock(
                task=task,
                run=run,
                scope_type=scope_type,
                scope_value=scope_value,
                now_iso=now_iso,
            )

        if task.project_id:
            self._projects.add_member(task.project_id, current_agent_id)
            if agent_role:
                self._projects.assign_role(task.project_id, agent_role, current_agent_id)

        return ClaimResult(task=task, run=run, lease=lease)

    def decide_gate(
        self,
        task_id: str,
        gate_id: str,
        *,
        status: GateStatus,
        decided_by: str | None = None,
        decision_role: str | None = None,
        summary: str = "",
    ) -> TaskRecord:
        self._sweep_expired_leases()
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        gate = self._find_gate(task, gate_id)
        current_agent_id = self._current_agent_id()
        effective_decider = str(decided_by).strip() if decided_by else current_agent_id
        normalized_decision_role = str(decision_role).strip() if decision_role else None
        self._ensure_gate_decider_allowed(
            task=task,
            gate=gate,
            current_agent_id=current_agent_id,
            effective_decider=effective_decider,
            decision_role=normalized_decision_role,
        )
        self._ensure_gate_transition_allowed(gate=gate, status=status)
        now_iso = self._now_iso()
        previous_status = gate.status
        gate.history.append(
            self._build_gate_history_entry(
                action=GateHistoryAction.DECISION,
                from_status=previous_status,
                to_status=status,
                actor=effective_decider,
                occurred_at=now_iso,
                summary=summary,
            )
        )
        gate.status = status
        gate.decided_at = now_iso
        gate.decided_by = effective_decider
        gate.summary = summary or None

        # If a human approves a gate on an escalated workflow, restore workflow to RUNNING.
        if (
            task.workflow is not None
            and task.workflow.status == WorkflowTrackingStatus.ESCALATED
            and status == GateStatus.APPROVED
        ):
            task.workflow.status = WorkflowTrackingStatus.RUNNING

        task.updated_at = now_iso
        self._store.put_task(task)
        return task

    def reopen_gate(
        self,
        task_id: str,
        gate_id: str,
        *,
        reopened_by: str | None = None,
        summary: str = "",
    ) -> TaskRecord:
        self._sweep_expired_leases()
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        gate = self._find_gate(task, gate_id)
        effective_reopener = str(reopened_by).strip() if reopened_by else self._current_agent_id()
        self._ensure_gate_reopen_allowed(
            task=task,
            gate=gate,
            effective_reopener=effective_reopener,
        )

        now_iso = self._now_iso()
        previous_status = gate.status
        gate.history.append(
            self._build_gate_history_entry(
                action=GateHistoryAction.REOPENED,
                from_status=previous_status,
                to_status=GateStatus.PENDING,
                actor=effective_reopener,
                occurred_at=now_iso,
                summary=summary,
            )
        )
        gate.status = GateStatus.PENDING
        gate.decided_by = None
        gate.decided_at = None
        gate.summary = summary or None
        task.updated_at = now_iso
        self._store.put_task(task)
        return task

    def heartbeat_run(self, run_id: str, *, lease_ttl_seconds: float = 300.0) -> LeaseRecord:
        if lease_ttl_seconds <= 0:
            raise TaskClaimError("lease_ttl_seconds must be > 0")

        self._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskClaimError(f"Run {run_id} is not active")

        lease = self._store.get_lease_for_run(run_id)
        if lease is None:
            raise TaskClaimError(f"Run {run_id} does not hold an active lease")

        now = self._now()
        run.updated_at = now.isoformat()
        lease.last_heartbeat_at = now.isoformat()
        lease.expires_at = (now + timedelta(seconds=lease_ttl_seconds)).isoformat()

        self._store.put_run(run)
        self._store.put_lease(lease)
        return lease

    def complete_run(self, run_id: str, *, summary: str = "") -> RunRecord:
        self._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskClaimError(f"Run {run_id} is not active")

        task = self._store.get_task(run.task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {run.task_id}")
        self._ensure_required_gates_resolved(task)

        now_iso = self._now_iso()
        run.status = RunStatus.COMPLETED
        run.updated_at = now_iso
        run.ended_at = now_iso
        run.summary = summary or None

        task.status = TaskStatus.COMPLETED
        task.updated_at = now_iso
        task.completed_at = now_iso
        task.active_run_id = None

        # Auto-finalize workflow tracking when all steps have reached COMPLETED.
        if task.workflow is not None and task.workflow.status == WorkflowTrackingStatus.RUNNING:
            _terminal = {
                WorkflowStepStatus.COMPLETED,
                WorkflowStepStatus.QUIT,
                WorkflowStepStatus.FAILED,
            }
            steps = task.workflow.steps
            if steps and all(s.status in _terminal for s in steps):
                if all(s.status == WorkflowStepStatus.COMPLETED for s in steps):
                    task.workflow.status = WorkflowTrackingStatus.COMPLETED

        self._store.put_run(run)
        self._store.put_task(task)
        self.release_locks_for_run(run.id)
        self._store.delete_lease(task.id)
        return run

    def release_run(self, run_id: str, *, reason: str = "") -> RunRecord:
        self._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskClaimError(f"Run {run_id} is not active")

        task = self._store.get_task(run.task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {run.task_id}")
        self._ensure_required_gates_resolved(task)

        now_iso = self._now_iso()
        run.status = RunStatus.RELEASED
        run.updated_at = now_iso
        run.ended_at = now_iso
        run.summary = reason or None

        task.status = TaskStatus.PENDING
        task.updated_at = now_iso
        task.active_run_id = None
        task.claimed_by_agent_id = None

        self._store.put_run(run)
        self._store.put_task(task)
        self.release_locks_for_run(run.id)
        self._store.delete_lease(task.id)
        return run
