"""Shared helpers and utilities for MCP tool handlers."""

import contextlib
from collections.abc import Generator
from typing import Any

import structlog

try:
    from mcp.types import ToolAnnotations
except ImportError:
    ToolAnnotations = None  # type: ignore

from ttadev.control_plane import ControlPlaneError, ControlPlaneService
from ttadev.control_plane.models import LeaseRecord, LockRecord, RunRecord, TaskRecord
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import SessionManager

logger = structlog.get_logger("tta_dev.mcp")

# ── Code-input size guard ──────────────────────────────────────────────────────
_MAX_CODE_CHARS = 25_000


def _check_code_size(code: str) -> dict[str, str] | None:
    """Return an error payload if code exceeds the character limit, else None."""
    if len(code) > _MAX_CODE_CHARS:
        return {
            "error": (
                f"Code input exceeds the {_MAX_CODE_CHARS:,}-character limit "
                f"({len(code):,} chars received). "
                "Pass a smaller snippet or a single function."
            )
        }
    return None


def _paginate(items: list[Any], limit: int, offset: int) -> dict[str, Any]:
    """Slice a list and return pagination metadata."""
    page = items[offset : offset + limit]
    total = len(items)
    has_more = offset + limit < total
    return {
        "items": page,
        "total_count": total,
        "has_more": has_more,
        "next_offset": offset + limit if has_more else None,
    }


def _read_only_annotations() -> Any:
    return ToolAnnotations(readOnlyHint=True, openWorldHint=False) if ToolAnnotations else None


def _mutating_annotations() -> Any:
    return (
        ToolAnnotations(destructiveHint=False, idempotentHint=False, openWorldHint=False)
        if ToolAnnotations
        else None
    )


def _idempotent_annotations() -> Any:
    return (
        ToolAnnotations(destructiveHint=False, idempotentHint=True, openWorldHint=False)
        if ToolAnnotations
        else None
    )


def _create_control_plane_service(data_dir: str = ".tta") -> ControlPlaneService:
    """Create a control-plane service for the requested data directory."""
    return ControlPlaneService(data_dir)


def _create_project_session_manager(data_dir: str = ".tta") -> ProjectSessionManager:
    """Create a project-session manager for the requested data directory."""
    return ProjectSessionManager(data_dir)


def _create_session_manager(data_dir: str = ".tta") -> SessionManager:
    """Create a session manager for the requested data directory."""
    return SessionManager(data_dir)


def _serialize_task(task: TaskRecord) -> dict[str, Any]:
    """Serialize a task record for MCP responses."""
    return task.to_dict()


def _serialize_run(run: RunRecord) -> dict[str, Any]:
    """Serialize a run record for MCP responses."""
    return run.to_dict()


def _serialize_lease(lease: LeaseRecord | None) -> dict[str, Any] | None:
    """Serialize a lease record for MCP responses."""
    if lease is None:
        return None
    return lease.to_dict()


def _serialize_lock(lock: LockRecord) -> dict[str, Any]:
    """Serialize a lock record for MCP responses."""
    return lock.to_dict()


def _serialize_ownership_record(record: dict[str, Any]) -> dict[str, Any]:
    """Serialize a nested ownership record for MCP responses."""
    return {
        "task": dict(record["task"]),
        "run": dict(record["run"]),
        "lease": dict(record["lease"]) if record.get("lease") is not None else None,
        "session": dict(record["session"]) if record.get("session") is not None else None,
        "project": dict(record["project"]) if record.get("project") is not None else None,
        "telemetry": (dict(record["telemetry"]) if record.get("telemetry") is not None else None),
    }


def _serialize_ownership_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialize nested ownership records for MCP responses."""
    return [_serialize_ownership_record(record) for record in records]


def _control_plane_error_payload(exc: Exception) -> dict[str, str]:
    """Convert a control-plane exception into a structured MCP payload."""
    return {
        "error": str(exc),
        "error_type": type(exc).__name__,
    }


@contextlib.contextmanager
def _emit_mcp_span(
    span_name: str,
    attributes: dict[str, str] | None = None,
) -> Generator[Any, None, None]:
    """Emit an OTel span for an MCP workflow tool call.

    Creates a parent span that wraps the service-layer child spans, forming
    a complete trace hierarchy in Jaeger when an OTLP exporter is configured.
    Degrades gracefully (yields None) when OpenTelemetry is unavailable or
    no TracerProvider is active.
    """
    try:
        from opentelemetry import trace as _otel_trace

        tracer = _otel_trace.get_tracer("ttadev.mcp")
        with tracer.start_as_current_span(span_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
    except Exception:
        yield None


def _ensure_project_exists(project_id: str, *, data_dir: str) -> None:
    """Validate that a project exists in the local project manager."""
    project = _create_project_session_manager(data_dir).get_by_id(project_id)
    if project is None:
        raise ControlPlaneError(f"Project not found: {project_id}")


def _ensure_session_exists(session_id: str, *, data_dir: str) -> None:
    """Validate that a session exists in the local session manager."""
    session = _create_session_manager(data_dir).get_session(session_id)
    if session is None:
        raise ControlPlaneError(f"Session not found: {session_id}")


# ── Fleet store — in-process v1 persistence (keyed by fleet_id) ───────────────
# Persistence (Redis/DB) is planned for v2; this is intentionally simple.
_FLEET_STORE: dict[str, dict[str, Any]] = {}

# Valid agent names in the registry — used to validate hints without importing
# every agent module at startup.
_KNOWN_AGENTS: frozenset[str] = frozenset(
    ["developer", "devops", "git", "github", "performance", "qa", "security"]
)


async def _run_fleet_task(
    fleet_id: str,
    task_idx: int,
    task_text: str,
    agent_hint: str | None,
    provider: str,
) -> None:
    """Execute a single fleet sub-task and persist the result in ``_FLEET_STORE``.

    v1 implementation uses a stub executor (no real LLM call) so the end-to-end
    MCP contract is correct.  Wire a real ``ChatPrimitive`` in the follow-up
    milestone.

    Args:
        fleet_id: Parent fleet identifier.
        task_idx: Zero-based position of this task within the fleet.
        task_text: Natural-language task description.
        agent_hint: Preferred agent name, or ``None`` for auto-select.
        provider: LLM provider hint passed through for future use.
    """
    fleet = _FLEET_STORE.get(fleet_id)
    if fleet is None:
        return  # fleet was evicted or never created — nothing to do

    # Resolve agent name — validate hint against the known registry.
    agent_name: str
    if agent_hint and agent_hint in _KNOWN_AGENTS:
        agent_name = agent_hint
    else:
        # Auto-select: pick the first registered agent as a deterministic default.
        try:
            from ttadev.agents.registry import get_registry

            registered = get_registry().all()
            agent_name = (
                registered[0].__name__.lower().replace("agent", "") if registered else "auto"
            )
        except Exception:
            agent_name = "auto"

    fleet["results"][task_idx]["status"] = "running"
    fleet["results"][task_idx]["agent"] = agent_name

    try:
        # ── v1 stub: echo task back with the selected agent name ──────────────
        # Replace this block with a real AgentPrimitive.execute() call in v2.
        output = f"[{agent_name}] Task acknowledged: {task_text}"
        fleet["results"][task_idx]["output"] = output
        fleet["results"][task_idx]["status"] = "complete"
    except Exception as exc:
        fleet["results"][task_idx]["output"] = None
        fleet["results"][task_idx]["status"] = "failed"
        fleet["results"][task_idx]["error"] = str(exc)
        logger.warning(
            "fleet_task_failed",
            fleet_id=fleet_id,
            task_idx=task_idx,
            error=str(exc),
        )
    finally:
        fleet["completed_count"] = sum(
            1 for r in fleet["results"] if r["status"] in ("complete", "failed")
        )
