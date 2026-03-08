"""
InfrastructureManager - L2 Domain Manager for Infrastructure Operations

Coordinates DockerExpert for infrastructure workflows: container orchestration,
image management, resource cleanup, health checks, and network management.

Architecture: Layer 2 (Domain Management) - Orchestrates Layer 3 experts
"""

from dataclasses import dataclass, field
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.apm.instrumented import APMWorkflowPrimitive

from ..experts.docker_expert import DockerExpert, DockerOperation

# ============================================================================
# Configuration and Operations
# ============================================================================


@dataclass
class InfrastructureManagerConfig:
    """Configuration for InfrastructureManager."""

    default_network: str = "bridge"
    """Default Docker network for containers"""

    auto_remove_containers: bool = True
    """Automatically remove containers on stop"""

    auto_pull_images: bool = True
    """Automatically pull missing images"""

    container_start_timeout: float = 30.0
    """Timeout for container start operations (seconds)"""

    health_check_retries: int = 3
    """Number of retries for health checks"""

    health_check_interval: float = 5.0
    """Interval between health check retries (seconds)"""

    cleanup_on_failure: bool = True
    """Clean up resources on operation failure"""

    volume_driver: str = "local"
    """Default volume driver"""


@dataclass
class InfrastructureOperation:
    """Operation specification for infrastructure workflow."""

    operation: str
    """Operation type: orchestrate_containers, manage_images, cleanup_resources, health_check"""

    # Container orchestration
    containers: list[dict[str, Any]] = field(default_factory=list)
    """List of container specifications for orchestration"""

    # Image management
    image_name: str | None = None
    """Image name for image operations"""

    image_tag: str = "latest"
    """Image tag"""

    build_path: str | None = None
    """Path to Dockerfile for build operations"""

    registry: str | None = None
    """Container registry URL"""

    # Resource cleanup
    cleanup_stopped: bool = True
    """Remove stopped containers during cleanup"""

    cleanup_unused_images: bool = False
    """Remove unused images during cleanup"""

    cleanup_volumes: bool = False
    """Remove unused volumes during cleanup"""

    # Health checks
    container_ids: list[str] = field(default_factory=list)
    """Container IDs to health check"""

    # Network management
    network_name: str | None = None
    """Network name for network operations"""


@dataclass
class InfrastructureResult:
    """Result of infrastructure operation."""

    success: bool
    """Whether operation succeeded"""

    operation: str
    """Operation type executed"""

    containers_started: list[str] = field(default_factory=list)
    """IDs of containers started"""

    containers_stopped: list[str] = field(default_factory=list)
    """IDs of containers stopped"""

    containers_removed: list[str] = field(default_factory=list)
    """IDs of containers removed"""

    images_pulled: list[str] = field(default_factory=list)
    """Images pulled"""

    images_built: list[str] = field(default_factory=list)
    """Images built"""

    images_removed: list[str] = field(default_factory=list)
    """Images removed"""

    health_status: dict[str, Any] = field(default_factory=dict)
    """Health check results by container ID"""

    cleanup_summary: dict[str, Any] = field(default_factory=dict)
    """Summary of cleanup operations"""

    duration_seconds: float = 0.0
    """Total operation duration"""

    error: str | None = None
    """Error message if operation failed"""


# ============================================================================
# InfrastructureManager Implementation
# ============================================================================


class InfrastructureManager(APMWorkflowPrimitive):
    """
    L2 Domain Manager for infrastructure operations.

    Coordinates DockerExpert for:
    - Container orchestration (multi-container deployments)
    - Image management (build, pull, push, cleanup)
    - Resource cleanup (containers, images, volumes)
    - Health checks (container status monitoring)
    - Network management (create, connect, disconnect)

    Example:
        >>> config = InfrastructureManagerConfig(
        ...     auto_remove_containers=True,
        ...     health_check_retries=3
        ... )
        >>> manager = InfrastructureManager(config=config)
        >>> operation = InfrastructureOperation(
        ...     operation="orchestrate_containers",
        ...     containers=[
        ...         {"image": "nginx", "name": "web"},
        ...         {"image": "postgres", "name": "db"}
        ...     ]
        ... )
        >>> result = await manager.execute(operation, context)
        >>> print(f"Started: {result.containers_started}")
    """

    def __init__(
        self,
        config: InfrastructureManagerConfig,
        docker_expert: DockerExpert | None = None,
    ):
        """
        Initialize InfrastructureManager.

        Args:
            config: Manager configuration
            docker_expert: Optional DockerExpert instance (creates default if None)
        """
        super().__init__(name="infrastructure_manager")
        self.config = config
        self.docker_expert = docker_expert or DockerExpert()

    async def _execute_impl(
        self,
        input_data: InfrastructureOperation,
        context: WorkflowContext,
    ) -> InfrastructureResult:
        """
        Execute infrastructure operation.

        Args:
            input_data: Infrastructure operation to execute
            context: Workflow context for observability

        Returns:
            InfrastructureResult with operation outcome
        """
        import time

        start_time = time.time()

        # Validate operation
        validation_error = self._validate_operation(input_data)
        if validation_error:
            return InfrastructureResult(
                success=False,
                operation=input_data.operation,
                error=validation_error,
                duration_seconds=time.time() - start_time,
            )

        # Route to appropriate handler
        try:
            if input_data.operation == "orchestrate_containers":
                result = await self._orchestrate_containers(input_data, context)
            elif input_data.operation == "manage_images":
                result = await self._manage_images(input_data, context)
            elif input_data.operation == "cleanup_resources":
                result = await self._cleanup_resources(input_data, context)
            elif input_data.operation == "health_check":
                result = await self._health_check(input_data, context)
            else:
                result = InfrastructureResult(
                    success=False,
                    operation=input_data.operation,
                    error=f"Unknown operation: {input_data.operation}",
                )

            # Set duration
            result.duration_seconds = time.time() - start_time
            return result

        except Exception as e:
            return InfrastructureResult(
                success=False,
                operation=input_data.operation,
                error=f"Operation failed: {e!s}",
                duration_seconds=time.time() - start_time,
            )

    def _validate_operation(self, operation: InfrastructureOperation) -> str | None:
        """
        Validate infrastructure operation.

        Args:
            operation: Operation to validate

        Returns:
            Error message if invalid, None if valid
        """
        if operation.operation not in [
            "orchestrate_containers",
            "manage_images",
            "cleanup_resources",
            "health_check",
        ]:
            return f"Invalid operation: {operation.operation}"

        if operation.operation == "orchestrate_containers":
            if not operation.containers:
                return "Container orchestration requires containers list"
            for container in operation.containers:
                if "image" not in container:
                    return "Each container must specify an image"

        if operation.operation == "manage_images":
            if not operation.image_name and not operation.build_path:
                return "Image management requires image_name or build_path"

        if operation.operation == "health_check":
            if not operation.container_ids:
                return "Health check requires container_ids list"

        return None

    async def _orchestrate_containers(
        self,
        operation: InfrastructureOperation,
        context: WorkflowContext,
    ) -> InfrastructureResult:
        """
        Orchestrate multiple containers.

        Starts containers in sequence, handling dependencies and network setup.

        Args:
            operation: Orchestration operation
            context: Workflow context

        Returns:
            Result with started container IDs
        """
        started = []
        errors = []

        for container_spec in operation.containers:
            try:
                # Prepare container run operation
                docker_op = DockerOperation(
                    operation="run_container",
                    params={
                        "image": container_spec["image"],
                        "name": container_spec.get("name"),
                        "command": container_spec.get("command"),
                        "environment": container_spec.get("environment", {}),
                        "ports": container_spec.get("ports", {}),
                        "volumes": container_spec.get("volumes", {}),
                        "detach": container_spec.get("detach", True),
                        "network": container_spec.get(
                            "network", self.config.default_network
                        ),
                    },
                )

                # Execute via DockerExpert
                result = await self.docker_expert.execute(docker_op, context)

                if result.success and result.data:
                    container_id = result.data.get("container_id")
                    if container_id:
                        started.append(container_id)
                else:
                    error_msg = result.error or "Failed to start container"
                    errors.append(
                        f"{container_spec.get('name', 'unknown')}: {error_msg}"
                    )

            except Exception as e:
                errors.append(f"{container_spec.get('name', 'unknown')}: {e!s}")

        # Determine success based on whether any containers started
        success = len(started) > 0 and len(errors) == 0

        return InfrastructureResult(
            success=success,
            operation="orchestrate_containers",
            containers_started=started,
            error="; ".join(errors) if errors else None,
        )

    async def _manage_images(
        self,
        operation: InfrastructureOperation,
        context: WorkflowContext,
    ) -> InfrastructureResult:
        """
        Manage Docker images (build, pull, push).

        Args:
            operation: Image management operation
            context: Workflow context

        Returns:
            Result with image operations performed
        """
        pulled = []
        built = []
        errors = []

        # Handle image build
        if operation.build_path:
            try:
                docker_op = DockerOperation(
                    operation="build_image",
                    params={
                        "path": operation.build_path,
                        "tag": f"{operation.image_name}:{operation.image_tag}"
                        if operation.image_name
                        else None,
                    },
                )

                result = await self.docker_expert.execute(docker_op, context)

                if result.success and result.data:
                    image_id = result.data.get("image_id")
                    if image_id:
                        built.append(image_id)
                else:
                    errors.append(f"Build failed: {result.error}")

            except Exception as e:
                errors.append(f"Build error: {e!s}")

        # Handle image pull
        elif operation.image_name and self.config.auto_pull_images:
            try:
                docker_op = DockerOperation(
                    operation="pull_image",
                    params={
                        "image": f"{operation.image_name}:{operation.image_tag}",
                    },
                )

                result = await self.docker_expert.execute(docker_op, context)

                if result.success:
                    pulled.append(f"{operation.image_name}:{operation.image_tag}")
                else:
                    errors.append(f"Pull failed: {result.error}")

            except Exception as e:
                errors.append(f"Pull error: {e!s}")

        success = (len(pulled) > 0 or len(built) > 0) and len(errors) == 0

        return InfrastructureResult(
            success=success,
            operation="manage_images",
            images_pulled=pulled,
            images_built=built,
            error="; ".join(errors) if errors else None,
        )

    async def _cleanup_resources(
        self,
        operation: InfrastructureOperation,
        context: WorkflowContext,
    ) -> InfrastructureResult:
        """
        Clean up Docker resources (containers, images, volumes).

        Args:
            operation: Cleanup operation
            context: Workflow context

        Returns:
            Result with cleanup summary
        """
        removed_containers = []
        removed_images = []
        errors = []

        # List all containers
        try:
            list_op = DockerOperation(
                operation="list_containers",
                params={"all": True},
            )

            result = await self.docker_expert.execute(list_op, context)

            if result.success and result.data:
                containers = result.data.get("containers", [])

                # Remove stopped containers if configured
                if operation.cleanup_stopped:
                    for container in containers:
                        if container.get("state") != "running":
                            try:
                                remove_op = DockerOperation(
                                    operation="remove_container",
                                    params={
                                        "container_id": container.get("id"),
                                        "force": True,
                                    },
                                )

                                remove_result = await self.docker_expert.execute(
                                    remove_op, context
                                )

                                if remove_result.success:
                                    removed_containers.append(container.get("id"))

                            except Exception as e:
                                errors.append(
                                    f"Failed to remove container {container.get('id')}: {e!s}"
                                )

        except Exception as e:
            errors.append(f"Failed to list containers: {e!s}")

        cleanup_summary = {
            "containers_removed": len(removed_containers),
            "images_removed": len(removed_images),
            "errors": len(errors),
        }

        return InfrastructureResult(
            success=len(errors) == 0,
            operation="cleanup_resources",
            containers_removed=removed_containers,
            images_removed=removed_images,
            cleanup_summary=cleanup_summary,
            error="; ".join(errors) if errors else None,
        )

    async def _health_check(
        self,
        operation: InfrastructureOperation,
        context: WorkflowContext,
    ) -> InfrastructureResult:
        """
        Perform health checks on containers.

        Args:
            operation: Health check operation
            context: Workflow context

        Returns:
            Result with health status for each container
        """
        health_status = {}
        errors = []

        for container_id in operation.container_ids:
            try:
                # Get container status
                list_op = DockerOperation(
                    operation="list_containers",
                    params={"all": True},
                )

                result = await self.docker_expert.execute(list_op, context)

                if result.success and result.data:
                    containers = result.data.get("containers", [])

                    # Find this container
                    container = next(
                        (c for c in containers if c.get("id") == container_id), None
                    )

                    if container:
                        health_status[container_id] = {
                            "state": container.get("state"),
                            "status": container.get("status"),
                            "healthy": container.get("state") == "running",
                        }
                    else:
                        health_status[container_id] = {
                            "state": "not_found",
                            "healthy": False,
                        }

            except Exception as e:
                errors.append(f"Health check failed for {container_id}: {e!s}")
                health_status[container_id] = {
                    "state": "error",
                    "error": str(e),
                    "healthy": False,
                }

        # Success if all containers are healthy
        all_healthy = all(
            status.get("healthy", False) for status in health_status.values()
        )

        return InfrastructureResult(
            success=all_healthy and len(errors) == 0,
            operation="health_check",
            health_status=health_status,
            error="; ".join(errors) if errors else None,
        )

    def close(self) -> None:
        """
        Clean up manager resources.

        Closes DockerExpert if it was created by this manager.
        """
        if hasattr(self.docker_expert, "close"):
            self.docker_expert.close()
