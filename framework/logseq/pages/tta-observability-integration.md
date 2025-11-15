# tta-observability-integration

**OpenTelemetry and Prometheus integration package for TTA.dev primitives.**

## Overview

The tta-observability-integration package provides automatic observability for TTA.dev workflows through OpenTelemetry tracing and Prometheus metrics.

**Package:** `packages/tta-observability-integration/`

## Installation

```bash
# From source (current)
cd packages/tta-observability-integration
uv sync

# From PyPI (when published)
pip install tta-observability-integration
```

## Quick Start

### Initialize Observability

```python
from observability_integration import initialize_observability

# Call once at application startup
success = initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    otlp_endpoint="http://localhost:4317"  # Optional
)

# All primitives automatically instrumented
```

### Use Enhanced Primitives

```python
from observability_integration.primitives import (
    RouterPrimitive,
    CachePrimitive,
    TimeoutPrimitive
)

# These primitives have enhanced observability
workflow = (
    CachePrimitive(expensive_op, ttl=3600) >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    TimeoutPrimitive(external_api, timeout=30)
)

# Automatic metrics, traces, and logs!
```

## Features

### 1. Automatic Tracing

Every primitive execution creates OpenTelemetry spans:

```python
# Span hierarchy automatically created:
# my-app.workflow.execute
#   ├─ cache.execute
#   ├─ router.execute
#   │  └─ llm1.execute
#   └─ timeout.execute
```

**View in Jaeger:** <http://localhost:16686>

### 2. Prometheus Metrics

Metrics automatically exported on port 9464:

```promql
# Execution duration
primitive_execution_duration_seconds{primitive="CachePrimitive"}

# Cache hit rate
cache_hit_rate{primitive="CachePrimitive"}

# Error rate
primitive_execution_errors_total{primitive="RouterPrimitive"}
```

**Scrape endpoint:** `http://localhost:9464/metrics`

### 3. Structured Logging

Automatic structured logs for all operations:

```json
{
  "timestamp": "2025-11-05T10:30:00Z",
  "level": "info",
  "message": "primitive_execution_complete",
  "primitive": "CachePrimitive",
  "duration_ms": 45.2,
  "status": "success",
  "correlation_id": "req-12345"
}
```

### 4. Context Propagation

[[TTA.dev/Data/WorkflowContext]] automatically propagates:
- Correlation IDs
- Trace context
- User metadata
- Custom attributes

## Enhanced Primitives

### CachePrimitive

**Metrics:**
- `cache_hits_total` - Cache hits
- `cache_misses_total` - Cache misses
- `cache_size` - Current cache size
- `cache_evictions_total` - LRU evictions

**Spans:**
- `cache.get` - Cache lookup
- `cache.set` - Cache write
- `cache.evict` - Eviction

### RouterPrimitive

**Metrics:**
- `router_route_selected_total{route="fast"}` - Route selections
- `router_execution_duration_seconds{route="quality"}` - Per-route latency

**Spans:**
- `router.select_route` - Route selection logic
- `router.execute_route` - Route execution

### TimeoutPrimitive

**Metrics:**
- `timeout_triggered_total` - Timeouts triggered
- `timeout_duration_seconds` - Operation duration

**Spans:**
- `timeout.execute` - Timed operation
- `timeout.cancel` - Cancellation (if timeout)

## Configuration

### Environment Variables

```bash
# OpenTelemetry
export OTEL_SERVICE_NAME="my-app"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Prometheus
export PROMETHEUS_PORT="9464"

# Logging
export LOG_LEVEL="INFO"
export LOG_FORMAT="json"
```

### Programmatic Configuration

```python
from observability_integration import ObservabilityConfig

config = ObservabilityConfig(
    service_name="my-app",
    service_version="1.0.0",
    enable_prometheus=True,
    prometheus_port=9464,
    enable_otlp=True,
    otlp_endpoint="http://collector:4317",
    log_level="INFO"
)

success = initialize_observability(config=config)
```

## Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - PROMETHEUS_PORT=9464
    ports:
      - "8000:8000"
      - "9464:9464"  # Prometheus metrics

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP receiver

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-metrics
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9464"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: myapp
  ports:
  - name: metrics
    port: 9464
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
```

## Grafana Dashboards

### Pre-built Dashboards

1. **Workflow Overview**
   - Request rate
   - Error rate
   - P95/P99 latency
   - Cache hit rate

2. **Primitive Performance**
   - Per-primitive latency
   - Execution counts
   - Error breakdown

3. **Cache Analytics**
   - Hit/miss ratio
   - Eviction rate
   - Size over time

**Import from:** `packages/tta-observability-integration/dashboards/`

## Troubleshooting

### Metrics Not Appearing

```python
# Check if Prometheus is initialized
from observability_integration import is_prometheus_enabled

if not is_prometheus_enabled():
    print("Prometheus not initialized!")
```

### Traces Not Showing

```bash
# Verify OTLP endpoint is reachable
curl http://localhost:4317

# Check OpenTelemetry configuration
python -c "from opentelemetry import trace; print(trace.get_tracer_provider())"
```

### High Memory Usage

```python
# Adjust batch sizes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,  # Reduce from default
    max_export_batch_size=512
)
```

## Integration Examples

### With FastAPI

```python
from fastapi import FastAPI
from observability_integration import initialize_observability

app = FastAPI()

@app.on_event("startup")
async def startup():
    initialize_observability(service_name="my-fastapi-app")

@app.get("/api/process")
async def process():
    result = await workflow.execute(data, context)
    return result
```

### With Celery

```python
from celery import Celery
from observability_integration import initialize_observability

app = Celery('tasks')

@app.task
def process_task():
    initialize_observability(service_name="celery-worker")
    # Task implementation
```

## Architecture

### Component Diagram

```
Application
    ↓
observability_integration.initialize_observability()
    ↓
    ├─ OpenTelemetry Setup
    │  ├─ TracerProvider
    │  ├─ OTLP Exporter
    │  └─ BatchSpanProcessor
    │
    ├─ Prometheus Setup
    │  ├─ Registry
    │  ├─ Metrics Server (:9464)
    │  └─ Custom Collectors
    │
    └─ Enhanced Primitives
       ├─ CachePrimitive
       ├─ RouterPrimitive
       └─ TimeoutPrimitive
```

## Related Documentation

- [[TTA.dev/Primitives]] - All primitives
- [[InstrumentedPrimitive]] - Base observability
- [[TTA.dev/Guides/Observability]] - Observability guide
- Package README: `packages/tta-observability-integration/README.md`

## External Resources

- OpenTelemetry: <https://opentelemetry.io/>
- Prometheus: <https://prometheus.io/>
- Jaeger: <https://www.jaegertracing.io/>
- Grafana: <https://grafana.com/>

## Tags

package:: tta-observability-integration
type:: integration
feature:: tracing
feature:: metrics
feature:: logging

- [[Project Hub]]
