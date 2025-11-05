"""
Tests for CICDManager - L2 Domain Manager.

Comprehensive test coverage for:
- Initialization with custom and default configs
- Operation validation
- All workflow types (full CI/CD, tests only, build only, PR only)
- Configuration options (auto_merge, comment_on_pr, test strategies)
- Multi-expert coordination
- Error handling and rollback
- Resource cleanup
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.managers import CICDManager, CICDManagerConfig
from tta_agent_coordination.managers.cicd_manager import CICDOperation
from tta_agent_coordination.wrappers.docker_wrapper import DockerResult
from tta_agent_coordination.wrappers.github_wrapper import GitHubResult
from tta_agent_coordination.wrappers.pytest_wrapper import PyTestResult


@pytest.fixture
def context():
    """Create workflow context for testing."""
    return WorkflowContext(correlation_id="test-123")


@pytest.fixture
def config():
    """Create CICDManager config for testing."""
    return CICDManagerConfig(
        github_token="test-token",
        github_repo="test-org/test-repo",
        docker_base_url="unix://var/run/docker.sock",
        pytest_executable="pytest",
        test_strategy="thorough",
        auto_merge=False,
        comment_on_pr=True,
    )


@pytest.fixture
def manager(config):
    """Create CICDManager instance with mocked experts."""
    with (
        patch("tta_agent_coordination.managers.cicd_manager.GitHubExpert") as mock_gh,
        patch("tta_agent_coordination.managers.cicd_manager.PyTestExpert") as mock_pt,
        patch("tta_agent_coordination.managers.cicd_manager.DockerExpert") as mock_dk,
    ):
        manager = CICDManager(config=config)

        # Store mocked experts for assertions
        manager._github = mock_gh.return_value
        manager._pytest = mock_pt.return_value
        manager._docker = mock_dk.return_value

        # Configure execute methods as AsyncMock
        manager._github.execute = AsyncMock()
        manager._pytest.execute = AsyncMock()
        manager._docker.execute = AsyncMock()

        # Configure close methods
        manager._github.close = MagicMock()
        manager._pytest.close = MagicMock()
        manager._docker.close = MagicMock()

        yield manager


# ============================================================================
# Initialization Tests
# ============================================================================


class TestCICDManagerInitialization:
    """Test CICDManager initialization."""

    @pytest.mark.asyncio
    async def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = CICDManagerConfig(
            github_token="custom-token",
            github_repo="custom-org/custom-repo",
            github_base_url="https://api.github.com",
            docker_base_url="unix://var/run/docker.sock",  # Use unix socket, not TCP
            pytest_executable="python",
            test_strategy="fast",
            auto_merge=True,
            comment_on_pr=False,
        )

        with (
            patch("tta_agent_coordination.managers.cicd_manager.GitHubExpert"),
            patch("tta_agent_coordination.managers.cicd_manager.PyTestExpert"),
            patch("tta_agent_coordination.managers.cicd_manager.DockerExpert"),
        ):
            manager = CICDManager(config=config)

            assert manager.config.github_token == "custom-token"
            assert manager.config.github_repo == "custom-org/custom-repo"
            assert manager.config.test_strategy == "fast"
            assert manager.config.auto_merge is True
            assert manager.config.comment_on_pr is False

    @pytest.mark.asyncio
    async def test_init_with_default_config(self):
        """Test initialization with default configuration values."""
        config = CICDManagerConfig(github_token="token", github_repo="org/repo")

        manager = CICDManager(config=config)

        assert manager.config.github_base_url == "https://api.github.com"
        assert manager.config.docker_base_url == "unix://var/run/docker.sock"
        assert manager.config.pytest_executable == "pytest"
        assert manager.config.test_strategy == "thorough"
        assert manager.config.auto_merge is False
        assert manager.config.comment_on_pr is True


# ============================================================================
# Validation Tests
# ============================================================================


class TestCICDManagerValidation:
    """Test operation validation."""

    @pytest.mark.asyncio
    async def test_invalid_operation_type(self, manager, context):
        """Test validation fails for invalid operation type."""
        operation = CICDOperation(
            operation="invalid_operation",
            branch="feature-branch",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert "Invalid operation" in result.error or "Unknown" in result.error

    @pytest.mark.asyncio
    async def test_missing_required_branch(self, manager, context):
        """Test validation fails when branch is missing."""
        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="",  # Empty branch
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_create_pr_missing_title(self, manager, context):
        """Test validation fails when PR title is missing."""
        operation = CICDOperation(
            operation="create_pr",
            branch="feature-branch",
            create_pr=True,
            pr_title="",  # Empty title
            pr_body="Description",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.error is not None


# ============================================================================
# Workflow Tests - run_cicd_workflow
# ============================================================================


class TestRunCICDWorkflow:
    """Test run_cicd_workflow execution."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, manager, context):
        """Test successful full CI/CD workflow: test → build → PR."""
        # Mock successful test execution
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 10, "passed": 10, "failed": 0, "duration": 5.2},
        )

        # Mock successful Docker build
        manager._docker.execute.return_value = DockerResult(
            success=True,
            operation="build_image",
            data={"image_id": "sha256:abc123"},
        )

        # Mock successful PR creation
        manager._github.execute.return_value = GitHubResult(
            success=True,
            operation="create_pr",
            data={"pr_number": 42, "html_url": "https://github.com/org/repo/pull/42"},
        )

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature-branch",
            create_pr=True,
            pr_title="Add feature",
            pr_body="Feature description",
        )

        result = await manager.execute(operation, context)

        assert result.success is True
        assert result.test_results is not None
        assert result.docker_results is not None
        assert result.pr_number == 42
        assert result.pr_url == "https://github.com/org/repo/pull/42"

        # Verify all experts were called
        assert manager._pytest.execute.called
        assert manager._docker.execute.called
        assert manager._github.execute.call_count == 2  # create_pr + add_comment

    @pytest.mark.asyncio
    async def test_workflow_test_failure_stops_build(self, manager, context):
        """Test workflow stops at test failure, doesn't build."""
        # Mock failed test execution
        manager._pytest.execute.return_value = PyTestResult(
            success=False,
            operation="run_tests",
            data={"total": 10, "passed": 8, "failed": 2, "duration": 5.2},
            error="2 tests failed",
        )

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature-branch",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.test_results is not None
        assert result.docker_results is None  # Build never ran
        assert "test" in result.error.lower() or "failed" in result.error.lower()

        # Verify only pytest was called
        assert manager._pytest.execute.called
        assert not manager._docker.execute.called
        assert not manager._github.execute.called

    @pytest.mark.asyncio
    async def test_workflow_build_failure(self, manager, context):
        """Test workflow handles Docker build failure."""
        # Mock successful test execution
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 10, "passed": 10, "failed": 0, "duration": 5.2},
        )

        # Mock failed Docker build
        manager._docker.execute.return_value = DockerResult(
            success=False,
            operation="build_image",
            error="Build failed: Dockerfile not found",
        )

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature-branch",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.test_results is not None
        assert result.docker_results is not None
        assert "build" in result.error.lower() or "docker" in result.error.lower()

        # Verify test and build were called, but not PR
        assert manager._pytest.execute.called
        assert manager._docker.execute.called
        assert not manager._github.execute.called

    @pytest.mark.asyncio
    async def test_workflow_without_pr_creation(self, manager, context):
        """Test workflow without PR creation."""
        # Mock successful test execution
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 10, "passed": 10, "failed": 0, "duration": 5.2},
        )

        # Mock successful Docker build
        manager._docker.execute.return_value = DockerResult(
            success=True,
            operation="build_image",
            data={"image_id": "sha256:abc123"},
        )

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature-branch",
            create_pr=False,  # No PR
        )

        result = await manager.execute(operation, context)

        assert result.success is True
        assert result.test_results is not None
        assert result.docker_results is not None
        assert result.pr_number is None
        assert result.pr_url is None

        # Verify test and build were called, but not PR
        assert manager._pytest.execute.called
        assert manager._docker.execute.called
        assert not manager._github.execute.called

    @pytest.mark.asyncio
    async def test_workflow_pr_creation_failure(self, manager, context):
        """Test workflow handles PR creation failure gracefully."""
        # Mock successful test execution
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 10, "passed": 10, "failed": 0, "duration": 5.2},
        )

        # Mock successful Docker build
        manager._docker.execute.return_value = DockerResult(
            success=True,
            operation="build_image",
            data={"image_id": "sha256:abc123"},
        )

        # Mock failed PR creation
        manager._github.execute.return_value = GitHubResult(
            success=False,
            operation="create_pr",
            error="PR already exists",
        )

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature-branch",
            create_pr=True,
            pr_title="Add feature",
            pr_body="Description",
        )

        result = await manager.execute(operation, context)

        # Workflow succeeds even if PR creation fails (tests and build passed)
        assert result.success is True
        assert result.test_results is not None
        assert result.docker_results is not None
        assert "pr_creation_error" in result.metadata


# ============================================================================
# Workflow Tests - run_tests_only
# ============================================================================


class TestRunTestsOnly:
    """Test run_tests_only workflow."""

    @pytest.mark.asyncio
    async def test_tests_only_success(self, manager, context):
        """Test successful test-only execution."""
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 25, "passed": 25, "failed": 0, "duration": 12.5},
        )

        operation = CICDOperation(
            operation="run_tests_only",
            branch="feature-branch",
            test_path="tests/unit/",
        )

        result = await manager.execute(operation, context)

        assert result.success is True
        assert result.test_results is not None
        assert result.test_results["total_tests"] == 25
        assert result.test_results["passed"] == 25
        assert result.docker_results is None
        assert result.pr_number is None

        # Verify only pytest was called
        assert manager._pytest.execute.called
        assert not manager._docker.execute.called
        assert not manager._github.execute.called

    @pytest.mark.asyncio
    async def test_tests_only_failure(self, manager, context):
        """Test test-only execution with failures."""
        manager._pytest.execute.return_value = PyTestResult(
            success=False,
            operation="run_tests",
            data={"total": 25, "passed": 20, "failed": 5, "duration": 12.5},
            error="5 tests failed",
        )

        operation = CICDOperation(
            operation="run_tests_only",
            branch="feature-branch",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.test_results is not None
        assert result.test_results["failed"] == 5
        assert "failed" in result.error.lower()


# ============================================================================
# Workflow Tests - build_only
# ============================================================================


class TestBuildOnly:
    """Test build_only workflow."""

    @pytest.mark.asyncio
    async def test_build_only_success(self, manager, context):
        """Test successful build-only execution."""
        manager._docker.execute.return_value = DockerResult(
            success=True,
            operation="build_image",
            data={"image_id": "sha256:def456"},
        )

        operation = CICDOperation(
            operation="build_only",
            branch="feature-branch",
            dockerfile_path="docker/Dockerfile",
            image_name="myapp:feature",
        )

        result = await manager.execute(operation, context)

        assert result.success is True
        assert result.docker_results is not None
        assert result.docker_results["image_name"] == "myapp:feature"
        assert result.docker_results["image_id"] == "sha256:def456"
        assert result.test_results is None
        assert result.pr_number is None

        # Verify only docker was called
        assert manager._docker.execute.called
        assert not manager._pytest.execute.called
        assert not manager._github.execute.called

    @pytest.mark.asyncio
    async def test_build_only_failure(self, manager, context):
        """Test build-only execution with failure."""
        manager._docker.execute.return_value = DockerResult(
            success=False,
            operation="build_image",
            error="Dockerfile syntax error",
        )

        operation = CICDOperation(
            operation="build_only",
            branch="feature-branch",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.docker_results is not None
        assert "build" in result.error.lower() or "docker" in result.error.lower()


# ============================================================================
# Workflow Tests - create_pr
# ============================================================================


class TestCreatePRWorkflow:
    """Test create_pr workflow."""

    @pytest.mark.asyncio
    async def test_create_pr_success(self, manager, context):
        """Test successful PR creation."""
        manager._github.execute.return_value = GitHubResult(
            success=True,
            operation="create_pr",
            data={"pr_number": 99, "html_url": "https://github.com/org/repo/pull/99"},
        )

        operation = CICDOperation(
            operation="create_pr",
            branch="feature-branch",
            pr_title="Add amazing feature",
            pr_body="This PR adds amazing feature",
            base_branch="main",
        )

        result = await manager.execute(operation, context)

        assert result.success is True
        assert result.pr_number == 99
        assert result.pr_url == "https://github.com/org/repo/pull/99"
        assert result.test_results is None
        assert result.docker_results is None

        # Verify only github was called
        assert manager._github.execute.called
        assert not manager._pytest.execute.called
        assert not manager._docker.execute.called

    @pytest.mark.asyncio
    async def test_create_pr_failure(self, manager, context):
        """Test PR creation failure."""
        manager._github.execute.return_value = GitHubResult(
            success=False,
            operation="create_pr",
            error="Branch does not exist",
        )

        operation = CICDOperation(
            operation="create_pr",
            branch="nonexistent-branch",
            pr_title="Add feature",
            pr_body="Description",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert "failed" in result.error.lower() or "PR" in result.error


# ============================================================================
# Configuration Tests
# ============================================================================


class TestCICDManagerConfiguration:
    """Test configuration options."""

    @pytest.mark.asyncio
    async def test_comment_on_pr_enabled(self, context):
        """Test that comments are posted to PR when enabled."""
        config = CICDManagerConfig(
            github_token="token",
            github_repo="org/repo",
            comment_on_pr=True,
        )

        with (
            patch(
                "tta_agent_coordination.managers.cicd_manager.GitHubExpert"
            ) as mock_gh,
            patch(
                "tta_agent_coordination.managers.cicd_manager.PyTestExpert"
            ) as mock_pt,
            patch(
                "tta_agent_coordination.managers.cicd_manager.DockerExpert"
            ) as mock_dk,
        ):
            manager = CICDManager(config=config)
            manager._github = mock_gh.return_value
            manager._pytest = mock_pt.return_value
            manager._docker = mock_dk.return_value

            manager._github.execute = AsyncMock()
            manager._pytest.execute = AsyncMock()
            manager._docker.execute = AsyncMock()

            # Mock responses
            manager._pytest.execute.return_value = PyTestResult(
                success=True,
                operation="run_tests",
                data={"total": 10, "passed": 10, "failed": 0, "duration": 5.0},
            )

            manager._docker.execute.return_value = DockerResult(
                success=True, operation="build_image", data={"image_id": "sha256:abc"}
            )

            manager._github.execute.return_value = GitHubResult(
                success=True,
                operation="create_pr",
                data={
                    "pr_number": 42,
                    "html_url": "https://github.com/org/repo/pull/42",
                },
            )

            operation = CICDOperation(
                operation="run_cicd_workflow",
                branch="feature",
                create_pr=True,
                pr_title="Title",
                pr_body="Body",
            )

            await manager.execute(operation, context)

            # Should call execute twice: create_pr + add_comment
            assert manager._github.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_comment_on_pr_disabled(self, context):
        """Test that comments are NOT posted when disabled."""
        config = CICDManagerConfig(
            github_token="token",
            github_repo="org/repo",
            comment_on_pr=False,  # Disabled
        )

        with (
            patch(
                "tta_agent_coordination.managers.cicd_manager.GitHubExpert"
            ) as mock_gh,
            patch(
                "tta_agent_coordination.managers.cicd_manager.PyTestExpert"
            ) as mock_pt,
            patch(
                "tta_agent_coordination.managers.cicd_manager.DockerExpert"
            ) as mock_dk,
        ):
            manager = CICDManager(config=config)
            manager._github = mock_gh.return_value
            manager._pytest = mock_pt.return_value
            manager._docker = mock_dk.return_value

            manager._github.execute = AsyncMock()
            manager._pytest.execute = AsyncMock()
            manager._docker.execute = AsyncMock()

            # Mock responses
            manager._pytest.execute.return_value = PyTestResult(
                success=True,
                operation="run_tests",
                data={"total": 10, "passed": 10, "failed": 0, "duration": 5.0},
            )

            manager._docker.execute.return_value = DockerResult(
                success=True, operation="build_image", data={"image_id": "sha256:abc"}
            )

            manager._github.execute.return_value = GitHubResult(
                success=True,
                operation="create_pr",
                data={
                    "pr_number": 42,
                    "html_url": "https://github.com/org/repo/pull/42",
                },
            )

            operation = CICDOperation(
                operation="run_cicd_workflow",
                branch="feature",
                create_pr=True,
                pr_title="Title",
                pr_body="Body",
            )

            await manager.execute(operation, context)

            # Should call execute only once: create_pr (no comment)
            assert manager._github.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_custom_test_strategy(self, context):
        """Test using custom test strategy."""
        config = CICDManagerConfig(
            github_token="token",
            github_repo="org/repo",
            test_strategy="fast",  # Custom strategy
        )

        with (
            patch(
                "tta_agent_coordination.managers.cicd_manager.GitHubExpert"
            ) as mock_gh,
            patch(
                "tta_agent_coordination.managers.cicd_manager.PyTestExpert"
            ) as mock_pt,
            patch(
                "tta_agent_coordination.managers.cicd_manager.DockerExpert"
            ) as mock_dk,
        ):
            manager = CICDManager(config=config)
            manager._github = mock_gh.return_value
            manager._pytest = mock_pt.return_value
            manager._docker = mock_dk.return_value

            manager._pytest.execute = AsyncMock()
            manager._pytest.execute.return_value = PyTestResult(
                success=True,
                operation="run_tests",
                data={"total": 5, "passed": 5, "failed": 0, "duration": 2.0},
            )

            operation = CICDOperation(
                operation="run_tests_only",
                branch="feature",
                test_strategy="fast",  # Overrides config
            )

            await manager.execute(operation, context)

            # Verify pytest was called with correct strategy
            call_args = manager._pytest.execute.call_args
            pytest_operation = call_args[0][0]
            assert pytest_operation.params["strategy"] == "fast"


# ============================================================================
# Integration & Error Handling Tests
# ============================================================================


class TestCICDManagerIntegration:
    """Test multi-expert coordination and error handling."""

    @pytest.mark.asyncio
    async def test_exception_handling(self, manager, context):
        """Test workflow handles exceptions gracefully."""
        # Make pytest raise an exception
        manager._pytest.execute.side_effect = Exception("Unexpected error")

        operation = CICDOperation(
            operation="run_tests_only",
            branch="feature-branch",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert "failed" in result.error.lower() or "error" in result.error.lower()

    @pytest.mark.asyncio
    async def test_close_cleans_up_experts(self, manager):
        """Test close() method cleans up all expert connections."""
        manager.close()

        # Verify all experts were closed
        manager._github.close.assert_called_once()
        manager._pytest.close.assert_called_once()
        manager._docker.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_expert_coordination_success(self, manager, context):
        """Test successful coordination across all three experts."""
        # Mock all experts returning success
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 15, "passed": 15, "failed": 0, "duration": 8.5},
        )

        manager._docker.execute.return_value = DockerResult(
            success=True,
            operation="build_image",
            data={"image_id": "sha256:xyz789"},
        )

        manager._github.execute.return_value = GitHubResult(
            success=True,
            operation="create_pr",
            data={
                "pr_number": 123,
                "html_url": "https://github.com/test/repo/pull/123",
            },
        )

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="epic-feature",
            create_pr=True,
            pr_title="Epic Feature",
            pr_body="This is an epic feature",
        )

        result = await manager.execute(operation, context)

        # Verify full coordination
        assert result.success is True
        assert result.test_results is not None
        assert result.docker_results is not None
        assert result.pr_number == 123
        assert result.branch == "epic-feature"
        assert result.operation == "run_cicd_workflow"

        # All experts were used
        assert manager._pytest.execute.called
        assert manager._docker.execute.called
        assert manager._github.execute.called

    @pytest.mark.asyncio
    async def test_error_in_middle_of_workflow(self, manager, context):
        """Test error handling when failure occurs mid-workflow."""
        # Test passes
        manager._pytest.execute.return_value = PyTestResult(
            success=True,
            operation="run_tests",
            data={"total": 10, "passed": 10, "failed": 0, "duration": 5.0},
        )

        # Build fails
        manager._docker.execute.side_effect = Exception("Docker daemon not running")

        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature",
        )

        result = await manager.execute(operation, context)

        assert result.success is False
        assert result.test_results is not None  # Tests ran
        assert result.error is not None  # Error captured

        # pytest ran, docker failed, github never called
        assert manager._pytest.execute.called
        assert manager._docker.execute.called
        assert not manager._github.execute.called
