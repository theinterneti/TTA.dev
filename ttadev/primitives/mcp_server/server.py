"""TTA.dev MCP Server Implementation.

Uses FastMCP for a clean, decorator-based API.
Exposes TTA.dev analysis and primitive recommendations as MCP tools.
"""

import argparse
import sys
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

        from ttadev.primitives.cli.app import (
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
        from ttadev.primitives.cli.app import (
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
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Transition a tracked workflow step to RUNNING.

        Pass ``trace_id`` and ``span_id`` to stamp the current OTel span
        context onto the step record.  Safe to call again on retry — the
        trace context is replaced each time.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_mark_workflow_step_running",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.mark_workflow_step_running(
                task_id,
                step_index=step_index,
                trace_id=trace_id,
                span_id=span_id,
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
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record the result and confidence score for a completed workflow step.

        ``confidence`` must be in the range 0.0–1.0.  Recording the result
        automatically evaluates any pending POLICY gates attached to the task.
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
            service = _create_control_plane_service(data_dir)
            task = service.record_workflow_step_result(
                task_id,
                step_index=step_index,
                result_summary=result_summary,
                confidence=confidence,
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
            service = _create_control_plane_service(data_dir)
            task = service.mark_workflow_step_failed(
                task_id,
                step_index=step_index,
                error_summary=error_summary,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

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
