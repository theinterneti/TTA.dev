"""
UV Package Manager Integration Primitive for TTA.dev

Provides composable workflows for managing uv operations across git worktrees,
with full observability and recovery patterns.

Example:
    # Execute uv commands in composable workflows
    uv_workflow = (
        UVSyncPrimitive(uv_command="sync", with_extras=True) >>
        UVRunPrimitive(command="pytest -v") >>
        UVPrimitive(uv_command="add", package="new-package")
    )

    result = await uv_workflow.execute(context, worktree_context)
"""

import asyncio
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from structlog import get_logger

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..recovery import RetryPrimitive, TimeoutPrimitive

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


class UVCommand(Enum):
    """Supported uv commands"""

    SYNC = "sync"
    ADD = "add"
    REMOVE = "remove"
    RUN = "run"
    LOCK = "lock"
    TREE = "tree"
    PIP = "pip"


@dataclass
class UVResult:
    """Result of a uv operation"""

    success: bool
    command: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time: float = 0.0
    worktree: str | None = None


class UVPrimitive(WorkflowPrimitive[dict[str, Any], UVResult]):
    """
    Core uv primitive for executing uv commands

    Supports all major uv operations with full observability and error handling.

    Args:
        uv_command: The uv command to execute (sync, add, remove, run, etc.)
        package: Package name for add/remove operations
        command: Command to run with 'uv run'
        with_extras: Include extras when syncing
        worktree_path: Override worktree path (defaults to context)
        timeout: Command timeout in seconds
    """

    def __init__(
        self,
        uv_command: UVCommand | str,
        package: str | None = None,
        command: str | None = None,
        with_extras: bool = False,
        worktree_path: Path | None = None,
        timeout: float = 300.0,  # 5 minutes default
    ):
        super().__init__()
        self.uv_command = (
            UVCommand(uv_command) if isinstance(uv_command, str) else uv_command
        )
        self.package = package
        self.command = command
        self.with_extras = with_extras
        self.worktree_path_override = worktree_path
        self.timeout = timeout

    async def execute(
        self, context: WorkflowContext, input_data: dict[str, Any]
    ) -> UVResult:
        """Execute the uv command"""
        with tracer.start_as_span(f"uv.{self.uv_command.value}") as span:
            start_time = asyncio.get_event_loop().time()

            try:
                # Build uv command
                cmd = self._build_command(input_data)

                # Determine worktree path
                worktree_path = self._get_worktree_path(context, input_data)

                span.set_attribute("uv.command", self.uv_command.value)
                span.set_attribute("uv.worktree", str(worktree_path))
                span.set_attribute("uv.timeout", self.timeout)

                logger.info(
                    "Executing uv command",
                    command=self.uv_command.value,
                    worktree=str(worktree_path),
                    full_command=cmd,
                )

                # Execute command with timeout
                result = await self._execute_command(cmd, worktree_path)

                execution_time = asyncio.get_event_loop().time() - start_time

                uv_result = UVResult(
                    success=result.returncode == 0,
                    command=self.uv_command.value,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode,
                    execution_time=execution_time,
                    worktree=str(worktree_path),
                )

                # Set span status
                if uv_result.success:
                    span.set_status(Status(StatusCode.OK))
                else:
                    span.set_status(Status(StatusCode.ERROR, uv_result.stderr))
                    span.record_exception(
                        ValueError(f"UV command failed: {uv_result.stderr}")
                    )

                span.set_attribute("uv.success", uv_result.success)
                span.set_attribute("uv.execution_time", execution_time)
                span.set_attribute("uv.return_code", uv_result.return_code)

                logger.info(
                    "UV command completed",
                    success=uv_result.success,
                    execution_time=execution_time,
                    return_code=uv_result.return_code,
                )

                return uv_result

            except TimeoutError:
                span.set_status(Status(StatusCode.ERROR, "Timeout"))
                span.record_exception(
                    TimeoutError(f"UV command timed out after {self.timeout}s")
                )
                raise
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def _build_command(self, input_data: dict[str, Any]) -> list[str]:
        """Build the uv command line"""
        cmd = ["uv"]

        if self.uv_command == UVCommand.SYNC:
            cmd.append("sync")
            if self.with_extras:
                cmd.append("--all-extras")

        elif self.uv_command == UVCommand.ADD:
            if not self.package:
                self.package = input_data.get("package")
            if not self.package:
                raise ValueError("Package name required for uv add")
            cmd.extend(["add", self.package])

        elif self.uv_command == UVCommand.REMOVE:
            if not self.package:
                self.package = input_data.get("package")
            if not self.package:
                raise ValueError("Package name required for uv remove")
            cmd.extend(["remove", self.package])

        elif self.uv_command == UVCommand.RUN:
            if not self.command:
                self.command = input_data.get("command")
            if not self.command:
                raise ValueError("Command required for uv run")
            cmd.extend(["run"] + self.command.split())

        elif self.uv_command == UVCommand.LOCK:
            cmd.append("lock")

        elif self.uv_command == UVCommand.TREE:
            cmd.append("tree")

        elif self.uv_command == UVCommand.PIP:
            # Pass through pip commands
            pip_args = input_data.get("pip_args", [])
            cmd.extend(["pip"] + pip_args)

        else:
            raise ValueError(f"Unsupported uv command: {self.uv_command}")

        return cmd

    def _get_worktree_path(
        self, context: WorkflowContext, input_data: dict[str, Any]
    ) -> Path:
        """Determine the worktree path to use"""
        # Override takes precedence
        if self.worktree_path_override:
            return self.worktree_path_override

        # Check input data
        worktree_path = input_data.get("worktree_path")
        if worktree_path:
            return Path(worktree_path)

        # Check context data
        worktree_path = context.data.get("worktree_path")
        if worktree_path:
            return Path(worktree_path)

        # Default to current directory
        return Path.cwd()

    async def _execute_command(
        self, cmd: list[str], worktree_path: Path
    ) -> subprocess.CompletedProcess:
        """Execute the uv command"""
        try:
            return await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=worktree_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    text=True,
                ).communicate(),
                timeout=self.timeout,
            )
        except TimeoutError:
            # Kill the process if it times out
            process = await asyncio.create_subprocess_exec(*cmd, cwd=worktree_path)
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except TimeoutError:
                process.kill()
            raise


class WorktreeAwareUVPrimitive(WorkflowPrimitive[dict[str, Any], UVResult]):
    """
    UV primitive that automatically detects and manages worktree-specific operations

    This primitive reads uv.toml configuration and adapts commands based on the
    current worktree's branch and configured packages.
    """

    def __init__(self, uv_command: UVCommand | str, **uv_kwargs):
        self.uv_primitive = UVPrimitive(uv_command, **uv_kwargs)
        self.repo_root = self._find_repo_root()

    def _find_repo_root(self) -> Path:
        """Find the git repository root"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists():
                return parent
        return Path.cwd()  # Fallback

    async def execute(
        self, context: WorkflowContext, input_data: dict[str, Any]
    ) -> UVResult:
        """Execute uv command with worktree awareness"""
        with tracer.start_as_span("worktree-aware-uv") as span:
            # Detect current worktree info
            worktree_info = await self._get_worktree_info()

            # Adapt command based on worktree configuration
            adapted_input = self._adapt_for_worktree(input_data, worktree_info)

            span.set_attribute(
                "worktree.branch", worktree_info.get("branch", "unknown")
            )
            span.set_attribute(
                "worktree.path", str(worktree_info.get("path", "unknown"))
            )

            # Execute with adapted input
            return await self.uv_primitive.execute(context, adapted_input)

    async def _get_worktree_info(self) -> dict[str, Any]:
        """Get information about the current worktree"""
        try:
            # Get current branch
            result = await asyncio.create_subprocess_exec(
                "git",
                "branch",
                "--show-current",
                cwd=self.repo_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True,
            )
            stdout, _ = await result.communicate()
            current_branch = stdout.strip() if result.returncode == 0 else "detached"

            return {
                "branch": current_branch,
                "path": Path.cwd(),
                "repo_root": self.repo_root,
            }
        except Exception:
            return {
                "branch": "unknown",
                "path": Path.cwd(),
                "repo_root": self.repo_root,
            }

    def _adapt_for_worktree(
        self, input_data: dict[str, Any], worktree_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Adapt input data for worktree-specific execution"""
        adapted = input_data.copy()

        # Add worktree path if not specified
        if "worktree_path" not in adapted:
            adapted["worktree_path"] = worktree_info["path"]

        # Add worktree context for logging/observability
        adapted["worktree_context"] = worktree_info

        return adapted


# Convenience primitives for common operations
class UVSyncPrimitive(UVPrimitive):
    """Primitive for uv sync operations"""

    def __init__(self, with_extras: bool = True, **kwargs):
        super().__init__(UVCommand.SYNC, with_extras=with_extras, **kwargs)


class UVAddPrimitive(UVPrimitive):
    """Primitive for uv add operations"""

    def __init__(self, package: str, **kwargs):
        super().__init__(UVCommand.ADD, package=package, **kwargs)


class UVRemovePrimitive(UVPrimitive):
    """Primitive for uv remove operations"""

    def __init__(self, package: str, **kwargs):
        super().__init__(UVCommand.REMOVE, package=package, **kwargs)


class UVRunPrimitive(UVPrimitive):
    """Primitive for uv run operations"""

    def __init__(self, command: str, **kwargs):
        super().__init__(UVCommand.RUN, command=command, **kwargs)


# Composable workflow patterns
def create_worktree_sync_workflow(
    with_extras: bool = True, timeout: float = 300.0
) -> WorkflowPrimitive:
    """
    Create a workflow that syncs dependencies with worktree awareness
    and includes retry/error handling
    """
    sync = WorktreeAwareUVPrimitive(
        UVCommand.SYNC, with_extras=with_extras, timeout=timeout
    )

    # Wrap with retry and timeout
    return RetryPrimitive(
        primitive=TimeoutPrimitive(primitive=sync, timeout_seconds=timeout),
        max_retries=2,
        backoff_strategy="exponential",
    )


def create_dependency_management_workflow(
    packages_to_add: list[str] | None = None,
    packages_to_remove: list[str] | None = None,
    sync_after: bool = True,
) -> WorkflowPrimitive:
    """
    Create a workflow for managing dependencies with proper sequencing

    Args:
        packages_to_add: List of packages to add
        packages_to_remove: List of packages to remove
        sync_after: Whether to sync dependencies after changes
    """
    primitives = []

    # Add packages
    if packages_to_add:
        for package in packages_to_add:
            primitives.append(UVAddPrimitive(package=package))

    # Remove packages
    if packages_to_remove:
        for package in packages_to_remove:
            primitives.append(UVRemovePrimitive(package=package))

    # Sync if requested
    if sync_after:
        primitives.append(UVSyncPrimitive(with_extras=True))

    # Compose the workflow
    if len(primitives) == 1:
        return primitives[0]

    # Use SequentialPrimitive for multiple operations
    from ..core.primitives import SequentialPrimitive

    return SequentialPrimitive(primitives=primitives)
