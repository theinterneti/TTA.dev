# Observability Integration

**Category:** Monitoring & Tracing
**Status:** Production Ready
**Version:** 2.0.0
**Last Updated:** 2024-03-19

---

## Overview

The TTA Observability Integration provides comprehensive monitoring, tracing, and metrics collection for TTA.dev applications. Built on OpenTelemetry standards, it enables end-to-end visibility into workflow execution, performance analysis, and error tracking.

### Key Features

- **Distributed Tracing** - OpenTelemetry-based span tracking across workflows
- **Metrics Collection** - Prometheus-compatible metrics export
- **Structured Logging** - JSON-formatted logs with correlation IDs
- **Context Propagation** - Automatic correlation across distributed systems
- **Performance Monitoring** - Execution time, throughput, error rate tracking

### Use Cases

1. **Workflow Debugging** - Trace execution paths through complex workflows
2. **Performance Analysis** - Identify bottlenecks and slow operations
3. **Error Tracking** - Monitor failure rates and error patterns
4. **Cost Optimization** - Track LLM API usage and costs
5. **SLA Monitoring** - Track response times and availability

---

## Architecture

### Two-Package Design

TTA.dev uses a two-package architecture for observability:

1. **Core Observability** (`tta-dev-primitives/observability/`)
   - `InstrumentedPrimitive` - Base class with automatic tracing
   - `ObservablePrimitive` - Wrapper for adding observability
   - `PrimitiveMetrics` - Built-in metrics collection
   - Integrated into all primitives by default

2. **Enhanced Integration** (`tta-observability-integration/`)
   - `initialize_observability()` - Setup function
   - Enhanced primitives with additional metrics
   - Prometheus metrics server (port 9464)
   - OpenTelemetry exporter configuration

### System Components

```text
┌──────────────────────────────────────────────────────────┐
│          TTA Observability Integration                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Tracing    │  │   Metrics    │  │    Logging     │  │
│  │             │  │              │  │                │  │
│  │ - Spans     │  │ - Counters   │  │ - Structured   │  │
│  │ - Baggage   │  │ - Gauges     │  │ - Correlated   │  │
│  │ - Context   │  │ - Histograms │  │ - JSON Format  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│         │                 │                    │         │
│         └─────────────────┴────────────────────┘         │
│                           │                              │
│                  ┌────────┴────────┐                     │
│                  │   Exporters     │                     │
│                  │                 │                     │
│                  │ - OTLP          │                     │
│                  │ - Prometheus    │                     │
│                  │ - Jaeger        │                     │
│                  └─────────────────┘                     │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
           ┌───────────────────────────────┐
           │     Monitoring Backends        │
           │                               │
           │  - Prometheus/Grafana         │
           │  - Jaeger                     │
           │  - Cloud Providers (AWS/GCP)  │
           └───────────────────────────────┘
```

### Data Flow

```text
Workflow Execution:
  Primitive.execute() →
  InstrumentedPrimitive (create span) →
  Execute business logic →
  Record metrics →
  Log events →
  Export to backends

Context Propagation:
  WorkflowContext →
  OpenTelemetry Context →
  HTTP Headers (trace-id, span-id) →
  Downstream Services →
  Correlated Traces
```

---

## Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Package Installation

```bash
# Add observability integration
uv add tta-observability-integration

# Or install from workspace
cd /home/thein/repos/TTA.dev
uv sync --all-extras
```

### Backend Services (Optional)

```bash
# Start Prometheus + Grafana
cd /home/thein/repos/TTA.dev
docker-compose -f docker-compose.test.yml up -d

# Access services
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# Jaeger: http://localhost:16686
```

---

## Configuration

### Basic Setup

```python
from observability_integration import initialize_observability

# Initialize observability
success = initialize_observability(
    service_name="my-tta-app",
    enable_prometheus=True,
    prometheus_port=9464,
)

if success:
    print("✅ Observability initialized")
else:
    print("⚠️  Observability initialization failed (graceful degradation)")
```

### Advanced Configuration

```python
from observability_integration import initialize_observability, ObservabilityConfig

config = ObservabilityConfig(
    # Service identification
    service_name="my-tta-app",
    service_version="1.0.0",
    environment="production",

    # OpenTelemetry
    otlp_endpoint="http://localhost:4317",  # Optional: OTLP exporter
    enable_console_exporter=False,  # Debug mode

    # Prometheus
    enable_prometheus=True,
    prometheus_port=9464,
    prometheus_endpoint="/metrics",

    # Tracing
    trace_sample_rate=1.0,  # 100% sampling
    trace_parent_based=True,

    # Logging
    log_level="INFO",
    structured_logging=True,
    log_correlation=True,

    # Performance
    batch_span_processor=True,
    max_export_batch_size=512,
    max_queue_size=2048,
)

success = initialize_observability(config=config)
```

### Environment Variables

```bash
# .env file
OTEL_SERVICE_NAME=my-tta-app
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_TRACES_SAMPLER=parentbased_always_on
OTEL_PYTHON_LOG_CORRELATION=true
PROMETHEUS_PORT=9464
```

---

## Usage Examples

### Basic Tracing

#### Automatic Tracing (Built-in)

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# All primitives have automatic tracing built-in
workflow = step1 >> step2 >> step3

# Execute with context
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

# Spans are created automatically
result = await workflow.execute(context, input_data)

# Trace is exported to configured backends
```

#### Manual Span Creation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def my_operation(context, data):
    # Create custom span
    with tracer.start_as_current_span("my_operation") as span:
        # Add attributes
        span.set_attribute("input_size", len(data))
        span.set_attribute("user_id", context.data.get("user_id"))

        # Do work
        result = await process_data(data)

        # Add events
        span.add_event("processing_complete")

        # Record result attributes
        span.set_attribute("output_size", len(result))

        return result
```

### Metrics Collection

#### Using Enhanced Primitives

```python
from observability_integration.primitives import (
    RouterPrimitive,
    CachePrimitive,
    TimeoutPrimitive
)

# Enhanced primitives automatically track metrics
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "quality": gpt4,
    },
    default_route="fast"
)

cache = CachePrimitive(
    primitive=expensive_operation,
    ttl_seconds=3600
)

# Metrics automatically exported:
# - router_route_selected{route="fast"}
# - cache_hit_total
# - cache_miss_total
# - operation_duration_seconds
```

#### Custom Metrics

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Create custom metrics
request_counter = meter.create_counter(
    "api_requests_total",
    description="Total API requests",
    unit="1"
)

response_time = meter.create_histogram(
    "api_response_time_seconds",
    description="API response time",
    unit="s"
)

# Record metrics
request_counter.add(1, {"endpoint": "/users", "method": "GET"})
response_time.record(0.123, {"endpoint": "/users"})
```

### Structured Logging

#### Basic Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Log with correlation
logger.info(
    "workflow_executed",
    workflow_name="user_onboarding",
    duration_ms=123.45,
    status="success",
    user_id="user-789"
)

# Automatic correlation with trace_id and span_id
# Output (JSON):
# {
#   "event": "workflow_executed",
#   "workflow_name": "user_onboarding",
#   "duration_ms": 123.45,
#   "status": "success",
#   "user_id": "user-789",
#   "trace_id": "a1b2c3d4e5f6...",
#   "span_id": "1234567890ab...",
#   "timestamp": "2024-03-19T10:30:00Z"
# }
```

#### Error Logging with Context

```python
import structlog
from opentelemetry import trace

logger = structlog.get_logger(__name__)

async def risky_operation(context, data):
    try:
        result = await process(data)
        return result
    except Exception as e:
        # Log error with full context
        logger.error(
            "operation_failed",
            error=str(e),
            error_type=type(e).__name__,
            user_id=context.data.get("user_id"),
            input_data=data,
            exc_info=True
        )

        # Record exception in span
        span = trace.get_current_span()
        span.record_exception(e)
        span.set_status(trace.Status(trace.StatusCode.ERROR))

        raise
```

### Context Propagation

#### WorkflowContext Integration

```python
from tta_dev_primitives import WorkflowContext

# Create context with correlation ID
context = WorkflowContext(
    correlation_id="req-abc-123",
    data={
        "user_id": "user-789",
        "session_id": "sess-456",
        "request_ip": "192.168.1.1"
    }
)

# Context automatically propagates:
# - correlation_id → logs
# - trace context → spans
# - custom data → available in all steps

result = await workflow.execute(context, input_data)
```

#### Cross-Service Propagation

```python
import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Instrument HTTP client
HTTPXClientInstrumentor().instrument()

async def call_downstream_service(context, data):
    async with httpx.AsyncClient() as client:
        # Trace context automatically injected in headers:
        # traceparent: 00-{trace_id}-{span_id}-01
        # tracestate: ...
        response = await client.post(
            "https://api.example.com/process",
            json=data
        )
        return response.json()
```

---

## Integration Patterns

### Pattern 1: Full-Stack Observability

```python
from observability_integration import initialize_observability
from observability_integration.primitives import RouterPrimitive, CachePrimitive
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
import structlog

# 1. Initialize observability
initialize_observability(
    service_name="user-service",
    enable_prometheus=True
)

logger = structlog.get_logger(__name__)

# 2. Build observable workflow
router = RouterPrimitive(
    routes={"fast": llm1, "quality": llm2},
    default_route="fast"
)

cache = CachePrimitive(
    primitive=router,
    ttl_seconds=3600
)

workflow = (
    input_validator >>
    cache >>
    output_formatter
)

# 3. Execute with full observability
async def handle_request(user_id: str, input_data: dict):
    context = WorkflowContext(
        correlation_id=f"req-{uuid.uuid4()}",
        data={"user_id": user_id}
    )

    logger.info("request_received", user_id=user_id)

    try:
        result = await workflow.execute(context, input_data)

        logger.info(
            "request_completed",
            user_id=user_id,
            status="success"
        )

        return result

    except Exception as e:
        logger.error(
            "request_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise

# Result: Full visibility
# - Traces show execution path
# - Metrics show cache hit rate, LLM usage
# - Logs show user journey with correlation
```

### Pattern 2: Performance Monitoring

```python
from observability_integration import initialize_observability
from opentelemetry import trace, metrics
import structlog

# Initialize
initialize_observability(service_name="perf-monitor")

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
logger = structlog.get_logger(__name__)

# Create metrics
operation_duration = meter.create_histogram(
    "operation_duration_seconds",
    description="Operation execution time",
    unit="s"
)

operation_errors = meter.create_counter(
    "operation_errors_total",
    description="Total operation errors",
    unit="1"
)

async def monitored_operation(context, data):
    start_time = time.time()

    with tracer.start_as_current_span("monitored_operation") as span:
        span.set_attribute("input_size", len(data))

        try:
            result = await expensive_operation(data)

            duration = time.time() - start_time
            operation_duration.record(duration, {"status": "success"})

            span.set_attribute("duration_ms", duration * 1000)
            span.set_attribute("output_size", len(result))

            logger.info(
                "operation_completed",
                duration_ms=duration * 1000,
                status="success"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            operation_duration.record(duration, {"status": "error"})
            operation_errors.add(1, {"error_type": type(e).__name__})

            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))

            logger.error(
                "operation_failed",
                duration_ms=duration * 1000,
                error=str(e),
                exc_info=True
            )

            raise

# Query Prometheus:
# rate(operation_duration_seconds_sum[5m])  # Throughput
# histogram_quantile(0.95, operation_duration_seconds_bucket)  # p95 latency
# rate(operation_errors_total[5m])  # Error rate
```

### Pattern 3: Cost Tracking

```python
from observability_integration import initialize_observability
from opentelemetry import metrics
import structlog

initialize_observability(service_name="cost-tracker")

meter = metrics.get_meter(__name__)
logger = structlog.get_logger(__name__)

# Cost tracking metrics
llm_requests = meter.create_counter(
    "llm_requests_total",
    description="Total LLM API requests",
    unit="1"
)

llm_tokens = meter.create_counter(
    "llm_tokens_total",
    description="Total LLM tokens used",
    unit="1"
)

llm_cost = meter.create_counter(
    "llm_cost_usd_total",
    description="Total LLM cost in USD",
    unit="USD"
)

async def tracked_llm_call(model: str, prompt: str):
    llm_requests.add(1, {"model": model})

    response = await llm_api.call(model=model, prompt=prompt)

    # Track usage
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = prompt_tokens + completion_tokens

    # Cost calculation (example rates)
    cost_per_1k = {
        "gpt-4": 0.03,
        "gpt-4-mini": 0.001,
        "gpt-3.5-turbo": 0.002,
    }

    cost = (total_tokens / 1000) * cost_per_1k.get(model, 0)

    # Record metrics
    llm_tokens.add(total_tokens, {
        "model": model,
        "token_type": "total"
    })
    llm_tokens.add(prompt_tokens, {
        "model": model,
        "token_type": "prompt"
    })
    llm_tokens.add(completion_tokens, {
        "model": model,
        "token_type": "completion"
    })
    llm_cost.add(cost, {"model": model})

    # Log
    logger.info(
        "llm_call_completed",
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost
    )

    return response

# Query Prometheus:
# sum(llm_cost_usd_total) by (model)  # Cost by model
# rate(llm_tokens_total[1h]) by (model)  # Token usage rate
# llm_cost_usd_total / llm_requests_total  # Cost per request
```

---

## Best Practices

### Tracing Best Practices

1. **Use Descriptive Span Names**

   ```python
   # ✅ Good - clear and hierarchical
   with tracer.start_as_current_span("workflow.user_onboarding.validate_email"):
       ...

   # ❌ Bad - vague
   with tracer.start_as_current_span("operation"):
       ...
   ```

2. **Add Meaningful Attributes**

   ```python
   span.set_attribute("user_id", user_id)
   span.set_attribute("workflow_name", "user_onboarding")
   span.set_attribute("step_index", 2)
   span.set_attribute("input_size_bytes", len(data))
   ```

3. **Record Events for Milestones**

   ```python
   span.add_event("validation_started")
   span.add_event("api_call_completed", {"status_code": 200})
   span.add_event("result_cached", {"cache_key": key})
   ```

4. **Handle Errors Properly**

   ```python
   try:
       result = await operation()
   except Exception as e:
       span.record_exception(e)
       span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
       raise
   ```

### Metrics Best Practices

1. **Choose the Right Metric Type**

   ```python
   # Counters - monotonically increasing
   requests_total = meter.create_counter("requests_total")

   # Gauges - current value (up or down)
   active_users = meter.create_up_down_counter("active_users")

   # Histograms - distributions
   response_time = meter.create_histogram("response_time_seconds")
   ```

2. **Use Consistent Labels**

   ```python
   # ✅ Good - consistent label names
   counter.add(1, {"method": "GET", "endpoint": "/users", "status": "200"})

   # ❌ Bad - inconsistent
   counter.add(1, {"http_method": "GET", "path": "/users", "code": "200"})
   ```

3. **Avoid High-Cardinality Labels**

   ```python
   # ❌ Bad - user_id has high cardinality
   counter.add(1, {"user_id": user_id})

   # ✅ Good - use aggregated labels
   counter.add(1, {"user_tier": "premium"})
   ```

### Logging Best Practices

1. **Use Structured Logging**

   ```python
   # ✅ Good - structured
   logger.info("user_registered", user_id=user_id, source="web")

   # ❌ Bad - unstructured
   logger.info(f"User {user_id} registered from web")
   ```

2. **Log at Appropriate Levels**

   ```python
   logger.debug("cache_lookup", key=key)  # Development
   logger.info("user_action", action="login")  # Normal events
   logger.warning("rate_limit_approaching", usage=0.85)  # Warnings
   logger.error("operation_failed", error=str(e))  # Errors
   logger.critical("service_unavailable", service="database")  # Critical
   ```

3. **Include Correlation IDs**

   ```python
   # Automatic with WorkflowContext
   logger.info(
       "request_processed",
       correlation_id=context.correlation_id,
       user_id=context.data["user_id"]
   )
   ```

---

## Troubleshooting

### Issue: Spans Not Exported

**Symptoms:**

```text
Workflow executes but no traces appear in Jaeger/backend
```

**Solution:**

```python
# 1. Check initialization
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="my-app",
    otlp_endpoint="http://localhost:4317",  # Verify endpoint
    enable_console_exporter=True  # Enable debug output
)

if not success:
    print("Observability initialization failed!")

# 2. Verify backend is running
# docker-compose -f docker-compose.test.yml ps

# 3. Check span processor
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("test"):
    print("Span created")
# Check console output if enable_console_exporter=True
```

### Issue: Metrics Not Appearing

**Symptoms:**

```text
Prometheus /metrics endpoint returns no data
```

**Solution:**

```python
# 1. Verify Prometheus server is running
import requests

response = requests.get("http://localhost:9464/metrics")
print(response.text)

# 2. Ensure metrics are being recorded
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
counter = meter.create_counter("test_counter")
counter.add(1)

# 3. Check Prometheus configuration
# scrape_configs:
#   - job_name: 'tta-app'
#     static_configs:
#       - targets: ['localhost:9464']
```

### Issue: Missing Correlation IDs

**Symptoms:**

```text
Logs don't have trace_id or span_id fields
```

**Solution:**

```python
# Enable log correlation
from observability_integration import initialize_observability

initialize_observability(
    service_name="my-app",
    config=ObservabilityConfig(
        log_correlation=True,
        structured_logging=True
    )
)

# Ensure using structlog
import structlog
logger = structlog.get_logger(__name__)

# Not standard logging
# import logging  # ❌ Won't have correlation
```

---

## API Reference

### Initialization

```python
def initialize_observability(
    service_name: str | None = None,
    service_version: str = "1.0.0",
    environment: str = "development",
    enable_prometheus: bool = True,
    prometheus_port: int = 9464,
    otlp_endpoint: str | None = None,
    config: ObservabilityConfig | None = None,
) -> bool:
    """
    Initialize observability for TTA.dev application.

    Returns:
        bool: True if initialization successful, False otherwise (graceful degradation)
    """
    ...
```

### Enhanced Primitives

```python
from observability_integration.primitives import (
    RouterPrimitive,
    CachePrimitive,
    TimeoutPrimitive,
)

# Same API as core primitives, with additional metrics
router = RouterPrimitive(routes={...})
cache = CachePrimitive(primitive=..., ttl_seconds=3600)
timeout = TimeoutPrimitive(primitive=..., timeout_seconds=30.0)
```

### Configuration

```python
@dataclass
class ObservabilityConfig:
    service_name: str
    service_version: str = "1.0.0"
    environment: str = "development"

    # OpenTelemetry
    otlp_endpoint: str | None = None
    enable_console_exporter: bool = False

    # Prometheus
    enable_prometheus: bool = True
    prometheus_port: int = 9464
    prometheus_endpoint: str = "/metrics"

    # Tracing
    trace_sample_rate: float = 1.0
    trace_parent_based: bool = True

    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True
    log_correlation: bool = True

    # Performance
    batch_span_processor: bool = True
    max_export_batch_size: int = 512
    max_queue_size: int = 2048
```

---

## Related Documentation

- **Package README:** [`packages/tta-observability-integration/README.md`](../../packages/tta-observability-integration/README.md)
- **Core Observability:** [`packages/tta-dev-primitives/src/tta_dev_primitives/observability/`](../../packages/tta-dev-primitives/src/tta_dev_primitives/observability/)
- **Architecture:** [`docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md`](../architecture/COMPONENT_INTEGRATION_ANALYSIS.md)
- **Monitoring Dashboard:** [`WEEK1_MONITORING_DASHBOARD.md`](../../WEEK1_MONITORING_DASHBOARD.md)

---

**Last Updated:** 2024-03-19
**Status:** Production Ready
**Maintainer:** TTA.dev Team
