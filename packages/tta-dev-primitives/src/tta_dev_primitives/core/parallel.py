"""Parallel workflow primitive composition."""

from __future__ import annotations

import asyncio
from typing import Any

from ..observability.instrumented_primitive import InstrumentedPrimitive
from .base import WorkflowContext, WorkflowPrimitive


class ParallelPrimitive(InstrumentedPrimitive[Any, list[Any]]):
    """
    Execute primitives in parallel.

    All primitives receive the same input and execute concurrently.
    Results are collected in a list.

    Example:
        ```python
        workflow = ParallelPrimitive([
            world_building,
            character_analysis,
            theme_analysis
        ])
        # Or use | operator:
        workflow = world_building | character_analysis | theme_analysis
        ```
    """

    def __init__(self, primitives: list[WorkflowPrimitive]) -> None:
        """
        Initialize with a list of primitives.

        Args:
            primitives: List of primitives to execute in parallel
        """
        if not primitives:
            raise ValueError("ParallelPrimitive requires at least one primitive")
        self.primitives = primitives
        # Initialize InstrumentedPrimitive with name
        super().__init__(name="ParallelPrimitive")

    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> list[Any]:
        """
        Execute primitives in parallel.

        Each primitive receives the same input and executes concurrently.
        Child contexts are created for each branch to maintain trace hierarchy.

        Args:
            input_data: Input data sent to all primitives
            context: Workflow context

        Returns:
            List of outputs from all primitives (in order)

        Raises:
            Exception: If any primitive fails
        """
        # Create child contexts for each parallel branch
        # This ensures proper trace context inheritance
        child_contexts = [context.create_child_context() for _ in self.primitives]

        # Execute all primitives in parallel with their own contexts
        tasks = [
            primitive.execute(input_data, child_ctx)
            for primitive, child_ctx in zip(self.primitives, child_contexts, strict=False)
        ]
        return await asyncio.gather(*tasks)

    def __or__(self, other: WorkflowPrimitive) -> ParallelPrimitive:
        """
        Add another primitive to parallel execution: self | other.

        Optimizes by flattening nested parallel primitives.

        Args:
            other: Primitive to add to parallel execution

        Returns:
            A new parallel primitive with all branches
        """
        if isinstance(other, ParallelPrimitive):
            # Flatten nested parallel primitives
            return ParallelPrimitive(self.primitives + other.primitives)
        else:
            return ParallelPrimitive(self.primitives + [other])
