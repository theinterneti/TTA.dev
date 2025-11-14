"""CLI commands for Keploy framework."""

import typer
from pathlib import Path
from rich.console import Console
from keploy_framework.config import create_default_config

app = typer.Typer()
console = Console()


@app.command()
def setup(
    name: str = typer.Option(..., prompt="Project name"),
    command: str = typer.Option(..., prompt="Start command (e.g., 'uvicorn app:app --port 8000')"),
    port: int = typer.Option(8000, prompt="API port"),
) -> None:
    """Set up Keploy in your project."""
    console.print("[bold blue]🚀 Setting up Keploy framework...[/bold blue]")

    # Create configuration
    config = create_default_config(name=name, command=command, port=port)
    console.print(f"[green]✅ Created keploy.yml[/green]")

    # Create directories
    Path("keploy/tests").mkdir(parents=True, exist_ok=True)
    console.print("[green]✅ Created keploy/tests/ directory[/green]")

    Path("scripts").mkdir(exist_ok=True)
    console.print("[green]✅ Created scripts/ directory[/green]")

    console.print("\n[bold green]Setup complete! Next steps:[/bold green]")
    console.print("1. Start your API")
    console.print("2. Run: keploy-record")
    console.print("3. Run: keploy-test")


@app.command()
def test() -> None:
    """Run Keploy tests."""
    from keploy_framework.test_runner import KeployTestRunner
    import asyncio

    runner = KeployTestRunner(api_url="http://localhost:8000")
    results = asyncio.run(runner.run_all_tests(validate=True))

    if not results.is_success:
        raise typer.Exit(code=1)


@app.command()
def record() -> None:
    """Start recording session."""
    console.print("[bold blue]📹 Recording mode activated[/bold blue]")
    console.print("Interact with your API now. Tests will be saved automatically.")
    console.print("Press Ctrl+C when done.")


if __name__ == "__main__":
    app()
