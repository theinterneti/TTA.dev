"""Parallel workflow primitive composition."""

from __future__ import annotations

import asyncio
from typing import Any

from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


class ParallelPrimitive(WorkflowPrimitive[Any, list[Any]]):
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

    async def execute(self, input_data: Any, context: WorkflowContext) -> list[Any]:
        """
        Execute primitives in parallel with instrumentation.

        Args:
            input_data: Input data sent to all primitives
            context: Workflow context

        Returns:
            List of outputs from all primitives (in order)

        Raises:
            Exception: If any primitive fails
        """
        # Record start checkpoint
        context.checkpoint("parallel_start")

        logger.info(
            "parallel_execution_start",
            branch_count=len(self.primitives),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Create child contexts for each branch
        child_contexts = [context.create_child_context() for _ in self.primitives]

        # Execute all branches
        tasks = [
            primitive.execute(input_data, child_ctx)
            for primitive, child_ctx in zip(self.primitives, child_contexts, strict=True)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        if exceptions:
            logger.error(
                "parallel_execution_failed",
                failed_count=len(exceptions),
                total_count=len(self.primitives),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            raise exceptions[0]  # Raise first exception

        # Record end checkpoint
        context.checkpoint("parallel_end")

        logger.info(
            "parallel_execution_complete",
            branch_count=len(self.primitives),
            elapsed_ms=context.elapsed_ms(),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        return results

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
