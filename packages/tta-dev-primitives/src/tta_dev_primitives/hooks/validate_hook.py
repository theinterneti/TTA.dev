import asyncio
import json
from dataclasses import dataclass, field
from shutil import which

from tta_dev_primitives.core.base import WorkflowPrimitive
from tta_dev_primitives.core.context import WorkflowContext


@dataclass
class ShellCheckIssue:
    file: str
    line: int
    endLine: int
    column: int
    endColumn: int
    level: str
    code: int
    message: str
    fix: dict | None = None


@dataclass
class ValidateHookInput:
    hook_path: str


@dataclass
class ValidationResult:
    success: bool
    issues: list[ShellCheckIssue] = field(default_factory=list)
    error_message: str | None = None


class ValidateHookPrimitive(WorkflowPrimitive[ValidateHookInput, ValidationResult]):
    """
    A primitive that validates a Cline hook script using shellcheck.
    """

    async def _execute(
        self,
        context: WorkflowContext,
        input_data: ValidateHookInput,
    ) -> ValidationResult:
        """
        Runs shellcheck on the provided hook script and returns the results.
        """
        if not which("shellcheck"):
            return ValidationResult(
                success=False,
                error_message="shellcheck is not installed or not in PATH.",
            )

        process = await asyncio.create_subprocess_exec(
            "shellcheck",
            "-f",
            "json",
            input_data.hook_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return ValidationResult(success=True)

        if process.returncode == 1:  # Issues found
            try:
                issues_data = json.loads(stdout)
                issues = [ShellCheckIssue(**issue) for issue in issues_data]
                return ValidationResult(success=False, issues=issues)
            except json.JSONDecodeError:
                return ValidationResult(
                    success=False,
                    error_message=f"Failed to parse shellcheck JSON output: {stdout.decode()}",
                )

        return ValidationResult(
            success=False,
            error_message=f"shellcheck exited with code {process.returncode}: {stderr.decode()}",
        )
