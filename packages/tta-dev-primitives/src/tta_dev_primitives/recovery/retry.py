"""Retry strategies for workflow primitives."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import TRACING_AVAILABLE
from ..observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetryStrategy:
    """Configuration for retry behavior."""

    max_retries: int = 3
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(self.backoff_base**attempt, self.max_backoff)

        if self.jitter:
            delay *= 0.5 + random.random()

        return delay


class RetryPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Retry a primitive with exponential backoff.

    Example:
        ```python
        workflow = RetryPrimitive(
            risky_primitive,
            strategy=RetryStrategy(max_retries=3, backoff_base=2.0)
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        strategy: RetryStrategy | None = None,
    ) -> None:
        """
        Initialize retry primitive.

        Args:
            primitive: The primitive to retry
            strategy: Retry strategy configuration
        """
        self.primitive = primitive
        self.strategy = strategy or RetryStrategy()

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitive with retry logic and comprehensive instrumentation.

        This method provides observability for retry execution:
        - Creates spans for each retry attempt
        - Logs retry attempts, backoff delays, and outcomes
        - Records per-attempt metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis
        - Monitors retry patterns and success rates

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from the primitive

        Raises:
            Exception: If all retries fail
        """

        metrics_collector = get_enhanced_metrics_collector()

        # Log workflow start
        logger.info(
            "retry_workflow_start",
            max_retries=self.strategy.max_retries,
            backoff_base=self.strategy.backoff_base,
            primitive_type=self.primitive.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record start checkpoint
        context.checkpoint("retry.start")
        workflow_start_time = time.time()

        last_error = None
        total_attempts = self.strategy.max_retries + 1

        # Create tracer once (if tracing available)

        tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        for attempt in range(total_attempts):
            # Log attempt start
            logger.info(
                "retry_attempt_start",
                attempt=attempt + 1,
                total_attempts=total_attempts,
                primitive_type=self.primitive.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record attempt checkpoint
            context.checkpoint(f"retry.attempt_{attempt}.start")
            attempt_start_time = time.time()

            try:
                if tracer and TRACING_AVAILABLE:
                    with tracer.start_as_current_span(
                        f"retry.attempt_{attempt}"
                    ) as span:
                        span.set_attribute("retry.attempt", attempt + 1)
                        span.set_attribute("retry.max_attempts", total_attempts)
                        span.set_attribute(
                            "retry.primitive_type", self.primitive.__class__.__name__
                        )

                        try:
                            result = await self.primitive.execute(input_data, context)
                            span.set_attribute("retry.status", "success")
                            span.set_attribute(
                                "retry.succeeded_on_attempt", attempt + 1
                            )
                        except Exception as e:
                            span.set_attribute("retry.status", "error")
                            span.set_attribute("retry.error", str(e))
                            span.record_exception(e)
                            raise
                else:
                    # Graceful degradation - execute without span
                    result = await self.primitive.execute(input_data, context)

                # Success! Record metrics and log
                context.checkpoint(f"retry.attempt_{attempt}.end")
                attempt_duration_ms = (time.time() - attempt_start_time) * 1000

                metrics_collector.record_execution(
                    f"RetryPrimitive.attempt_{attempt}",
                    duration_ms=attempt_duration_ms,
                    success=True,
                )

                logger.info(
                    "retry_attempt_success",
                    attempt=attempt + 1,
                    total_attempts=total_attempts,
                    duration_ms=attempt_duration_ms,
                    primitive_type=self.primitive.__class__.__name__,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record workflow completion
                context.checkpoint("retry.end")
                workflow_duration_ms = (time.time() - workflow_start_time) * 1000

                logger.info(
                    "retry_workflow_complete",
                    succeeded_on_attempt=attempt + 1,
                    total_attempts=total_attempts,
                    total_duration_ms=workflow_duration_ms,
                    workflow_id=context.workflow_id,
                    correlation_id=context.correlation_id,
                )

                # Record overall success metrics
                metrics_collector.record_execution(
                    "RetryPrimitive.workflow",
                    duration_ms=workflow_duration_ms,
                    success=True,
                )

                return result

            except Exception as e:
                last_error = e

                # Record attempt failure
                context.checkpoint(f"retry.attempt_{attempt}.end")
                attempt_duration_ms = (time.time() - attempt_start_time) * 1000

                metrics_collector.record_execution(
                    f"RetryPrimitive.attempt_{attempt}",
                    duration_ms=attempt_duration_ms,
                    success=False,
                )

                if attempt < self.strategy.max_retries:
                    # Calculate backoff delay
                    delay = self.strategy.calculate_delay(attempt)

                    logger.warning(
                        "retry_attempt_failed",
                        attempt=attempt + 1,
                        total_attempts=total_attempts,
                        duration_ms=attempt_duration_ms,
                        backoff_delay=delay,
                        error=str(e),
                        primitive_type=self.primitive.__class__.__name__,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )

                    # Record backoff checkpoint
                    context.checkpoint(f"retry.backoff_{attempt}.start")
                    backoff_start_time = time.time()

                    await asyncio.sleep(delay)

                    # Record backoff metrics
                    backoff_duration_ms = (time.time() - backoff_start_time) * 1000
                    context.checkpoint(f"retry.backoff_{attempt}.end")

                    metrics_collector.record_execution(
                        f"RetryPrimitive.backoff_{attempt}",
                        duration_ms=backoff_duration_ms,
                        success=True,
                    )

                    logger.info(
                        "retry_backoff_complete",
                        attempt=attempt + 1,
                        backoff_delay=delay,
                        actual_duration_ms=backoff_duration_ms,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )
                else:
                    # Retry exhausted
                    logger.error(
                        "retry_exhausted",
                        total_attempts=total_attempts,
                        final_error=str(e),
                        primitive_type=self.primitive.__class__.__name__,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )

                    # Record workflow failure
                    context.checkpoint("retry.end")
                    workflow_duration_ms = (time.time() - workflow_start_time) * 1000

                    logger.error(
                        "retry_workflow_failed",
                        total_attempts=total_attempts,
                        total_duration_ms=workflow_duration_ms,
                        workflow_id=context.workflow_id,
                        correlation_id=context.correlation_id,
                    )

                    # Record overall failure metrics
                    metrics_collector.record_execution(
                        "RetryPrimitive.workflow",
                        duration_ms=workflow_duration_ms,
                        success=False,
                    )

        if last_error is not None:
            raise last_error
        raise RuntimeError("Retry failed without capturing an error")
