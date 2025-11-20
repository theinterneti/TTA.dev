"""Tests for CICDManager."""

from unittest.mock import AsyncMock

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.experts.docker_expert import DockerResult
from tta_agent_coordination.experts.github_expert import GitHubResult
from tta_agent_coordination.experts.pytest_expert import PyTestResult
from tta_agent_coordination.managers.cicd_manager import (
    CICDManager,
    CICDOperation,
    CICDOperationType,
)


@pytest.fixture
def mock_experts(mocker):
    """Mock the internal experts of CICDManager."""
    # We patch the classes so when CICDManager instantiates them, it gets mocks
    mock_github_cls = mocker.patch(
        "tta_agent_coordination.managers.cicd_manager.GitHubExpert"
    )
    mock_docker_cls = mocker.patch(
        "tta_agent_coordination.managers.cicd_manager.DockerExpert"
    )
    mock_pytest_cls = mocker.patch(
        "tta_agent_coordination.managers.cicd_manager.PyTestExpert"
    )

    mock_github = mock_github_cls.return_value
    mock_docker = mock_docker_cls.return_value
    mock_pytest = mock_pytest_cls.return_value

    # Setup default async return values
    mock_github.execute = AsyncMock()
    mock_docker.execute = AsyncMock()
    mock_pytest.execute = AsyncMock()

    return mock_github, mock_docker, mock_pytest


@pytest.mark.asyncio
async def test_build_and_test_success(mock_experts):
    """Test build_and_test operation success path."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup success responses
    mock_docker.execute.return_value = DockerResult(
        success=True, operation="build_image", data={"id": "sha256:123"}
    )
    mock_pytest.execute.return_value = PyTestResult(
        success=True, operation="run_tests", data={"passed": 10}
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="build_and_test", params={"build_path": ".", "test_path": "tests/"}
    )

    result = await manager.execute(op, context)

    assert result.success
    assert result.operation == "build_and_test"
    assert mock_docker.execute.called
    assert mock_pytest.execute.called


@pytest.mark.asyncio
async def test_build_and_test_build_fail(mock_experts):
    """Test build_and_test fails when build fails."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup build failure
    mock_docker.execute.return_value = DockerResult(
        success=False, operation="build_image", error="Build failed"
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(operation="build_and_test", params={})

    result = await manager.execute(op, context)

    assert not result.success
    assert "Build failed" in str(result.error)
    assert mock_docker.execute.called
    assert not mock_pytest.execute.called  # Should not run tests if build fails


@pytest.mark.asyncio
async def test_build_and_test_test_fail(mock_experts):
    """Test build_and_test fails when tests fail."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup build success, test failure
    mock_docker.execute.return_value = DockerResult(
        success=True, operation="build_image", data={"id": "sha256:123"}
    )
    mock_pytest.execute.return_value = PyTestResult(
        success=False, operation="run_tests", error="Tests failed"
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="build_and_test", params={"build_path": ".", "test_path": "tests/"}
    )

    result = await manager.execute(op, context)

    assert not result.success
    assert "Tests failed" in str(result.error)
    assert mock_docker.execute.called
    assert mock_pytest.execute.called


@pytest.mark.asyncio
async def test_validate_pr_success(mock_experts):
    """Test validate_pr success path."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup responses
    mock_pytest.execute.return_value = PyTestResult(
        success=True, operation="run_tests", data={"output": "10 passed"}
    )
    mock_github.execute.return_value = GitHubResult(
        success=True, operation="add_comment", data={"url": "http://github.com/..."}
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="validate_pr",
        params={"pr_number": 123, "repo_name": "org/repo"},
    )

    result = await manager.execute(op, context)

    assert result.success
    assert result.operation == "validate_pr"
    assert mock_pytest.execute.called
    assert mock_github.execute.called

    # Verify comment was posted
    call_args = mock_github.execute.call_args
    assert call_args is not None
    op_arg = call_args[0][0]
    assert op_arg.operation == "add_comment"
    assert "PASSED" in op_arg.params["body"]


@pytest.mark.asyncio
async def test_run_pipeline_success(mock_experts):
    """Test full pipeline success."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup responses
    mock_docker.execute.return_value = DockerResult(
        success=True, operation="build_image"
    )
    mock_pytest.execute.return_value = PyTestResult(success=True, operation="run_tests")
    mock_github.execute.return_value = GitHubResult(
        success=True, operation="add_comment"
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="run_pipeline",
        params={"pr_number": 123, "repo_name": "org/repo"},
    )

    result = await manager.execute(op, context)

    assert result.success
    assert mock_docker.execute.called
    assert mock_pytest.execute.called
    assert mock_github.execute.called  # Should report success


@pytest.mark.asyncio
async def test_run_pipeline_failure_reporting(mock_experts):
    """Test pipeline reports failure to GitHub."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup build failure
    mock_docker.execute.return_value = DockerResult(
        success=False, operation="build_image", error="Build error"
    )
    mock_github.execute.return_value = GitHubResult(
        success=True, operation="add_comment"
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="run_pipeline",
        params={"pr_number": 123, "repo_name": "org/repo"},
    )

    result = await manager.execute(op, context)

    assert not result.success
    assert mock_docker.execute.called
    assert mock_github.execute.called  # Should report failure

    # Verify failure comment
    call_args = mock_github.execute.call_args
    op_arg = call_args[0][0]
    assert "Pipeline Failed" in op_arg.params["body"]
    assert "Build error" in op_arg.params["body"]


@pytest.mark.asyncio
async def test_unknown_operation(mock_experts):
    """Test unknown operation handling."""
    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(operation="unknown_op", params={})

    result = await manager.execute(op, context)

    assert not result.success
    assert "Unknown operation" in str(result.error)


@pytest.mark.asyncio
async def test_enum_operation(mock_experts):
    """Test using Enum for operation type."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup success
    mock_docker.execute.return_value = DockerResult(
        success=True, operation="build_image"
    )
    mock_pytest.execute.return_value = PyTestResult(success=True, operation="run_tests")

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation=CICDOperationType.BUILD_AND_TEST, params={"build_path": "."}
    )

    result = await manager.execute(op, context)

    assert result.success
    assert result.operation == "build_and_test"


@pytest.mark.asyncio
async def test_validate_pr_missing_params(mock_experts):
    """Test validate_pr with missing parameters."""
    manager = CICDManager()
    context = WorkflowContext()

    # Missing pr_number
    op = CICDOperation(operation="validate_pr", params={"repo_name": "org/repo"})
    result = await manager.execute(op, context)
    assert not result.success
    assert "Missing pr_number" in str(result.error)

    # Missing repo_name
    op = CICDOperation(operation="validate_pr", params={"pr_number": 123})
    result = await manager.execute(op, context)
    assert not result.success
    assert "Missing pr_number" in str(result.error)


@pytest.mark.asyncio
async def test_validate_pr_comment_failure(mock_experts):
    """Test validate_pr fails when comment posting fails."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Setup tests pass but comment fails
    mock_pytest.execute.return_value = PyTestResult(
        success=True, operation="run_tests", data={"output": "passed"}
    )
    mock_github.execute.return_value = GitHubResult(
        success=False, operation="add_comment", error="API Error"
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="validate_pr",
        params={"pr_number": 123, "repo_name": "org/repo"},
    )

    result = await manager.execute(op, context)

    assert not result.success
    assert "Failed to post comment" in str(result.error)
    assert "API Error" in str(result.error)


def test_close(mock_experts):
    """Test close method closes all experts."""
    mock_github, mock_docker, mock_pytest = mock_experts

    manager = CICDManager()
    manager.close()

    assert mock_github.close.called
    assert mock_docker.close.called
    assert mock_pytest.close.called


@pytest.mark.asyncio
async def test_validate_pr_missing_output_data(mock_experts):
    """Test validate_pr handles missing test output gracefully."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Test result data is None (edge case)
    mock_pytest.execute.return_value = PyTestResult(
        success=True, operation="run_tests", data=None
    )
    mock_github.execute.return_value = GitHubResult(
        success=True, operation="add_comment", data={"url": "http://github.com/..."}
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="validate_pr",
        params={"pr_number": 456, "repo_name": "test/repo"},
    )

    result = await manager.execute(op, context)

    assert result.success
    # Verify fallback message is used
    call_args = mock_github.execute.call_args
    op_arg = call_args[0][0]
    assert "No output available" in op_arg.params["body"]


@pytest.mark.asyncio
async def test_validate_pr_empty_output_dict(mock_experts):
    """Test validate_pr handles empty data dict gracefully."""
    mock_github, mock_docker, mock_pytest = mock_experts

    # Test result data exists but no 'output' key (edge case)
    mock_pytest.execute.return_value = PyTestResult(
        success=False, operation="run_tests", data={"passed": 0, "failed": 5}
    )
    mock_github.execute.return_value = GitHubResult(
        success=True, operation="add_comment"
    )

    manager = CICDManager()
    context = WorkflowContext()

    op = CICDOperation(
        operation="validate_pr",
        params={"pr_number": 789, "repo_name": "test/repo2"},
    )

    result = await manager.execute(op, context)

    assert not result.success  # Tests failed
    # Verify fallback message is used when 'output' key missing
    call_args = mock_github.execute.call_args
    op_arg = call_args[0][0]
    assert "No output available" in op_arg.params["body"]
    assert "FAILED" in op_arg.params["body"]
