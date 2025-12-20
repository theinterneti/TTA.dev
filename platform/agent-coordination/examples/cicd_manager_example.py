"""
Simple CI/CD Manager Example

Demonstrates how to use CICDManager with the actual API.

This example shows the real operations supported by CICDManager:
- run_cicd_workflow: Complete pipeline (tests → build → optionally create PR)
- run_tests_only: Run tests without building
- build_only: Build Docker image without tests
- create_pr: Create pull request

Requirements:
- GitHub token in GITHUB_TOKEN env var (optional for demo)
- Docker daemon running (optional for demo)
- tta-agent-coordination package installed
"""

import asyncio
import os

from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.managers import (
    CICDManager,
    CICDManagerConfig,
    CICDOperation,
)


async def example_run_tests_only():
    """Example: Run tests only (no Docker build)."""
    print("\n" + "=" * 80)
    print("Example 1: Run Tests Only")
    print("=" * 80 + "\n")

    # Configure manager
    config = CICDManagerConfig(
        github_token=os.getenv("GITHUB_TOKEN", "demo-token"),
        github_repo="owner/repo",  # Format: "owner/repo"
        pytest_executable="python",  # "python" or "uv"
    )

    manager = CICDManager(config)

    try:
        # Create operation
        operation = CICDOperation(
            operation="run_tests_only",
            branch="feature/my-feature",
            test_strategy="fast",  # Options: fast, thorough, coverage
            test_path="tests/",
        )

        # Execute
        context = WorkflowContext(correlation_id="test-example-1")
        result = await manager.execute(operation, context)

        # Print results
        print(f"Success: {result.success}")
        if result.test_results:
            print(f"Tests: {result.test_results}")
        if result.error:
            print(f"Error: {result.error}")

    finally:
        manager.close()  # Note: close() is NOT async


async def example_full_workflow():
    """Example: Complete CI/CD workflow (tests → build → create PR)."""
    print("\n" + "=" * 80)
    print("Example 2: Full CI/CD Workflow")
    print("=" * 80 + "\n")

    # Configure manager
    config = CICDManagerConfig(
        github_token=os.getenv("GITHUB_TOKEN", "demo-token"),
        github_repo="owner/repo",
        pytest_executable="python",
        test_strategy="thorough",  # Default strategy
        auto_merge=False,  # Don't auto-merge PRs
        comment_on_pr=True,  # Post test results as comments
    )

    manager = CICDManager(config)

    try:
        # Create operation for full workflow
        operation = CICDOperation(
            operation="run_cicd_workflow",
            branch="feature/new-api",
            test_strategy="thorough",
            test_path="tests/",
            dockerfile_path="Dockerfile",
            image_name="myapp:feature-new-api",
            create_pr=True,  # Create PR after successful build
            pr_title="Add new API endpoint",
            pr_body="This PR adds a new REST API endpoint for user management.",
            base_branch="main",
        )

        # Execute
        context = WorkflowContext(correlation_id="full-workflow-example")
        result = await manager.execute(operation, context)

        # Print results
        print(f"Overall Success: {result.success}")
        print(f"Operation: {result.operation}")
        print(f"Branch: {result.branch}")

        if result.test_results:
            print("\nTest Results:")
            print(f"  Success: {result.test_results.get('success')}")
            print(f"  Total: {result.test_results.get('total_tests')}")
            print(f"  Passed: {result.test_results.get('passed')}")
            print(f"  Failed: {result.test_results.get('failed')}")

        if result.docker_results:
            print("\nDocker Results:")
            print(f"  Success: {result.docker_results.get('success')}")
            print(f"  Image: {result.docker_results.get('image_name')}")

        if result.pr_number:
            print("\nPR Created:")
            print(f"  Number: #{result.pr_number}")
            print(f"  URL: {result.pr_url}")

        if result.error:
            print(f"\nError: {result.error}")

    finally:
        manager.close()


async def example_build_only():
    """Example: Build Docker image only (no tests)."""
    print("\n" + "=" * 80)
    print("Example 3: Build Docker Image Only")
    print("=" * 80 + "\n")

    config = CICDManagerConfig(
        github_token=os.getenv("GITHUB_TOKEN", "demo-token"),
        github_repo="owner/repo",
        docker_base_url="unix://var/run/docker.sock",
    )

    manager = CICDManager(config)

    try:
        operation = CICDOperation(
            operation="build_only",
            branch="feature/hotfix",
            dockerfile_path="Dockerfile",
            image_name="myapp:hotfix-v1.2.3",
        )

        context = WorkflowContext(correlation_id="build-example")
        result = await manager.execute(operation, context)

        print(f"Build Success: {result.success}")
        if result.docker_results:
            print(f"Image: {result.docker_results.get('image_name')}")
            print(f"Image ID: {result.docker_results.get('image_id')}")

    finally:
        manager.close()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  CI/CD Manager Examples")
    print("  Real API Demonstration")
    print("=" * 80)

    print("\n⚠️  Note: These examples use the ACTUAL CICDManager API")
    print("   Set GITHUB_TOKEN for real GitHub integration")
    print("   Ensure Docker daemon is running for build operations\n")

    # Run examples
    await example_run_tests_only()
    await example_full_workflow()
    await example_build_only()

    print("\n" + "=" * 80)
    print("  Examples Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
