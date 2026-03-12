"""Unit tests for ttadev.cli.session — T2-T7 (RED → GREEN)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ttadev.cli.session import (
    current_session,
    end_session,
    list_sessions,
    list_spans,
    show_session,
)
from ttadev.observability.session_manager import Session, SessionManager
from ttadev.observability.span_processor import ProcessedSpan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(
    tmp_path: Path,
    *,
    ended: bool = False,
    agent_tool: str = "claude-code",
    project_id: str | None = None,
    minutes_ago: int = 0,
) -> Session:
    mgr = SessionManager(data_dir=tmp_path)
    s = mgr.start_session()
    # Patch started_at for ordering tests
    if minutes_ago:
        started = (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat()
        s = Session(
            id=s.id,
            started_at=started,
            ended_at=None,
            agent_tool=agent_tool,
            project_path=s.project_path,
            hostname=s.hostname,
            agent_id=s.agent_id,
            project_id=project_id,
        )
        meta_file = tmp_path / "sessions" / f"{s.id}.json"
        meta_file.write_text(json.dumps({k: v for k, v in s.__dict__.items()}))
    if ended:
        mgr.end_session()
        # Re-read to get ended_at
        meta_file = tmp_path / "sessions" / f"{s.id}.json"
        data = json.loads(meta_file.read_text())
        s = Session(**data)
    return s


def _make_span(session_id: str, tmp_path: Path, primitive_type: str = "RetryPrimitive") -> None:
    mgr = SessionManager(data_dir=tmp_path)
    span = ProcessedSpan(
        span_id="s1",
        trace_id="t1",
        parent_span_id=None,
        name="retry.execute",
        provider="anthropic",
        model="claude-sonnet-4-6",
        agent_role="engineer",
        workflow_id="wf-1",
        primitive_type=primitive_type,
        started_at=datetime.now(UTC).isoformat(),
        duration_ms=150.0,
        status="success",
    )
    mgr.add_span(session_id, span)


# ---------------------------------------------------------------------------
# T2 — list_sessions
# ---------------------------------------------------------------------------


def test_list_sessions_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    list_sessions(tmp_path, limit=10, project_name=None)
    out = capsys.readouterr().out
    assert "No sessions found" in out


def test_list_sessions_shows_session(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path, ended=True)
    list_sessions(tmp_path, limit=10, project_name=None)
    out = capsys.readouterr().out
    assert s.id[:8] in out
    assert "claude-code" in out
    assert "ended" in out


def test_list_sessions_active_status(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _make_session(tmp_path, ended=False)
    list_sessions(tmp_path, limit=10, project_name=None)
    out = capsys.readouterr().out
    assert "active" in out


def test_list_sessions_newest_first(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old = _make_session(tmp_path, ended=True, minutes_ago=10)
    new = _make_session(tmp_path, ended=True, minutes_ago=1)
    list_sessions(tmp_path, limit=10, project_name=None)
    out = capsys.readouterr().out
    assert out.index(new.id[:8]) < out.index(old.id[:8])


def test_list_sessions_limit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for i in range(5):
        _make_session(tmp_path, ended=True, minutes_ago=i + 1)
    list_sessions(tmp_path, limit=2, project_name=None)
    out = capsys.readouterr().out
    # Count data rows only (exclude header and separator)
    rows = [
        ln
        for ln in out.splitlines()
        if ln and not ln.startswith("SESSION") and not ln.startswith("-")
    ]
    assert len(rows) == 2


def test_list_sessions_filter_by_project(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Wire project_id directly via _make_session
    mgr = SessionManager(data_dir=tmp_path)
    s1 = mgr.start_session()
    mgr.end_session()
    # Patch project_id into s1's JSON
    meta = json.loads((tmp_path / "sessions" / f"{s1.id}.json").read_text())
    meta["project_id"] = "proj-abc"
    (tmp_path / "sessions" / f"{s1.id}.json").write_text(json.dumps(meta))

    s2 = mgr.start_session()
    mgr.end_session()

    # Also create the project file so filtering can resolve name → id
    (tmp_path / "projects").mkdir(exist_ok=True)
    (tmp_path / "projects" / "myproject.json").write_text(
        json.dumps(
            {"id": "proj-abc", "name": "myproject", "created_at": "2026-01-01T00:00:00+00:00"}
        )
    )

    list_sessions(tmp_path, limit=10, project_name="myproject")
    out = capsys.readouterr().out
    assert s1.id[:8] in out
    assert s2.id[:8] not in out


# ---------------------------------------------------------------------------
# T3 — show_session
# ---------------------------------------------------------------------------


def test_show_session_full_id(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    show_session(s.id, tmp_path)
    out = capsys.readouterr().out
    assert s.id in out
    assert "claude-code" in out


def test_show_session_prefix(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    show_session(s.id[:8], tmp_path)
    out = capsys.readouterr().out
    assert s.id in out


def test_show_session_not_found_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        show_session("00000000", tmp_path)
    assert exc.value.code == 1


def test_show_session_ambiguous_exits_1(tmp_path: Path) -> None:
    import unittest.mock as mock

    ids = ["ffffffff-0000-0000-0000-000000000001", "ffffffff-0000-0000-0000-000000000002"]
    id_iter = iter(ids)
    with mock.patch(
        "ttadev.observability.session_manager.uuid.uuid4", side_effect=lambda: next(id_iter)
    ):
        m1 = SessionManager(data_dir=tmp_path)
        m1.start_session()
        m1.end_session()
        m2 = SessionManager(data_dir=tmp_path)
        m2.start_session()
        m2.end_session()

    with pytest.raises(SystemExit) as exc:
        show_session("ffffffff", tmp_path)
    assert exc.value.code == 1


def test_show_session_shows_span_count(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    _make_span(s.id, tmp_path)
    _make_span(s.id, tmp_path)
    show_session(s.id, tmp_path)
    out = capsys.readouterr().out
    assert "2" in out


# ---------------------------------------------------------------------------
# T4 — current_session
# ---------------------------------------------------------------------------


def test_current_session_active(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    mgr = SessionManager(data_dir=tmp_path)
    s = mgr.start_session()
    current_session(tmp_path)
    out = capsys.readouterr().out
    assert s.id[:8] in out
    assert "active" in out


def test_current_session_none_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        current_session(tmp_path)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# T5 — end_session
# ---------------------------------------------------------------------------


def test_end_session_writes_ended_at(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    mgr = SessionManager(data_dir=tmp_path)
    s = mgr.start_session()
    end_session(tmp_path)
    meta = json.loads((tmp_path / "sessions" / f"{s.id}.json").read_text())
    assert meta["ended_at"] is not None
    assert s.id[:8] in capsys.readouterr().out


def test_end_session_no_active_exits_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    end_session(tmp_path)  # no active session — should not raise
    err = capsys.readouterr().err
    assert "No active" in err


# ---------------------------------------------------------------------------
# T6 — list_spans
# ---------------------------------------------------------------------------


def test_list_spans_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    list_spans(s.id, tmp_path, limit=20, primitive_filter=None)
    out = capsys.readouterr().out
    assert "No spans" in out


def test_list_spans_shows_columns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    _make_span(s.id, tmp_path, primitive_type="RetryPrimitive")
    list_spans(s.id, tmp_path, limit=20, primitive_filter=None)
    out = capsys.readouterr().out
    assert "RetryPrimitive" in out
    assert "150" in out  # duration_ms


def test_list_spans_limit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    for _ in range(5):
        _make_span(s.id, tmp_path)
    list_spans(s.id, tmp_path, limit=2, primitive_filter=None)
    out = capsys.readouterr().out
    rows = [ln for ln in out.splitlines() if ln and not ln.startswith("SPAN") and "Primitive" in ln]
    assert len(rows) == 2


def test_list_spans_filter_primitive(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    s = _make_session(tmp_path)
    _make_span(s.id, tmp_path, primitive_type="RetryPrimitive")
    _make_span(s.id, tmp_path, primitive_type="CachePrimitive")
    list_spans(s.id, tmp_path, limit=20, primitive_filter="CachePrimitive")
    out = capsys.readouterr().out
    assert "CachePrimitive" in out
    assert "RetryPrimitive" not in out


def test_list_spans_not_found_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        list_spans("00000000", tmp_path, limit=20, primitive_filter=None)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# T7 — argparse dispatcher (subprocess)
# ---------------------------------------------------------------------------


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


def test_cli_session_help_exits_zero() -> None:
    r = _run(["session", "--help"])
    assert r.returncode == 0
    assert "list" in r.stdout
    assert "show" in r.stdout
    assert "current" in r.stdout
    assert "end" in r.stdout
    assert "spans" in r.stdout


def test_cli_session_list_subprocess(tmp_path: Path) -> None:
    r = _run(["--data-dir", str(tmp_path), "session", "list"])
    assert r.returncode == 0
    assert "No sessions found" in r.stdout


def test_cli_session_current_no_session_exits_1(tmp_path: Path) -> None:
    r = _run(["--data-dir", str(tmp_path), "session", "current"])
    assert r.returncode == 1


def test_cli_session_show_not_found_exits_1(tmp_path: Path) -> None:
    r = _run(["--data-dir", str(tmp_path), "session", "show", "00000000"])
    assert r.returncode == 1


def test_cli_session_spans_not_found_exits_1(tmp_path: Path) -> None:
    r = _run(["--data-dir", str(tmp_path), "session", "spans", "00000000"])
    assert r.returncode == 1


def test_cli_session_end_no_session_exits_0(tmp_path: Path) -> None:
    r = _run(["--data-dir", str(tmp_path), "session", "end"])
    assert r.returncode == 0
    assert "No active" in r.stderr
