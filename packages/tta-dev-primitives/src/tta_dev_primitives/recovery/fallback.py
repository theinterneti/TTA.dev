"""Fallback strategies for workflow primitives."""

from __future__ import annotations

from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class FallbackStrategy:
    """Strategy for fallback to alternative primitive."""

    def __init__(self, fallback_primitive: WorkflowPrimitive) -> None:
        """
        Initialize fallback strategy.

        Args:
            fallback_primitive: Alternative primitive to use on failure
        """
        self.fallback_primitive = fallback_primitive


class FallbackPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Try a primitive with fallback to alternative.

    Example:
        ```python
        workflow = FallbackPrimitive(
            primary=openai_narrative,
            fallback=local_narrative
        )
        ```
    """

    def __init__(
        self,
        primary: WorkflowPrimitive,
        fallback: WorkflowPrimitive,
    ) -> None:
        """
        Initialize fallback primitive.

        Args:
            primary: Primary primitive to try first
            fallback: Fallback primitive if primary fails
        """
        self.primary = primary
        self.fallback = fallback

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute with fallback logic.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from primary or fallback

        Raises:
            Exception: If both primary and fallback fail
        """
        try:
            return await self.primary.execute(input_data, context)

        except Exception as primary_error:
            logger.warning(
                "primitive_fallback_triggered",
                primary=self.primary.__class__.__name__,
                fallback=self.fallback.__class__.__name__,
                error=str(primary_error),
            )

            try:
                result = await self.fallback.execute(input_data, context)
                logger.info(
                    "primitive_fallback_succeeded",
                    fallback=self.fallback.__class__.__name__,
                )
                return result

            except Exception as fallback_error:
                logger.error(
                    "primitive_fallback_failed",
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error),
                )
                # Re-raise the original error
                raise primary_error
