"""
CICDManager - L2 Domain Manager.

Coordinates GitHub, Docker, and PyTest experts to execute
complete CI/CD workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from tta_agent_coordination.experts.docker_expert import (
    DockerExpert,
    DockerExpertConfig,
    DockerOperation,
)
from tta_agent_coordination.experts.github_expert import (
    GitHubExpert,
    GitHubExpertConfig,
    GitHubOperation,
)
from tta_agent_coordination.experts.pytest_expert import (
    PyTestExpert,
    PyTestExpertConfig,
    PyTestOperation,
)


class CICDOperationType(str, Enum):
    """Types of CI/CD operations."""

    BUILD_AND_TEST = "build_and_test"
    VALIDATE_PR = "validate_pr"
    RUN_PIPELINE = "run_pipeline"


@dataclass
class CICDOperation:
    """Operation for CICDManager."""

    operation: CICDOperationType | str
    params: dict[str, Any]


@dataclass
class CICDResult:
    """Result from CICDManager."""

    success: bool
    operation: str
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class CICDManagerConfig:
    """Configuration for CICDManager."""

    github_config: GitHubExpertConfig | None = None
    docker_config: DockerExpertConfig | None = None
    pytest_config: PyTestExpertConfig | None = None


class CICDManager(WorkflowPrimitive[CICDOperation, CICDResult]):
    """
    L2 Domain Manager for CI/CD workflows.

    Coordinates L3 experts to execute complex CI/CD tasks:
    - Build Docker images
    - Run tests
    - Report results to GitHub
    """

    def __init__(self, config: CICDManagerConfig | None = None):
        """Initialize CICDManager with L3 experts."""
        super().__init__()
        self.config = config or CICDManagerConfig()

        # Initialize L3 experts
        self.github = GitHubExpert(config=self.config.github_config)
        self.docker = DockerExpert(config=self.config.docker_config)
        self.pytest = PyTestExpert(config=self.config.pytest_config)

    async def execute(
        self, input_data: CICDOperation, context: WorkflowContext
    ) -> CICDResult:
        """Execute CI/CD operation."""
        op_type = input_data.operation
        if isinstance(op_type, Enum):
            op_type = op_type.value

        if op_type == "build_and_test":
            return await self._build_and_test(input_data.params, context)
        elif op_type == "validate_pr":
            return await self._validate_pr(input_data.params, context)
        elif op_type == "run_pipeline":
            return await self._run_pipeline(input_data.params, context)
        else:
            return CICDResult(
                success=False,
                operation=str(op_type),
                error=f"Unknown operation: {op_type}",
            )

    async def _build_and_test(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> CICDResult:
        """
        Build Docker image and run tests.

        Steps:
        1. Build Docker image
        2. Run tests (if build success)
        """
        # 1. Build Image
        build_op = DockerOperation(
            operation="build_image",
            params={
                "path": params.get("build_path", "."),
                "tag": params.get("image_tag", "latest"),
            },
        )
        build_result = await self.docker.execute(build_op, context)

        if not build_result.success:
            return CICDResult(
                success=False,
                operation="build_and_test",
                error=f"Build failed: {build_result.error}",
            )

        # 2. Run Tests
        test_op = PyTestOperation(
            operation="run_tests",
            params={
                "test_path": params.get("test_path", "tests/"),
                "strategy": params.get("test_strategy", "fast"),
            },
        )
        test_result = await self.pytest.execute(test_op, context)

        if not test_result.success:
            return CICDResult(
                success=False,
                operation="build_and_test",
                error=f"Tests failed: {test_result.error}",
                data={"build": build_result.data, "tests": test_result.data},
            )

        return CICDResult(
            success=True,
            operation="build_and_test",
            data={"build": build_result.data, "tests": test_result.data},
        )

    async def _validate_pr(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> CICDResult:
        """
        Validate a PR by running tests and commenting results.

        Steps:
        1. Run tests
        2. Post comment to PR
        """
        pr_number = params.get("pr_number")
        repo_name = params.get("repo_name")

        if not pr_number or not repo_name:
            return CICDResult(
                success=False,
                operation="validate_pr",
                error="Missing pr_number or repo_name",
            )

        # 1. Run Tests
        test_op = PyTestOperation(
            operation="run_tests",
            params={
                "test_path": params.get("test_path", "tests/"),
                "strategy": "coverage",  # Always use coverage for PRs
            },
        )
        test_result = await self.pytest.execute(test_op, context)

        # 2. Format Comment
        status_emoji = "✅" if test_result.success else "❌"

        # Safely get output
        output = "No output available"
        if test_result.data and "output" in test_result.data:
            output = test_result.data["output"]

        comment_body = (
            f"## CI Validation Results\n\n"
            f"Status: {status_emoji} **"
            f"{'PASSED' if test_result.success else 'FAILED'}**\n\n"
            f"### Test Summary\n"
            f"```\n{output}\n```"
        )

        # 3. Post Comment
        comment_op = GitHubOperation(
            operation="add_comment",
            repo_name=repo_name,
            params={
                "issue_number": pr_number,
                "body": comment_body,
            },
        )
        comment_result = await self.github.execute(comment_op, context)

        if not comment_result.success:
            return CICDResult(
                success=False,
                operation="validate_pr",
                error=f"Failed to post comment: {comment_result.error}",
                data={"tests": test_result.data},
            )

        return CICDResult(
            success=test_result.success,
            operation="validate_pr",
            data={
                "tests": test_result.data,
                "comment_url": (
                    comment_result.data.get("url") if comment_result.data else None
                ),
            },
        )

    async def _run_pipeline(
        self, params: dict[str, Any], context: WorkflowContext
    ) -> CICDResult:
        """Full pipeline: Build -> Test -> Report."""
        # 1. Build & Test
        bt_result = await self._build_and_test(params, context)

        if not bt_result.success:
            # Report failure if we have PR info
            if "pr_number" in params and "repo_name" in params:
                await self._report_failure(params, str(bt_result.error), context)
            return bt_result

        # 2. Report Success (if PR info exists)
        if "pr_number" in params and "repo_name" in params:
            await self._report_success(params, bt_result.data or {}, context)

        return CICDResult(success=True, operation="run_pipeline", data=bt_result.data)

    async def _report_failure(
        self, params: dict, error: str, context: WorkflowContext
    ) -> None:
        """Helper to report failure to GitHub."""
        comment_op = GitHubOperation(
            operation="add_comment",
            repo_name=params["repo_name"],
            params={
                "issue_number": params["pr_number"],
                "body": f"## ❌ Pipeline Failed\n\nError: {error}",
            },
        )
        await self.github.execute(comment_op, context)

    async def _report_success(
        self, params: dict, data: dict, context: WorkflowContext
    ) -> None:
        """Helper to report success to GitHub."""
        comment_op = GitHubOperation(
            operation="add_comment",
            repo_name=params["repo_name"],
            params={
                "issue_number": params["pr_number"],
                "body": "## ✅ Pipeline Passed\n\nBuild and tests successful.",
            },
        )
        await self.github.execute(comment_op, context)

    def close(self) -> None:
        """Close all experts."""
        self.github.close()
        self.docker.close()
        self.pytest.close()
