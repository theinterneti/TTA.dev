"""Unit tests for the local L0 control-plane store."""

from datetime import UTC, datetime

from ttadev.control_plane.models import LeaseRecord, RunRecord, RunStatus, TaskRecord, TaskStatus
from ttadev.control_plane.store import ControlPlaneStore


def _now() -> str:
    return datetime.now(UTC).isoformat()


def test_task_roundtrip(tmp_path) -> None:
    store = ControlPlaneStore(tmp_path)
    task = TaskRecord(
        id="task_123",
        title="Add control plane",
        description="Build first L0 slice",
        created_at=_now(),
        updated_at=_now(),
        status=TaskStatus.PENDING,
        project_name="tta-dev",
    )
    store.put_task(task)

    loaded = store.get_task(task.id)
    assert loaded is not None
    assert loaded.id == task.id
    assert loaded.project_name == "tta-dev"


def test_run_roundtrip(tmp_path) -> None:
    store = ControlPlaneStore(tmp_path)
    run = RunRecord(
        id="run_123",
        task_id="task_123",
        agent_id="agent-1",
        agent_tool="copilot",
        started_at=_now(),
        updated_at=_now(),
        status=RunStatus.ACTIVE,
    )
    store.put_run(run)

    loaded = store.get_run(run.id)
    assert loaded is not None
    assert loaded.id == run.id
    assert loaded.agent_tool == "copilot"


def test_lease_roundtrip_and_delete(tmp_path) -> None:
    store = ControlPlaneStore(tmp_path)
    lease = LeaseRecord(
        task_id="task_123",
        run_id="run_123",
        holder_agent_id="agent-1",
        acquired_at=_now(),
        last_heartbeat_at=_now(),
        expires_at=_now(),
    )
    store.put_lease(lease)

    loaded = store.get_lease_for_task("task_123")
    assert loaded is not None
    assert loaded.run_id == "run_123"

    store.delete_lease("task_123")
    assert store.get_lease_for_task("task_123") is None
