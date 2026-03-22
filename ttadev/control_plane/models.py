"""State models for the local L0 control plane."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TaskStatus(StrEnum):
    """Lifecycle state for a control-plane task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RunStatus(StrEnum):
    """Lifecycle state for a claimed run."""

    ACTIVE = "active"
    COMPLETED = "completed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass
class TaskRecord:
    """A unit of work managed by the L0 control plane."""

    id: str
    title: str
    description: str
    created_at: str
    updated_at: str
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "normal"
    project_id: str | None = None
    project_name: str | None = None
    requested_role: str | None = None
    active_run_id: str | None = None
    claimed_by_agent_id: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "priority": self.priority,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "requested_role": self.requested_role,
            "active_run_id": self.active_run_id,
            "claimed_by_agent_id": self.claimed_by_agent_id,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> TaskRecord:
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            description=str(data.get("description") or ""),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            status=TaskStatus(str(data.get("status") or TaskStatus.PENDING.value)),
            priority=str(data.get("priority") or "normal"),
            project_id=data.get("project_id"),
            project_name=data.get("project_name"),
            requested_role=data.get("requested_role"),
            active_run_id=data.get("active_run_id"),
            claimed_by_agent_id=data.get("claimed_by_agent_id"),
            completed_at=data.get("completed_at"),
        )


@dataclass
class RunRecord:
    """A concrete execution attempt against a task."""

    id: str
    task_id: str
    agent_id: str
    agent_tool: str
    started_at: str
    updated_at: str
    status: RunStatus = RunStatus.ACTIVE
    agent_role: str | None = None
    session_id: str | None = None
    ended_at: str | None = None
    summary: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "agent_tool": self.agent_tool,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "agent_role": self.agent_role,
            "session_id": self.session_id,
            "ended_at": self.ended_at,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> RunRecord:
        return cls(
            id=str(data["id"]),
            task_id=str(data["task_id"]),
            agent_id=str(data["agent_id"]),
            agent_tool=str(data.get("agent_tool") or "unknown"),
            started_at=str(data["started_at"]),
            updated_at=str(data["updated_at"]),
            status=RunStatus(str(data.get("status") or RunStatus.ACTIVE.value)),
            agent_role=data.get("agent_role"),
            session_id=data.get("session_id"),
            ended_at=data.get("ended_at"),
            summary=data.get("summary"),
        )


@dataclass
class LeaseRecord:
    """Ephemeral ownership for an active task run."""

    task_id: str
    run_id: str
    holder_agent_id: str
    acquired_at: str
    last_heartbeat_at: str
    expires_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "holder_agent_id": self.holder_agent_id,
            "acquired_at": self.acquired_at,
            "last_heartbeat_at": self.last_heartbeat_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> LeaseRecord:
        return cls(
            task_id=str(data["task_id"]),
            run_id=str(data["run_id"]),
            holder_agent_id=str(data["holder_agent_id"]),
            acquired_at=str(data["acquired_at"]),
            last_heartbeat_at=str(data["last_heartbeat_at"]),
            expires_at=str(data["expires_at"]),
        )


@dataclass
class ClaimResult:
    """Composite result from claiming a task."""

    task: TaskRecord
    run: RunRecord
    lease: LeaseRecord
