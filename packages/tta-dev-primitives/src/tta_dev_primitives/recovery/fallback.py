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
        Execute with fallback logic and comprehensive instrumentation.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from primary or fallback

        Raises:
            Exception: If both primary and fallback fail
        """
        logger.info(
            "fallback_primitive_start",
            primary=self.primary.__class__.__name__,
            fallback=self.fallback.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        try:
            result = await self.primary.execute(input_data, context)

            logger.info(
                "fallback_primary_succeeded",
                primary=self.primary.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Store success statistics in context
            if "fallback_statistics" not in context.state:
                context.state["fallback_statistics"] = []
            context.state["fallback_statistics"].append(
                {
                    "primary": self.primary.__class__.__name__,
                    "fallback": self.fallback.__class__.__name__,
                    "used_fallback": False,
                    "success": True,
                }
            )

            return result

        except Exception as primary_error:
            primary_error_type = type(primary_error).__name__

            logger.warning(
                "primitive_fallback_triggered",
                primary=self.primary.__class__.__name__,
                fallback=self.fallback.__class__.__name__,
                error=str(primary_error),
                error_type=primary_error_type,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            try:
                result = await self.fallback.execute(input_data, context)
                logger.info(
                    "primitive_fallback_succeeded",
                    fallback=self.fallback.__class__.__name__,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Store fallback success statistics in context
                if "fallback_statistics" not in context.state:
                    context.state["fallback_statistics"] = []
                context.state["fallback_statistics"].append(
                    {
                        "primary": self.primary.__class__.__name__,
                        "fallback": self.fallback.__class__.__name__,
                        "used_fallback": True,
                        "success": True,
                        "primary_error_type": primary_error_type,
                    }
                )

                return result

            except Exception as fallback_error:
                fallback_error_type = type(fallback_error).__name__

                logger.error(
                    "primitive_fallback_failed",
                    primary_error=str(primary_error),
                    primary_error_type=primary_error_type,
                    fallback_error=str(fallback_error),
                    fallback_error_type=fallback_error_type,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Store failure statistics in context
                if "fallback_statistics" not in context.state:
                    context.state["fallback_statistics"] = []
                context.state["fallback_statistics"].append(
                    {
                        "primary": self.primary.__class__.__name__,
                        "fallback": self.fallback.__class__.__name__,
                        "used_fallback": True,
                        "success": False,
                        "primary_error_type": primary_error_type,
                        "fallback_error_type": fallback_error_type,
                    }
                )

                # Re-raise the original error
                raise primary_error
