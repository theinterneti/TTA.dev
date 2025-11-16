import os
import stat
from dataclasses import dataclass
from pathlib import Path

from tta_dev_primitives.core.base import WorkflowPrimitive
from tta_dev_primitives.core.context import WorkflowContext


@dataclass
class CreateHookInput:
    name: str
    content: str
    make_executable: bool = True


class CreateHookPrimitive(WorkflowPrimitive[CreateHookInput, str]):
    """
    A primitive that creates a new Cline hook script.
    """

    async def _execute(
        self,
        context: WorkflowContext,
        input_data: CreateHookInput,
    ) -> str:
        """
        Creates a new hook file, writes content to it, and optionally makes it executable.
        """
        hooks_dir = Path.home() / ".cline" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_path = hooks_dir / input_data.name

        with open(hook_path, "w") as f:
            f.write(input_data.content)

        if input_data.make_executable:
            # Make the file executable for the owner
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

        return str(hook_path)
