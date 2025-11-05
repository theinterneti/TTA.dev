"""
Docker SDK Wrapper - L4 Execution Layer.

Production-ready wrapper around Docker SDK with:
- Container lifecycle management
- Image operations
- Volume management
- Network operations
- Comprehensive error handling
- Observable execution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import docker
from docker.errors import APIError, ContainerError, ImageNotFound, NotFound
from docker.models.containers import Container
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


@dataclass
class DockerConfig:
    """Configuration for Docker SDK wrapper."""

    base_url: str | None = (
        None  # Docker daemon URL (defaults to unix:///var/run/docker.sock)
    )
    timeout: int = 60  # Request timeout in seconds
    version: str = "auto"  # API version
    tls: bool = False  # Use TLS


@dataclass
class DockerOperation:
    """Input for Docker operations."""

    operation: str  # "run_container", "build_image", "pull_image", etc.
    params: dict[str, Any]  # Operation-specific parameters


@dataclass
class DockerResult:
    """Output from Docker operations."""

    success: bool
    operation: str
    data: dict[str, Any] | None = None
    error: str | None = None


class DockerSDKWrapper(WorkflowPrimitive[DockerOperation, DockerResult]):
    """
    L4 Execution Wrapper for Docker SDK.

    Wraps Docker SDK with production-grade error handling, resource management,
    and observability.

    Supported Operations:
    - run_container: Run container from image
    - stop_container: Stop running container
    - remove_container: Remove container
    - list_containers: List containers
    - get_container_logs: Get container logs
    - build_image: Build image from Dockerfile
    - pull_image: Pull image from registry
    - push_image: Push image to registry
    - remove_image: Remove image
    - list_images: List images
    - create_volume: Create volume
    - remove_volume: Remove volume
    - list_volumes: List volumes
    - create_network: Create network
    - remove_network: Remove network

    Example:
        ```python
        wrapper = DockerSDKWrapper()

        # Run container
        operation = DockerOperation(
            operation="run_container",
            params={
                "image": "python:3.11",
                "command": "python --version",
                "remove": True
            }
        )

        context = WorkflowContext(correlation_id="req-123")
        result = await wrapper.execute(operation, context)

        if result.success:
            print(f"Container ID: {result.data['container_id']}")
            print(f"Output: {result.data['logs']}")
        ```
    """

    def __init__(self, config: DockerConfig | None = None):
        """
        Initialize Docker SDK wrapper.

        Args:
            config: Docker configuration. If None, uses defaults.
        """
        super().__init__()
        self.config = config or DockerConfig()

        # Initialize Docker client
        kwargs = {"version": self.config.version, "timeout": self.config.timeout}
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        if self.config.tls:
            kwargs["tls"] = True

        try:
            self.client = docker.DockerClient(**kwargs)
            # Test connection
            self.client.ping()
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Docker daemon: {e}. Is Docker running?"
            ) from e

    async def execute(
        self, input_data: DockerOperation, context: WorkflowContext
    ) -> DockerResult:
        """
        Execute Docker operation.

        Args:
            input_data: Operation to perform
            context: Workflow context for tracing

        Returns:
            Result of operation

        Raises:
            ValueError: Invalid operation or parameters
            APIError: Docker API errors
        """
        try:
            # Dispatch to operation handler
            operation_handlers = {
                "run_container": self._run_container,
                "stop_container": self._stop_container,
                "remove_container": self._remove_container,
                "list_containers": self._list_containers,
                "get_container_logs": self._get_container_logs,
                "build_image": self._build_image,
                "pull_image": self._pull_image,
                "push_image": self._push_image,
                "remove_image": self._remove_image,
                "list_images": self._list_images,
                "create_volume": self._create_volume,
                "remove_volume": self._remove_volume,
                "list_volumes": self._list_volumes,
                "create_network": self._create_network,
                "remove_network": self._remove_network,
            }

            handler = operation_handlers.get(input_data.operation)
            if not handler:
                raise ValueError(
                    f"Unknown operation: {input_data.operation}. "
                    f"Supported: {list(operation_handlers.keys())}"
                )

            # Execute operation
            data = handler(input_data.params)

            return DockerResult(success=True, operation=input_data.operation, data=data)

        except (APIError, ContainerError, ImageNotFound, NotFound) as e:
            return DockerResult(
                success=False,
                operation=input_data.operation,
                error=f"Docker error: {type(e).__name__}: {e}",
            )

        except Exception as e:
            return DockerResult(
                success=False,
                operation=input_data.operation,
                error=f"Unexpected error: {type(e).__name__}: {e}",
            )

    def _run_container(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run container from image."""
        if "image" not in params:
            raise ValueError("Missing required parameter: image")

        # Extract parameters
        image = params["image"]
        command = params.get("command")
        detach = params.get("detach", False)
        remove = params.get("remove", False)
        environment = params.get("environment", {})
        volumes = params.get("volumes", {})
        ports = params.get("ports", {})
        name = params.get("name")

        # Run container
        container: Container = self.client.containers.run(
            image=image,
            command=command,
            detach=detach,
            remove=remove,
            environment=environment,
            volumes=volumes,
            ports=ports,
            name=name,
        )

        result = {
            "container_id": container.id if hasattr(container, "id") else None,
            "name": container.name if hasattr(container, "name") else name,
        }

        # Get logs if not detached
        if not detach and hasattr(container, "logs"):
            result["logs"] = container.logs().decode("utf-8")

        # Get status if detached
        if detach and hasattr(container, "status"):
            container.reload()
            result["status"] = container.status

        return result

    def _stop_container(self, params: dict[str, Any]) -> dict[str, Any]:
        """Stop running container."""
        if "container_id" not in params:
            raise ValueError("Missing required parameter: container_id")

        container = self.client.containers.get(params["container_id"])
        timeout = params.get("timeout", 10)

        container.stop(timeout=timeout)
        container.reload()

        return {"container_id": container.id, "status": container.status}

    def _remove_container(self, params: dict[str, Any]) -> dict[str, Any]:
        """Remove container."""
        if "container_id" not in params:
            raise ValueError("Missing required parameter: container_id")

        container = self.client.containers.get(params["container_id"])
        force = params.get("force", False)
        v = params.get("v", False)  # Remove associated volumes

        container.remove(force=force, v=v)

        return {"container_id": container.id, "removed": True}

    def _list_containers(self, params: dict[str, Any]) -> dict[str, Any]:
        """List containers."""
        all_containers = params.get("all", False)
        filters = params.get("filters", {})

        containers = self.client.containers.list(all=all_containers, filters=filters)

        container_list = []
        for container in containers:
            container_list.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0]
                    if container.image.tags
                    else container.image.id,
                }
            )

        return {"containers": container_list, "count": len(container_list)}

    def _get_container_logs(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get container logs."""
        if "container_id" not in params:
            raise ValueError("Missing required parameter: container_id")

        container = self.client.containers.get(params["container_id"])
        timestamps = params.get("timestamps", False)
        tail = params.get("tail", "all")

        logs = container.logs(timestamps=timestamps, tail=tail).decode("utf-8")

        return {"container_id": container.id, "logs": logs}

    def _build_image(self, params: dict[str, Any]) -> dict[str, Any]:
        """Build image from Dockerfile."""
        if "path" not in params:
            raise ValueError("Missing required parameter: path")

        path = params["path"]
        tag = params.get("tag")
        dockerfile = params.get("dockerfile", "Dockerfile")
        buildargs = params.get("buildargs", {})
        nocache = params.get("nocache", False)
        rm = params.get("rm", True)

        image, build_logs = self.client.images.build(
            path=path,
            tag=tag,
            dockerfile=dockerfile,
            buildargs=buildargs,
            nocache=nocache,
            rm=rm,
        )

        # Process build logs
        log_lines = []
        for log in build_logs:
            if "stream" in log:
                log_lines.append(log["stream"].strip())

        return {
            "image_id": image.id,
            "tags": image.tags,
            "size": image.attrs.get("Size", 0),
            "build_logs": "\n".join(log_lines) if log_lines else None,
        }

    def _pull_image(self, params: dict[str, Any]) -> dict[str, Any]:
        """Pull image from registry."""
        if "repository" not in params:
            raise ValueError("Missing required parameter: repository")

        repository = params["repository"]
        tag = params.get("tag", "latest")

        image = self.client.images.pull(repository, tag=tag)

        return {
            "image_id": image.id,
            "tags": image.tags,
            "size": image.attrs.get("Size", 0),
        }

    def _push_image(self, params: dict[str, Any]) -> dict[str, Any]:
        """Push image to registry."""
        if "repository" not in params:
            raise ValueError("Missing required parameter: repository")

        repository = params["repository"]
        tag = params.get("tag", "latest")

        push_logs = self.client.images.push(repository, tag=tag)

        return {"repository": repository, "tag": tag, "pushed": True, "logs": push_logs}

    def _remove_image(self, params: dict[str, Any]) -> dict[str, Any]:
        """Remove image."""
        if "image" not in params:
            raise ValueError("Missing required parameter: image")

        image_id = params["image"]
        force = params.get("force", False)
        noprune = params.get("noprune", False)

        self.client.images.remove(image_id, force=force, noprune=noprune)

        return {"image": image_id, "removed": True}

    def _list_images(self, params: dict[str, Any]) -> dict[str, Any]:
        """List images."""
        name = params.get("name")
        all_images = params.get("all", False)
        filters = params.get("filters", {})

        images = self.client.images.list(name=name, all=all_images, filters=filters)

        image_list = []
        for image in images:
            image_list.append(
                {
                    "id": image.id,
                    "tags": image.tags,
                    "size": image.attrs.get("Size", 0),
                    "created": image.attrs.get("Created"),
                }
            )

        return {"images": image_list, "count": len(image_list)}

    def _create_volume(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create volume."""
        name = params.get("name")
        driver = params.get("driver", "local")
        driver_opts = params.get("driver_opts", {})
        labels = params.get("labels", {})

        volume = self.client.volumes.create(
            name=name, driver=driver, driver_opts=driver_opts, labels=labels
        )

        return {
            "name": volume.name,
            "driver": volume.attrs.get("Driver"),
            "mountpoint": volume.attrs.get("Mountpoint"),
        }

    def _remove_volume(self, params: dict[str, Any]) -> dict[str, Any]:
        """Remove volume."""
        if "name" not in params:
            raise ValueError("Missing required parameter: name")

        volume = self.client.volumes.get(params["name"])
        force = params.get("force", False)

        volume.remove(force=force)

        return {"name": params["name"], "removed": True}

    def _list_volumes(self, params: dict[str, Any]) -> dict[str, Any]:
        """List volumes."""
        filters = params.get("filters", {})

        volumes = self.client.volumes.list(filters=filters)

        volume_list = []
        for volume in volumes:
            volume_list.append(
                {
                    "name": volume.name,
                    "driver": volume.attrs.get("Driver"),
                    "mountpoint": volume.attrs.get("Mountpoint"),
                }
            )

        return {"volumes": volume_list, "count": len(volume_list)}

    def _create_network(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create network."""
        if "name" not in params:
            raise ValueError("Missing required parameter: name")

        name = params["name"]
        driver = params.get("driver", "bridge")
        options = params.get("options", {})
        labels = params.get("labels", {})

        network = self.client.networks.create(
            name=name, driver=driver, options=options, labels=labels
        )

        return {
            "id": network.id,
            "name": network.name,
            "driver": network.attrs.get("Driver"),
        }

    def _remove_network(self, params: dict[str, Any]) -> dict[str, Any]:
        """Remove network."""
        if "name" not in params:
            raise ValueError("Missing required parameter: name")

        network = self.client.networks.get(params["name"])
        network.remove()

        return {"name": params["name"], "removed": True}

    def close(self) -> None:
        """Close Docker client."""
        if hasattr(self, "client"):
            self.client.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
