"""Distributed tracing for workflow primitives."""

from __future__ import annotations

import time
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

from ..core.base import WorkflowContext, WorkflowPrimitive


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
    Wrapper adding observability to any primitive.

    Provides:
    - Distributed tracing with OpenTelemetry
    - Structured logging with correlation IDs
    - Metrics collection

    Example:
        ```python
        workflow = (
            ObservablePrimitive(input_proc, "input_processing") >>
            ObservablePrimitive(world_build, "world_building") >>
            ObservablePrimitive(narrative_gen, "narrative_generation")
        )
        ```
    """

    def __init__(self, primitive: WorkflowPrimitive, name: str) -> None:
        """
        Initialize observable primitive.

        Args:
            primitive: The primitive to wrap
            name: Name for tracing and metrics
        """
        self.primitive = primitive
        self.name = name
        self.tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitive with observability.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output from the wrapped primitive

        Raises:
            Exception: If execution fails
        """
        start_time = time.time()

        # Create span if tracing is available
        if self.tracer:
            with self.tracer.start_as_current_span(
                f"primitive.{self.name}",
                attributes={
                    "primitive.name": self.name,
                    "workflow.id": context.workflow_id or "unknown",
                    "session.id": context.session_id or "unknown",
                },
            ) as span:
                try:
                    result = await self.primitive.execute(input_data, context)
                    duration_ms = (time.time() - start_time) * 1000

                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("primitive.duration_ms", duration_ms)

                    # Record metrics
                    from .metrics import get_metrics_collector

                    metrics = get_metrics_collector()
                    metrics.record_execution(self.name, duration_ms, success=True)

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                    # Record failure metrics
                    from .metrics import get_metrics_collector

                    metrics = get_metrics_collector()
                    metrics.record_execution(
                        self.name, duration_ms, success=False, error_type=type(e).__name__
                    )

                    raise
        else:
            # No tracing, just execute with metrics
            try:
                result = await self.primitive.execute(input_data, context)
                duration_ms = (time.time() - start_time) * 1000

                from .metrics import get_metrics_collector

                metrics = get_metrics_collector()
                metrics.record_execution(self.name, duration_ms, success=True)

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                from .metrics import get_metrics_collector

                metrics = get_metrics_collector()
                metrics.record_execution(
                    self.name, duration_ms, success=False, error_type=type(e).__name__
                )

                raise
