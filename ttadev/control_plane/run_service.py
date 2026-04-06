"""Run lifecycle management for the L0 control plane."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Any

from ttadev.control_plane.exceptions import (
    ControlPlaneError,
    RunNotFoundError,
    TaskClaimError,
    TaskNotFoundError,
)
from ttadev.control_plane.lease_service import LeaseService
from ttadev.control_plane.models import (
    ClaimResult,
    LeaseRecord,
    RunRecord,
    RunStatus,
    TaskRecord,
    TaskStatus,
    WorkflowStepStatus,
    WorkflowTrackingRecord,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.control_plane.task_service import TaskService
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import Session, SessionManager


class RunService:
    """Claim, heartbeat, complete, and release task runs.

    Also owns run-level workflow operations such as ``finalize_tracked_workflow``
    and the ``list_active_ownership`` dashboard query.
    """

    def __init__(
        self,
        store: ControlPlaneStore,
        projects: ProjectSessionManager,
        sessions: SessionManager,
        task_service: TaskService,
        lease_service: LeaseService,
    ) -> None:
        self._store = store
        self._projects = projects
        self._sessions = sessions
        self._task = task_service
        self._lease = lease_service

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _now_iso(self) -> str:
        return self._now().isoformat()

    def _make_run_id(self) -> str:
        return f"run_{uuid.uuid4().hex[:12]}"

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

    def _get_workflow_tracking(self, task: TaskRecord) -> WorkflowTrackingRecord:
        """Return workflow tracking metadata or raise if the task is not workflow-backed."""
        if task.workflow is None:
            raise ControlPlaneError(f"Task {task.id} is not tracking a workflow")
        return task.workflow

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

    # ── Public API ────────────────────────────────────────────────────────────

    def list_runs(self, *, status: RunStatus | None = None) -> list[RunRecord]:
        self._lease._sweep_expired_leases()
        runs = self._store.list_runs()
        if status is not None:
            runs = [run for run in runs if run.status == status]
        return sorted(runs, key=lambda run: run.updated_at, reverse=True)

    def get_run(self, run_id: str) -> RunRecord:
        self._lease._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        return run

    def get_lease_for_run(self, run_id: str) -> LeaseRecord | None:
        self._lease._sweep_expired_leases()
        return self._store.get_lease_for_run(run_id)

    def list_active_ownership(
        self,
        *,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return active run ownership linked to task, lease, session, and project state."""
        self._lease._sweep_expired_leases()
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

        self._lease._sweep_expired_leases()
        task = self._store.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        if task.status == TaskStatus.COMPLETED:
            raise TaskClaimError(f"Task {task_id} is already completed")

        active_session = self._get_active_session()
        from ttadev.control_plane import service as _svc  # noqa: PLC0415

        current_agent_id = (
            active_session.agent_id
            if active_session and active_session.agent_id
            else _svc.get_agent_id()
        )
        current_agent_tool = active_session.agent_tool if active_session else _svc.get_agent_tool()
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
        claim_locks = self._lease._prepare_claim_locks(task, run)

        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = now_iso
        task.active_run_id = run.id
        task.claimed_by_agent_id = current_agent_id

        self._store.put_run(run)
        self._store.put_lease(lease)
        self._store.put_task(task)
        for scope_type, scope_value in claim_locks:
            self._lease._acquire_lock(
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

        # Emit Langfuse session for this run so all LLM calls nest under it
        try:
            from tta_apm_langfuse import (
                get_integration,  # noqa: PLC0415  # type: ignore[import-untyped]
            )

            _lf = get_integration()
            if _lf is not None:
                _lf.session_id = run.id
                import logging as _logging  # noqa: PLC0415

                _logging.getLogger(__name__).debug("Langfuse session bound to run %s", run.id)
        except Exception:
            pass

        return ClaimResult(task=task, run=run, lease=lease)

    def heartbeat_run(self, run_id: str, *, lease_ttl_seconds: float = 300.0) -> LeaseRecord:
        if lease_ttl_seconds <= 0:
            raise TaskClaimError("lease_ttl_seconds must be > 0")

        self._lease._sweep_expired_leases()
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
        self._lease._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskClaimError(f"Run {run_id} is not active")

        task = self._store.get_task(run.task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {run.task_id}")
        self._task._ensure_required_gates_resolved(task)

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
        self._lease.release_locks_for_run(run.id)
        self._store.delete_lease(task.id)
        return run

    def release_run(self, run_id: str, *, reason: str = "") -> RunRecord:
        self._lease._sweep_expired_leases()
        run = self._store.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")
        if run.status != RunStatus.ACTIVE:
            raise TaskClaimError(f"Run {run_id} is not active")

        task = self._store.get_task(run.task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {run.task_id}")
        self._task._ensure_required_gates_resolved(task)

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
        self._lease.release_locks_for_run(run.id)
        self._store.delete_lease(task.id)
        return run

    def finalize_tracked_workflow(
        self,
        task_id: str,
        run_id: str,
        *,
        status: WorkflowTrackingStatus,
        summary: str = "",
    ) -> RunRecord:
        """Finalize a tracked workflow run and close the corresponding control-plane run."""
        self._lease._sweep_expired_leases()
        if status not in {
            WorkflowTrackingStatus.COMPLETED,
            WorkflowTrackingStatus.QUIT,
            WorkflowTrackingStatus.FAILED,
        }:
            raise ControlPlaneError(
                "Tracked workflow finalization requires completed, quit, or failed status"
            )

        task = self._task.get_task(task_id)
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
        self._lease.release_locks_for_run(run.id)
        self._store.delete_lease(task.id)
        return run
