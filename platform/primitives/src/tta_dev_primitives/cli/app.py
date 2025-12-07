"""TTA.dev CLI Application.

Main Typer application with all CLI commands.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from tta_dev_primitives.analysis import TTAAnalyzer

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


@app.command()
def analyze(
    file: Path = typer.Argument(
        ...,
        help="File to analyze for primitive recommendations",
        exists=True,
        readable=True,
    ),
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: table, json, brief",
    ),
    min_confidence: float = typer.Option(
        0.3,
        "--min-confidence",
        "-c",
        help="Minimum confidence threshold (0.0 to 1.0)",
    ),
    show_templates: bool = typer.Option(
        False,
        "--templates",
        "-t",
        help="Show code templates for recommendations",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress debug logs (cleaner output for agents)",
    ),
    show_lines: bool = typer.Option(
        False,
        "--lines",
        "-l",
        help="Show line numbers for detected patterns",
    ),
    suggest_diff: bool = typer.Option(
        False,
        "--suggest-diff",
        "-d",
        help="Show suggested code transformations as diffs",
    ),
) -> None:
    """Analyze code and suggest TTA.dev primitives.

    Analyzes the given file for patterns and recommends appropriate
    TTA.dev primitives with confidence scores and code templates.

    Examples:
        tta-dev analyze api_client.py
        tta-dev analyze app.py --output json
        tta-dev analyze workflow.py --min-confidence 0.5 --templates
        tta-dev analyze api.py --quiet --suggest-diff  # Agent-friendly
    """
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
    }

    api_patterns = re.compile(r"(requests\.|httpx\.|aiohttp|\.get\(|\.post\(|fetch\()")
    async_patterns = re.compile(r"(async def|await\s)")
    error_patterns = re.compile(r"(try:|except\s|raise\s)")
    llm_patterns = re.compile(
        r"(openai|anthropic|chat.*completion|llm|gpt|claude)", re.IGNORECASE
    )
    for_patterns = re.compile(r"^\s*for\s+\w+\s+in\s+")

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

    return {k: v for k, v in result.items() if v}  # Only return non-empty


def _print_suggested_diffs(
    code: str,
    file_path: str,
    report: AnalysisReport,
    line_info: dict[str, list[int]],
) -> None:
    """Print suggested code transformations."""
    console.print("\n[bold blue]📝 Suggested Transformations:[/bold blue]")

    # Get top recommendation
    top_rec = report.recommendations[0] if report.recommendations else None
    if not top_rec:
        return

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
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: table, json",
    ),
) -> None:
    """List all available TTA.dev primitives.

    Shows all primitives with their descriptions and use cases.

    Examples:
        tta-dev primitives
        tta-dev primitives --output json
    """
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
    primitive: str = typer.Argument(
        ...,
        help="Name of the primitive to get documentation for",
    ),
    show_all_templates: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all available templates",
    ),
) -> None:
    """Show documentation for a specific primitive.

    Displays detailed information including description, use cases,
    related primitives, and code templates.

    Examples:
        tta-dev docs RetryPrimitive
        tta-dev docs CachePrimitive --all
    """
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
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport type: stdio, sse, http",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port for HTTP/SSE transport",
    ),
) -> None:
    """Start the TTA.dev MCP server.

    Starts a Model Context Protocol server that exposes TTA.dev
    primitives as tools for AI agents like Claude, Copilot, and Cline.

    Examples:
        tta-dev serve                    # stdio (default for Claude Desktop)
        tta-dev serve --transport sse    # SSE transport
        tta-dev serve --transport http --port 3000
    """
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
        False,
        "--quiet",
        "-q",
        help="Suppress informational output",
    ),
) -> None:
    """Transform code by wrapping with a TTA.dev primitive.

    Automatically detects functions that match the primitive's use case
    and generates transformed code.

    Examples:
        tta-dev transform api.py RetryPrimitive           # Wrap API calls with retry
        tta-dev transform api.py CachePrimitive -f fetch  # Cache specific function
        tta-dev transform api.py ParallelPrimitive -o diff  # Show as diff
    """
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
    }

    keywords = patterns.get(primitive, [])
    return any(kw in code_lower for kw in keywords)


def _generate_transformation(
    code: str, primitive: str, targets: list[dict], info: dict
) -> str:
    """Generate transformed code."""
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
    }

    return templates.get(primitive, f"# TODO: Wrap with {primitive}")


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
        3,
        "--iterations",
        "-i",
        help="Max iterations per task",
    ),
) -> None:
    """Run ACE learning benchmarks.

    Executes benchmark tasks to test self-learning code generation
    using ACE + E2B execution environments.

    Examples:
        tta-dev benchmark                       # Run all benchmarks
        tta-dev benchmark --difficulty easy     # Run only easy tasks
        tta-dev benchmark --output json         # Output as JSON
    """
    import asyncio

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
        5,
        "--runs",
        "-r",
        help="Number of runs per variant",
    ),
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: table, json",
    ),
) -> None:
    """A/B test code with different TTA.dev primitives.

    Executes the given code with different primitive wrappers using
    E2B sandboxes and compares performance metrics.

    Examples:
        tta-dev ab-test api_client.py
        tta-dev ab-test fetch.py --variants "retry,fallback,timeout"
        tta-dev ab-test workflow.py --runs 10 --output json
    """
    import asyncio
    import statistics

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
