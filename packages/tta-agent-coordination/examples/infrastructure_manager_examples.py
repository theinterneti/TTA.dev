"""
InfrastructureManager Usage Examples

Demonstrates real-world usage of InfrastructureManager for Docker orchestration.

Examples:
1. Single Container Deployment
2. Multi-Container Stack (Web + DB + Cache)
3. Image Build and Deployment
4. Health Monitoring Workflow
5. Resource Cleanup Automation
6. Custom Network Configuration
7. Development Environment Setup
8. Complete Infrastructure Workflow

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

# =============================================================================
# Example 1: Single Container Deployment
# =============================================================================


async def example_single_container():
    """Deploy a single NGINX web server."""
    print("\n" + "=" * 80)
    print("Example 1: Single Container Deployment")
    print("=" * 80 + "\n")

    # Initialize manager
    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(
            auto_pull_images=True,  # Automatically pull if image not found locally
            container_start_timeout=30.0,
        )
    )

    # Create context
    context = WorkflowContext(correlation_id="example-1")

    try:
        # Deploy NGINX container
        operation = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "nginx:latest",
                    "name": "web-server",
                    "ports": {"80": "8080"},  # Map container port 80 to host port 8080
                    "detach": True,
                }
            ],
        )

        result = await manager.execute(operation, context)

        if result.success:
            print(f"✅ Container deployed: {result.containers_started}")
            print("   Access at: http://localhost:8080")
        else:
            print(f"❌ Deployment failed: {result.error}")

    finally:
        await manager.close()


# =============================================================================
# Example 2: Multi-Container Stack (Web + DB + Cache)
# =============================================================================


async def example_multi_container_stack():
    """Deploy a complete application stack with web server, database, and cache."""
    print("\n" + "=" * 80)
    print("Example 2: Multi-Container Stack (Web + Database + Cache)")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(
            default_network="app-network",  # All containers on same network
            auto_pull_images=True,
            health_check_retries=3,
        )
    )

    context = WorkflowContext(correlation_id="example-2")

    try:
        # Deploy complete stack
        operation = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                # Database (deploy first - dependencies need it)
                {
                    "image": "postgres:15",
                    "name": "db",
                    "environment": {
                        "POSTGRES_DB": "myapp",
                        "POSTGRES_USER": "admin",
                        "POSTGRES_PASSWORD": "secret123",
                    },
                    "volumes": {"db-data": "/var/lib/postgresql/data"},
                    "detach": True,
                },
                # Cache (deploy second)
                {
                    "image": "redis:7",
                    "name": "cache",
                    "ports": {"6379": "6379"},
                    "detach": True,
                },
                # Web application (deploy last - depends on db and cache)
                {
                    "image": "nginx:latest",  # Replace with your app image
                    "name": "web",
                    "ports": {"80": "3000"},
                    "environment": {
                        "DATABASE_URL": "postgresql://admin:secret123@db:5432/myapp",
                        "REDIS_URL": "redis://cache:6379",
                    },
                    "detach": True,
                },
            ],
        )

        result = await manager.execute(operation, context)

        if result.success:
            print("✅ Stack deployed successfully!")
            print(f"   Containers: {', '.join(result.containers_started)}")
            print("   Web: http://localhost:3000")
            print("   Redis: localhost:6379")

            # Check health
            health_op = InfrastructureOperation(
                operation="health_check", container_ids=result.containers_started
            )
            health_result = await manager.execute(health_op, context)

            print("\n📊 Health Status:")
            for container, status in health_result.health_status.items():
                emoji = "✅" if status == "healthy" else "⚠️"
                print(f"   {emoji} {container}: {status}")

        else:
            print(f"❌ Stack deployment failed: {result.error}")

    finally:
        await manager.close()


# =============================================================================
# Example 3: Image Build and Deployment
# =============================================================================


async def example_image_build_deploy():
    """Build a custom Docker image and deploy it."""
    print("\n" + "=" * 80)
    print("Example 3: Image Build and Deployment")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(auto_pull_images=True)
    )

    context = WorkflowContext(correlation_id="example-3")

    try:
        # Step 1: Build custom image
        print("📦 Building custom image...")
        build_op = InfrastructureOperation(
            operation="manage_images",
            image_params={
                "action": "build",
                "path": "./app",  # Directory containing Dockerfile
                "tag": "myapp:v1.0.0",
                "dockerfile": "Dockerfile",
            },
        )

        build_result = await manager.execute(build_op, context)

        if not build_result.success:
            print(f"❌ Build failed: {build_result.error}")
            return

        print(f"✅ Image built: {build_result.images_built}")

        # Step 2: Deploy the built image
        print("\n🚀 Deploying built image...")
        deploy_op = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "myapp:v1.0.0",
                    "name": "myapp-server",
                    "ports": {"8000": "8000"},
                    "environment": {"ENV": "production"},
                    "detach": True,
                }
            ],
        )

        deploy_result = await manager.execute(deploy_op, context)

        if deploy_result.success:
            print(f"✅ Application deployed: {deploy_result.containers_started}")
            print("   Access at: http://localhost:8000")
        else:
            print(f"❌ Deployment failed: {deploy_result.error}")

    finally:
        await manager.close()


# =============================================================================
# Example 4: Health Monitoring Workflow
# =============================================================================


async def example_health_monitoring():
    """Monitor container health with automatic retry and reporting."""
    print("\n" + "=" * 80)
    print("Example 4: Health Monitoring Workflow")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(
            health_check_retries=5,  # Retry 5 times
            health_check_interval=2.0,  # Wait 2 seconds between retries
        )
    )

    context = WorkflowContext(correlation_id="example-4")

    try:
        # First, deploy some containers to monitor
        print("🚀 Deploying containers to monitor...")
        deploy_op = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {"image": "nginx:latest", "name": "web1", "detach": True},
                {"image": "redis:7", "name": "cache1", "detach": True},
            ],
        )

        deploy_result = await manager.execute(deploy_op, context)

        if not deploy_result.success:
            print(f"❌ Deployment failed: {deploy_result.error}")
            return

        print(f"✅ Containers deployed: {deploy_result.containers_started}\n")

        # Monitor health in a loop
        print("📊 Starting health monitoring (10 second interval)...")
        for i in range(3):  # Monitor for 3 cycles
            await asyncio.sleep(10 if i > 0 else 2)  # Wait before first check

            health_op = InfrastructureOperation(
                operation="health_check",
                container_ids=deploy_result.containers_started,
            )

            health_result = await manager.execute(health_op, context)

            print(f"\n⏰ Health Check #{i + 1}:")
            all_healthy = True
            for container, status in health_result.health_status.items():
                emoji = "✅" if status == "healthy" else "❌"
                print(f"   {emoji} {container}: {status}")
                if status != "healthy":
                    all_healthy = False

            if all_healthy:
                print("   🎉 All containers healthy!")
            else:
                print("   ⚠️  Some containers unhealthy - check logs")

    finally:
        await manager.close()


# =============================================================================
# Example 5: Resource Cleanup Automation
# =============================================================================


async def example_resource_cleanup():
    """Automatically clean up stopped containers and unused images."""
    print("\n" + "=" * 80)
    print("Example 5: Resource Cleanup Automation")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(cleanup_on_failure=True)
    )

    context = WorkflowContext(correlation_id="example-5")

    try:
        # Perform cleanup
        print("🧹 Cleaning up Docker resources...")
        cleanup_op = InfrastructureOperation(
            operation="cleanup_resources",
            cleanup_stopped_containers=True,
            cleanup_unused_images=True,
            force_remove=False,  # Safe cleanup (don't force)
        )

        result = await manager.execute(cleanup_op, context)

        if result.success:
            print("✅ Cleanup complete!")
            print(
                f"   Containers removed: {len(result.containers_removed)} "
                f"({', '.join(result.containers_removed) if result.containers_removed else 'none'})"
            )
            print(
                f"   Images removed: {len(result.images_removed)} "
                f"({', '.join(result.images_removed) if result.images_removed else 'none'})"
            )

            if result.cleanup_summary:
                print("\n📊 Cleanup Summary:")
                for key, value in result.cleanup_summary.items():
                    print(f"   {key}: {value}")
        else:
            print(f"❌ Cleanup failed: {result.error}")

    finally:
        await manager.close()


# =============================================================================
# Example 6: Custom Network Configuration
# =============================================================================


async def example_custom_network():
    """Deploy containers with custom network configuration."""
    print("\n" + "=" * 80)
    print("Example 6: Custom Network Configuration")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(
            default_network="frontend-network",  # Custom network name
            auto_remove_containers=False,  # Keep containers for inspection
        )
    )

    context = WorkflowContext(correlation_id="example-6")

    try:
        # Deploy with custom network
        operation = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "nginx:latest",
                    "name": "frontend-1",
                    "networks": ["frontend-network"],
                    "detach": True,
                },
                {
                    "image": "nginx:latest",
                    "name": "frontend-2",
                    "networks": ["frontend-network"],
                    "detach": True,
                },
            ],
        )

        result = await manager.execute(operation, context)

        if result.success:
            print("✅ Containers deployed on custom network!")
            print("   Network: frontend-network")
            print(f"   Containers: {', '.join(result.containers_started)}")
            print("\n💡 Containers can communicate using container names:")
            print("   frontend-1 can reach frontend-2 at http://frontend-2:80")
        else:
            print(f"❌ Deployment failed: {result.error}")

    finally:
        await manager.close()


# =============================================================================
# Example 7: Development Environment Setup
# =============================================================================


async def example_dev_environment():
    """Set up a complete development environment with all services."""
    print("\n" + "=" * 80)
    print("Example 7: Development Environment Setup")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(
            default_network="dev-network",
            auto_pull_images=True,
            health_check_retries=5,
            cleanup_on_failure=True,  # Clean up if setup fails
        )
    )

    context = WorkflowContext(correlation_id="example-7")

    try:
        print("🚀 Setting up development environment...\n")

        # Step 1: Pull required images
        print("📦 Pulling images...")
        for image in ["postgres:15", "redis:7", "nginx:latest"]:
            pull_op = InfrastructureOperation(
                operation="manage_images",
                image_params={"action": "pull", "image": image},
            )
            pull_result = await manager.execute(pull_op, context)
            status = "✅" if pull_result.success else "❌"
            print(f"   {status} {image}")

        # Step 2: Deploy development stack
        print("\n🏗️  Deploying services...")
        deploy_op = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "postgres:15",
                    "name": "dev-db",
                    "environment": {
                        "POSTGRES_DB": "devdb",
                        "POSTGRES_USER": "dev",
                        "POSTGRES_PASSWORD": "devpass",
                    },
                    "ports": {"5432": "5432"},
                    "volumes": {"dev-db-data": "/var/lib/postgresql/data"},
                    "detach": True,
                },
                {
                    "image": "redis:7",
                    "name": "dev-cache",
                    "ports": {"6379": "6379"},
                    "detach": True,
                },
                {
                    "image": "nginx:latest",
                    "name": "dev-proxy",
                    "ports": {"80": "8080"},
                    "detach": True,
                },
            ],
        )

        deploy_result = await manager.execute(deploy_op, context)

        if not deploy_result.success:
            print(f"❌ Deployment failed: {deploy_result.error}")
            return

        print(f"✅ Services deployed: {', '.join(deploy_result.containers_started)}")

        # Step 3: Wait for services to be healthy
        print("\n⏳ Waiting for services to be healthy...")
        await asyncio.sleep(5)  # Give services time to start

        health_op = InfrastructureOperation(
            operation="health_check", container_ids=deploy_result.containers_started
        )
        health_result = await manager.execute(health_op, context)

        print("\n📊 Service Health:")
        for container, status in health_result.health_status.items():
            emoji = "✅" if status == "healthy" else "⚠️"
            print(f"   {emoji} {container}: {status}")

        print("\n🎉 Development environment ready!")
        print("\n📝 Connection Details:")
        print("   PostgreSQL: postgresql://dev:devpass@localhost:5432/devdb")
        print("   Redis:      redis://localhost:6379")
        print("   Proxy:      http://localhost:8080")

    finally:
        await manager.close()


# =============================================================================
# Example 8: Complete Infrastructure Workflow
# =============================================================================


async def example_complete_workflow():
    """
    Complete infrastructure workflow:
    1. Build custom image
    2. Deploy multi-container stack
    3. Monitor health
    4. Clean up on completion
    """
    print("\n" + "=" * 80)
    print("Example 8: Complete Infrastructure Workflow")
    print("=" * 80 + "\n")

    manager = InfrastructureManager(
        config=InfrastructureManagerConfig(
            default_network="prod-network",
            auto_pull_images=True,
            health_check_retries=3,
            cleanup_on_failure=True,
        )
    )

    context = WorkflowContext(correlation_id="example-8")

    containers_deployed = []

    try:
        # Phase 1: Image Management
        print("📦 Phase 1: Image Management")
        print("-" * 40)

        # Pull base images
        for image in ["nginx:latest", "redis:7"]:
            pull_op = InfrastructureOperation(
                operation="manage_images",
                image_params={"action": "pull", "image": image},
            )
            result = await manager.execute(pull_op, context)
            print(f"   {'✅' if result.success else '❌'} Pulled {image}")

        # Phase 2: Container Orchestration
        print("\n🚀 Phase 2: Container Orchestration")
        print("-" * 40)

        deploy_op = InfrastructureOperation(
            operation="orchestrate_containers",
            containers=[
                {
                    "image": "redis:7",
                    "name": "app-cache",
                    "ports": {"6379": "6379"},
                    "detach": True,
                },
                {
                    "image": "nginx:latest",
                    "name": "app-web",
                    "ports": {"80": "8888"},
                    "detach": True,
                },
            ],
        )

        deploy_result = await manager.execute(deploy_op, context)

        if not deploy_result.success:
            print(f"   ❌ Deployment failed: {deploy_result.error}")
            return

        containers_deployed = deploy_result.containers_started
        print(f"   ✅ Deployed: {', '.join(containers_deployed)}")

        # Phase 3: Health Monitoring
        print("\n📊 Phase 3: Health Monitoring")
        print("-" * 40)

        await asyncio.sleep(2)  # Let containers start

        health_op = InfrastructureOperation(
            operation="health_check", container_ids=containers_deployed
        )
        health_result = await manager.execute(health_op, context)

        all_healthy = True
        for container, status in health_result.health_status.items():
            emoji = "✅" if status == "healthy" else "❌"
            print(f"   {emoji} {container}: {status}")
            if status != "healthy":
                all_healthy = False

        if all_healthy:
            print("\n   🎉 All services healthy and running!")
        else:
            print("\n   ⚠️  Some services unhealthy")

        # Phase 4: Cleanup (optional)
        print("\n🧹 Phase 4: Resource Cleanup (commented out)")
        print("-" * 40)
        print("   💡 Uncomment to clean up stopped containers")
        print("   💡 Containers are still running - use Docker CLI to stop")

        # Uncomment to perform cleanup:
        # cleanup_op = InfrastructureOperation(
        #     operation="cleanup_resources",
        #     cleanup_stopped_containers=True,
        #     cleanup_unused_images=False,
        # )
        # cleanup_result = await manager.execute(cleanup_op, context)
        # print(f"   ✅ Cleanup: {len(cleanup_result.containers_removed)} containers removed")

        print("\n✅ Workflow complete!")

    finally:
        await manager.close()


# =============================================================================
# Main Runner
# =============================================================================


async def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print("  InfrastructureManager Usage Examples")
    print("=" * 80)

    examples = [
        ("1", "Single Container", example_single_container),
        ("2", "Multi-Container Stack", example_multi_container_stack),
        ("3", "Image Build & Deploy", example_image_build_deploy),
        ("4", "Health Monitoring", example_health_monitoring),
        ("5", "Resource Cleanup", example_resource_cleanup),
        ("6", "Custom Network", example_custom_network),
        ("7", "Dev Environment", example_dev_environment),
        ("8", "Complete Workflow", example_complete_workflow),
    ]

    print("\nAvailable examples:")
    for num, name, _ in examples:
        print(f"  {num}. {name}")

    print("\nRunning all examples...")
    print("(In production, you'd run these individually)\n")

    # Run each example
    for num, name, func in examples:
        try:
            await func()
        except Exception as e:
            print(f"\n❌ Example {num} failed: {e}")

        # Pause between examples
        await asyncio.sleep(2)

    print("\n" + "=" * 80)
    print("  All examples complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
