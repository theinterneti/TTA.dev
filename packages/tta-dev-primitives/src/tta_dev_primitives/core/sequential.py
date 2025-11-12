"""Sequential workflow primitive composition."""

from __future__ import annotations

import time
from typing import Any

from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import (
    TRACING_AVAILABLE,
    InstrumentedPrimitive,
)
from ..observability.logging import get_logger
from ..observability.metrics_v2 import get_primitive_metrics
from ..observability.prometheus_metrics import get_prometheus_metrics
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


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
        # Initialize InstrumentedPrimitive with semantic naming
        super().__init__(name="SequentialPrimitive", primitive_type="sequential", action="execute")

    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitives sequentially with step-level instrumentation.

        This method provides comprehensive observability for each step:
        - Creates child spans for each step execution
        - Logs step start/completion with timing
        - Records per-step metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis

        Args:
            input_data: Initial input data
            context: Workflow context

        Returns:
            Output from the last primitive

        Raises:
            Exception: If any primitive fails
        """
        metrics_collector = get_enhanced_metrics_collector()
        primitive_metrics = get_primitive_metrics()
        prom_metrics = get_prometheus_metrics()

        # Record workflow start
        workflow_success = False

        # Log workflow start
        logger.info(
            "sequential_workflow_start",
            step_count=len(self.primitives),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        try:
            result = input_data
            for i, primitive in enumerate(self.primitives):
                step_name = f"step_{i}_{primitive.__class__.__name__}"

                # Record connection to next primitive (for service map)
                if i > 0:
                    prev_primitive = self.primitives[i - 1]
                    primitive_metrics.record_connection(
                        source_primitive=prev_primitive.__class__.__name__,
                        target_primitive=primitive.__class__.__name__,
                        connection_type="sequential",
                    )

                # Log step start
                logger.info(
                    "sequential_step_start",
                    step=i,
                    total_steps=len(self.primitives),
                    primitive_type=primitive.__class__.__name__,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record checkpoint
                context.checkpoint(f"sequential.step_{i}.start")
                step_start_time = time.time()

                # Create step span (if tracing available)
                if self._tracer and TRACING_AVAILABLE:
                    # Use semantic span naming: primitive.sequential.step_0
                    step_span_name = f"primitive.sequential.step_{i}"
                    with self._tracer.start_as_current_span(step_span_name) as span:
                        # Standard step attributes
                        span.set_attribute("step.index", i)
                        span.set_attribute("step.name", step_name)
                        span.set_attribute("step.primitive_type", primitive.__class__.__name__)
                        span.set_attribute("step.total_steps", len(self.primitives))
                        span.set_attribute("primitive.type", "sequential")
                        span.set_attribute("primitive.action", f"step_{i}")

                        try:
                            result = await primitive.execute(result, context)
                            span.set_attribute("step.status", "success")
                            span.set_attribute("execution.status", "success")
                        except Exception as e:
                            span.set_attribute("step.status", "error")
                            span.set_attribute("execution.status", "error")
                            span.set_attribute("step.error", str(e))
                            span.set_attribute("error.type", type(e).__name__)
                            span.set_attribute("error.message", str(e))
                            span.record_exception(e)
                            raise
                else:
                    # Graceful degradation - execute without step span
                    result = await primitive.execute(result, context)

                # Record checkpoint and metrics
                context.checkpoint(f"sequential.step_{i}.end")
                step_duration_ms = (time.time() - step_start_time) * 1000
                metrics_collector.record_execution(
                    f"{self.name}.step_{i}", duration_ms=step_duration_ms, success=True
                )

                # Log step completion
                logger.info(
                    "sequential_step_complete",
                    step=i,
                    total_steps=len(self.primitives),
                    primitive_type=primitive.__class__.__name__,
                    duration_ms=step_duration_ms,
                    elapsed_ms=context.elapsed_ms(),
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

            # Mark workflow as successful
            workflow_success = True

            # Log workflow completion
            logger.info(
                "sequential_workflow_complete",
                step_count=len(self.primitives),
                total_duration_ms=context.elapsed_ms(),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            return result

        except Exception:
            # Workflow failed - let exception propagate
            # Prometheus metrics will be recorded in finally block
            raise

        finally:
            # Record workflow-level Prometheus metrics (success or failure)
            prom_metrics.record_workflow_execution(
                workflow_name="SequentialPrimitive",
                status="success" if workflow_success else "failure",
            )

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
