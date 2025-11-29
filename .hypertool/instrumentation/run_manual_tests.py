#!/usr/bin/env python3
"""
Manual Testing Execution Script

Runs all manual tests and generates a report.
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


class TestResult:
    """Represents the result of a test execution."""

    def __init__(self, name: str, duration: float, passed: bool, notes: str = ""):
        self.name = name
        self.duration = duration
        self.passed = passed
        self.notes = notes


class TestRunner:
    """Manages test execution and reporting."""

    def __init__(self):
        self.results: list[TestResult] = []
        self.start_time = datetime.now()

    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

    def print_success(self, text: str):
        """Print success message."""
        print(f"{GREEN}✅ {text}{RESET}")

    def print_error(self, text: str):
        """Print error message."""
        print(f"{RED}❌ {text}{RESET}")

    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{YELLOW}⚠️  {text}{RESET}")

    def print_info(self, text: str):
        """Print info message."""
        print(f"{BLUE}ℹ️  {text}{RESET}")

    async def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        self.print_header("Checking Prerequisites")

        checks = []

        # Check Prometheus
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:9090/-/healthy"],
                capture_output=True,
                timeout=5,
            )
            prometheus_ok = result.returncode == 0
            if prometheus_ok:
                self.print_success("Prometheus is running")
            else:
                self.print_error("Prometheus is not running")
            checks.append(prometheus_ok)
        except Exception as e:
            self.print_error(f"Prometheus check failed: {e}")
            checks.append(False)

        # Check Grafana
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:3000/api/health"],
                capture_output=True,
                timeout=5,
            )
            grafana_ok = result.returncode == 0
            if grafana_ok:
                self.print_success("Grafana is running")
            else:
                self.print_error("Grafana is not running")
            checks.append(grafana_ok)
        except Exception as e:
            self.print_error(f"Grafana check failed: {e}")
            checks.append(False)

        # Check Langfuse env vars
        import os

        langfuse_ok = all(
            [
                os.getenv("LANGFUSE_PUBLIC_KEY"),
                os.getenv("LANGFUSE_SECRET_KEY"),
                os.getenv("LANGFUSE_HOST"),
            ]
        )
        if langfuse_ok:
            self.print_success("Langfuse environment variables set")
        else:
            self.print_warning(
                "Langfuse environment variables not set (tests will run with degradation)"
            )
        checks.append(True)  # Don't fail on missing Langfuse        # Check Python dependencies
        try:
            import langfuse  # noqa: F401
            from observability_integration import (  # noqa: F401
                initialize_observability,
            )

            self.print_success("Python dependencies installed")
            checks.append(True)
        except ImportError as e:
            self.print_error(f"Missing Python dependencies: {e}")
            checks.append(False)

        return all(checks)

    async def run_baseline_test(self) -> TestResult:
        """Run the baseline test workflow."""
        self.print_header("Test 1: Baseline - test_instrumented_workflow.py")

        start = datetime.now()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    ".hypertool.instrumentation.test_instrumented_workflow",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            duration = (datetime.now() - start).total_seconds()

            if result.returncode == 0 and "✅ Workflow Complete" in result.stdout:
                self.print_success(f"Baseline test passed in {duration:.1f}s")
                print(f"\n{result.stdout}")
                return TestResult("Baseline Test", duration, True)
            else:
                self.print_error("Baseline test failed")
                print(f"\nStdout:\n{result.stdout}")
                print(f"\nStderr:\n{result.stderr}")
                return TestResult("Baseline Test", duration, False, result.stderr)

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds()
            self.print_error("Baseline test timed out")
            return TestResult("Baseline Test", duration, False, "Timeout")
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.print_error(f"Baseline test error: {e}")
            return TestResult("Baseline Test", duration, False, str(e))

    async def verify_prometheus_metrics(self) -> TestResult:
        """Verify Prometheus metrics are being collected."""
        self.print_header("Verifying Prometheus Metrics")

        start = datetime.now()
        try:
            # Query for Hypertool metrics
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-G",
                    "http://localhost:9090/api/v1/label/__name__/values",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            duration = (datetime.now() - start).total_seconds()

            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                hypertool_metrics = [m for m in data.get("data", []) if "hypertool" in m]

                if hypertool_metrics:
                    self.print_success(f"Found {len(hypertool_metrics)} Hypertool metrics")
                    for metric in hypertool_metrics[:5]:  # Show first 5
                        self.print_info(f"  - {metric}")
                    if len(hypertool_metrics) > 5:
                        self.print_info(f"  ... and {len(hypertool_metrics) - 5} more")
                    return TestResult("Prometheus Metrics", duration, True)
                else:
                    self.print_error("No Hypertool metrics found")
                    return TestResult("Prometheus Metrics", duration, False, "No metrics found")
            else:
                self.print_error("Failed to query Prometheus")
                return TestResult("Prometheus Metrics", duration, False, "Query failed")

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.print_error(f"Metrics verification error: {e}")
            return TestResult("Prometheus Metrics", duration, False, str(e))

    async def verify_grafana_dashboards(self) -> TestResult:
        """Verify Grafana dashboards exist."""
        self.print_header("Verifying Grafana Dashboards")

        start = datetime.now()
        try:
            # Check if dashboard files exist
            dashboard_dir = Path(".hypertool/instrumentation/dashboards")
            dashboards = list(dashboard_dir.glob("*.json"))

            duration = (datetime.now() - start).total_seconds()

            if dashboards:
                self.print_success(f"Found {len(dashboards)} dashboard file(s)")
                for dashboard in dashboards:
                    self.print_info(f"  - {dashboard.name}")
                return TestResult("Grafana Dashboards", duration, True)
            else:
                self.print_error("No dashboard files found")
                return TestResult("Grafana Dashboards", duration, False, "No dashboards")

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.print_error(f"Dashboard verification error: {e}")
            return TestResult("Grafana Dashboards", duration, False, str(e))

    async def verify_alert_rules(self) -> TestResult:
        """Verify Prometheus alert rules exist."""
        self.print_header("Verifying Alert Rules")

        start = datetime.now()
        try:
            alert_file = Path(".hypertool/instrumentation/persona_alerts.yml")

            duration = (datetime.now() - start).total_seconds()

            if alert_file.exists():
                # Count alerts in file
                content = alert_file.read_text()
                alert_count = content.count("- alert:")
                self.print_success(f"Found alert rules file with {alert_count} alerts")
                return TestResult("Alert Rules", duration, True)
            else:
                self.print_error("Alert rules file not found")
                return TestResult("Alert Rules", duration, False, "File not found")

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.print_error(f"Alert rules verification error: {e}")
            return TestResult("Alert Rules", duration, False, str(e))

    def generate_report(self):
        """Generate test summary report."""
        self.print_header("Test Summary Report")

        total_duration = (datetime.now() - self.start_time).total_seconds()

        # Overall statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        print(f"{BOLD}Overall Results:{RESET}")
        print(f"  Total Tests: {total_tests}")
        print(f"  {GREEN}Passed: {passed_tests}{RESET}")
        print(f"  {RED}Failed: {failed_tests}{RESET}")
        print(f"  Duration: {total_duration:.1f}s")

        # Individual test results
        print(f"\n{BOLD}Individual Test Results:{RESET}")
        for result in self.results:
            status = f"{GREEN}✅ PASS{RESET}" if result.passed else f"{RED}❌ FAIL{RESET}"
            print(f"  {status} - {result.name} ({result.duration:.1f}s)")
            if result.notes and not result.passed:
                print(f"         Notes: {result.notes}")

        # Final verdict
        print()
        if failed_tests == 0:
            self.print_success("All tests passed! 🎉")
            return True
        else:
            self.print_error(f"{failed_tests} test(s) failed")
            return False

    async def run_all_tests(self):
        """Run all manual tests."""
        self.print_header("Phase 5 Manual Testing - Execution")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Check prerequisites
        if not await self.check_prerequisites():
            self.print_error("Prerequisites check failed. Please fix and retry.")
            self.print_info(
                "\nTo start observability stack:\n  docker-compose -f docker-compose.test.yml up -d"
            )
            return False

        # Run tests
        self.results.append(await self.run_baseline_test())
        await asyncio.sleep(2)  # Brief pause between tests

        self.results.append(await self.verify_prometheus_metrics())
        await asyncio.sleep(1)

        self.results.append(await self.verify_grafana_dashboards())
        await asyncio.sleep(1)

        self.results.append(await self.verify_alert_rules())

        # Generate report
        return self.generate_report()


async def main():
    """Main entry point."""
    runner = TestRunner()
    success = await runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
