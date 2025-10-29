"""Compensation patterns for workflow primitives (Saga pattern)."""

from __future__ import annotations

from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class CompensationStrategy:
    """Strategy for compensating transaction (undoing effects)."""

    def __init__(self, compensation_primitive: WorkflowPrimitive) -> None:
        """
        Initialize compensation strategy.

        Args:
            compensation_primitive: Primitive to run for compensation
        """
        self.compensation_primitive = compensation_primitive


class SagaPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Saga pattern: Execute with compensation on failure.

    Useful for maintaining consistency across distributed operations.

    Example:
        ```python
        workflow = SagaPrimitive(
            forward=update_world_state,
            compensation=rollback_world_state
        )
        ```
    """

    def __init__(
        self,
        forward: WorkflowPrimitive,
        compensation: WorkflowPrimitive,
    ) -> None:
        """
        Initialize saga primitive.

        Args:
            forward: Forward transaction primitive
            compensation: Compensation primitive (runs on failure)
        """
        self.forward = forward
        self.compensation = compensation

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute with saga pattern and instrumentation.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from forward primitive

        Raises:
            Exception: After running compensation
        """
        try:
            logger.info(
                "saga_forward_attempt",
                forward=self.forward.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            
            result = await self.forward.execute(input_data, context)
            
            logger.info(
                "saga_forward_succeeded",
                forward=self.forward.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            
            return result

        except Exception as forward_error:
            logger.warning(
                "saga_compensation_triggered",
                forward=self.forward.__class__.__name__,
                compensation=self.compensation.__class__.__name__,
                error=str(forward_error),
                error_type=type(forward_error).__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            try:
                await self.compensation.execute(input_data, context)
                logger.info(
                    "saga_compensation_succeeded",
                    compensation=self.compensation.__class__.__name__,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

            except Exception as compensation_error:
                logger.error(
                    "saga_compensation_failed",
                    forward_error=str(forward_error),
                    forward_error_type=type(forward_error).__name__,
                    compensation_error=str(compensation_error),
                    compensation_error_type=type(compensation_error).__name__,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

            # Always re-raise the original error
            raise forward_error
