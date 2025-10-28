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
        Execute primitive with retry logic.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from the primitive

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(self.strategy.max_retries + 1):
            try:
                return await self.primitive.execute(input_data, context)

            except Exception as e:
                last_error = e

                if attempt < self.strategy.max_retries:
                    delay = self.strategy.calculate_delay(attempt)
                    logger.warning(
                        "primitive_retry",
                        primitive=self.primitive.__class__.__name__,
                        attempt=attempt + 1,
                        max_retries=self.strategy.max_retries + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "primitive_retry_exhausted",
                        primitive=self.primitive.__class__.__name__,
                        attempts=self.strategy.max_retries + 1,
                        error=str(e),
                    )

        raise last_error
