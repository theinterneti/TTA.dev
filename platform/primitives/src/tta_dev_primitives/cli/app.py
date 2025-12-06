"""TTA.dev CLI Application.

Main Typer application with all CLI commands.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

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
) -> None:
    """Analyze code and suggest TTA.dev primitives.

    Analyzes the given file for patterns and recommends appropriate
    TTA.dev primitives with confidence scores and code templates.

    Examples:
        tta-dev analyze api_client.py
        tta-dev analyze app.py --output json
        tta-dev analyze workflow.py --min-confidence 0.5 --templates
    """
    try:
        code = file.read_text()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1) from e

    # Run analysis
    report = analyzer.analyze(
        code,
        file_path=str(file),
        min_confidence=min_confidence,
    )

    # Output based on format
    if output == "json":
        print(json.dumps(report.to_dict(), indent=2, default=str))
    elif output == "brief":
        _print_brief(report)
    else:
        _print_table(report, show_templates)


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


def _print_table(report: AnalysisReport, show_templates: bool = False) -> None:
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
            console.print(f"  • {issue}")

    # Show optimization opportunities
    if report.context.optimization_opportunities:
        console.print("\n[bold green]💡 Optimization Opportunities:[/bold green]")
        for opp in report.context.optimization_opportunities:
            console.print(f"  • {opp}")


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
