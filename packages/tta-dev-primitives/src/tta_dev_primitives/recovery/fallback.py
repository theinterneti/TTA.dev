"""Fallback strategies for workflow primitives."""

from __future__ import annotations

import time
from typing import Any

from opentelemetry import trace

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import TRACING_AVAILABLE
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

        This method provides observability for fallback execution:
        - Creates spans for primary and fallback executions
        - Logs primary execution, fallback triggers, and outcomes
        - Records per-execution metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis
        - Monitors fallback usage patterns

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from primary or fallback

        Raises:
            Exception: If both primary and fallback fail
        """

        metrics_collector = get_enhanced_metrics_collector()
        # Log workflow start
        logger.info(
            "fallback_workflow_start",
            primary_type=self.primary.__class__.__name__,
            fallback_type=self.fallback.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record start checkpoint
        context.checkpoint("fallback.start")
        workflow_start_time = time.time()

        # Try primary execution
        logger.info(
            "fallback_primary_start",
            primary_type=self.primary.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        context.checkpoint("fallback.primary.start")
        primary_start_time = time.time()

        # Create primary span (if tracing available)

        tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        try:
            if tracer and TRACING_AVAILABLE:
                with tracer.start_as_current_span("fallback.primary") as span:
                    span.set_attribute("fallback.execution", "primary")
                    span.set_attribute("fallback.primary_type", self.primary.__class__.__name__)
                    span.set_attribute("fallback.fallback_type", self.fallback.__class__.__name__)

                    try:
                        result = await self.primary.execute(input_data, context)
                        span.set_attribute("fallback.status", "success")
                        span.set_attribute("fallback.used_fallback", False)
                    except Exception as e:
                        span.set_attribute("fallback.status", "error")
                        span.set_attribute("fallback.error", str(e))
                        span.record_exception(e)
                        raise
            else:
                # Graceful degradation - execute without span
                result = await self.primary.execute(input_data, context)

            # Primary succeeded! Record metrics and log
            context.checkpoint("fallback.primary.end")
            primary_duration_ms = (time.time() - primary_start_time) * 1000

            metrics_collector.record_execution(
                "FallbackPrimitive.primary",
                duration_ms=primary_duration_ms,
                success=True,
            )

            logger.info(
                "fallback_primary_success",
                primary_type=self.primary.__class__.__name__,
                duration_ms=primary_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record workflow completion (no fallback needed)
            context.checkpoint("fallback.end")
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000

            logger.info(
                "fallback_workflow_complete",
                used_fallback=False,
                execution_path="primary",
                total_duration_ms=workflow_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record overall success metrics
            metrics_collector.record_execution(
                "FallbackPrimitive.workflow",
                duration_ms=workflow_duration_ms,
                success=True,
            )

            return result

        except Exception as primary_error:
            # Primary failed - record metrics
            context.checkpoint("fallback.primary.end")
            primary_duration_ms = (time.time() - primary_start_time) * 1000

            metrics_collector.record_execution(
                "FallbackPrimitive.primary",
                duration_ms=primary_duration_ms,
                success=False,
            )

            logger.warning(
                "fallback_primary_failed",
                primary_type=self.primary.__class__.__name__,
                duration_ms=primary_duration_ms,
                error=str(primary_error),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Trigger fallback
            logger.warning(
                "fallback_triggered",
                primary_type=self.primary.__class__.__name__,
                fallback_type=self.fallback.__class__.__name__,
                primary_error=str(primary_error),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Try fallback execution
            logger.info(
                "fallback_execution_start",
                fallback_type=self.fallback.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            context.checkpoint("fallback.fallback.start")
            fallback_start_time = time.time()

            try:
                if tracer and TRACING_AVAILABLE:
                    with tracer.start_as_current_span("fallback.fallback") as span:
                        span.set_attribute("fallback.execution", "fallback")
                        span.set_attribute(
                            "fallback.fallback_type", self.fallback.__class__.__name__
                        )
                        span.set_attribute("fallback.primary_error", str(primary_error))

                        try:
                            result = await self.fallback.execute(input_data, context)
                            span.set_attribute("fallback.status", "success")
                            span.set_attribute("fallback.used_fallback", True)
                        except Exception as e:
                            span.set_attribute("fallback.status", "error")
                            span.set_attribute("fallback.error", str(e))
                            span.record_exception(e)
                            raise
                else:
                    # Graceful degradation - execute without span
                    result = await self.fallback.execute(input_data, context)

                # Fallback succeeded! Record metrics and log
                context.checkpoint("fallback.fallback.end")
                fallback_duration_ms = (time.time() - fallback_start_time) * 1000

                metrics_collector.record_execution(
                    "FallbackPrimitive.fallback",
                    duration_ms=fallback_duration_ms,
                    success=True,
                )

                logger.info(
                    "fallback_execution_success",
                    fallback_type=self.fallback.__class__.__name__,
                    duration_ms=fallback_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record workflow completion (fallback succeeded)
                context.checkpoint("fallback.end")
                workflow_duration_ms = (time.time() - workflow_start_time) * 1000

                logger.info(
                    "fallback_workflow_complete",
                    used_fallback=True,
                    execution_path="fallback",
                    total_duration_ms=workflow_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record overall success metrics
                metrics_collector.record_execution(
                    "FallbackPrimitive.workflow",
                    duration_ms=workflow_duration_ms,
                    success=True,
                )

                return result

            except Exception as fallback_error:
                # Fallback also failed - record metrics
                context.checkpoint("fallback.fallback.end")
                fallback_duration_ms = (time.time() - fallback_start_time) * 1000

                metrics_collector.record_execution(
                    "FallbackPrimitive.fallback",
                    duration_ms=fallback_duration_ms,
                    success=False,
                )

                logger.error(
                    "fallback_execution_failed",
                    fallback_type=self.fallback.__class__.__name__,
                    duration_ms=fallback_duration_ms,
                    error=str(fallback_error),
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Both failed - log exhaustion
                logger.error(
                    "fallback_exhausted",
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error),
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record workflow failure
                context.checkpoint("fallback.end")
                workflow_duration_ms = (time.time() - workflow_start_time) * 1000

                logger.error(
                    "fallback_workflow_failed",
                    total_duration_ms=workflow_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record overall failure metrics
                metrics_collector.record_execution(
                    "FallbackPrimitive.workflow",
                    duration_ms=workflow_duration_ms,
                    success=False,
                )

                # Re-raise the original error
                raise primary_error
