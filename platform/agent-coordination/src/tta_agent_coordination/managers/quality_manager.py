"""
QualityManager - L2 Domain Manager for Quality Operations

Coordinates PyTestExpert for quality-focused workflows: coverage analysis,
test selection, quality gates, report generation, and trend tracking.

Architecture: Layer 2 (Domain Management) - Orchestrates Layer 3 experts
"""

from dataclasses import dataclass, field
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.apm.instrumented import APMWorkflowPrimitive

from ..experts.pytest_expert import PyTestExpert, PyTestOperation, PyTestResult

# ============================================================================
# Configuration and Operations
# ============================================================================


@dataclass
class QualityManagerConfig:
    """Configuration for QualityManager."""

    pytest_executable: str = "python"
    """Pytest executable: 'python' (python -m pytest) or 'uv' (uv run pytest)"""

    default_test_strategy: str = "coverage"
    """Default test strategy: fast, thorough, coverage"""

    min_coverage_percent: float = 80.0
    """Minimum coverage percentage for quality gate"""

    max_failures: int = 0
    """Maximum number of test failures allowed for quality gate"""

    coverage_output_format: str = "html"
    """Coverage report format: html, xml, json, term"""

    generate_reports: bool = True
    """Whether to generate quality reports"""

    track_trends: bool = False
    """Whether to track quality trends over time"""

    trends_file: str = ".quality_trends.json"
    """File to store quality trends data"""


@dataclass
class QualityOperation:
    """Operation specification for quality workflow."""

    operation: str
    """Operation type: coverage_analysis, quality_gate, generate_report"""

    test_path: str | None = None
    """Path to tests (default: all tests)"""

    test_strategy: str | None = None
    """Override test strategy: fast, thorough, coverage"""

    coverage_threshold: float | None = None
    """Override minimum coverage threshold"""

    max_failures: int | None = None
    """Override maximum failures threshold"""

    output_format: str | None = None
    """Override coverage output format"""

    include_trends: bool = False
    """Include historical trend analysis"""


@dataclass
class QualityResult:
    """Result of quality operation."""

    success: bool
    """Whether operation succeeded"""

    operation: str
    """Operation type executed"""

    test_results: dict[str, Any] = field(default_factory=dict)
    """Test execution results"""

    coverage_data: dict[str, Any] = field(default_factory=dict)
    """Coverage analysis data"""

    quality_gate_passed: bool = False
    """Whether quality gates passed"""

    quality_issues: list[str] = field(default_factory=list)
    """List of quality issues found"""

    report_path: str | None = None
    """Path to generated report (if any)"""

    trends_data: dict[str, Any] = field(default_factory=dict)
    """Historical trends data (if enabled)"""

    duration_seconds: float = 0.0
    """Total operation duration"""

    error: str | None = None
    """Error message if operation failed"""


# ============================================================================
# QualityManager Implementation
# ============================================================================


class QualityManager(APMWorkflowPrimitive):
    """
    L2 Domain Manager for quality-focused operations.

    Coordinates PyTestExpert for:
    - Coverage analysis with configurable thresholds
    - Test selection strategies (fast, thorough, coverage)
    - Quality gates (minimum coverage, max failures)
    - Report generation (HTML, XML, JSON formats)
    - Historical trend tracking (optional)

    Example:
        >>> config = QualityManagerConfig(
        ...     min_coverage_percent=85.0,
        ...     max_failures=0
        ... )
        >>> manager = QualityManager(config=config)
        >>> operation = QualityOperation(
        ...     operation="coverage_analysis",
        ...     test_strategy="coverage"
        ... )
        >>> result = await manager.execute(operation, context)
        >>> print(f"Coverage: {result.coverage_data['total_coverage']}")
    """

    def __init__(
        self,
        config: QualityManagerConfig,
        pytest_expert: PyTestExpert | None = None,
    ):
        """
        Initialize QualityManager.

        Args:
            config: Configuration for quality operations
            pytest_expert: Optional PyTestExpert instance (creates if None)
        """
        super().__init__(name="quality_manager")
        self.config = config

        # Initialize PyTestExpert
        if pytest_expert:
            self.pytest_expert = pytest_expert
        else:
            from ..experts.pytest_expert import PyTestConfig, PyTestExpertConfig

            pytest_config = PyTestExpertConfig()
            if config.pytest_executable:
                pytest_config.pytest_config = PyTestConfig(
                    python_executable=config.pytest_executable
                )
            self.pytest_expert = PyTestExpert(config=pytest_config)

    async def _execute_impl(
        self,
        input_data: QualityOperation,
        context: WorkflowContext,
    ) -> QualityResult:
        """
        Execute quality operation.

        Args:
            input_data: Quality operation specification
            context: Workflow context for tracing

        Returns:
            Quality operation result
        """
        operation = input_data.operation

        # Validate operation
        validation_error = self._validate_operation(input_data)
        if validation_error:
            return QualityResult(
                success=False,
                operation=operation,
                error=validation_error,
            )

        # Route to appropriate handler
        if operation == "coverage_analysis":
            return await self._run_coverage_analysis(input_data, context)
        elif operation == "quality_gate":
            return await self._check_quality_gate(input_data, context)
        elif operation == "generate_report":
            return await self._generate_report(input_data, context)
        else:
            return QualityResult(
                success=False,
                operation=operation,
                error=f"Unknown operation: {operation}",
            )

    def _validate_operation(self, operation: QualityOperation) -> str | None:
        """
        Validate quality operation.

        Args:
            operation: Operation to validate

        Returns:
            Error message if invalid, None if valid
        """
        valid_operations = ["coverage_analysis", "quality_gate", "generate_report"]
        if operation.operation not in valid_operations:
            return f"Invalid operation: {operation.operation}"

        # Validate coverage threshold
        if operation.coverage_threshold is not None:
            if not 0 <= operation.coverage_threshold <= 100:
                return "Coverage threshold must be between 0 and 100"

        # Validate max failures
        if operation.max_failures is not None:
            if operation.max_failures < 0:
                return "Max failures must be non-negative"

        return None

    async def _run_coverage_analysis(
        self,
        operation: QualityOperation,
        context: WorkflowContext,
    ) -> QualityResult:
        """
        Run coverage analysis.

        Args:
            operation: Coverage operation spec
            context: Workflow context

        Returns:
            Quality result with coverage data
        """
        import time

        start_time = time.time()

        # Prepare pytest operation
        test_strategy = operation.test_strategy or self.config.default_test_strategy
        pytest_op = PyTestOperation(
            operation="run_tests",
            params={
                "test_path": operation.test_path or "tests/",
                "strategy": test_strategy,
            },
        )

        # Run tests with coverage
        pytest_result = await self.pytest_expert.execute(pytest_op, context)

        duration = time.time() - start_time

        if not pytest_result.success:
            test_data = pytest_result.data or {}
            return QualityResult(
                success=False,
                operation="coverage_analysis",
                test_results={
                    "total_tests": test_data.get("total_tests", 0),
                    "passed": test_data.get("passed", 0),
                    "failed": test_data.get("failed", 0),
                },
                error=f"Test execution failed: {pytest_result.error}",
                duration_seconds=duration,
            )

        # Extract coverage data
        coverage_data = self._extract_coverage_data(pytest_result)

        # Check if coverage meets threshold
        threshold = operation.coverage_threshold or self.config.min_coverage_percent
        coverage_percent = self._get_coverage_percent(coverage_data)
        meets_threshold = coverage_percent >= threshold

        # Build result
        test_data = pytest_result.data or {}
        result = QualityResult(
            success=True,
            operation="coverage_analysis",
            test_results={
                "total_tests": test_data.get("total_tests", 0),
                "passed": test_data.get("passed", 0),
                "failed": test_data.get("failed", 0),
                "duration_seconds": test_data.get("duration_seconds", 0.0),
            },
            coverage_data=coverage_data,
            quality_gate_passed=meets_threshold,
            quality_issues=[]
            if meets_threshold
            else [f"Coverage {coverage_percent:.1f}% below threshold {threshold}%"],
            duration_seconds=duration,
        )

        # Add trends if requested
        if operation.include_trends and self.config.track_trends:
            result.trends_data = self._get_trends_data(coverage_data)

        return result

    async def _check_quality_gate(
        self,
        operation: QualityOperation,
        context: WorkflowContext,
    ) -> QualityResult:
        """
        Check quality gates (coverage + test failures).

        Args:
            operation: Quality gate operation
            context: Workflow context

        Returns:
            Quality result with gate status
        """
        import time

        start_time = time.time()

        # Run coverage analysis first
        coverage_result = await self._run_coverage_analysis(operation, context)

        if not coverage_result.success:
            return coverage_result

        # Get thresholds
        coverage_threshold = (
            operation.coverage_threshold or self.config.min_coverage_percent
        )
        max_failures = operation.max_failures or self.config.max_failures

        # Check gates
        issues = []

        # Coverage gate
        coverage_percent = self._get_coverage_percent(coverage_result.coverage_data)
        if coverage_percent < coverage_threshold:
            issues.append(
                f"Coverage {coverage_percent:.1f}% "
                f"below threshold {coverage_threshold}%"
            )

        # Failure gate
        failed_tests = coverage_result.test_results.get("failed", 0)
        if failed_tests > max_failures:
            issues.append(
                f"Failed tests ({failed_tests}) exceeds maximum ({max_failures})"
            )

        gate_passed = len(issues) == 0

        duration = time.time() - start_time

        return QualityResult(
            success=True,
            operation="quality_gate",
            test_results=coverage_result.test_results,
            coverage_data=coverage_result.coverage_data,
            quality_gate_passed=gate_passed,
            quality_issues=issues,
            duration_seconds=duration,
        )

    async def _generate_report(
        self,
        operation: QualityOperation,
        context: WorkflowContext,
    ) -> QualityResult:
        """
        Generate quality report.

        Args:
            operation: Report generation operation
            context: Workflow context

        Returns:
            Quality result with report path
        """
        import time

        start_time = time.time()

        # Run coverage analysis
        coverage_result = await self._run_coverage_analysis(operation, context)

        if not coverage_result.success:
            return coverage_result

        # Generate report
        output_format = operation.output_format or self.config.coverage_output_format
        report_path = self._generate_quality_report(
            coverage_result.test_results,
            coverage_result.coverage_data,
            output_format,
        )

        duration = time.time() - start_time

        return QualityResult(
            success=True,
            operation="generate_report",
            test_results=coverage_result.test_results,
            coverage_data=coverage_result.coverage_data,
            quality_gate_passed=coverage_result.quality_gate_passed,
            quality_issues=coverage_result.quality_issues,
            report_path=report_path,
            duration_seconds=duration,
        )

    def _extract_coverage_data(self, pytest_result: PyTestResult) -> dict[str, Any]:
        """
        Extract coverage data from pytest result.

        Args:
            pytest_result: Pytest execution result

        Returns:
            Coverage data dictionary
        """
        # PyTestResult stores data in .data dict
        test_data = pytest_result.data or {}
        coverage = test_data.get("coverage", {})

        if not coverage:
            # No coverage data available
            return {
                "total_coverage": "N/A",
                "covered_lines": 0,
                "total_lines": 0,
                "modules": {},
            }

        return coverage

    def _get_coverage_percent(self, coverage_data: dict[str, Any]) -> float:
        """
        Extract coverage percentage from coverage data.

        Args:
            coverage_data: Coverage dictionary

        Returns:
            Coverage percentage (0-100)
        """
        total_coverage = coverage_data.get("total_coverage", "0%")

        if isinstance(total_coverage, str):
            # Parse "85.3%" format
            try:
                return float(total_coverage.rstrip("%"))
            except ValueError:
                return 0.0

        # Already a number
        return float(total_coverage)

    def _generate_quality_report(
        self,
        test_results: dict[str, Any],
        coverage_data: dict[str, Any],
        output_format: str,
    ) -> str:
        """
        Generate quality report file.

        Args:
            test_results: Test execution results
            coverage_data: Coverage data
            output_format: Report format (html, xml, json)

        Returns:
            Path to generated report
        """
        import json
        from pathlib import Path

        # Create reports directory
        reports_dir = Path(".quality_reports")
        reports_dir.mkdir(exist_ok=True)

        # Generate report filename
        timestamp = self._get_timestamp()
        filename = f"quality_report_{timestamp}.{output_format}"
        report_path = reports_dir / filename

        # Generate report content
        if output_format == "json":
            report_data = {
                "test_results": test_results,
                "coverage_data": coverage_data,
                "timestamp": timestamp,
            }
            report_path.write_text(json.dumps(report_data, indent=2))

        elif output_format == "html":
            html_content = self._generate_html_report(test_results, coverage_data)
            report_path.write_text(html_content)

        elif output_format == "xml":
            xml_content = self._generate_xml_report(test_results, coverage_data)
            report_path.write_text(xml_content)

        else:
            # Default to text format
            text_content = self._generate_text_report(test_results, coverage_data)
            report_path.write_text(text_content)

        return str(report_path)

    def _generate_html_report(
        self,
        test_results: dict[str, Any],
        coverage_data: dict[str, Any],
    ) -> str:
        """Generate HTML quality report."""
        total_coverage = coverage_data.get("total_coverage", "N/A")
        total_tests = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .metric {{ margin: 20px 0; }}
        .metric-label {{ font-weight: bold; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
    </style>
</head>
<body>
    <h1>Quality Report</h1>
    <div class="metric">
        <span class="metric-label">Total Coverage:</span>
        <span>{total_coverage}</span>
    </div>
    <div class="metric">
        <span class="metric-label">Tests:</span>
        <span>{total_tests} total, </span>
        <span class="success">{passed} passed</span>,
        <span class="failure">{failed} failed</span>
    </div>
</body>
</html>
        """

    def _generate_xml_report(
        self,
        test_results: dict[str, Any],
        coverage_data: dict[str, Any],
    ) -> str:
        """Generate XML quality report."""
        total_coverage = coverage_data.get("total_coverage", "N/A")
        total_tests = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)

        return f"""
<?xml version="1.0" encoding="UTF-8"?>
<quality-report>
    <coverage>
        <total>{total_coverage}</total>
    </coverage>
    <tests>
        <total>{total_tests}</total>
        <passed>{passed}</passed>
        <failed>{failed}</failed>
    </tests>
</quality-report>
        """

    def _generate_text_report(
        self,
        test_results: dict[str, Any],
        coverage_data: dict[str, Any],
    ) -> str:
        """Generate text quality report."""
        total_coverage = coverage_data.get("total_coverage", "N/A")
        total_tests = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)

        return f"""
Quality Report
==============

Coverage: {total_coverage}
Tests: {total_tests} total, {passed} passed, {failed} failed
        """

    def _get_trends_data(self, coverage_data: dict[str, Any]) -> dict[str, Any]:
        """
        Get historical trends data.

        Args:
            coverage_data: Current coverage data

        Returns:
            Trends data (current + historical)
        """
        import json
        from pathlib import Path

        trends_file = Path(self.config.trends_file)

        # Load existing trends
        if trends_file.exists():
            trends = json.loads(trends_file.read_text())
        else:
            trends = {"history": []}

        # Add current data point
        trends["history"].append(
            {
                "timestamp": self._get_timestamp(),
                "coverage": coverage_data.get("total_coverage", "N/A"),
            }
        )

        # Save updated trends
        trends_file.write_text(json.dumps(trends, indent=2))

        return trends

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def close(self) -> None:
        """Close QualityManager and cleanup resources."""
        # PyTestExpert doesn't need explicit cleanup
        pass
