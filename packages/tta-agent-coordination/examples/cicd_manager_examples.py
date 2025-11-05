"""
CICDManager Usage Examples

Demonstrates practical usage patterns for CICDManager, the L2 Domain Manager
that coordinates GitHub, PyTest, and Docker experts for complete CI/CD workflows.
"""

import asyncio

from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.managers import CICDManager, CICDManagerConfig
from tta_agent_coordination.managers.cicd_manager import CICDOperation

# ============================================================================
# Example 1: Simple CI/CD Workflow (Tests + Build + PR)
# ============================================================================


async def example_1_simple_cicd():
    """
    Run a complete CI/CD workflow: test → build → create PR.

    This is the most common use case - validate code with tests, build Docker
    image, and create a pull request.
    """
    print("\n" + "=" * 70)
    print("Example 1: Simple CI/CD Workflow")
    print("=" * 70 + "\n")

    # Configure CICDManager
    config = CICDManagerConfig(
        github_token="your-github-token",  # Use real token or env var
        github_repo="your-org/your-repo",
        docker_base_url="unix://var/run/docker.sock",
        pytest_executable="python",  # Uses "python -m pytest"
        test_strategy="thorough",  # Run all tests
        auto_merge=False,  # Don't auto-merge PRs
        comment_on_pr=True,  # Post test results as comment
    )

    manager = CICDManager(config=config)

    # Define the CI/CD operation
    operation = CICDOperation(
        operation="run_cicd_workflow",
        branch="feature/add-authentication",
        create_pr=True,
        pr_title="Add user authentication",
        pr_body="This PR adds JWT-based authentication to the API",
        base_branch="main",
    )

    # Create workflow context for tracing
    context = WorkflowContext(correlation_id="cicd-example-1")

    try:
        # Execute the workflow
        print("🚀 Starting CI/CD workflow...")
        result = await manager.execute(operation, context)

        if result.success:
            print("✅ CI/CD workflow completed successfully!")
            print("\n📊 Test Results:")
            print(f"   Total tests: {result.test_results['total_tests']}")
            print(f"   Passed: {result.test_results['passed']}")
            print(f"   Failed: {result.test_results['failed']}")
            print(f"   Duration: {result.test_results['duration_seconds']:.2f}s")

            print("\n🐳 Docker Build:")
            print(f"   Image: {result.docker_results['image_name']}")
            print(f"   Image ID: {result.docker_results['image_id']}")

            print("\n🔀 Pull Request:")
            print(f"   PR #{result.pr_number}")
            print(f"   URL: {result.pr_url}")
        else:
            print(f"❌ CI/CD workflow failed: {result.error}")

    finally:
        manager.close()


# ============================================================================
# Example 2: Tests-Only Workflow (No Build or PR)
# ============================================================================


async def example_2_tests_only():
    """
    Run tests only without building or creating a PR.

    Useful for quick validation during development or for branches that
    don't need Docker images.
    """
    print("\n" + "=" * 70)
    print("Example 2: Tests-Only Workflow")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
        pytest_executable="python",
        test_strategy="fast",  # Run unit tests only (fast)
    )

    manager = CICDManager(config=config)

    operation = CICDOperation(
        operation="run_tests_only",
        branch="feature/quick-fix",
        test_path="tests/unit/",  # Only run unit tests
    )

    context = WorkflowContext(correlation_id="cicd-example-2")

    try:
        print("🧪 Running tests...")
        result = await manager.execute(operation, context)

        if result.success:
            print("✅ All tests passed!")
            print("\n📊 Results:")
            print(f"   Total: {result.test_results['total_tests']}")
            print(f"   Passed: {result.test_results['passed']}")
            print(f"   Duration: {result.test_results['duration_seconds']:.2f}s")
        else:
            print(f"❌ Tests failed: {result.error}")
            if result.test_results:
                print(f"   Failed tests: {result.test_results.get('failed', 0)}")

    finally:
        manager.close()


# ============================================================================
# Example 3: Build-Only Workflow (No Tests or PR)
# ============================================================================


async def example_3_build_only():
    """
    Build Docker image without running tests or creating a PR.

    Useful for rebuilding images after infrastructure changes or when
    tests are already validated.
    """
    print("\n" + "=" * 70)
    print("Example 3: Build-Only Workflow")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
        docker_base_url="unix://var/run/docker.sock",
    )

    manager = CICDManager(config=config)

    operation = CICDOperation(
        operation="build_only",
        branch="main",
        dockerfile_path="docker/Dockerfile",
        image_name="myapp",
        image_tag="latest",
    )

    context = WorkflowContext(correlation_id="cicd-example-3")

    try:
        print("🐳 Building Docker image...")
        result = await manager.execute(operation, context)

        if result.success:
            print("✅ Docker image built successfully!")
            print("\n🐳 Build Results:")
            print(f"   Image: {result.docker_results['image_name']}")
            print(f"   Image ID: {result.docker_results['image_id']}")
        else:
            print(f"❌ Build failed: {result.error}")

    finally:
        manager.close()


# ============================================================================
# Example 4: Create PR Without Tests/Build
# ============================================================================


async def example_4_pr_only():
    """
    Create a pull request without running tests or building.

    Useful when tests and builds are handled by external CI/CD systems,
    or when creating documentation-only PRs.
    """
    print("\n" + "=" * 70)
    print("Example 4: PR-Only Workflow")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
        comment_on_pr=False,  # Don't add comments for doc-only PRs
    )

    manager = CICDManager(config=config)

    operation = CICDOperation(
        operation="create_pr",
        branch="docs/update-readme",
        pr_title="Update README with installation instructions",
        pr_body="""
## Changes
- Added step-by-step installation guide
- Updated example code snippets
- Fixed typos in API documentation

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [x] Documentation update
        """,
        base_branch="main",
    )

    context = WorkflowContext(correlation_id="cicd-example-4")

    try:
        print("🔀 Creating pull request...")
        result = await manager.execute(operation, context)

        if result.success:
            print("✅ Pull request created successfully!")
            print("\n🔀 PR Details:")
            print(f"   PR #{result.pr_number}")
            print(f"   URL: {result.pr_url}")
        else:
            print(f"❌ PR creation failed: {result.error}")

    finally:
        manager.close()


# ============================================================================
# Example 5: CI/CD with Custom Test Strategy
# ============================================================================


async def example_5_custom_strategy():
    """
    Run CI/CD workflow with coverage collection.

    Uses the 'coverage' test strategy to collect coverage data during
    test execution.
    """
    print("\n" + "=" * 70)
    print("Example 5: CI/CD with Coverage")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
        docker_base_url="unix://var/run/docker.sock",
        test_strategy="coverage",  # Enable coverage collection
    )

    manager = CICDManager(config=config)

    operation = CICDOperation(
        operation="run_cicd_workflow",
        branch="feature/improve-coverage",
        test_strategy="coverage",  # Override config strategy
        create_pr=True,
        pr_title="Improve test coverage",
        pr_body="Added tests to increase coverage from 80% to 95%",
    )

    context = WorkflowContext(correlation_id="cicd-example-5")

    try:
        print("🚀 Starting CI/CD with coverage...")
        result = await manager.execute(operation, context)

        if result.success:
            print("✅ CI/CD completed!")

            # Coverage data available in test_results
            coverage = result.test_results.get("coverage", {})
            print("\n📊 Test Results:")
            print(
                f"   Tests passed: {result.test_results['passed']}/{result.test_results['total_tests']}"
            )
            print(f"   Coverage: {coverage.get('total_coverage', 'N/A')}")

            print("\n🔀 Pull Request:")
            print(f"   PR #{result.pr_number}")
            print(f"   URL: {result.pr_url}")
        else:
            print(f"❌ Workflow failed: {result.error}")

    finally:
        manager.close()


# ============================================================================
# Example 6: Error Handling and Validation
# ============================================================================


async def example_6_error_handling():
    """
    Demonstrate error handling and validation failures.

    Shows how CICDManager handles validation errors, test failures,
    and build failures with proper error messages.
    """
    print("\n" + "=" * 70)
    print("Example 6: Error Handling")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
    )

    manager = CICDManager(config=config)

    # Example 6a: Validation error (missing PR title)
    print("📝 Test 6a: Validation Error (Missing PR Title)")
    operation = CICDOperation(
        operation="create_pr",
        branch="feature-branch",
        pr_title="",  # Empty title - validation error
        pr_body="Description",
    )

    context = WorkflowContext(correlation_id="cicd-example-6a")
    result = await manager.execute(operation, context)
    print(f"   Result: {'❌ Failed' if not result.success else '✅ Passed'}")
    if not result.success:
        print(f"   Error: {result.error}")

    # Example 6b: Invalid operation
    print("\n📝 Test 6b: Invalid Operation")
    operation = CICDOperation(
        operation="unknown_operation",  # Invalid operation type
        branch="feature-branch",
    )

    context = WorkflowContext(correlation_id="cicd-example-6b")
    result = await manager.execute(operation, context)
    print(f"   Result: {'❌ Failed' if not result.success else '✅ Passed'}")
    if not result.success:
        print(f"   Error: {result.error}")

    manager.close()


# ============================================================================
# Example 7: CI/CD Without Auto-Comment
# ============================================================================


async def example_7_no_comment():
    """
    Run CI/CD workflow without posting test results as PR comment.

    Useful when you want to create PRs but don't need automatic
    comment posting (e.g., bot-created PRs).
    """
    print("\n" + "=" * 70)
    print("Example 7: CI/CD Without Comment")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
        docker_base_url="unix://var/run/docker.sock",
        comment_on_pr=False,  # Disable automatic commenting
    )

    manager = CICDManager(config=config)

    operation = CICDOperation(
        operation="run_cicd_workflow",
        branch="automated/dependency-update",
        create_pr=True,
        pr_title="chore: Update dependencies",
        pr_body="Automated dependency update by Dependabot",
    )

    context = WorkflowContext(correlation_id="cicd-example-7")

    try:
        print("🚀 Starting CI/CD (no comment)...")
        result = await manager.execute(operation, context)

        if result.success:
            print("✅ CI/CD completed!")
            print(f"   PR #{result.pr_number} created (no comment added)")
        else:
            print(f"❌ Workflow failed: {result.error}")

    finally:
        manager.close()


# ============================================================================
# Example 8: Fail-Fast Behavior
# ============================================================================


async def example_8_fail_fast():
    """
    Demonstrate fail-fast behavior when tests fail.

    Shows how CICDManager stops execution when tests fail, skipping
    the Docker build and PR creation steps.
    """
    print("\n" + "=" * 70)
    print("Example 8: Fail-Fast on Test Failure")
    print("=" * 70 + "\n")

    config = CICDManagerConfig(
        github_token="your-github-token",
        github_repo="your-org/your-repo",
        docker_base_url="unix://var/run/docker.sock",
    )

    manager = CICDManager(config=config)

    operation = CICDOperation(
        operation="run_cicd_workflow",
        branch="feature/buggy-code",  # Assume this has failing tests
        create_pr=True,
        pr_title="Add feature with bugs",
        pr_body="This will fail at test stage",
    )

    context = WorkflowContext(correlation_id="cicd-example-8")

    try:
        print("🚀 Starting CI/CD (will fail at tests)...")
        result = await manager.execute(operation, context)

        if not result.success:
            print("❌ CI/CD stopped due to test failures (fail-fast)")
            print("\n📊 Test Results:")
            if result.test_results:
                print(
                    f"   Failed: {result.test_results.get('failed', 0)}/{result.test_results.get('total_tests', 0)}"
                )

            print("\n🐳 Docker Build: SKIPPED (tests failed)")
            print("🔀 Pull Request: SKIPPED (tests failed)")
        else:
            print("✅ All steps passed (unexpected in this example)")

    finally:
        manager.close()


# ============================================================================
# Main - Run All Examples
# ============================================================================


async def main():
    """Run all examples sequentially."""
    print("\n" + "=" * 70)
    print("CICDManager Usage Examples")
    print("=" * 70)

    # NOTE: These examples use placeholder tokens/repos.
    # Replace with real values or set environment variables:
    #   - GITHUB_TOKEN
    #   - GITHUB_REPO

    print("\n⚠️  NOTE: Examples use placeholder values.")
    print("   Update tokens and repo names before running in production.\n")

    # Run examples
    # Commented out by default - uncomment to run
    # await example_1_simple_cicd()
    # await example_2_tests_only()
    # await example_3_build_only()
    # await example_4_pr_only()
    # await example_5_custom_strategy()
    # await example_6_error_handling()
    # await example_7_no_comment()
    # await example_8_fail_fast()

    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
