"""Distributed tracing for workflow primitives."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Agent identity — delegate to the shared module; re-export for callers that
# import directly from tracing (backward compat).
# ---------------------------------------------------------------------------
try:
    from ttadev.observability.agent_identity import get_agent_id, get_agent_tool
except ImportError:
    # ttadev.observability not installed — generate a minimal fallback so the
    # primitives package remains usable in isolation.
    import os
    import uuid as _uuid

    _FALLBACK_ID: str = os.environ.get("TTA_AGENT_ID") or str(_uuid.uuid4())

    def get_agent_id() -> str:  # type: ignore[misc]
        return _FALLBACK_ID

    def get_agent_tool() -> str:  # type: ignore[misc]
        if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
            return "claude-code"
        if "vscode" in os.environ.get("TERM_PROGRAM", "").lower():
            return "copilot"
        if os.environ.get("CLINE"):
            return "cline"
        return os.environ.get("TTA_AGENT_TOOL", "unknown")


try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
    from opentelemetry.trace import Status, StatusCode

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

from ..core.base import WorkflowContext, WorkflowPrimitive

_logger = logging.getLogger(__name__)


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
                    if span.context is None:
                        continue
                    span_dict = {
                        "trace_id": format(span.context.trace_id, "032x"),
                        "span_id": format(span.context.span_id, "016x"),
                        "name": span.name,
                        "start_time": span.start_time,
                        "end_time": span.end_time,
                        "duration_ns": (span.end_time - span.start_time)
                        if (span.end_time and span.start_time)
                        else 0,
                        # Agent identity — stable per process, used by the observability
                        # server to route this span to the correct session automatically.
                        "tta_agent_id": get_agent_id(),
                        "tta_agent_tool": get_agent_tool(),
                        "attributes": dict(span.attributes) if span.attributes else {},
                        "status": {
                            "status_code": span.status.status_code.name if span.status else "UNSET",
                            "description": span.status.description if span.status else "",
                        },
                        "parent_span_id": format(span.parent.span_id, "016x")
                        if span.parent
                        else None,
                    }
                    f.write(json.dumps(span_dict) + "\n")
            return SpanExportResult.SUCCESS
        except Exception as e:
            _logger.warning("Failed to export spans to file %s: %s", self.file_path, e)
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown exporter."""
        pass


def setup_tracing(service_name: str = "tta-workflow") -> None:
    """
    Setup OpenTelemetry tracing with file-based export and auto-instrumentation.

    Args:
        service_name: Name of the service for traces
    """
    if not TRACING_AVAILABLE:
        return

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": service_name,
            "tta.agent_id": get_agent_id(),
            "tta.agent_tool": get_agent_tool(),
        }
    )
    provider = TracerProvider(resource=resource)

    # Add file-based exporter
    file_exporter = FileSpanExporter()
    processor = BatchSpanProcessor(file_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    # Auto-instrument all primitives
    _auto_instrument_primitives()


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


def _auto_instrument_primitives() -> None:
    """Auto-instrument all WorkflowPrimitive subclasses with tracing."""
    if not TRACING_AVAILABLE:
        return

    import functools

    tracer = trace.get_tracer(__name__)
    original_execute = WorkflowPrimitive.execute

    @functools.wraps(original_execute)
    async def instrumented_execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Wrapped execute with automatic tracing."""
        primitive_name = self.__class__.__name__

        with tracer.start_as_current_span(
            primitive_name,
            attributes={
                "primitive.type": primitive_name,
                "workflow.id": context.workflow_id or "",
                "workflow.correlation_id": context.correlation_id or "",
            },
        ) as span:
            try:
                result = await original_execute(self, input_data, context)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    # Monkey-patch the base class
    WorkflowPrimitive.execute = instrumented_execute
