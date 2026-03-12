"""SessionManager — session lifecycle, persistence, and span indexing.

Storage layout:
  .tta/sessions/{session_id}.json         — session metadata
  .tta/sessions/{session_id}/spans.jsonl  — append-only span log
"""

import json
import socket
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from ttadev.observability.agent_identity import get_agent_id, get_agent_tool
from ttadev.observability.span_processor import ProcessedSpan


@dataclass
class Session:
    """Metadata for a single observability session."""

    id: str
    started_at: str  # ISO 8601
    ended_at: str | None
    agent_tool: str  # "claude-code" | "copilot" | "cline" | "unknown"
    project_path: str
    hostname: str
    # Stable per-process identifier from FileSpanExporter._AGENT_ID.
    # None for sessions created before agent identity was introduced.
    agent_id: str | None = None
    # ProjectSession id this session belongs to (if any).
    project_id: str | None = None


class SessionManager:
    """Manages session lifecycle and provides span storage/query."""

    def __init__(self, data_dir: Path | str = ".tta") -> None:
        self._data_dir = Path(data_dir)
        self._sessions_dir = self._data_dir / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._current: Session | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_session(self) -> Session:
        """Create and persist a new session. Returns the active session."""
        session = Session(
            id=str(uuid.uuid4()),
            started_at=datetime.now(UTC).isoformat(),
            ended_at=None,
            agent_tool=get_agent_tool(),
            project_path=str(Path.cwd()),
            hostname=socket.gethostname(),
            agent_id=get_agent_id(),
        )
        self._current = session
        self._persist_session(session)
        # Create span directory eagerly
        self._span_dir(session.id).mkdir(parents=True, exist_ok=True)
        return session

    def end_session(self) -> None:
        """Mark the current session as ended."""
        if self._current is None:
            return
        self._current.ended_at = datetime.now(UTC).isoformat()
        self._persist_session(self._current)
        self._current = None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_current(self) -> Session | None:
        """Return the currently active session, or None."""
        return self._current

    def list_sessions(self) -> list[Session]:
        """Return all sessions newest-first."""
        sessions: list[Session] = []
        for meta_file in self._sessions_dir.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
                sessions.append(Session(**data))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        return sessions

    def get_or_create_agent_session(
        self, agent_id: str, agent_tool: str, project_id: str | None = None
    ) -> Session:
        """Return the existing session for this agent_id, or create a new one.

        Called by the ingestion loop when a span carries a tta_agent_id that
        doesn't match any known session.  Creating happens at most once per
        unique agent_id — subsequent calls return the cached session.
        """
        # Fast path: scan in-memory sessions first
        for meta_file in self._sessions_dir.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
                if data.get("agent_id") == agent_id:
                    session = Session(**data)
                    # Back-fill project_id if span now carries one
                    if project_id and not session.project_id:
                        session.project_id = project_id
                        self._persist_session(session)
                    return session
            except Exception:
                continue

        # Not found — create a new session for this agent
        session = Session(
            id=str(uuid.uuid4()),
            started_at=datetime.now(UTC).isoformat(),
            ended_at=None,
            agent_tool=agent_tool,
            project_path=str(Path.cwd()),
            hostname=socket.gethostname(),
            agent_id=agent_id,
            project_id=project_id,
        )
        self._persist_session(session)
        self._span_dir(session.id).mkdir(parents=True, exist_ok=True)
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Return a specific session by ID, or None."""
        meta_file = self._sessions_dir / f"{session_id}.json"
        if not meta_file.exists():
            return None
        try:
            data = json.loads(meta_file.read_text())
            return Session(**data)
        except Exception:
            return None

    def resolve_session_id(self, prefix: str) -> str:
        """Resolve a full or partial session ID prefix to a full ID.

        Raises ValueError if the prefix matches zero or more than one session.
        """
        all_ids = [f.stem for f in self._sessions_dir.glob("*.json")]
        matches = [sid for sid in all_ids if sid.startswith(prefix)]
        if not matches:
            raise ValueError(f"No session matching prefix: {prefix!r}")
        if len(matches) > 1:
            listed = ", ".join(sorted(matches)[:5])
            raise ValueError(f"Ambiguous prefix {prefix!r}: {len(matches)} matches — {listed}")
        return matches[0]

    # ------------------------------------------------------------------
    # Span ingestion
    # ------------------------------------------------------------------

    def add_span(self, session_id: str, span: ProcessedSpan) -> None:
        """Append a ProcessedSpan to the session's spans.jsonl."""
        span_file = self._span_dir(session_id) / "spans.jsonl"
        with span_file.open("a") as f:
            f.write(json.dumps(asdict(span)) + "\n")

    def get_session_spans(self, session_id: str) -> list[ProcessedSpan]:
        """Return all spans for a session."""
        span_file = self._span_dir(session_id) / "spans.jsonl"
        if not span_file.exists():
            return []
        spans: list[ProcessedSpan] = []
        for line in span_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                spans.append(ProcessedSpan(**json.loads(line)))
            except Exception:
                continue
        return spans

    # ------------------------------------------------------------------
    # Live overlay helpers
    # ------------------------------------------------------------------

    def get_active_primitive_names(self, session_id: str) -> list[str]:
        """Return deduplicated list of primitive types used in this session."""
        seen: set[str] = set()
        for span in self.get_session_spans(session_id):
            if span.primitive_type:
                seen.add(span.primitive_type)
        return sorted(seen)

    def get_recently_active(self, session_id: str, within_seconds: int = 30) -> list[str]:
        """Return primitive types active within the last N seconds."""
        now = datetime.now(UTC)
        seen: set[str] = set()
        for span in self.get_session_spans(session_id):
            if not span.primitive_type or not span.started_at:
                continue
            try:
                started = datetime.fromisoformat(span.started_at)
                # Make offset-aware if naive
                if started.tzinfo is None:
                    started = started.replace(tzinfo=UTC)
                age = (now - started).total_seconds()
                if age <= within_seconds:
                    seen.add(span.primitive_type)
            except ValueError:
                continue
        return sorted(seen)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _span_dir(self, session_id: str) -> Path:
        d = self._sessions_dir / session_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _persist_session(self, session: Session) -> None:
        meta_file = self._sessions_dir / f"{session.id}.json"
        meta_file.write_text(json.dumps(asdict(session), indent=2))
