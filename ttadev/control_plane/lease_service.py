"""Distributed lease and lock management for the L0 control plane."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import PurePosixPath

from ttadev.control_plane.exceptions import RunNotFoundError, TaskLockError, TaskNotFoundError
from ttadev.control_plane.models import (
    LeaseRecord,
    LockRecord,
    LockScopeType,
    RunRecord,
    RunStatus,
    TaskRecord,
    TaskStatus,
)
from ttadev.control_plane.store import ControlPlaneStore


class LeaseService:
    """Manages distributed leases and file/workspace locks."""

    def __init__(self, store: ControlPlaneStore) -> None:
        self._store = store

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

    def _make_lock_id(self) -> str:
        return f"lock_{uuid.uuid4().hex[:12]}"

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

    # ── Public API ────────────────────────────────────────────────────────────

    def list_locks(self, *, scope_type: LockScopeType | None = None) -> list[LockRecord]:
        self._sweep_expired_leases()
        locks = self._store.list_locks()
        if scope_type is not None:
            locks = [lock for lock in locks if lock.scope_type == scope_type]
        return sorted(locks, key=lambda lock: lock.updated_at, reverse=True)

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
