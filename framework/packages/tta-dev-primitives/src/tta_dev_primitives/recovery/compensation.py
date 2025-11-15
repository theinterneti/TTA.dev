"""Compensation patterns for workflow primitives (Saga pattern)."""

from __future__ import annotations

import time
from typing import Any

from opentelemetry import trace

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import TRACING_AVAILABLE
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

    See: [[TTA Primitives___CompensationPrimitive]] for more details.

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
        Execute with saga pattern and comprehensive instrumentation.

        This method provides observability for saga execution:
        - Creates spans for forward and compensation executions
        - Logs forward execution, compensation triggers, and outcomes
        - Records per-execution metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis
        - Monitors compensation patterns

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from forward primitive

        Raises:
            Exception: After running compensation
        """

        metrics_collector = get_enhanced_metrics_collector()
        # Log workflow start
        logger.info(
            "saga_workflow_start",
            forward_type=self.forward.__class__.__name__,
            compensation_type=self.compensation.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record start checkpoint
        context.checkpoint("saga.start")
        workflow_start_time = time.time()

        # Try forward execution
        logger.info(
            "saga_forward_start",
            forward_type=self.forward.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        context.checkpoint("saga.forward.start")
        forward_start_time = time.time()

        # Create forward span (if tracing available)

        tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        try:
            if tracer and TRACING_AVAILABLE:
                with tracer.start_as_current_span("saga.forward") as span:
                    span.set_attribute("saga.execution", "forward")
                    span.set_attribute(
                        "saga.forward_type", self.forward.__class__.__name__
                    )
                    span.set_attribute(
                        "saga.compensation_type", self.compensation.__class__.__name__
                    )

                    try:
                        result = await self.forward.execute(input_data, context)
                        span.set_attribute("saga.status", "success")
                        span.set_attribute("saga.compensation_triggered", False)
                    except Exception as e:
                        span.set_attribute("saga.status", "error")
                        span.set_attribute("saga.error", str(e))
                        span.record_exception(e)
                        raise
            else:
                # Graceful degradation - execute without span
                result = await self.forward.execute(input_data, context)

            # Forward succeeded! Record metrics and log
            context.checkpoint("saga.forward.end")
            forward_duration_ms = (time.time() - forward_start_time) * 1000

            metrics_collector.record_execution(
                "SagaPrimitive.forward",
                duration_ms=forward_duration_ms,
                success=True,
            )

            logger.info(
                "saga_forward_success",
                forward_type=self.forward.__class__.__name__,
                duration_ms=forward_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record workflow completion (no compensation needed)
            context.checkpoint("saga.end")
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000

            logger.info(
                "saga_workflow_complete",
                compensation_triggered=False,
                execution_path="forward",
                total_duration_ms=workflow_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record overall success metrics
            metrics_collector.record_execution(
                "SagaPrimitive.workflow",
                duration_ms=workflow_duration_ms,
                success=True,
            )

            return result

        except Exception as forward_error:
            # Forward failed - record metrics
            context.checkpoint("saga.forward.end")
            forward_duration_ms = (time.time() - forward_start_time) * 1000

            metrics_collector.record_execution(
                "SagaPrimitive.forward",
                duration_ms=forward_duration_ms,
                success=False,
            )

            logger.warning(
                "saga_forward_failed",
                forward_type=self.forward.__class__.__name__,
                duration_ms=forward_duration_ms,
                error=str(forward_error),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Trigger compensation
            logger.warning(
                "saga_compensation_triggered",
                forward_type=self.forward.__class__.__name__,
                compensation_type=self.compensation.__class__.__name__,
                forward_error=str(forward_error),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Try compensation execution
            logger.info(
                "saga_compensation_start",
                compensation_type=self.compensation.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            context.checkpoint("saga.compensation.start")
            compensation_start_time = time.time()

            try:
                if tracer and TRACING_AVAILABLE:
                    with tracer.start_as_current_span("saga.compensation") as span:
                        span.set_attribute("saga.execution", "compensation")
                        span.set_attribute(
                            "saga.compensation_type",
                            self.compensation.__class__.__name__,
                        )
                        span.set_attribute("saga.forward_error", str(forward_error))

                        try:
                            await self.compensation.execute(input_data, context)
                            span.set_attribute("saga.status", "success")
                            span.set_attribute("saga.compensation_triggered", True)
                        except Exception as e:
                            span.set_attribute("saga.status", "error")
                            span.set_attribute("saga.error", str(e))
                            span.record_exception(e)
                            raise
                else:
                    # Graceful degradation - execute without span
                    await self.compensation.execute(input_data, context)

                # Compensation succeeded! Record metrics and log
                context.checkpoint("saga.compensation.end")
                compensation_duration_ms = (
                    time.time() - compensation_start_time
                ) * 1000

                metrics_collector.record_execution(
                    "SagaPrimitive.compensation",
                    duration_ms=compensation_duration_ms,
                    success=True,
                )

                logger.info(
                    "saga_compensation_success",
                    compensation_type=self.compensation.__class__.__name__,
                    duration_ms=compensation_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record workflow completion (compensation succeeded)
                context.checkpoint("saga.end")
                workflow_duration_ms = (time.time() - workflow_start_time) * 1000

                logger.info(
                    "saga_workflow_complete",
                    compensation_triggered=True,
                    execution_path="compensation",
                    total_duration_ms=workflow_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record overall workflow metrics (forward failed, compensation succeeded)
                metrics_collector.record_execution(
                    "SagaPrimitive.workflow",
                    duration_ms=workflow_duration_ms,
                    success=False,  # Workflow failed (forward failed)
                )

            except Exception as compensation_error:
                # Compensation also failed - record metrics
                context.checkpoint("saga.compensation.end")
                compensation_duration_ms = (
                    time.time() - compensation_start_time
                ) * 1000

                metrics_collector.record_execution(
                    "SagaPrimitive.compensation",
                    duration_ms=compensation_duration_ms,
                    success=False,
                )

                logger.error(
                    "saga_compensation_failed",
                    compensation_type=self.compensation.__class__.__name__,
                    duration_ms=compensation_duration_ms,
                    error=str(compensation_error),
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Both failed - log critical failure
                logger.error(
                    "saga_critical_failure",
                    forward_error=str(forward_error),
                    compensation_error=str(compensation_error),
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record workflow failure
                context.checkpoint("saga.end")
                workflow_duration_ms = (time.time() - workflow_start_time) * 1000

                logger.error(
                    "saga_workflow_failed",
                    total_duration_ms=workflow_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record overall failure metrics
                metrics_collector.record_execution(
                    "SagaPrimitive.workflow",
                    duration_ms=workflow_duration_ms,
                    success=False,
                )

            # Always re-raise the original error
            raise forward_error
