"""Retry strategies for workflow primitives."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetryStrategy:
    """Configuration for retry behavior."""

    max_retries: int = 3
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(self.backoff_base**attempt, self.max_backoff)

        if self.jitter:
            delay *= 0.5 + random.random()

        return delay


class RetryPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Retry a primitive with exponential backoff.

    Example:
        ```python
        workflow = RetryPrimitive(
            risky_primitive,
            strategy=RetryStrategy(max_retries=3, backoff_base=2.0)
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        strategy: RetryStrategy | None = None,
    ) -> None:
        """
        Initialize retry primitive.

        Args:
            primitive: The primitive to retry
            strategy: Retry strategy configuration
        """
        self.primitive = primitive
        self.strategy = strategy or RetryStrategy()

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitive with retry logic and comprehensive instrumentation.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from the primitive

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        # Log retry configuration
        logger.info(
            "retry_primitive_start",
            primitive=self.primitive.__class__.__name__,
            max_retries=self.strategy.max_retries,
            backoff_base=self.strategy.backoff_base,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        for attempt in range(self.strategy.max_retries + 1):
            try:
                result = await self.primitive.execute(input_data, context)

                # Log successful execution (especially if after retries)
                if attempt > 0:
                    logger.info(
                        "retry_primitive_success_after_retries",
                        primitive=self.primitive.__class__.__name__,
                        attempt=attempt + 1,
                        total_attempts=self.strategy.max_retries + 1,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )

                # Store retry statistics in context
                if "retry_statistics" not in context.state:
                    context.state["retry_statistics"] = []
                context.state["retry_statistics"].append(
                    {
                        "primitive": self.primitive.__class__.__name__,
                        "attempts": attempt + 1,
                        "success": True,
                    }
                )

                return result

            except Exception as e:
                last_error = e
                error_type = type(e).__name__

                if attempt < self.strategy.max_retries:
                    delay = self.strategy.calculate_delay(attempt)
                    logger.warning(
                        "primitive_retry",
                        primitive=self.primitive.__class__.__name__,
                        attempt=attempt + 1,
                        max_retries=self.strategy.max_retries + 1,
                        delay=delay,
                        error=str(e),
                        error_type=error_type,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "primitive_retry_exhausted",
                        primitive=self.primitive.__class__.__name__,
                        attempts=self.strategy.max_retries + 1,
                        error=str(e),
                        error_type=error_type,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )

                    # Store failure statistics in context
                    if "retry_statistics" not in context.state:
                        context.state["retry_statistics"] = []
                    context.state["retry_statistics"].append(
                        {
                            "primitive": self.primitive.__class__.__name__,
                            "attempts": attempt + 1,
                            "success": False,
                            "error_type": error_type,
                        }
                    )

        raise last_error
