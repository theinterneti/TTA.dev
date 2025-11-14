"""E2B Code Execution Primitive.

Provides secure, sandboxed code execution using E2B cloud sandboxes.
Supports multiple languages, session persistence, and automatic cleanup.

Features:
- 150ms sandbox startup (vs 1-5s Docker)
- Isolated filesystem and network
- Process management and monitoring
- Automatic session rotation (before 1-hour limit)
- Built-in observability with metrics

Free Tier: 20 concurrent sandboxes, 8 vCPUs each, 1-hour sessions.

Example:
    ```python
    from tta_dev_primitives.integrations import CodeExecutionPrimitive
    from tta_dev_primitives import WorkflowContext

    executor = CodeExecutionPrimitive()

    code = '''
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)

    print(fibonacci(10))
    '''

    context = WorkflowContext(trace_id="exec-001")
    result = await executor.execute({"code": code, "language": "python"}, context)

    print(result["output"])  # "55"
    print(result["execution_time"])  # e.g., 0.023 seconds
    ```
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import TypedDict

from e2b_code_interpreter import AsyncSandbox

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

logger = logging.getLogger(__name__)


class CodeInput(TypedDict, total=False):
    """Input data for code execution."""

    code: str  # Required: Code to execute
    language: str  # Optional: Language (default: python)
    timeout: int  # Optional: Timeout in seconds (default: 30)
    env_vars: dict[str, str]  # Optional: Environment variables


class CodeOutput(TypedDict):
    """Output from code execution."""

    output: str  # Standard output
    error: str | None  # Error output if any
    execution_time: float  # Execution time in seconds
    success: bool  # Whether execution succeeded
    logs: list[str]  # Execution logs
    sandbox_id: str  # E2B sandbox ID used


class CodeExecutionPrimitive(InstrumentedPrimitive[CodeInput, CodeOutput]):
    """Execute code in secure E2B sandboxes.

    This primitive provides safe, isolated code execution using E2B cloud
    sandboxes. Each execution runs in a fresh Firecracker microVM with:
    - Full filesystem isolation
    - Network access control
    - Process monitoring
    - Resource limits (8 vCPU, 8GB RAM on free tier)

    The primitive automatically handles:
    - Sandbox creation and cleanup
    - Session rotation (before 1-hour limit)
    - Error handling and logging
    - Observability (traces, metrics, logs)

    Attributes:
        api_key: E2B API key (from E2B_API_KEY env var)
        default_timeout: Default execution timeout in seconds
        session_max_age: Max session age before rotation (default: 55 min)
        _sandbox: Current E2B sandbox instance
        _session_created_at: Timestamp of current session creation
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_timeout: int = 30,
        session_max_age: int = 3300,  # 55 minutes (before 1-hour limit)
        template_id: str | None = None,
    ) -> None:
        """Initialize code execution primitive.

        Args:
            api_key: E2B API key. If None, reads from E2B_API_KEY env var.
            default_timeout: Default timeout for code execution in seconds.
            session_max_age: Max session age in seconds before rotation.
            template_id: E2B template ID for custom environments (e.g., "tta-ml-minimal").
                        If None, uses default Python environment.

        Raises:
            ValueError: If api_key is not provided and E2B_API_KEY env var is not set.
        """
        super().__init__()
        self.api_key = api_key or os.getenv("E2B_API_KEY") or os.getenv("E2B_KEY")
        if not self.api_key:
            raise ValueError(
                "E2B API key is required. Provide via api_key parameter or E2B_API_KEY/E2B_KEY env var."
            )

        # Ensure E2B SDK can find the API key
        os.environ["E2B_API_KEY"] = self.api_key

        self.default_timeout = default_timeout
        self.session_max_age = session_max_age
        self.template_id = template_id
        self._sandbox: AsyncSandbox | None = None
        self._session_created_at: float = 0

    async def _execute_impl(self, input_data: CodeInput, context: WorkflowContext) -> CodeOutput:
        """Execute code in E2B sandbox.

        Args:
            input_data: Code execution parameters
            context: Workflow context for tracing

        Returns:
            Execution results including output, errors, and metrics

        Raises:
            ValueError: If code is missing or invalid
            TimeoutError: If execution exceeds timeout
            Exception: If sandbox creation or execution fails
        """
        # Validate input
        if "code" not in input_data:
            raise ValueError("Code is required in input_data")

        code = input_data["code"]
        timeout = input_data.get("timeout", self.default_timeout)
        env_vars = input_data.get("env_vars", {})

        # Note: language parameter reserved for future multi-language support
        # Currently E2B Code Interpreter defaults to Python

        # Check if we need to rotate session (before 1-hour limit)
        await self._maybe_rotate_session()

        # Ensure sandbox is ready
        if not self._sandbox:
            await self._create_sandbox()

        # Execute code
        logs: list[str] = []

        try:
            # Note: E2B SDK doesn't support custom env vars in run_code yet
            # Environment variables would need to be set via sandbox.run_code("export VAR=value")
            if env_vars and self._sandbox:
                logger.warning(
                    "Environment variables not directly supported, setting via export commands"
                )
                for key, value in env_vars.items():
                    await self._sandbox.run_code(f'import os; os.environ["{key}"] = "{value}"')

            # Execute code with timeout using E2B's run_code method
            start_time = time.time()
            execution = await asyncio.wait_for(
                self._run_code_with_retries(code, timeout=timeout),
                timeout=timeout + 10,
            )
            execution_time = time.time() - start_time

            # Collect results using correct E2B API
            output_logs = getattr(execution, "logs", None)
            if output_logs and hasattr(output_logs, "stdout") and output_logs.stdout:
                # stdout is a list of strings in E2B API
                if isinstance(output_logs.stdout, list):
                    output_text = "\n".join(output_logs.stdout)
                else:
                    output_text = str(output_logs.stdout)
            else:
                output_text = ""

            error_text = None

            # Check for errors in execution
            error_obj = getattr(execution, "error", None)
            if error_obj:
                error_text = str(error_obj)

            # Collect logs (stdout is already the main output)
            execution_logs = getattr(execution, "logs", None)
            if execution_logs:
                if hasattr(execution_logs, "stdout") and execution_logs.stdout:
                    # stdout is a list of strings in E2B API
                    if isinstance(execution_logs.stdout, list):
                        for line in execution_logs.stdout:
                            logs.append(f"[stdout] {line.strip()}")
                    else:
                        logs.append(f"[stdout] {execution_logs.stdout.strip()}")
                if hasattr(execution_logs, "stderr") and execution_logs.stderr:
                    # stderr is a list of strings in E2B API
                    if isinstance(execution_logs.stderr, list):
                        for line in execution_logs.stderr:
                            logs.append(f"[stderr] {line.strip()}")
                    else:
                        logs.append(f"[stderr] {execution_logs.stderr.strip()}")

            success = error_text is None
            sandbox_id = self._sandbox.sandbox_id if self._sandbox else "unknown"

            return CodeOutput(
                output=output_text,
                error=error_text,
                execution_time=execution_time,
                success=success,
                logs=logs,
                sandbox_id=sandbox_id,
            )

        except TimeoutError:
            execution_time = time.time() - start_time
            raise TimeoutError(f"Code execution timed out after {timeout} seconds") from None

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Code execution failed: {e}",
                extra={
                    "trace_id": context.trace_id,
                    "execution_time": execution_time,
                    "error": str(e),
                },
            )
            raise

    async def _create_sandbox(self) -> None:
        """Create new E2B sandbox.

        Note: API key is set via E2B_API_KEY environment variable.
        The create() method doesn't accept api_key parameter directly.
        """
        if self.template_id:
            logger.info(f"Creating E2B sandbox with template: {self.template_id}")
            # E2B SDK reads API key from environment automatically
            self._sandbox = await AsyncSandbox.create(
                template=self.template_id, timeout=self.session_max_age
            )
        else:
            logger.info("Creating new E2B sandbox with default environment")
            # E2B SDK reads API key from environment automatically
            self._sandbox = await AsyncSandbox.create(timeout=self.session_max_age)

        self._session_created_at = time.time()
        logger.info(
            f"Sandbox created: {self._sandbox.sandbox_id}",
            extra={
                "sandbox_id": self._sandbox.sandbox_id,
                "template_id": self.template_id,
            },
        )

    async def _run_code_with_retries(self, code: str, timeout: int) -> object:
        """Run code in the sandbox with short retries to tolerate startup races.

        The E2B sandbox can claim to be "running" while the internal code
        interpreter service is still starting and not yet accepting connections.
        This helper retries a number of times on the common 'port not open'
        / connection errors before giving up.

        Returns the execution result on success or raises the last exception.
        """
        # For custom templates (especially ML), allow more time for initialization
        base_wait = 120 if self.template_id else 60
        max_total_wait = min(base_wait, max(20, timeout))  # don't wait forever
        attempt = 0
        start = time.time()
        last_exc: Exception | None = None

        while time.time() - start < max_total_wait:
            attempt += 1
            try:
                if not self._sandbox:
                    raise RuntimeError("Sandbox not initialized")
                return await self._sandbox.run_code(code)

            except Exception as e:
                last_exc = e
                msg = str(e).lower()

                # Common transient conditions: port not open, 502 from gateway
                if (
                    "port is not open" in msg
                    or "502" in msg
                    or "connection refused" in msg
                    or "connection" in msg
                    and "refused" in msg
                ):
                    wait = min(0.5 * (2 ** (attempt - 1)), 5.0)
                    logger.info(
                        f"Sandbox interpreter not ready (attempt={attempt}), waiting {wait:.1f}s",
                        extra={"sandbox_id": getattr(self._sandbox, "sandbox_id", None)},
                    )
                    await asyncio.sleep(wait)
                    continue

                # Non-transient error — re-raise
                raise

        # Timed out
        logger.error(
            "Sandbox interpreter did not become ready in time",
            extra={
                "sandbox_id": getattr(self._sandbox, "sandbox_id", None),
                "last_error": str(last_exc),
            },
        )
        if last_exc:
            raise last_exc
        raise RuntimeError("Sandbox interpreter not ready")

    async def _maybe_rotate_session(self) -> None:
        """Rotate session if approaching 1-hour limit.

        E2B free tier has 1-hour session limit. We rotate at 55 minutes
        to avoid mid-execution termination.
        """
        if not self._sandbox:
            return

        session_age = time.time() - self._session_created_at

        if session_age >= self.session_max_age:
            logger.info(
                f"Rotating sandbox session (age: {session_age:.0f}s)",
                extra={"sandbox_id": self._sandbox.sandbox_id},
            )
            await self.cleanup()
            await self._create_sandbox()

    async def cleanup(self) -> None:
        """Close and cleanup E2B sandbox.

        Should be called when done with execution to free resources.
        Automatically called by context manager or on session rotation.
        """
        if self._sandbox:
            try:
                await self._sandbox.kill()
                logger.info("Sandbox killed successfully")
            except Exception as e:
                logger.warning(f"Error killing sandbox: {e}")
            finally:
                self._sandbox = None
                self._session_created_at = 0

    async def __aenter__(self) -> CodeExecutionPrimitive:
        """Async context manager entry."""
        await self._create_sandbox()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()


# Convenience alias
E2BPrimitive = CodeExecutionPrimitive

__all__ = ["CodeExecutionPrimitive", "E2BPrimitive", "CodeInput", "CodeOutput"]
