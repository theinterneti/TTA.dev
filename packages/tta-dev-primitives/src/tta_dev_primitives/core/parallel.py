"""Parallel workflow primitive composition."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from ..observability.instrumented_primitive import (
    InstrumentedPrimitive,
)
from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


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

    async def _execute_impl(
        self, input_data: Any, context: WorkflowContext
    ) -> list[Any]:
        """
        Execute primitives in parallel with branch-level instrumentation.

        This method provides comprehensive observability for parallel execution:
        - Creates child spans for each branch execution
        - Logs workflow start/completion and branch timing
        - Records per-branch metrics (duration, success/failure)
        - Tracks checkpoints for fan-out/fan-in timing analysis
        - Monitors concurrency and parallel execution patterns

        Args:
            input_data: Input data sent to all primitives
            context: Workflow context

        Returns:
            List of outputs from all primitives (in order)

        Raises:
            Exception: If any primitive fails
        """
        from ..observability.enhanced_collector import get_enhanced_metrics_collector
        from ..observability.instrumented_primitive import TRACING_AVAILABLE

        metrics_collector = get_enhanced_metrics_collector()

        # Log workflow start
        logger.info(
            "parallel_workflow_start",
            branch_count=len(self.primitives),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record fan-out checkpoint
        context.checkpoint("parallel.fan_out")
        workflow_start_time = time.time()

        # Create child contexts for each parallel branch
        # This ensures proper trace context inheritance
        child_contexts = [context.create_child_context() for _ in self.primitives]

        # Create tasks with branch-level instrumentation
        async def execute_branch(
            branch_idx: int, primitive: WorkflowPrimitive, child_ctx: WorkflowContext
        ) -> Any:
            """Execute a single branch with instrumentation."""
            branch_name = f"branch_{branch_idx}_{primitive.__class__.__name__}"

            # Log branch start
            logger.info(
                "parallel_branch_start",
                branch=branch_idx,
                total_branches=len(self.primitives),
                primitive_type=primitive.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record checkpoint
            context.checkpoint(f"parallel.branch_{branch_idx}.start")
            branch_start_time = time.time()

            # Create branch span (if tracing available)
            if self._tracer and TRACING_AVAILABLE:
                with self._tracer.start_as_current_span(
                    f"parallel.branch_{branch_idx}"
                ) as span:
                    span.set_attribute("branch.index", branch_idx)
                    span.set_attribute("branch.name", branch_name)
                    span.set_attribute(
                        "branch.primitive_type", primitive.__class__.__name__
                    )
                    span.set_attribute("branch.total_branches", len(self.primitives))

                    try:
                        result = await primitive.execute(input_data, child_ctx)
                        span.set_attribute("branch.status", "success")
                    except Exception as e:
                        span.set_attribute("branch.status", "error")
                        span.set_attribute("branch.error", str(e))
                        span.record_exception(e)
                        raise
            else:
                # Graceful degradation - execute without branch span
                result = await primitive.execute(input_data, child_ctx)

            # Record checkpoint and metrics
            context.checkpoint(f"parallel.branch_{branch_idx}.end")
            branch_duration_ms = (time.time() - branch_start_time) * 1000
            metrics_collector.record_execution(
                f"{self.name}.branch_{branch_idx}",
                duration_ms=branch_duration_ms,
                success=True,
            )

            # Log branch completion
            logger.info(
                "parallel_branch_complete",
                branch=branch_idx,
                total_branches=len(self.primitives),
                primitive_type=primitive.__class__.__name__,
                duration_ms=branch_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            return result

        # Execute all branches in parallel
        tasks = [
            execute_branch(i, primitive, child_ctx)
            for i, (primitive, child_ctx) in enumerate(
                zip(self.primitives, child_contexts, strict=True)
            )
        ]

        # Gather results (this is the fan-in point)
        results = await asyncio.gather(*tasks)

        # Record fan-in checkpoint
        context.checkpoint("parallel.fan_in")
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000

        # Log workflow completion
        logger.info(
            "parallel_workflow_complete",
            branch_count=len(self.primitives),
            total_duration_ms=workflow_duration_ms,
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
