"""Service layer for the local L0 control plane."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ttadev.control_plane.models import (
    ClaimResult,
    LeaseRecord,
    RunRecord,
    RunStatus,
    TaskRecord,
    TaskStatus,
)
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.observability.agent_identity import get_agent_id, get_agent_tool
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import Session, SessionManager


class ControlPlaneError(Exception):
    """Base control-plane error."""


class TaskNotFoundError(ControlPlaneError):
    """Raised when a task ID is unknown."""


class RunNotFoundError(ControlPlaneError):
    """Raised when a run ID is unknown."""


class TaskClaimError(ControlPlaneError):
    """Raised when a task cannot be claimed or mutated."""


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

    def _get_active_session(self) -> Session | None:
        for session in self._sessions.list_sessions():
            if session.ended_at is None:
                return session
        return None

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
    ) -> TaskRecord:
        now_iso = self._now_iso()
        project_id: str | None = None
        normalized_project_name: str | None = None
        if project_name:
            project = self._projects.join(project_name)
            project_id = project.id
            normalized_project_name = project.name

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
        )
        self._store.put_task(task)
        return task

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

    def claim_task(
        self,
        task_id: str,
        *,
        agent_role: str | None = None,
        lease_ttl_seconds: float = 300.0,
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
        )
        lease = LeaseRecord(
            task_id=task.id,
            run_id=run.id,
            holder_agent_id=current_agent_id,
            acquired_at=now_iso,
            last_heartbeat_at=now_iso,
            expires_at=expires_at,
        )

        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = now_iso
        task.active_run_id = run.id
        task.claimed_by_agent_id = current_agent_id

        self._store.put_run(run)
        self._store.put_lease(lease)
        self._store.put_task(task)

        if task.project_id:
            self._projects.add_member(task.project_id, current_agent_id)
            if agent_role:
                self._projects.assign_role(task.project_id, agent_role, current_agent_id)

        return ClaimResult(task=task, run=run, lease=lease)

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

        now_iso = self._now_iso()
        run.status = RunStatus.COMPLETED
        run.updated_at = now_iso
        run.ended_at = now_iso
        run.summary = summary or None

        task.status = TaskStatus.COMPLETED
        task.updated_at = now_iso
        task.completed_at = now_iso
        task.active_run_id = None

        self._store.put_run(run)
        self._store.put_task(task)
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
        self._store.delete_lease(task.id)
        return run
