"""State models for the local L0 control plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


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


class GateType(StrEnum):
    """Supported gate categories for gated L0 tasks."""

    APPROVAL = "approval"
    POLICY = "policy"
    REVIEW = "review"


class GateStatus(StrEnum):
    """Decision state for a task gate."""

    PENDING = "pending"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"


class GateHistoryAction(StrEnum):
    """Supported gate audit history actions."""

    DECISION = "decision"
    REOPENED = "reopened"


class WorkflowTrackingStatus(StrEnum):
    """Lifecycle state for a tracked workflow run."""

    RUNNING = "running"
    COMPLETED = "completed"
    QUIT = "quit"
    FAILED = "failed"
    ESCALATED = "escalated"


class WorkflowStepStatus(StrEnum):
    """Execution state for a tracked workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    QUIT = "quit"
    FAILED = "failed"


class WorkflowGateDecisionOutcome(StrEnum):
    """Approval-gate outcomes recorded for tracked workflow steps."""

    CONTINUE = "continue"
    SKIP = "skip"
    EDIT = "edit"
    QUIT = "quit"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class LockScopeType(StrEnum):
    """Supported coordination lock scopes."""

    WORKSPACE = "workspace"
    FILE = "file"


@dataclass
class GatePolicy:
    """Named policy governing when a gate auto-approves or escalates.

    Replaces the opaque ``policy_name`` string for callers that want a
    typed representation. Convert to a ``policy_name`` string for storage:
    use ``GatePolicy.to_policy_name()`` when passing to service methods.
    """

    name: str
    approve_above_confidence: float | None = None
    escalate_below_confidence: float | None = None

    def to_policy_name(self) -> str:
        """Serialize to the policy_name string format used by the service."""
        if self.approve_above_confidence is not None:
            return f"auto:confidence≥{self.approve_above_confidence}"
        if self.escalate_below_confidence is not None:
            return f"auto:escalate_below:{self.escalate_below_confidence}"
        return "auto:always"


@dataclass
class GateHistoryEntry:
    """Append-only audit entry for a gate mutation."""

    action: GateHistoryAction
    from_status: GateStatus | None
    to_status: GateStatus
    actor: str
    occurred_at: str
    summary: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Serialize the history entry for JSON persistence."""
        return {
            "action": self.action.value,
            "from_status": self.from_status.value if self.from_status is not None else None,
            "to_status": self.to_status.value,
            "actor": self.actor,
            "occurred_at": self.occurred_at,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateHistoryEntry:
        """Deserialize a history entry from persisted JSON data."""
        from_status = data.get("from_status")
        return cls(
            action=GateHistoryAction(str(data["action"])),
            from_status=GateStatus(str(from_status)) if from_status is not None else None,
            to_status=GateStatus(str(data["to_status"])),
            actor=str(data["actor"]),
            occurred_at=str(data["occurred_at"]),
            summary=data.get("summary"),
        )


@dataclass
class WorkflowGateDecisionRecord:
    """Recorded approval-gate decision for a tracked workflow step."""

    decision: WorkflowGateDecisionOutcome
    occurred_at: str
    summary: str | None = None
    policy_name: str | None = None
    """Non-None when the gate decision was made automatically by policy.

    Examples: ``"auto:confidence≥0.85"``, ``"auto:always"``.
    None indicates a human made the decision interactively.
    """

    def to_dict(self) -> dict[str, str | None]:
        """Serialize the workflow gate-decision record for JSON persistence."""
        return {
            "decision": self.decision.value,
            "occurred_at": self.occurred_at,
            "summary": self.summary,
            "policy_name": self.policy_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowGateDecisionRecord:
        """Deserialize a workflow gate-decision record from persisted JSON data."""
        return cls(
            decision=WorkflowGateDecisionOutcome(str(data["decision"])),
            occurred_at=str(data["occurred_at"]),
            summary=data.get("summary"),
            policy_name=data.get("policy_name"),
        )


@dataclass
class WorkflowStepRecord:
    """Tracked execution state for a single workflow step."""

    step_index: int
    agent_name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    linked_gate_id: str | None = None
    attempts: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    last_result_summary: str | None = None
    last_confidence: float | None = None
    gate_decision: WorkflowGateDecisionOutcome | None = None
    gate_history: list[WorkflowGateDecisionRecord] = field(default_factory=list)
    trace_id: str | None = None
    """OTel trace ID (32-hex) stamped when the step transitions to RUNNING."""
    span_id: str | None = None
    """OTel span ID (16-hex) stamped when the step transitions to RUNNING."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the workflow step record for JSON persistence."""
        return {
            "step_index": self.step_index,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "linked_gate_id": self.linked_gate_id,
            "attempts": self.attempts,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_result_summary": self.last_result_summary,
            "last_confidence": self.last_confidence,
            "gate_decision": self.gate_decision.value if self.gate_decision is not None else None,
            "gate_history": [entry.to_dict() for entry in self.gate_history],
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStepRecord:
        """Deserialize a workflow step record from persisted JSON data."""
        gate_history: list[WorkflowGateDecisionRecord] = []
        for entry in data.get("gate_history", []):
            if not isinstance(entry, dict):
                continue
            try:
                gate_history.append(WorkflowGateDecisionRecord.from_dict(entry))
            except (KeyError, TypeError, ValueError):
                continue

        gate_decision = data.get("gate_decision")
        last_confidence = data.get("last_confidence")
        return cls(
            step_index=int(data["step_index"]),
            agent_name=str(data["agent_name"]),
            status=WorkflowStepStatus(str(data.get("status") or WorkflowStepStatus.PENDING.value)),
            linked_gate_id=data.get("linked_gate_id"),
            attempts=int(data.get("attempts", 0)),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            last_result_summary=data.get("last_result_summary"),
            last_confidence=float(last_confidence) if last_confidence is not None else None,
            gate_decision=(
                WorkflowGateDecisionOutcome(str(gate_decision))
                if gate_decision is not None
                else None
            ),
            gate_history=gate_history,
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
        )


@dataclass
class WorkflowTrackingRecord:
    """Tracked execution metadata for a workflow-backed control-plane task."""

    workflow_name: str
    workflow_goal: str
    total_steps: int
    status: WorkflowTrackingStatus = WorkflowTrackingStatus.RUNNING
    current_step_index: int | None = None
    current_agent: str | None = None
    steps: list[WorkflowStepRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the workflow tracking record for JSON persistence."""
        return {
            "workflow_name": self.workflow_name,
            "workflow_goal": self.workflow_goal,
            "total_steps": self.total_steps,
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "current_agent": self.current_agent,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowTrackingRecord:
        """Deserialize workflow tracking metadata from persisted JSON data."""
        return cls(
            workflow_name=str(data["workflow_name"]),
            workflow_goal=str(data["workflow_goal"]),
            total_steps=int(data["total_steps"]),
            status=WorkflowTrackingStatus(
                str(data.get("status") or WorkflowTrackingStatus.RUNNING.value)
            ),
            current_step_index=data.get("current_step_index"),
            current_agent=data.get("current_agent"),
            steps=[
                WorkflowStepRecord.from_dict(step)
                for step in data.get("steps", [])
                if isinstance(step, dict)
            ],
        )


@dataclass
class GateRecord:
    """Approval, policy, or review gate stored on a task."""

    id: str
    gate_type: GateType
    label: str
    required: bool = True
    assigned_role: str | None = None
    assigned_agent_id: str | None = None
    assigned_decider: str | None = None
    status: GateStatus = GateStatus.PENDING
    decided_by: str | None = None
    decided_at: str | None = None
    summary: str | None = None
    policy_name: str | None = None
    """Evaluation rule for POLICY-type gates.

    When set on a ``GateType.POLICY`` gate the service auto-evaluates the gate
    after a workflow step records its confidence score.

    Supported patterns:
      ``"auto:always"``           — always approve
      ``"auto:confidence≥{n}"``   — approve when confidence ≥ n (0.0–1.0)
      ``"auto:confidence<{n}"``   — request changes when confidence < n
    """
    history: list[GateHistoryEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the gate record for JSON persistence."""
        return {
            "id": self.id,
            "gate_type": self.gate_type.value,
            "label": self.label,
            "required": self.required,
            "assigned_role": self.assigned_role,
            "assigned_agent_id": self.assigned_agent_id,
            "assigned_decider": self.assigned_decider,
            "status": self.status.value,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "summary": self.summary,
            "policy_name": self.policy_name,
            "history": [entry.to_dict() for entry in self.history],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateRecord:
        """Deserialize a gate record from persisted JSON data."""
        history: list[GateHistoryEntry] = []
        for entry in data.get("history", []):
            if not isinstance(entry, dict):
                continue
            try:
                history.append(GateHistoryEntry.from_dict(entry))
            except (KeyError, TypeError, ValueError):
                continue

        return cls(
            id=str(data["id"]),
            gate_type=GateType(str(data["gate_type"])),
            label=str(data["label"]),
            required=bool(data.get("required", True)),
            assigned_role=data.get("assigned_role"),
            assigned_agent_id=data.get("assigned_agent_id"),
            assigned_decider=data.get("assigned_decider"),
            status=GateStatus(str(data.get("status") or GateStatus.PENDING.value)),
            decided_by=data.get("decided_by"),
            decided_at=data.get("decided_at"),
            summary=data.get("summary"),
            policy_name=data.get("policy_name"),
            history=history,
        )


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
    workflow: WorkflowTrackingRecord | None = None
    gates: list[GateRecord] = field(default_factory=list)
    workspace_locks: list[str] = field(default_factory=list)
    file_locks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
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
            "workflow": self.workflow.to_dict() if self.workflow is not None else None,
            "gates": [gate.to_dict() for gate in self.gates],
            "workspace_locks": list(self.workspace_locks),
            "file_locks": list(self.file_locks),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskRecord:
        workflow = data.get("workflow")
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
            workflow=(
                WorkflowTrackingRecord.from_dict(workflow) if isinstance(workflow, dict) else None
            ),
            gates=[
                GateRecord.from_dict(gate)
                for gate in data.get("gates", [])
                if isinstance(gate, dict)
            ],
            workspace_locks=[
                str(lock)
                for lock in data.get("workspace_locks", [])
                if isinstance(lock, str) and lock.strip()
            ],
            file_locks=[
                str(lock)
                for lock in data.get("file_locks", [])
                if isinstance(lock, str) and lock.strip()
            ],
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
    trace_id: str | None = None
    """OTel trace ID (32-hex) stamped at claim time when a span context is available."""
    span_id: str | None = None
    """OTel span ID (16-hex) stamped at claim time when a span context is available."""

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
            "trace_id": self.trace_id,
            "span_id": self.span_id,
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
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
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
class LockRecord:
    """Exclusive workspace or file lock held by an active run."""

    id: str
    scope_type: LockScopeType
    scope_value: str
    task_id: str
    run_id: str
    agent_id: str
    acquired_at: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        """Serialize the lock record for JSON persistence."""
        return {
            "id": self.id,
            "scope_type": self.scope_type.value,
            "scope_value": self.scope_value,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "acquired_at": self.acquired_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> LockRecord:
        """Deserialize a lock record from persisted JSON data."""
        return cls(
            id=str(data["id"]),
            scope_type=LockScopeType(str(data["scope_type"])),
            scope_value=str(data["scope_value"]),
            task_id=str(data["task_id"]),
            run_id=str(data["run_id"]),
            agent_id=str(data["agent_id"]),
            acquired_at=str(data["acquired_at"]),
            updated_at=str(data["updated_at"]),
        )


@dataclass
class ClaimResult:
    """Composite result from claiming a task."""

    task: TaskRecord
    run: RunRecord
    lease: LeaseRecord
