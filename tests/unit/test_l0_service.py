"""Unit tests for the local L0 control-plane service."""

from __future__ import annotations

import pytest

from ttadev.control_plane import ControlPlaneService, RunStatus, TaskClaimError, TaskStatus


def test_create_task_with_project(tmp_path) -> None:
    service = ControlPlaneService(tmp_path)
    task = service.create_task(
        "Create queue",
        description="Need a local queue",
        project_name="alpha",
        requested_role="developer",
    )
    assert task.project_name == "alpha"
    assert task.project_id is not None
    assert task.requested_role == "developer"


def test_claim_task_creates_run_and_lease(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Implement lease handling")

    claim = service.claim_task(task.id, agent_role="developer", lease_ttl_seconds=60)

    assert claim.task.status == TaskStatus.IN_PROGRESS
    assert claim.run.status == RunStatus.ACTIVE
    assert claim.run.agent_id == "agent-1"
    assert claim.lease.holder_agent_id == "agent-1"


def test_second_agent_cannot_claim_active_task(monkeypatch, tmp_path) -> None:
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Protect active lease")

    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service.claim_task(task.id, lease_ttl_seconds=60)

    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-2")
    with pytest.raises(TaskClaimError):
        service.claim_task(task.id, lease_ttl_seconds=60)


def test_heartbeat_extends_lease(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Keep lease alive")

    claim = service.claim_task(task.id, lease_ttl_seconds=30)
    renewed = service.heartbeat_run(claim.run.id, lease_ttl_seconds=60)

    assert renewed.expires_at >= claim.lease.expires_at


def test_complete_run_marks_task_completed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Finish work")

    claim = service.claim_task(task.id, lease_ttl_seconds=60)
    run = service.complete_run(claim.run.id, summary="Implemented control plane")
    updated_task = service.get_task(task.id)

    assert run.status == RunStatus.COMPLETED
    assert updated_task.status == TaskStatus.COMPLETED
    assert service.get_lease_for_run(claim.run.id) is None


def test_release_run_returns_task_to_pending(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
    monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Release for another agent")

    claim = service.claim_task(task.id, lease_ttl_seconds=60)
    run = service.release_run(claim.run.id, reason="Need another reviewer")
    updated_task = service.get_task(task.id)

    assert run.status == RunStatus.RELEASED
    assert updated_task.status == TaskStatus.PENDING
    assert updated_task.active_run_id is None
