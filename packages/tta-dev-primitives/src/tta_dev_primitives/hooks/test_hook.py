import asyncio
from dataclasses import dataclass, field

from tta_dev_primitives.core.base import WorkflowPrimitive
from tta_dev_primitives.core.context import WorkflowContext


@dataclass
class TestHookInput:
    hook_path: str
    env: dict[str, str] = field(default_factory=dict)
    timeout: int = 5  # seconds


@dataclass
class TestResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class TestHookPrimitive(WorkflowPrimitive[TestHookInput, TestResult]):
    """
    A primitive that tests a Cline hook script in a controlled environment.
    """

    async def _execute(
        self,
        context: WorkflowContext,
        input_data: TestHookInput,
    ) -> TestResult:
        """
        Executes the hook script in a subprocess with a specified environment and captures the output.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                input_data.hook_path,
                env=input_data.env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=input_data.timeout
            )

            return TestResult(
                exit_code=process.returncode,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return TestResult(
                exit_code=-1,
                stdout="",
                stderr=f"Hook execution timed out after {input_data.timeout} seconds.",
                timed_out=True,
            )
