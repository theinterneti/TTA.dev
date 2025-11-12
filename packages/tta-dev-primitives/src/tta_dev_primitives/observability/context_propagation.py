"""W3C Trace Context propagation for WorkflowContext."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

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


@contextmanager
def create_linked_span(
    tracer: trace.Tracer, name: str, context: WorkflowContext, **kwargs
) -> Generator[trace.Span, None, None]:
    """
    Create a span linked to the ACTIVE OpenTelemetry context.

    This function uses start_as_current_span() to automatically link to the
    active context, ensuring proper parent-child relationships in distributed
    traces. The previous implementation using NonRecordingSpan caused broken
    span linking.

    Args:
        tracer: OpenTelemetry tracer
        name: Span name
        context: WorkflowContext to update with span information
        **kwargs: Additional span creation arguments (attributes, links, etc.)

    Yields:
        Active span with proper parent linkage

    Example:
        ```python
        with create_linked_span(tracer, "my_operation", context) as span:
            span.set_attribute("operation.type", "processing")
            result = await do_work()
            span.set_attribute("result.size", len(result))
        # Span automatically closes with proper parent-child relationship
        ```
    """
    # Use start_as_current_span to automatically link to active context
    # This ensures proper parent-child relationships in the trace tree
    with tracer.start_as_current_span(name, **kwargs) as span:
        # Update WorkflowContext with span info for logging/debugging
        span_ctx = span.get_span_context()
        context.span_id = format(span_ctx.span_id, "016x")
        context.trace_id = format(span_ctx.trace_id, "032x")
        context.trace_flags = span_ctx.trace_flags.sampled

        yield span


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
        from opentelemetry.baggage import (
            get_all_baggage,  # type: ignore[attr-defined]  # May not be in all OTel versions
        )

        baggage = get_all_baggage()
        if baggage:
            context.baggage.update(baggage)
    except ImportError:
        logger.debug("Baggage extraction not available")
