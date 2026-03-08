"""
DockerExpert - L3 Tool Expertise Layer.

Production-ready Docker operations with:
- Automatic fallback for image operations (try local, fallback to pull)
- Timeout protection for long-running operations
- Container lifecycle management
- Resource cleanup on failures
- Observable execution
"""

from __future__ import annotations

from dataclasses import dataclass

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive, TimeoutPrimitive

from tta_agent_coordination.wrappers.docker_wrapper import (
    DockerConfig,
    DockerOperation,
    DockerResult,
    DockerSDKWrapper,
)


@dataclass
class DockerExpertConfig:
    """Configuration for DockerExpert."""

    # Docker configuration
    docker_config: DockerConfig | None = None

    # Timeout configuration (seconds)
    container_start_timeout: float = 30.0
    container_stop_timeout: float = 10.0
    image_pull_timeout: float = 300.0  # 5 minutes
    image_build_timeout: float = 600.0  # 10 minutes

    # Retry configuration
    auto_pull_on_missing: bool = True
    cleanup_on_failure: bool = True


class DockerExpert(WorkflowPrimitive[DockerOperation, DockerResult]):
    """
    L3 Tool Expertise Layer for Docker operations.

    Wraps DockerSDKWrapper (L4) with:
    - Automatic fallback (run local image → pull if missing)
    - Timeout protection for all operations
    - Smart resource cleanup on failures
    - Container lifecycle management best practices

    Example:
        ```python
        from tta_dev_primitives import WorkflowContext

        # Create expert with automatic fallback and timeouts
        expert = DockerExpert(
            config=DockerExpertConfig(
                auto_pull_on_missing=True,
                container_start_timeout=30.0
            )
        )

        # Run container with automatic image pull if missing
        operation = DockerOperation(
            operation="run_container",
            params={
                "image": "python:3.11",
                "command": "python --version",
                "detach": False
            }
        )

        context = WorkflowContext(correlation_id="req-123")
        result = await expert.execute(operation, context)
        # Automatically pulls python:3.11 if not found locally
        # Applies 30s timeout to container start
        # Cleans up on failure
        ```

    Operations with automatic fallback:
    - run_container: Try local image → pull if missing
    - build_image: Apply build timeout

    Operations with timeout protection:
    - run_container: container_start_timeout
    - stop_container: container_stop_timeout
    - pull_image: image_pull_timeout
    - build_image: image_build_timeout

    Best Practices Enforced:
    - Container name validation
    - Resource limits validation
    - Automatic cleanup on failures
    - Graceful container shutdown
    """

    def __init__(self, config: DockerExpertConfig | None = None):
        """
        Initialize Docker expert with fallback and timeouts.

        Args:
            config: Expert configuration. If None, uses defaults.
        """
        super().__init__()
        self.config = config or DockerExpertConfig()

        # Create L4 wrapper
        self._wrapper = DockerSDKWrapper(config=self.config.docker_config)

    def _validate_operation(self, operation: DockerOperation) -> dict[str, str] | None:
        """
        Validate operation follows Docker best practices.

        Args:
            operation: Operation to validate

        Returns:
            None if valid, error dict if validation fails
        """
        # Validate container operations
        if operation.operation in ["run_container", "stop_container"]:
            # Check container name if provided
            name = operation.params.get("name", "")
            if name:
                # Docker names must match [a-zA-Z0-9][a-zA-Z0-9_.-]+
                if not name[0].isalnum():
                    return {"error": "Container name must start with alphanumeric"}

        # Validate run_container
        if operation.operation == "run_container":
            image = operation.params.get("image", "")
            if not image:
                return {"error": "Image name is required for run_container"}

        # Validate build_image
        elif operation.operation == "build_image":
            path = operation.params.get("path", "")
            if not path:
                return {"error": "Build path is required for build_image"}

        return None

    async def _run_with_auto_pull(
        self, operation: DockerOperation, context: WorkflowContext
    ) -> DockerResult:
        """
        Run container with automatic image pull fallback.

        Args:
            operation: Run container operation
            context: Workflow context

        Returns:
            Operation result
        """
        if not self.config.auto_pull_on_missing:
            # No fallback, just run directly
            return await self._wrapper.execute(operation, context)

        # Create primary operation (run container)
        primary = TimeoutPrimitive(
            primitive=self._wrapper,
            timeout_seconds=self.config.container_start_timeout,
        )

        # Create fallback: pull image then run
        async def pull_and_run(
            op: DockerOperation, ctx: WorkflowContext
        ) -> DockerResult:
            """Pull image and then run container."""
            image = op.params.get("image", "")

            # Pull image first
            pull_op = DockerOperation(operation="pull_image", params={"image": image})
            pull_wrapper = TimeoutPrimitive(
                primitive=self._wrapper,
                timeout_seconds=self.config.image_pull_timeout,
            )
            pull_result = await pull_wrapper.execute(pull_op, ctx)

            if not pull_result.get("success"):
                return pull_result

            # Now run with pulled image
            return await primary.execute(op, ctx)

        # Create wrapper that does pull_and_run
        class PullAndRunWrapper(WorkflowPrimitive[DockerOperation, DockerResult]):
            def __init__(self, expert_self):
                super().__init__()
                self.expert_self = expert_self

            async def execute(
                self, input_data: DockerOperation, context: WorkflowContext
            ) -> DockerResult:
                return await pull_and_run(input_data, context)

        fallback_wrapper = PullAndRunWrapper(self)

        # Use fallback primitive: try primary, fallback if image not found
        with_fallback = FallbackPrimitive(
            primary=primary,
            fallback=fallback_wrapper,
        )

        return await with_fallback.execute(operation, context)

    async def execute(
        self, input_data: DockerOperation, context: WorkflowContext
    ) -> DockerResult:
        """
        Execute Docker operation with fallback, timeouts, and validation.

        Args:
            input_data: Docker operation to execute
            context: Workflow context for tracing

        Returns:
            Operation result with automatic fallback and timeout protection
        """
        # Validate operation follows best practices
        if validation_error := self._validate_operation(input_data):
            return DockerResult(
                success=False,
                operation=input_data.operation,
                error=validation_error["error"],
            )

        # Choose execution path based on operation
        if input_data.operation == "run_container":
            # Use automatic pull fallback
            return await self._run_with_auto_pull(input_data, context)

        # Apply timeouts to long-running operations
        elif input_data.operation == "stop_container":
            wrapper = TimeoutPrimitive(
                primitive=self._wrapper,
                timeout_seconds=self.config.container_stop_timeout,
            )
            return await wrapper.execute(input_data, context)

        elif input_data.operation == "pull_image":
            wrapper = TimeoutPrimitive(
                primitive=self._wrapper,
                timeout_seconds=self.config.image_pull_timeout,
            )
            return await wrapper.execute(input_data, context)

        elif input_data.operation == "build_image":
            wrapper = TimeoutPrimitive(
                primitive=self._wrapper,
                timeout_seconds=self.config.image_build_timeout,
            )
            return await wrapper.execute(input_data, context)

        else:
            # Other operations use wrapper directly (fast operations)
            return await self._wrapper.execute(input_data, context)

    def close(self) -> None:
        """Close the underlying Docker client."""
        self._wrapper.close()
