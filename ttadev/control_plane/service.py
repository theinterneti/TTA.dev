"""Thin facade exposing the full ControlPlaneService public API.

The implementation is split into focused domain services:
- LeaseService  — lock and lease management
- TaskService   — task CRUD, gates, and workflow cleanup
- RunService    — run lifecycle, ownership, and claim
- WorkflowService — tracked workflow step and gate operations

This module re-exports all error classes so that existing
``from ttadev.control_plane.service import XxxError`` imports continue
to work without modification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Re-export error classes — must appear before domain imports so that
# ``from ttadev.control_plane.service import ControlPlaneError`` works.
from ttadev.control_plane.exceptions import (  # noqa: F401
    ControlPlaneError,
    RunNotFoundError,
    TaskClaimError,
    TaskGateError,
    TaskLockError,
    TaskNotFoundError,
)
from ttadev.control_plane.lease_service import LeaseService
from ttadev.control_plane.models import (
    ActiveStepInfo,
    ClaimResult,
    GateStatus,
    LeaseRecord,
    LockRecord,
    LockScopeType,
    RunRecord,
    RunStatus,
    TaskRecord,
    TaskStatus,
    WorkflowGateDecisionOutcome,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.run_service import RunService
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.control_plane.task_service import TaskService
from ttadev.control_plane.workflow_service import WorkflowService

# Re-exported so tests can monkeypatch ``ttadev.control_plane.service.get_agent_id``.
from ttadev.observability.agent_identity import get_agent_id, get_agent_tool  # noqa: F401
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import SessionManager


class ControlPlaneService:
    """High-level operations for tasks, runs, and leases.

    Delegates to focused domain services; see the individual service
    modules for implementation details.
    """

    def __init__(self, data_dir: Path | str = ".tta") -> None:
        self._data_dir = Path(data_dir)
        self._store = ControlPlaneStore(self._data_dir)
        self._projects = ProjectSessionManager(self._data_dir)
        self._sessions = SessionManager(self._data_dir)

        self._lease = LeaseService(self._store)
        self._task = TaskService(self._store, self._projects, self._sessions, self._lease)
        self._run = RunService(self._store, self._projects, self._sessions, self._task, self._lease)
        self._workflow = WorkflowService(self._store, self._task, self._run, self._lease)

    # ── Task operations ───────────────────────────────────────────────────────

    def create_task(
        self,
        title: str,
        description: str = "",
        *,
        project_name: str | None = None,
        requested_role: str | None = None,
        priority: str = "normal",
        gates: list[dict[str, Any]] | None = None,
        workspace_locks: list[str] | None = None,
        file_locks: list[str] | None = None,
    ) -> TaskRecord:
        return self._task.create_task(
            title,
            description,
            project_name=project_name,
            requested_role=requested_role,
            priority=priority,
            gates=gates,
            workspace_locks=workspace_locks,
            file_locks=file_locks,
        )

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_name: str | None = None,
    ) -> list[TaskRecord]:
        return self._task.list_tasks(status=status, project_name=project_name)

    def get_task(self, task_id: str) -> TaskRecord:
        return self._task.get_task(task_id)

    def explain_active_step(self, task_id: str) -> ActiveStepInfo | None:
        return self._task.explain_active_step(task_id)

    def decide_gate(
        self,
        task_id: str,
        gate_id: str,
        *,
        status: GateStatus,
        decided_by: str | None = None,
        decision_role: str | None = None,
        summary: str = "",
    ) -> TaskRecord:
        return self._task.decide_gate(
            task_id,
            gate_id,
            status=status,
            decided_by=decided_by,
            decision_role=decision_role,
            summary=summary,
        )

    def reopen_gate(
        self,
        task_id: str,
        gate_id: str,
        *,
        reopened_by: str | None = None,
        summary: str = "",
    ) -> TaskRecord:
        return self._task.reopen_gate(task_id, gate_id, reopened_by=reopened_by, summary=summary)

    @staticmethod
    def _parse_policy_decision(
        policy_name: str,
        confidence: float | None,
    ) -> tuple[GateStatus, str] | None:
        return TaskService._parse_policy_decision(policy_name, confidence)

    def expire_abandoned_workflows(self) -> list[str]:
        return self._task.expire_abandoned_workflows()

    def cleanup_orphaned_steps(self, task_id: str) -> int:
        return self._task.cleanup_orphaned_steps(task_id)

    # ── Run operations ────────────────────────────────────────────────────────

    def claim_task(
        self,
        task_id: str,
        *,
        agent_role: str | None = None,
        lease_ttl_seconds: float = 300.0,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> ClaimResult:
        return self._run.claim_task(
            task_id,
            agent_role=agent_role,
            lease_ttl_seconds=lease_ttl_seconds,
            trace_id=trace_id,
            span_id=span_id,
        )

    def list_runs(self, *, status: RunStatus | None = None) -> list[RunRecord]:
        return self._run.list_runs(status=status)

    def get_run(self, run_id: str) -> RunRecord:
        return self._run.get_run(run_id)

    def get_lease_for_run(self, run_id: str) -> LeaseRecord | None:
        return self._run.get_lease_for_run(run_id)

    def list_active_ownership(
        self,
        *,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._run.list_active_ownership(project_id=project_id, session_id=session_id)

    def heartbeat_run(self, run_id: str, *, lease_ttl_seconds: float = 300.0) -> LeaseRecord:
        return self._run.heartbeat_run(run_id, lease_ttl_seconds=lease_ttl_seconds)

    def complete_run(self, run_id: str, *, summary: str = "") -> RunRecord:
        return self._run.complete_run(run_id, summary=summary)

    def release_run(self, run_id: str, *, reason: str = "") -> RunRecord:
        return self._run.release_run(run_id, reason=reason)

    def finalize_tracked_workflow(
        self,
        task_id: str,
        run_id: str,
        *,
        status: WorkflowTrackingStatus,
        summary: str = "",
    ) -> RunRecord:
        return self._run.finalize_tracked_workflow(task_id, run_id, status=status, summary=summary)

    # ── Lock / lease operations ───────────────────────────────────────────────

    def list_locks(self, *, scope_type: LockScopeType | None = None) -> list[LockRecord]:
        return self._lease.list_locks(scope_type=scope_type)

    def acquire_workspace_lock(self, task_id: str, run_id: str, workspace_name: str) -> LockRecord:
        return self._lease.acquire_workspace_lock(task_id, run_id, workspace_name)

    def acquire_file_lock(self, task_id: str, run_id: str, file_path: str) -> LockRecord:
        return self._lease.acquire_file_lock(task_id, run_id, file_path)

    def release_lock(self, lock_id: str) -> None:
        return self._lease.release_lock(lock_id)

    def release_locks_for_run(self, run_id: str) -> None:
        return self._lease.release_locks_for_run(run_id)

    # ── Tracked workflow operations ───────────────────────────────────────────

    def start_tracked_workflow(
        self,
        *,
        workflow_name: str,
        workflow_goal: str,
        step_agents: list[str],
        project_name: str | None = None,
        extra_gates: list[dict[str, Any]] | None = None,
        lease_ttl_seconds: float = 300.0,
    ) -> ClaimResult:
        return self._workflow.start_tracked_workflow(
            workflow_name=workflow_name,
            workflow_goal=workflow_goal,
            step_agents=step_agents,
            project_name=project_name,
            extra_gates=extra_gates,
            lease_ttl_seconds=lease_ttl_seconds,
        )

    def attach_workflow_to_task(
        self,
        task_id: str,
        *,
        workflow_name: str,
        workflow_goal: str,
        step_agents: list[str],
        extra_gates: list[dict[str, Any]] | None = None,
        lease_ttl_seconds: float = 300.0,
    ) -> ClaimResult:
        return self._workflow.attach_workflow_to_task(
            task_id,
            workflow_name=workflow_name,
            workflow_goal=workflow_goal,
            step_agents=step_agents,
            extra_gates=extra_gates,
            lease_ttl_seconds=lease_ttl_seconds,
        )

    def mark_workflow_step_running(
        self,
        task_id: str,
        *,
        step_index: int,
        trace_id: str | None = None,
        span_id: str | None = None,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
    ) -> TaskRecord:
        return self._workflow.mark_workflow_step_running(
            task_id,
            step_index=step_index,
            trace_id=trace_id,
            span_id=span_id,
            hindsight_bank_id=hindsight_bank_id,
            hindsight_document_id=hindsight_document_id,
        )

    def record_workflow_step_result(
        self,
        task_id: str,
        *,
        step_index: int,
        result_summary: str,
        confidence: float,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
    ) -> TaskRecord:
        return self._workflow.record_workflow_step_result(
            task_id,
            step_index=step_index,
            result_summary=result_summary,
            confidence=confidence,
            hindsight_bank_id=hindsight_bank_id,
            hindsight_document_id=hindsight_document_id,
        )

    def record_workflow_gate_outcome(
        self,
        task_id: str,
        *,
        step_index: int,
        decision: WorkflowGateDecisionOutcome,
        summary: str = "",
        policy_name: str | None = None,
    ) -> TaskRecord:
        return self._workflow.record_workflow_gate_outcome(
            task_id,
            step_index=step_index,
            decision=decision,
            summary=summary,
            policy_name=policy_name,
        )

    def mark_workflow_step_failed(
        self,
        task_id: str,
        *,
        step_index: int,
        error_summary: str,
    ) -> TaskRecord:
        return self._workflow.mark_workflow_step_failed(
            task_id,
            step_index=step_index,
            error_summary=error_summary,
        )
