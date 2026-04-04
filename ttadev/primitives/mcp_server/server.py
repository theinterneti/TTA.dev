"""TTA.dev MCP Server Implementation.

Uses FastMCP for a clean, decorator-based API.
Exposes TTA.dev analysis and primitive recommendations as MCP tools.
"""

import argparse
import asyncio
import contextlib
import sys
import uuid
import warnings
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import structlog

# Try to import MCP - graceful degradation if not available
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None  # type: ignore
    ToolAnnotations = None  # type: ignore

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ttadev.control_plane import (
    ControlPlaneError,
    ControlPlaneService,
    GateStatus,
    LockScopeType,
    RunStatus,
    TaskStatus,
)
from ttadev.control_plane.models import (
    LeaseRecord,
    LockRecord,
    RunRecord,
    TaskRecord,
    WorkflowGateDecisionOutcome,
)
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import SessionManager
from ttadev.primitives.analysis import TTAAnalyzer

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


# ── Pagination helper ──────────────────────────────────────────────────────────
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


# ── Tool annotation presets ────────────────────────────────────────────────────
# Defined as functions so they work gracefully when MCP is unavailable.
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


def create_server() -> Any:
    """Create and configure the MCP server.

    Returns:
        Configured FastMCP server instance

    Raises:
        ImportError: If MCP package is not installed
    """
    if not MCP_AVAILABLE or FastMCP is None:
        raise ImportError("MCP package not installed. Install with: uv add mcp")

    # Create server
    mcp = FastMCP(
        name="TTA.dev Primitives",
        instructions="TTA.dev provides composable workflow primitives for building reliable AI applications. Use analyze_code to get recommendations, get_primitive_info for documentation, and get_template for code snippets.",
    )

    # Shared analyzer instance
    analyzer = TTAAnalyzer()

    # Pre-build annotation objects once per server instance
    _ro = _read_only_annotations()
    _mut = _mutating_annotations()
    _idem = _idempotent_annotations()

    # ========== TOOLS ==========

    # ── Orientation ────────────────────────────────────────────────────────────

    @mcp.tool(annotations=_ro)
    async def tta_bootstrap(agent_id: str = "", task_hint: str = "") -> dict[str, Any]:
        """One-call orientation for coding agents. Returns primitives, tools, patterns, and provider status.

        Call this FIRST at the start of any TTA.dev agent session to get full context.

        Args:
            agent_id: Identifier for this agent session (used for logging, optional)
            task_hint: Brief description of what you're trying to build (used to rank primitives)

        Returns:
            Complete TTA.dev orientation package: primitives catalog, MCP tool index,
            quick-start patterns, and live provider status.
        """
        import re
        from importlib.metadata import version as _pkg_version
        from pathlib import Path

        logger.info("mcp_tool_called", tool="tta_bootstrap", agent_id=agent_id, task_hint=task_hint)

        # ── 1. Package version ────────────────────────────────────────────────
        try:
            pkg_version = _pkg_version("ttadev")
        except Exception:
            pkg_version = "0.1.0"

        # ── 2. Parse PRIMITIVES_CATALOG.md ────────────────────────────────────
        _max_primitives = 15  # keep response within token budget
        _desc_len = 70  # max chars for when_to_use description

        primitives: list[dict[str, str]] = []
        catalog_path = Path(__file__).parents[4] / "PRIMITIVES_CATALOG.md"
        if not catalog_path.exists():
            catalog_path = Path(__file__).parents[3] / "PRIMITIVES_CATALOG.md"

        _import_re = re.compile(r"from\s+(ttadev[\w.]*)\s+import\s+(\w+)")
        _section_re = re.compile(r"^## (.+)")
        _primitive_re = re.compile(r"^### ([\w\[\], ]+)")
        # Line prefixes to skip when collecting a human-readable description
        _skip_pfx = (
            "```",
            "#",
            "|",
            "- ",
            "* ",
            "> ",
            "!",
            "**Source",
            "**Import",
            "**Status",
            "**Test",
            "**Type",
            "**Key",
            "**Prop",
            "**Feature",
            "**Usage",
            "**State",
            "**Param",
        )

        _category_map: dict[str, str] = {
            "core workflow primitives": "core",
            "recovery primitives": "recovery",
            "performance primitives": "performance",
            "skill primitives": "skill",
            "llm routing primitives": "llm_routing",
            "orchestration primitives": "orchestration",
            "testing primitives": "testing",
            "observability primitives": "observability",
            "adaptive/self-improving primitives": "adaptive",
            "ace framework primitives": "ace",
            "coordination primitives": "coordination",
            "collaboration primitives": "collaboration",
        }
        # Allowlist: only emit these names to keep the payload focused
        _emit_names: set[str] = {
            "WorkflowPrimitive",
            "SequentialPrimitive",
            "ParallelPrimitive",
            "ConditionalPrimitive",
            "RouterPrimitive",
            "RetryPrimitive",
            "FallbackPrimitive",
            "TimeoutPrimitive",
            "CompensationPrimitive",
            "CircuitBreakerPrimitive",
            "CachePrimitive",
            "MemoryPrimitive",
            "ModelRouterPrimitive",
            "DelegationPrimitive",
            "TaskClassifierPrimitive",
            "MockPrimitive",
            "InstrumentedPrimitive",
            "AdaptivePrimitive",
            "AdaptiveRetryPrimitive",
            "SelfLearningCodePrimitive",
            "GitCollaborationPrimitive",
        }

        if catalog_path.exists():
            raw = catalog_path.read_text(encoding="utf-8")
            current_category = "core"
            current_name: str | None = None
            current_desc_lines: list[str] = []
            current_import: str = ""

            def _flush_primitive() -> None:
                if not current_name:
                    return
                clean = current_name.split("[")[0].strip()
                if clean not in _emit_names:
                    return
                desc = " ".join(current_desc_lines).strip()
                if not desc:
                    desc = f"A {current_category} primitive."
                imp = current_import or f"from ttadev.primitives import {clean}"
                primitives.append(
                    {
                        "name": clean,
                        "category": current_category,
                        "when_to_use": desc[:_desc_len],
                        "import": imp,
                    }
                )

            for line in raw.splitlines():
                sec = _section_re.match(line)
                if sec:
                    _flush_primitive()
                    current_name = None
                    current_desc_lines = []
                    current_import = ""
                    current_category = _category_map.get(
                        sec.group(1).strip().lower(), current_category
                    )
                    continue

                prim = _primitive_re.match(line)
                if prim:
                    _flush_primitive()
                    current_name = prim.group(1).strip()
                    current_desc_lines = []
                    current_import = ""
                    continue

                if current_name:
                    imp_match = _import_re.search(line)
                    if imp_match and not current_import:
                        current_import = f"from {imp_match.group(1)} import {imp_match.group(2)}"
                        continue
                    # Collect human-readable description lines only.
                    # Bold lines like "**Auto retry with exponential backoff.**" are good;
                    # code fence lines (```python) and bullet lists are not.
                    stripped = line.strip()
                    if (
                        stripped
                        and not stripped.startswith(_skip_pfx)
                        and stripped not in ("-", "---")
                        and "`" not in stripped  # skip inline code
                        and len(current_desc_lines) < 2
                    ):
                        # Strip markdown bold markers
                        cleaned = stripped.strip("*").strip()
                        if cleaned and len(cleaned) > 10:
                            current_desc_lines.append(cleaned)

            _flush_primitive()

        # Deduplicate, preserve catalog order, cap at _max_primitives
        seen: set[str] = set()
        deduped: list[dict[str, str]] = []
        for p in primitives:
            if p["name"] not in seen:
                seen.add(p["name"])
                deduped.append(p)
            if len(deduped) >= _max_primitives:
                break
        primitives = deduped

        # Fallback: use analyzer when catalog parse yielded nothing
        if not primitives:
            for p in analyzer.list_primitives()[:_max_primitives]:
                desc = p.get("description") or (p.get("use_cases") or [""])[0] or ""
                primitives.append(
                    {
                        "name": p.get("name", ""),
                        "category": p.get("category", "core"),
                        "when_to_use": desc[:_desc_len],
                        "import": p.get("import_path", ""),
                    }
                )

        # ── 3. MCP tool index grouped by domain ───────────────────────────────
        try:
            all_tools = await mcp.list_tools()
            all_tool_names = [t.name for t in all_tools]
        except Exception:
            all_tool_names = list(mcp._tool_manager._tools.keys())

        def _domain(name: str) -> str:
            if name == "tta_bootstrap":
                return "orientation"
            if "_" in name:
                prefix = name.split("_")[0]
                if prefix in {"control", "llm", "memory", "workflow"}:
                    return prefix
            return "analysis"

        mcp_tools: dict[str, list[str]] = {}
        for tool_name in all_tool_names:
            domain = _domain(tool_name)
            mcp_tools.setdefault(domain, []).append(tool_name)

        # ── 4. Provider status ────────────────────────────────────────────────
        try:
            provider_status = llm_list_providers()
        except Exception as exc:
            provider_status = {"error": str(exc), "providers": []}

        # ── 5. Quick-start guide (≈150 words, stays in token budget) ─────────
        quick_start = (
            "TTA.dev: composable workflow primitives for reliable AI apps.\n\n"
            "GETTING STARTED:\n"
            "1. Import: `from ttadev.primitives import RetryPrimitive, WorkflowContext`\n"
            "2. Compose with >> (sequential) or | (parallel):\n"
            "   `workflow = fetch >> parse >> store`\n"
            "   `parallel = step_a | step_b | step_c`\n"
            "3. Execute: `await workflow.execute(data, WorkflowContext(workflow_id='...'))`\n\n"
            "PRIMITIVE GROUPS:\n"
            "- Recovery: Retry, Fallback, Timeout, CircuitBreaker\n"
            "- Performance: Cache, Memory\n"
            "- Core: Sequential, Parallel, Conditional\n"
            "- Orchestration: Delegation, MultiModel\n\n"
            "KEY MCP TOOLS:\n"
            "- tta_bootstrap: this tool — call first\n"
            "- list_primitives / get_primitive_info\n"
            "- llm_list_providers / llm_recommend_model\n"
            "- analyze_code: scan code for opportunities\n\n"
            "RULES: Never write manual retry loops (RetryPrimitive). "
            "Never use time.sleep for timeouts (TimeoutPrimitive)."
        )

        # ── 6. Key patterns (concise) ─────────────────────────────────────────
        patterns = (
            "Sequential: a >> b >> c\n"
            "Parallel:   a | b | c\n"
            "Retry:      RetryPrimitive(primitive=p, max_retries=3)\n"
            "Cache:      CachePrimitive(primitive=p, ttl_seconds=300)\n"
            "Timeout:    TimeoutPrimitive(primitive=p, timeout_seconds=30.0)\n"
            "Fallback:   FallbackPrimitive(primary=p1, fallbacks=[p2, p3])\n"
            "Circuit:    CircuitBreakerPrimitive(primitive=p, config=CircuitBreakerConfig(...))\n"
            "Context:    WorkflowContext(workflow_id='my-wf')\n"
        )

        # ── 7. Task-hint relevance ranking ────────────────────────────────────
        # Common words that appear in almost every primitive description — skip them
        _stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "to",
            "of",
            "in",
            "for",
            "with",
            "build",
            "create",
            "use",
            "using",
            "that",
            "this",
            "is",
            "it",
            "my",
        }
        top_for_task: list[dict[str, str]] = []
        if task_hint and primitives:
            hint_words = {w for w in task_hint.lower().split() if w not in _stop_words}

            def _score(p: dict[str, str]) -> tuple[int, int]:
                name_lower = p["name"].lower()
                text = (name_lower + " " + p["category"] + " " + p["when_to_use"]).lower()
                base = sum(1 for w in hint_words if w in text)
                # Bonus: name *starts with* a hint word (e.g. "retry" → RetryPrimitive wins
                # over AdaptiveRetryPrimitive for the "retry" hint)
                prefix_bonus = sum(1 for w in hint_words if name_lower.startswith(w))
                # Tie-break: prefer shorter (more specific) names
                return (base + prefix_bonus, -len(p["name"]))

            scored = sorted(primitives, key=_score, reverse=True)
            top_for_task = [p for p in scored if _score(p)[0] > 0][:3]
            if not top_for_task:
                top_for_task = scored[:3]

        return {
            "version": pkg_version,
            "agent_id": agent_id,
            "primitives": primitives,
            "mcp_tools": mcp_tools,
            "quick_start": quick_start,
            "patterns": patterns,
            "provider_status": provider_status,
            "top_primitives_for_task": top_for_task,
        }

    # ── Analysis / recommendations ─────────────────────────────────────────────

    @mcp.tool(annotations=_ro)
    async def analyze_code(
        code: str,
        file_path: str = "",
        project_type: str = "general",
        min_confidence: float = 0.3,
    ) -> dict[str, Any]:
        """Analyze code and recommend TTA.dev primitives.

        Analyzes source code for patterns and suggests appropriate
        TTA.dev primitives with confidence scores, reasoning, and
        ready-to-use code templates.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context
            project_type: Type of project (general, web, api, data_processing, ml)
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            dict: Analysis report with the following structure:
                {
                    "detected_patterns": List[str],
                    "recommendations": List[{
                        "primitive_name": str,
                        "confidence_score": float,
                        "reasoning": str,
                        "code_template": str,
                        "import_path": str
                    }],
                    "detected_issues": List[str],
                    "optimization_opportunities": List[str],
                    "complexity_level": str
                }
        """
        if err := _check_code_size(code):
            return err
        logger.info(
            "mcp_tool_called",
            tool="analyze_code",
            file_path=file_path,
            code_length=len(code),
        )
        report = analyzer.analyze(
            code,
            file_path=file_path,
            project_type=project_type,
            min_confidence=min_confidence,
        )
        return report.to_dict()

    @mcp.tool(annotations=_ro)
    async def get_primitive_info(primitive_name: str) -> dict[str, Any]:
        """Get detailed information about a TTA.dev primitive.

        Returns comprehensive documentation including description,
        use cases, code templates, and related primitives.

        Args:
            primitive_name: Name of the primitive (e.g., "RetryPrimitive")

        Returns:
            dict: Primitive documentation with the following structure:
                {
                    "name": str,
                    "description": str,
                    "import_path": str,
                    "use_cases": List[str],
                    "templates": List[str],
                    "related_primitives": List[str],
                    "category": str
                }
        """
        return analyzer.get_primitive_info(primitive_name)

    @mcp.tool(annotations=_ro)
    async def list_primitives() -> list[dict[str, Any]]:
        """List all available TTA.dev primitives.

        Returns a list of all primitives with their descriptions
        and primary use cases.

        Returns:
            list[dict]: List of primitives, each with the following structure:
                [{
                    "name": str,
                    "description": str,
                    "import_path": str,
                    "use_cases": List[str],
                    "category": str
                }]
        """
        return analyzer.list_primitives()

    @mcp.tool(annotations=_ro)
    async def search_templates(query: str) -> list[dict[str, Any]]:
        """Search for primitive templates by keyword.

        Searches through all templates and examples to find
        relevant code patterns.

        Args:
            query: Search query (e.g., "retry", "cache", "parallel")

        Returns:
            list[dict]: List of matching templates with structure:
                [{
                    "primitive_name": str,
                    "match_type": str,  # "template" or "example"
                    "match_text": str,
                    "relevance_score": float
                }]
        """
        return analyzer.search_templates(query)

    @mcp.tool(annotations=_ro)
    async def get_composition_example(
        primitives: list[str],
    ) -> dict[str, Any]:
        """Get an example of composing multiple primitives.

        Shows how to combine multiple primitives into a workflow
        using the >> (sequential) and | (parallel) operators.

        Args:
            primitives: List of primitive names to compose

        Returns:
            dict: Composition example with structure:
                {
                    "primitives": List[str],
                    "code": str,
                    "explanation": str,
                    "benefits": List[str],
                    "imports": List[str]
                }
        """
        if not primitives:
            return {"error": "Provide at least one primitive name"}

        # Build composition example
        imports = []
        for prim in primitives:
            info = analyzer.get_primitive_info(prim)
            if "import_path" in info:
                imports.append(info["import_path"])

        # Generate composition code
        primitives_str = ", ".join(primitives)

        code = f"""# Import primitives
{chr(10).join(set(imports))}
from ttadev.primitives.core.base import WorkflowContext

# Composing: {primitives_str}
workflow = (
    {" >> ".join([f"{p.replace('Primitive', '').lower()}_step" for p in primitives])}
)

# Or use | operator for parallel execution
# parallel_workflow = step1 | step2 | step3

# Execute the workflow
context = WorkflowContext(workflow_id="composed-workflow")
result = await workflow.execute(data, context)
"""

        return {
            "primitives": primitives,
            "code": code,
            "explanation": f"Composes {len(primitives)} primitives into a sequential workflow",
            "benefits": [
                "Automatic error propagation",
                "Built-in observability",
                "Type-safe composition",
            ],
            "imports": list(set(imports)),
        }

    @mcp.tool(annotations=_ro)
    async def transform_code(
        code: str,
        primitive: str,
        function_name: str | None = None,
    ) -> dict[str, Any]:
        """Transform code by wrapping functions with a TTA.dev primitive.

        Automatically detects suitable functions and generates transformed
        code with the primitive applied.

        Args:
            code: Source code to transform
            primitive: Primitive to apply (e.g., "RetryPrimitive", "CachePrimitive")
            function_name: Specific function to wrap (optional, auto-detects if not provided)

        Returns:
            dict: Transformation result with structure:
                {
                    "transformed_code": str,
                    "wrapped_functions": List[str],
                    "diff": str,
                    "primitive": str,
                    "error": Optional[str]
                }
        """
        if err := _check_code_size(code):
            return err

        import difflib

        from ttadev.primitives.cli.app import (  # type: ignore[import]
            _find_transform_targets,
            _generate_transformation,
        )

        logger.info(
            "mcp_tool_called",
            tool="transform_code",
            primitive=primitive,
            code_length=len(code),
        )

        # Get primitive info
        info = analyzer.get_primitive_info(primitive)
        if "error" in info:
            return {"error": f"Unknown primitive: {primitive}"}

        # Find targets
        targets = _find_transform_targets(code, primitive, function_name)
        if not targets:
            return {
                "error": f"No suitable functions found for {primitive}",
                "hint": "Try specifying a function_name explicitly",
            }

        # Generate transformation
        transformed = _generate_transformation(code, primitive, targets, info)

        # Generate diff
        diff = list(
            difflib.unified_diff(
                code.splitlines(keepends=True),
                transformed.splitlines(keepends=True),
                fromfile="original",
                tofile="transformed",
            )
        )

        return {
            "transformed_code": transformed,
            "wrapped_functions": [t["name"] for t in targets],
            "diff": "".join(diff),
            "primitive": primitive,
        }

    @mcp.tool(annotations=_ro)
    async def analyze_and_fix(
        code: str,
        file_path: str = "",
        primitive: str | None = None,
    ) -> dict[str, Any]:
        """Analyze code and automatically apply the best primitive fix.

        Combines analysis and transformation in one step. Uses the top
        recommendation unless a specific primitive is provided.

        Args:
            code: Source code to analyze and fix
            file_path: Optional file path for context
            primitive: Specific primitive to apply (uses top recommendation if not provided)

        Returns:
            dict: Combined result with structure:
                {
                    "analysis": dict,  # Full analysis report
                    "transformation": Optional[{
                        "code": str,
                        "wrapped_functions": List[str]
                    }],
                    "applied_primitive": Optional[str],
                    "message": Optional[str]
                }
        """
        if err := _check_code_size(code):
            return err
        logger.info(
            "mcp_tool_called",
            tool="analyze_and_fix",
            file_path=file_path,
            code_length=len(code),
        )

        # First analyze
        report = analyzer.analyze(code, file_path=file_path)
        analysis_dict = report.to_dict()

        # Determine which primitive to apply
        if primitive:
            prim_to_apply = primitive
        elif report.recommendations:
            prim_to_apply = report.recommendations[0].primitive_name
        else:
            return {
                "analysis": analysis_dict,
                "transformation": None,
                "message": "No recommendations found - code looks good!",
            }

        # Apply transformation
        from ttadev.primitives.cli.app import (  # type: ignore[import]
            _find_transform_targets,
            _generate_transformation,
        )

        info = analyzer.get_primitive_info(prim_to_apply)
        targets = _find_transform_targets(code, prim_to_apply, None)

        if targets:
            transformed = _generate_transformation(code, prim_to_apply, targets, info)
            return {
                "analysis": analysis_dict,
                "transformation": {
                    "code": transformed,
                    "wrapped_functions": [t["name"] for t in targets],
                },
                "applied_primitive": prim_to_apply,
            }
        else:
            return {
                "analysis": analysis_dict,
                "transformation": None,
                "applied_primitive": None,
                "message": f"No suitable functions found for {prim_to_apply}",
            }

    @mcp.tool(annotations=_ro)
    async def suggest_fixes(
        code: str,
        file_path: str = "",
        max_suggestions: int = 3,
    ) -> dict[str, Any]:
        """Get actionable fix suggestions with line numbers.

        Analyzes code and returns specific, actionable suggestions
        with exact line numbers for issues and opportunities.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context
            max_suggestions: Maximum number of suggestions to return

        Returns:
            dict: Suggestions with structure:
                {
                    "issues": List[{
                        "description": str,
                        "lines": List[int]
                    }],
                    "opportunities": List[{
                        "description": str,
                        "lines": List[int]
                    }],
                    "top_fixes": List[{
                        "primitive": str,
                        "confidence": str,
                        "reasoning": str,
                        "import": str,
                        "template": str
                    }],
                    "complexity": str,
                    "patterns_found": List[str]
                }
        """
        import re

        if err := _check_code_size(code):
            return err
        logger.info(
            "mcp_tool_called",
            tool="suggest_fixes",
            file_path=file_path,
            code_length=len(code),
        )

        # Analyze
        report = analyzer.analyze(code, file_path=file_path)

        # Find line numbers for patterns
        lines = code.split("\n")
        line_info: dict[str, list[int]] = {
            "api_calls": [],
            "async_operations": [],
            "error_handling": [],
            "llm_patterns": [],
        }

        api_patterns = re.compile(r"(requests\.|httpx\.|aiohttp|\.get\(|\.post\()")
        async_patterns = re.compile(r"(async def|await\s)")

        for i, line in enumerate(lines, 1):
            if api_patterns.search(line):
                line_info["api_calls"].append(i)
            if async_patterns.search(line):
                line_info["async_operations"].append(i)

        # Build suggestions
        issues_with_lines = []
        for issue in report.context.detected_issues:
            issue_info = {"description": issue, "lines": []}
            if "API" in issue and line_info["api_calls"]:
                issue_info["lines"] = line_info["api_calls"][:3]
            elif "Async" in issue and line_info["async_operations"]:
                issue_info["lines"] = line_info["async_operations"][:3]
            issues_with_lines.append(issue_info)

        opportunities_with_lines = []
        for opp in report.context.optimization_opportunities:
            opp_info = {"description": opp, "lines": []}
            if "API" in opp and line_info["api_calls"]:
                opp_info["lines"] = line_info["api_calls"][:5]
            opportunities_with_lines.append(opp_info)

        # Top fixes
        top_fixes = []
        for rec in report.recommendations[:max_suggestions]:
            top_fixes.append(
                {
                    "primitive": rec.primitive_name,
                    "confidence": f"{rec.confidence_score:.0%}",
                    "reasoning": rec.reasoning,
                    "import": rec.import_path,
                    "template": rec.code_template,
                }
            )

        return {
            "issues": issues_with_lines,
            "opportunities": opportunities_with_lines,
            "top_fixes": top_fixes,
            "complexity": report.analysis.complexity_level,
            "patterns_found": report.analysis.detected_patterns,
        }

    @mcp.tool(annotations=_ro)
    async def detect_anti_patterns(
        code: str,
        file_path: str = "",
    ) -> dict[str, Any]:
        """Detect anti-patterns that should use TTA.dev primitives.

        Finds manual implementations of retry loops, timeout handling,
        fallback logic, caching, and other patterns that have dedicated
        TTA.dev primitives.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context

        Returns:
            dict: Detected anti-patterns with structure:
                {
                    "anti_patterns": List[{
                        "pattern_type": str,
                        "description": str,
                        "lines": List[int],
                        "severity": str,  # "low", "medium", "high"
                        "recommended_primitive": str,
                        "fix_template": str
                    }],
                    "total_found": int,
                    "summary": str
                }
        """
        from ttadev.primitives.analysis.patterns import PatternDetector

        if err := _check_code_size(code):
            return err
        logger.info(
            "mcp_tool_called",
            tool="detect_anti_patterns",
            file_path=file_path,
            code_length=len(code),
        )

        detector = PatternDetector()

        # Get summary (flat list of issues)
        summary = detector.get_anti_pattern_summary(code)

        # Get detailed anti-patterns (categorized)
        detailed = detector.detect_anti_patterns(code)

        return {
            "total_issues": summary["total_issues"],
            "primitives_needed": summary["primitives_needed"],
            "issues": summary["issues"],
            "anti_patterns": detailed,
        }

    @mcp.tool(annotations=_ro)
    async def rewrite_code(
        code: str,
        primitive: str | None = None,
        auto_detect: bool = True,
    ) -> dict[str, Any]:
        """Rewrite code using AST-based transformation to use TTA.dev primitives.

        Uses intelligent AST analysis to transform manual implementations
        into proper TTA.dev primitive usage. More sophisticated than
        simple wrapping - actually rewrites the code structure.

        Args:
            code: Source code to rewrite
            primitive: Specific primitive to apply (optional)
            auto_detect: Auto-detect anti-patterns if no primitive specified

        Returns:
            dict: Rewrite result with structure:
                {
                    "transformed_code": str,
                    "changes_made": List[str],
                    "imports_added": List[str],
                    "success": bool,
                    "error": Optional[str],
                    "diff": str
                }
        """
        if err := _check_code_size(code):
            return err

        import difflib

        from ttadev.primitives.analysis.transformer import transform_code

        logger.info(
            "mcp_tool_called",
            tool="rewrite_code",
            primitive=primitive,
            auto_detect=auto_detect,
            code_length=len(code),
        )

        result = transform_code(
            code,
            primitive=primitive,
            auto_detect=auto_detect,
        )

        # Generate diff
        diff = list(
            difflib.unified_diff(
                result.original_code.splitlines(keepends=True),
                result.transformed_code.splitlines(keepends=True),
                fromfile="original",
                tofile="rewritten",
            )
        )

        return {
            "transformed_code": result.transformed_code,
            "changes_made": result.changes_made,
            "imports_added": result.imports_added,
            "success": result.success,
            "error": result.error,
            "diff": "".join(diff),
        }

    @mcp.tool(annotations=_mut)
    async def control_create_task(
        title: str,
        description: str = "",
        project_name: str | None = None,
        requested_role: str | None = None,
        priority: str = "normal",
        gates: list[dict[str, Any]] | None = None,
        workspace_locks: list[str] | None = None,
        file_locks: list[str] | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Create a new L0 control-plane task."""
        logger.info(
            "mcp_tool_called",
            tool="control_create_task",
            data_dir=data_dir,
            project_name=project_name,
            priority=priority,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.create_task(
                title,
                description=description,
                project_name=project_name,
                requested_role=requested_role,
                priority=priority,
                gates=gates,
                workspace_locks=workspace_locks,
                file_locks=file_locks,
            )
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_ro)
    async def control_list_tasks(
        status: str | None = None,
        project_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List L0 control-plane tasks."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_tasks",
            data_dir=data_dir,
            status=status,
            project_name=project_name,
        )
        try:
            service = _create_control_plane_service(data_dir)
            parsed_status = TaskStatus(status) if status is not None else None
            tasks = service.list_tasks(status=parsed_status, project_name=project_name)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        page = _paginate([_serialize_task(t) for t in tasks], limit, offset)
        return {"tasks": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_ro)
    async def control_get_task(task_id: str, data_dir: str = ".tta") -> dict[str, Any]:
        """Get a single L0 control-plane task."""
        logger.info(
            "mcp_tool_called",
            tool="control_get_task",
            data_dir=data_dir,
            task_id=task_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.get_task(task_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_claim_task(
        task_id: str,
        agent_role: str | None = None,
        lease_ttl_seconds: float = 300.0,
        trace_id: str | None = None,
        span_id: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Claim an L0 control-plane task and create an active run.

        Pass ``trace_id`` and ``span_id`` (hex strings) to stamp the current
        OTel span context onto the run record for attribution.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_claim_task",
            data_dir=data_dir,
            task_id=task_id,
            agent_role=agent_role,
            lease_ttl_seconds=lease_ttl_seconds,
        )
        try:
            service = _create_control_plane_service(data_dir)
            claim = service.claim_task(
                task_id,
                agent_role=agent_role,
                lease_ttl_seconds=lease_ttl_seconds,
                trace_id=trace_id,
                span_id=span_id,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {
            "task": _serialize_task(claim.task),
            "run": _serialize_run(claim.run),
            "lease": _serialize_lease(claim.lease),
        }

    @mcp.tool(annotations=_mut)
    async def control_decide_gate(
        task_id: str,
        gate_id: str,
        status: str,
        decided_by: str | None = None,
        decision_role: str | None = None,
        summary: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record a gate decision for an L0 control-plane task."""
        logger.info(
            "mcp_tool_called",
            tool="control_decide_gate",
            data_dir=data_dir,
            task_id=task_id,
            gate_id=gate_id,
            status=status,
            decision_role=decision_role,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.decide_gate(
                task_id,
                gate_id,
                status=GateStatus(status),
                decided_by=decided_by,
                decision_role=decision_role,
                summary=summary,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_reopen_gate(
        task_id: str,
        gate_id: str,
        reopened_by: str | None = None,
        summary: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Reopen a gate that is currently in changes_requested."""
        logger.info(
            "mcp_tool_called",
            tool="control_reopen_gate",
            data_dir=data_dir,
            task_id=task_id,
            gate_id=gate_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.reopen_gate(
                task_id,
                gate_id,
                reopened_by=reopened_by,
                summary=summary,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_ro)
    async def control_list_locks(
        scope_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 control-plane locks."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_locks",
            data_dir=data_dir,
            scope_type=scope_type,
        )
        try:
            service = _create_control_plane_service(data_dir)
            parsed_scope_type = LockScopeType(scope_type) if scope_type is not None else None
            locks = service.list_locks(scope_type=parsed_scope_type)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        page = _paginate([_serialize_lock(lock) for lock in locks], limit, offset)
        return {"locks": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_mut)
    async def control_acquire_workspace_lock(
        task_id: str,
        run_id: str,
        workspace_name: str,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Acquire a workspace lock for an active L0 run."""
        logger.info(
            "mcp_tool_called",
            tool="control_acquire_workspace_lock",
            data_dir=data_dir,
            task_id=task_id,
            run_id=run_id,
            workspace_name=workspace_name,
        )
        try:
            service = _create_control_plane_service(data_dir)
            lock = service.acquire_workspace_lock(task_id, run_id, workspace_name)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"lock": _serialize_lock(lock)}

    @mcp.tool(annotations=_mut)
    async def control_acquire_file_lock(
        task_id: str,
        run_id: str,
        file_path: str,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Acquire a file lock for an active L0 run."""
        logger.info(
            "mcp_tool_called",
            tool="control_acquire_file_lock",
            data_dir=data_dir,
            task_id=task_id,
            run_id=run_id,
            file_path=file_path,
        )
        try:
            service = _create_control_plane_service(data_dir)
            lock = service.acquire_file_lock(task_id, run_id, file_path)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"lock": _serialize_lock(lock)}

    @mcp.tool(annotations=_idem)
    async def control_release_lock(lock_id: str, data_dir: str = ".tta") -> dict[str, Any]:
        """Release an L0 control-plane lock."""
        logger.info(
            "mcp_tool_called",
            tool="control_release_lock",
            data_dir=data_dir,
            lock_id=lock_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            service.release_lock(lock_id)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"released_lock_id": lock_id}

    @mcp.tool(annotations=_ro)
    async def control_list_runs(
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List L0 control-plane runs."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_runs",
            data_dir=data_dir,
            status=status,
        )
        try:
            service = _create_control_plane_service(data_dir)
            parsed_status = RunStatus(status) if status is not None else None
            runs = service.list_runs(status=parsed_status)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        page = _paginate([_serialize_run(r) for r in runs], limit, offset)
        return {"runs": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_ro)
    async def control_get_run(run_id: str, data_dir: str = ".tta") -> dict[str, Any]:
        """Get a single L0 control-plane run and its lease, if any."""
        logger.info(
            "mcp_tool_called",
            tool="control_get_run",
            data_dir=data_dir,
            run_id=run_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            run = service.get_run(run_id)
            lease = service.get_lease_for_run(run_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        return {
            "run": _serialize_run(run),
            "lease": _serialize_lease(lease),
        }

    @mcp.tool(annotations=_idem)
    async def control_heartbeat_run(
        run_id: str,
        lease_ttl_seconds: float = 300.0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Renew the lease for an active L0 control-plane run."""
        logger.info(
            "mcp_tool_called",
            tool="control_heartbeat_run",
            data_dir=data_dir,
            run_id=run_id,
            lease_ttl_seconds=lease_ttl_seconds,
        )
        try:
            service = _create_control_plane_service(data_dir)
            lease = service.heartbeat_run(run_id, lease_ttl_seconds=lease_ttl_seconds)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"lease": _serialize_lease(lease)}

    @mcp.tool(annotations=_mut)
    async def control_complete_run(
        run_id: str,
        summary: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Complete an active L0 control-plane run."""
        logger.info(
            "mcp_tool_called",
            tool="control_complete_run",
            data_dir=data_dir,
            run_id=run_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            run = service.complete_run(run_id, summary=summary)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"run": _serialize_run(run)}

    @mcp.tool(annotations=_mut)
    async def control_release_run(
        run_id: str,
        reason: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Release an active L0 control-plane run back to pending."""
        logger.info(
            "mcp_tool_called",
            tool="control_release_run",
            data_dir=data_dir,
            run_id=run_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            run = service.release_run(run_id, reason=reason)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"run": _serialize_run(run)}

    @mcp.tool(annotations=_ro)
    async def control_list_ownership(
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 ownership records across all projects and sessions."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_ownership",
            data_dir=data_dir,
        )
        try:
            service = _create_control_plane_service(data_dir)
            active = service.list_active_ownership()
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        page = _paginate(_serialize_ownership_records(active), limit, offset)
        return {"active": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_ro)
    async def control_list_project_ownership(
        project_id: str,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 ownership records for a single project."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_project_ownership",
            data_dir=data_dir,
            project_id=project_id,
        )
        try:
            _ensure_project_exists(project_id, data_dir=data_dir)
            service = _create_control_plane_service(data_dir)
            active = service.list_active_ownership(project_id=project_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        page = _paginate(_serialize_ownership_records(active), limit, offset)
        return {
            "project_id": project_id,
            "active": page["items"],
            **{k: v for k, v in page.items() if k != "items"},
        }

    @mcp.tool(annotations=_ro)
    async def control_list_session_ownership(
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 ownership records for a single session."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_session_ownership",
            data_dir=data_dir,
            session_id=session_id,
        )
        try:
            _ensure_session_exists(session_id, data_dir=data_dir)
            service = _create_control_plane_service(data_dir)
            active = service.list_active_ownership(session_id=session_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        page = _paginate(_serialize_ownership_records(active), limit, offset)
        return {
            "session_id": session_id,
            "active": page["items"],
            **{k: v for k, v in page.items() if k != "items"},
        }

    # ========== WORKFLOW PROGRESSION ==========

    @mcp.tool(annotations=_mut)
    async def control_start_workflow(
        workflow_name: str,
        workflow_goal: str,
        step_agents: list[str],
        project_name: str | None = None,
        policy_gates: list[dict[str, str]] | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Create and claim a tracked multi-agent workflow task.

        ``step_agents`` is an ordered list of agent names — one entry per
        workflow step.  ``policy_gates`` is an optional list of extra POLICY
        gate dicts, each with keys ``id``, ``label``, and ``policy``
        (e.g. ``"auto:confidence>=0.85"``).

        Returns the same ``{task, run, lease}`` envelope as
        ``control_claim_task``.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_start_workflow",
            data_dir=data_dir,
            workflow_name=workflow_name,
            step_agents=step_agents,
        )
        try:
            extra_gates: list[dict[str, Any]] | None = None
            if policy_gates:
                extra_gates = [
                    {
                        "id": g["id"],
                        "gate_type": "policy",
                        "label": g["label"],
                        "required": True,
                        "policy_name": g["policy"],
                    }
                    for g in policy_gates
                ]
            with _emit_mcp_span(
                "tta.l0.mcp.workflow.start",
                {"workflow.name": workflow_name, "data_dir": data_dir},
            ):
                service = _create_control_plane_service(data_dir)
                claim = service.start_tracked_workflow(
                    workflow_name=workflow_name,
                    workflow_goal=workflow_goal,
                    step_agents=step_agents,
                    project_name=project_name,
                    extra_gates=extra_gates,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {
            "task": _serialize_task(claim.task),
            "run": _serialize_run(claim.run),
            "lease": _serialize_lease(claim.lease),
        }

    @mcp.tool(annotations=_idem)
    async def control_mark_workflow_step_running(
        task_id: str,
        step_index: int,
        trace_id: str | None = None,
        span_id: str | None = None,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Transition a tracked workflow step to RUNNING.

        Pass ``trace_id`` and ``span_id`` to stamp the current OTel span
        context onto the step record.  Safe to call again on retry — the
        trace context is replaced each time.

        Pass ``hindsight_bank_id`` and ``hindsight_document_id`` to correlate
        this step with a Hindsight memory retain operation, so the step record
        carries a direct link to the retained memory artifact.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_mark_workflow_step_running",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
        )
        try:
            with _emit_mcp_span(
                "tta.l0.mcp.step.running",
                {"task.id": task_id, "step.index": str(step_index), "data_dir": data_dir},
            ):
                service = _create_control_plane_service(data_dir)
                task = service.mark_workflow_step_running(
                    task_id,
                    step_index=step_index,
                    trace_id=trace_id,
                    span_id=span_id,
                    hindsight_bank_id=hindsight_bank_id,
                    hindsight_document_id=hindsight_document_id,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_record_workflow_step_result(
        task_id: str,
        step_index: int,
        result_summary: str,
        confidence: float,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record the result and confidence score for a completed workflow step.

        ``confidence`` must be in the range 0.0–1.0.  Recording the result
        automatically evaluates any pending POLICY gates attached to the task.

        Pass ``hindsight_bank_id`` and ``hindsight_document_id`` to attach a
        link to the Hindsight memory retain artifact produced by this step.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_record_workflow_step_result",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
            confidence=confidence,
        )
        try:
            with _emit_mcp_span(
                "tta.l0.mcp.step.completed",
                {
                    "task.id": task_id,
                    "step.index": str(step_index),
                    "step.confidence": str(confidence),
                    "data_dir": data_dir,
                },
            ):
                service = _create_control_plane_service(data_dir)
                task = service.record_workflow_step_result(
                    task_id,
                    step_index=step_index,
                    result_summary=result_summary,
                    confidence=confidence,
                    hindsight_bank_id=hindsight_bank_id,
                    hindsight_document_id=hindsight_document_id,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_record_workflow_gate_outcome(
        task_id: str,
        step_index: int,
        decision: str,
        summary: str = "",
        policy_name: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record the approval-gate decision for a tracked workflow step.

        ``decision`` must be one of: ``continue``, ``skip``, ``edit``, ``quit``.
        Set ``policy_name`` when the decision was made automatically by a policy
        rule rather than by a human reviewer.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_record_workflow_gate_outcome",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
            decision=decision,
        )
        try:
            outcome = WorkflowGateDecisionOutcome(decision)
            with _emit_mcp_span(
                "tta.l0.mcp.gate.outcome",
                {
                    "task.id": task_id,
                    "step.index": str(step_index),
                    "gate.decision": decision,
                    "data_dir": data_dir,
                },
            ):
                service = _create_control_plane_service(data_dir)
                task = service.record_workflow_gate_outcome(
                    task_id,
                    step_index=step_index,
                    decision=outcome,
                    summary=summary,
                    policy_name=policy_name,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_mark_workflow_step_failed(
        task_id: str,
        step_index: int,
        error_summary: str,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Mark a tracked workflow step as FAILED with an error summary."""
        logger.info(
            "mcp_tool_called",
            tool="control_mark_workflow_step_failed",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
        )
        try:
            with _emit_mcp_span(
                "tta.l0.mcp.step.failed",
                {
                    "task.id": task_id,
                    "step.index": str(step_index),
                    "error.summary": error_summary,
                    "data_dir": data_dir,
                },
            ) as _span:
                if _span is not None:
                    try:
                        from opentelemetry.trace import Status, StatusCode

                        _span.set_status(Status(StatusCode.ERROR, error_summary))
                    except Exception:
                        pass
                service = _create_control_plane_service(data_dir)
                task = service.mark_workflow_step_failed(
                    task_id,
                    step_index=step_index,
                    error_summary=error_summary,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    # ========== LLM TOOLS ==========

    @mcp.tool(annotations=_ro)
    def llm_hardware_profile() -> dict:
        """Return the detected hardware profile for this machine.

        Reports CPU cores, total RAM, GPU name/VRAM and compute backend
        (cuda/rocm/metal/cpu), plus the estimated largest model size that
        will fit in memory at Q4 quantisation.

        Use this to understand what Ollama models are viable before pulling
        or routing to them.

        Returns:
            Hardware profile dict with keys: cpu_cores, ram_gb, gpus,
            backend, total_vram_gb, max_params_b_q4, max_params_b_q8.
        """
        from ttadev.primitives.llm.hardware_detector import HardwareDetector

        det = HardwareDetector()
        profile = det.detect()
        result = profile.to_dict()
        result["recommend_size_tag"] = det.recommend_size_tag()
        return result

    @mcp.tool(annotations=_ro)
    def llm_viable_ollama_models(model_ids: list[str]) -> dict:
        """Filter a list of Ollama model IDs to only those that fit in available memory.

        Checks both GPU VRAM and system RAM (Ollama can offload to CPU RAM).
        Models without a recognised parameter count are assumed viable.

        Args:
            model_ids: Candidate Ollama model IDs, e.g.
                ``["llama3.2:1b", "qwen3:14b", "llama3.3:70b"]``.

        Returns:
            Dict with ``viable`` (list that fits) and ``too_large`` (list that
            doesn't fit in available memory).
        """
        from ttadev.primitives.llm.hardware_detector import HardwareDetector

        det = HardwareDetector()
        viable = det.filter_ollama_models(model_ids)
        too_large = [m for m in model_ids if m not in viable]
        return {
            "viable": viable,
            "too_large": too_large,
            "hardware_summary": det.detect().summary(),
        }

    @mcp.tool(annotations=_ro)
    def llm_benchmark_score(model_id: str, benchmark: str | None = None) -> dict:
        """Look up benchmark scores for a model from the TTA.dev benchmark DB.

        Includes live data sourced from Artificial Analysis and the HuggingFace
        Open LLM Leaderboard (refreshed every 24 hours).

        Args:
            model_id: Model identifier as stored in the benchmark DB, e.g.
                ``"gpt-4o"``, ``"llama-3.3-70b-versatile"``.
            benchmark: Specific benchmark name (e.g. ``"humaneval"``,
                ``"mmlu"``, ``"gpqa"``).  When ``None``, all known scores
                for the model are returned.

        Returns:
            Dict with ``model_id``, ``benchmark`` (or ``"all"``), and
            ``scores`` mapping benchmark name → score (0–100 scale).
        """
        from ttadev.primitives.llm.model_benchmarks import (
            get_benchmarks,
            get_best_score,
        )

        if benchmark:
            score = get_best_score(model_id, benchmark)
            return {
                "model_id": model_id,
                "benchmark": benchmark,
                "score": score,
                "available": score is not None,
            }

        # Return all scores for this model
        entries = get_benchmarks(model_id)
        scores = {e.benchmark: e.score for e in entries}
        return {
            "model_id": model_id,
            "benchmark": "all",
            "scores": scores,
            "best_coding": get_best_score(model_id, "humaneval"),
            "best_knowledge": get_best_score(model_id, "mmlu"),
        }

    @mcp.tool(annotations=_idem)
    async def llm_refresh_benchmarks(force: bool = False) -> dict:
        """Refresh the live benchmark cache from Artificial Analysis and HuggingFace.

        This is normally done automatically (24-hour TTL) but can be triggered
        manually here.  Network access is required; the tool is a no-op if no
        API keys are configured.

        Args:
            force: When ``True``, ignores the TTL and re-downloads regardless
                of when the cache was last refreshed.

        Returns:
            Dict with ``ok`` (bool), ``models_updated`` (int), and
            ``message`` (str).
        """
        try:
            from ttadev.primitives.llm.benchmark_fetcher import BenchmarkFetcher

            fetcher = BenchmarkFetcher()
            data = await fetcher.refresh(force=force)
            return {
                "ok": True,
                "models_updated": len(data),
                "message": f"Refreshed {len(data)} model benchmark records.",
            }
        except Exception as exc:
            return {
                "ok": False,
                "models_updated": 0,
                "message": f"Refresh failed: {exc}",
            }

    @mcp.tool(annotations=_ro)
    def llm_list_providers() -> dict:
        """List all configured LLM providers and their status.

        Returns information about each provider: whether an API key is
        configured, the default model, and the base URL.  Useful for
        agents checking which cloud providers are available before routing.

        Returns:
            Dict with ``providers`` list, each entry having ``name``,
            ``api_key_configured``, ``default_model``, and ``base_url``.
        """
        import os

        from ttadev.primitives.llm.providers import PROVIDERS

        result = []
        for name, spec in PROVIDERS.items():
            env_key = f"{name.upper()}_API_KEY"
            if name == "openrouter":
                env_key = "OPENROUTER_API_KEY"
            elif name == "google":
                env_key = "GOOGLE_API_KEY"
            elif name == "groq":
                env_key = "GROQ_API_KEY"
            elif name == "ollama":
                env_key = ""  # no key needed

            # Google: accept GOOGLE_API_KEY (canonical) or GEMINI_API_KEY
            # (backward-compat for users who set GEMINI_API_KEY manually).
            if name == "google":
                google_key = os.environ.get("GOOGLE_API_KEY")
                gemini_key = os.environ.get("GEMINI_API_KEY")
                if gemini_key and not google_key:
                    warnings.warn(
                        "GEMINI_API_KEY is deprecated; set GOOGLE_API_KEY instead "
                        "(matches Google AI Studio convention). "
                        "Support for GEMINI_API_KEY will be removed in a future release.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                api_key_configured = bool(google_key or gemini_key)
            else:
                api_key_configured = bool(env_key and os.environ.get(env_key))

            result.append(
                {
                    "name": name,
                    "api_key_configured": api_key_configured,
                    "default_model": getattr(spec, "default_model", None),
                    "base_url": getattr(spec, "base_url", None),
                    "is_local": name == "ollama",
                }
            )

        return {"providers": result, "count": len(result)}

    @mcp.tool(annotations=_ro)
    def llm_recommend_model(
        task: str = "coding",
        complexity: str = "moderate",
        prefer_local: bool = False,
        max_cost_tier: str = "high",
    ) -> dict:
        """Recommend the best available model for a given task and complexity.

        Consults the task-aware model selector using live provider data,
        hardware viability (for Ollama), and benchmark scores.

        Args:
            task: Task type — one of ``"coding"``, ``"reasoning"``,
                ``"math"``, ``"chat"``, ``"function_calling"``,
                ``"vision"``, ``"general"``.
            complexity: Complexity hint — ``"simple"``, ``"moderate"``,
                or ``"complex"``.
            prefer_local: When ``True``, prefers Ollama models if viable.
            max_cost_tier: Maximum cost tier to consider —
                ``"free"``, ``"low"``, ``"medium"``, ``"high"``.

        Returns:
            Dict with ``model_id``, ``provider``, ``rationale``, and
            ``fallback`` (next-best option).
        """
        from ttadev.primitives.llm.task_selector import (
            COMPLEXITY_COMPLEX,
            COMPLEXITY_MODERATE,
            COMPLEXITY_SIMPLE,
            TASK_CHAT,
            TASK_CODING,
            TASK_FUNCTION_CALLING,
            TASK_GENERAL,
            TASK_MATH,
            TASK_REASONING,
            TASK_VISION,
            TaskProfile,
            rank_models_for_task,
        )

        task_map = {
            "coding": TASK_CODING,
            "reasoning": TASK_REASONING,
            "math": TASK_MATH,
            "chat": TASK_CHAT,
            "function_calling": TASK_FUNCTION_CALLING,
            "vision": TASK_VISION,
            "general": TASK_GENERAL,
        }
        complexity_map = {
            "simple": COMPLEXITY_SIMPLE,
            "moderate": COMPLEXITY_MODERATE,
            "complex": COMPLEXITY_COMPLEX,
        }

        task_type = task_map.get(task.lower(), TASK_CODING)
        complexity_level = complexity_map.get(complexity.lower(), COMPLEXITY_MODERATE)

        profile = TaskProfile(task_type=task_type, complexity=complexity_level)

        # Use the static cloud model catalog (no network calls needed)
        from ttadev.primitives.llm.model_registry import (
            _COST_TIER_ORDER,
            _DEFAULT_CLOUD_MODELS,
        )

        all_entries = list(_DEFAULT_CLOUD_MODELS)
        ranked = rank_models_for_task(
            [e.model_id for e in all_entries],
            profile,
        )

        # Apply cost tier filter
        max_rank = _COST_TIER_ORDER.get(max_cost_tier, 99)
        entry_map = {e.model_id: e for e in all_entries}

        cost_filtered = [
            model_id
            for model_id in ranked
            if model_id in entry_map
            and _COST_TIER_ORDER.get(entry_map[model_id].cost_tier, 99) <= max_rank
        ]

        # Apply local preference
        if prefer_local:
            local_first = [m for m in cost_filtered if entry_map.get(m) and entry_map[m].is_local]
            cloud = [m for m in cost_filtered if not (entry_map.get(m) and entry_map[m].is_local)]
            cost_filtered = local_first + cloud

        top = cost_filtered[0] if cost_filtered else None
        second = cost_filtered[1] if len(cost_filtered) > 1 else None

        def _provider(mid: str | None) -> str | None:
            if mid is None:
                return None
            e = entry_map.get(mid)
            return e.provider if e else None

        return {
            "model_id": top,
            "provider": _provider(top),
            "fallback": second,
            "fallback_provider": _provider(second),
            "task": task,
            "complexity": complexity,
            "rationale": (
                f"Selected for {task} ({complexity} complexity). "
                f"Provider: {_provider(top)}. "
                f"Prefer local: {prefer_local}."
            ),
        }

    # ========== MEMORY TOOLS ==========

    _ro_m = ToolAnnotations(readOnlyHint=True) if ToolAnnotations else None
    _idem_m = ToolAnnotations(idempotentHint=True) if ToolAnnotations else None

    @mcp.tool(annotations=_ro_m)
    async def memory_recall(
        query: str,
        bank_id: str = "tta-dev",
        budget: str = "mid",
    ) -> dict[str, object]:
        """Recall relevant memories from a Hindsight memory bank.

        Semantically searches the Hindsight bank for memories that match the
        query. Returns the top matches with text content and optional type.

        Args:
            query: Semantic search string (must not be empty).
            bank_id: Hindsight bank identifier (default: ``"tta-dev"``).
            budget: Recall depth — ``"low"`` (fast), ``"mid"``, or ``"high"`` (thorough).

        Returns:
            Dict with ``memories`` list (each has ``id``, ``text``, ``type``)
            and ``count`` integer.
        """
        if not query:
            return {"error": "query must not be empty", "memories": [], "count": 0}
        if budget not in ("low", "mid", "high"):
            budget = "mid"
        try:
            from ttadev.primitives.memory import AgentMemory

            mem = AgentMemory(bank_id=bank_id)
            if not mem.is_available():
                return {
                    "error": "Hindsight unavailable — start with: docker start hindsight",
                    "memories": [],
                    "count": 0,
                }
            results = await mem.recall(query, budget=budget)  # type: ignore[arg-type]
            return {"memories": list(results), "count": len(results)}
        except Exception as exc:
            return {"error": str(exc), "memories": [], "count": 0}

    @mcp.tool()
    async def memory_retain(
        content: str,
        bank_id: str = "tta-dev",
        context: str = "",
    ) -> dict[str, object]:
        """Store a new memory in a Hindsight memory bank.

        Persists *content* to the specified bank for future recall. Use the
        retain format: ``"[type: decision|pattern|failure|insight] <what happened>"``
        for structured, searchable memories.

        Args:
            content: Memory content to store (must not be empty).
            bank_id: Hindsight bank identifier (default: ``"tta-dev"``).
            context: Optional context label (e.g. module or task name).

        Returns:
            Dict with ``success`` bool and optional ``operation_id``.
        """
        if not content:
            return {"success": False, "error": "content must not be empty"}
        if context:
            content = f"{content}\nContext: {context}"
        try:
            from ttadev.primitives.memory import AgentMemory

            mem = AgentMemory(bank_id=bank_id)
            if not mem.is_available():
                return {
                    "success": False,
                    "error": "Hindsight unavailable — start with: docker start hindsight",
                }
            result = await mem.retain(content)
            return dict(result)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @mcp.tool(annotations=_ro_m)
    async def memory_build_context(
        query: str,
        bank_id: str = "tta-dev",
    ) -> dict[str, object]:
        """Build a system-prompt-friendly context prefix from Hindsight.

        Fetches active directives and semantically relevant memories from the
        specified bank, returning a formatted string suitable for prepending to
        an agent's system prompt.

        Args:
            query: Semantic search string to find relevant memories.
            bank_id: Hindsight bank identifier (default: ``"tta-dev"``).

        Returns:
            Dict with ``context`` string (empty string if Hindsight unavailable)
            and ``available`` bool.
        """
        if not query:
            return {"error": "query must not be empty", "context": "", "available": False}
        try:
            from ttadev.primitives.memory import AgentMemory

            mem = AgentMemory(bank_id=bank_id)
            available = mem.is_available()
            if not available:
                return {
                    "context": "",
                    "available": False,
                    "error": "Hindsight unavailable — start with: docker start hindsight",
                }
            prefix = await mem.build_context_prefix(query)
            return {"context": prefix, "available": True}
        except Exception as exc:
            return {"context": "", "available": False, "error": str(exc)}

    @mcp.tool(annotations=_ro_m)
    async def memory_list_banks(
        base_url: str = "http://localhost:8888",
    ) -> dict[str, object]:
        """List all available Hindsight memory banks.

        Queries the Hindsight server for all configured banks. Useful for
        discovering which banks exist before calling recall or retain.

        Args:
            base_url: Hindsight server URL (default: ``http://localhost:8888``).

        Returns:
            Dict with ``banks`` list (each has id, name) and ``count`` integer.
        """
        try:
            import httpx

            resp = httpx.get(f"{base_url.rstrip('/')}/v1/default/banks", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                banks = data if isinstance(data, list) else data.get("banks", [])
                return {"banks": banks, "count": len(banks)}
            return {"banks": [], "count": 0, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {
                "banks": [],
                "count": 0,
                "error": f"Hindsight unavailable: {exc}",
            }

    # ========== AGENT FLEET TOOLS ==========

    @mcp.tool(annotations=_mut)
    async def agent_spawn_fleet(
        tasks: list[str],
        agent_hints: list[str | None] | None = None,
        provider: str = "auto",
    ) -> dict[str, Any]:
        """Dispatch multiple agent tasks concurrently and return a fleet ID.

        Each task runs in parallel via asyncio background tasks.  Results are
        stored in the in-process fleet store and are retrievable via
        :func:`agent_poll_fleet`.

        Args:
            tasks: List of task descriptions (natural language).  Must be
                non-empty; maximum 50 tasks per fleet.
            agent_hints: Optional list of agent names to use, parallel-indexed
                with ``tasks``.  ``None`` entries mean auto-select.  When
                omitted, all tasks are auto-assigned.  Valid names:
                ``developer``, ``devops``, ``git``, ``github``,
                ``performance``, ``qa``, ``security``.
            provider: LLM provider hint — ``'groq'``, ``'google'``,
                ``'ollama'``, or ``'auto'``.  Passed through to the agent
                executor for future model-routing support.

        Returns:
            ``{'fleet_id': str, 'task_count': int, 'status': 'dispatched'}``
        """
        logger.info(
            "mcp_tool_called",
            tool="agent_spawn_fleet",
            task_count=len(tasks),
            provider=provider,
        )

        if not tasks:
            return {"error": "tasks must be a non-empty list"}
        if len(tasks) > 50:
            return {"error": f"Too many tasks: {len(tasks)} (maximum 50 per fleet)"}

        # Normalise hints to a list the same length as tasks.
        hints: list[str | None]
        if agent_hints is None:
            hints = [None] * len(tasks)
        elif len(agent_hints) != len(tasks):
            return {
                "error": (
                    f"agent_hints length ({len(agent_hints)}) must match "
                    f"tasks length ({len(tasks)}) when provided"
                )
            }
        else:
            hints = list(agent_hints)

        fleet_id = "fleet-" + uuid.uuid4().hex[:8]

        # Initialise fleet entry before spawning tasks so poll can see it
        # immediately even if the background tasks haven't started yet.
        _FLEET_STORE[fleet_id] = {
            "fleet_id": fleet_id,
            "task_count": len(tasks),
            "completed_count": 0,
            "provider": provider,
            "results": [
                {
                    "task_id": f"{fleet_id}-{i}",
                    "task": task,
                    "agent": hints[i] or "auto",
                    "output": None,
                    "status": "pending",
                }
                for i, task in enumerate(tasks)
            ],
        }

        # Fire-and-forget — one asyncio Task per fleet member.
        for i, (task_text, hint) in enumerate(zip(tasks, hints)):
            asyncio.create_task(
                _run_fleet_task(fleet_id, i, task_text, hint, provider),
                name=f"{fleet_id}-task-{i}",
            )

        logger.info("fleet_dispatched", fleet_id=fleet_id, task_count=len(tasks))
        return {"fleet_id": fleet_id, "task_count": len(tasks), "status": "dispatched"}

    @mcp.tool(annotations=_ro)
    async def agent_poll_fleet(fleet_id: str) -> dict[str, Any]:
        """Poll the status of a previously spawned agent fleet.

        Args:
            fleet_id: The ``fleet_id`` returned by :func:`agent_spawn_fleet`.

        Returns:
            ::

                {
                    'status': 'pending' | 'running' | 'partial' | 'complete',
                    'task_count': int,
                    'completed_count': int,
                    'results': [
                        {
                            'task_id': str,
                            'task': str,
                            'agent': str,
                            'output': str | None,
                            'status': str,
                        }
                    ]
                }

            Returns ``{'error': str}`` when the ``fleet_id`` is unknown.
        """
        logger.info("mcp_tool_called", tool="agent_poll_fleet", fleet_id=fleet_id)

        fleet = _FLEET_STORE.get(fleet_id)
        if fleet is None:
            return {"error": f"Unknown fleet_id: {fleet_id!r}"}

        task_count: int = fleet["task_count"]
        completed: int = fleet["completed_count"]
        results: list[dict[str, Any]] = fleet["results"]

        if completed == 0:
            any_running = any(r["status"] == "running" for r in results)
            status = "running" if any_running else "pending"
        elif completed < task_count:
            status = "partial"
        else:
            status = "complete"

        return {
            "status": status,
            "task_count": task_count,
            "completed_count": completed,
            "results": list(results),
        }

    # ========== RESOURCES ==========

    @mcp.resource("tta://catalog")
    def get_catalog() -> str:
        """Get the complete TTA.dev primitives catalog."""
        primitives = analyzer.list_primitives()
        lines = ["# TTA.dev Primitives Catalog\n"]

        for prim in primitives:
            lines.append(f"## {prim['name']}")
            lines.append(f"{prim['description']}\n")
            lines.append(f"Import: `{prim['import_path']}`\n")
            if prim["use_cases"]:
                lines.append("Use cases:")
                for case in prim["use_cases"]:
                    lines.append(f"- {case}")
            lines.append("")

        return "\n".join(lines)

    @mcp.resource("tta://patterns")
    def get_patterns() -> str:
        """Get information about detectable code patterns."""
        from ttadev.primitives.analysis.patterns import PatternDetector

        detector = PatternDetector()
        info = detector.get_pattern_info()

        lines = ["# Detectable Code Patterns\n"]
        lines.append(f"Total patterns: {info['pattern_count']}\n")
        lines.append("## Patterns")
        for pattern in info["patterns"]:
            lines.append(f"- {pattern.replace('_', ' ').title()}")
        lines.append("\n## Inferred Requirements")
        for req in info["requirements"]:
            lines.append(f"- {req.replace('_', ' ').title()}")

        return "\n".join(lines)

    # ========== PROMPTS ==========

    @mcp.prompt()
    def analyze_and_improve(code: str, goal: str = "reliability") -> str:
        """Generate a prompt for analyzing and improving code.

        Args:
            code: The code to analyze
            goal: Improvement goal (reliability, performance, resilience)
        """
        return f"""Analyze this code and suggest TTA.dev primitive improvements.

Goal: {goal}

Code:
```python
{code}
```

Please:
1. Use the analyze_code tool to detect patterns
2. Review the recommendations
3. Show how to implement the top recommendations
4. Explain how these primitives will improve {goal}
"""

    @mcp.prompt()
    def implement_primitive(primitive_name: str, context: str = "") -> str:
        """Generate a prompt for implementing a specific primitive.

        Args:
            primitive_name: Name of the primitive to implement
            context: Additional context about the use case
        """
        return f"""Help me implement {primitive_name} in my code.

{f"Context: {context}" if context else ""}

Please:
1. Use get_primitive_info to get the documentation
2. Show the basic template
3. Explain the key parameters
4. Provide a complete working example
5. Suggest related primitives that might help
"""

    return mcp


def run_server(
    transport: str = "stdio",
    port: int = 8000,
) -> None:
    """Run the MCP server.

    Args:
        transport: Transport type (stdio, sse, http)
        port: Port for HTTP/SSE transport
    """
    if not MCP_AVAILABLE:
        print("Error: MCP package not installed.", file=sys.stderr)
        print("Install with: uv add mcp", file=sys.stderr)
        sys.exit(1)

    mcp = create_server()

    if transport == "stdio":
        mcp.run()
    elif transport == "sse":
        mcp.run(transport="sse", port=port)
    elif transport == "http":
        mcp.run(transport="streamable-http", port=port)
    else:
        print(f"Unknown transport: {transport}", file=sys.stderr)
        print("Available: stdio, sse, http", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """CLI entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="TTA.dev MCP Server - Primitive recommendations for AI coding agents"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE/HTTP transport (default: 8000)",
    )
    args = parser.parse_args()

    run_server(transport=args.transport, port=args.port)


if __name__ == "__main__":
    main()
