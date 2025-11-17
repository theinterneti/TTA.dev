"""
Simple Infrastructure Manager Example

Demonstrates how to use InfrastructureManager with the actual API.

This example shows infrastructure operations:
- orchestrate_containers: Deploy multi-container applications
- manage_images: Build, pull, push images
- health_check: Monitor container health
- cleanup_resources: Remove unused resources

Requirements:
- Docker daemon running
- tta-agent-coordination package installed
"""

import asyncio

from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.managers import (
    InfrastructureManager,
    InfrastructureManagerConfig,
    InfrastructureOperation,
)


async def example_orchestrate_containers():
    """Example: Deploy multiple containers."""
    print("\n" + "=" * 80)
    print("Example 1: Orchestrate Containers")
    print("=" * 80 + "\n")

    # Configure manager
    config = InfrastructureManagerConfig(
        default_network="bridge",
        auto_remove_containers=True,
        auto_pull_images=True,
        container_start_timeout=30.0,
        cleanup_on_failure=True,
    )

    manager = InfrastructureManager(config)

    try:
        # Create operation with multiple containers
        operation = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "nginx:latest",
                    "name": "web-server",
                    "ports": {"80": "8080"},
                    "detach": True,
                },
                {
                    "image": "redis:alpine",
                    "name": "cache",
                    "ports": {"6379": "6379"},
                    "detach": True,
                },
            ],
        )

        # Execute
        context = WorkflowContext(correlation_id="orchestrate-example")
        result = await manager.execute(operation, context)

        # Print results
        print(f"Success: {result.success}")
        print(f"Containers Started: {result.containers_started}")

        if result.error:
            print(f"Error: {result.error}")

    finally:
        manager.close()  # Note: close() is NOT async


async def example_manage_images():
    """Example: Build Docker image."""
    print("\n" + "=" * 80)
    print("Example 2: Build Docker Image")
    print("=" * 80 + "\n")

    config = InfrastructureManagerConfig(
        auto_pull_images=True,
    )

    manager = InfrastructureManager(config)

    try:
        # Build image operation
        operation = InfrastructureOperation(
            operation="manage_images",
            image_name="myapp",
            image_tag="v1.0.0",
            build_path=".",  # Path to Dockerfile directory
        )

        context = WorkflowContext(correlation_id="build-image-example")
        result = await manager.execute(operation, context)

        print(f"Build Success: {result.success}")
        if result.images_built:
            print(f"Images Built: {result.images_built}")

    finally:
        manager.close()


async def example_health_check():
    """Example: Check container health."""
    print("\n" + "=" * 80)
    print("Example 3: Health Check")
    print("=" * 80 + "\n")

    config = InfrastructureManagerConfig(
        health_check_retries=3,
        health_check_interval=5.0,
    )

    manager = InfrastructureManager(config)

    try:
        # First, start a container to check
        start_op = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "nginx:alpine",
                    "name": "health-test",
                    "detach": True,
                }
            ],
        )

        context = WorkflowContext(correlation_id="health-example")
        start_result = await manager.execute(start_op, context)

        if start_result.success and start_result.containers_started:
            # Now check health
            health_op = InfrastructureOperation(
                operation="health_check",
                container_ids=start_result.containers_started,
            )

            health_result = await manager.execute(health_op, context)

            print(f"Health Check Success: {health_result.success}")
            print(f"Health Status: {health_result.health_status}")

    finally:
        manager.close()


async def example_cleanup_resources():
    """Example: Clean up Docker resources."""
    print("\n" + "=" * 80)
    print("Example 4: Cleanup Resources")
    print("=" * 80 + "\n")

    config = InfrastructureManagerConfig(
        auto_remove_containers=False,  # Keep containers for cleanup demo
        cleanup_on_failure=True,
    )

    manager = InfrastructureManager(config)

    try:
        # Cleanup operation
        operation = InfrastructureOperation(
            operation="cleanup_resources",
            cleanup_stopped=True,  # Remove stopped containers
            cleanup_unused_images=False,  # Keep images
            cleanup_volumes=False,  # Keep volumes
        )

        context = WorkflowContext(correlation_id="cleanup-example")
        result = await manager.execute(operation, context)

        print(f"Cleanup Success: {result.success}")
        print(f"Containers Removed: {len(result.containers_removed)}")
        print(f"Images Removed: {len(result.images_removed)}")

        if result.cleanup_summary:
            print(f"Cleanup Summary: {result.cleanup_summary}")

    finally:
        manager.close()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  Infrastructure Manager Examples")
    print("  Real API Demonstration")
    print("=" * 80)

    print("\n⚠️  Note: These examples use the ACTUAL InfrastructureManager API")
    print("   Ensure Docker daemon is running\n")

    # Run examples
    await example_orchestrate_containers()
    await example_manage_images()
    await example_health_check()
    await example_cleanup_resources()

    print("\n" + "=" * 80)
    print("  Examples Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
