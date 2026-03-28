"""JSON-backed persistence for the local L0 control plane."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ttadev.control_plane.models import (
    LeaseRecord,
    LockRecord,
    LockScopeType,
    RunRecord,
    TaskRecord,
)


class ControlPlaneStore:
    """Durable local storage under ``.tta/control``."""

    def __init__(self, data_dir: Path | str = ".tta") -> None:
        self._root = Path(data_dir) / "control"
        self._root.mkdir(parents=True, exist_ok=True)
        self._tasks_file = self._root / "tasks.json"
        self._runs_file = self._root / "runs.json"
        self._leases_file = self._root / "leases.json"
        self._locks_file = self._root / "locks.json"

    def _read_map(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _write_map(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        tmp.replace(path)

    def list_tasks(self) -> list[TaskRecord]:
        data = self._read_map(self._tasks_file)
        return [TaskRecord.from_dict(value) for value in data.values()]

    def get_task(self, task_id: str) -> TaskRecord | None:
        data = self._read_map(self._tasks_file)
        payload = data.get(task_id)
        return TaskRecord.from_dict(payload) if isinstance(payload, dict) else None

    def put_task(self, task: TaskRecord) -> None:
        data = self._read_map(self._tasks_file)
        data[task.id] = task.to_dict()
        self._write_map(self._tasks_file, data)

    def list_runs(self) -> list[RunRecord]:
        data = self._read_map(self._runs_file)
        return [RunRecord.from_dict(value) for value in data.values()]

    def get_run(self, run_id: str) -> RunRecord | None:
        data = self._read_map(self._runs_file)
        payload = data.get(run_id)
        return RunRecord.from_dict(payload) if isinstance(payload, dict) else None

    def put_run(self, run: RunRecord) -> None:
        data = self._read_map(self._runs_file)
        data[run.id] = run.to_dict()
        self._write_map(self._runs_file, data)

    def list_leases(self) -> list[LeaseRecord]:
        data = self._read_map(self._leases_file)
        return [LeaseRecord.from_dict(value) for value in data.values()]

    def get_lease_for_task(self, task_id: str) -> LeaseRecord | None:
        data = self._read_map(self._leases_file)
        payload = data.get(task_id)
        return LeaseRecord.from_dict(payload) if isinstance(payload, dict) else None

    def get_lease_for_run(self, run_id: str) -> LeaseRecord | None:
        for lease in self.list_leases():
            if lease.run_id == run_id:
                return lease
        return None

    def put_lease(self, lease: LeaseRecord) -> None:
        data = self._read_map(self._leases_file)
        data[lease.task_id] = lease.to_dict()
        self._write_map(self._leases_file, data)

    def delete_lease(self, task_id: str) -> None:
        data = self._read_map(self._leases_file)
        if task_id in data:
            del data[task_id]
            self._write_map(self._leases_file, data)

    def list_locks(self) -> list[LockRecord]:
        data = self._read_map(self._locks_file)
        return [LockRecord.from_dict(value) for value in data.values()]

    def get_lock(self, lock_id: str) -> LockRecord | None:
        data = self._read_map(self._locks_file)
        payload = data.get(lock_id)
        return LockRecord.from_dict(payload) if isinstance(payload, dict) else None

    def get_lock_for_scope(self, scope_type: LockScopeType, scope_value: str) -> LockRecord | None:
        for lock in self.list_locks():
            if lock.scope_type == scope_type and lock.scope_value == scope_value:
                return lock
        return None

    def list_locks_for_run(self, run_id: str) -> list[LockRecord]:
        return [lock for lock in self.list_locks() if lock.run_id == run_id]

    def put_lock(self, lock: LockRecord) -> None:
        data = self._read_map(self._locks_file)
        data[lock.id] = lock.to_dict()
        self._write_map(self._locks_file, data)

    def delete_lock(self, lock_id: str) -> None:
        data = self._read_map(self._locks_file)
        if lock_id in data:
            del data[lock_id]
            self._write_map(self._locks_file, data)
