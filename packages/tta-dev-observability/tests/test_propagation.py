"""Tests for trace context propagation."""

import pytest
from tta_dev_primitives.core.base import WorkflowContext

from tta_dev_observability.context.propagation import (
    extract_trace_context,
    inject_trace_context,
)

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False


@pytest.mark.asyncio
async def test_inject_trace_context_without_otel() -> None:
    """Test inject_trace_context gracefully handles missing OpenTelemetry."""
    context = WorkflowContext(workflow_id="test")

    # Should not fail even without OpenTelemetry
    result = inject_trace_context(context)

    # Context returned unchanged
    assert result is context


@pytest.mark.asyncio
async def test_extract_trace_context_without_otel() -> None:
    """Test extract_trace_context gracefully handles missing OpenTelemetry."""
    context = WorkflowContext(
        workflow_id="test",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
    )

    # Should return None without OpenTelemetry
    result = extract_trace_context(context)

    if not TRACING_AVAILABLE:
        assert result is None


@pytest.mark.asyncio
async def test_extract_trace_context_with_invalid_data() -> None:
    """Test extract_trace_context handles invalid trace data."""
    context = WorkflowContext(
        workflow_id="test",
        trace_id="invalid-hex",  # Invalid hex
        span_id="also-invalid",  # Invalid hex
    )

    # Should return None for invalid data
    result = extract_trace_context(context)
    assert result is None


@pytest.mark.asyncio
async def test_extract_trace_context_with_missing_fields() -> None:
    """Test extract_trace_context handles missing trace fields."""
    # Context without trace fields
    context = WorkflowContext(workflow_id="test")

    result = extract_trace_context(context)
    assert result is None

    # Context with only trace_id
    context = WorkflowContext(workflow_id="test", trace_id="0123456789abcdef0123456789abcdef")

    result = extract_trace_context(context)
    assert result is None

    # Context with only span_id
    context = WorkflowContext(workflow_id="test", span_id="0123456789abcdef")

    result = extract_trace_context(context)
    assert result is None


@pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
@pytest.mark.asyncio
async def test_inject_trace_context_with_otel() -> None:
    """Test inject_trace_context with OpenTelemetry available."""
    # Setup OpenTelemetry
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer(__name__)

    # Create a span and inject its context
    with tracer.start_as_current_span("test-span") as span:
        context = WorkflowContext(workflow_id="test")
        result = inject_trace_context(context)

        # Should have injected trace info
        assert result.trace_id is not None
        assert result.span_id is not None
        assert len(result.trace_id) == 32  # 128-bit trace ID as hex
        assert len(result.span_id) == 16  # 64-bit span ID as hex

        # Verify the trace_id matches the span's trace_id
        span_context = span.get_span_context()
        expected_trace_id = format(span_context.trace_id, "032x")
        assert result.trace_id == expected_trace_id


@pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
@pytest.mark.asyncio
async def test_extract_trace_context_round_trip() -> None:
    """Test extract can parse what inject creates."""
    # Setup OpenTelemetry
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer(__name__)

    # Create a span, inject context, then extract it
    with tracer.start_as_current_span("test-span"):
        context = WorkflowContext(workflow_id="test")
        context = inject_trace_context(context)

        # Extract should work
        span_context = extract_trace_context(context)
        assert span_context is not None
        assert span_context.is_valid


@pytest.mark.asyncio
async def test_graceful_degradation() -> None:
    """Test that operations work without OpenTelemetry."""
    # Create context
    context = WorkflowContext(workflow_id="test")

    # Inject should not fail
    result = inject_trace_context(context)
    assert result is context

    # Extract should return None
    extracted = extract_trace_context(result)
    if not TRACING_AVAILABLE:
        assert extracted is None

    # Context should still be usable
    assert context.workflow_id == "test"
    assert context.correlation_id is not None
