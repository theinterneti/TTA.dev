"""TTA.dev CLI Application.

Main Typer application with all CLI commands.

Configuration is loaded from (in priority order):
1. Command-line arguments (highest priority)
2. .ttadevrc.yaml / .ttadevrc.yml / .ttadevrc.toml / .ttadevrc.json
3. pyproject.toml [tool.tta-dev] section
4. Default values (lowest priority)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from tta_dev_primitives.analysis import TTAAnalyzer
from tta_dev_primitives.config import (
    TTAConfig,
    find_config_file,
    generate_default_config,
    load_config,
    save_config,
)

if TYPE_CHECKING:
    from tta_dev_primitives.analysis import AnalysisReport

# Create the main app
app = typer.Typer(
    name="tta-dev",
    help="TTA.dev - Composable workflow primitives for reliable AI applications.",
    add_completion=True,
    no_args_is_help=True,
)

# Rich console for pretty output
console = Console()

# Shared analyzer instance
analyzer = TTAAnalyzer()

# Global config (loaded once per invocation)
_config: TTAConfig | None = None


def _get_config(config_path: Path | None = None) -> TTAConfig:
    """Get configuration, loading from file if available."""
    global _config
    if _config is None or config_path is not None:
        _config = load_config(config_path)
    return _config


def _resolve_option(cli_value: object, config_value: object, default: object) -> object:
    """Resolve option value: CLI > config > default.

    Returns config value if CLI value equals the default (wasn't set by user).
    """
    if cli_value != default:
        return cli_value  # User explicitly set via CLI
    return config_value  # Use config file value


@app.callback()
def main_callback(
    ctx: typer.Context,
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-C",
            help="Path to configuration file",
            exists=True,
            readable=True,
        ),
    ] = None,
) -> None:
    """TTA.dev CLI - Load configuration before running commands."""
    # Load config file (explicit path or auto-detect)
    global _config
    _config = load_config(config_file)

    # Store in context for commands to access
    ctx.ensure_object(dict)
    ctx.obj["config"] = _config

    # Show config info if verbose
    config_path = find_config_file() if config_file is None else config_file
    if config_path:
        # Only log if not in quiet mode (will be checked by commands)
        pass  # Config loaded silently


@app.command()
def analyze(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="File to analyze for primitive recommendations",
        exists=True,
        readable=True,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table, json, brief (default from config)",
    ),
    min_confidence: float = typer.Option(
        None,
        "--min-confidence",
        "-c",
        help="Minimum confidence threshold (0.0 to 1.0, default from config)",
    ),
    show_templates: bool = typer.Option(
        None,
        "--templates",
        "-t",
        help="Show code templates for recommendations",
    ),
    quiet: bool = typer.Option(
        None,
        "--quiet",
        "-q",
        help="Suppress debug logs (cleaner output for agents)",
    ),
    show_lines: bool = typer.Option(
        None,
        "--lines",
        "-l",
        help="Show line numbers for detected patterns",
    ),
    suggest_diff: bool = typer.Option(
        None,
        "--suggest-diff",
        "-d",
        help="Show suggested code transformations as diffs",
    ),
    apply: bool = typer.Option(
        None,
        "--apply",
        "-a",
        help="Auto-apply top recommendation (modifies file in place)",
    ),
    apply_primitive: str = typer.Option(
        None,
        "--apply-primitive",
        "-p",
        help="Apply specific primitive instead of top recommendation",
    ),
) -> None:
    """Analyze code and suggest TTA.dev primitives.

    Analyzes the given file for patterns and recommends appropriate
    TTA.dev primitives with confidence scores and code templates.

    Configuration values from .ttadevrc.yaml are used as defaults.
    CLI arguments override config file values.

    Examples:
        tta-dev analyze api_client.py
        tta-dev analyze app.py --output json
        tta-dev analyze workflow.py --min-confidence 0.5 --templates
        tta-dev analyze api.py --quiet --suggest-diff  # Agent-friendly
        tta-dev analyze api.py --apply                 # Auto-fix with top rec
        tta-dev analyze api.py --apply-primitive RetryPrimitive  # Apply specific
    """
    # Get config (loaded by callback)
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options: CLI > config > hardcoded default
    output = output if output is not None else config.analysis.output_format
    min_confidence = (
        min_confidence if min_confidence is not None else config.analysis.min_confidence
    )
    show_templates = (
        show_templates if show_templates is not None else config.analysis.show_templates
    )
    quiet = quiet if quiet is not None else config.analysis.quiet
    show_lines = (
        show_lines if show_lines is not None else config.analysis.show_line_numbers
    )
    suggest_diff = (
        suggest_diff if suggest_diff is not None else config.transform.suggest_diff
    )
    apply = apply if apply is not None else config.transform.auto_fix

    # Suppress logs if --quiet
    if quiet:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
        )

    try:
        code = file.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1) from e

    # Find line numbers for patterns if requested
    line_info = _find_pattern_lines(code) if show_lines or suggest_diff else {}

    # Run analysis
    report = analyzer.analyze(
        code,
        file_path=str(file),
        min_confidence=min_confidence,
    )

    # Handle --apply or --apply-primitive
    if apply or apply_primitive:
        from tta_dev_primitives.analysis.transformer import transform_code

        # Use AST-based transformer for smarter rewrites
        if apply_primitive:
            result = transform_code(code, primitive=apply_primitive, auto_detect=False)
        else:
            # Auto-detect anti-patterns and transform
            result = transform_code(code, auto_detect=True)

        if not result.success:
            console.print(f"[red]Transformation failed: {result.error}[/red]")
            raise typer.Exit(1) from None

        if not result.changes_made:
            # Fall back to old method if AST transform didn't work
            if not report.recommendations:
                if not quiet:
                    console.print("[yellow]No recommendations to apply.[/yellow]")
                raise typer.Exit(0) from None

            # Determine which primitive to apply
            primitive_to_apply = apply_primitive
            if not primitive_to_apply:
                primitive_to_apply = report.recommendations[0].primitive_name

            # Verify the primitive exists
            info = analyzer.get_primitive_info(primitive_to_apply)
            if "error" in info:
                console.print(f"[red]Unknown primitive: {primitive_to_apply}[/red]")
                raise typer.Exit(1) from None

            # Find targets and generate transformation (old method)
            targets = _find_transform_targets(code, primitive_to_apply, None)
            if not targets:
                if not quiet:
                    console.print(
                        f"[yellow]No suitable functions found for {primitive_to_apply}[/yellow]"
                    )
                raise typer.Exit(0) from None

            transformed = _generate_transformation(
                code, primitive_to_apply, targets, info
            )

            # Write back to file
            file.write_text(transformed)

            if not quiet:
                console.print(
                    f"[green]✓ Applied {primitive_to_apply} to {file}[/green]"
                )
                console.print(
                    f"  Wrapped functions: {', '.join(t['name'] for t in targets)}"
                )
        else:
            # AST transform succeeded
            file.write_text(result.transformed_code)

            if not quiet:
                console.print(f"[green]✓ Transformed {file}[/green]")
                console.print(f"  Changes made: {len(result.changes_made)}")
                for change in result.changes_made:
                    change_type = change.get("type", "unknown")
                    console.print(f"    • {change_type}: {change}")
                console.print(f"  Imports added: {len(result.imports_added)}")

        return  # Exit after applying

    # Output based on format
    if output == "json":
        # Enrich with line info if available
        result = report.to_dict()
        if line_info:
            result["line_info"] = line_info
        print(json.dumps(result, indent=2, default=str))
    elif output == "brief":
        _print_brief(report)
    else:
        _print_table(report, show_templates, line_info if show_lines else None)

    # Show diffs if requested
    if suggest_diff and report.recommendations:
        _print_suggested_diffs(code, str(file), report, line_info)


def _print_brief(report: AnalysisReport) -> None:
    """Print brief summary of recommendations."""
    if not report.recommendations:
        console.print("[yellow]No recommendations found.[/yellow]")
        return

    console.print(f"\n[bold]Analysis: {report.context.file_path}[/bold]")
    console.print(f"Patterns: {', '.join(report.analysis.detected_patterns) or 'none'}")
    console.print(f"Complexity: {report.analysis.complexity_level}")
    console.print()

    for rec in report.recommendations:
        console.print(
            f"  • [cyan]{rec.primitive_name}[/cyan] ({rec.confidence_percent}) - {rec.reasoning}"
        )


def _print_table(
    report: AnalysisReport, show_templates: bool = False, line_info: dict | None = None
) -> None:
    """Print formatted table with recommendations."""
    # Header panel
    console.print(
        Panel(
            f"[bold]TTA.dev Analysis[/bold]\n"
            f"File: {report.context.file_path}\n"
            f"Patterns: {', '.join(report.analysis.detected_patterns) or 'none'}\n"
            f"Complexity: {report.analysis.complexity_level}",
            title="📊 Analysis Report",
            expand=False,
        )
    )

    if not report.recommendations:
        console.print(
            "\n[yellow]No recommendations found above the confidence threshold.[/yellow]"
        )
        return

    # Recommendations table
    table = Table(title="Recommendations", show_header=True, header_style="bold cyan")
    table.add_column("Primitive", style="cyan", no_wrap=True)
    table.add_column("Confidence", justify="center", style="green")
    table.add_column("Reasoning", style="white")
    table.add_column("Related", style="dim")

    for rec in report.recommendations:
        related = (
            ", ".join(rec.related_primitives[:2]) if rec.related_primitives else "-"
        )
        table.add_row(
            rec.primitive_name,
            rec.confidence_percent,
            rec.reasoning[:50] + "..." if len(rec.reasoning) > 50 else rec.reasoning,
            related,
        )

    console.print(table)

    # Show templates if requested
    if show_templates and report.recommendations:
        console.print("\n[bold]Code Templates:[/bold]")
        for rec in report.recommendations[:2]:  # Show top 2
            if rec.code_template:
                console.print(f"\n[cyan]{rec.primitive_name}[/cyan]")
                console.print(
                    Syntax(
                        rec.code_template, "python", theme="monokai", line_numbers=False
                    )
                )

    # Show detected issues
    if report.context.detected_issues:
        console.print("\n[bold yellow]⚠️  Detected Issues:[/bold yellow]")
        for issue in report.context.detected_issues:
            lines_str = ""
            if line_info:
                # Find relevant lines for this issue
                if "API calls" in issue and "api_calls" in line_info:
                    lines_str = (
                        f" (lines: {', '.join(map(str, line_info['api_calls'][:3]))})"
                    )
                elif "Async" in issue and "async_operations" in line_info:
                    lines_str = f" (lines: {', '.join(map(str, line_info['async_operations'][:3]))})"
            console.print(f"  • {issue}{lines_str}")

    # Show optimization opportunities
    if report.context.optimization_opportunities:
        console.print("\n[bold green]💡 Optimization Opportunities:[/bold green]")
        for opp in report.context.optimization_opportunities:
            lines_str = ""
            if line_info and "API calls" in opp and "api_calls" in line_info:
                lines_str = (
                    f" (lines: {', '.join(map(str, line_info['api_calls'][:5]))})"
                )
            console.print(f"  • {opp}{lines_str}")


def _find_pattern_lines(code: str) -> dict[str, list[int]]:
    """Find line numbers for different patterns in the code."""
    lines = code.split("\n")
    result: dict[str, list[int]] = {
        "api_calls": [],
        "async_operations": [],
        "error_handling": [],
        "llm_patterns": [],
        "for_loops": [],
        "timeout_patterns": [],
        "fallback_patterns": [],
    }

    api_patterns = re.compile(r"(requests\.|httpx\.|aiohttp|\.get\(|\.post\(|fetch\()")
    async_patterns = re.compile(r"(async def|await\s)")
    error_patterns = re.compile(r"(try:|except\s|raise\s)")
    llm_patterns = re.compile(
        r"(openai|anthropic|chat.*completion|llm|gpt|claude)", re.IGNORECASE
    )
    for_patterns = re.compile(r"^\s*for\s+\w+\s+in\s+")
    timeout_patterns = re.compile(
        r"(asyncio\.wait_for|asyncio\.timeout|signal\.alarm|timeout\s*=|TimeoutError)"
    )
    fallback_patterns = re.compile(
        r"(except\s*:?\s*\n?\s*return|or\s+default|fallback|backup|if\s+\w+\s+is\s+None)"
    )

    for i, line in enumerate(lines, 1):
        if api_patterns.search(line):
            result["api_calls"].append(i)
        if async_patterns.search(line):
            result["async_operations"].append(i)
        if error_patterns.search(line):
            result["error_handling"].append(i)
        if llm_patterns.search(line):
            result["llm_patterns"].append(i)
        if for_patterns.search(line):
            result["for_loops"].append(i)
        if timeout_patterns.search(line):
            result["timeout_patterns"].append(i)
        if fallback_patterns.search(line):
            result["fallback_patterns"].append(i)

    return {k: v for k, v in result.items() if v}  # Only return non-empty


def _detect_anti_patterns(code: str) -> dict[str, Any]:
    """Detect anti-patterns that should be converted to TTA.dev primitives."""
    from tta_dev_primitives.analysis.patterns import PatternDetector

    detector = PatternDetector()
    return detector.get_anti_pattern_summary(code)


def _print_suggested_diffs(
    code: str,
    file_path: str,
    report: AnalysisReport,
    line_info: dict[str, list[int]],
) -> None:
    """Print suggested code transformations."""
    console.print("\n[bold blue]📝 Suggested Transformations:[/bold blue]")

    # First, detect anti-patterns using the detector
    anti_pattern_summary = _detect_anti_patterns(code)
    if anti_pattern_summary["total_issues"] > 0:
        console.print(
            f"\n[bold red]⚠️ Found {anti_pattern_summary['total_issues']} anti-patterns:[/bold red]"
        )
        for issue in anti_pattern_summary["issues"][:5]:  # Show top 5
            console.print(f"  Line {issue['line']}: [yellow]{issue['issue']}[/yellow]")
            console.print(f"    → {issue['fix']}")
            console.print(
                f"    [dim]{issue['code'][:60]}...[/dim]"
                if len(issue["code"]) > 60
                else f"    [dim]{issue['code']}[/dim]"
            )

    # Get top recommendation
    top_rec = report.recommendations[0] if report.recommendations else None
    if not top_rec:
        return

    # For timeout suggestions
    if "timeout_patterns" in line_info:
        if any("Timeout" in rec.primitive_name for rec in report.recommendations):
            console.print("\n[cyan]Timeout wrapper suggestion:[/cyan]")
            console.print(
                f"  Lines {line_info['timeout_patterns'][:3]} have manual timeout handling."
            )
            console.print(
                "\n[dim]Replace asyncio.wait_for with TimeoutPrimitive:[/dim]"
            )
            timeout_code = """from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives import WorkflowContext

# Wrap your operation with timeout protection
protected_operation = TimeoutPrimitive(
    primitive=your_async_function,
    timeout_seconds=30.0,
    raise_on_timeout=True,
)

# Usage:
context = WorkflowContext(workflow_id="timeout-workflow")
result = await protected_operation.execute(input_data, context)"""
            console.print(
                Syntax(timeout_code, "python", theme="monokai", line_numbers=False)
            )

    # For fallback suggestions
    if "fallback_patterns" in line_info or "error_handling" in line_info:
        if any("Fallback" in rec.primitive_name for rec in report.recommendations):
            console.print("\n[cyan]Fallback cascade suggestion:[/cyan]")
            lines_to_show = line_info.get(
                "fallback_patterns", line_info.get("error_handling", [])
            )
            console.print(
                f"  Lines {lines_to_show[:3]} have manual fallback/error handling."
            )
            console.print("\n[dim]Replace with FallbackPrimitive:[/dim]")
            fallback_code = """from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives import WorkflowContext

# Define your primary and fallback operations
resilient_workflow = FallbackPrimitive(
    primary=primary_api_call,
    fallbacks=[
        backup_api_call,
        local_fallback,
    ]
)

# Usage - automatically tries fallbacks on failure:
context = WorkflowContext(workflow_id="fallback-workflow")
result = await resilient_workflow.execute(input_data, context)"""
            console.print(
                Syntax(fallback_code, "python", theme="monokai", line_numbers=False)
            )

    # For parallelization suggestions
    if "api_calls" in line_info and len(line_info["api_calls"]) >= 2:
        if any("Parallel" in rec.primitive_name for rec in report.recommendations):
            console.print("\n[cyan]Parallelization suggestion:[/cyan]")
            console.print(
                f"  Lines {line_info['api_calls']} contain API calls that could run concurrently."
            )
            console.print("\n[dim]Before:[/dim]")
            _print_code_context(code, line_info["api_calls"][:2], context=1)
            console.print("\n[dim]After (using ParallelPrimitive):[/dim]")
            parallel_code = """from tta_dev_primitives import ParallelPrimitive, WorkflowContext

# Wrap your API calls as primitives
workflow = ParallelPrimitive([
    api_call_1,  # These will run concurrently
    api_call_2,
    api_call_3,
])

# Execute all in parallel
context = WorkflowContext(workflow_id="parallel-api")
results = await workflow.execute(input_data, context)"""
            console.print(
                Syntax(parallel_code, "python", theme="monokai", line_numbers=False)
            )

    # For retry suggestions
    if top_rec.primitive_name == "RetryPrimitive" and "api_calls" in line_info:
        console.print("\n[cyan]Retry wrapper suggestion:[/cyan]")
        console.print(
            f"  API calls at lines {line_info['api_calls'][:3]} should be wrapped with retry logic."
        )
        if top_rec.code_template:
            console.print(
                Syntax(
                    top_rec.code_template, "python", theme="monokai", line_numbers=False
                )
            )

    # For circuit breaker
    if top_rec.primitive_name == "CircuitBreakerPrimitive":
        console.print("\n[cyan]Circuit breaker suggestion:[/cyan]")
        console.print(
            "  Multiple error handlers detected. Consider wrapping with CircuitBreakerPrimitive."
        )
        if top_rec.code_template:
            console.print(
                Syntax(
                    top_rec.code_template, "python", theme="monokai", line_numbers=False
                )
            )


def _print_code_context(code: str, line_numbers: list[int], context: int = 2) -> None:
    """Print code snippets around specified line numbers."""
    lines = code.split("\n")
    printed = set()

    for line_num in line_numbers:
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)

        if start in printed:
            continue

        snippet = "\n".join(
            f"{i + 1:3d} | {lines[i]}" for i in range(start, end) if i not in printed
        )
        if snippet:
            console.print(f"[dim]{snippet}[/dim]")
            printed.update(range(start, end))


@app.command()
def primitives(
    ctx: typer.Context,
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table, json (default from config)",
    ),
) -> None:
    """List all available TTA.dev primitives.

    Shows all primitives with their descriptions and use cases.

    Configuration values from .ttadevrc.yaml are used as defaults.

    Examples:
        tta-dev primitives
        tta-dev primitives --output json
    """
    # Get config
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options from config
    output = output if output is not None else config.analysis.output_format

    prims = analyzer.list_primitives()

    if output == "json":
        print(json.dumps(prims, indent=2))
        return

    table = Table(
        title="TTA.dev Primitives", show_header=True, header_style="bold cyan"
    )
    table.add_column("Primitive", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Use Cases", style="dim")

    for prim in prims:
        use_cases = ", ".join(prim["use_cases"][:2]) if prim["use_cases"] else ""
        table.add_row(
            prim["name"],
            prim["description"],
            use_cases[:40] + "..." if len(use_cases) > 40 else use_cases,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(prims)} primitives[/dim]")


@app.command()
def docs(
    ctx: typer.Context,
    primitive: str = typer.Argument(
        ...,
        help="Name of the primitive to get documentation for",
    ),
    show_all_templates: bool = typer.Option(
        None,
        "--all",
        "-a",
        help="Show all available templates (default from config)",
    ),
) -> None:
    """Show documentation for a specific primitive.

    Displays detailed information including description, use cases,
    related primitives, and code templates.

    Configuration values from .ttadevrc.yaml are used as defaults.

    Examples:
        tta-dev docs RetryPrimitive
        tta-dev docs CachePrimitive --all
    """
    # Get config
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options from config
    show_all_templates = (
        show_all_templates
        if show_all_templates is not None
        else config.analysis.show_templates
    )

    info = analyzer.get_primitive_info(primitive)

    if "error" in info:
        console.print(f"[red]{info['error']}[/red]")
        console.print("\nAvailable primitives:")
        for p in analyzer.list_primitives():
            console.print(f"  • {p['name']}")
        raise typer.Exit(1)

    # Header
    console.print(
        Panel(
            f"[bold]{info['name']}[/bold]\n\n"
            f"{info['description']}\n\n"
            f"[dim]Import: {info['import_path']}[/dim]",
            title="📚 Primitive Documentation",
            expand=False,
        )
    )

    # Use cases
    if info["use_cases"]:
        console.print("\n[bold]Use Cases:[/bold]")
        for case in info["use_cases"]:
            console.print(f"  • {case}")

    # Related primitives
    if info["related_primitives"]:
        console.print(
            f"\n[bold]Related Primitives:[/bold] {', '.join(info['related_primitives'])}"
        )

    # Templates
    templates = info.get("templates", {})
    if templates:
        console.print("\n[bold]Code Templates:[/bold]")

        if show_all_templates:
            for name, template in templates.items():
                console.print(f"\n[cyan]Template: {name}[/cyan]")
                console.print(
                    Syntax(template, "python", theme="monokai", line_numbers=False)
                )
        else:
            # Show just the basic template
            basic = templates.get(
                "basic", list(templates.values())[0] if templates else ""
            )
            if basic:
                console.print(
                    Syntax(basic, "python", theme="monokai", line_numbers=False)
                )
            console.print(
                f"\n[dim]Use --all to see all {len(templates)} templates[/dim]"
            )


@app.command()
def serve(
    ctx: typer.Context,
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport type: stdio, sse, http",
    ),
    port: int = typer.Option(
        None,
        "--port",
        "-p",
        help="Port for HTTP/SSE transport (default from config)",
    ),
) -> None:
    """Start the TTA.dev MCP server.

    Starts a Model Context Protocol server that exposes TTA.dev
    primitives as tools for AI agents like Claude, Copilot, and Cline.

    Configuration values from .ttadevrc.yaml are used as defaults.

    Examples:
        tta-dev serve                    # stdio (default for Claude Desktop)
        tta-dev serve --transport sse    # SSE transport
        tta-dev serve --transport http --port 3000
    """
    # Get config
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options from config
    port = port if port is not None else config.mcp.port

    console.print("[bold]Starting TTA.dev MCP Server[/bold]")
    console.print(f"Transport: {transport}")
    if transport != "stdio":
        console.print(f"Port: {port}")

    try:
        # Import and run the MCP server
        from tta_dev_primitives.mcp_server import run_server

        run_server(transport=transport, port=port)
    except ImportError as e:
        console.print(f"[red]MCP server not available: {e}[/red]")
        console.print("[dim]Install with: uv add mcp[/dim]")
        raise typer.Exit(1) from e


@app.command()
def transform(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="File to transform",
        exists=True,
        readable=True,
    ),
    primitive: str = typer.Argument(
        ...,
        help="Primitive to wrap code with (e.g., RetryPrimitive, CachePrimitive)",
    ),
    function: str = typer.Option(
        None,
        "--function",
        "-f",
        help="Specific function to wrap (default: auto-detect)",
    ),
    output: str = typer.Option(
        "stdout",
        "--output",
        "-o",
        help="Output: stdout, file, or diff",
    ),
    quiet: bool = typer.Option(
        None,
        "--quiet",
        "-q",
        help="Suppress informational output (default from config)",
    ),
) -> None:
    """Transform code by wrapping with a TTA.dev primitive.

    Automatically detects functions that match the primitive's use case
    and generates transformed code.

    Configuration values from .ttadevrc.yaml are used as defaults.

    Examples:
        tta-dev transform api.py RetryPrimitive           # Wrap API calls with retry
        tta-dev transform api.py CachePrimitive -f fetch  # Cache specific function
        tta-dev transform api.py ParallelPrimitive -o diff  # Show as diff
    """
    # Get config
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options from config
    quiet = quiet if quiet is not None else config.analysis.quiet

    try:
        code = file.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1) from e

    # Get primitive info
    info = analyzer.get_primitive_info(primitive)
    if "error" in info:
        console.print(f"[red]Unknown primitive: {primitive}[/red]")
        console.print("[dim]Use 'tta-dev primitives' to see available primitives[/dim]")
        raise typer.Exit(1) from None

    # Find target functions
    targets = _find_transform_targets(code, primitive, function)

    if not targets:
        if not quiet:
            console.print(
                f"[yellow]No suitable functions found for {primitive}[/yellow]"
            )
        raise typer.Exit(0) from None

    # Generate transformed code
    transformed = _generate_transformation(code, primitive, targets, info)

    if output == "diff":
        _print_diff(code, transformed, str(file))
    elif output == "file":
        file.write_text(transformed)
        if not quiet:
            console.print(f"[green]✓ Transformed {file}[/green]")
    else:
        if not quiet:
            console.print(f"[bold]Transformed code ({primitive}):[/bold]\n")
        print(transformed)


def _find_transform_targets(
    code: str, primitive: str, specific_function: str | None
) -> list[dict]:
    """Find functions suitable for transformation."""
    import ast

    targets = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return targets

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # If specific function requested, only match that
            if specific_function and node.name != specific_function:
                continue

            # Determine if function is suitable for the primitive
            func_code = ast.get_source_segment(code, node) or ""
            suitable = _is_suitable_for_primitive(func_code, primitive)

            if suitable or specific_function:
                targets.append(
                    {
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, "end_lineno", node.lineno + 10),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "code": func_code,
                    }
                )

    return targets


def _is_suitable_for_primitive(func_code: str, primitive: str) -> bool:
    """Check if a function is suitable for a specific primitive."""
    code_lower = func_code.lower()

    patterns = {
        "RetryPrimitive": ["request", "fetch", "get(", "post(", "api", "http"],
        "CachePrimitive": ["llm", "openai", "claude", "gpt", "query", "fetch"],
        "TimeoutPrimitive": ["await", "async", "request", "api", "external"],
        "CircuitBreakerPrimitive": ["request", "api", "external", "service"],
        "ParallelPrimitive": ["for ", "requests", "multiple", "batch"],
        "FallbackPrimitive": ["llm", "openai", "api", "provider"],
        "SequentialPrimitive": ["async def", "await", "step", "pipeline", "process"],
        "RouterPrimitive": [
            "if ",
            "elif ",
            "match",
            "provider",
            "model",
            "tier",
            "handler",
        ],
        "AdaptivePrimitive": ["llm", "openai", "claude", "retry", "adaptive"],
        "AdaptiveRetryPrimitive": ["request", "api", "retry", "fetch"],
        "CompensationPrimitive": [
            "try",
            "except",
            "rollback",
            "cleanup",
            "undo",
            "delete",
            "cancel",
            "revert",
            "saga",
            "transaction",
        ],
    }

    keywords = patterns.get(primitive, [])
    # If no specific patterns defined, match any async function
    if not keywords:
        return "async def" in code_lower or "await" in code_lower
    return any(kw in code_lower for kw in keywords)


def _generate_transformation(
    code: str, primitive: str, targets: list[dict], info: dict
) -> str:
    """Generate transformed code."""
    # Use AST transformer for smarter extraction on specific primitives
    if primitive == "CompensationPrimitive":
        return _generate_compensation_transformation(code, targets, info)
    if primitive == "TimeoutPrimitive":
        return _generate_timeout_transformation(code, targets, info)
    if primitive == "FallbackPrimitive":
        return _generate_fallback_transformation(code, targets, info)
    if primitive == "RouterPrimitive":
        return _generate_router_transformation(code, targets, info)
    if primitive == "CircuitBreakerPrimitive":
        return _generate_circuit_breaker_transformation(code, targets, info)
    if primitive == "MemoryPrimitive":
        return _generate_memory_transformation(code, targets, info)
    if primitive == "DelegationPrimitive":
        return _generate_delegation_transformation(code, targets, info)
    if primitive == "SequentialPrimitive":
        return _generate_sequential_transformation(code, targets, info)
    if primitive == "AdaptivePrimitive":
        return _generate_adaptive_transformation(code, targets, info)

    import_path = info.get("import_path", f"from tta_dev_primitives import {primitive}")
    lines = code.split("\n")

    # Add import at the top (after existing imports)
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_idx = i + 1
        elif line.strip() and not line.startswith("#") and import_idx > 0:
            break

    # Check if import already exists
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Add wrapper usage comment at the end
    wrapper_code = _generate_wrapper_code(primitive, targets, info)
    lines.append("")
    lines.append("# --- TTA.dev Transformation ---")
    lines.append(wrapper_code)

    return "\n".join(lines)


def _generate_wrapper_code(primitive: str, targets: list[dict], info: dict) -> str:
    """Generate the wrapper code for the primitive."""
    func_names = [t["name"] for t in targets]
    is_async = any(t["is_async"] for t in targets)

    templates = {
        "RetryPrimitive": f"""
# Wrap {func_names[0]} with retry logic
{func_names[0]}_with_retry = RetryPrimitive(
    primitive={func_names[0]},
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
)

# Usage:
# context = WorkflowContext(workflow_id="retry-workflow")
# result = {"await " if is_async else ""}await {func_names[0]}_with_retry.execute(data, context)
""",
        "CachePrimitive": f"""
# Cache results from {func_names[0]}
cached_{func_names[0]} = CachePrimitive(
    primitive={func_names[0]},
    ttl_seconds=3600,  # 1 hour
    max_size=1000,
)

# Usage:
# context = WorkflowContext(workflow_id="cached-workflow")
# result = await cached_{func_names[0]}.execute(data, context)
""",
        "TimeoutPrimitive": f"""
# Add timeout protection to {func_names[0]}
protected_{func_names[0]} = TimeoutPrimitive(
    primitive={func_names[0]},
    timeout_seconds=30.0,
)

# Usage:
# context = WorkflowContext(workflow_id="timeout-workflow")
# result = await protected_{func_names[0]}.execute(data, context)
""",
        "ParallelPrimitive": f"""
# Execute multiple functions in parallel
parallel_workflow = ParallelPrimitive([
    {", ".join(func_names)}
])

# Usage:
# context = WorkflowContext(workflow_id="parallel-workflow")
# results = await parallel_workflow.execute(data, context)
""",
        "FallbackPrimitive": f"""
# Add fallback cascade to {func_names[0]}
resilient_{func_names[0]} = FallbackPrimitive(
    primary={func_names[0]},
    fallbacks=[
        backup_{func_names[0]},  # First fallback
        local_{func_names[0]},   # Second fallback
    ]
)

# Usage - automatically tries fallbacks on failure:
# context = WorkflowContext(workflow_id="fallback-workflow")
# result = await resilient_{func_names[0]}.execute(data, context)
""",
        "CircuitBreakerPrimitive": f"""
# Protect {func_names[0]} with circuit breaker
protected_{func_names[0]} = CircuitBreakerPrimitive(
    primitive={func_names[0]},
    failure_threshold=5,      # Open circuit after 5 failures
    recovery_timeout=60,      # Wait 60 seconds before half-open
    expected_successes=2,     # 2 successes to close circuit
)

# Usage:
# context = WorkflowContext(workflow_id="circuit-breaker-workflow")
# result = await protected_{func_names[0]}.execute(data, context)
""",
        "SequentialPrimitive": (
            f"# Compose {', '.join(func_names)} into a sequential workflow\n"
            "sequential_workflow = SequentialPrimitive([\n"
            f"    {','.join(func_names)}\n"
            "])\n\n"
            "# Or use the >> operator for cleaner composition:\n"
            f"# workflow = {' >> '.join(func_names)}\n\n"
            "# Usage:\n"
            '# context = WorkflowContext(workflow_id="sequential-workflow")\n'
            "# result = await sequential_workflow.execute(initial_data, context)\n"
        ),
        "RouterPrimitive": """
# Dynamic routing based on input conditions
router = RouterPrimitive(
    routes={
        "fast": fast_handler,
        "balanced": balanced_handler,
        "quality": quality_handler,
    },
    router_fn=lambda data, ctx: data.get("tier", "balanced"),
    default="balanced"
)

# Usage:
# context = WorkflowContext(workflow_id="router-workflow")
# result = await router.execute({"tier": "fast", "data": input_data}, context)
""",
        "CompensationPrimitive": f"""
# Wrap {func_names[0]} with saga/compensation pattern
# Forward operation performs the main action
# Compensation operation undoes it on failure

async def {func_names[0]}_forward(data: dict, context: WorkflowContext):
    \"\"\"Forward operation - main business logic.\"\"\"
    # Extract the main operation from {func_names[0]}
    # This runs first and produces a result
    pass


async def {func_names[0]}_compensation(data: dict, context: WorkflowContext):
    \"\"\"Compensation operation - rollback/cleanup on failure.\"\"\"
    # Extract the cleanup/rollback logic from {func_names[0]}
    # This runs if forward fails or if later steps fail
    pass


# Create the saga workflow
{func_names[0]}_saga = CompensationPrimitive(
    forward={func_names[0]}_forward,
    compensation={func_names[0]}_compensation,
)

# Usage:
# context = WorkflowContext(workflow_id="saga-workflow")
# result = await {func_names[0]}_saga.execute(data, context)
# On failure, compensation is automatically called
""",
    }

    return templates.get(primitive, f"# TODO: Wrap with {primitive}")


def _generate_compensation_transformation(
    code: str, targets: list[dict], info: dict
) -> str:
    """Generate smart CompensationPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import CompensationDetector

    lines = code.split("\n")

    # Add imports
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_idx = i + 1
        elif line.strip() and not line.startswith("#") and import_idx > 0:
            break

    import_path = info.get(
        "import_path", "from tta_dev_primitives.recovery import CompensationPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract actual compensation patterns
    try:
        tree = ast.parse(code)
        detector = CompensationDetector()
        detector.visit(tree)

        if detector.compensation_patterns:
            # Generate smart transformation based on detected patterns
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for pattern in detector.compensation_patterns:
                func_name = pattern["name"]
                cleanup_actions = pattern.get("cleanup_actions", [])
                is_async = pattern.get("is_async", True)

                # Find the original function to extract its body
                func_node = pattern.get("node")
                forward_body = ""
                compensation_body = ""

                if func_node:
                    # Extract forward operations (try body)
                    for stmt in func_node.body:
                        if isinstance(stmt, ast.Try):
                            # Get try body as forward operations
                            forward_stmts = []
                            for try_stmt in stmt.body:
                                try:
                                    forward_stmts.append("    " + ast.unparse(try_stmt))
                                except Exception:
                                    pass
                            forward_body = (
                                "\n".join(forward_stmts)
                                if forward_stmts
                                else "    pass"
                            )

                            # Get except body (excluding raise) as compensation
                            for handler in stmt.handlers:
                                comp_stmts = []
                                for h_stmt in handler.body:
                                    if not isinstance(h_stmt, ast.Raise):
                                        try:
                                            comp_stmts.append(
                                                "    " + ast.unparse(h_stmt)
                                            )
                                        except Exception:
                                            pass
                                compensation_body = (
                                    "\n".join(comp_stmts) if comp_stmts else "    pass"
                                )
                                break

                if not forward_body:
                    forward_body = "    # Extract forward operations from original function\n    pass"
                if not compensation_body:
                    compensation_body = (
                        f"    # Cleanup actions: {', '.join(cleanup_actions)}\n    pass"
                    )

                async_kw = "async " if is_async else ""

                wrapper_parts.append(f'''
# Saga pattern for {func_name}
# Forward: executes the main business logic
# Compensation: automatically called on failure to rollback

{async_kw}def {func_name}_forward(data: dict, context: WorkflowContext):
    """Forward operation - extracted from {func_name}."""
{forward_body}


{async_kw}def {func_name}_compensation(data: dict, context: WorkflowContext):
    """Compensation operation - rollback logic from {func_name}."""
{compensation_body}


# Create CompensationPrimitive workflow
{func_name}_saga = CompensationPrimitive(
    forward={func_name}_forward,
    compensation={func_name}_compensation,
)

# Usage:
# context = WorkflowContext(workflow_id="saga-{func_name}")
# result = await {func_name}_saga.execute(data, context)
''')

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template approach
    func_names = [t["name"] for t in targets]
    lines.append("")
    lines.append("# --- TTA.dev Transformation ---")
    lines.append(f"# TODO: Extract forward and compensation logic from {func_names[0]}")
    lines.append("# See CompensationPrimitive documentation for saga pattern")

    return "\n".join(lines)


def _generate_timeout_transformation(code: str, targets: list[dict], info: dict) -> str:
    """Generate smart TimeoutPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import TimeoutDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives.recovery import TimeoutPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract actual timeout patterns
    try:
        tree = ast.parse(code)
        detector = TimeoutDetector()
        detector.visit(tree)

        if detector.timeout_calls:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for call_info in detector.timeout_calls:
                func_name = call_info.get("function", "operation")
                timeout = call_info.get("timeout", 30)

                wrapper_parts.append(f"""
# Extracted from asyncio.wait_for - actual timeout: {timeout}s
{func_name}_with_timeout = TimeoutPrimitive(
    primitive={func_name},
    timeout_seconds={timeout},
)

# Usage:
# context = WorkflowContext(workflow_id="timeout-{func_name}")
# result = await {func_name}_with_timeout.execute(data, context)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "TimeoutPrimitive"
    )


def _generate_fallback_transformation(
    code: str, targets: list[dict], info: dict
) -> str:
    """Generate smart FallbackPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import FallbackDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives.recovery import FallbackPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract actual fallback patterns
    try:
        tree = ast.parse(code)
        detector = FallbackDetector()
        detector.visit(tree)

        if detector.fallback_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for pattern in detector.fallback_patterns:
                primary = pattern.get("primary", "primary_func")
                fallback = pattern.get("fallback", "fallback_func")
                func_name = pattern.get(
                    "function", targets[0]["name"] if targets else "operation"
                )

                wrapper_parts.append(f"""
# Extracted from try/except pattern
# Primary: {primary}, Fallback: {fallback}
{func_name}_resilient = FallbackPrimitive(
    primary={primary},
    fallbacks=[{fallback}],
)

# Usage:
# context = WorkflowContext(workflow_id="fallback-{func_name}")
# result = await {func_name}_resilient.execute(data, context)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "FallbackPrimitive"
    )


def _generate_router_transformation(code: str, targets: list[dict], info: dict) -> str:
    """Generate smart RouterPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import RouterPatternDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives.core import RouterPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract actual router patterns
    try:
        tree = ast.parse(code)
        detector = RouterPatternDetector()
        detector.visit(tree)

        if detector.router_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for pattern in detector.router_patterns:
                routes = pattern.get("routes", {})
                variable = pattern.get("variable", "provider")
                func_name = pattern.get(
                    "function", targets[0]["name"] if targets else "router"
                )

                if routes:
                    routes_str = ",\n        ".join(
                        [f'"{k}": {v}' for k, v in routes.items()]
                    )
                    default_key = list(routes.keys())[0] if routes else "default"

                    wrapper_parts.append(f"""
# Extracted from if/elif chain - routes: {list(routes.keys())}
{func_name}_router = RouterPrimitive(
    routes={{
        {routes_str}
    }},
    router_fn=lambda data, ctx: data.get("{variable}", "{default_key}"),
    default="{default_key}"
)

# Usage:
# context = WorkflowContext(workflow_id="router-{func_name}")
# result = await {func_name}_router.execute({{"{variable}": "value", ...}}, context)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "RouterPrimitive"
    )


def _generate_circuit_breaker_transformation(
    code: str, targets: list[dict], info: dict
) -> str:
    """Generate smart CircuitBreakerPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import CircuitBreakerDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives.recovery import CircuitBreakerPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract circuit breaker patterns
    try:
        tree = ast.parse(code)
        detector = CircuitBreakerDetector()
        detector.visit(tree)

        if detector.circuit_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for pattern in detector.circuit_patterns:
                func_name = pattern.get("name", "operation")
                exception_count = pattern.get("exception_count", 2)

                # Calculate reasonable thresholds based on exception count
                failure_threshold = max(3, exception_count + 2)

                wrapper_parts.append(f"""
# Extracted from function with {exception_count} exception handlers
# Circuit breaker protects against cascading failures
{func_name}_protected = CircuitBreakerPrimitive(
    primitive={func_name},
    failure_threshold={failure_threshold},      # Open after {failure_threshold} failures
    recovery_timeout=60,       # Wait 60s before half-open
    expected_successes=2,      # 2 successes to close
)

# Usage:
# context = WorkflowContext(workflow_id="circuit-{func_name}")
# result = await {func_name}_protected.execute(data, context)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "CircuitBreakerPrimitive"
    )


def _generate_memory_transformation(code: str, targets: list[dict], info: dict) -> str:
    """Generate smart MemoryPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import MemoryDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives.performance import MemoryPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract memory patterns
    try:
        tree = ast.parse(code)
        detector = MemoryDetector()
        detector.visit(tree)

        if detector.memory_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            # Group by pattern type
            message_appends = [
                p for p in detector.memory_patterns if p["type"] == "message_append"
            ]
            deque_patterns = [
                p for p in detector.memory_patterns if p["type"] == "deque_history"
            ]
            dict_patterns = [
                p for p in detector.memory_patterns if p["type"] == "dict_storage"
            ]

            if message_appends:
                var = message_appends[0]["variable"]
                wrapper_parts.append(f"""
# Extracted conversation history pattern from '{var}'
# Replace manual list with MemoryPrimitive for:
# - Automatic LRU eviction (prevent memory bloat)
# - Keyword search across history
# - Optional Redis persistence for scaling

# Create memory store (works immediately, no setup required)
conversation_memory = MemoryPrimitive(max_size=100)

async def add_message(role: str, content: str, session_id: str):
    \"\"\"Add a message to conversation memory.\"\"\"
    key = f"{{session_id}}:{{role}}:{{content[:20]}}"
    await conversation_memory.add(key, {{"role": role, "content": content}})

async def get_history(query: str = None) -> list:
    \"\"\"Retrieve conversation history, optionally filtered by keyword.\"\"\"
    if query:
        return await conversation_memory.search(query)
    return await conversation_memory.get_all()

# Usage:
# await add_message("user", "What is TTA.dev?", "session-123")
# await add_message("assistant", "TTA.dev provides...", "session-123")
# history = await get_history("TTA.dev")
""")

            if deque_patterns:
                pattern = deque_patterns[0]
                var = pattern["variable"]
                maxlen = pattern.get("maxlen", 100)
                wrapper_parts.append(f"""
# Extracted bounded history from deque '{var}' (maxlen={maxlen})
# Replace with MemoryPrimitive for same behavior + search + persistence

{var}_memory = MemoryPrimitive(max_size={maxlen})

# Usage (same API, enhanced capabilities):
# await {var}_memory.add(key, value)
# result = await {var}_memory.get(key)
# results = await {var}_memory.search("keyword")
""")

            if dict_patterns:
                var = dict_patterns[0]["variable"]
                wrapper_parts.append(f"""
# Extracted context storage from dict '{var}'
# Replace with MemoryPrimitive for:
# - LRU eviction (bounded memory)
# - Async-safe operations
# - Optional persistence

{var} = MemoryPrimitive(max_size=1000)

# Usage:
# await {var}.add("key", {{"context": "data"}})
# data = await {var}.get("key")
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "MemoryPrimitive"
    )


def _generate_delegation_transformation(
    code: str, targets: list[dict], info: dict
) -> str:
    """Generate smart DelegationPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import DelegationDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path",
        "from tta_dev_primitives.orchestration import DelegationPrimitive",
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract delegation patterns
    try:
        tree = ast.parse(code)
        detector = DelegationDetector()
        detector.visit(tree)

        if detector.delegation_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            # Group by pattern type
            model_routing = [
                p for p in detector.delegation_patterns if p["type"] == "model_routing"
            ]
            agent_dispatch = [
                p for p in detector.delegation_patterns if p["type"] == "agent_dispatch"
            ]
            executor_dispatch = [
                p
                for p in detector.delegation_patterns
                if p["type"] == "executor_dispatch"
            ]

            if model_routing:
                pattern = model_routing[0]
                var = pattern["variable"]
                models = pattern["models"]
                func_name = pattern.get("parent_function", "route_task")
                models_str = ", ".join(f'"{m}"' for m in models)

                wrapper_parts.append(f"""
# Extracted model routing from if/elif chain on '{var}'
# Detected models: {models_str}
#
# DelegationPrimitive enables orchestrator→executor pattern:
# - High-quality model plans/validates (small token usage)
# - Cost-effective models execute (bulk work)
# - 80%+ cost reduction while maintaining quality

from tta_dev_primitives.orchestration import DelegationPrimitive, DelegationRequest

# Register executor models
delegation = DelegationPrimitive()
# delegation.register_executor("gpt-4", gpt4_primitive)
# delegation.register_executor("claude", claude_primitive)
# delegation.register_executor("gemini", gemini_primitive)

async def {func_name}_delegated(task: str, model: str):
    \"\"\"Delegate task to appropriate model.\"\"\"
    request = DelegationRequest(
        task_description=task,
        executor_model=model,
        messages=[{{"role": "user", "content": task}}],
    )
    context = WorkflowContext(workflow_id="delegation-{func_name}")
    return await delegation.execute(request, context)

# Usage:
# result = await {func_name}_delegated("Summarize document", "{models[0] if models else "gpt-4"}")
""")

            if agent_dispatch:
                pattern = agent_dispatch[0]
                container = pattern["container"]
                method = pattern["method"]
                func_name = pattern.get("parent_function", "dispatch")

                wrapper_parts.append(f"""
# Extracted agent dispatch pattern: {container}[role].{method}()
# DelegationPrimitive provides structured orchestrator→executor flow

# Create delegation with registered executors
delegation = DelegationPrimitive()

# Register agents as executors
# for role, agent in {container}.items():
#     delegation.register_executor(role, agent)

async def {func_name}_to_agent(task: str, role: str):
    \"\"\"Delegate task to specific agent role.\"\"\"
    request = DelegationRequest(
        task_description=task,
        executor_model=role,
        messages=[{{"role": "user", "content": task}}],
    )
    context = WorkflowContext(workflow_id="agent-delegation")
    return await delegation.execute(request, context)
""")

            if executor_dispatch:
                pattern = executor_dispatch[0]
                executor = pattern["executor"]
                method = pattern["method"]

                wrapper_parts.append(f"""
# Extracted executor pattern: {executor}.{method}()
# Wrap with DelegationPrimitive for observability and cost tracking

delegation = DelegationPrimitive()
# delegation.register_executor("default", {executor})

# Usage with full observability:
# request = DelegationRequest(task_description="...", executor_model="default", ...)
# result = await delegation.execute(request, context)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "DelegationPrimitive"
    )


def _generate_sequential_transformation(
    code: str, targets: list[dict], info: dict
) -> str:
    """Generate smart SequentialPrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import SequentialDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives import SequentialPrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(import_idx + 2, "")

    # Parse code to extract sequential patterns
    try:
        tree = ast.parse(code)
        detector = SequentialDetector()
        detector.visit(tree)

        if detector.sequential_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for pattern in detector.sequential_patterns:
                steps = pattern["steps"]
                step_count = pattern["step_count"]
                func_name = pattern.get("parent_function", "pipeline")
                is_async = pattern.get("is_async", True)
                pattern_type = pattern["type"]

                steps_str = ", ".join(steps)
                async_kw = "async " if is_async else ""
                await_kw = "await " if is_async else ""

                if pattern_type == "nested_calls":
                    wrapper_parts.append(f"""
# Extracted nested call chain: {steps_str}
# {step_count} steps detected → Use SequentialPrimitive for:
# - Step-level observability (traces per step)
# - Error handling with context
# - Easy debugging and profiling

# Convert each step to a primitive
# step1 = WrapperPrimitive({steps[0]})
# step2 = WrapperPrimitive({steps[1] if len(steps) > 1 else "step2"})
# ...

# Compose with >> operator
{func_name}_workflow = {" >> ".join(steps[:3])}{"..." if len(steps) > 3 else ""}

# Or explicit composition:
# {func_name}_workflow = SequentialPrimitive([{steps_str}])

{async_kw}def {func_name}_sequential(data: dict):
    \"\"\"Execute {step_count}-step pipeline with full observability.\"\"\"
    context = WorkflowContext(workflow_id="{func_name}-pipeline")
    return {await_kw}{func_name}_workflow.execute(data, context)

# Usage:
# result = {await_kw}{func_name}_sequential({{"input": data}})
""")

                elif pattern_type == "assignment_chain":
                    wrapper_parts.append(f"""
# Extracted assignment chain: {steps_str}
# {step_count} sequential steps → Use SequentialPrimitive for:
# - Automatic output→input chaining
# - Step-level metrics and traces
# - Checkpoint/resume capability

# Wrap each step as a primitive
class Step1Primitive(WorkflowPrimitive[dict, dict]):
    {async_kw}def execute(self, data: dict, ctx: WorkflowContext) -> dict:
        return {await_kw}{steps[0]}(data)

# Compose pipeline
{func_name}_pipeline = SequentialPrimitive([
    # {steps[0]},
    # {steps[1] if len(steps) > 1 else "step2"},
    # ...add wrapped primitives
])

# Or use >> operator for cleaner syntax:
# {func_name}_pipeline = step1 >> step2 >> step3

{async_kw}def {func_name}_workflow(input_data):
    \"\"\"Execute {step_count}-step sequential workflow.\"\"\"
    context = WorkflowContext(workflow_id="{func_name}")
    return {await_kw}{func_name}_pipeline.execute(input_data, context)

# Usage:
# result = {await_kw}{func_name}_workflow(initial_data)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "SequentialPrimitive"
    )


def _generate_adaptive_transformation(
    code: str, targets: list[dict], info: dict
) -> str:
    """Generate smart AdaptivePrimitive transformation using AST analysis."""
    import ast

    from tta_dev_primitives.analysis.transformer import AdaptiveDetector

    lines = code.split("\n")

    # Add imports
    import_idx = _find_import_index(lines)
    import_path = info.get(
        "import_path", "from tta_dev_primitives.adaptive import AdaptivePrimitive"
    )
    if import_path not in code:
        lines.insert(import_idx, import_path)
        lines.insert(import_idx + 1, "from tta_dev_primitives import WorkflowContext")
        lines.insert(
            import_idx + 2, "from tta_dev_primitives.adaptive import LearningMode"
        )
        lines.insert(import_idx + 3, "")

    # Parse code to extract adaptive patterns
    try:
        tree = ast.parse(code)
        detector = AdaptiveDetector()
        detector.visit(tree)

        if detector.adaptive_patterns:
            wrapper_parts = ["\n# --- TTA.dev Transformation ---\n"]

            for pattern in detector.adaptive_patterns:
                pattern_type = pattern["type"]
                func_name = pattern.get("parent_function", "adaptive_operation")
                is_async = pattern.get("is_async", True)
                async_kw = "async " if is_async else ""
                await_kw = "await " if is_async else ""

                if pattern_type == "metric_based_adjustment":
                    counter_vars = pattern.get("counter_vars", [])
                    counters_str = ", ".join(counter_vars)

                    wrapper_parts.append(f"""
# Extracted metric-based adjustment pattern
# Detected counters: {counters_str}
#
# AdaptivePrimitive provides:
# - Automatic strategy learning from execution patterns
# - Safe validation before adopting new strategies
# - Context-aware optimization (prod vs staging)
# - Logseq integration for strategy persistence

from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LearningStrategy,
    LogseqStrategyIntegration,
)

# Setup Logseq integration for strategy persistence (optional)
logseq = LogseqStrategyIntegration("{func_name}")

# Create adaptive retry with automatic learning
adaptive_{func_name} = AdaptiveRetryPrimitive(
    target_primitive=your_operation,  # Wrap your existing operation
    logseq_integration=logseq,
    enable_auto_persistence=True,
    learning_mode=LearningMode.ACTIVE,  # DISABLED, OBSERVE, VALIDATE, ACTIVE
    min_observations_before_learning=10,
)

{async_kw}def {func_name}_adaptive(data: dict):
    \"\"\"Execute with automatic strategy optimization.\"\"\"
    context = WorkflowContext(workflow_id="{func_name}-adaptive")
    return {await_kw}adaptive_{func_name}.execute(data, context)

# Check learned strategies:
# for name, strategy in adaptive_{func_name}.strategies.items():
#     print(f"{{name}}: {{strategy.metrics.success_rate:.1%}} success")
""")

                elif pattern_type == "strategy_config":
                    var = pattern.get("variable", "strategies")

                    wrapper_parts.append(f"""
# Extracted strategy configuration: {var}
#
# AdaptivePrimitive can learn optimal strategy selection:
# - Tracks success/failure per strategy
# - Adapts selection based on context
# - Validates improvements before adoption

from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningStrategy

# Define baseline strategies from your config
baseline = LearningStrategy(
    name="default",
    description="Initial strategy",
    parameters={var}.get("default", {{}})  # Extract from your config
)

# Create adaptive primitive that learns from execution
class Adaptive{var.title()}Primitive(AdaptivePrimitive[dict, dict]):
    {async_kw}def _execute_with_strategy(
        self, strategy: LearningStrategy, data: dict, ctx: WorkflowContext
    ) -> dict:
        # Use strategy.parameters to configure execution
        params = strategy.parameters
        return {await_kw}your_operation(data, **params)

    {async_kw}def _consider_new_strategy(
        self, data: dict, ctx: WorkflowContext, metrics
    ) -> LearningStrategy | None:
        # Return new strategy if current underperforming
        if metrics.success_rate < 0.8:
            return LearningStrategy(name="optimized", parameters={{...}})
        return None

# Usage:
# adaptive = Adaptive{var.title()}Primitive(baseline_strategy=baseline)
# result = {await_kw}adaptive.execute(data, context)
""")

            lines.append("".join(wrapper_parts))
            return "\n".join(lines)

    except Exception:
        pass

    # Fallback to template
    return _fallback_template_transformation(
        code, lines, targets, info, "AdaptivePrimitive"
    )


def _find_import_index(lines: list[str]) -> int:
    """Find the index where imports should be inserted."""
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_idx = i + 1
        elif line.strip() and not line.startswith("#") and import_idx > 0:
            break
    return import_idx


def _fallback_template_transformation(
    code: str, lines: list[str], targets: list[dict], info: dict, primitive: str
) -> str:
    """Fallback to simple template-based transformation."""
    [t["name"] for t in targets]
    any(t["is_async"] for t in targets)
    wrapper_code = _generate_wrapper_code(primitive, targets, info)
    lines.append("")
    lines.append("# --- TTA.dev Transformation ---")
    lines.append(wrapper_code)
    return "\n".join(lines)


def _print_diff(original: str, transformed: str, filename: str) -> None:
    """Print a unified diff between original and transformed code."""
    import difflib

    original_lines = original.splitlines(keepends=True)
    transformed_lines = transformed.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        transformed_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )

    diff_text = "".join(diff)
    if diff_text:
        console.print(Syntax(diff_text, "diff", theme="monokai"))
    else:
        console.print("[yellow]No changes needed[/yellow]")


@app.command()
def benchmark(
    ctx: typer.Context,
    difficulty: str = typer.Option(
        "all",
        "--difficulty",
        "-d",
        help="Filter by difficulty: easy, medium, hard, all",
    ),
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: table, json",
    ),
    iterations: int = typer.Option(
        None,
        "--iterations",
        "-i",
        help="Max iterations per task (default from config)",
    ),
) -> None:
    """Run ACE learning benchmarks.

    Executes benchmark tasks to test self-learning code generation
    using ACE + E2B execution environments.

    Configuration values from .ttadevrc.yaml are used as defaults.

    Examples:
        tta-dev benchmark                       # Run all benchmarks
        tta-dev benchmark --difficulty easy     # Run only easy tasks
        tta-dev benchmark --output json         # Output as JSON
    """
    import asyncio

    # Get config
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options from config
    iterations = iterations if iterations is not None else config.benchmark.iterations

    try:
        from tta_dev_primitives.ace import BenchmarkSuite, SelfLearningCodePrimitive
        from tta_dev_primitives.core.base import WorkflowContext
    except ImportError as e:
        console.print(f"[red]ACE module not available: {e}[/red]")
        raise typer.Exit(1) from e

    console.print("[bold]🧪 ACE Learning Benchmarks[/bold]\n")

    suite = BenchmarkSuite()

    # Filter tasks by difficulty
    if difficulty != "all":
        tasks = [t for t in suite.tasks if t.difficulty.value == difficulty]
    else:
        tasks = suite.tasks

    if not tasks:
        console.print(f"[yellow]No tasks found for difficulty: {difficulty}[/yellow]")
        raise typer.Exit(1)

    console.print(f"Running {len(tasks)} benchmark tasks...")
    console.print(f"Difficulty filter: {difficulty}")
    console.print(f"Max iterations: {iterations}\n")

    async def run_benchmarks() -> list[dict]:
        try:
            learner = SelfLearningCodePrimitive()
        except ValueError as e:
            console.print(f"[red]E2B API key required: {e}[/red]")
            console.print("[dim]Set E2B_API_KEY environment variable[/dim]")
            raise typer.Exit(1) from e

        results = []
        context = WorkflowContext(correlation_id="benchmark-run")

        for task in tasks:
            console.print(f"  Running: [cyan]{task.name}[/cyan]...", end=" ")
            try:
                result = await suite.run_benchmark(task, learner, context)
                results.append(
                    {
                        "task_id": result.task_id,
                        "task_name": result.task_name,
                        "difficulty": task.difficulty.value,
                        "success": result.success,
                        "iterations": result.iterations_used,
                        "time": f"{result.execution_time:.2f}s",
                        "strategies_learned": result.strategies_learned,
                        "validation_passed": result.validation_passed,
                    }
                )
                status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                console.print(status)
            except Exception as e:
                results.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "difficulty": task.difficulty.value,
                        "success": False,
                        "error": str(e),
                    }
                )
                console.print(f"[red]✗ Error: {e}[/red]")

        return results

    results = asyncio.run(run_benchmarks())

    if output == "json":
        print(json.dumps(results, indent=2))
        return

    # Display table
    console.print()
    table = Table(title="Benchmark Results", show_header=True, header_style="bold cyan")
    table.add_column("Task", style="cyan")
    table.add_column("Difficulty", justify="center")
    table.add_column("Success", justify="center")
    table.add_column("Time", justify="right")
    table.add_column("Strategies", justify="center")

    for r in results:
        success_str = "[green]✓[/green]" if r.get("success") else "[red]✗[/red]"
        table.add_row(
            r["task_name"],
            r["difficulty"],
            success_str,
            r.get("time", "N/A"),
            str(r.get("strategies_learned", 0)),
        )

    console.print(table)

    # Summary
    passed = sum(1 for r in results if r.get("success"))
    console.print(f"\n[bold]Summary:[/bold] {passed}/{len(results)} passed")


@app.command(name="ab-test")
def ab_test(
    ctx: typer.Context,
    code_file: Path = typer.Argument(
        ...,
        help="Python file to A/B test with different primitives",
        exists=True,
        readable=True,
    ),
    variants: str = typer.Option(
        "retry,circuit-breaker",
        "--variants",
        "-v",
        help="Comma-separated primitive variants to test",
    ),
    runs: int = typer.Option(
        None,
        "--runs",
        "-r",
        help="Number of runs per variant (default from config)",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table, json (default from config)",
    ),
) -> None:
    """A/B test code with different TTA.dev primitives.

    Executes the given code with different primitive wrappers using
    E2B sandboxes and compares performance metrics.

    Configuration values from .ttadevrc.yaml are used as defaults.

    Examples:
        tta-dev ab-test api_client.py
        tta-dev ab-test fetch.py --variants "retry,fallback,timeout"
        tta-dev ab-test workflow.py --runs 10 --output json
    """
    import asyncio
    import statistics

    # Get config
    config = ctx.obj.get("config") if ctx.obj else None
    if config is None:
        config = _get_config()

    # Resolve options from config
    runs = runs if runs is not None else config.benchmark.iterations
    output = output if output is not None else config.analysis.output_format

    console.print("[bold]🔬 A/B Testing with E2B Execution[/bold]\n")

    try:
        code = code_file.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1) from e

    variant_list = [v.strip() for v in variants.split(",")]
    console.print(f"File: [cyan]{code_file}[/cyan]")
    console.print(f"Variants: {', '.join(variant_list)}")
    console.print(f"Runs per variant: {runs}\n")

    # First analyze the code
    report = analyzer.analyze(code, file_path=str(code_file))
    console.print(
        f"Detected patterns: {', '.join(report.analysis.detected_patterns) or 'none'}"
    )
    console.print()

    async def run_ab_tests() -> dict:
        try:
            from tta_dev_primitives.core.base import WorkflowContext
            from tta_dev_primitives.integrations.e2b_primitive import (
                CodeExecutionPrimitive,
            )
        except ImportError as e:
            console.print(f"[red]E2B integration not available: {e}[/red]")
            raise typer.Exit(1) from e

        try:
            executor = CodeExecutionPrimitive()
        except ValueError as e:
            console.print(f"[red]E2B API key required: {e}[/red]")
            console.print("[dim]Set E2B_API_KEY environment variable[/dim]")
            raise typer.Exit(1) from e

        results = {}

        for variant in variant_list:
            console.print(f"Testing variant: [cyan]{variant}[/cyan]...")
            times = []
            successes = 0

            # Get template for this variant
            template_info = analyzer.get_primitive_info(_variant_to_primitive(variant))
            wrapper_code = _generate_wrapper(code, variant, template_info)

            context = WorkflowContext(correlation_id=f"ab-test-{variant}")

            for i in range(runs):
                try:
                    result = await executor.execute(
                        {"code": wrapper_code, "language": "python", "timeout": 30},
                        context,
                    )
                    times.append(result["execution_time"])
                    if result["success"]:
                        successes += 1
                except Exception as e:
                    console.print(f"  [dim]Run {i + 1} failed: {e}[/dim]")

            results[variant] = {
                "runs": runs,
                "successes": successes,
                "success_rate": successes / runs if runs > 0 else 0,
                "avg_time": statistics.mean(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            }

        return results

    results = asyncio.run(run_ab_tests())

    if output == "json":
        print(json.dumps(results, indent=2))
        return

    # Display table
    table = Table(title="A/B Test Results", show_header=True, header_style="bold cyan")
    table.add_column("Variant", style="cyan")
    table.add_column("Success Rate", justify="center")
    table.add_column("Avg Time", justify="right")
    table.add_column("Min/Max", justify="right")
    table.add_column("Std Dev", justify="right")

    for variant, metrics in results.items():
        success_pct = f"{metrics['success_rate']:.0%}"
        avg_time = f"{metrics['avg_time'] * 1000:.1f}ms"
        min_max = f"{metrics['min_time'] * 1000:.1f}/{metrics['max_time'] * 1000:.1f}ms"
        std_dev = f"{metrics['std_dev'] * 1000:.1f}ms"

        table.add_row(variant, success_pct, avg_time, min_max, std_dev)

    console.print(table)

    # Winner
    if results:
        best = min(
            results.items(),
            key=lambda x: x[1]["avg_time"]
            if x[1]["success_rate"] > 0.5
            else float("inf"),
        )
        console.print(f"\n[bold green]🏆 Recommended: {best[0]}[/bold green]")


def _variant_to_primitive(variant: str) -> str:
    """Map variant name to primitive name."""
    mapping = {
        "retry": "RetryPrimitive",
        "timeout": "TimeoutPrimitive",
        "cache": "CachePrimitive",
        "fallback": "FallbackPrimitive",
        "circuit-breaker": "CircuitBreakerPrimitive",
        "parallel": "ParallelPrimitive",
        "sequential": "SequentialPrimitive",
    }
    return mapping.get(variant.lower(), "RetryPrimitive")


def _generate_wrapper(code: str, variant: str, template_info: dict | None) -> str:
    """Generate wrapper code for A/B testing.

    Creates a test harness that:
    1. Includes the original code
    2. Detects callable main/test functions
    3. Wraps execution with timing and error handling
    """
    import re

    # Find potential entry points in the code
    main_patterns = [
        r"def\s+(main)\s*\(",
        r"def\s+(run)\s*\(",
        r"def\s+(execute)\s*\(",
        r"def\s+(test_\w+)\s*\(",
        r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:",
    ]

    entry_points = []
    for pattern in main_patterns:
        matches = re.findall(pattern, code)
        entry_points.extend(matches)

    # Generate appropriate call
    if "main" in entry_points:
        call_code = "main()"
    elif "run" in entry_points:
        call_code = "run()"
    elif "execute" in entry_points:
        call_code = "execute()"
    elif any(ep.startswith("test_") for ep in entry_points):
        test_fn = next(ep for ep in entry_points if ep.startswith("test_"))
        call_code = f"{test_fn}()"
    else:
        # No entry point found - just import and measure module load time
        call_code = "pass  # No entry point found - measuring import time"

    # Simple test code that demonstrates the concept
    # Note: Don't use sys.exit() as E2B treats exit codes as errors
    wrapper = f"""
import time

# Variant being tested: {variant}
# Primitive: {_variant_to_primitive(variant)}

# Measure total execution time
_start = time.perf_counter()

try:
    # Original code
{_indent_code(code, 4)}

    # Try to call entry point
    {call_code}

    _elapsed = time.perf_counter() - _start
    print(f"SUCCESS: Execution completed in {{_elapsed:.4f}}s")

except Exception as e:
    _elapsed = time.perf_counter() - _start
    print(f"ERROR: {{type(e).__name__}}: {{e}}")
    print(f"Execution time before error: {{_elapsed:.4f}}s")
    raise  # Re-raise to mark as error in E2B
"""
    return wrapper


def _indent_code(code: str, spaces: int) -> str:
    """Indent code by specified number of spaces."""
    indent = " " * spaces
    lines = code.split("\n")
    return "\n".join(indent + line if line.strip() else line for line in lines)


# Config subcommand group
config_app = typer.Typer(
    name="config",
    help="Manage TTA.dev configuration files.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@config_app.command(name="init")
def config_init(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to create config file (default: .ttadevrc.yaml)",
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        "-f",
        help="Output format: yaml, json, toml",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing config file",
    ),
) -> None:
    """Initialize a new configuration file.

    Creates a .ttadevrc.yaml file with default settings.

    Examples:
        tta-dev config init
        tta-dev config init --format json
        tta-dev config init --path ./my-config.yaml
    """
    # Determine output path
    if path is None:
        ext_map = {"yaml": ".yaml", "json": ".json", "toml": ".toml"}
        ext = ext_map.get(format, ".yaml")
        path = Path(f".ttadevrc{ext}")

    # Check if file exists
    if path.exists() and not force:
        console.print(f"[yellow]Config file already exists: {path}[/yellow]")
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    # Generate and save config
    try:
        config = TTAConfig()
        save_config(config, path, format=format)
        console.print(f"[green]✓ Created config file: {path}[/green]")
        console.print("\nYou can now customize the settings in this file.")
        console.print("The CLI will automatically load it when running commands.")
    except Exception as e:
        console.print(f"[red]Error creating config: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command(name="show")
def config_show(
    config_path: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (auto-detected if not specified)",
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        "-f",
        help="Output format: yaml, json",
    ),
) -> None:
    """Show current configuration.

    Displays the merged configuration from config file and defaults.

    Examples:
        tta-dev config show
        tta-dev config show --format json
        tta-dev config show --config ./my-config.yaml
    """
    try:
        load_config(config_path)
        config_file = find_config_file()

        if config_file:
            console.print(f"[dim]Config loaded from: {config_file}[/dim]\n")
        else:
            console.print("[dim]No config file found, showing defaults[/dim]\n")

        output = generate_default_config(format=format)

        if format == "json":
            console.print(output)
        else:
            syntax = Syntax(output, "yaml", theme="monokai", line_numbers=False)
            console.print(syntax)

    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command(name="path")
def config_path() -> None:
    """Show path to current configuration file.

    Examples:
        tta-dev config path
    """
    config_file = find_config_file()

    if config_file:
        console.print(f"[green]{config_file}[/green]")
    else:
        console.print("[yellow]No configuration file found.[/yellow]")
        console.print("\nSearched locations:")
        console.print(
            "  • .ttadevrc.yaml / .ttadevrc.yml / .ttadevrc.toml / .ttadevrc.json"
        )
        console.print("  • pyproject.toml [tool.tta-dev]")
        console.print("  • Parent directories (up to root)")
        console.print("  • Home directory")
        console.print("\nRun 'tta-dev config init' to create a config file.")


@config_app.command(name="validate")
def config_validate(
    config_path: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file to validate",
    ),
) -> None:
    """Validate a configuration file.

    Checks for syntax errors and invalid values.

    Examples:
        tta-dev config validate
        tta-dev config validate --config ./my-config.yaml
    """
    try:
        if config_path:
            if not config_path.exists():
                console.print(f"[red]Config file not found: {config_path}[/red]")
                raise typer.Exit(1)
            config_file = config_path
        else:
            config_file = find_config_file()
            if not config_file:
                console.print("[yellow]No config file found to validate.[/yellow]")
                raise typer.Exit(0)

        # Try to load and validate
        config = load_config(config_file)

        console.print(f"[green]✓ Configuration is valid: {config_file}[/green]")
        console.print(f"\n  Version: {config.version}")
        console.print(f"  Min confidence: {config.analysis.min_confidence}")
        console.print(f"  Output format: {config.analysis.output_format}")
        console.print(f"  Auto-fix: {config.transform.auto_fix}")
        console.print(f"  Ignored patterns: {len(config.patterns.ignore)}")

    except ValueError as e:
        console.print("[red]✗ Invalid configuration:[/red]")
        console.print(f"  {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error validating config: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def version() -> None:
    """Show version information."""
    from tta_dev_primitives import __version__

    console.print(f"[bold]TTA.dev Primitives[/bold] v{__version__}")
    console.print(f"Analyzer version: {analyzer.VERSION}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
