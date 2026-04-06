"""TTA.dev MCP Server Implementation.

Uses FastMCP for a clean, decorator-based API.
Exposes TTA.dev analysis and primitive recommendations as MCP tools.

Tool handlers live in the ``tools/`` sub-package; this module wires them
together and keeps the resource/prompt registrations, backward-compatibility
re-exports, and the ``run_server``/``main`` entry points.
"""

import argparse
import sys
from typing import TYPE_CHECKING, Any

import structlog

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

from ttadev.primitives.analysis import TTAAnalyzer

# ── Backward-compatibility re-exports ─────────────────────────────────────────
# Tests import these directly from this module; keep them importable.
from ttadev.primitives.mcp_server.tools._helpers import (  # noqa: F401
    _FLEET_STORE,
    _MAX_CODE_CHARS,
    _check_code_size,
    _idempotent_annotations,
    _mutating_annotations,
    _read_only_annotations,
)

logger = structlog.get_logger("tta_dev.mcp")


def create_server() -> Any:
    """Create and configure the MCP server.

    Returns:
        Configured FastMCP server instance

    Raises:
        ImportError: If MCP package is not installed
    """
    if not MCP_AVAILABLE or FastMCP is None:
        raise ImportError("MCP package not installed. Install with: uv add mcp")

    mcp = FastMCP(
        name="TTA.dev Primitives",
        instructions=(
            "TTA.dev provides composable workflow primitives for building reliable "
            "AI applications. Use analyze_code to get recommendations, "
            "get_primitive_info for documentation, and get_template for code snippets."
        ),
    )

    analyzer = TTAAnalyzer()

    _ro = _read_only_annotations()
    _mut = _mutating_annotations()
    _idem = _idempotent_annotations()

    # ── Register tool groups ───────────────────────────────────────────────────
    from ttadev.primitives.mcp_server.tools import (
        register_agent_tools,
        register_control_plane_tools,
        register_observability_tools,
        register_primitives_tools,
        register_transform_tools,
        register_workflow_tools,
    )

    register_primitives_tools(mcp, analyzer, _ro)
    register_transform_tools(mcp, analyzer, _ro)
    register_control_plane_tools(mcp, _ro, _mut, _idem)
    register_workflow_tools(mcp, _mut, _idem)
    register_observability_tools(mcp, _ro, _idem)
    register_agent_tools(mcp, _ro, _mut)

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
