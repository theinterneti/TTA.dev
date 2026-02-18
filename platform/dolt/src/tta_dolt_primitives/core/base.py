"""Base class for Dolt primitives."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

from .models import DoltConfig

logger = structlog.get_logger(__name__)


class DoltPrimitive[T, U](WorkflowPrimitive[T, U]):
    """Base class for all Dolt primitives.

    Provides shared helpers for running Dolt CLI commands and logging.
    All Dolt primitives extend this class.
    """

    def __init__(self, config: DoltConfig) -> None:
        self.config = config
        self._log = logger.bind(
            primitive=self.__class__.__name__,
            repo=config.repo_path,
        )

    async def _run_dolt(self, *args: str) -> tuple[str, str, int]:
        """Run a Dolt CLI command in the repo directory.

        Args:
            *args: Dolt command arguments (e.g., "branch", "-a").

        Returns:
            Tuple of (stdout, stderr, returncode).
        """
        cmd = ["dolt", *args]
        self._log.debug("running dolt command", cmd=cmd)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.config.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode().strip()
        stderr = stderr_bytes.decode().strip()
        returncode = proc.returncode or 0

        if returncode != 0:
            self._log.warning(
                "dolt command failed",
                cmd=cmd,
                stderr=stderr,
                returncode=returncode,
            )

        return stdout, stderr, returncode

    async def _run_dolt_json(self, *args: str) -> Any:
        """Run a Dolt CLI command and parse JSON output.

        Args:
            *args: Dolt command arguments.

        Returns:
            Parsed JSON output.

        Raises:
            ValueError: If output is not valid JSON.
        """
        stdout, _, _ = await self._run_dolt(*args)
        try:
            return json.loads(stdout) if stdout else []
        except json.JSONDecodeError as e:
            raise ValueError(f"Dolt returned non-JSON output: {stdout!r}") from e

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        raise NotImplementedError
