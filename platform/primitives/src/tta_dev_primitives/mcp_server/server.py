"""TTA.dev MCP Server Implementation.

Uses FastMCP for a clean, decorator-based API.
Exposes TTA.dev analysis and primitive recommendations as MCP tools.
"""

import argparse
import sys
from typing import Any

import structlog

# Try to import MCP - graceful degradation if not available
try:
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None  # type: ignore

from tta_dev_primitives.analysis import TTAAnalyzer

logger = structlog.get_logger("tta_dev.mcp")


def create_server() -> "FastMCP":
    """Create and configure the MCP server.

    Returns:
        Configured FastMCP server instance

    Raises:
        ImportError: If MCP package is not installed
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP package not installed. Install with: uv add mcp")

    # Create server
    mcp = FastMCP(
        name="TTA.dev Primitives",
        instructions="TTA.dev provides composable workflow primitives for building reliable AI applications. Use analyze_code to get recommendations, get_primitive_info for documentation, and get_template for code snippets.",
    )

    # Shared analyzer instance
    analyzer = TTAAnalyzer()

    # ========== TOOLS ==========

    @mcp.tool()
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
            Analysis report with recommendations, including:
            - detected_patterns: Patterns found in the code
            - recommendations: List of primitive recommendations with templates
            - detected_issues: Potential problems found
            - optimization_opportunities: Ways to improve the code
        """
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

    @mcp.tool()
    async def get_primitive_info(primitive_name: str) -> dict[str, Any]:
        """Get detailed information about a TTA.dev primitive.

        Returns comprehensive documentation including description,
        use cases, code templates, and related primitives.

        Args:
            primitive_name: Name of the primitive (e.g., "RetryPrimitive")

        Returns:
            Primitive documentation including:
            - description: What the primitive does
            - import_path: Python import statement
            - use_cases: When to use this primitive
            - templates: Ready-to-use code templates
            - related_primitives: Primitives that work well together
        """
        return analyzer.get_primitive_info(primitive_name)

    @mcp.tool()
    async def list_primitives() -> list[dict[str, Any]]:
        """List all available TTA.dev primitives.

        Returns a list of all primitives with their descriptions
        and primary use cases.

        Returns:
            List of primitives with:
            - name: Primitive name
            - description: Brief description
            - import_path: Python import
            - use_cases: Example use cases
        """
        return analyzer.list_primitives()

    @mcp.tool()
    async def search_templates(query: str) -> list[dict[str, Any]]:
        """Search for primitive templates by keyword.

        Searches through all templates and examples to find
        relevant code patterns.

        Args:
            query: Search query (e.g., "retry", "cache", "parallel")

        Returns:
            List of matching templates with:
            - primitive_name: Which primitive this template is for
            - match_type: "template" or "example"
            - match_text: The matching content
        """
        return analyzer.search_templates(query)

    @mcp.tool()
    async def get_composition_example(
        primitives: list[str],
    ) -> dict[str, Any]:
        """Get an example of composing multiple primitives.

        Shows how to combine multiple primitives into a workflow
        using the >> (sequential) and | (parallel) operators.

        Args:
            primitives: List of primitive names to compose

        Returns:
            Composition example with:
            - code: Ready-to-use composition code
            - explanation: How the composition works
            - benefits: What this composition provides
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
from tta_dev_primitives import WorkflowContext

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
        }

    @mcp.tool()
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
            Transformation result including:
            - transformed_code: The modified code with primitive applied
            - wrapped_functions: List of functions that were wrapped
            - diff: Unified diff showing changes
        """
        import difflib

        from tta_dev_primitives.cli.app import (
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

    @mcp.tool()
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
            Combined result including:
            - analysis: Full analysis report
            - transformation: Transformed code (if applicable)
            - applied_primitive: Which primitive was applied
        """
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
        from tta_dev_primitives.cli.app import (
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

    @mcp.tool()
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
            Suggestions including:
            - issues: Problems found with line numbers
            - opportunities: Optimization opportunities with line numbers
            - top_fixes: Top primitive recommendations with ready-to-use code
        """
        import re

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
        from tta_dev_primitives.analysis.patterns import PatternDetector

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
