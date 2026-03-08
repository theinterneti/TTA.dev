"""JavaScript (pnpm) package-manager primitives.

Wraps common ``pnpm`` CLI operations as composable workflow primitives:

* `PnpmInstallPrimitive` — ``pnpm install``
* `PnpmAddPrimitive` — ``pnpm add``
* `PnpmRemovePrimitive` — ``pnpm remove``
* `PnpmRunPrimitive` — ``pnpm run``
* `PnpmUpdatePrimitive` — ``pnpm update``

# See: [[TTA.dev/Primitives/PackageManagers/Pnpm]]
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..core.base import WorkflowContext
from .base import PackageManagerOutput, PackageManagerPrimitive

# ---------------------------------------------------------------------------
# Input / output models
# ---------------------------------------------------------------------------


class PnpmInstallInput(BaseModel):
    """Input for ``pnpm install``."""

    frozen_lockfile: bool = False
    prefer_offline: bool = False


class PnpmInstallOutput(PackageManagerOutput):
    """Output for ``pnpm install``."""


class PnpmAddInput(BaseModel):
    """Input for ``pnpm add``."""

    packages: list[str]
    dev: bool = False
    save_exact: bool = False


class PnpmAddOutput(PackageManagerOutput):
    """Output for ``pnpm add``."""

    packages_added: list[str] = Field(default_factory=list)


class PnpmRemoveInput(BaseModel):
    """Input for ``pnpm remove``."""

    packages: list[str]


class PnpmRemoveOutput(PackageManagerOutput):
    """Output for ``pnpm remove``."""


class PnpmRunInput(BaseModel):
    """Input for ``pnpm run``."""

    script: str
    args: list[str] = Field(default_factory=list)


class PnpmRunOutput(PackageManagerOutput):
    """Output for ``pnpm run``."""


class PnpmUpdateInput(BaseModel):
    """Input for ``pnpm update``."""

    packages: list[str] = Field(default_factory=list)
    latest: bool = False


class PnpmUpdateOutput(PackageManagerOutput):
    """Output for ``pnpm update``."""


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


class PnpmInstallPrimitive(
    PackageManagerPrimitive[PnpmInstallInput, PnpmInstallOutput],
):
    """Run ``pnpm install`` with optional flags.

    Example:
        ```python
        prim = PnpmInstallPrimitive()
        result = await prim.execute(
            PnpmInstallInput(frozen_lockfile=True),
            WorkflowContext(workflow_id="ci"),
        )
        assert result.success
        ```
    """

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="pnpm", working_dir=working_dir)

    def _build_command(self, input_data: PnpmInstallInput) -> list[str]:
        cmd: list[str] = ["pnpm", "install"]
        if input_data.frozen_lockfile:
            cmd.append("--frozen-lockfile")
        if input_data.prefer_offline:
            cmd.append("--prefer-offline")
        return cmd

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> PnpmInstallOutput:
        return PnpmInstallOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )


class PnpmAddPrimitive(
    PackageManagerPrimitive[PnpmAddInput, PnpmAddOutput],
):
    """Run ``pnpm add <packages>``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="pnpm", working_dir=working_dir)
        self._last_packages: list[str] = []

    def _build_command(self, input_data: PnpmAddInput) -> list[str]:
        cmd: list[str] = ["pnpm", "add"]
        if input_data.dev:
            cmd.append("--save-dev")
        if input_data.save_exact:
            cmd.append("--save-exact")
        cmd.extend(input_data.packages)
        return cmd

    async def execute(self, input_data: PnpmAddInput, context: WorkflowContext) -> PnpmAddOutput:
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
    ) -> PnpmAddOutput:
        return PnpmAddOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
            packages_added=(self._last_packages if return_code == 0 else []),
        )


class PnpmRemovePrimitive(
    PackageManagerPrimitive[PnpmRemoveInput, PnpmRemoveOutput],
):
    """Run ``pnpm remove <packages>``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="pnpm", working_dir=working_dir)

    def _build_command(self, input_data: PnpmRemoveInput) -> list[str]:
        return ["pnpm", "remove", *input_data.packages]

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> PnpmRemoveOutput:
        return PnpmRemoveOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )


class PnpmRunPrimitive(
    PackageManagerPrimitive[PnpmRunInput, PnpmRunOutput],
):
    """Run ``pnpm run <script> [args...]``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="pnpm", working_dir=working_dir)

    def _build_command(self, input_data: PnpmRunInput) -> list[str]:
        return ["pnpm", "run", input_data.script, *input_data.args]

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> PnpmRunOutput:
        return PnpmRunOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )


class PnpmUpdatePrimitive(
    PackageManagerPrimitive[PnpmUpdateInput, PnpmUpdateOutput],
):
    """Run ``pnpm update [packages...]``."""

    def __init__(self, working_dir: str | None = None) -> None:
        super().__init__(command_name="pnpm", working_dir=working_dir)

    def _build_command(self, input_data: PnpmUpdateInput) -> list[str]:
        cmd: list[str] = ["pnpm", "update"]
        if input_data.latest:
            cmd.append("--latest")
        cmd.extend(input_data.packages)
        return cmd

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        command: str,
    ) -> PnpmUpdateOutput:
        return PnpmUpdateOutput(
            success=return_code == 0,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            command=command,
        )
