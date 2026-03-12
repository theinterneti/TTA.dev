"""tta session subcommands: list, show, current, end, spans."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ttadev.observability.session_manager import Session, SessionManager


def _fmt_dt(iso: str | None) -> str:
    """Format an ISO datetime to a compact UTC display string."""
    if iso is None:
        return "(active)"
    # e.g. "2026-03-10T19:51:45.078611+00:00" → "2026-03-10 19:51 UTC"
    return iso[:16].replace("T", " ") + " UTC"


def _span_count(mgr: SessionManager, session_id: str) -> int:
    return len(mgr.get_session_spans(session_id))


def _resolve(mgr: SessionManager, prefix: str) -> str:
    """Resolve prefix → full ID, printing errors and exiting on failure."""
    try:
        return mgr.resolve_session_id(prefix)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def list_sessions(data_dir: Path, limit: int, project_name: str | None) -> None:
    """Print a table of recent sessions."""
    mgr = SessionManager(data_dir=data_dir)
    sessions = mgr.list_sessions()  # newest-first

    # Filter by project name if requested
    if project_name is not None:
        project_file = data_dir / "projects" / f"{project_name}.json"
        if not project_file.exists():
            print(f"No sessions for project: {project_name}")
            return
        meta = json.loads(project_file.read_text())
        project_id = meta["id"]
        sessions = [s for s in sessions if s.project_id == project_id]

    if not sessions:
        print("No sessions found.")
        return

    sessions = sessions[:limit]

    # Header
    col = [8, 19, 6, 12, 5]
    header = (
        f"{'SESSION ID':<{col[0]}}  "
        f"{'STARTED':<{col[1]}}  "
        f"{'STATUS':<{col[2]}}  "
        f"{'AGENT':<{col[3]}}  "
        f"{'SPANS':>{col[4]}}"
    )
    print(header)
    print("-" * len(header))

    for s in sessions:
        status = "active" if s.ended_at is None else "ended"
        spans = _span_count(mgr, s.id)
        print(
            f"{s.id[:8]:<{col[0]}}  "
            f"{_fmt_dt(s.started_at):<{col[1]}}  "
            f"{status:<{col[2]}}  "
            f"{s.agent_tool:<{col[3]}}  "
            f"{spans:>{col[4]}}"
        )


def show_session(session_id_prefix: str, data_dir: Path) -> None:
    """Print full details for one session."""
    mgr = SessionManager(data_dir=data_dir)
    full_id = _resolve(mgr, session_id_prefix)
    s = mgr.get_session(full_id)
    if s is None:
        print(f"Session not found: {full_id}", file=sys.stderr)
        sys.exit(1)

    status = "(active)" if s.ended_at is None else _fmt_dt(s.ended_at)
    spans = _span_count(mgr, full_id)
    primitives = mgr.get_active_primitive_names(full_id)

    print(f"Session: {s.id}")
    print(f"  started_at:   {_fmt_dt(s.started_at)}")
    print(f"  ended_at:     {status}")
    print(f"  agent_tool:   {s.agent_tool}")
    print(f"  project_path: {s.project_path}")
    print(f"  hostname:     {s.hostname}")
    print(f"  spans:        {spans}")
    if primitives:
        print(f"  primitives:   {', '.join(sorted(primitives))}")


def _find_active(mgr: SessionManager) -> Session | None:
    """Find the most recently started session with no ended_at (disk-backed)."""
    for s in mgr.list_sessions():  # newest-first
        if s.ended_at is None:
            return s
    return None


def current_session(data_dir: Path) -> None:
    """Print the active session, or exit 1 if none."""
    mgr = SessionManager(data_dir=data_dir)
    s = _find_active(mgr)
    if s is None:
        print("No active session.", file=sys.stderr)
        sys.exit(1)

    spans = _span_count(mgr, s.id)
    primitives = mgr.get_active_primitive_names(s.id)
    print(f"Session: {s.id[:8]} (active)")
    print(f"  agent_tool:  {s.agent_tool}")
    print(f"  spans:       {spans}")
    if primitives:
        print(f"  primitives:  {', '.join(sorted(primitives))}")


def end_session(data_dir: Path) -> None:
    """End the active session, writing ended_at."""
    mgr = SessionManager(data_dir=data_dir)
    s = _find_active(mgr)
    if s is None:
        print("No active session to end.", file=sys.stderr)
        return

    # Load session into manager's in-memory state so end_session() can persist it
    mgr._current = s  # noqa: SLF001
    mgr.end_session()
    print(f"Ended session: {s.id}")


def list_spans(
    session_id_prefix: str,
    data_dir: Path,
    limit: int,
    primitive_filter: str | None,
) -> None:
    """Print a table of spans for a session."""
    mgr = SessionManager(data_dir=data_dir)
    full_id = _resolve(mgr, session_id_prefix)

    spans = mgr.get_session_spans(full_id)

    if primitive_filter:
        spans = [sp for sp in spans if sp.primitive_type == primitive_filter]

    if not spans:
        print("No spans recorded.")
        return

    spans = spans[:limit]

    col = [8, 24, 20, 10, 7]
    header = (
        f"{'SPAN ID':<{col[0]}}  "
        f"{'NAME':<{col[1]}}  "
        f"{'PRIMITIVE':<{col[2]}}  "
        f"{'DURATION':>{col[3]}}  "
        f"{'STATUS':<{col[4]}}"
    )
    print(header)
    print("-" * len(header))

    for sp in spans:
        prim = sp.primitive_type or "-"
        dur = f"{sp.duration_ms:.0f}ms" if sp.duration_ms else "-"
        print(
            f"{sp.span_id[:8]:<{col[0]}}  "
            f"{sp.name:<{col[1]}}  "
            f"{prim:<{col[2]}}  "
            f"{dur:>{col[3]}}  "
            f"{sp.status:<{col[4]}}"
        )
