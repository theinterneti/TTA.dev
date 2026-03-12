"""Unit tests for SessionManager — Task 3 (RED → GREEN).

All file I/O uses tmp_path to stay hermetic.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import ttadev.observability.agent_identity as _agent_identity_mod
from ttadev.observability.session_manager import SessionManager
from ttadev.observability.span_processor import ProcessedSpan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_span(
    *,
    primitive_type: str | None = "RetryPrimitive",
    started_at: str | None = None,
) -> ProcessedSpan:
    return ProcessedSpan(
        span_id="s1",
        trace_id="t1",
        parent_span_id=None,
        name="retry.execute",
        provider="anthropic",
        model="claude-sonnet-4-6",
        agent_role="backend-engineer",
        workflow_id="wf-1",
        primitive_type=primitive_type,
        started_at=started_at or datetime.now(timezone.utc).isoformat(),
        duration_ms=150.0,
        status="success",
    )


@pytest.fixture
def mgr(tmp_path: Path) -> SessionManager:
    return SessionManager(data_dir=tmp_path)


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


def test_start_session_creates_metadata_file(mgr: SessionManager, tmp_path: Path) -> None:
    session = mgr.start_session()
    meta_file = tmp_path / "sessions" / f"{session.id}.json"
    assert meta_file.exists()
    data = json.loads(meta_file.read_text())
    assert data["id"] == session.id
    assert data["ended_at"] is None


def test_start_session_returns_session_with_uuid(mgr: SessionManager) -> None:
    session = mgr.start_session()
    # UUID4 has 36 characters with hyphens
    assert len(session.id) == 36
    assert session.id.count("-") == 4


def test_start_session_records_project_path(mgr: SessionManager) -> None:
    session = mgr.start_session()
    assert session.project_path != ""


def test_end_session_sets_ended_at(mgr: SessionManager, tmp_path: Path) -> None:
    session = mgr.start_session()
    mgr.end_session()
    meta_file = tmp_path / "sessions" / f"{session.id}.json"
    data = json.loads(meta_file.read_text())
    assert data["ended_at"] is not None


def test_get_current_returns_active_session(mgr: SessionManager) -> None:
    session = mgr.start_session()
    current = mgr.get_current()
    assert current is not None
    assert current.id == session.id


def test_get_current_returns_none_after_end(mgr: SessionManager) -> None:
    mgr.start_session()
    mgr.end_session()
    assert mgr.get_current() is None


def test_get_current_returns_none_with_no_session(mgr: SessionManager) -> None:
    assert mgr.get_current() is None


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


def test_list_sessions_empty_initially(mgr: SessionManager) -> None:
    assert mgr.list_sessions() == []


def test_list_sessions_newest_first(tmp_path: Path) -> None:
    # Three separate managers sharing the same data_dir to simulate three sessions
    m1 = SessionManager(data_dir=tmp_path)
    s1 = m1.start_session()
    m1.end_session()

    time.sleep(0.01)  # ensure distinct timestamps

    m2 = SessionManager(data_dir=tmp_path)
    m2.start_session()
    m2.end_session()

    time.sleep(0.01)

    m3 = SessionManager(data_dir=tmp_path)
    s3 = m3.start_session()
    m3.end_session()

    sessions = m3.list_sessions()
    assert len(sessions) == 3
    ids = [s.id for s in sessions]
    assert ids[0] == s3.id  # newest first
    assert ids[-1] == s1.id  # oldest last


# ---------------------------------------------------------------------------
# add_span / get_session_spans
# ---------------------------------------------------------------------------


def test_add_span_persists_to_jsonl(mgr: SessionManager, tmp_path: Path) -> None:
    session = mgr.start_session()
    mgr.add_span(session.id, _make_span())
    spans_file = tmp_path / "sessions" / session.id / "spans.jsonl"
    assert spans_file.exists()
    lines = [ln for ln in spans_file.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1


def test_get_session_spans_returns_all(mgr: SessionManager) -> None:
    session = mgr.start_session()
    for _ in range(3):
        mgr.add_span(session.id, _make_span())
    spans = mgr.get_session_spans(session.id)
    assert len(spans) == 3


def test_get_session_spans_empty_when_none_added(mgr: SessionManager) -> None:
    session = mgr.start_session()
    assert mgr.get_session_spans(session.id) == []


# ---------------------------------------------------------------------------
# get_active_primitive_names
# ---------------------------------------------------------------------------


def test_get_active_primitive_names_deduplicates(mgr: SessionManager) -> None:
    session = mgr.start_session()
    mgr.add_span(session.id, _make_span(primitive_type="RetryPrimitive"))
    mgr.add_span(session.id, _make_span(primitive_type="RetryPrimitive"))
    mgr.add_span(session.id, _make_span(primitive_type="CachePrimitive"))
    names = mgr.get_active_primitive_names(session.id)
    assert sorted(names) == ["CachePrimitive", "RetryPrimitive"]


def test_get_active_primitive_names_excludes_none(mgr: SessionManager) -> None:
    session = mgr.start_session()
    mgr.add_span(session.id, _make_span(primitive_type=None))
    names = mgr.get_active_primitive_names(session.id)
    assert names == []


# ---------------------------------------------------------------------------
# get_recently_active
# ---------------------------------------------------------------------------


def test_get_recently_active_includes_recent_span(mgr: SessionManager) -> None:
    session = mgr.start_session()
    mgr.add_span(session.id, _make_span(primitive_type="RetryPrimitive"))
    recent = mgr.get_recently_active(session.id, within_seconds=30)
    assert "RetryPrimitive" in recent


def test_get_recently_active_excludes_old_span(mgr: SessionManager) -> None:
    session = mgr.start_session()
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    mgr.add_span(session.id, _make_span(primitive_type="RetryPrimitive", started_at=old_time))
    recent = mgr.get_recently_active(session.id, within_seconds=30)
    assert "RetryPrimitive" not in recent


# ---------------------------------------------------------------------------
# Agent tool detection
# ---------------------------------------------------------------------------


def test_detect_agent_tool_env_override(tmp_path: Path) -> None:
    _agent_identity_mod._AGENT_TOOL = None
    os.environ["TTA_AGENT_TOOL"] = "copilot"
    try:
        mgr = SessionManager(data_dir=tmp_path)
        session = mgr.start_session()
        assert session.agent_tool == "copilot"
    finally:
        del os.environ["TTA_AGENT_TOOL"]
        _agent_identity_mod._AGENT_TOOL = None


def test_detect_agent_tool_fallback(tmp_path: Path) -> None:
    _agent_identity_mod._AGENT_TOOL = None
    # Remove any env vars that would trigger detection
    for key in ("TTA_AGENT_TOOL", "CLAUDE_CODE", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLINE"):
        os.environ.pop(key, None)
    # Don't set TERM_PROGRAM to a known value for this test
    original = os.environ.pop("TERM_PROGRAM", None)
    try:
        mgr = SessionManager(data_dir=tmp_path)
        session = mgr.start_session()
        # Should be "unknown" or a detected value — not crash
        assert isinstance(session.agent_tool, str)
        assert len(session.agent_tool) > 0
    finally:
        if original is not None:
            os.environ["TERM_PROGRAM"] = original
        _agent_identity_mod._AGENT_TOOL = None


def test_detect_agent_tool_claude_code_env(tmp_path: Path) -> None:
    _agent_identity_mod._AGENT_TOOL = None
    os.environ.pop("TTA_AGENT_TOOL", None)
    os.environ["CLAUDE_CODE"] = "1"
    try:
        mgr = SessionManager(data_dir=tmp_path)
        session = mgr.start_session()
        assert session.agent_tool == "claude-code"
    finally:
        del os.environ["CLAUDE_CODE"]
        _agent_identity_mod._AGENT_TOOL = None
