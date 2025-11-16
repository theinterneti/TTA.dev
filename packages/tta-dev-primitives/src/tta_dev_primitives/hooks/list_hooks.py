import os
from dataclasses import dataclass
from pathlib import Path

from tta_dev_primitives.core.base import WorkflowPrimitive
from tta_dev_primitives.core.context import WorkflowContext


@dataclass
class HookInfo:
    name: str
    path: str
    permissions: str


class ListHooksPrimitive(WorkflowPrimitive[None, list[HookInfo]]):
    """
    A primitive that lists all executable hooks in the specified Cline hooks directory.
    """

    async def _execute(
        self,
        context: WorkflowContext,
        input_data: None = None,
    ) -> list[HookInfo]:
        """
        Scans the .cline/hooks directory and returns a list of hooks.
        """
        hooks_dir = Path.home() / ".cline" / "hooks"
        if not hooks_dir.is_dir():
            return []

        hooks = []
        for item in hooks_dir.iterdir():
            if item.is_file() and os.access(item, os.X_OK):
                permissions = oct(item.stat().st_mode)[-3:]
                hooks.append(
                    HookInfo(name=item.name, path=str(item), permissions=permissions)
                )

        return hooks
