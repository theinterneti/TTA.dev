#!/usr/bin/env python3
"""
Examples of using UV primitives for dependency management across git worktrees

This script demonstrates:
- Composable UV workflows with SequentialPrimitive
- Worktree-aware dependency management
- Observability and error recovery patterns
- Cross-worktree package management

Run with: uv run python packages/tta-dev-primitives/examples/manage_uv_dependencies.py
"""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations.uv_primitive import (
    UVAddPrimitive,
    UVRunPrimitive,
    UVSyncPrimitive,
    WorktreeAwareUVPrimitive,
    create_dependency_management_workflow,
    create_worktree_sync_workflow,
)
from tta_dev_primitives.recovery import RetryPrimitive


async def example_basic_uv_operations():
    """Basic UV operations example"""
    print("=== Basic UV Operations ===")

    context = WorkflowContext(
        correlation_id="uv-example-1", data={"worktree_path": "."}
    )

    # Sync dependencies with extras
    sync_primitive = UVSyncPrimitive(with_extras=True)
    result = await sync_primitive.execute(context, {})
    print(f"Sync result: {result.success}, took {result.execution_time:.2f}s")

    # Add a package
    add_primitive = UVAddPrimitive(package="rich")
    result = await add_primitive.execute(context, {})
    print(f"Add rich: {result.success}")

    # Run a command
    run_primitive = UVRunPrimitive(command="python --version")
    result = await run_primitive.execute(context, {})
    print(f"Python version: {result.stdout.strip()}")


async def example_composable_workflows():
    """Composable UV workflows using SequentialPrimitive"""
    print("\n=== Composable UV Workflows ===")

    context = WorkflowContext(
        correlation_id="uv-example-2", data={"worktree_path": "."}
    )

    # Create a workflow: sync -> add packages -> run tests
    workflow = (
        UVSyncPrimitive(with_extras=True)
        >> UVAddPrimitive(package="pytest-cov")
        >> UVRunPrimitive(command="pytest --version")
    )

    result = await workflow.execute(context, {})
    print(f"Workflow completed: {result.success}")


async def example_worktree_aware_operations():
    """Worktree-aware UV operations"""
    print("\n=== Worktree-Aware Operations ===")

    context = WorkflowContext(correlation_id="uv-example-3")

    # Worktree-aware sync that detects current branch and adapts
    worktree_sync = WorktreeAwareUVPrimitive("sync", with_extras=True)
    result = await worktree_sync.execute(context, {})
    print(f"Worktree-aware sync: {result.success}")


async def example_dependency_management_workflow():
    """Complex dependency management workflow"""
    print("\n=== Dependency Management Workflow ===")

    context = WorkflowContext(
        correlation_id="uv-example-4", data={"worktree_path": "."}
    )

    # Create workflow for adding multiple packages
    workflow = create_dependency_management_workflow(
        packages_to_add=["click", "typer", "questionary"],
        packages_to_remove=[],  # None to remove
        sync_after=True,
    )

    result = await workflow.execute(context, {})
    print(f"Dependency management completed: {result.success}")


async def example_parallel_worktree_operations():
    """Parallel operations across different worktrees"""
    print("\n=== Parallel Worktree Operations ===")

    # This would require multiple worktree paths
    # Simulating parallel sync operations
    context1 = WorkflowContext(
        correlation_id="parallel-1",
        data={"worktree_path": "/home/thein/repos/TTA.dev"},  # main worktree
    )
    context2 = WorkflowContext(
        correlation_id="parallel-2",
        data={"worktree_path": "/home/thein/repos/TTA.dev-cline"},  # current worktree
    )

    # Create separate workflows
    workflow1 = create_worktree_sync_workflow(with_extras=True)
    workflow2 = create_worktree_sync_workflow(with_extras=True)

    # Run them sequentially for now (parallel would need proper worktree detection)
    result1 = await workflow1.execute(context1, {})
    result2 = await workflow2.execute(context2, {})

    print(f"Main worktree sync: {result1.success}")
    print(f"Current worktree sync: {result2.success}")


async def example_error_recovery():
    """Error recovery patterns with UV primitives"""
    print("\n=== Error Recovery Patterns ===")

    context = WorkflowContext(correlation_id="uv-example-5")

    # Wrap UV operation with retry for resilience
    unreliable_sync = RetryPrimitive(
        primitive=WorktreeAwareUVPrimitive("sync", with_extras=True),
        max_retries=3,
        backoff_strategy="exponential",
    )

    result = await unreliable_sync.execute(context, {})
    print(f"Resilient sync completed: {result.success}")


async def example_mixed_workflow():
    """Complex workflow mixing UV and other primitives"""
    print("\n=== Mixed Workflow Example ===")

    from tta_dev_primitives.testing import MockPrimitive

    context = WorkflowContext(
        correlation_id="uv-example-6", data={"worktree_path": "."}
    )

    # Mock analysis step + UV deployment
    mock_analysis = MockPrimitive(return_value={"analysis_complete": True})
    uv_sync = UVSyncPrimitive(with_extras=True)
    uv_run = UVRunPrimitive(command="echo 'Deployment complete'")

    # Chain: analyze -> sync -> deploy
    workflow = mock_analysis >> uv_sync >> uv_run

    result = await workflow.execute(context, {})
    print(f"Mixed workflow: {result.success}")


async def main():
    """Run all UV primitive examples"""
    print("🚀 TTA.dev UV Primitives Examples\n")

    try:
        await example_basic_uv_operations()
        await example_composable_workflows()
        await example_worktree_aware_operations()
        await example_dependency_management_workflow()
        await example_parallel_worktree_operations()
        await example_error_recovery()
        await example_mixed_workflow()

        print("\n✅ All UV primitive examples completed successfully!")

    except Exception as e:
        print(f"❌ Error in examples: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
