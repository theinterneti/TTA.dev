# Memory Layer Performance Monitoring

**Purpose**: Metrics, monitoring, and observability for TTA.dev's 4-layer memory system.

**Status**: Active
**Last Updated**: 2025-10-28

---

## Overview

This document describes the performance monitoring strategy for the memory system, including metrics collection, observability integration, and performance optimization techniques.

## Table of Contents

1. [Metrics Overview](#metrics-overview)
2. [Implementation](#implementation)
3. [OpenTelemetry Integration](#opentelemetry-integration)
4. [Dashboards](#dashboards)
5. [Alerts](#alerts)
6. [Performance Optimization](#performance-optimization)

---

## Metrics Overview

### Memory Layer Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `memory.layer1.session.messages` | Counter | Session messages stored | - |
| `memory.layer2.cache.hits` | Counter | Cache hit count | >80% |
| `memory.layer2.cache.misses` | Counter | Cache miss count | <20% |
| `memory.layer3.deep.queries` | Counter | Deep memory queries | - |
| `memory.layer3.deep.results` | Histogram | Results per query | 5-20 |
| `memory.layer4.paf.validations` | Counter | PAF validations | - |
| `memory.layer4.paf.violations` | Counter | PAF violations | 0 |

### Latency Metrics

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `memory.operation.duration` | Histogram | Operation latency (ms) | <100ms (p95) |
| `memory.context.load.duration` | Histogram | Context loading time | <500ms (p95) |
| `memory.search.duration` | Histogram | Search query time | <200ms (p95) |
| `memory.enrichment.duration` | Histogram | A-MEM enrichment time | <2s (p95) |

### Size Metrics

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|----------------|
| `memory.session.size` | Gauge | Session context size (bytes) | >10MB |
| `memory.cache.size` | Gauge | Cache memory size (bytes) | >100MB |
| `memory.deep.count` | Gauge | Total deep memories | >10,000 |

---

## Implementation

### 1. Instrumented MemoryWorkflowPrimitive

Add metrics to the core primitive:

```python
from opentelemetry import metrics
from opentelemetry.metrics import get_meter
from time import time


class MemoryWorkflowPrimitive:
    """Memory primitive with observability."""

    def __init__(self, redis_url: str, user_id: str):
        self.redis_client = RedisAgentMemoryClient(redis_url)
        self.user_id = user_id
        
        # Initialize metrics
        meter = get_meter(__name__)
        
        # Counters
        self.session_messages_counter = meter.create_counter(
            "memory.layer1.session.messages",
            description="Number of session messages stored"
        )
        
        self.cache_hits_counter = meter.create_counter(
            "memory.layer2.cache.hits",
            description="Cache hit count"
        )
        
        self.cache_misses_counter = meter.create_counter(
            "memory.layer2.cache.misses",
            description="Cache miss count"
        )
        
        self.deep_queries_counter = meter.create_counter(
            "memory.layer3.deep.queries",
            description="Deep memory query count"
        )
        
        self.paf_validations_counter = meter.create_counter(
            "memory.layer4.paf.validations",
            description="PAF validation count"
        )
        
        self.paf_violations_counter = meter.create_counter(
            "memory.layer4.paf.violations",
            description="PAF violation count"
        )
        
        # Histograms
        self.operation_duration_histogram = meter.create_histogram(
            "memory.operation.duration",
            description="Memory operation latency in milliseconds",
            unit="ms"
        )
        
        self.context_load_duration_histogram = meter.create_histogram(
            "memory.context.load.duration",
            description="Context loading duration in milliseconds",
            unit="ms"
        )
        
        self.search_duration_histogram = meter.create_histogram(
            "memory.search.duration",
            description="Search query duration in milliseconds",
            unit="ms"
        )
        
        # Gauges (up-down counters)
        self.session_size_gauge = meter.create_up_down_counter(
            "memory.session.size",
            description="Session context size in bytes",
            unit="bytes"
        )
        
        self.cache_size_gauge = meter.create_up_down_counter(
            "memory.cache.size",
            description="Cache memory size in bytes",
            unit="bytes"
        )

    async def add_session_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """Add session message with metrics."""
        start = time()
        
        try:
            # Original logic
            await self.redis_client.add_message(
                session_id=session_id,
                user_id=self.user_id,
                role=role,
                content=content
            )
            
            # Record metrics
            self.session_messages_counter.add(1, {"session_id": session_id})
            
            message_size = len(content.encode('utf-8'))
            self.session_size_gauge.add(message_size, {"session_id": session_id})
            
        finally:
            duration_ms = (time() - start) * 1000
            self.operation_duration_histogram.record(
                duration_ms,
                {"operation": "add_session_message", "layer": "1"}
            )

    async def get_cache_memory(
        self,
        session_id: str,
        time_window_hours: int
    ) -> list[dict]:
        """Get cache memory with hit/miss tracking."""
        start = time()
        
        try:
            # Original logic
            results = await self.redis_client.get_working_memory(
                session_id=session_id,
                user_id=self.user_id,
                time_window=timedelta(hours=time_window_hours)
            )
            
            # Track cache hit/miss
            if results:
                self.cache_hits_counter.add(1, {"session_id": session_id})
            else:
                self.cache_misses_counter.add(1, {"session_id": session_id})
            
            # Track cache size
            cache_size = sum(len(r.get("text", "").encode('utf-8')) for r in results)
            self.cache_size_gauge.add(cache_size, {"session_id": session_id})
            
            return results
            
        finally:
            duration_ms = (time() - start) * 1000
            self.operation_duration_histogram.record(
                duration_ms,
                {"operation": "get_cache_memory", "layer": "2"}
            )

    async def search_deep_memory(
        self,
        query: str,
        limit: int = 10,
        tags: list[str] | None = None
    ) -> list[dict]:
        """Search deep memory with query tracking."""
        start = time()
        
        try:
            # Original logic
            results = await self.redis_client.search_long_term_memory(
                text=query,
                user_id=self.user_id,
                k=limit,
                filter_metadata={"tags": tags} if tags else None
            )
            
            # Record query
            self.deep_queries_counter.add(1, {"query_tags": str(tags)})
            
            return results
            
        finally:
            duration_ms = (time() - start) * 1000
            self.search_duration_histogram.record(
                duration_ms,
                {"operation": "search_deep_memory", "layer": "3", "result_count": len(results)}
            )

    def validate_paf(
        self,
        paf_id: str,
        actual_value: Any
    ) -> PAFValidationResult:
        """Validate PAF with violation tracking."""
        start = time()
        
        try:
            # Original logic
            result = self.paf_primitive.validate_against_paf(paf_id, actual_value)
            
            # Record validation
            self.paf_validations_counter.add(1, {"paf_id": paf_id})
            
            # Track violations
            if not result.is_valid:
                self.paf_violations_counter.add(
                    1,
                    {"paf_id": paf_id, "severity": result.severity}
                )
            
            return result
            
        finally:
            duration_ms = (time() - start) * 1000
            self.operation_duration_histogram.record(
                duration_ms,
                {"operation": "validate_paf", "layer": "4"}
            )

    async def load_workflow_context(
        self,
        context: WorkflowContext,
        stage: str,
        mode: WorkflowMode
    ) -> WorkflowContext:
        """Load workflow context with full timing."""
        start = time()
        
        try:
            # Original logic (complex multi-layer loading)
            enriched_ctx = await self._load_context_internal(context, stage, mode)
            
            return enriched_ctx
            
        finally:
            duration_ms = (time() - start) * 1000
            self.context_load_duration_histogram.record(
                duration_ms,
                {
                    "stage": stage,
                    "mode": mode.value,
                    "layers_loaded": self._count_loaded_layers(enriched_ctx)
                }
            )
```

### 2. OpenTelemetry Setup

Initialize OpenTelemetry in your application:

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter


def setup_memory_observability(
    otlp_endpoint: str = "http://localhost:4317",
    service_name: str = "tta-memory-service"
):
    """Setup OpenTelemetry for memory metrics."""
    
    # Create OTLP exporter
    exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=True
    )
    
    # Create metric reader (export every 30 seconds)
    reader = PeriodicExportingMetricReader(
        exporter=exporter,
        export_interval_millis=30000
    )
    
    # Create meter provider
    provider = MeterProvider(
        metric_readers=[reader],
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0"
        })
    )
    
    # Set global meter provider
    metrics.set_meter_provider(provider)
    
    print(f"✅ Memory observability initialized (OTLP: {otlp_endpoint})")


# Usage
setup_memory_observability()

memory = MemoryWorkflowPrimitive(
    redis_url="http://localhost:8000",
    user_id="my-user"
)
```

---

## OpenTelemetry Integration

### Integration with Existing APM

If you already have OpenTelemetry APM setup (from `tta-dev-primitives`):

```python
from tta_dev_primitives import setup_apm

# Setup APM for primitives + memory
setup_apm(
    service_name="tta-app",
    otlp_endpoint="http://localhost:4317",
    enable_console_export=False
)

# Memory metrics will automatically use the same provider
memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")
```

### Grafana Integration

Export metrics to Grafana Cloud or self-hosted Grafana:

```yaml
# docker-compose.yml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
      - "8889:8889"  # Prometheus metrics

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
```

---

## Dashboards

### Memory Overview Dashboard

**Panels**:

1. **Layer Activity** (Time Series)
   - Metric: `sum(rate(memory.layer*.*.messages[5m])) by (layer)`
   - Shows activity across all 4 layers

2. **Cache Hit Rate** (Gauge)
   - Metric: `memory.layer2.cache.hits / (memory.layer2.cache.hits + memory.layer2.cache.misses)`
   - Target: >80%

3. **PAF Violations** (Counter)
   - Metric: `sum(memory.layer4.paf.violations)`
   - Alert if > 0

4. **Operation Latency** (Histogram)
   - Metric: `histogram_quantile(0.95, memory.operation.duration)`
   - P50, P95, P99

5. **Context Load Time by Mode** (Bar Chart)
   - Metric: `avg(memory.context.load.duration) by (mode)`
   - Compare Rapid vs Standard vs Augster-Rigorous

### Example PromQL Queries

```promql
# Cache hit rate
sum(rate(memory_layer2_cache_hits_total[5m])) 
/ 
(sum(rate(memory_layer2_cache_hits_total[5m])) + sum(rate(memory_layer2_cache_misses_total[5m])))

# Average context load time by stage
avg(memory_context_load_duration_bucket) by (stage)

# PAF violations by severity
sum(memory_layer4_paf_violations_total) by (severity)

# Deep memory query throughput
rate(memory_layer3_deep_queries_total[5m])
```

---

## Alerts

### Critical Alerts

```yaml
# Prometheus alert rules
groups:
  - name: memory_critical
    interval: 30s
    rules:
      - alert: MemoryCacheHitRateLow
        expr: |
          sum(rate(memory_layer2_cache_hits_total[5m])) 
          / 
          (sum(rate(memory_layer2_cache_hits_total[5m])) + sum(rate(memory_layer2_cache_misses_total[5m]))) 
          < 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory cache hit rate below 50%"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
      
      - alert: PAFViolationsDetected
        expr: sum(increase(memory_layer4_paf_violations_total[5m])) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PAF violations detected"
          description: "{{ $value }} PAF violations in last 5 minutes"
      
      - alert: ContextLoadingSlow
        expr: histogram_quantile(0.95, memory_context_load_duration_bucket) > 2000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Context loading taking >2s (p95)"
          description: "P95 context load time: {{ $value }}ms"
```

---

## Performance Optimization

### 1. Cache Tuning

```python
# Adjust cache time windows based on hit rate metrics
if cache_hit_rate < 0.5:
    # Increase cache window
    memory.get_cache_memory(session_id, time_window_hours=24)  # Increase from 1 to 24
else:
    # Use smaller window (faster)
    memory.get_cache_memory(session_id, time_window_hours=1)
```

### 2. Query Optimization

```python
# Use metrics to identify slow queries
slow_query_threshold_ms = 500

# Monitor and optimize
if avg_search_duration > slow_query_threshold_ms:
    # Reduce search scope
    results = await memory.search_deep_memory(
        query=query,
        limit=5,  # Reduce from 20
        tags=specific_tags  # Add more specific filters
    )
```

### 3. Context Loading Strategy

```python
# Use metrics to choose appropriate mode
if p95_context_load_time > 1000:
    # Switch to faster mode
    ctx = await memory.load_workflow_context(
        context=ctx,
        stage=stage,
        mode=WorkflowMode.RAPID  # Faster loading
    )
```

---

## Testing Performance

### Benchmark Script

```python
import asyncio
import time
from statistics import mean, median, stdev


async def benchmark_memory_operations():
    """Benchmark memory operations."""
    memory = MemoryWorkflowPrimitive(
        redis_url="http://localhost:8000",
        user_id="benchmark-user"
    )
    
    # Test 1: Session message add
    times = []
    for i in range(100):
        start = time.time()
        await memory.add_session_message(
            session_id="benchmark-session",
            role="user",
            content=f"Test message {i}"
        )
        times.append((time.time() - start) * 1000)
    
    print(f"Session Message Add:")
    print(f"  Mean: {mean(times):.2f}ms")
    print(f"  Median: {median(times):.2f}ms")
    print(f"  Std Dev: {stdev(times):.2f}ms")
    print(f"  P95: {sorted(times)[94]:.2f}ms")
    
    # Test 2: Deep memory search
    times = []
    for i in range(50):
        start = time.time()
        results = await memory.search_deep_memory(
            query="test",
            limit=10
        )
        times.append((time.time() - start) * 1000)
    
    print(f"\nDeep Memory Search:")
    print(f"  Mean: {mean(times):.2f}ms")
    print(f"  P95: {sorted(times)[47]:.2f}ms")
    
    # Test 3: Context loading
    ctx = WorkflowContext(workflow_id="test", session_id="benchmark-session")
    times = []
    for mode in [WorkflowMode.RAPID, WorkflowMode.STANDARD, WorkflowMode.AUGSTER_RIGOROUS]:
        start = time.time()
        await memory.load_workflow_context(ctx, "understand", mode)
        duration = (time.time() - start) * 1000
        times.append((mode.value, duration))
    
    print(f"\nContext Loading:")
    for mode, duration in times:
        print(f"  {mode}: {duration:.2f}ms")


asyncio.run(benchmark_memory_operations())
```

---

## Next Steps

1. **Deploy Monitoring**: Set up Grafana dashboards
2. **Baseline Performance**: Establish baseline metrics
3. **Set Alerts**: Configure alert thresholds
4. **Continuous Tuning**: Monitor and optimize based on real usage

---

**Last Updated**: 2025-10-28
**Maintained By**: TTA.dev Observability Team
