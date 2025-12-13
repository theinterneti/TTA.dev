# TTA.dev Observability Architecture

**Component:** Observability System
**Version:** 2.0.0
**Last Updated:** October 30, 2025

---

## Overview

TTA.dev's observability architecture provides comprehensive monitoring, tracing, and metrics collection across all workflow primitives. Built on OpenTelemetry standards, it enables end-to-end visibility into workflow execution, performance analysis, and error tracking.

### Design Goals

1. **Automatic Instrumentation** - All primitives instrumented by default
2. **Minimal Overhead** - Observability adds <5ms per primitive execution
3. **Graceful Degradation** - Application works without observability backends
4. **Standards-Based** - OpenTelemetry for vendor neutrality
5. **Production-Ready** - Prometheus, Jaeger, cloud provider support

---

## Architecture Layers

### Layer 1: Core Observability (Built-in)

**Location:** `platform/primitives/src/tta_dev_primitives/observability/`

**Components:**
- `InstrumentedPrimitive` - Base class with automatic tracing
- `ObservablePrimitive` - Wrapper for adding observability
- `PrimitiveMetrics` - Lightweight metrics collection
- `WorkflowContext` - Context propagation

**Key Characteristics:**
- ✅ Zero external dependencies (uses Python logging)
- ✅ Always available
- ✅ Automatic span creation
- ✅ Context propagation

### Layer 2: Enhanced Observability (Optional)

**Location:** `platform/observability/`

**Components:**
- `initialize_observability()` - OpenTelemetry setup
- Enhanced primitives (Router, Cache, Timeout)
- Prometheus metrics server (port 9464)
- OTLP exporter configuration

**Key Characteristics:**
- 🔌 Optional OpenTelemetry dependency
- 📊 Prometheus metrics export
- 🔍 Distributed tracing (Jaeger, Zipkin)
- ☁️ Cloud provider integration (AWS X-Ray, GCP Cloud Trace)

---

## Component Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  (User workflows using primitives)                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              WorkflowPrimitive Base Class                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  execute(context, input_data)                       │   │
│  │    ├─ Create span (InstrumentedPrimitive)          │   │
│  │    ├─ Record metrics (PrimitiveMetrics)            │   │
│  │    ├─ Execute _execute_impl()                      │   │
│  │    └─ Log events                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Tracing  │    │ Metrics  │    │ Logging  │
    │          │    │          │    │          │
    │ OpenTel  │    │Prometheus│    │Structured│
    │ Spans    │    │ Counters │    │   JSON   │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
           ┌───────────────────────────────┐
           │       Exporters               │
           │                               │
           │  ├─ OTLP (OpenTelemetry)     │
           │  ├─ Prometheus HTTP          │
           │  ├─ Jaeger                   │
           │  └─ Console (debug)          │
           └───────────────────────────────┘
                           │
                           ▼
           ┌───────────────────────────────┐
           │    Monitoring Backends        │
           │                               │
           │  ├─ Prometheus + Grafana     │
           │  ├─ Jaeger UI                │
           │  ├─ AWS CloudWatch           │
           │  └─ GCP Cloud Monitoring     │
           └───────────────────────────────┘
```

---

## Core Observability Design

### InstrumentedPrimitive

**Purpose:** Base class providing automatic tracing for all primitives

**Implementation:**

```python
from opentelemetry import trace
from tta_dev_primitives.core.base import WorkflowPrimitive

class InstrumentedPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Base primitive with automatic instrumentation."""

    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self.tracer = trace.get_tracer(__name__)

    async def execute(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        """Execute with automatic span creation."""
        with self.tracer.start_as_current_span(
            f"{self.name}.execute",
            attributes={
                "primitive.name": self.name,
                "primitive.type": self.__class__.__name__,
                "correlation_id": context.correlation_id,
            }
        ) as span:
            try:
                result = await self._execute_impl(context, input_data)
                span.set_status(trace.Status(trace.StatusCode.OK))
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
```

**Key Features:**
- Automatic span creation per primitive execution
- Correlation ID propagation
- Error recording
- Status tracking

### PrimitiveMetrics

**Purpose:** Lightweight metrics collection without external dependencies

**Implementation:**

```python
from dataclasses import dataclass, field
from time import time
from typing import Dict

@dataclass
class PrimitiveMetrics:
    """Collect metrics for primitive execution."""

    name: str
    execution_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    execution_times: list[float] = field(default_factory=list)

    def record_execution(self, duration_ms: float, error: bool = False):
        """Record a single execution."""
        self.execution_count += 1
        if error:
            self.error_count += 1
        self.total_duration_ms += duration_ms
        self.execution_times.append(duration_ms)

    @property
    def avg_duration_ms(self) -> float:
        """Average execution time."""
        if self.execution_count == 0:
            return 0.0
        return self.total_duration_ms / self.execution_count

    @property
    def error_rate(self) -> float:
        """Error rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.error_count / self.execution_count) * 100
```

**Usage:**

```python
class MyPrimitive(InstrumentedPrimitive[str, str]):
    def __init__(self):
        super().__init__("my_primitive")
        self.metrics = PrimitiveMetrics(name="my_primitive")

    async def _execute_impl(self, context, input_data):
        start_time = time()
        try:
            result = await self.do_work(input_data)
            duration = (time() - start_time) * 1000
            self.metrics.record_execution(duration)
            return result
        except Exception as e:
            duration = (time() - start_time) * 1000
            self.metrics.record_execution(duration, error=True)
            raise
```

### WorkflowContext

**Purpose:** Propagate context and correlation across primitives

**Design:**

```python
@dataclass
class WorkflowContext:
    """Context passed through workflow execution."""

    # Unique correlation ID for request
    correlation_id: str

    # User-defined data
    data: dict[str, Any]

    # OpenTelemetry span context (optional)
    parent_span_context: SpanContext | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, correlation_id: str | None = None, **data) -> "WorkflowContext":
        """Create context with auto-generated correlation ID."""
        return cls(
            correlation_id=correlation_id or str(uuid.uuid4()),
            data=data
        )
```

**Context Propagation:**

```python
# Create context at entry point
context = WorkflowContext.create(
    user_id="user-123",
    request_type="analysis"
)

# Context flows through workflow automatically
result = await workflow.execute(context, input_data)

# All primitives receive same context
# Correlation ID appears in all logs/traces
```

---

## Enhanced Observability Design

### Initialization

**Entry Point:** `initialize_observability()`

**Implementation:**

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from prometheus_client import start_http_server

def initialize_observability(
    service_name: str,
    enable_prometheus: bool = True,
    prometheus_port: int = 9464,
    otlp_endpoint: str | None = None,
) -> bool:
    """
    Initialize observability with OpenTelemetry.
    Returns True if successful, False for graceful degradation.
    """
    try:
        # Setup tracer provider
        tracer_provider = TracerProvider(
            resource=Resource.create({
                "service.name": service_name,
                "service.version": "1.0.0",
            })
        )

        # Add exporters
        if otlp_endpoint:
            tracer_provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=otlp_endpoint)
                )
            )

        # Register provider
        trace.set_tracer_provider(tracer_provider)

        # Setup Prometheus
        if enable_prometheus:
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics on :{prometheus_port}/metrics")

        return True

    except Exception as e:
        logger.warning(f"Observability init failed: {e}")
        return False  # Graceful degradation
```

### Enhanced Primitives

**Pattern:** Extend core primitives with additional metrics

**Example: Enhanced CachePrimitive**

```python
from tta_dev_primitives.performance import CachePrimitive
from prometheus_client import Counter, Histogram

# Prometheus metrics
cache_hits = Counter(
    "cache_hit_total",
    "Total cache hits",
    ["primitive_name"]
)

cache_misses = Counter(
    "cache_miss_total",
    "Total cache misses",
    ["primitive_name"]
)

cache_operation_duration = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration",
    ["primitive_name", "operation"]
)

class EnhancedCachePrimitive(CachePrimitive):
    """CachePrimitive with Prometheus metrics."""

    async def _execute_impl(self, context, input_data):
        start_time = time()

        # Check cache
        cached = self._get_from_cache(input_data)

        if cached:
            cache_hits.labels(primitive_name=self.name).inc()
            duration = time() - start_time
            cache_operation_duration.labels(
                primitive_name=self.name,
                operation="hit"
            ).observe(duration)
            return cached

        # Cache miss
        cache_misses.labels(primitive_name=self.name).inc()

        # Execute and cache
        result = await self.primitive.execute(context, input_data)
        self._store_in_cache(input_data, result)

        duration = time() - start_time
        cache_operation_duration.labels(
            primitive_name=self.name,
            operation="miss"
        ).observe(duration)

        return result
```

### Prometheus Metrics Server

**Implementation:**

```python
from prometheus_client import start_http_server, Counter, Histogram, Gauge

# Define metrics
primitive_executions = Counter(
    "primitive_executions_total",
    "Total primitive executions",
    ["primitive_name", "status"]
)

primitive_duration = Histogram(
    "primitive_duration_seconds",
    "Primitive execution duration",
    ["primitive_name"],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0]
)

active_workflows = Gauge(
    "active_workflows",
    "Number of active workflows"
)

# Start server
start_http_server(9464)
# Metrics available at http://localhost:9464/metrics
```

---

## Distributed Tracing

### Span Hierarchy

```text
Root Span: workflow.execute
├─ Span: input_processor.execute
│  └─ Span: validate_input
│     └─ Event: validation_complete
│
├─ Span: router.execute
│  ├─ Attribute: route_selected=fast
│  ├─ Attribute: model=gpt-4-mini
│  └─ Event: route_decision_made
│
├─ Span: llm_call.execute
│  ├─ Attribute: prompt_tokens=150
│  ├─ Attribute: completion_tokens=200
│  ├─ Event: api_call_started
│  ├─ Event: api_call_completed
│  └─ Attribute: cost_usd=0.015
│
└─ Span: output_formatter.execute
   └─ Event: formatting_complete
```

### Context Propagation

**Within Process:**

```python
from opentelemetry import trace

# Get current span
current_span = trace.get_current_span()

# Add attributes
current_span.set_attribute("user_id", "user-123")

# Add events
current_span.add_event("processing_started")

# Child spans automatically inherit context
```

**Across Services:**

```python
import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Instrument HTTP client
HTTPXClientInstrumentor().instrument()

# Trace context automatically propagated in headers
async with httpx.AsyncClient() as client:
    # traceparent header added automatically:
    # traceparent: 00-{trace_id}-{span_id}-01
    response = await client.post("https://api.example.com/process")
```

---

## Metrics Collection

### Core Metrics

**Per Primitive:**
- `primitive_executions_total` - Counter by status (success/error)
- `primitive_duration_seconds` - Histogram of execution times
- `primitive_errors_total` - Counter of errors by type

**Workflow-Level:**
- `workflow_executions_total` - Counter by workflow name
- `workflow_duration_seconds` - Histogram of total duration
- `active_workflows` - Gauge of concurrent workflows

**Cache-Specific:**
- `cache_hit_total` - Counter of cache hits
- `cache_miss_total` - Counter of cache misses
- `cache_size_bytes` - Gauge of cache size
- `cache_evictions_total` - Counter of evictions

**Router-Specific:**
- `router_route_selected` - Counter by route name
- `router_decision_duration_seconds` - Histogram

### PromQL Queries

**Performance:**
```promql
# Average request duration (last 5min)
rate(primitive_duration_seconds_sum[5m])
  /
rate(primitive_duration_seconds_count[5m])

# P95 latency
histogram_quantile(0.95,
  rate(primitive_duration_seconds_bucket[5m])
)

# Request rate
rate(primitive_executions_total[5m])
```

**Reliability:**
```promql
# Error rate (%)
(rate(primitive_executions_total{status="error"}[5m])
  /
rate(primitive_executions_total[5m])) * 100

# Success rate (%)
(rate(primitive_executions_total{status="success"}[5m])
  /
rate(primitive_executions_total[5m])) * 100
```

**Cost Tracking:**
```promql
# Total LLM cost (last hour)
increase(llm_cost_usd_total[1h])

# Cost per request
llm_cost_usd_total / llm_requests_total

# Token usage rate
rate(llm_tokens_total[5m])
```

---

## Structured Logging

### Log Format

**JSON Structure:**

```json
{
  "timestamp": "2024-10-30T10:30:00.123Z",
  "level": "INFO",
  "event": "workflow_executed",
  "correlation_id": "req-abc-123",
  "trace_id": "a1b2c3d4e5f6789...",
  "span_id": "1234567890ab...",
  "service": "tta-app",
  "workflow_name": "user_onboarding",
  "duration_ms": 234.56,
  "status": "success",
  "user_id": "user-789"
}
```

### Implementation

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)

# Log with structure
logger.info(
    "workflow_executed",
    workflow_name="user_onboarding",
    duration_ms=234.56,
    status="success"
)
```

### Log Correlation

**Automatic Correlation:**

```python
from opentelemetry import trace

# Correlation IDs automatically added
span = trace.get_current_span()
span_context = span.get_span_context()

logger.info(
    "operation_completed",
    # These are added automatically by structlog processor
    trace_id=format(span_context.trace_id, '032x'),
    span_id=format(span_context.span_id, '016x')
)
```

---

## Performance Considerations

### Overhead Analysis

**Core Observability:**
- Span creation: ~0.5ms
- Attribute setting: ~0.1ms per attribute
- Event recording: ~0.1ms per event
- **Total per primitive:** ~1-2ms

**Enhanced Observability:**
- Prometheus metric recording: ~0.5ms
- OTLP span export (batched): ~0ms (async)
- **Total per primitive:** ~2-3ms

**Optimization Strategies:**

1. **Batch Span Export**
   ```python
   from opentelemetry.sdk.trace.export import BatchSpanProcessor

   processor = BatchSpanProcessor(
       exporter,
       max_queue_size=2048,
       max_export_batch_size=512,
       schedule_delay_millis=5000
   )
   ```

2. **Sampling**
   ```python
   from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

   sampler = ParentBasedTraceIdRatio(0.1)  # 10% sampling
   ```

3. **Selective Instrumentation**
   ```python
   # Only instrument critical paths
   if context.data.get("enable_tracing", False):
       with tracer.start_as_current_span("operation"):
           result = await operation()
   ```

---

## Production Deployment

### Monitoring Stack

**Recommended Setup:**

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
```

**Prometheus Configuration:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tta-app'
    static_configs:
      - targets: ['localhost:9464']
    scrape_interval: 15s
```

### Cloud Deployment

**AWS:**
```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Export to AWS X-Ray via OTLP
exporter = OTLPSpanExporter(
    endpoint="https://xray.us-east-1.amazonaws.com"
)
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
```

**GCP:**
```python
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

# Export to Google Cloud Trace
exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
```

---

## Best Practices

### Span Design

1. **Descriptive Names** - Use hierarchical names: `workflow.step.operation`
2. **Meaningful Attributes** - Add context: user_id, request_type, input_size
3. **Events for Milestones** - Mark important points: validation_complete, api_call_started
4. **Error Recording** - Always record exceptions with `span.record_exception(e)`

### Metrics Design

1. **Use Counters for Totals** - Requests, errors, events
2. **Use Histograms for Distributions** - Latency, size, duration
3. **Use Gauges for Current State** - Active connections, queue size
4. **Consistent Labeling** - Same label names across metrics

### Logging Best Practices

1. **Structured Always** - Use structlog, never string formatting
2. **Correlation IDs** - Include in every log
3. **Appropriate Levels** - DEBUG for verbose, INFO for events, ERROR for issues
4. **Searchable Fields** - Use consistent field names

---

## Related Documentation

- **Package README:** [`platform/observability/README.md`](../../platform/observability/README.md)
- **Integration Guide:** [`docs/integration/observability-integration.md`](../integration/observability-integration.md)
- **Component Analysis:** [`COMPONENT_INTEGRATION_ANALYSIS.md`](COMPONENT_INTEGRATION_ANALYSIS.md)
- **Monitoring Dashboard:** [`WEEK1_MONITORING_DASHBOARD.md`](../../WEEK1_MONITORING_DASHBOARD.md)

---

**Last Updated:** October 30, 2025
**Maintainer:** TTA.dev Core Team


---
**Logseq:** [[TTA.dev/Docs/Architecture/Observability_architecture]]
