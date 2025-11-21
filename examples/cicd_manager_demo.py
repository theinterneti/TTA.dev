"""
Demo script for CICDManager.

This script demonstrates the CICDManager in action by mocking the low-level
L4 wrappers (GitHub, Docker, PyTest CLI) while keeping the L2 (Manager)
and L3 (Experts) logic intact. This validates the integration between layers.
"""

import asyncio
import sys
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append("platform/agent-coordination/src")

from tta_agent_coordination.experts.docker_expert import DockerResult
from tta_agent_coordination.experts.github_expert import GitHubResult
from tta_agent_coordination.experts.pytest_expert import PyTestResult
from tta_agent_coordination.managers.cicd_manager import (
    CICDManager,
    CICDOperation,
)
from tta_dev_primitives import WorkflowContext


async def main():
    print("🚀 Starting CICDManager Demo...\n")

    # Mock L4 Wrappers to avoid real side effects
    with (
        patch(
            "tta_agent_coordination.experts.github_expert.GitHubAPIWrapper"
        ) as MockGH,
        patch(
            "tta_agent_coordination.experts.docker_expert.DockerSDKWrapper"
        ) as MockDocker,
        patch(
            "tta_agent_coordination.experts.pytest_expert.PyTestCLIWrapper"
        ) as MockPyTest,
    ):
        # Setup Mock Behaviors

        # Docker: Build succeeds
        docker_instance = MockDocker.return_value
        # Note: The wrapper execute method is async, so we need an async mock or return a future
        # However, the L3 experts await the wrapper.execute.
        # If we mock the class, the instance.execute should be an AsyncMock.

        async def async_docker_success(*args, **kwargs):
            return DockerResult(
                success=True,
                operation="build_image",
                data={"id": "sha256:demo_image_id"},
            )

        async def async_pytest_success(*args, **kwargs):
            return PyTestResult(
                success=True,
                operation="run_tests",
                data={"output": "==== 10 passed ===="},
            )

        async def async_github_success(*args, **kwargs):
            return GitHubResult(
                success=True,
                operation="add_comment",
                data={"url": "http://github.com/comment"},
            )

        docker_instance.execute = MagicMock(side_effect=async_docker_success)
        pytest_instance = MockPyTest.return_value
        pytest_instance.execute = MagicMock(side_effect=async_pytest_success)
        github_instance = MockGH.return_value
        github_instance.execute = MagicMock(side_effect=async_github_success)

        # Initialize Manager
        manager = CICDManager()
        context = WorkflowContext(correlation_id="demo-run-001")

        # --- Scenario 1: Build and Test ---
        print("--- Scenario 1: Build and Test ---")
        op1 = CICDOperation(
            operation="build_and_test",
            params={"build_path": ".", "test_path": "tests/"},
        )
        result1 = await manager.execute(op1, context)
        print(f"Result: {'✅ Success' if result1.success else '❌ Failed'}")
        print(f"Data: {result1.data}\n")

        # --- Scenario 2: Validate PR ---
        print("--- Scenario 2: Validate PR ---")
        op2 = CICDOperation(
            operation="validate_pr", params={"pr_number": 123, "repo_name": "org/repo"}
        )
        result2 = await manager.execute(op2, context)
        print(f"Result: {'✅ Success' if result2.success else '❌ Failed'}")
        print(f"Comment URL: {result2.data.get('comment_url')}\n")

        # --- Scenario 3: Full Pipeline ---
        print("--- Scenario 3: Full Pipeline ---")
        op3 = CICDOperation(
            operation="run_pipeline", params={"pr_number": 123, "repo_name": "org/repo"}
        )
        result3 = await manager.execute(op3, context)
        print(f"Result: {'✅ Success' if result3.success else '❌ Failed'}")

        print("\n✨ Demo Completed Successfully!")


if __name__ == "__main__":
    asyncio.run(main())
