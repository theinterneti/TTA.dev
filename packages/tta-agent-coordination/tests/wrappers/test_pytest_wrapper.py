"""
Tests for PyTest CLI Wrapper (L4 Execution Layer).

Comprehensive test coverage for PyTestCLIWrapper including:
- Test execution operations
- Collection operations
- Result parsing
- Coverage extraction
- Failure analysis
- Report generation
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import Mock, mock_open, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.wrappers.pytest_wrapper import (
    PyTestCLIWrapper,
    PyTestConfig,
    PyTestOperation,
)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess module."""
    with patch("tta_agent_coordination.wrappers.pytest_wrapper.subprocess") as mock:
        # Mock pytest --version check
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "pytest 7.4.0"
        mock.run.return_value = version_result
        yield mock


@pytest.fixture
def wrapper(mock_subprocess):
    """Create PyTest wrapper with mock subprocess."""
    config = PyTestConfig()
    return PyTestCLIWrapper(config=config)


@pytest.fixture
def context():
    """Create workflow context."""
    return WorkflowContext(correlation_id="test-123")


class TestPyTestCLIWrapper:
    """Test suite for PyTestCLIWrapper."""

    def test_init_with_config(self, mock_subprocess):
        """Test initialization with explicit config."""
        config = PyTestConfig(python_executable="python3", timeout=600)
        wrapper = PyTestCLIWrapper(config=config)

        assert wrapper.config.python_executable == "python3"
        assert wrapper.config.timeout == 600

    def test_init_pytest_not_found(self):
        """Test initialization when pytest not available."""
        with patch("tta_agent_coordination.wrappers.pytest_wrapper.subprocess") as mock:
            mock.run.side_effect = FileNotFoundError("pytest not found")

            with pytest.raises(FileNotFoundError, match="pytest not available"):
                PyTestCLIWrapper()

    @pytest.mark.asyncio
    async def test_run_tests_success(self, wrapper, context, mock_subprocess):
        """Test successful test execution."""
        # Mock subprocess result
        test_result = Mock()
        test_result.returncode = 0
        test_result.stdout = "5 passed in 1.23s"
        test_result.stderr = ""

        # Mock JSON results file
        json_data = {
            "summary": {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
            "duration": 1.23,
            "tests": [],
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            with patch("pathlib.Path.exists", return_value=True):
                mock_subprocess.run.return_value = test_result

                operation = PyTestOperation(
                    operation="run_tests",
                    params={
                        "test_path": "tests/",
                        "verbose": 2,
                        "coverage": True,
                        "json_output": "/tmp/results.json",
                    },
                )

                result = await wrapper.execute(operation, context)

                assert result.success is True
                assert result.data["passed"] == 5
                assert result.data["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_run_tests_with_failures(self, wrapper, context, mock_subprocess):
        """Test execution with test failures."""
        test_result = Mock()
        test_result.returncode = 1  # Failures present
        test_result.stdout = "3 passed, 2 failed in 2.45s"
        test_result.stderr = ""

        json_data = {
            "summary": {"total": 5, "passed": 3, "failed": 2, "skipped": 0},
            "duration": 2.45,
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            with patch("pathlib.Path.exists", return_value=True):
                mock_subprocess.run.return_value = test_result

                operation = PyTestOperation(
                    operation="run_tests", params={"test_path": "tests/"}
                )

                result = await wrapper.execute(operation, context)

                assert result.success is True  # Exit code 1 is acceptable
                assert result.data["failed"] == 2
                assert result.data["passed"] == 3

    @pytest.mark.asyncio
    async def test_run_tests_missing_path(self, wrapper, context):
        """Test run_tests with missing test_path parameter."""
        operation = PyTestOperation(
            operation="run_tests",
            params={"verbose": 2},  # Missing test_path
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameter: test_path" in result.error

    @pytest.mark.asyncio
    async def test_run_tests_with_markers(self, wrapper, context, mock_subprocess):
        """Test execution with pytest markers."""
        test_result = Mock()
        test_result.returncode = 0
        test_result.stdout = "3 passed in 0.5s"
        test_result.stderr = ""

        with patch("pathlib.Path.exists", return_value=False):
            mock_subprocess.run.return_value = test_result

            operation = PyTestOperation(
                operation="run_tests",
                params={
                    "test_path": "tests/",
                    "markers": ["unit", "not slow"],
                    "coverage": False,
                },
            )

            result = await wrapper.execute(operation, context)

            # Verify execution succeeded
            assert result.success is True
            assert result.data["passed"] == 3

            # Verify markers were added to command
            call_args = mock_subprocess.run.call_args[0][0]
            assert "-m" in call_args
            assert "unit" in call_args

    @pytest.mark.asyncio
    async def test_run_tests_timeout(self, wrapper, context, mock_subprocess):
        """Test test execution timeout."""
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired(
            cmd="pytest", timeout=300
        )

        operation = PyTestOperation(
            operation="run_tests", params={"test_path": "tests/"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_collect_tests_success(self, wrapper, context, mock_subprocess):
        """Test test collection."""
        test_result = Mock()
        test_result.returncode = 0
        test_result.stdout = """
tests/test_file1.py::test_func1
tests/test_file1.py::test_func2
tests/test_file2.py::test_func3
"""
        test_result.stderr = ""
        mock_subprocess.run.return_value = test_result

        operation = PyTestOperation(
            operation="collect_tests", params={"test_path": "tests/"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["count"] == 3
        assert "test_func1" in result.data["tests"][0]

    @pytest.mark.asyncio
    async def test_collect_tests_missing_path(self, wrapper, context):
        """Test collect_tests with missing test_path."""
        operation = PyTestOperation(operation="collect_tests", params={})

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameter: test_path" in result.error

    @pytest.mark.asyncio
    async def test_parse_results_success(self, wrapper, context):
        """Test parsing JSON results."""
        json_data = {
            "summary": {
                "total": 10,
                "passed": 8,
                "failed": 1,
                "skipped": 1,
                "error": 0,
            },
            "duration": 5.67,
            "tests": [{"nodeid": "test1", "outcome": "passed"}],
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            operation = PyTestOperation(
                operation="parse_results", params={"json_path": "/tmp/results.json"}
            )

            result = await wrapper.execute(operation, context)

            assert result.success is True
            assert result.data["total"] == 10
            assert result.data["passed"] == 8
            assert result.data["failed"] == 1
            assert result.data["duration"] == 5.67

    @pytest.mark.asyncio
    async def test_parse_results_missing_file(self, wrapper, context):
        """Test parse_results with missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            operation = PyTestOperation(
                operation="parse_results", params={"json_path": "/tmp/missing.json"}
            )

            result = await wrapper.execute(operation, context)

            assert result.success is False
            assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_parse_results_missing_path(self, wrapper, context):
        """Test parse_results with missing json_path parameter."""
        operation = PyTestOperation(operation="parse_results", params={})

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameter: json_path" in result.error

    @pytest.mark.asyncio
    async def test_get_coverage_success(self, wrapper, context):
        """Test coverage data extraction."""
        coverage_data = {
            "totals": {
                "percent_covered": 85.5,
                "covered_lines": 342,
                "missing_lines": 58,
            },
            "files": {
                "src/module1.py": {
                    "summary": {"percent_covered": 90.0},
                    "missing_lines": [10, 15, 20],
                },
                "src/module2.py": {
                    "summary": {"percent_covered": 80.0},
                    "missing_lines": [5, 8],
                },
            },
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
            operation = PyTestOperation(
                operation="get_coverage", params={"coverage_path": "coverage.json"}
            )

            result = await wrapper.execute(operation, context)

            assert result.success is True
            assert result.data["total_coverage"] == 85.5
            assert result.data["lines_covered"] == 342
            assert "src/module1.py" in result.data["files"]
            assert result.data["files"]["src/module1.py"]["percent_covered"] == 90.0

    @pytest.mark.asyncio
    async def test_get_coverage_missing_file(self, wrapper, context):
        """Test get_coverage with missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            operation = PyTestOperation(
                operation="get_coverage", params={"coverage_path": "missing.json"}
            )

            result = await wrapper.execute(operation, context)

            assert result.success is False
            assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_analyze_failures_success(self, wrapper, context):
        """Test failure analysis."""
        json_data = {
            "tests": [
                {
                    "nodeid": "tests/test_1.py::test_pass",
                    "outcome": "passed",
                    "duration": 0.5,
                },
                {
                    "nodeid": "tests/test_2.py::test_fail",
                    "outcome": "failed",
                    "duration": 1.2,
                    "call": {"longrepr": "AssertionError: expected 5, got 3"},
                },
                {
                    "nodeid": "tests/test_3.py::test_error",
                    "outcome": "error",
                    "duration": 0.1,
                    "call": {"longrepr": "ImportError: module not found"},
                },
            ]
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            operation = PyTestOperation(
                operation="analyze_failures", params={"json_path": "/tmp/results.json"}
            )

            result = await wrapper.execute(operation, context)

            assert result.success is True
            assert result.data["count"] == 2  # 1 failed + 1 error
            assert len(result.data["failures"]) == 2
            assert "AssertionError" in result.data["failures"][0]["message"]

    @pytest.mark.asyncio
    async def test_analyze_failures_missing_path(self, wrapper, context):
        """Test analyze_failures with missing json_path."""
        operation = PyTestOperation(operation="analyze_failures", params={})

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameter: json_path" in result.error

    @pytest.mark.asyncio
    async def test_generate_report_text_format(self, wrapper, context):
        """Test text report generation."""
        json_data = {
            "summary": {"total": 10, "passed": 8, "failed": 2, "skipped": 0},
            "duration": 3.45,
            "tests": [
                {"nodeid": "tests/test_fail1.py::test1", "outcome": "failed"},
                {"nodeid": "tests/test_fail2.py::test2", "outcome": "failed"},
            ],
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            operation = PyTestOperation(
                operation="generate_report",
                params={"json_path": "/tmp/results.json", "format": "text"},
            )

            result = await wrapper.execute(operation, context)

            assert result.success is True
            assert result.data["format"] == "text"
            assert "Test Execution Report" in result.data["report"]
            assert "Passed: 8" in result.data["report"]
            assert "Failed: 2" in result.data["report"]

    @pytest.mark.asyncio
    async def test_generate_report_markdown_format(self, wrapper, context):
        """Test markdown report generation."""
        json_data = {
            "summary": {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
            "duration": 1.23,
            "tests": [],
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            operation = PyTestOperation(
                operation="generate_report",
                params={"json_path": "/tmp/results.json", "format": "markdown"},
            )

            result = await wrapper.execute(operation, context)

            assert result.success is True
            assert result.data["format"] == "markdown"
            assert "# Test Execution Report" in result.data["report"]
            assert "**Passed:** 5 ✅" in result.data["report"]

    @pytest.mark.asyncio
    async def test_generate_report_unsupported_format(self, wrapper, context):
        """Test report generation with unsupported format."""
        json_data = {"summary": {}, "tests": []}

        with patch("builtins.open", mock_open(read_data=json.dumps(json_data))):
            operation = PyTestOperation(
                operation="generate_report",
                params={"json_path": "/tmp/results.json", "format": "pdf"},
            )

            result = await wrapper.execute(operation, context)

            assert result.success is False
            assert "Unsupported format" in result.error

    @pytest.mark.asyncio
    async def test_generate_report_missing_path(self, wrapper, context):
        """Test generate_report with missing json_path."""
        operation = PyTestOperation(
            operation="generate_report", params={"format": "text"}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameter: json_path" in result.error

    @pytest.mark.asyncio
    async def test_invalid_operation(self, wrapper, context):
        """Test invalid operation handling."""
        operation = PyTestOperation(operation="invalid_operation", params={})

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Unknown operation" in result.error
