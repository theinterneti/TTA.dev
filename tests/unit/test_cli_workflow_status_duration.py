"""Tests for _fmt_seconds, _fmt_step_duration helpers and the dur column in workflow status."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ttadev.cli.control import _fmt_seconds, _fmt_step_duration, handle_control_command
from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import WorkflowStepRecord, WorkflowStepStatus
from ttadev.observability import agent_identity

# ── _fmt_seconds unit tests ───────────────────────────────────────────────────


def test_fmt_seconds_under_60() -> None:
    assert _fmt_seconds(45.0) == "45s"


def test_fmt_seconds_under_3600() -> None:
    assert _fmt_seconds(125.0) == "2m 5s"


def test_fmt_seconds_hours() -> None:
    assert _fmt_seconds(3725.0) == "1h 2m"


# ── _fmt_step_duration unit tests ─────────────────────────────────────────────


def _make_step(
    *,
    status: WorkflowStepStatus,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> WorkflowStepRecord:
    return WorkflowStepRecord(
        step_index=0,
        agent_name="test-agent",
        status=status,
        started_at=started_at,
        completed_at=completed_at,
    )


def test_fmt_step_duration_running_with_started_at() -> None:
    """RUNNING step with started_at set returns a non-'-' duration string."""
    started = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    step = _make_step(status=WorkflowStepStatus.RUNNING, started_at=started)
    result = _fmt_step_duration(step)
    assert result != "-"
    assert re.search(r"\d+s|\d+m \d+s|\d+h \d+m", result)


def test_fmt_step_duration_running_no_started_at() -> None:
    """RUNNING step with started_at=None returns '-'."""
    step = _make_step(status=WorkflowStepStatus.RUNNING, started_at=None)
    assert _fmt_step_duration(step) == "-"


def test_fmt_step_duration_completed_both_timestamps() -> None:
    """COMPLETED step with both timestamps returns non-'-' string."""
    started = (datetime.now(UTC) - timedelta(seconds=90)).isoformat()
    completed = datetime.now(UTC).isoformat()
    step = _make_step(
        status=WorkflowStepStatus.COMPLETED,
        started_at=started,
        completed_at=completed,
    )
    result = _fmt_step_duration(step)
    assert result != "-"
    assert re.search(r"\d+s|\d+m \d+s|\d+h \d+m", result)


def test_fmt_step_duration_completed_missing_timestamp() -> None:
    """COMPLETED step with started_at=None returns '-'."""
    completed = datetime.now(UTC).isoformat()
    step = _make_step(
        status=WorkflowStepStatus.COMPLETED,
        started_at=None,
        completed_at=completed,
    )
    assert _fmt_step_duration(step) == "-"


def test_fmt_step_duration_completed_missing_completed_at() -> None:
    """COMPLETED step with completed_at=None returns '-'."""
    started = datetime.now(UTC).isoformat()
    step = _make_step(
        status=WorkflowStepStatus.COMPLETED,
        started_at=started,
        completed_at=None,
    )
    assert _fmt_step_duration(step) == "-"


def test_fmt_step_duration_pending() -> None:
    """PENDING step returns '-'."""
    step = _make_step(status=WorkflowStepStatus.PENDING)
    assert _fmt_step_duration(step) == "-"


# ── integration test: dur column appears in workflow status output ─────────────


def _set_agent_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", "agent-test")
    monkeypatch.setenv("TTA_AGENT_TOOL", "copilot")


def _make_status_args(tmp_path: Path, task_id: str):  # type: ignore[no-untyped-def]
    import argparse

    return argparse.Namespace(
        control_command="workflow",
        control_workflow_command="status",
        task_id=task_id,
        data_dir=str(tmp_path),
    )


def test_workflow_status_dur_column_in_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """workflow status output contains a duration string for COMPLETED and RUNNING steps."""
    _set_agent_identity(monkeypatch)
    service = ControlPlaneService(tmp_path)
    claim = service.start_tracked_workflow(
        workflow_name="dur-test-wf",
        workflow_goal="test duration column",
        step_agents=["developer", "reviewer"],
    )
    task_id = claim.run.task_id

    # Complete the first step
    service.mark_workflow_step_running(task_id, step_index=0)
    service.record_workflow_step_result(
        task_id, step_index=0, result_summary="done", confidence=0.9
    )

    # Start (but don't complete) the second step
    service.mark_workflow_step_running(task_id, step_index=1)

    args = _make_status_args(tmp_path, task_id)
    rc = handle_control_command(args, tmp_path)

    assert rc == 0
    out = capsys.readouterr().out

    # There should be at least one duration string (e.g. "0s", "1s", "1m 5s", etc.)
    assert re.search(r"\d+s|\d+m \d+s|\d+h \d+m", out), (
        f"Expected duration string in output, got:\n{out}"
    )
