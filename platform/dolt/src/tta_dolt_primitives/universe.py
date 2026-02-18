"""DoltUniversePrimitive — branch management for parallel universes."""

from __future__ import annotations

from dataclasses import dataclass

from tta_dev_primitives.core.base import WorkflowContext

from .core.base import DoltPrimitive
from .core.models import BranchInfo, BranchOperation, DoltConfig


@dataclass
class UniverseInput:
    """Input for a universe (branch) operation.

    Args:
        operation: The branch operation to perform.
        name: Branch name for create/checkout/delete operations.
        from_branch: Source branch for create operations (defaults to current branch).
    """

    operation: BranchOperation
    name: str = ""
    from_branch: str = ""


@dataclass
class UniverseOutput:
    """Output of a universe (branch) operation."""

    success: bool
    current_branch: str
    branches: list[BranchInfo]
    message: str = ""


class DoltUniversePrimitive(DoltPrimitive[UniverseInput, UniverseOutput]):
    """Manage parallel universe branches in a Dolt repository.

    A universe is a Dolt branch. This primitive handles the full lifecycle:
    creating new universes (branching from any commit), switching between them,
    listing all that exist, and deleting those that are no longer needed.

    Example:
        ```python
        config = DoltConfig(repo_path="/path/to/game-db")
        universe = DoltUniversePrimitive(config)

        # Fork a new private universe from the current state
        result = await universe.execute(
            UniverseInput(
                operation=BranchOperation.CREATE_AND_CHECKOUT,
                name="player-42/brave-choice",
            ),
            context,
        )
        ```
    """

    def __init__(self, config: DoltConfig) -> None:
        super().__init__(config)

    async def execute(self, input_data: UniverseInput, context: WorkflowContext) -> UniverseOutput:
        """Execute a branch operation.

        Args:
            input_data: The operation to perform and target branch name.
            context: Workflow context for logging and tracing.

        Returns:
            UniverseOutput with current branch and full branch list.

        Raises:
            ValueError: If a required branch name is missing.
            RuntimeError: If the Dolt command fails.
        """
        op = input_data.operation

        if op == BranchOperation.LIST:
            return await self._list()

        if op == BranchOperation.CURRENT:
            return await self._current()

        if not input_data.name:
            raise ValueError(f"Branch name required for operation '{op}'")

        if op == BranchOperation.CREATE:
            return await self._create(input_data.name, input_data.from_branch)

        if op == BranchOperation.CHECKOUT:
            return await self._checkout(input_data.name)

        if op == BranchOperation.CREATE_AND_CHECKOUT:
            result = await self._create(input_data.name, input_data.from_branch)
            if not result.success:
                return result
            return await self._checkout(input_data.name)

        if op == BranchOperation.DELETE:
            return await self._delete(input_data.name)

        raise ValueError(f"Unknown operation: {op}")

    async def _list(self) -> UniverseOutput:
        stdout, _, rc = await self._run_dolt("branch", "-a")
        branches = []
        current = ""
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            is_current = line.startswith("* ")
            name = line.lstrip("* ").strip()
            if is_current:
                current = name
            branches.append(BranchInfo(name=name, is_current=is_current))
        return UniverseOutput(success=(rc == 0), current_branch=current, branches=branches)

    async def _current(self) -> UniverseOutput:
        stdout, _, rc = await self._run_dolt("branch", "--show-current")
        current = stdout.strip()
        return UniverseOutput(
            success=(rc == 0),
            current_branch=current,
            branches=[BranchInfo(name=current, is_current=True)],
        )

    async def _create(self, name: str, from_branch: str) -> UniverseOutput:
        args = ["branch", name]
        if from_branch:
            args.append(from_branch)
        stdout, stderr, rc = await self._run_dolt(*args)
        result = await self._list()
        result.success = rc == 0
        result.message = stderr if rc != 0 else f"Universe '{name}' created"
        return result

    async def _checkout(self, name: str) -> UniverseOutput:
        _, stderr, rc = await self._run_dolt("checkout", name)
        result = await self._list()
        result.success = rc == 0
        result.message = stderr if rc != 0 else f"Switched to universe '{name}'"
        return result

    async def _delete(self, name: str) -> UniverseOutput:
        _, stderr, rc = await self._run_dolt("branch", "-d", name)
        result = await self._list()
        result.success = rc == 0
        result.message = stderr if rc != 0 else f"Universe '{name}' deleted"
        return result
