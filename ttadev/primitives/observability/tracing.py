"""Distributed tracing for workflow primitives."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
    from opentelemetry.sdk.trace import ReadableSpan

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

from ..core.base import WorkflowContext, WorkflowPrimitive


class FileSpanExporter(SpanExporter):
    """Export spans to a JSONL file."""

    def __init__(self, file_path: str = ".observability/traces.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        """Export spans to file."""
        try:
            with open(self.file_path, "a") as f:
                for span in spans:
                    span_dict = {
                        "trace_id": format(span.context.trace_id, "032x"),
                        "span_id": format(span.context.span_id, "016x"),
                        "name": span.name,
                        "start_time": span.start_time,
                        "end_time": span.end_time,
                        "duration_ns": span.end_time - span.start_time if span.end_time else 0,
                        "attributes": dict(span.attributes) if span.attributes else {},
                        "status": {
                            "status_code": span.status.status_code.name if span.status else "UNSET",
                            "description": span.status.description if span.status else "",
                        },
                        "parent_span_id": format(span.parent.span_id, "016x") if span.parent else None,
                    }
                    f.write(json.dumps(span_dict) + "\n")
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Error exporting spans: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown exporter."""
        pass


def setup_tracing(service_name: str = "tta-workflow") -> None:
    """
    Setup OpenTelemetry tracing with file-based export.

    Args:
        service_name: Name of the service for traces
    """
    if not TRACING_AVAILABLE:
        return

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    
    # Add file-based exporter
    file_exporter = FileSpanExporter()
    processor = BatchSpanProcessor(file_exporter)
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
