"""Task CRUD, gate management, and workflow cleanup for the L0 control plane."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ttadev.control_plane.exceptions import (
    ControlPlaneError,
    TaskGateError,
    TaskNotFoundError,
)
from ttadev.control_plane.lease_service import LeaseService
from ttadev.control_plane.models import (
    ActiveStepInfo,
    GateHistoryAction,
    GateHistoryEntry,
    GateRecord,
    GateStatus,
    GateType,
    LockScopeType,
    RunStatus,
    TaskRecord,
    TaskStatus,
    WorkflowStepStatus,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import Session, SessionManager


class TaskService:
    """Task CRUD, gate state management, and workflow-task cleanup."""

    def __init__(
        self,
        store: ControlPlaneStore,
        projects: ProjectSessionManager,
        sessions: SessionManager,
        lease_service: LeaseService,
    ) -> None:
        self._store = store
        self._projects = projects
        self._sessions = sessions
        self._lease = lease_service

    # ── Internal helpers ──────────────────────────────────────────────────────

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

    def _get_active_session(self) -> Session | None:
        for session in self._sessions.list_sessions():
            if session.ended_at is None:
                return session
        return None

    def _current_agent_id(self) -> str:
        active_session = self._get_active_session()
        if active_session and active_session.agent_id:
            return active_session.agent_id
        from ttadev.control_plane import service as _svc  # noqa: PLC0415

        return _svc.get_agent_id()

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
        """Return (outcome, summary) for auto-evaluable policy names, else None."""
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
                GateHistoryEntry(
                    action=GateHistoryAction.DECISION,
                    from_status=GateStatus.PENDING,
                    to_status=outcome,
                    actor=f"policy:{gate.policy_name}",
                    occurred_at=now_iso,
                    summary=summary or None,
                )
            )
            gate.status = outcome
            gate.decided_at = now_iso
            gate.decided_by = f"policy:{gate.policy_name}"
            gate.summary = summary

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
        if not any((gate.assigned_role, gate.assigned_agent_id, gate.assigned_decider)):
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

    def _ensure_required_gates_resolved(self, task: TaskRecord) -> None:
        unresolved = [
            gate.id for gate in task.gates if gate.required and gate.status != GateStatus.APPROVED
        ]
        if unresolved:
            unresolved_csv = ", ".join(unresolved)
            raise TaskGateError(f"Required gates unresolved: {unresolved_csv}")

    # ── Public API ────────────────────────────────────────────────────────────

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
        normalized_workspace_locks = self._lease._normalize_lock_values(
            workspace_locks,
            scope_type=LockScopeType.WORKSPACE,
        )
        normalized_file_locks = self._lease._normalize_lock_values(
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

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_name: str | None = None,
    ) -> list[TaskRecord]:
        self._lease._sweep_expired_leases()
        tasks = self._store.list_tasks()
        if status is not None:
            tasks = [task for task in tasks if task.status == status]
        if project_name is not None:
            tasks = [task for task in tasks if task.project_name == project_name]
        return sorted(tasks, key=lambda task: task.updated_at, reverse=True)

    def get_task(self, task_id: str) -> TaskRecord:
        self._lease._sweep_expired_leases()
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task

    def explain_active_step(self, task_id: str) -> ActiveStepInfo | None:
        """Return a read-only view of the currently-running workflow step, or None."""
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
        self._lease._sweep_expired_leases()
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
            GateHistoryEntry(
                action=GateHistoryAction.DECISION,
                from_status=previous_status,
                to_status=status,
                actor=effective_decider,
                occurred_at=now_iso,
                summary=summary or None,
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
        self._lease._sweep_expired_leases()
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
            GateHistoryEntry(
                action=GateHistoryAction.REOPENED,
                from_status=previous_status,
                to_status=GateStatus.PENDING,
                actor=effective_reopener,
                occurred_at=now_iso,
                summary=summary or None,
            )
        )
        gate.status = GateStatus.PENDING
        gate.decided_by = None
        gate.decided_at = None
        gate.summary = summary or None
        task.updated_at = now_iso
        self._store.put_task(task)
        return task

    def expire_abandoned_workflows(self) -> list[str]:
        """Find workflows whose active lease has expired and mark them FAILED; returns affected IDs."""
        from datetime import datetime  # noqa: PLC0415

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
        """Mark any RUNNING steps as FAILED for a terminated workflow; returns count cleaned."""
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
