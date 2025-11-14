"""Integration test for observability trace propagation.

This test validates that trace context propagates correctly through
the observability infrastructure.
"""

import pytest

# Try to import observability components
try:
    from observability_integration import initialize_observability, is_observability_enabled
    from observability_integration.apm_setup import get_tracer, get_meter
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    pytest.skip("Observability integration not available", allow_module_level=True)


@pytest.fixture(scope="module", autouse=True)
def setup_observability():
    """Initialize observability for all tests in this module."""
    if OBSERVABILITY_AVAILABLE:
        success = initialize_observability(
            service_name="tta-integration-test",
            enable_console_traces=True,
            enable_prometheus=False  # Don't need Prometheus for this test
        )
        assert success, "Failed to initialize observability"
        yield
    else:
        yield


@pytest.mark.integration
def test_observability_initialization():
    """Test that observability initializes correctly."""
    assert is_observability_enabled(), "Observability should be enabled"


@pytest.mark.integration
def test_tracer_availability():
    """Test that tracer is available after initialization."""
    tracer = get_tracer(__name__)
    assert tracer is not None, "Tracer should be available"


@pytest.mark.integration
def test_meter_availability():
    """Test that meter is available after initialization."""
    meter = get_meter(__name__)
    assert meter is not None, "Meter should be available"


@pytest.mark.integration
def test_trace_context_creation():
    """Test that trace context can be created."""
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("test_span") as span:
        # Get span context
        span_context = span.get_span_context()
        
        # Validate trace ID exists
        assert span_context.trace_id > 0, "Trace ID should be set"
        assert span_context.span_id > 0, "Span ID should be set"
        
        # Test nested span
        with tracer.start_as_current_span("nested_span") as nested_span:
            nested_context = nested_span.get_span_context()
            
            # Should share same trace ID
            assert nested_context.trace_id == span_context.trace_id, \
                "Nested span should share trace ID"
            
            # Should have different span ID
            assert nested_context.span_id != span_context.span_id, \
                "Nested span should have different span ID"


@pytest.mark.integration
def test_metrics_creation():
    """Test that metrics can be created and used."""
    meter = get_meter(__name__)
    
    # Create a counter
    counter = meter.create_counter(
        "test_counter",
        description="Test counter for integration test"
    )
    
    # Add some counts
    counter.add(1, {"test": "integration"})
    counter.add(5, {"test": "integration"})
    
    # No exception means success


@pytest.mark.integration
def test_trace_attributes():
    """Test that trace attributes can be set."""
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("test_attributes") as span:
        # Set attributes
        span.set_attribute("test.attribute", "value")
        span.set_attribute("test.number", 42)
        span.set_attribute("test.boolean", True)
        
        # No exception means success


@pytest.mark.integration
def test_multiple_tracers():
    """Test that multiple tracers can coexist."""
    tracer1 = get_tracer("test_module_1")
    tracer2 = get_tracer("test_module_2")
    
    assert tracer1 is not None
    assert tracer2 is not None
    
    # Create spans from different tracers
    with tracer1.start_as_current_span("span1"):
        with tracer2.start_as_current_span("span2"):
            pass  # Just verify no errors


@pytest.mark.integration
def test_error_recording():
    """Test that errors can be recorded in spans."""
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("test_error") as span:
        try:
            # Simulate an error
            raise ValueError("Test error for observability")
        except ValueError as e:
            # Record the exception
            span.record_exception(e)
            # Don't re-raise in test
    
    # No exception means success
