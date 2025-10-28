"""W3C Trace Context propagation for WorkflowContext."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.base import WorkflowContext

try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanContext, TraceFlags

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    # When OpenTelemetry is unavailable, graceful degradation occurs:
    # - inject_trace_context() returns context unchanged
    # - extract_trace_context() returns None
    # - create_linked_span() creates spans without parent linkage

logger = logging.getLogger(__name__)


def inject_trace_context(context: WorkflowContext) -> WorkflowContext:
    """
    Inject current OpenTelemetry trace context into WorkflowContext.

    Args:
        context: WorkflowContext to inject trace info into

    Returns:
        Updated context with trace information

    Example:
        ```python
        from tta_dev_primitives.core.base import WorkflowContext

        # At workflow entry point (e.g., HTTP handler)
        context = WorkflowContext(workflow_id="process-123")
        context = inject_trace_context(context)  # Injects current span info

        # Now context.trace_id and context.span_id are populated
        result = await workflow.execute(data, context)
        ```
    """
    if not TRACING_AVAILABLE:
        return context

    current_span = trace.get_current_span()
    if not current_span or not current_span.is_recording():
        return context

    span_context = current_span.get_span_context()
    if not span_context.is_valid:
        return context

    # Update context with trace information
    context.trace_id = format(span_context.trace_id, "032x")
    context.span_id = format(span_context.span_id, "016x")
    context.trace_flags = span_context.trace_flags.sampled

    return context


def extract_trace_context(context: WorkflowContext) -> SpanContext | None:
    """
    Extract OpenTelemetry SpanContext from WorkflowContext.

    Args:
        context: WorkflowContext with trace information

    Returns:
        SpanContext if valid trace info present, None otherwise
    """
    if not TRACING_AVAILABLE:
        return None

    if not context.trace_id or not context.span_id:
        return None

    try:
        trace_id = int(context.trace_id, 16)
        span_id = int(context.span_id, 16)
        trace_flags = TraceFlags(context.trace_flags)

        return SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            is_remote=True,
            trace_flags=trace_flags,
        )
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to extract trace context: {e}")
        return None


def create_linked_span(
    tracer: trace.Tracer, name: str, context: WorkflowContext, **kwargs
) -> trace.Span:
    """
    Create a span linked to the trace context in WorkflowContext.

    Args:
        tracer: OpenTelemetry tracer
        name: Span name
        context: WorkflowContext with trace information
        **kwargs: Additional span creation arguments

    Returns:
        New span linked to parent context
    """
    parent_context = extract_trace_context(context)

    if parent_context:
        # Create span with explicit parent
        span = tracer.start_span(
            name,
            context=trace.set_span_in_context(trace.NonRecordingSpan(parent_context)),
            **kwargs,
        )
    else:
        # Create new root span
        span = tracer.start_span(name, **kwargs)

    # Update WorkflowContext with new span info
    span_context = span.get_span_context()
    context.span_id = format(span_context.span_id, "016x")
    if not context.trace_id:
        context.trace_id = format(span_context.trace_id, "032x")

    return span


def propagate_baggage(context: WorkflowContext) -> None:
    """
    Propagate W3C Baggage from WorkflowContext to OpenTelemetry context.

    Args:
        context: WorkflowContext with baggage to propagate
    """
    if not TRACING_AVAILABLE or not context.baggage:
        return

    try:
        from opentelemetry.baggage import set_baggage

        for key, value in context.baggage.items():
            set_baggage(key, value)
    except ImportError:
        logger.debug("Baggage propagation not available")


def extract_baggage(context: WorkflowContext) -> None:
    """
    Extract W3C Baggage from OpenTelemetry context into WorkflowContext.

    Args:
        context: WorkflowContext to populate with baggage
    """
    if not TRACING_AVAILABLE:
        return

    try:
        from opentelemetry.baggage import get_all_baggage

        baggage = get_all_baggage()
        if baggage:
            context.baggage.update(baggage)
    except ImportError:
        logger.debug("Baggage extraction not available")

