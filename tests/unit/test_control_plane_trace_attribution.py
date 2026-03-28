"""Unit tests for OTel trace attribution on RunRecord and WorkflowStepRecord."""

from __future__ import annotations

from pathlib import Path

import pytest

from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import RunRecord, WorkflowStepRecord
from ttadev.observability import agent_identity

_FAKE_TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
_FAKE_SPAN_ID = "00f067aa0ba902b7"


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str,
    agent_tool: str = "copilot",
) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


# ── RunRecord model ───────────────────────────────────────────────────────────


def test_run_record_defaults_trace_fields_to_none() -> None:
    """Legacy RunRecord payloads without trace fields deserialize cleanly."""
    run = RunRecord.from_dict(
        {
            "id": "run_legacy",
            "task_id": "task_1",
            "agent_id": "agent-1",
            "agent_tool": "copilot",
            "started_at": "2026-03-27T00:00:00+00:00",
            "updated_at": "2026-03-27T00:00:00+00:00",
            "status": "active",
        }
    )

    assert run.trace_id is None
    assert run.span_id is None


def test_run_record_round_trips_trace_fields() -> None:
    """trace_id and span_id survive serialization round-trip."""
    run = RunRecord.from_dict(
        {
            "id": "run_traced",
            "task_id": "task_1",
            "agent_id": "agent-1",
            "agent_tool": "copilot",
            "started_at": "2026-03-27T00:00:00+00:00",
            "updated_at": "2026-03-27T00:00:00+00:00",
            "status": "active",
            "trace_id": _FAKE_TRACE_ID,
            "span_id": _FAKE_SPAN_ID,
        }
    )

    serialized = run.to_dict()
    assert serialized["trace_id"] == _FAKE_TRACE_ID
    assert serialized["span_id"] == _FAKE_SPAN_ID

    restored = RunRecord.from_dict(serialized)
    assert restored.trace_id == _FAKE_TRACE_ID
    assert restored.span_id == _FAKE_SPAN_ID


# ── WorkflowStepRecord model ──────────────────────────────────────────────────


def test_workflow_step_defaults_trace_fields_to_none() -> None:
    """Legacy WorkflowStepRecord payloads without trace fields deserialize cleanly."""
    step = WorkflowStepRecord.from_dict(
        {
            "step_index": 0,
            "agent_name": "agent-a",
            "status": "pending",
        }
    )

    assert step.trace_id is None
    assert step.span_id is None


def test_workflow_step_round_trips_trace_fields() -> None:
    """trace_id and span_id survive serialization round-trip on WorkflowStepRecord."""
    step = WorkflowStepRecord.from_dict(
        {
            "step_index": 0,
            "agent_name": "agent-a",
            "status": "running",
            "trace_id": _FAKE_TRACE_ID,
            "span_id": _FAKE_SPAN_ID,
        }
    )

    serialized = step.to_dict()
    assert serialized["trace_id"] == _FAKE_TRACE_ID
    assert serialized["span_id"] == _FAKE_SPAN_ID

    restored = WorkflowStepRecord.from_dict(serialized)
    assert restored.trace_id == _FAKE_TRACE_ID
    assert restored.span_id == _FAKE_SPAN_ID


# ── Service: claim_task stamps trace context ──────────────────────────────────


def test_claim_task_stamps_trace_id_on_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """claim_task stores the caller-supplied trace_id and span_id on the RunRecord."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Traced task")

    claim = service.claim_task(
        task.id,
        trace_id=_FAKE_TRACE_ID,
        span_id=_FAKE_SPAN_ID,
    )

    assert claim.run.trace_id == _FAKE_TRACE_ID
    assert claim.run.span_id == _FAKE_SPAN_ID

    # Persisted and re-loaded
    reloaded_run = service.get_run(claim.run.id)
    assert reloaded_run is not None
    assert reloaded_run.trace_id == _FAKE_TRACE_ID
    assert reloaded_run.span_id == _FAKE_SPAN_ID


def test_claim_task_without_trace_context_leaves_fields_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """claim_task without trace context leaves trace fields as None."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    task = service.create_task("Untraced task")

    claim = service.claim_task(task.id)

    assert claim.run.trace_id is None
    assert claim.run.span_id is None


# ── Service: mark_workflow_step_running stamps trace context ──────────────────


def test_mark_workflow_step_running_stamps_trace_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mark_workflow_step_running stores trace_id and span_id on the step record."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="verify trace attribution",
        step_agents=["agent-test"],
    )
    task_id = claim.run.task_id

    updated = service.mark_workflow_step_running(
        task_id,
        step_index=0,
        trace_id=_FAKE_TRACE_ID,
        span_id=_FAKE_SPAN_ID,
    )

    step = updated.workflow.steps[0]  # type: ignore[union-attr]
    assert step.trace_id == _FAKE_TRACE_ID
    assert step.span_id == _FAKE_SPAN_ID

    # Persisted and re-loaded
    reloaded = service.get_task(task_id)
    assert reloaded.workflow is not None
    assert reloaded.workflow.steps[0].trace_id == _FAKE_TRACE_ID
    assert reloaded.workflow.steps[0].span_id == _FAKE_SPAN_ID


def test_mark_workflow_step_running_without_trace_leaves_fields_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mark_workflow_step_running without trace context leaves trace fields as None."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="untraced step",
        step_agents=["agent-test"],
    )
    task_id = claim.run.task_id

    updated = service.mark_workflow_step_running(task_id, step_index=0)

    step = updated.workflow.steps[0]  # type: ignore[union-attr]
    assert step.trace_id is None
    assert step.span_id is None


def test_trace_id_cleared_on_step_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Retrying a step replaces the previous trace context with the new one."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="test-wf",
        workflow_goal="verify trace replacement on retry",
        step_agents=["agent-test"],
    )
    task_id = claim.run.task_id

    old_trace = "aaaabbbbccccdddd" * 2
    service.mark_workflow_step_running(task_id, step_index=0, trace_id=old_trace)
    service.mark_workflow_step_failed(task_id, step_index=0, error_summary="transient error")

    new_trace = _FAKE_TRACE_ID
    updated = service.mark_workflow_step_running(
        task_id, step_index=0, trace_id=new_trace, span_id=_FAKE_SPAN_ID
    )

    step = updated.workflow.steps[0]  # type: ignore[union-attr]
    assert step.trace_id == new_trace
    assert step.span_id == _FAKE_SPAN_ID
