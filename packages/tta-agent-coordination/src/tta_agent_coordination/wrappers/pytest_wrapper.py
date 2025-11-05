"""
PyTest CLI Wrapper - L4 Execution Layer.

Production-ready wrapper around pytest CLI with:
- Test execution with various configurations
- Result parsing and analysis
- Coverage collection
- Test failure extraction
- Report generation
- Observable execution
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Any

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


@dataclass
class PyTestConfig:
    """Configuration for PyTest CLI wrapper."""

    python_executable: str = "python"  # Python executable to use
    pytest_args: list[str] | None = None  # Default pytest arguments
    timeout: int = 300  # Test execution timeout in seconds
    coverage_enabled: bool = True  # Enable coverage collection by default


@dataclass
class PyTestOperation:
    """Input for PyTest operations."""

    operation: str  # "run_tests", "collect_tests", "parse_results", etc.
    params: dict[str, Any]  # Operation-specific parameters


@dataclass
class PyTestResult:
    """Output from PyTest operations."""

    success: bool
    operation: str
    data: dict[str, Any] | None = None
    error: str | None = None


class PyTestCLIWrapper(WorkflowPrimitive[PyTestOperation, PyTestResult]):
    """
    L4 Execution Wrapper for PyTest CLI.

    Provides atomic operations for test execution:
    - run_tests: Execute tests with configuration
    - collect_tests: Discover tests without running
    - parse_results: Parse pytest JSON output
    - get_coverage: Extract coverage data
    - analyze_failures: Extract failure details
    - generate_report: Create test report

    Features:
    - JSON output parsing
    - Coverage integration
    - Failure analysis
    - Timeout handling
    - Marker support
    - Fixture discovery
    """

    def __init__(self, config: PyTestConfig | None = None):
        """
        Initialize PyTest CLI wrapper.

        Args:
            config: PyTest configuration. If None, uses defaults.
        """
        super().__init__()
        self.config = config or PyTestConfig()

        # Verify pytest is available
        try:
            result = subprocess.run(
                [self.config.python_executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise FileNotFoundError("pytest not found or not installed")
        except Exception as e:
            raise FileNotFoundError(f"pytest not available: {e}") from e

    async def execute(
        self, input_data: PyTestOperation, context: WorkflowContext
    ) -> PyTestResult:
        """
        Execute PyTest operation.

        Args:
            input_data: Operation specification
            context: Workflow context for tracing

        Returns:
            PyTestResult with operation outcome
        """
        operation = input_data.operation
        params = input_data.params

        try:
            if operation == "run_tests":
                return await self._run_tests(params, context)
            elif operation == "collect_tests":
                return await self._collect_tests(params, context)
            elif operation == "parse_results":
                return await self._parse_results(params, context)
            elif operation == "get_coverage":
                return await self._get_coverage(params, context)
            elif operation == "analyze_failures":
                return await self._analyze_failures(params, context)
            elif operation == "generate_report":
                return await self._generate_report(params, context)
            else:
                return PyTestResult(
                    success=False,
                    operation=operation,
                    error=f"Unknown operation: {operation}",
                )
        except Exception as e:
            return PyTestResult(
                success=False, operation=operation, error=f"PyTest error: {e}"
            )

    async def _run_tests(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> PyTestResult:
        """
        Run pytest with specified configuration.

        Params:
            test_path: Path to tests (required)
            markers: Pytest markers to filter tests
            verbose: Verbose output level (0-2)
            coverage: Enable coverage collection
            json_output: Path for JSON results
            extra_args: Additional pytest arguments

        Returns:
            PyTestResult with test execution data
        """
        test_path = params.get("test_path")
        if not test_path:
            return PyTestResult(
                success=False,
                operation="run_tests",
                error="Missing required parameter: test_path",
            )

        # Build pytest command
        cmd = [self.config.python_executable, "-m", "pytest", test_path]

        # Add markers
        if markers := params.get("markers"):
            if isinstance(markers, list):
                for marker in markers:
                    cmd.extend(["-m", marker])
            else:
                cmd.extend(["-m", markers])

        # Add verbosity
        verbose = params.get("verbose", 1)
        cmd.append("-" + "v" * verbose)

        # Add coverage
        if params.get("coverage", self.config.coverage_enabled):
            cmd.extend(["--cov", "--cov-report=json", "--cov-report=term"])

        # Add JSON output
        json_output = params.get("json_output", "/tmp/pytest_results.json")
        cmd.extend(["--json-report", f"--json-report-file={json_output}"])

        # Add extra args
        if extra_args := params.get("extra_args"):
            cmd.extend(extra_args)

        # Execute pytest
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=params.get("cwd"),
            )

            # Parse results
            test_data = self._parse_pytest_output(result.stdout, result.stderr)
            test_data["exit_code"] = result.returncode
            test_data["command"] = " ".join(cmd)

            # Load JSON results if available
            if Path(json_output).exists():
                with open(json_output) as f:
                    test_data["json_results"] = json.load(f)

            return PyTestResult(
                success=result.returncode in [0, 1],  # 0=pass, 1=failures
                operation="run_tests",
                data=test_data,
            )
        except TimeoutExpired:
            return PyTestResult(
                success=False,
                operation="run_tests",
                error=f"Test execution timeout after {self.config.timeout}s",
            )
        except Exception as e:
            return PyTestResult(
                success=False, operation="run_tests", error=f"Execution error: {e}"
            )

    async def _collect_tests(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> PyTestResult:
        """
        Collect tests without running them.

        Params:
            test_path: Path to tests (required)
            markers: Filter by markers

        Returns:
            PyTestResult with collected test list
        """
        test_path = params.get("test_path")
        if not test_path:
            return PyTestResult(
                success=False,
                operation="collect_tests",
                error="Missing required parameter: test_path",
            )

        cmd = [
            self.config.python_executable,
            "-m",
            "pytest",
            test_path,
            "--collect-only",
            "-q",
        ]

        if markers := params.get("markers"):
            cmd.extend(["-m", markers])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=params.get("cwd")
            )

            # Parse collected tests
            tests = []
            for line in result.stdout.splitlines():
                if "::" in line and not line.startswith(" "):
                    tests.append(line.strip())

            return PyTestResult(
                success=True,
                operation="collect_tests",
                data={"count": len(tests), "tests": tests, "output": result.stdout},
            )
        except Exception as e:
            return PyTestResult(
                success=False,
                operation="collect_tests",
                error=f"Collection error: {e}",
            )

    async def _parse_results(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> PyTestResult:
        """
        Parse pytest JSON results.

        Params:
            json_path: Path to JSON results file (required)

        Returns:
            PyTestResult with parsed data
        """
        json_path = params.get("json_path")
        if not json_path:
            return PyTestResult(
                success=False,
                operation="parse_results",
                error="Missing required parameter: json_path",
            )

        try:
            with open(json_path) as f:
                data = json.load(f)

            summary = data.get("summary", {})
            parsed = {
                "total": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "errors": summary.get("error", 0),
                "duration": data.get("duration", 0),
                "tests": data.get("tests", []),
            }

            return PyTestResult(success=True, operation="parse_results", data=parsed)
        except FileNotFoundError:
            return PyTestResult(
                success=False,
                operation="parse_results",
                error=f"Results file not found: {json_path}",
            )
        except Exception as e:
            return PyTestResult(
                success=False, operation="parse_results", error=f"Parse error: {e}"
            )

    async def _get_coverage(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> PyTestResult:
        """
        Extract coverage data.

        Params:
            coverage_path: Path to coverage JSON (default: coverage.json)

        Returns:
            PyTestResult with coverage data
        """
        coverage_path = params.get("coverage_path", "coverage.json")

        try:
            with open(coverage_path) as f:
                data = json.load(f)

            coverage_data = {
                "total_coverage": data.get("totals", {}).get("percent_covered", 0),
                "lines_covered": data.get("totals", {}).get("covered_lines", 0),
                "lines_missing": data.get("totals", {}).get("missing_lines", 0),
                "files": {},
            }

            # Parse per-file coverage
            for file_path, file_data in data.get("files", {}).items():
                coverage_data["files"][file_path] = {
                    "percent_covered": file_data.get("summary", {}).get(
                        "percent_covered", 0
                    ),
                    "missing_lines": file_data.get("missing_lines", []),
                }

            return PyTestResult(
                success=True, operation="get_coverage", data=coverage_data
            )
        except FileNotFoundError:
            return PyTestResult(
                success=False,
                operation="get_coverage",
                error=f"Coverage file not found: {coverage_path}",
            )
        except Exception as e:
            return PyTestResult(
                success=False, operation="get_coverage", error=f"Coverage error: {e}"
            )

    async def _analyze_failures(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> PyTestResult:
        """
        Analyze test failures and extract details.

        Params:
            json_path: Path to JSON results (required)

        Returns:
            PyTestResult with failure analysis
        """
        json_path = params.get("json_path")
        if not json_path:
            return PyTestResult(
                success=False,
                operation="analyze_failures",
                error="Missing required parameter: json_path",
            )

        try:
            with open(json_path) as f:
                data = json.load(f)

            failures = []
            for test in data.get("tests", []):
                if test.get("outcome") in ["failed", "error"]:
                    failure = {
                        "nodeid": test.get("nodeid"),
                        "outcome": test.get("outcome"),
                        "duration": test.get("duration"),
                        "message": test.get("call", {}).get("longrepr", ""),
                    }
                    failures.append(failure)

            return PyTestResult(
                success=True,
                operation="analyze_failures",
                data={"count": len(failures), "failures": failures},
            )
        except Exception as e:
            return PyTestResult(
                success=False,
                operation="analyze_failures",
                error=f"Analysis error: {e}",
            )

    async def _generate_report(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> PyTestResult:
        """
        Generate human-readable test report.

        Params:
            json_path: Path to JSON results (required)
            format: Report format (text, markdown, html)

        Returns:
            PyTestResult with generated report
        """
        json_path = params.get("json_path")
        if not json_path:
            return PyTestResult(
                success=False,
                operation="generate_report",
                error="Missing required parameter: json_path",
            )

        try:
            with open(json_path) as f:
                data = json.load(f)

            summary = data.get("summary", {})
            report_format = params.get("format", "text")

            if report_format == "text":
                report = self._generate_text_report(summary, data)
            elif report_format == "markdown":
                report = self._generate_markdown_report(summary, data)
            else:
                return PyTestResult(
                    success=False,
                    operation="generate_report",
                    error=f"Unsupported format: {report_format}",
                )

            return PyTestResult(
                success=True,
                operation="generate_report",
                data={"format": report_format, "report": report},
            )
        except Exception as e:
            return PyTestResult(
                success=False,
                operation="generate_report",
                error=f"Report generation error: {e}",
            )

    def _parse_pytest_output(self, stdout: str, stderr: str) -> dict[str, Any]:
        """Parse pytest text output for key information."""
        data = {"stdout": stdout, "stderr": stderr}

        # Extract test counts
        if match := re.search(
            r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?", stdout
        ):
            data["passed"] = int(match.group(1))
            data["failed"] = int(match.group(2)) if match.group(2) else 0
            data["skipped"] = int(match.group(3)) if match.group(3) else 0

        # Extract duration
        if match := re.search(r"in ([\d.]+)s", stdout):
            data["duration"] = float(match.group(1))

        return data

    def _generate_text_report(self, summary: dict, data: dict) -> str:
        """Generate plain text report."""
        lines = [
            "Test Execution Report",
            "=" * 50,
            f"Total: {summary.get('total', 0)}",
            f"Passed: {summary.get('passed', 0)}",
            f"Failed: {summary.get('failed', 0)}",
            f"Skipped: {summary.get('skipped', 0)}",
            f"Duration: {data.get('duration', 0):.2f}s",
        ]

        if summary.get("failed", 0) > 0:
            lines.extend(["", "Failures:", "-" * 50])
            for test in data.get("tests", []):
                if test.get("outcome") == "failed":
                    lines.append(f"- {test.get('nodeid')}")

        return "\n".join(lines)

    def _generate_markdown_report(self, summary: dict, data: dict) -> str:
        """Generate markdown report."""
        lines = [
            "# Test Execution Report",
            "",
            "## Summary",
            "",
            f"- **Total:** {summary.get('total', 0)}",
            f"- **Passed:** {summary.get('passed', 0)} ✅",
            f"- **Failed:** {summary.get('failed', 0)} ❌",
            f"- **Skipped:** {summary.get('skipped', 0)} ⏭️",
            f"- **Duration:** {data.get('duration', 0):.2f}s",
        ]

        if summary.get("failed", 0) > 0:
            lines.extend(["", "## Failures", ""])
            for test in data.get("tests", []):
                if test.get("outcome") == "failed":
                    lines.append(f"- `{test.get('nodeid')}`")

        return "\n".join(lines)
