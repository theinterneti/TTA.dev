"""Distributed tracing for workflow primitives."""

from __future__ import annotations

import logging
import time
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

from ..core.base import WorkflowContext, WorkflowPrimitive
from .config import get_observability_config
from .sampling import CompositeSampler, SamplingConfig, SamplingDecision, SamplingResult

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "tta-workflow") -> None:
    """
    Setup OpenTelemetry tracing.

    Args:
        service_name: Name of the service for traces
    """
    if not TRACING_AVAILABLE:
        return

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


class ObservablePrimitive(WorkflowPrimitive[Any, Any]):
    """
    Wrapper adding observability to any primitive with sampling support.

    Provides:
    - Distributed tracing with OpenTelemetry
    - Intelligent sampling (probabilistic, tail-based, adaptive)
    - Structured logging with correlation IDs
    - Metrics collection

    Example:
        ```python
        from tta_dev_primitives.observability import ObservablePrimitive

        # Wrap primitives with observability
        workflow = (
            ObservablePrimitive(input_proc, "input_processing") >>
            ObservablePrimitive(world_build, "world_building") >>
            ObservablePrimitive(narrative_gen, "narrative_generation")
        )

        # Sampling is automatically applied based on configuration
        result = await workflow.execute(data, context)
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        name: str,
        sampler: CompositeSampler | None = None,
    ) -> None:
        """
        Initialize observable primitive with sampling.

        Args:
            primitive: The primitive to wrap
            name: Name for tracing and metrics
            sampler: Optional custom sampler (uses global config if None)
        """
        self.primitive = primitive
        self.name = name
        self.tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        # Initialize sampler from config if not provided
        if sampler is None:
            config = get_observability_config()
            self.sampler = CompositeSampler(config.tracing.sampling)
        else:
            self.sampler = sampler

        # Track sampling decision for tail-based sampling
        self._head_decision: SamplingResult | None = None

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitive with observability and sampling.

        Head-based sampling decision is made at execution start.
        Tail-based sampling can upgrade the decision based on errors or latency.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from the wrapped primitive

        Raises:
            Exception: If execution fails
        """
        start_time = time.time()
        has_error = False
        error_to_raise = None

        # Generate trace ID from context for consistent sampling
        trace_id = context.correlation_id or context.workflow_id or context.session_id

        # Head-based sampling decision
        self._head_decision = self.sampler.should_sample_head(trace_id=trace_id)

        # Determine if we should create a span
        should_trace = self._head_decision.decision == SamplingDecision.SAMPLE

        # Create span if tracing is available and sampled
        if self.tracer and should_trace:
            with self.tracer.start_as_current_span(
                f"primitive.{self.name}",
                attributes={
                    "primitive.name": self.name,
                    "workflow.id": context.workflow_id or "unknown",
                    "session.id": context.session_id or "unknown",
                    "sampling.decision": self._head_decision.decision.value,
                    "sampling.reason": self._head_decision.reason,
                    "sampling.rate": self._head_decision.sample_rate or 0.0,
                },
            ) as span:
                try:
                    result = await self.primitive.execute(input_data, context)
                    duration_ms = (time.time() - start_time) * 1000

                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("primitive.duration_ms", duration_ms)

                    # Tail-based sampling decision
                    tail_decision = self.sampler.should_sample_tail(
                        trace_id=trace_id,
                        has_error=False,
                        duration_ms=duration_ms,
                        head_decision=self._head_decision,
                    )

                    # Update span with tail decision
                    span.set_attribute("sampling.tail_decision", tail_decision.decision.value)
                    span.set_attribute("sampling.tail_reason", tail_decision.reason)

                    # Record metrics
                    from .metrics import get_metrics_collector

                    metrics = get_metrics_collector()
                    metrics.record_execution(self.name, duration_ms, success=True)

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    has_error = True
                    error_to_raise = e

                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                    # Tail-based sampling for errors (should always be sampled)
                    tail_decision = self.sampler.should_sample_tail(
                        trace_id=trace_id,
                        has_error=True,
                        duration_ms=duration_ms,
                        head_decision=self._head_decision,
                    )

                    # Mark span as important due to error
                    span.set_attribute("sampling.tail_decision", tail_decision.decision.value)
                    span.set_attribute("sampling.tail_reason", tail_decision.reason)
                    span.set_attribute("error.sampled", "true")

                    # Record failure metrics
                    from .metrics import get_metrics_collector

                    metrics = get_metrics_collector()
                    metrics.record_execution(
                        self.name, duration_ms, success=False, error_type=type(e).__name__
                    )

                    raise
        else:
            # No tracing (either unavailable or not sampled), just execute with metrics
            try:
                result = await self.primitive.execute(input_data, context)
                duration_ms = (time.time() - start_time) * 1000

                # Still check tail-based sampling for metrics
                if not should_trace:
                    tail_decision = self.sampler.should_sample_tail(
                        trace_id=trace_id,
                        has_error=False,
                        duration_ms=duration_ms,
                        head_decision=self._head_decision,
                    )

                    # Log if tail would have sampled
                    if tail_decision.decision == SamplingDecision.SAMPLE:
                        logger.debug(
                            f"Trace not sampled at head but would be sampled at tail: "
                            f"{self.name} (reason: {tail_decision.reason})"
                        )

                from .metrics import get_metrics_collector

                metrics = get_metrics_collector()
                metrics.record_execution(self.name, duration_ms, success=True)

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                has_error = True

                # Check tail-based sampling for errors
                if not should_trace:
                    tail_decision = self.sampler.should_sample_tail(
                        trace_id=trace_id,
                        has_error=True,
                        duration_ms=duration_ms,
                        head_decision=self._head_decision,
                    )

                    # Errors should always be sampled
                    if tail_decision.decision == SamplingDecision.SAMPLE:
                        logger.warning(
                            f"Error in unsampled trace (would be sampled at tail): "
                            f"{self.name} - {type(e).__name__}: {e}"
                        )

                from .metrics import get_metrics_collector

                metrics = get_metrics_collector()
                metrics.record_execution(
                    self.name, duration_ms, success=False, error_type=type(e).__name__
                )

                raise
