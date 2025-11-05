"""
Complete CI/CD Workflow Example

Demonstrates end-to-end integration of all 3 L2 Domain Managers:
- CICDManager: GitHub PR management and workflow orchestration
- QualityManager: Testing and validation
- InfrastructureManager: Docker deployment and monitoring

Real-world scenario:
1. Developer opens PR
2. CI/CD pipeline runs tests (QualityManager)
3. On success, builds Docker image (InfrastructureManager)
4. Deploys to staging environment (InfrastructureManager)
5. Runs health checks (InfrastructureManager)
6. Updates PR with deployment status (CICDManager)

Requirements:
- GitHub token in GITHUB_TOKEN env var
- Docker daemon running
- tta-agent-coordination package installed
"""

import asyncio
import os
from typing import Any

from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.managers import (
    CICDManager,
    CICDManagerConfig,
    CICDOperation,
    InfrastructureManager,
    InfrastructureManagerConfig,
    InfrastructureOperation,
    QualityManager,
    QualityManagerConfig,
    QualityOperation,
)

# =============================================================================
# Workflow Orchestrator
# =============================================================================


class DeploymentPipeline:
    """
    Orchestrates complete CI/CD pipeline using all L2 managers.

    Workflow:
    1. Fetch PR details (CICDManager)
    2. Run tests (QualityManager)
    3. Build Docker image (InfrastructureManager)
    4. Deploy to staging (InfrastructureManager)
    5. Health check (InfrastructureManager)
    6. Update PR status (CICDManager)
    """

    def __init__(
        self,
        github_token: str,
        repo_owner: str,
        repo_name: str,
        project_path: str = ".",
    ):
        """
        Initialize pipeline with all managers.

        Args:
            github_token: GitHub API token
            repo_owner: Repository owner
            repo_name: Repository name
            project_path: Path to project directory
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.project_path = project_path

        # Initialize L2 managers
        self.cicd_manager = CICDManager(
            config=CICDManagerConfig(
                github_token=github_token,
                default_repo_owner=repo_owner,
                default_repo_name=repo_name,
            )
        )

        self.quality_manager = QualityManager(
            config=QualityManagerConfig(
                pytest_path="pytest",
                pytest_timeout=300.0,
                coverage_threshold=80.0,
            )
        )

        self.infrastructure_manager = InfrastructureManager(
            config=InfrastructureManagerConfig(
                default_network="staging-network",
                auto_pull_images=True,
                health_check_retries=5,
                cleanup_on_failure=True,
            )
        )

    async def close(self):
        """Close all managers."""
        await self.cicd_manager.close()
        await self.quality_manager.close()
        await self.infrastructure_manager.close()

    async def run_pipeline(
        self, pr_number: int, branch_name: str, dockerfile_path: str = "Dockerfile"
    ) -> dict[str, Any]:
        """
        Execute complete CI/CD pipeline for a PR.

        Args:
            pr_number: Pull request number
            branch_name: Branch to deploy
            dockerfile_path: Path to Dockerfile

        Returns:
            Pipeline execution results
        """
        context = WorkflowContext(correlation_id=f"pipeline-pr-{pr_number}")

        results = {
            "pr_number": pr_number,
            "branch": branch_name,
            "success": False,
            "stages": {},
        }

        print("\n" + "=" * 80)
        print(f"🚀 CI/CD Pipeline: PR #{pr_number} ({branch_name})")
        print("=" * 80 + "\n")

        try:
            # Stage 1: Fetch PR Details
            print("📋 Stage 1: Fetch PR Details")
            print("-" * 40)

            pr_result = await self._fetch_pr_details(pr_number, context)
            results["stages"]["pr_fetch"] = pr_result

            if not pr_result["success"]:
                print(f"   ❌ Failed to fetch PR: {pr_result['error']}")
                return results

            print(f"   ✅ PR fetched: {pr_result['title']}")
            print(f"   Author: {pr_result['author']}")
            print(f"   Status: {pr_result['state']}")

            # Stage 2: Run Tests
            print("\n🧪 Stage 2: Run Tests")
            print("-" * 40)

            test_result = await self._run_tests(context)
            results["stages"]["tests"] = test_result

            if not test_result["success"]:
                print(f"   ❌ Tests failed: {test_result['error']}")
                await self._update_pr_status(
                    pr_number, "failure", "Tests failed", context
                )
                return results

            print(
                f"   ✅ Tests passed: {test_result['tests_passed']}/{test_result['total_tests']}"
            )
            print(f"   Coverage: {test_result.get('coverage', 'N/A')}%")

            # Stage 3: Build Docker Image
            print("\n📦 Stage 3: Build Docker Image")
            print("-" * 40)

            image_tag = f"app:{branch_name}-{pr_number}"
            build_result = await self._build_image(dockerfile_path, image_tag, context)
            results["stages"]["build"] = build_result

            if not build_result["success"]:
                print(f"   ❌ Build failed: {build_result['error']}")
                await self._update_pr_status(
                    pr_number, "failure", "Docker build failed", context
                )
                return results

            print(f"   ✅ Image built: {image_tag}")

            # Stage 4: Deploy to Staging
            print("\n🚀 Stage 4: Deploy to Staging")
            print("-" * 40)

            deploy_result = await self._deploy_staging(image_tag, pr_number, context)
            results["stages"]["deploy"] = deploy_result

            if not deploy_result["success"]:
                print(f"   ❌ Deployment failed: {deploy_result['error']}")
                await self._update_pr_status(
                    pr_number, "failure", "Deployment failed", context
                )
                return results

            print(f"   ✅ Deployed: {', '.join(deploy_result['containers'])}")

            # Stage 5: Health Check
            print("\n📊 Stage 5: Health Check")
            print("-" * 40)

            health_result = await self._check_health(
                deploy_result["containers"], context
            )
            results["stages"]["health"] = health_result

            if not health_result["success"]:
                print(f"   ❌ Health check failed: {health_result['error']}")
                await self._update_pr_status(
                    pr_number, "failure", "Health check failed", context
                )
                return results

            print("   ✅ All containers healthy")
            for container, status in health_result["health_status"].items():
                print(f"      • {container}: {status}")

            # Stage 6: Update PR Status
            print("\n✅ Stage 6: Update PR Status")
            print("-" * 40)

            await self._update_pr_status(
                pr_number,
                "success",
                f"Deployed to staging: {', '.join(deploy_result['containers'])}",
                context,
            )
            print("   ✅ PR updated with success status")

            results["success"] = True
            print("\n🎉 Pipeline completed successfully!")

        except Exception as e:
            print(f"\n❌ Pipeline failed with exception: {e}")
            results["error"] = str(e)
            await self._update_pr_status(
                pr_number, "error", f"Pipeline error: {e}", context
            )

        return results

    async def _fetch_pr_details(
        self, pr_number: int, context: WorkflowContext
    ) -> dict[str, Any]:
        """Fetch PR details from GitHub."""
        operation = CICDOperation(
            operation="get_pr",
            repo_owner=self.repo_owner,
            repo_name=self.repo_name,
            pr_number=pr_number,
        )

        result = await self.cicd_manager.execute(operation, context)

        return {
            "success": result.success,
            "title": result.pr_details.get("title") if result.pr_details else None,
            "author": result.pr_details.get("user", {}).get("login")
            if result.pr_details
            else None,
            "state": result.pr_details.get("state") if result.pr_details else None,
            "error": result.error,
        }

    async def _run_tests(self, context: WorkflowContext) -> dict[str, Any]:
        """Run pytest tests."""
        operation = QualityOperation(
            operation="run_tests",
            test_path=self.project_path,
            coverage=True,
            verbose=True,
        )

        result = await self.quality_manager.execute(operation, context)

        return {
            "success": result.success,
            "tests_passed": result.tests_passed,
            "total_tests": result.tests_run,
            "coverage": result.coverage_percent,
            "error": result.error,
        }

    async def _build_image(
        self, dockerfile_path: str, image_tag: str, context: WorkflowContext
    ) -> dict[str, Any]:
        """Build Docker image."""
        operation = InfrastructureOperation(
            operation="manage_images",
            image_params={
                "action": "build",
                "path": self.project_path,
                "tag": image_tag,
                "dockerfile": dockerfile_path,
            },
        )

        result = await self.infrastructure_manager.execute(operation, context)

        return {
            "success": result.success,
            "image": image_tag,
            "error": result.error,
        }

    async def _deploy_staging(
        self, image_tag: str, pr_number: int, context: WorkflowContext
    ) -> dict[str, Any]:
        """Deploy to staging environment."""
        operation = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": image_tag,
                    "name": f"staging-app-pr{pr_number}",
                    "ports": {"8000": str(8000 + pr_number)},  # Unique port per PR
                    "environment": {
                        "ENV": "staging",
                        "PR_NUMBER": str(pr_number),
                    },
                    "detach": True,
                }
            ],
        )

        result = await self.infrastructure_manager.execute(operation, context)

        return {
            "success": result.success,
            "containers": result.containers_started,
            "error": result.error,
        }

    async def _check_health(
        self, container_ids: list[str], context: WorkflowContext
    ) -> dict[str, Any]:
        """Check container health."""
        # Give containers time to start
        await asyncio.sleep(3)

        operation = InfrastructureOperation(
            operation="health_check", container_ids=container_ids
        )

        result = await self.infrastructure_manager.execute(operation, context)

        return {
            "success": result.success,
            "health_status": result.health_status,
            "error": result.error,
        }

    async def _update_pr_status(
        self,
        pr_number: int,
        state: str,
        description: str,
        context: WorkflowContext,
    ) -> None:
        """Update PR with status check."""
        operation = CICDOperation(
            operation="create_status",
            repo_owner=self.repo_owner,
            repo_name=self.repo_name,
            commit_sha="HEAD",  # In real scenario, get from PR
            state=state,
            description=description,
            context_name="ci/deployment-pipeline",
        )

        await self.cicd_manager.execute(operation, context)


# =============================================================================
# Cleanup Workflow
# =============================================================================


async def cleanup_staging_environment(
    pr_number: int, infrastructure_manager: InfrastructureManager
) -> None:
    """
    Clean up staging environment for a PR.

    Args:
        pr_number: PR number to clean up
        infrastructure_manager: Infrastructure manager instance
    """
    print("\n🧹 Cleaning up staging environment")
    print("-" * 40)

    context = WorkflowContext(correlation_id=f"cleanup-pr-{pr_number}")

    # Remove containers
    operation = InfrastructureOperation(
        operation="cleanup_resources",
        cleanup_stopped_containers=True,
        cleanup_unused_images=False,  # Keep images for faster rebuilds
        force_remove=True,
    )

    result = await infrastructure_manager.execute(operation, context)

    if result.success:
        print(
            f"✅ Cleanup complete: {len(result.containers_removed)} containers removed"
        )
    else:
        print(f"❌ Cleanup failed: {result.error}")


# =============================================================================
# Example Usage Scenarios
# =============================================================================


async def example_pr_deployment():
    """Example: Deploy a PR to staging."""
    print("\n" + "=" * 80)
    print("Example: PR Deployment Pipeline")
    print("=" * 80)

    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("\n⚠️  GITHUB_TOKEN not set - using mock mode")
        print("   Set GITHUB_TOKEN environment variable for real GitHub integration")
        return

    # Initialize pipeline
    pipeline = DeploymentPipeline(
        github_token=github_token,
        repo_owner="your-org",  # Replace with your org
        repo_name="your-repo",  # Replace with your repo
        project_path=".",
    )

    try:
        # Run pipeline for PR #42
        results = await pipeline.run_pipeline(
            pr_number=42, branch_name="feature/new-api", dockerfile_path="Dockerfile"
        )

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Pipeline Summary")
        print("=" * 80)
        print(f"\nPR #{results['pr_number']} ({results['branch']})")
        print(
            f"Overall Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}\n"
        )

        for stage_name, stage_result in results["stages"].items():
            status = "✅" if stage_result.get("success") else "❌"
            print(f"{status} {stage_name}: {stage_result}")

    finally:
        await pipeline.close()


async def example_multi_pr_deployment():
    """Example: Deploy multiple PRs in parallel."""
    print("\n" + "=" * 80)
    print("Example: Multi-PR Deployment")
    print("=" * 80)

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("\n⚠️  GITHUB_TOKEN not set - skipping")
        return

    pipeline = DeploymentPipeline(
        github_token=github_token,
        repo_owner="your-org",
        repo_name="your-repo",
    )

    try:
        # Deploy multiple PRs concurrently
        pr_numbers = [42, 43, 44]
        branches = ["feature/api", "feature/ui", "bugfix/auth"]

        tasks = [
            pipeline.run_pipeline(pr, branch, "Dockerfile")
            for pr, branch in zip(pr_numbers, branches)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Multi-PR Summary")
        print("=" * 80 + "\n")

        for pr, result in zip(pr_numbers, results):
            if isinstance(result, Exception):
                print(f"❌ PR #{pr}: {result}")
            else:
                status = "✅" if result["success"] else "❌"
                print(f"{status} PR #{pr}: {result['branch']}")

    finally:
        await pipeline.close()


async def example_full_lifecycle():
    """Example: Full PR lifecycle - deploy, test, cleanup."""
    print("\n" + "=" * 80)
    print("Example: Full PR Lifecycle")
    print("=" * 80)

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("\n⚠️  GITHUB_TOKEN not set - using demo mode")

        # Demo mode: just show the workflow
        print("\n📋 Full Lifecycle Workflow:")
        print("   1. Deploy PR to staging")
        print("   2. Run integration tests")
        print("   3. Run smoke tests")
        print("   4. Cleanup staging environment")
        print("\n💡 Set GITHUB_TOKEN to run real workflow")
        return

    pipeline = DeploymentPipeline(
        github_token=github_token,
        repo_owner="your-org",
        repo_name="your-repo",
    )

    try:
        pr_number = 45
        branch = "feature/payment"

        # Phase 1: Deploy
        print("\n📦 Phase 1: Deploy to Staging")
        results = await pipeline.run_pipeline(pr_number, branch, "Dockerfile")

        if not results["success"]:
            print("❌ Deployment failed - aborting lifecycle")
            return

        # Phase 2: Integration Tests (using deployed staging)
        print("\n🧪 Phase 2: Integration Tests")
        print("-" * 40)

        context = WorkflowContext(correlation_id=f"integration-pr-{pr_number}")
        integration_op = QualityOperation(
            operation="run_tests",
            test_path="tests/integration",
            markers=["integration"],
            verbose=True,
        )

        integration_result = await pipeline.quality_manager.execute(
            integration_op, context
        )

        if integration_result.success:
            print(
                f"   ✅ Integration tests passed: {integration_result.tests_passed}/{integration_result.tests_run}"
            )
        else:
            print(f"   ❌ Integration tests failed: {integration_result.error}")

        # Phase 3: Smoke Tests
        print("\n🔥 Phase 3: Smoke Tests")
        print("-" * 40)

        smoke_op = QualityOperation(
            operation="run_tests",
            test_path="tests/smoke",
            markers=["smoke"],
            verbose=True,
        )

        smoke_result = await pipeline.quality_manager.execute(smoke_op, context)

        if smoke_result.success:
            print(
                f"   ✅ Smoke tests passed: {smoke_result.tests_passed}/{smoke_result.tests_run}"
            )
        else:
            print(f"   ❌ Smoke tests failed: {smoke_result.error}")

        # Phase 4: Cleanup
        print("\n🧹 Phase 4: Cleanup")
        print("-" * 40)
        await cleanup_staging_environment(pr_number, pipeline.infrastructure_manager)

        # Final status
        all_success = (
            results["success"] and integration_result.success and smoke_result.success
        )

        print("\n" + "=" * 80)
        print("📊 Lifecycle Summary")
        print("=" * 80)
        print(f"Overall: {'✅ SUCCESS' if all_success else '❌ FAILED'}")
        print(f"   Deployment: {'✅' if results['success'] else '❌'}")
        print(f"   Integration: {'✅' if integration_result.success else '❌'}")
        print(f"   Smoke Tests: {'✅' if smoke_result.success else '❌'}")

    finally:
        await pipeline.close()


# =============================================================================
# Main Runner
# =============================================================================


async def main():
    """Run all CI/CD workflow examples."""
    print("\n" + "=" * 80)
    print("  Complete CI/CD Workflow Examples")
    print("  L2 Manager Integration Demonstration")
    print("=" * 80)

    examples = [
        ("PR Deployment", example_pr_deployment),
        ("Multi-PR Deployment", example_multi_pr_deployment),
        ("Full Lifecycle", example_full_lifecycle),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n" + "=" * 80)
    print("⚠️  Note: These examples require:")
    print("   • GITHUB_TOKEN environment variable")
    print("   • Docker daemon running")
    print("   • Valid GitHub repository")
    print("=" * 80 + "\n")

    # Run examples
    for name, func in examples:
        try:
            await func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")

        # Pause between examples
        await asyncio.sleep(2)

    print("\n" + "=" * 80)
    print("  Examples Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
