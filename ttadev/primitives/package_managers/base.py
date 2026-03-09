"""Base class for package manager primitives.

Provides ``PackageManagerPrimitive[T, U]`` — a composable, instrumented
base for wrapping CLI package-manager commands (``uv``, ``pnpm``, …) as
workflow primitives with automatic OpenTelemetry tracing.

# See: [[TTA.dev/Primitives/PackageManagerPrimitive]]
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import abstractmethod
from typing import TypeVar

from pydantic import BaseModel, Field

from ..core.base import WorkflowContext, WorkflowPrimitive

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


# ---------------------------------------------------------------------------
# Shared output model
# ---------------------------------------------------------------------------


class PackageManagerOutput(BaseModel):
    """Base output model for all package manager operations."""

    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    command: str = Field(description="Full command that was executed")


# ---------------------------------------------------------------------------
# Base primitive
# ---------------------------------------------------------------------------


class PackageManagerPrimitive(WorkflowPrimitive[T, U]):
    """Base class for package-manager primitives.

    Subclasses only need to implement two methods:

    * ``_build_command`` — turn typed input into a list of CLI arguments.
    * ``_parse_output`` — turn raw stdout / stderr / return-code into a
      typed output model.

    The base class handles:
    * Running the subprocess via ``asyncio.create_subprocess_exec``
    * Capturing stdout / stderr
    * Measuring wall-clock execution time
    * Logging (structured, with correlation IDs)

    Example:
        ```python
        class MyPrimitive(PackageManagerPrimitive[MyInput, MyOutput]):
            def __init__(self) -> None:
                super().__init__(command_name="my-tool")

            def _build_command(self, input_data: MyInput) -> list[str]:
                return ["my-tool", "run"]

            def _parse_output(
                self, stdout, stderr, return_code, execution_time, command,
            ) -> MyOutput:
                return MyOutput(success=return_code == 0, ...)
        ```
    """

    def __init__(
        self,
        command_name: str,
        working_dir: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialise a package-manager primitive.

        Args:
            command_name: Name of the CLI binary (e.g. ``"uv"``, ``"pnpm"``).
            working_dir: Optional working directory for the subprocess.
            name: Human-readable name used in logs.  Defaults to the class name.
        """
        self._command_name = command_name
        self._working_dir = working_dir
        self._name = name or self.__class__.__name__

    # -- abstract interface --------------------------------------------------

    @abstractmethod
    def _build_command(self, input_data: T) -> list[str]:
        """Build the CLI argument list from typed input.

        Args:
            input_data: Pydantic model with the operation parameters.

        Returns:
            Complete argument list, **including** the binary name as the
            first element (e.g. ``["uv", "sync", "--all-extras"]``).
        """

    @abstractmethod
    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> U:
        """Parse subprocess output into a typed result model.

        Args:
            stdout: Captured standard output.
            stderr: Captured standard error.
            return_code: Process exit code.
            execution_time: Wall-clock seconds.
            command: The full command string for logging.

        Returns:
            Typed output model.
        """

    # -- concrete helpers ----------------------------------------------------

    async def _run_command(self, args: list[str]) -> tuple[str, str, int]:
        """Run *args* as a subprocess and return ``(stdout, stderr, rc)``.

        Args:
            args: Full argument list (binary + flags).

        Returns:
            Tuple of ``(stdout, stderr, return_code)``.
        """
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._working_dir,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (
            stdout_bytes.decode("utf-8", errors="replace"),
            stderr_bytes.decode("utf-8", errors="replace"),
            proc.returncode or 0,
        )

    # -- WorkflowPrimitive implementation ------------------------------------

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Execute the package-manager operation.

        Orchestrates ``_build_command → _run_command → _parse_output`` and
        records timing information on the *context*.

        Args:
            input_data: Typed operation parameters.
            context: Workflow context for tracing / correlation.

        Returns:
            Typed result model produced by ``_parse_output``.
        """
        context.checkpoint(f"{self._name}.start")
        start = time.time()

        args = self._build_command(input_data)
        command_str = " ".join(args)

        logger.info(
            "Running package-manager command",
            extra={
                "command": command_str,
                "primitive": self._name,
                "correlation_id": context.correlation_id,
            },
        )

        stdout, stderr, rc = await self._run_command(args)
        elapsed = time.time() - start

        context.checkpoint(f"{self._name}.end")

        if rc != 0:
            logger.warning(
                "Command exited with non-zero code",
                extra={
                    "command": command_str,
                    "return_code": rc,
                    "stderr": stderr[:500],
                    "correlation_id": context.correlation_id,
                },
            )

        return self._parse_output(stdout, stderr, rc, elapsed, command_str)
