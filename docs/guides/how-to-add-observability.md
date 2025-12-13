# How to Add Observability to Workflows

**Complete guide for instrumenting TTA.dev workflows with tracing, metrics, and logging**

---

## Overview

This guide shows you how to add comprehensive observability to your workflows using:
- OpenTelemetry distributed tracing
- Prometheus metrics
- Structured logging
- Context propagation

**Benefits:**
- Debug production issues faster
- Monitor performance trends
- Track costs and usage
- Understand workflow behavior

---

## Quick Start (5 minutes)

### Step 1: Initialize Observability

```python
from observability_integration import initialize_observability

# Initialize once at application startup
success = initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    prometheus_port=9464
)

if success:
    print("✅ Observability initialized")
else:
    print("⚠️ Running without observability")
```

### Step 2: Use Enhanced Primitives

```python
from observability_integration.primitives import (
    RouterPrimitive,
    CachePrimitive,
    TimeoutPrimitive
)

# These primitives have automatic observability
workflow = (
    CachePrimitive(expensive_op, ttl=3600) >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    TimeoutPrimitive(api_call, timeout=30)
)
```

### Step 3: Execute with Context

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-12345",
    metadata={"user_id": "user-789"}
)

result = await workflow.execute(input_data, context)
```

**That's it!** You now have:
- ✅ Distributed tracing
- ✅ Prometheus metrics on `:9464/metrics`
- ✅ Structured logging
- ✅ Context propagation

---

## Deep Dive: Observability Components

### Component 1: Distributed Tracing

#### What You Get

Every primitive execution creates OpenTelemetry spans:

```text
root_span: workflow_execution
├── span: cache_primitive.execute
│   └── span: cache_primitive.lookup
├── span: router_primitive.execute
│   ├── span: router_primitive.route_selection
│   └── span: llm1.execute
└── span: timeout_primitive.execute
```

#### How to Use

```python
from opentelemetry import trace

# Get tracer
tracer = trace.get_tracer(__name__)

# Create custom spans
async def my_operation():
    with tracer.start_as_current_span("my_operation") as span:
        # Add attributes
        span.set_attribute("input_size", len(data))

        # Do work
        result = await process(data)

        # Add events
        span.add_event("processing_complete")

        # Record metrics
        span.set_attribute("output_size", len(result))

        return result
```

#### View Traces

If you have a tracing backend (Jaeger, Zipkin):

```bash
# Export to Jaeger
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Restart application
# View at http://localhost:16686
```

---

### Component 2: Prometheus Metrics

#### What You Get

Automatic metrics for all primitives:

```promql
# Execution duration
primitive_execution_duration_seconds{primitive_name="cache"}

# Success/failure counts
primitive_execution_total{primitive_name="router", status="success"}
primitive_execution_total{primitive_name="router", status="error"}

# Cache metrics
cache_hits_total{primitive_name="cache"}
cache_misses_total{primitive_name="cache"}
cache_size{primitive_name="cache"}

# Router metrics
router_route_selected_total{primitive_name="router", route="fast"}
router_route_selected_total{primitive_name="router", route="quality"}
```

#### How to Query

```bash
# Start Prometheus (if not already running)
docker run -p 9090:9090 prom/prometheus

# Configure to scrape your app
# prometheus.yml:
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['localhost:9464']

# View metrics at http://localhost:9090
```

#### Example Queries

```promql
# Average execution time by primitive
rate(primitive_execution_duration_seconds_sum[5m])
/ rate(primitive_execution_duration_seconds_count[5m])

# Error rate
rate(primitive_execution_total{status="error"}[5m])

# Cache hit rate
rate(cache_hits_total[5m])
/ (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

---

### Component 3: Structured Logging

#### What You Get

All primitives log execution details:

```json
{
  "timestamp": "2025-10-31T10:30:00Z",
  "level": "INFO",
  "logger": "tta_dev_primitives.cache",
  "message": "Cache hit",
  "correlation_id": "req-12345",
  "primitive_name": "cache",
  "cache_key": "hash_abc123",
  "ttl_remaining": 2400
}
```

#### How to Configure

```python
import logging
import structlog

# Configure structlog (already done in initialize_observability)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# Use in your code
logger = structlog.get_logger(__name__)

logger.info(
    "operation_complete",
    operation="process_data",
    duration_ms=123.45,
    status="success",
    correlation_id=context.correlation_id
)
```

---

### Component 4: Context Propagation

#### What is WorkflowContext?

`WorkflowContext` carries state and correlation IDs through your workflow:

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-12345",  # Unique request ID
    metadata={
        "user_id": "user-789",
        "request_type": "analysis",
        "priority": "high"
    }
)
```

#### Benefits

- **Trace requests** across services
- **Filter logs** by correlation ID
- **Debug issues** by following single request
- **Aggregate metrics** by user/type

#### How It Works

```python
# Context is passed through entire workflow
workflow = step1 >> step2 >> step3

# Each primitive receives the same context
result = await workflow.execute(input_data, context)

# All spans share the same trace_id
# All logs include the correlation_id
```

---

## Advanced Patterns

### Pattern 1: Custom Primitive with Observability

```python
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives import WorkflowContext

class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    """Custom primitive with automatic observability."""

    def __init__(self):
        super().__init__(name="my_primitive")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Span is automatically created

        # Add custom attributes
        context.add_attribute("custom_metric", value)

        # Add events
        context.add_event("processing_started")

        # Your logic
        result = await self._process(input_data)

        # More attributes
        context.add_attribute("result_size", len(result))

        return result
```

### Pattern 2: Wrapping External Functions

```python
from observability_integration.primitives import ObservablePrimitive

# Wrap existing function with observability
observable_llm = ObservablePrimitive(
    primitive=external_llm_call,
    name="external_llm"
)

# Now has tracing, metrics, logging
result = await observable_llm.execute(input_data, context)
```

### Pattern 3: Custom Metrics

```python
from tta_dev_primitives.observability import PrimitiveMetrics

class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    def __init__(self):
        super().__init__(name="my_primitive")
        self.metrics = PrimitiveMetrics(primitive_name="my_primitive")

    async def _execute_impl(self, input_data, context):
        # Record custom counter
        self.metrics.record_custom_metric("items_processed", count)

        # Record custom histogram
        self.metrics.record_custom_metric("processing_time", duration)

        return result
```

### Pattern 4: Conditional Observability

```python
class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    def __init__(self, enable_detailed_tracing: bool = False):
        super().__init__(name="my_primitive")
        self.detailed_tracing = enable_detailed_tracing

    async def _execute_impl(self, input_data, context):
        if self.detailed_tracing:
            context.add_event("detailed_step_1")
            context.add_attribute("intermediate_result", value)

        result = await self._process(input_data)
        return result
```

---

## Grafana Dashboard Setup

### Step 1: Run Prometheus + Grafana

```bash
# Use docker-compose
cd TTA.dev
docker-compose -f docker-compose.test.yml up -d

# Access:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Step 2: Add Prometheus Data Source

1. Grafana → Configuration → Data Sources
2. Add Prometheus
3. URL: `http://prometheus:9090`
4. Save & Test

### Step 3: Import Dashboard

Create dashboard with these panels:

#### Panel: Request Rate

```promql
sum(rate(primitive_execution_total[5m])) by (primitive_name)
```

#### Panel: Error Rate

```promql
sum(rate(primitive_execution_total{status="error"}[5m])) by (primitive_name)
/ sum(rate(primitive_execution_total[5m])) by (primitive_name)
```

#### Panel: Average Latency

```promql
histogram_quantile(0.95,
  rate(primitive_execution_duration_seconds_bucket[5m])
) by (primitive_name)
```

#### Panel: Cache Hit Rate

```promql
rate(cache_hits_total[5m])
/ (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

---

## Troubleshooting Observability

### Issue: No metrics appearing

**Diagnosis:**

```bash
# Check if metrics endpoint is accessible
curl http://localhost:9464/metrics

# Should see Prometheus format output
```

**Solutions:**

1. Verify `initialize_observability(enable_prometheus=True)`
2. Check port not in use: `lsof -i :9464`
3. Restart application

### Issue: Traces not showing up

**Diagnosis:**

```python
from opentelemetry import trace

# Check if tracing is configured
tracer = trace.get_tracer(__name__)
print(tracer)  # Should not be NoOpTracer
```

**Solutions:**

1. Verify OTEL environment variables set
2. Check exporter endpoint reachable
3. Review application logs for OTEL errors

### Issue: Logs missing correlation IDs

**Diagnosis:**

```python
# Verify context is passed
context = WorkflowContext(correlation_id="test-123")
result = await workflow.execute(data, context)

# Check logs for correlation_id field
```

**Solutions:**

1. Ensure `WorkflowContext` is created with `correlation_id`
2. Verify structlog configuration
3. Check logger is using structlog

---

## Best Practices

### DO ✅

1. **Always create WorkflowContext**
   ```python
   context = WorkflowContext(correlation_id=generate_id())
   ```

2. **Use enhanced primitives**
   ```python
   from observability_integration.primitives import CachePrimitive
   ```

3. **Add meaningful attributes**
   ```python
   context.add_attribute("user_id", user_id)
   context.add_attribute("model_used", model_name)
   ```

4. **Log important events**
   ```python
   logger.info("cache_miss", key=cache_key)
   ```

5. **Monitor metrics in Grafana**
   - Set up alerts for error rates
   - Track latency trends
   - Monitor cache efficiency

### DON'T ❌

1. **Don't skip context creation**
   ```python
   # Bad
   result = await workflow.execute(data, None)
   ```

2. **Don't ignore errors silently**
   ```python
   # Bad
   try:
       result = await workflow.execute(data, context)
   except Exception:
       pass  # No logging!
   ```

3. **Don't log sensitive data**
   ```python
   # Bad
   logger.info("user_data", password=user_password)
   ```

4. **Don't create too many custom spans**
   ```python
   # Bad - span per loop iteration
   for item in items:
       with tracer.start_as_current_span(f"process_{item}"):
           ...
   ```

---

## Testing Observability

### Test Traces

```python
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter
)

@pytest.fixture
def span_exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(
        SimpleSpanProcessor(exporter)
    )
    trace.set_tracer_provider(provider)
    return exporter

@pytest.mark.asyncio
async def test_primitive_creates_span(span_exporter):
    primitive = MyPrimitive()
    context = WorkflowContext(correlation_id="test")

    await primitive.execute({"test": "data"}, context)

    spans = span_exporter.get_finished_spans()
    assert len(spans) > 0
    assert spans[0].name == "my_primitive.execute"
```

### Test Metrics

```python
from prometheus_client import REGISTRY

@pytest.mark.asyncio
async def test_primitive_records_metrics():
    primitive = MyPrimitive()
    context = WorkflowContext(correlation_id="test")

    await primitive.execute({"test": "data"}, context)

    # Check metric exists
    metrics = REGISTRY.collect()
    metric_names = [m.name for m in metrics]
    assert "primitive_execution_duration_seconds" in metric_names
```

---

## Checklist

Before deploying to production:

- [ ] `initialize_observability()` called at startup
- [ ] Using enhanced primitives from `observability_integration`
- [ ] All workflows create `WorkflowContext` with correlation IDs
- [ ] Prometheus scraping configured
- [ ] Grafana dashboards created
- [ ] Alerts configured for error rates
- [ ] Log aggregation configured (if using)
- [ ] Traces exported to backend (if using)
- [ ] Observability tested in staging
- [ ] Documentation updated

---

## Related Pages

- [[TTA Observability]]
- [[tta-observability-integration]]
- [[How to Create a New Primitive]]
- [[PRIMITIVES_CATALOG]]

---

**Last Updated:** [[2025-10-31]]
**Difficulty:** Intermediate
**Time:** 1-2 hours


---
**Logseq:** [[TTA.dev/Docs/Guides/How-to-add-observability]]
