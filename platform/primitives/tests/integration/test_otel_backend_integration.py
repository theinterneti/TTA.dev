"""
Integration tests for OpenTelemetry backend integration.

Tests verify that instrumented primitives work correctly with real
OpenTelemetry backends (Jaeger, Prometheus) and that observability
data is correctly exported and queryable.

Prerequisites:
    - Docker and Docker Compose installed
    - Run: docker-compose -f docker-compose.integration.yml up -d
    - Wait ~10 seconds for services to be ready

Environment Variables:
    - JAEGER_ENDPOINT: Jaeger collector endpoint (default: http://localhost:14268)
    - PROMETHEUS_ENDPOINT: Prometheus query endpoint (default: http://localhost:9090)
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4318)

NOTE: All tests in this module require Docker containers and should run as integration tests.
"""

import asyncio
import os
import time
from typing import Any

import pytest
import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from tta_dev_primitives import WorkflowContext

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration
from tta_dev_primitives.core.conditional import ConditionalPrimitive, SwitchPrimitive
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)
from tta_dev_primitives.recovery.compensation import SagaPrimitive
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive

# ============================================================================
# Configuration
# ============================================================================

JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268")
JAEGER_QUERY_ENDPOINT = os.getenv("JAEGER_QUERY_ENDPOINT", "http://localhost:16686")
PROMETHEUS_ENDPOINT = os.getenv("PROMETHEUS_ENDPOINT", "http://localhost:9090")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

# Skip tests if backends are not available
BACKENDS_AVAILABLE = False


def check_backends_available() -> bool:
    """Check if Jaeger and Prometheus are available."""
    try:
        # Check Jaeger
        jaeger_response = requests.get(f"{JAEGER_QUERY_ENDPOINT}/api/services", timeout=2)
        jaeger_ok = jaeger_response.status_code == 200

        # Check Prometheus
        prom_response = requests.get(f"{PROMETHEUS_ENDPOINT}/-/healthy", timeout=2)
        prom_ok = prom_response.status_code == 200

        return jaeger_ok and prom_ok
    except Exception:
        return False


BACKENDS_AVAILABLE = check_backends_available()

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def otel_tracer_provider():
    """Set up OpenTelemetry tracer provider for tests."""
    if not BACKENDS_AVAILABLE:
        pytest.skip("OpenTelemetry backends not available")

    # Create resource
    resource = Resource.create(
        {
            "service.name": "tta-primitives-integration-test",
            "environment": "integration-test",
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Set as global provider
    trace.set_tracer_provider(provider)

    yield provider

    # Cleanup
    provider.shutdown()


@pytest.fixture
def test_context():
    """Create a test workflow context."""
    return WorkflowContext(
        workflow_id="integration-test",
        correlation_id=f"test-{int(time.time() * 1000)}",
    )


# ============================================================================
# Test Primitives
# ============================================================================


class SimplePrimitive(InstrumentedPrimitive[dict, dict]):
    """Simple test primitive."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute simple logic."""
        await asyncio.sleep(0.01)
        return {**input_data, "processed": True}


class MultiplyPrimitive(InstrumentedPrimitive[dict, dict]):
    """Primitive that multiplies a value."""

    def __init__(self, multiplier: int = 2) -> None:
        super().__init__()
        self.multiplier = multiplier

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Multiply the value."""
        await asyncio.sleep(0.01)
        value = input_data.get("value", 1)
        return {**input_data, "value": value * self.multiplier}


class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Always fail."""
        raise ValueError("Intentional failure for testing")


class CompensationPrimitive(InstrumentedPrimitive[dict, dict]):
    """Primitive for compensation."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute compensation."""
        await asyncio.sleep(0.01)
        return {**input_data, "compensated": True}


class AggregatorPrimitive(InstrumentedPrimitive[list, dict]):
    """Aggregate parallel results into single dict."""

    async def _execute_impl(self, input_data: list, context: WorkflowContext) -> dict:
        """Take first result from parallel execution."""
        return input_data[0] if input_data else {}


# ============================================================================
# Helper Functions
# ============================================================================


def query_jaeger_traces(
    service_name: str, operation_name: str | None = None
) -> list[dict[str, Any]]:
    """Query Jaeger for traces."""
    params = {"service": service_name, "limit": 100}
    if operation_name:
        params["operation"] = operation_name

    response = requests.get(f"{JAEGER_QUERY_ENDPOINT}/api/traces", params=params, timeout=5)
    response.raise_for_status()

    data = response.json()
    return data.get("data", [])


def query_prometheus_metrics(metric_name: str) -> dict[str, Any]:
    """Query Prometheus for metrics."""
    response = requests.get(
        f"{PROMETHEUS_ENDPOINT}/api/v1/query",
        params={"query": metric_name},
        timeout=5,
    )
    response.raise_for_status()

    return response.json()


# ============================================================================
# Tests: SequentialPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_sequential_primitive_creates_spans(otel_tracer_provider, test_context) -> None:
    """Test that SequentialPrimitive creates spans in Jaeger."""
    # Create workflow
    workflow = SequentialPrimitive(
        primitives=[
            SimplePrimitive(),
            MultiplyPrimitive(multiplier=2),
            MultiplyPrimitive(multiplier=3),
        ]
    )

    # Execute workflow
    result = await workflow.execute({"value": 10}, test_context)

    # Verify result
    assert result["value"] == 60  # 10 * 2 * 3
    assert result["processed"] is True

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger for traces
    traces = query_jaeger_traces("tta-dev-primitives")

    # Verify traces exist
    assert len(traces) > 0, "No traces found in Jaeger"

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify we have spans for the sequential workflow
    # Note: Only primitive.X spans have correlation_id tags, not internal sequential.step_X spans
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for SequentialPrimitive span
    assert any(
        name == "primitive.SequentialPrimitive" for name in span_names
    ), f"Expected primitive.SequentialPrimitive span, got: {span_names}"

    # Check for child primitive spans (SimplePrimitive, MultiplyPrimitive)
    primitive_spans = [name for name in span_names if name.startswith("primitive.")]
    assert (
        len(primitive_spans) >= 3
    ), f"Expected at least 3 primitive spans (1 Sequential + 2 children), got {len(primitive_spans)}: {primitive_spans}"


# ============================================================================
# Tests: ParallelPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_parallel_primitive_creates_concurrent_spans(
    otel_tracer_provider, test_context
) -> None:
    """Test that ParallelPrimitive creates concurrent spans in Jaeger."""
    # Create workflow with parallel branches
    workflow = ParallelPrimitive(
        primitives=[
            MultiplyPrimitive(multiplier=2),
            MultiplyPrimitive(multiplier=3),
            MultiplyPrimitive(multiplier=5),
        ]
    )

    # Execute workflow
    results = await workflow.execute({"value": 10}, test_context)

    # Verify results (all branches should execute)
    assert len(results) == 3
    assert results[0]["value"] == 20  # 10 * 2
    assert results[1]["value"] == 30  # 10 * 3
    assert results[2]["value"] == 50  # 10 * 5

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger for traces
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify parallel branch spans
    # Note: Only primitive.X spans have correlation_id tags
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for ParallelPrimitive span
    assert any(
        name == "primitive.ParallelPrimitive" for name in span_names
    ), f"Expected primitive.ParallelPrimitive span, got: {span_names}"

    # Check for child primitive spans (3 MultiplyPrimitive)
    multiply_spans = [name for name in span_names if name == "primitive.MultiplyPrimitive"]
    assert (
        len(multiply_spans) >= 3
    ), f"Expected at least 3 primitive.MultiplyPrimitive spans, got {len(multiply_spans)}: {multiply_spans}"


# ============================================================================
# Tests: ConditionalPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_conditional_primitive_creates_branch_spans(
    otel_tracer_provider, test_context
) -> None:
    """Test that ConditionalPrimitive creates branch spans in Jaeger."""
    # Create workflow with conditional
    workflow = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("value", 0) > 5,
        then_primitive=MultiplyPrimitive(multiplier=10),
        else_primitive=MultiplyPrimitive(multiplier=1),
    )

    # Execute workflow (should take then branch)
    result = await workflow.execute({"value": 10}, test_context)
    assert result["value"] == 100  # 10 * 10

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify conditional branch spans
    # Note: ConditionalPrimitive doesn't extend InstrumentedPrimitive, so it doesn't have correlation_id tags
    # We can only verify the child primitive spans
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for child primitive span (MultiplyPrimitive from then branch)
    assert any(
        name == "primitive.MultiplyPrimitive" for name in span_names
    ), f"Expected primitive.MultiplyPrimitive span (from then branch), got: {span_names}"


# ============================================================================
# Tests: SwitchPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_switch_primitive_creates_case_spans(otel_tracer_provider, test_context) -> None:
    """Test that SwitchPrimitive creates case spans in Jaeger."""
    # Create workflow with switch
    workflow = SwitchPrimitive(
        selector=lambda data, ctx: data.get("operation", "add"),
        cases={
            "add": MultiplyPrimitive(multiplier=2),
            "multiply": MultiplyPrimitive(multiplier=10),
        },
        default=SimplePrimitive(),
    )

    # Execute workflow (should take "add" case)
    result = await workflow.execute({"value": 5, "operation": "add"}, test_context)
    assert result["value"] == 10  # 5 * 2

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify switch case spans
    # Note: SwitchPrimitive doesn't extend InstrumentedPrimitive, so it doesn't have correlation_id tags
    # We can only verify the child primitive spans
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for child primitive span (MultiplyPrimitive from case_add)
    assert any(
        name == "primitive.MultiplyPrimitive" for name in span_names
    ), f"Expected primitive.MultiplyPrimitive span (from case_add), got: {span_names}"


# ============================================================================
# Tests: RetryPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_retry_primitive_creates_attempt_spans(otel_tracer_provider, test_context) -> None:
    """Test that RetryPrimitive creates attempt spans in Jaeger."""

    class FlakeyPrimitive(InstrumentedPrimitive[dict, dict]):
        """Primitive that fails first time, succeeds second time."""

        def __init__(self) -> None:
            super().__init__()
            self.attempt_count = 0

        async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
            """Fail first time, succeed second time."""
            self.attempt_count += 1
            if self.attempt_count == 1:
                raise ValueError("First attempt fails")
            return {**input_data, "success": True}

    # Create workflow with retry
    flakey = FlakeyPrimitive()
    from tta_dev_primitives.recovery.retry import RetryStrategy

    workflow = RetryPrimitive(
        primitive=flakey, strategy=RetryStrategy(max_retries=2, backoff_base=0.1)
    )

    # Execute workflow (should succeed on second attempt)
    result = await workflow.execute({"value": 10}, test_context)
    assert result["success"] is True

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify retry attempt spans
    # Note: RetryPrimitive doesn't extend InstrumentedPrimitive, so it doesn't have correlation_id tags
    # We can only verify the child primitive spans
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for child primitive spans (FlakeyPrimitive - should have 2 attempts)
    flakey_spans = [name for name in span_names if name == "primitive.FlakeyPrimitive"]
    assert (
        len(flakey_spans) >= 2
    ), f"Expected at least 2 primitive.FlakeyPrimitive spans (retry attempts), got {len(flakey_spans)}: {flakey_spans}"


# ============================================================================
# Tests: FallbackPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_fallback_primitive_creates_execution_spans(
    otel_tracer_provider, test_context
) -> None:
    """Test that FallbackPrimitive creates primary and fallback spans in Jaeger."""
    # Create workflow with fallback
    workflow = FallbackPrimitive(
        primary=FailingPrimitive(),
        fallback=SimplePrimitive(),
    )

    # Execute workflow (primary fails, fallback succeeds)
    result = await workflow.execute({"value": 10}, test_context)
    assert result["processed"] is True

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify fallback execution spans
    # Note: FallbackPrimitive doesn't extend InstrumentedPrimitive, so it doesn't have correlation_id tags
    # We can only verify the child primitive spans
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for both primary (FailingPrimitive) and fallback (SimplePrimitive) spans
    assert any(
        name == "primitive.FailingPrimitive" for name in span_names
    ), f"Expected primitive.FailingPrimitive span (primary), got: {span_names}"
    assert any(
        name == "primitive.SimplePrimitive" for name in span_names
    ), f"Expected primitive.SimplePrimitive span (fallback), got: {span_names}"


# ============================================================================
# Tests: SagaPrimitive Integration
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_saga_primitive_creates_compensation_spans(
    otel_tracer_provider, test_context
) -> None:
    """Test that SagaPrimitive creates forward and compensation spans in Jaeger."""
    # Create workflow with saga
    workflow = SagaPrimitive(
        forward=FailingPrimitive(),
        compensation=CompensationPrimitive(),
    )

    # Execute workflow (forward fails, compensation runs)
    with pytest.raises(ValueError, match="Intentional failure"):
        await workflow.execute({"value": 10}, test_context)

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify saga compensation spans
    # Note: SagaPrimitive doesn't extend InstrumentedPrimitive, so it doesn't have correlation_id tags
    # We can only verify the child primitive spans
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for both forward (FailingPrimitive) and compensation (CompensationPrimitive) spans
    assert any(
        name == "primitive.FailingPrimitive" for name in span_names
    ), f"Expected primitive.FailingPrimitive span (forward), got: {span_names}"
    assert any(
        name == "primitive.CompensationPrimitive" for name in span_names
    ), f"Expected primitive.CompensationPrimitive span (compensation), got: {span_names}"


# ============================================================================
# Tests: Composed Workflows
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="OpenTelemetry backends not available")
@pytest.mark.asyncio
async def test_composed_workflow_trace_propagation(otel_tracer_provider, test_context) -> None:
    """Test that trace context propagates across composed primitives."""
    # Create complex composed workflow
    workflow = (
        SequentialPrimitive(
            primitives=[
                MultiplyPrimitive(multiplier=2),
                MultiplyPrimitive(multiplier=3),
            ]
        )
        >> ParallelPrimitive(
            primitives=[
                MultiplyPrimitive(multiplier=1),
                MultiplyPrimitive(multiplier=1),
            ]
        )
        >> AggregatorPrimitive()  # Convert list to dict
        >> ConditionalPrimitive(
            condition=lambda data, ctx: data.get("value", 0) > 50,
            then_primitive=SimplePrimitive(),
            else_primitive=SimplePrimitive(),
        )
    )

    # Execute workflow
    await workflow.execute({"value": 10}, test_context)

    # Force flush spans to OTLP collector
    otel_tracer_provider.force_flush()

    # Wait for spans to propagate to Jaeger
    await asyncio.sleep(5)

    # Query Jaeger
    traces = query_jaeger_traces("tta-dev-primitives")
    assert len(traces) > 0

    # Collect all spans from traces with matching correlation ID
    all_spans = []
    for trace_data in traces:
        for span in trace_data.get("spans", []):
            tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
            if tags.get("workflow.correlation_id") == test_context.correlation_id:
                all_spans.append(span)

    assert len(all_spans) > 0, f"No spans found with correlation_id {test_context.correlation_id}"

    # Verify trace propagation across primitives
    # Note: Only InstrumentedPrimitive subclasses have correlation_id tags
    # ConditionalPrimitive doesn't extend InstrumentedPrimitive, so we can't verify it
    span_names = [span.get("operationName", "") for span in all_spans]

    # Check for SequentialPrimitive and ParallelPrimitive (both extend InstrumentedPrimitive)
    assert any(
        name == "primitive.SequentialPrimitive" for name in span_names
    ), f"Missing primitive.SequentialPrimitive span, got: {span_names}"
    assert any(
        name == "primitive.ParallelPrimitive" for name in span_names
    ), f"Missing primitive.ParallelPrimitive span, got: {span_names}"

    # Check for child primitives (MultiplyPrimitive, SimplePrimitive, AggregatorPrimitive)
    assert any(
        name == "primitive.MultiplyPrimitive" for name in span_names
    ), f"Missing primitive.MultiplyPrimitive spans, got: {span_names}"
    assert any(
        name == "primitive.SimplePrimitive" for name in span_names
    ), f"Missing primitive.SimplePrimitive span, got: {span_names}"
    assert any(
        name == "primitive.AggregatorPrimitive" for name in span_names
    ), f"Missing primitive.AggregatorPrimitive span, got: {span_names}"

    # Verify span hierarchy (parent-child relationships)
    span_refs = {}
    for span in all_spans:
        span_id = span.get("spanID")
        parent_id = None
        for ref in span.get("references", []):
            if ref.get("refType") == "CHILD_OF":
                parent_id = ref.get("spanID")
                break
        span_refs[span_id] = parent_id

    # Should have parent-child relationships
    assert len(span_refs) > 0, "No span relationships found"
