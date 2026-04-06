"""TTA.dev MCP server: code transformation tools."""

from typing import Any

from ._helpers import (
    _check_code_size,
    logger,
)


def register_transform_tools(mcp: Any, analyzer: Any, _ro: Any) -> None:
    """Register code transformation and analysis tools with the MCP server."""

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

        from ttadev.primitives.analysis.transformer import transform_code as _transform_code

        logger.info(
            "mcp_tool_called",
            tool="rewrite_code",
            primitive=primitive,
            auto_detect=auto_detect,
            code_length=len(code),
        )

        result = _transform_code(
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
