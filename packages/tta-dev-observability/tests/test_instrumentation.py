"""Tests for InstrumentedPrimitive."""

import pytest
from tta_dev_primitives.core.base import WorkflowContext

from tta_dev_observability.instrumentation.base import InstrumentedPrimitive

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False


class SamplePrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive for testing instrumentation."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Simple implementation that returns input plus success flag."""
        return {**input_data, "success": True}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Always raises an error."""
        raise ValueError("Intentional failure")


@pytest.mark.asyncio
async def test_instrumented_primitive_without_otel() -> None:
    """Test InstrumentedPrimitive works without OpenTelemetry."""
    primitive = SamplePrimitive(name="test-primitive")
    context = WorkflowContext(workflow_id="test")

    # Should execute successfully
    result = await primitive.execute({"input": "data"}, context)

    assert result == {"input": "data", "success": True}


@pytest.mark.asyncio
async def test_instrumented_primitive_default_name() -> None:
    """Test InstrumentedPrimitive uses class name by default."""
    primitive = SamplePrimitive()  # No name provided

    assert primitive.name == "SamplePrimitive"


@pytest.mark.asyncio
async def test_instrumented_primitive_custom_name() -> None:
    """Test InstrumentedPrimitive accepts custom name."""
    primitive = SamplePrimitive(name="custom-name")

    assert primitive.name == "custom-name"


@pytest.mark.asyncio
async def test_instrumented_primitive_error_handling() -> None:
    """Test InstrumentedPrimitive properly propagates errors."""
    primitive = FailingPrimitive(name="failing-primitive")
    context = WorkflowContext(workflow_id="test")

    # Should raise the error
    with pytest.raises(ValueError, match="Intentional failure"):
        await primitive.execute({"input": "data"}, context)


@pytest.mark.asyncio
async def test_not_implemented_error() -> None:
    """Test that InstrumentedPrimitive without _execute_impl raises NotImplementedError."""

    class IncompletePrimitive(InstrumentedPrimitive[dict, dict]):
        pass  # Doesn't implement _execute_impl

    primitive = IncompletePrimitive()
    context = WorkflowContext()

    with pytest.raises(NotImplementedError, match="must implement _execute_impl"):
        await primitive.execute({}, context)


@pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
@pytest.mark.asyncio
async def test_instrumented_primitive_with_otel() -> None:
    """Test InstrumentedPrimitive creates spans with OpenTelemetry."""
    # Setup fresh OpenTelemetry
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Execute primitive
    primitive = SamplePrimitive(name="test-primitive")
    primitive._tracer = provider.get_tracer(__name__)  # Use specific tracer
    context = WorkflowContext(workflow_id="test-wf")

    result = await primitive.execute({"input": "data"}, context)

    # Check result
    assert result == {"input": "data", "success": True}

    # Check spans were created
    spans = exporter.get_finished_spans()
    assert len(spans) > 0

    # Find our span
    our_span = None
    for span in spans:
        if span.name == "test-primitive.execute":
            our_span = span
            break

    assert our_span is not None
    assert our_span.attributes["primitive.name"] == "test-primitive"
    assert our_span.attributes["primitive.type"] == "SamplePrimitive"
    assert our_span.attributes["primitive.status"] == "success"
    assert "primitive.duration_ms" in our_span.attributes


@pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
@pytest.mark.asyncio
async def test_instrumented_primitive_error_recording() -> None:
    """Test InstrumentedPrimitive records errors in spans."""
    # Setup fresh OpenTelemetry
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Execute failing primitive
    primitive = FailingPrimitive(name="failing-primitive")
    primitive._tracer = provider.get_tracer(__name__)  # Use specific tracer
    context = WorkflowContext(workflow_id="test-wf")

    with pytest.raises(ValueError):
        await primitive.execute({"input": "data"}, context)

    # Check spans
    spans = exporter.get_finished_spans()
    assert len(spans) > 0

    # Find our span
    our_span = None
    for span in spans:
        if span.name == "failing-primitive.execute":
            our_span = span
            break

    assert our_span is not None
    assert our_span.attributes["primitive.status"] == "error"
    assert our_span.attributes["error.type"] == "ValueError"
    assert "error.message" in our_span.attributes

    # Check that exception was recorded
    assert len(our_span.events) > 0


@pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not installed")
@pytest.mark.asyncio
async def test_instrumented_primitive_context_injection() -> None:
    """Test InstrumentedPrimitive injects trace context."""
    # Setup fresh OpenTelemetry
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    tracer = provider.get_tracer(__name__)

    # Execute within a parent span
    with tracer.start_as_current_span("parent-span") as parent:
        primitive = SamplePrimitive(name="test-primitive")
        primitive._tracer = tracer  # Use same tracer
        context = WorkflowContext(workflow_id="test-wf")

        # Context should not have trace info yet
        assert context.trace_id is None

        await primitive.execute({"input": "data"}, context)

        # Context should now have trace info (injected by primitive)
        assert context.trace_id is not None
        assert context.span_id is not None

        # Verify trace_id matches parent
        parent_context = parent.get_span_context()
        expected_trace_id = format(parent_context.trace_id, "032x")
        assert context.trace_id == expected_trace_id


@pytest.mark.asyncio
async def test_context_correlation_id_preserved() -> None:
    """Test that correlation_id is preserved during execution."""
    primitive = SamplePrimitive(name="test-primitive")
    context = WorkflowContext(workflow_id="test")

    original_correlation_id = context.correlation_id

    await primitive.execute({"input": "data"}, context)

    # Correlation ID should be unchanged
    assert context.correlation_id == original_correlation_id
