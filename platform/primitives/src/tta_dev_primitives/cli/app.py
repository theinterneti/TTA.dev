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
        console.print("\n[yellow]No recommendations found above the confidence threshold.[/yellow]")
        return

    # Recommendations table
    table = Table(title="Recommendations", show_header=True, header_style="bold cyan")
    table.add_column("Primitive", style="cyan", no_wrap=True)
    table.add_column("Confidence", justify="center", style="green")
    table.add_column("Reasoning", style="white")
    table.add_column("Related", style="dim")

    for rec in report.recommendations:
        related = ", ".join(rec.related_primitives[:2]) if rec.related_primitives else "-"
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
                    Syntax(rec.code_template, "python", theme="monokai", line_numbers=False)
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

    table = Table(title="TTA.dev Primitives", show_header=True, header_style="bold cyan")
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
        console.print(f"\n[bold]Related Primitives:[/bold] {', '.join(info['related_primitives'])}")

    # Templates
    templates = info.get("templates", {})
    if templates:
        console.print("\n[bold]Code Templates:[/bold]")

        if show_all_templates:
            for name, template in templates.items():
                console.print(f"\n[cyan]Template: {name}[/cyan]")
                console.print(Syntax(template, "python", theme="monokai", line_numbers=False))
        else:
            # Show just the basic template
            basic = templates.get("basic", list(templates.values())[0] if templates else "")
            if basic:
                console.print(Syntax(basic, "python", theme="monokai", line_numbers=False))
            console.print(f"\n[dim]Use --all to see all {len(templates)} templates[/dim]")


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
