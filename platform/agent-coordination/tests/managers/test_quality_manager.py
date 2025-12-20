"""
Tests for QualityManager - L2 Domain Manager for Quality Operations

Tests coverage:
- Initialization and configuration
- Coverage analysis workflows
- Quality gate validation
- Report generation (HTML, XML, JSON)
- Error handling and validation
- Integration with PyTestExpert
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.experts.pytest_expert import PyTestResult
from tta_agent_coordination.managers.quality_manager import (
    QualityManager,
    QualityManagerConfig,
    QualityOperation,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def default_config():
    """Default QualityManager configuration."""
    return QualityManagerConfig(
        pytest_executable="python",
        default_test_strategy="coverage",
        min_coverage_percent=80.0,
        max_failures=0,
        coverage_output_format="html",
        generate_reports=True,
        track_trends=False,
    )


@pytest.fixture
def mock_pytest_expert():
    """Mock PyTestExpert for testing."""
    expert = MagicMock()
    expert.execute = AsyncMock()
    return expert


@pytest.fixture
def workflow_context():
    """Workflow context for testing."""
    return WorkflowContext(correlation_id="quality-test-123")


@pytest.fixture
def mock_pytest_result_success():
    """Mock successful PyTestResult."""
    return PyTestResult(
        success=True,
        operation="run_tests",
        data={
            "total_tests": 50,
            "passed": 50,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 12.5,
            "exit_code": 0,
            "coverage": {
                "total_coverage": "85.3%",
                "covered_lines": 853,
                "total_lines": 1000,
                "modules": {"module1.py": "90%", "module2.py": "80%"},
            },
        },
        error=None,
    )


@pytest.fixture
def mock_pytest_result_failure():
    """Mock failed PyTestResult."""
    return PyTestResult(
        success=False,
        operation="run_tests",
        data={
            "total_tests": 50,
            "passed": 45,
            "failed": 5,
            "skipped": 0,
            "duration_seconds": 15.0,
            "exit_code": 1,
        },
        error="5 tests failed",
    )


@pytest.fixture
def mock_pytest_result_low_coverage():
    """Mock PyTestResult with low coverage."""
    return PyTestResult(
        success=True,
        operation="run_tests",
        data={
            "total_tests": 50,
            "passed": 50,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 12.5,
            "exit_code": 0,
            "coverage": {
                "total_coverage": "65.0%",
                "covered_lines": 650,
                "total_lines": 1000,
                "modules": {},
            },
        },
        error=None,
    )


# ============================================================================
# Test Initialization
# ============================================================================


def test_quality_manager_init_with_config(default_config):
    """Test QualityManager initialization with configuration."""
    manager = QualityManager(config=default_config)

    assert manager.config == default_config
    assert manager.pytest_expert is not None
    assert manager.config.min_coverage_percent == 80.0
    assert manager.config.max_failures == 0


def test_quality_manager_init_with_custom_expert(default_config, mock_pytest_expert):
    """Test QualityManager initialization with custom PyTestExpert."""
    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    assert manager.config == default_config
    assert manager.pytest_expert == mock_pytest_expert


# ============================================================================
# Test Validation
# ============================================================================


@pytest.mark.asyncio
async def test_validate_operation_invalid_operation(
    default_config, workflow_context, mock_pytest_expert
):
    """Test validation rejects invalid operation type."""
    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="invalid_operation")

    result = await manager.execute(operation, workflow_context)

    assert not result.success
    assert result.error == "Invalid operation: invalid_operation"


@pytest.mark.asyncio
async def test_validate_operation_invalid_coverage_threshold(
    default_config, workflow_context, mock_pytest_expert
):
    """Test validation rejects invalid coverage threshold."""
    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(
        operation="coverage_analysis",
        coverage_threshold=150.0,  # Invalid: > 100
    )

    result = await manager.execute(operation, workflow_context)

    assert not result.success
    assert "Coverage threshold must be between 0 and 100" in result.error


@pytest.mark.asyncio
async def test_validate_operation_invalid_max_failures(
    default_config, workflow_context, mock_pytest_expert
):
    """Test validation rejects negative max failures."""
    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(
        operation="quality_gate",
        max_failures=-1,  # Invalid: negative
    )

    result = await manager.execute(operation, workflow_context)

    assert not result.success
    assert "Max failures must be non-negative" in result.error


# ============================================================================
# Test Coverage Analysis
# ============================================================================


@pytest.mark.asyncio
async def test_coverage_analysis_success(
    default_config, workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test successful coverage analysis."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(
        operation="coverage_analysis", test_strategy="coverage"
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.operation == "coverage_analysis"
    assert result.test_results["total_tests"] == 50
    assert result.test_results["passed"] == 50
    assert result.test_results["failed"] == 0
    assert "85.3%" in str(result.coverage_data["total_coverage"])
    assert result.quality_gate_passed  # 85.3% > 80% threshold
    assert len(result.quality_issues) == 0


@pytest.mark.asyncio
async def test_coverage_analysis_low_coverage(
    default_config,
    workflow_context,
    mock_pytest_expert,
    mock_pytest_result_low_coverage,
):
    """Test coverage analysis with low coverage."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_low_coverage

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="coverage_analysis")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.operation == "coverage_analysis"
    assert not result.quality_gate_passed  # 65% < 80% threshold
    assert len(result.quality_issues) == 1
    assert "Coverage 65.0% below threshold 80.0%" in result.quality_issues[0]


@pytest.mark.asyncio
async def test_coverage_analysis_with_custom_threshold(
    default_config,
    workflow_context,
    mock_pytest_expert,
    mock_pytest_result_low_coverage,
):
    """Test coverage analysis with custom threshold."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_low_coverage

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    # Lower threshold to 60% - should pass now
    operation = QualityOperation(operation="coverage_analysis", coverage_threshold=60.0)

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.quality_gate_passed  # 65% > 60% threshold
    assert len(result.quality_issues) == 0


@pytest.mark.asyncio
async def test_coverage_analysis_test_failure(
    default_config, workflow_context, mock_pytest_expert, mock_pytest_result_failure
):
    """Test coverage analysis when tests fail."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_failure

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="coverage_analysis")

    result = await manager.execute(operation, workflow_context)

    assert not result.success
    assert "Test execution failed" in result.error
    assert result.test_results["failed"] == 5


# ============================================================================
# Test Quality Gate
# ============================================================================


@pytest.mark.asyncio
async def test_quality_gate_pass(
    default_config, workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test quality gate with passing coverage and no failures."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="quality_gate")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.operation == "quality_gate"
    assert result.quality_gate_passed
    assert len(result.quality_issues) == 0


@pytest.mark.asyncio
async def test_quality_gate_fail_coverage(
    default_config,
    workflow_context,
    mock_pytest_expert,
    mock_pytest_result_low_coverage,
):
    """Test quality gate fails on low coverage."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_low_coverage

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="quality_gate")

    result = await manager.execute(operation, workflow_context)

    assert result.success  # Operation succeeded
    assert not result.quality_gate_passed  # But gate failed
    assert len(result.quality_issues) == 1
    assert "Coverage 65.0% below threshold 80.0%" in result.quality_issues[0]


@pytest.mark.asyncio
async def test_quality_gate_fail_test_failures(
    default_config, workflow_context, mock_pytest_expert
):
    """Test quality gate fails on test failures."""
    # Create result with good coverage but test failures
    pytest_result = PyTestResult(
        success=True,
        operation="run_tests",
        data={
            "total_tests": 50,
            "passed": 47,
            "failed": 3,
            "skipped": 0,
            "duration_seconds": 12.5,
            "exit_code": 0,
            "coverage": {
                "total_coverage": "85.0%",
                "covered_lines": 850,
                "total_lines": 1000,
                "modules": {},
            },
        },
        error=None,
    )

    mock_pytest_expert.execute.return_value = pytest_result

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="quality_gate")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert not result.quality_gate_passed  # 3 failures > max_failures (0)
    assert len(result.quality_issues) == 1
    assert "Failed tests (3) exceeds maximum (0)" in result.quality_issues[0]


@pytest.mark.asyncio
async def test_quality_gate_multiple_issues(
    default_config,
    workflow_context,
    mock_pytest_expert,
):
    """Test quality gate with both coverage and failure issues."""
    # Create result with low coverage AND test failures
    pytest_result = PyTestResult(
        success=True,
        operation="run_tests",
        data={
            "total_tests": 50,
            "passed": 47,
            "failed": 3,
            "skipped": 0,
            "duration_seconds": 12.5,
            "exit_code": 0,
            "coverage": {
                "total_coverage": "70.0%",  # Below 80% threshold
                "covered_lines": 700,
                "total_lines": 1000,
                "modules": {},
            },
        },
        error=None,
    )

    mock_pytest_expert.execute.return_value = pytest_result

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="quality_gate")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert not result.quality_gate_passed
    assert len(result.quality_issues) == 2  # Both issues present
    assert any("Coverage" in issue for issue in result.quality_issues)
    assert any("Failed tests" in issue for issue in result.quality_issues)


# ============================================================================
# Test Report Generation
# ============================================================================


@pytest.mark.asyncio
async def test_generate_report_json(
    default_config, workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test JSON report generation."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="generate_report", output_format="json")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.operation == "generate_report"
    assert result.report_path is not None
    assert ".json" in result.report_path
    assert Path(result.report_path).exists()

    # Cleanup
    Path(result.report_path).unlink()
    Path(result.report_path).parent.rmdir()


@pytest.mark.asyncio
async def test_generate_report_html(
    default_config, workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test HTML report generation."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="generate_report", output_format="html")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.report_path is not None
    assert ".html" in result.report_path
    assert Path(result.report_path).exists()

    # Verify HTML content
    content = Path(result.report_path).read_text()
    assert "<!DOCTYPE html>" in content
    assert "Quality Report" in content

    # Cleanup
    Path(result.report_path).unlink()
    Path(result.report_path).parent.rmdir()


@pytest.mark.asyncio
async def test_generate_report_xml(
    default_config, workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test XML report generation."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="generate_report", output_format="xml")

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.report_path is not None
    assert ".xml" in result.report_path
    assert Path(result.report_path).exists()

    # Verify XML content
    content = Path(result.report_path).read_text()
    assert "<?xml version" in content
    assert "<quality-report>" in content

    # Cleanup
    Path(result.report_path).unlink()
    Path(result.report_path).parent.rmdir()


# ============================================================================
# Test Configuration Options
# ============================================================================


@pytest.mark.asyncio
async def test_custom_test_strategy(
    workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test using custom test strategy."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    config = QualityManagerConfig(pytest_executable="uv", default_test_strategy="fast")

    manager = QualityManager(config=config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(
        operation="coverage_analysis",
        test_strategy="thorough",  # Override config
    )

    result = await manager.execute(operation, workflow_context)

    assert result.success
    # Verify pytest expert was called with thorough strategy
    call_args = mock_pytest_expert.execute.call_args
    pytest_operation = call_args[0][0]
    assert pytest_operation.operation == "run_tests"
    assert pytest_operation.params["strategy"] == "thorough"


@pytest.mark.asyncio
async def test_custom_max_failures(
    workflow_context, mock_pytest_expert, mock_pytest_result_success
):
    """Test custom max_failures threshold."""
    mock_pytest_expert.execute.return_value = mock_pytest_result_success

    config = QualityManagerConfig(max_failures=5)  # Allow up to 5 failures

    manager = QualityManager(config=config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="quality_gate", max_failures=10)

    result = await manager.execute(operation, workflow_context)

    assert result.success
    assert result.quality_gate_passed  # 0 failures < 10 max


# ============================================================================
# Test Integration
# ============================================================================


@pytest.mark.asyncio
async def test_integration_with_pytest_expert(default_config, workflow_context):
    """Test QualityManager integration with real PyTestExpert."""
    # Use real PyTestExpert (not mocked)
    manager = QualityManager(config=default_config)

    operation = QualityOperation(
        operation="coverage_analysis",
        test_path="tests/unit/",  # Non-existent path for testing
    )

    # This will call real pytest expert which should handle gracefully
    result = await manager.execute(operation, workflow_context)

    # Result depends on whether tests/unit/ exists
    # But operation should complete without crashing
    assert result.operation == "coverage_analysis"


# ============================================================================
# Test Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_error_handling_pytest_expert_failure(
    default_config, workflow_context, mock_pytest_expert
):
    """Test error handling when PyTestExpert fails."""
    mock_pytest_expert.execute.side_effect = Exception("PyTest expert crashed")

    manager = QualityManager(config=default_config, pytest_expert=mock_pytest_expert)

    operation = QualityOperation(operation="coverage_analysis")

    # Should not raise, should return error result
    with pytest.raises(Exception, match="PyTest expert crashed"):
        await manager.execute(operation, workflow_context)


@pytest.mark.asyncio
async def test_close_manager(default_config):
    """Test QualityManager cleanup."""
    manager = QualityManager(config=default_config)

    # Should not raise
    manager.close()
