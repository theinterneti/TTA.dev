"""Tests for ControlPlaneStore file locking (no lost-update race condition)."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ttadev.control_plane.models import TaskRecord, TaskStatus
from ttadev.control_plane.store import ControlPlaneStore


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _make_task(task_id: str) -> TaskRecord:
    return TaskRecord(
        id=task_id,
        title=f"Task {task_id}",
        description="",
        created_at=_now(),
        updated_at=_now(),
        status=TaskStatus.PENDING,
    )


@pytest.mark.slow
def test_put_task_concurrent_no_lost_updates(tmp_path: Path) -> None:
    """Two threads calling put_task concurrently must not lose any writes.

    Each thread writes 50 unique tasks; after both finish all 100 tasks
    must be present in the store (no silent overwrite from a race).
    """
    store = ControlPlaneStore(tmp_path)
    errors: list[Exception] = []

    def write_tasks(prefix: str, count: int) -> None:
        for i in range(count):
            try:
                task = _make_task(f"{prefix}-{i}")
                store.put_task(task)
            except Exception as exc:
                errors.append(exc)

    t1 = threading.Thread(target=write_tasks, args=("thread-a", 50))
    t2 = threading.Thread(target=write_tasks, args=("thread-b", 50))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Threads raised exceptions: {errors}"

    all_tasks = store.list_tasks()
    assert len(all_tasks) == 100, (
        f"Expected 100 tasks but found {len(all_tasks)} — lost updates occurred"
    )
    all_ids = {t.id for t in all_tasks}
    for i in range(50):
        assert f"thread-a-{i}" in all_ids, f"Missing thread-a-{i}"
        assert f"thread-b-{i}" in all_ids, f"Missing thread-b-{i}"
