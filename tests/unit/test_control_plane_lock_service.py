"""Unit tests for lock-aware L0 control-plane service behavior."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ttadev.control_plane import ControlPlaneService, LockScopeType, TaskLockError
from ttadev.control_plane.models import TaskRecord
from ttadev.observability import agent_identity


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str,
    agent_tool: str = "copilot",
) -> None:
    """Pin the process agent identity for control-plane tests."""
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


def test_task_record_defaults_missing_locks_to_empty() -> None:
    """Deserialize legacy task payloads without lock declarations."""
    task = TaskRecord.from_dict(
        {
            "id": "task_legacy",
            "title": "Legacy task",
            "description": "",
            "created_at": "2026-03-23T00:00:00+00:00",
            "updated_at": "2026-03-23T00:00:00+00:00",
            "status": "pending",
            "priority": "normal",
        }
    )

    assert task.workspace_locks == []
    assert task.file_locks == []


def test_claim_acquires_declared_workspace_and_file_locks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Auto-acquire declared locks during claim."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Locking task",
        workspace_locks=["alpha-workspace"],
        file_locks=["src/demo.py"],
    )

    claim = service.claim_task(task.id)
    locks = service.list_locks()

    assert claim.task.workspace_locks == ["alpha-workspace"]
    assert claim.task.file_locks == ["src/demo.py"]
    assert {(lock.scope_type, lock.scope_value) for lock in locks} == {
        (LockScopeType.WORKSPACE, "alpha-workspace"),
        (LockScopeType.FILE, "src/demo.py"),
    }


def test_manual_same_run_lock_reacquisition_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return the existing lock when the same run reacquires it."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Manual lock task")
    claim = service.claim_task(task.id)

    first = service.acquire_workspace_lock(task.id, claim.run.id, "shared-workspace")
    second = service.acquire_workspace_lock(task.id, claim.run.id, "shared-workspace")

    assert first.id == second.id
    assert len(service.list_locks()) == 1


def test_conflicting_lock_blocks_second_claim_without_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject conflicting claim-time locks and avoid partial state."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    service = ControlPlaneService(tmp_path)
    first_task = service.create_task("First", workspace_locks=["shared-workspace"])
    first_claim = service.claim_task(first_task.id)

    _set_agent_identity(monkeypatch, agent_id="agent-two")
    second_task = service.create_task("Second", workspace_locks=["shared-workspace"])

    with pytest.raises(TaskLockError, match="shared-workspace"):
        service.claim_task(second_task.id)

    second_task_after = service.get_task(second_task.id)
    assert second_task_after.status.value == "pending"
    assert second_task_after.active_run_id is None
    assert second_task_after.claimed_by_agent_id is None
    assert service.get_lease_for_run(first_claim.run.id) is not None
    assert len(service.list_runs()) == 1
    assert len(service.list_locks()) == 1


def test_locks_release_on_complete_release_and_expiry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Release locks when runs complete, release, or expire."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    service = ControlPlaneService(tmp_path)

    complete_task = service.create_task("Complete", workspace_locks=["complete-workspace"])
    complete_claim = service.claim_task(complete_task.id)
    service.complete_run(complete_claim.run.id, summary="done")
    assert service.list_locks() == []

    release_task = service.create_task("Release", workspace_locks=["release-workspace"])
    release_claim = service.claim_task(release_task.id)
    service.release_run(release_claim.run.id, reason="handoff")
    assert service.list_locks() == []

    expire_task = service.create_task("Expire", workspace_locks=["expire-workspace"])
    expire_claim = service.claim_task(expire_task.id, lease_ttl_seconds=0.01)
    assert service.list_locks()
    time.sleep(0.02)
    service.list_tasks()
    assert service.get_run(expire_claim.run.id).status.value == "expired"
    assert service.list_locks() == []


def test_file_lock_paths_are_normalized_and_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Normalize safe relative paths and reject escaping paths."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("File locks", file_locks=["./src\\demo.py"])
    claim = service.claim_task(task.id)

    assert claim.task.file_locks == ["src/demo.py"]
    assert service.list_locks()[0].scope_value == "src/demo.py"

    bad_task = service.create_task("Manual bad path")
    bad_claim = service.claim_task(bad_task.id)
    with pytest.raises(TaskLockError, match="repo"):
        service.acquire_file_lock(bad_task.id, bad_claim.run.id, "../secrets.txt")
