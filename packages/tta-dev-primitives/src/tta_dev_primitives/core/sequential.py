"""Sequential workflow primitive composition."""

from __future__ import annotations

from typing import Any

from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


class SequentialPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Execute primitives in sequence.

    Each primitive's output becomes the next primitive's input.

    Example:
        ```python
        workflow = SequentialPrimitive([
            input_processing,
            world_building,
            narrative_generation
        ])
        # Or use >> operator:
        workflow = input_processing >> world_building >> narrative_generation
        ```
    """

    def __init__(self, primitives: list[WorkflowPrimitive]) -> None:
        """
        Initialize with a list of primitives.

        Args:
            primitives: List of primitives to execute in order
        """
        if not primitives:
            raise ValueError("SequentialPrimitive requires at least one primitive")
        self.primitives = primitives

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitives sequentially with instrumentation.

        Args:
            input_data: Initial input data
            context: Workflow context

        Returns:
            Output from the last primitive

        Raises:
            Exception: If any primitive fails
        """
        # Record start checkpoint
        context.checkpoint("sequential_start")

        logger.info(
            "sequential_execution_start",
            total_steps=len(self.primitives),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        result = input_data
        for idx, primitive in enumerate(self.primitives):
            step_name = f"step_{idx}_{primitive.__class__.__name__}"

            # Log step start
            logger.info(
                "sequential_step_start",
                step=idx,
                total_steps=len(self.primitives),
                primitive=primitive.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Execute step
            result = await primitive.execute(result, context)

            # Record checkpoint
            context.checkpoint(step_name)

            # Log step completion
            logger.info(
                "sequential_step_complete",
                step=idx,
                total_steps=len(self.primitives),
                primitive=primitive.__class__.__name__,
                elapsed_ms=context.elapsed_ms(),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

        # Record end checkpoint
        context.checkpoint("sequential_end")

        logger.info(
            "sequential_execution_complete",
            total_steps=len(self.primitives),
            elapsed_ms=context.elapsed_ms(),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        return result

    def __rshift__(self, other: WorkflowPrimitive) -> SequentialPrimitive:
        """
        Chain another primitive: self >> other.

        Optimizes by flattening nested sequential primitives.

        Args:
            other: Primitive to append

        Returns:
            A new sequential primitive with all steps
        """
        if isinstance(other, SequentialPrimitive):
            # Flatten nested sequential primitives
            return SequentialPrimitive(self.primitives + other.primitives)
        else:
            return SequentialPrimitive(self.primitives + [other])
