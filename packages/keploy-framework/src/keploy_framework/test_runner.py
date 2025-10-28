"""Test runner with validation and reporting."""

import asyncio
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class TestResults:
    """Results from a Keploy test run."""

    total: int
    passed: int
    failed: int
    pass_rate: float
    test_cases: list[dict[str, Any]]

    @property
    def is_success(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0


class KeployTestRunner:
    """Intelligent Keploy test runner with validation."""

    def __init__(
        self,
        api_url: str,
        keploy_dir: str | Path = "./keploy",
        timeout: int = 30,
        docker_image: str = "ghcr.io/keploy/keploy:latest",
    ) -> None:
        """Initialize test runner.

        Args:
            api_url: Base URL of API to test
            keploy_dir: Directory containing Keploy tests
            timeout: Test timeout in seconds
            docker_image: Keploy Docker image
        """
        self.api_url = api_url
        self.keploy_dir = Path(keploy_dir)
        self.timeout = timeout
        self.docker_image = docker_image

    async def run_all_tests(
        self,
        validate: bool = True,
        generate_report: bool = False,
    ) -> TestResults:
        """Run all Keploy tests.

        Args:
            validate: Validate test results
            generate_report: Generate HTML report

        Returns:
            Test results
        """
        console.print("[bold blue]🧪 Running Keploy tests...[/bold blue]")

        # Run Keploy test command
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network", "host",
            "-v", f"{self.keploy_dir.absolute()}:/keploy",
            self.docker_image,
            "test",
            "-c", self.api_url,
            "--delay", "5",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            # Parse results
            test_results = self._parse_results(result.stdout)

            if validate:
                self._validate_results(test_results)

            if generate_report:
                self._generate_report(test_results)

            return test_results

        except subprocess.TimeoutExpired:
            console.print(f"[bold red]❌ Tests timed out after {self.timeout}s[/bold red]")
            raise
        except Exception as e:
            console.print(f"[bold red]❌ Test execution failed: {e}[/bold red]")
            raise

    def _parse_results(self, output: str) -> TestResults:
        """Parse Keploy test output.

        Args:
            output: Raw test output

        Returns:
            Parsed results
        """
        # Parse output for pass/fail counts
        # This is a simplified parser - real implementation would be more robust
        lines = output.split("\n")
        total = 0
        passed = 0
        failed = 0
        test_cases = []

        for line in lines:
            if "test passed" in line.lower():
                passed += 1
                total += 1
                test_cases.append({"status": "passed", "name": line.split()[0]})
            elif "test failed" in line.lower():
                failed += 1
                total += 1
                test_cases.append({"status": "failed", "name": line.split()[0]})

        pass_rate = (passed / total * 100) if total > 0 else 0.0

        return TestResults(
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            test_cases=test_cases,
        )

    def _validate_results(self, results: TestResults) -> None:
        """Validate test results and print summary.

        Args:
            results: Test results to validate
        """
        table = Table(title="Test Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Tests", str(results.total))
        table.add_row("Passed", f"[green]{results.passed}[/green]")
        table.add_row("Failed", f"[red]{results.failed}[/red]")
        table.add_row("Pass Rate", f"{results.pass_rate:.1f}%")

        console.print(table)

        if results.is_success:
            console.print("[bold green]✅ All tests passed![/bold green]")
        else:
            console.print(
                f"[bold yellow]⚠️  {results.failed} test(s) failed[/bold yellow]"
            )

    def _generate_report(self, results: TestResults) -> None:
        """Generate HTML test report.

        Args:
            results: Test results
        """
        report_path = self.keploy_dir / "test-report.html"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Keploy Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>Keploy Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {results.total}</p>
        <p class="pass">Passed: {results.passed}</p>
        <p class="fail">Failed: {results.failed}</p>
        <p>Pass Rate: {results.pass_rate:.1f}%</p>
    </div>
    <h2>Test Cases</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
        </tr>
        {"".join(f'<tr><td>{tc["name"]}</td><td class="{tc["status"]}">{tc["status"]}</td></tr>' for tc in results.test_cases)}
    </table>
</body>
</html>
"""

        report_path.write_text(html)
        console.print(f"[bold green]📊 Report generated: {report_path}[/bold green]")
