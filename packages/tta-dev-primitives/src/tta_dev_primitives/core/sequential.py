"""Sequential workflow primitive composition."""

from __future__ import annotations

from typing import Any

from ..observability.instrumented_primitive import InstrumentedPrimitive
from .base import WorkflowContext, WorkflowPrimitive


class SequentialPrimitive(InstrumentedPrimitive[Any, Any]):
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
        # Initialize InstrumentedPrimitive with name
        super().__init__(name="SequentialPrimitive")

    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitives sequentially.

        Args:
            input_data: Initial input data
            context: Workflow context

        Returns:
            Output from the last primitive

        Raises:
            Exception: If any primitive fails
        """
        result = input_data
        for i, primitive in enumerate(self.primitives):
            # Record step checkpoint
            context.checkpoint(f"sequential.step_{i}.start")
            result = await primitive.execute(result, context)
            context.checkpoint(f"sequential.step_{i}.end")
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
