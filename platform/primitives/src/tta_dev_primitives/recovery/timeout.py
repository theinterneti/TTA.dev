"""Timeout enforcement for primitives.

# See: [[TTA.dev/Primitives/TimeoutPrimitive]]
"""

from __future__ import annotations

import asyncio
import builtins
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Timeout exceeded during execution."""

    pass


class TimeoutPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Enforce execution timeout with optional fallback.

    Prevents workflows from hanging indefinitely by enforcing time limits.
    Essential for maintaining good UX and resource efficiency.

    Example:
        ```python
        # Simple timeout
        workflow = TimeoutPrimitive(
            primitive=slow_operation,
            timeout_seconds=30.0
        )

        # Timeout with fallback
        workflow = TimeoutPrimitive(
            primitive=expensive_llm_call,
            timeout_seconds=30.0,
            fallback=cached_response_primitive
        )

        # Timeout with monitoring
        workflow = TimeoutPrimitive(
            primitive=critical_operation,
            timeout_seconds=45.0,
            fallback=degraded_service,
            track_timeouts=True
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        timeout_seconds: float,
        fallback: WorkflowPrimitive | None = None,
        track_timeouts: bool = True,
    ) -> None:
        """
        Initialize timeout primitive.

        Args:
            primitive: Primitive to execute with timeout
            timeout_seconds: Maximum execution time in seconds
            fallback: Optional fallback primitive on timeout
            track_timeouts: Whether to track timeout occurrences in context
        """
        self.primitive = primitive
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback
        self.track_timeouts = track_timeouts

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute with timeout enforcement.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from primitive or fallback

        Raises:
            TimeoutError: If timeout exceeded and no fallback provided
        """
        try:
            result = await asyncio.wait_for(
                self.primitive.execute(input_data, context),
                timeout=self.timeout_seconds,
            )

            logger.info(
                "timeout_success",
                primitive=self.primitive.__class__.__name__,
                timeout=self.timeout_seconds,
                workflow_id=context.workflow_id,
            )

            return result

        except builtins.TimeoutError:
            logger.warning(
                "timeout_exceeded",
                primitive=self.primitive.__class__.__name__,
                timeout=self.timeout_seconds,
                has_fallback=self.fallback is not None,
                workflow_id=context.workflow_id,
            )

            # Track timeout in context
            if self.track_timeouts:
                if "timeout_count" not in context.state:
                    context.state["timeout_count"] = 0
                context.state["timeout_count"] += 1

                if "timeout_history" not in context.state:
                    context.state["timeout_history"] = []
                context.state["timeout_history"].append(
                    {
                        "primitive": self.primitive.__class__.__name__,
                        "timeout": self.timeout_seconds,
                        "had_fallback": self.fallback is not None,
                    }
                )

            # Execute fallback if available
            if self.fallback:
                logger.info(
                    "executing_fallback",
                    fallback=self.fallback.__class__.__name__,
                )
                return await self.fallback.execute(input_data, context)

            # No fallback - raise error
            raise TimeoutError(f"Execution exceeded {self.timeout_seconds}s timeout")
