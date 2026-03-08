"""Python (uv) package-manager primitives.

Wraps common ``uv`` CLI operations as composable workflow primitives:

* `UvSyncPrimitive` — ``uv sync``
* `UvAddPrimitive` — ``uv add``
* `UvRemovePrimitive` — ``uv remove``
* `UvRunPrimitive` — ``uv run``
* `UvLockPrimitive` — ``uv lock``
* `UvTreePrimitive` — ``uv tree``

# See: [[TTA.dev/Primitives/PackageManagers/Uv]]
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..core.base import WorkflowContext
from .base import PackageManagerOutput, PackageManagerPrimitive

# ---------------------------------------------------------------------------
# Input / output models
# ---------------------------------------------------------------------------


class UvSyncInput(BaseModel):
    """Input for ``uv sync``."""

    all_extras: bool = False
    frozen: bool = False
    no_dev: bool = False


class UvSyncOutput(PackageManagerOutput):
    """Output for ``uv sync``."""


class UvAddInput(BaseModel):
    """Input for ``uv add``."""

    packages: list[str]
    dev: bool = False
    group: str | None = None


class UvAddOutput(PackageManagerOutput):
    """Output for ``uv add``."""

    packages_added: list[str] = Field(default_factory=list)


class UvRemoveInput(BaseModel):
    """Input for ``uv remove``."""

    packages: list[str]


class UvRemoveOutput(PackageManagerOutput):
    """Output for ``uv remove``."""

    packages_removed: list[str] = Field(default_factory=list)


class UvRunInput(BaseModel):
    """Input for ``uv run``."""

    command: str
    args: list[str] = Field(default_factory=list)


class UvRunOutput(PackageManagerOutput):
    """Output for ``uv run``."""


class UvLockInput(BaseModel):
    """Input for ``uv lock``."""

    upgrade: bool = False


class UvLockOutput(PackageManagerOutput):
    """Output for ``uv lock``."""


class UvTreeInput(BaseModel):
    """Input for ``uv tree``."""

    package: str | None = None
    depth: int | None = None


class UvTreeOutput(PackageManagerOutput):
    """Output for ``uv tree``."""


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


class UvSyncPrimitive(PackageManagerPrimitive[UvSyncInput, UvSyncOutput]):
    """Run ``uv sync`` with optional flags.

    Example:
        ```python
        prim = UvSyncPrimitive()
        result = await prim.execute(
            UvSyncInput(all_extras=True),
            WorkflowContext(workflow_id="setup"),
        )
        assert result.success
        ```
    """

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="uv", working_dir=working_dir)

    def _build_command(self, input_data: UvSyncInput) -> list[str]:
        cmd: list[str] = ["uv", "sync"]
        if input_data.all_extras:
            cmd.append("--all-extras")
        if input_data.frozen:
            cmd.append("--frozen")
        if input_data.no_dev:
            cmd.append("--no-dev")
        return cmd

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> UvSyncOutput:
        return UvSyncOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )


class UvAddPrimitive(PackageManagerPrimitive[UvAddInput, UvAddOutput]):
    """Run ``uv add <packages>``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="uv", working_dir=working_dir)
        self._last_packages: list[str] = []

    def _build_command(self, input_data: UvAddInput) -> list[str]:
        cmd: list[str] = ["uv", "add"]
        if input_data.dev:
            cmd.append("--dev")
        if input_data.group:
            cmd.extend(["--group", input_data.group])
        cmd.extend(input_data.packages)
        return cmd

    async def execute(self, input_data: UvAddInput, context: WorkflowContext) -> UvAddOutput:
        """Override to capture input packages for output."""
        self._last_packages = list(input_data.packages)
        return await super().execute(input_data, context)

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> UvAddOutput:
        return UvAddOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
            packages_added=self._last_packages if return_code == 0 else [],
        )


class UvRemovePrimitive(PackageManagerPrimitive[UvRemoveInput, UvRemoveOutput]):
    """Run ``uv remove <packages>``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="uv", working_dir=working_dir)
        self._last_packages: list[str] = []

    def _build_command(self, input_data: UvRemoveInput) -> list[str]:
        return ["uv", "remove", *input_data.packages]

    async def execute(self, input_data: UvRemoveInput, context: WorkflowContext) -> UvRemoveOutput:
        """Override to capture input packages for output."""
        self._last_packages = list(input_data.packages)
        return await super().execute(input_data, context)

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> UvRemoveOutput:
        return UvRemoveOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
            packages_removed=(self._last_packages if return_code == 0 else []),
        )


class UvRunPrimitive(PackageManagerPrimitive[UvRunInput, UvRunOutput]):
    """Run ``uv run <command> [args...]``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="uv", working_dir=working_dir)

    def _build_command(self, input_data: UvRunInput) -> list[str]:
        return ["uv", "run", input_data.command, *input_data.args]

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> UvRunOutput:
        return UvRunOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )


class UvLockPrimitive(PackageManagerPrimitive[UvLockInput, UvLockOutput]):
    """Run ``uv lock``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="uv", working_dir=working_dir)

    def _build_command(self, input_data: UvLockInput) -> list[str]:
        cmd: list[str] = ["uv", "lock"]
        if input_data.upgrade:
            cmd.append("--upgrade")
        return cmd

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> UvLockOutput:
        return UvLockOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )


class UvTreePrimitive(PackageManagerPrimitive[UvTreeInput, UvTreeOutput]):
    """Run ``uv tree``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="uv", working_dir=working_dir)

    def _build_command(self, input_data: UvTreeInput) -> list[str]:
        cmd: list[str] = ["uv", "tree"]
        if input_data.package:
            cmd.extend(["--package", input_data.package])
        if input_data.depth is not None:
            cmd.extend(["--depth", str(input_data.depth)])
        return cmd

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> UvTreeOutput:
        return UvTreeOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )
