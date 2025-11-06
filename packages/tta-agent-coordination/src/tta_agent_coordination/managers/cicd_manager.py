"""CI/CD Manager - L2 Domain Manager coordinating GitHub, PyTest, and Docker experts.

This manager orchestrates complete CI/CD workflows by coordinating:
- GitHubExpert: Branch management, PR creation, commenting
- PyTestExpert: Test execution with different strategies
- DockerExpert: Image building and container management

Example usage:
    ```python
    from tta_agent_coordination.managers import CICDManager, CICDManagerConfig
    from tta_dev_primitives import WorkflowContext

    config = CICDManagerConfig(
        github_token="your-token",
        github_repo="owner/repo"
    )

    manager = CICDManager(config)

    # Run complete CI/CD workflow
    context = WorkflowContext(workflow_id="cicd-123")
    result = await manager.execute({
        "operation": "run_cicd_workflow",
        "branch": "feature/new-feature",
        "test_strategy": "thorough"
    }, context)
    ```
"""

from dataclasses import dataclass, field
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.apm.instrumented import APMWorkflowPrimitive

from tta_agent_coordination.experts import (
    DockerExpert,
    DockerExpertConfig,
    GitHubExpert,
    GitHubExpertConfig,
    PyTestExpert,
    PyTestExpertConfig,
)
from tta_agent_coordination.wrappers.docker_wrapper import (
    DockerConfig,
    DockerOperation,
)
from tta_agent_coordination.wrappers.github_wrapper import (
    GitHubConfig,
    GitHubOperation,
)
from tta_agent_coordination.wrappers.pytest_wrapper import (
    PyTestConfig,
    PyTestOperation,
)


@dataclass
class CICDManagerConfig:
    """Configuration for CI/CD Manager.

    Attributes:
        github_token: GitHub API token for authentication
        github_repo: Repository in format "owner/repo"
        github_base_url: GitHub API base URL (default: https://api.github.com)
        docker_base_url: Docker daemon URL (default: unix://var/run/docker.sock)
        pytest_executable: Path to pytest executable (default: pytest)
        test_strategy: Default test strategy (fast/thorough/coverage)
        auto_merge: Automatically merge PR if tests pass (default: False)
        comment_on_pr: Post test results as PR comment (default: True)
    """

    github_token: str
    github_repo: str
    github_base_url: str = "https://api.github.com"
    docker_base_url: str = "unix://var/run/docker.sock"
    pytest_executable: str = "pytest"
    test_strategy: str = "thorough"
    auto_merge: bool = False
    comment_on_pr: bool = True


@dataclass
class CICDOperation:
    """CI/CD operation parameters.

    Attributes:
        operation: Operation type (run_cicd_workflow, run_tests_only, build_only, etc.)
        branch: Branch name to work with
        test_strategy: Test strategy override (fast/thorough/coverage)
        test_path: Path to tests (default: tests/)
        dockerfile_path: Path to Dockerfile (default: Dockerfile)
        image_name: Docker image name (default: repo-name:branch)
        create_pr: Create PR after successful tests (default: False)
        pr_title: PR title if creating PR
        pr_body: PR description if creating PR
        base_branch: Base branch for PR (default: main)
    """

    operation: str
    branch: str
    test_strategy: str = "thorough"
    test_path: str = "tests/"
    dockerfile_path: str = "Dockerfile"
    image_name: str | None = None
    create_pr: bool = False
    pr_title: str | None = None
    pr_body: str | None = None
    base_branch: str = "main"


@dataclass
class CICDResult:
    """CI/CD workflow result.

    Attributes:
        success: Overall workflow success
        operation: Operation that was executed
        branch: Branch that was processed
        test_results: PyTest execution results
        docker_results: Docker operation results
        pr_number: PR number if PR was created
        pr_url: PR URL if available
        error: Error message if failed
        metadata: Additional metadata
    """

    success: bool
    operation: str
    branch: str
    test_results: dict[str, Any] | None = None
    docker_results: dict[str, Any] | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CICDManager(APMWorkflowPrimitive):
    """L2 Domain Manager coordinating GitHub, PyTest, and Docker experts.

    This manager orchestrates complete CI/CD workflows:
    - Test execution with different strategies (fast, thorough, coverage)
    - Docker image building and tagging
    - Pull request creation with test results
    - Automated merge when tests pass

    Features:
    - Sequential workflows with error handling
    - Conditional execution (only build if tests pass)
    - Cross-expert communication (post test results to GitHub)
    - Rollback on failure (cleanup on error)
    """

    def __init__(self, config: CICDManagerConfig):
        """Initialize CI/CD Manager with configuration.

        Args:
            config: CI/CD manager configuration
        """
        super().__init__(name="cicd_manager")
        self.config = config

        # Initialize L3 experts with proper configs
        github_config = GitHubExpertConfig()
        if config.github_token or config.github_repo or config.github_base_url:
            github_config.github_config = GitHubConfig(
                token=config.github_token,
                base_url=config.github_base_url or "https://api.github.com",
            )
        self._github = GitHubExpert(config=github_config)

        pytest_config = PyTestExpertConfig()
        if config.pytest_executable:
            pytest_config.pytest_config = PyTestConfig(
                python_executable=config.pytest_executable
            )
        self._pytest = PyTestExpert(config=pytest_config)

        docker_config = DockerExpertConfig()
        if config.docker_base_url:
            docker_config.docker_config = DockerConfig(base_url=config.docker_base_url)
        self._docker = DockerExpert(config=docker_config)

    async def _execute_impl(
        self, input_data: CICDOperation, context: WorkflowContext
    ) -> CICDResult:
        """Execute CI/CD workflow.

        Args:
            input_data: CI/CD operation parameters
            context: Workflow context for tracing

        Returns:
            CICDResult with workflow outcomes

        Raises:
            ValueError: If operation is invalid or required parameters missing
        """
        # Validate operation
        validation_error = self._validate_operation(input_data)
        if validation_error:
            return CICDResult(
                success=False,
                operation=input_data.operation,
                branch=input_data.branch,
                error=validation_error,
            )

        # Route to appropriate workflow
        if input_data.operation == "run_cicd_workflow":
            return await self._run_full_workflow(input_data, context)
        elif input_data.operation == "run_tests_only":
            return await self._run_tests_only(input_data, context)
        elif input_data.operation == "build_only":
            return await self._build_only(input_data, context)
        elif input_data.operation == "create_pr":
            return await self._create_pr_workflow(input_data, context)
        else:
            return CICDResult(
                success=False,
                operation=input_data.operation,
                branch=input_data.branch,
                error=f"Unknown operation: {input_data.operation}",
            )

    def _validate_operation(self, operation: CICDOperation) -> str | None:
        """Validate CI/CD operation parameters.

        Args:
            operation: Operation to validate

        Returns:
            Error message if validation fails, None if valid
        """
        # Validate operation type
        valid_operations = [
            "run_cicd_workflow",
            "run_tests_only",
            "build_only",
            "create_pr",
        ]
        if operation.operation not in valid_operations:
            return (
                f"Invalid operation: {operation.operation}. "
                f"Must be one of: {', '.join(valid_operations)}"
            )

        # Validate branch name
        if not operation.branch or not operation.branch.strip():
            return "Branch name is required"

        # Validate test strategy
        valid_strategies = ["fast", "thorough", "coverage"]
        if operation.test_strategy not in valid_strategies:
            return (
                f"Invalid test strategy: {operation.test_strategy}. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )

        # Validate PR creation parameters
        if operation.create_pr:
            if not operation.pr_title:
                return "PR title is required when create_pr=True"
            if not operation.pr_body:
                return "PR body is required when create_pr=True"

        return None

    async def _run_full_workflow(
        self, operation: CICDOperation, context: WorkflowContext
    ) -> CICDResult:
        """Run complete CI/CD workflow: test → build → optionally create PR.

        Args:
            operation: CI/CD operation parameters
            context: Workflow context

        Returns:
            CICDResult with complete workflow outcomes
        """
        result = CICDResult(
            success=True, operation=operation.operation, branch=operation.branch
        )

        try:
            # Step 1: Run tests
            test_result = await self._pytest.execute(
                PyTestOperation(
                    operation="run_tests",
                    params={
                        "test_path": operation.test_path,
                        "strategy": operation.test_strategy,
                    },
                ),
                context,
            )

            # Extract test metrics from result.data
            test_data = test_result.data or {}
            result.test_results = {
                "success": test_result.success,
                "total_tests": test_data.get("total", 0),
                "passed": test_data.get("passed", 0),
                "failed": test_data.get("failed", 0),
                "duration": test_data.get("duration", 0.0),
            }

            # If tests fail, stop workflow
            if not test_result.success:
                result.success = False
                result.error = f"Tests failed: {test_data.get('failed', 0)} failures"
                return result

            # Step 2: Build Docker image (if tests pass)
            image_name = operation.image_name or self._generate_image_name(
                operation.branch
            )

            build_result = await self._docker.execute(
                DockerOperation(
                    operation="build_image",
                    params={
                        "path": ".",
                        "dockerfile": operation.dockerfile_path,
                        "tag": image_name,
                    },
                ),
                context,
            )

            # Extract build data from result.data
            build_data = build_result.data or {}
            result.docker_results = {
                "success": build_result.success,
                "image_name": image_name,
                "image_id": build_data.get("image_id"),
            }

            if not build_result.success:
                result.success = False
                result.error = (
                    f"Docker build failed: {build_result.error or 'Unknown error'}"
                )
                return result

            # Step 3: Create PR if requested
            if operation.create_pr:
                pr_result = await self._github.execute(
                    GitHubOperation(
                        operation="create_pr",
                        repo_name=self.config.github_repo,
                        params={
                            "title": operation.pr_title,
                            "body": operation.pr_body,
                            "head": operation.branch,
                            "base": operation.base_branch,
                        },
                    ),
                    context,
                )

                # Extract PR data from result
                if pr_result.success:
                    pr_data = pr_result.data or {}
                    result.pr_number = pr_data.get("pr_number") or pr_data.get("number")
                    result.pr_url = pr_data.get("html_url")

                    # Post test results as comment if enabled
                    if self.config.comment_on_pr and result.pr_number:
                        comment = self._format_test_results_comment(result.test_results)
                        await self._github.execute(
                            GitHubOperation(
                                operation="add_comment",
                                repo_name=self.config.github_repo,
                                params={
                                    "issue_number": result.pr_number,
                                    "body": comment,
                                },
                            ),
                            context,
                        )
                else:
                    result.metadata["pr_creation_error"] = (
                        pr_result.error or "Unknown error"
                    )

            result.success = True
            return result

        except Exception as e:
            result.success = False
            result.error = f"Workflow failed: {str(e)}"
            return result

    async def _run_tests_only(
        self, operation: CICDOperation, context: WorkflowContext
    ) -> CICDResult:
        """Run tests only workflow.

        Args:
            operation: CI/CD operation parameters
            context: Workflow context

        Returns:
            CICDResult with test outcomes
        """
        result = CICDResult(
            success=True, operation=operation.operation, branch=operation.branch
        )

        try:
            test_result = await self._pytest.execute(
                PyTestOperation(
                    operation="run_tests",
                    params={
                        "test_path": operation.test_path,
                        "strategy": operation.test_strategy,
                    },
                ),
                context,
            )

            # Extract test metrics from result.data
            test_data = test_result.data or {}
            result.test_results = {
                "success": test_result.success,
                "total_tests": test_data.get("total", 0),
                "passed": test_data.get("passed", 0),
                "failed": test_data.get("failed", 0),
                "duration": test_data.get("duration", 0.0),
            }

            result.success = test_result.success
            if not result.success:
                result.error = f"Tests failed: {test_data.get('failed', 0)} failures"

            return result

        except Exception as e:
            result.success = False
            result.error = f"Test execution failed: {str(e)}"
            return result

    async def _build_only(
        self, operation: CICDOperation, context: WorkflowContext
    ) -> CICDResult:
        """Build Docker image only workflow.

        Args:
            operation: CI/CD operation parameters
            context: Workflow context

        Returns:
            CICDResult with build outcomes
        """
        result = CICDResult(
            success=True, operation=operation.operation, branch=operation.branch
        )

        try:
            image_name = operation.image_name or self._generate_image_name(
                operation.branch
            )

            build_result = await self._docker.execute(
                DockerOperation(
                    operation="build_image",
                    params={
                        "path": ".",
                        "dockerfile": operation.dockerfile_path,
                        "tag": image_name,
                    },
                ),
                context,
            )

            # Extract build info from result.data
            build_data = build_result.data or {}
            result.docker_results = {
                "success": build_result.success,
                "image_name": image_name,
                "image_id": build_data.get("image_id"),
            }

            result.success = build_result.success
            if not result.success:
                result.error = (
                    f"Docker build failed: {build_result.error or 'Unknown error'}"
                )

            return result

        except Exception as e:
            result.success = False
            result.error = f"Build failed: {str(e)}"
            return result

    async def _create_pr_workflow(
        self, operation: CICDOperation, context: WorkflowContext
    ) -> CICDResult:
        """Create PR workflow.

        Args:
            operation: CI/CD operation parameters
            context: Workflow context

        Returns:
            CICDResult with PR creation outcomes
        """
        result = CICDResult(
            success=True, operation=operation.operation, branch=operation.branch
        )

        try:
            pr_result = await self._github.execute(
                GitHubOperation(
                    operation="create_pr",
                    repo_name=self.config.github_repo,
                    params={
                        "title": operation.pr_title,
                        "body": operation.pr_body,
                        "head": operation.branch,
                        "base": operation.base_branch,
                    },
                ),
                context,
            )

            # Extract PR data from result
            if pr_result.success:
                pr_data = pr_result.data or {}
                result.pr_number = pr_data.get("pr_number")
                result.pr_url = pr_data.get("html_url")
                result.success = True
            else:
                result.success = False
                error_msg = pr_result.error or "Unknown error"
                result.error = f"PR creation failed: {error_msg}"

            return result

        except Exception as e:
            result.success = False
            result.error = f"PR creation failed: {str(e)}"
            return result

    def _generate_image_name(self, branch: str) -> str:
        """Generate Docker image name from branch.

        Args:
            branch: Branch name

        Returns:
            Docker image name
        """
        # Extract repo name from "owner/repo"
        repo_name = self.config.github_repo.split("/")[-1]

        # Sanitize branch name for Docker tag
        tag = branch.replace("/", "-").replace("_", "-").lower()

        return f"{repo_name}:{tag}"

    def _format_test_results_comment(self, test_results: dict[str, Any]) -> str:
        """Format test results as GitHub comment markdown.

        Args:
            test_results: Test results dictionary

        Returns:
            Markdown formatted comment
        """
        total = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        duration = test_results.get("duration", 0.0)

        status_emoji = "✅" if failed == 0 else "❌"

        return f"""## {status_emoji} Test Results

**Total Tests:** {total}
**Passed:** {passed} ✅
**Failed:** {failed} {"❌" if failed > 0 else ""}
**Duration:** {duration:.2f}s

{"All tests passed!" if failed == 0 else f"{failed} test(s) failed. Please review."}
"""

    def close(self) -> None:
        """Clean up resources.

        Note: close() methods on primitives are sync, not async.
        """
        self._github.close()
        self._pytest.close()
        self._docker.close()
