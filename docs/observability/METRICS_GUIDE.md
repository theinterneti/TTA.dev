# Phase 3 Enhanced Metrics Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-29  
**Status:** ✅ Production Ready

---

## Overview

Phase 3 Enhanced Metrics provides production-quality observability with percentile tracking, SLO monitoring, throughput metrics, and comprehensive cost tracking. This guide covers all metrics types, usage patterns, and best practices.

## Table of Contents

1. [Metrics Types](#metrics-types)
2. [Usage Examples](#usage-examples)
3. [Integration](#integration)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

---

## Metrics Types

### 1. PercentileMetrics

**Purpose:** Track latency percentiles (p50, p90, p95, p99) for performance analysis.

**Key Features:**
- Sliding window (configurable size, default 1000 samples)
- Uses numpy for accurate calculation (falls back to manual if unavailable)
- Thread-safe for concurrent access

**Usage:**
```python
from tta_dev_primitives.observability import PercentileMetrics

# Create metrics instance
metrics = PercentileMetrics(window_size=1000)

# Record latencies
metrics.record(45.2)
metrics.record(123.5)
metrics.record(567.8)

# Get specific percentile
p95 = metrics.get_percentile(0.95)
print(f"p95 latency: {p95}ms")

# Get all common percentiles
stats = metrics.get_stats()
print(f"p50: {stats['p50']}ms")
print(f"p90: {stats['p90']}ms")
print(f"p95: {stats['p95']}ms")
print(f"p99: {stats['p99']}ms")
print(f"Sample count: {stats['count']}")
```

**When to Use:**
- Latency analysis and SLO tracking
- Performance regression detection
- Capacity planning

---

### 2. SLOMetrics

**Purpose:** Track Service Level Objectives with error budget calculation.

**Key Features:**
- Supports latency and availability SLOs
- Automatic error budget tracking
- Configurable time windows

**Usage:**
```python
from tta_dev_primitives.observability import SLOConfig, SLOMetrics

# Configure latency SLO: 95% of requests under 1000ms
latency_slo = SLOConfig(
    name="api_latency",
    target=0.95,  # 95% target
    threshold_ms=1000.0,  # 1 second threshold
    window_seconds=2592000.0  # 30 days
)

slo = SLOMetrics(latency_slo)

# Record requests
slo.record_request(success=True, latency_ms=450.0)
slo.record_request(success=True, latency_ms=1500.0)  # SLO violation

# Check compliance
compliance = slo.get_compliance()
print(f"SLO compliance: {compliance:.2%}")

# Check error budget
budget = slo.get_error_budget()
print(f"Error budget remaining: {budget:.2%}")

# Get comprehensive stats
stats = slo.get_stats()
print(f"Target: {stats['target']:.2%}")
print(f"Compliance: {stats['compliance']:.2%}")
print(f"Error budget: {stats['error_budget']:.2%}")
print(f"Total requests: {stats['total_requests']}")
print(f"Conforming requests: {stats['conforming_requests']}")
```

**Availability SLO Example:**
```python
# Configure availability SLO: 99.9% success rate
availability_slo = SLOConfig(
    name="api_availability",
    target=0.999,
    threshold_ms=None,  # No latency threshold
    window_seconds=2592000.0
)

slo = SLOMetrics(availability_slo)

# Record requests (latency not required for availability SLO)
slo.record_request(success=True)
slo.record_request(success=False)  # Failure
```

**When to Use:**
- Production SLO monitoring
- Error budget tracking
- Reliability engineering

---

### 3. ThroughputMetrics

**Purpose:** Track requests per second (RPS) and active concurrent requests.

**Key Features:**
- Real-time RPS calculation
- Active request tracking
- Thread-safe for concurrent operations

**Usage:**
```python
from tta_dev_primitives.observability import ThroughputMetrics

# Create metrics instance
throughput = ThroughputMetrics(window_seconds=60.0)

# Track requests
throughput.start_request()
try:
    # Process request
    pass
finally:
    throughput.end_request()

# Get metrics
rps = throughput.get_rps()
active = throughput.get_active_requests()
print(f"Current load: {rps:.1f} req/s")
print(f"Active requests: {active}")

# Get comprehensive stats
stats = throughput.get_stats()
print(f"RPS: {stats['rps']:.1f}")
print(f"Active: {stats['active_requests']}")
```

**When to Use:**
- Load monitoring
- Capacity planning
- Autoscaling decisions

---

### 4. CostMetrics

**Purpose:** Track costs and savings from optimizations.

**Key Features:**
- Separate cost and savings tracking
- Savings rate calculation
- Support for any currency unit

**Usage:**
```python
from tta_dev_primitives.observability import CostMetrics

# Create metrics instance
cost = CostMetrics()

# Record actual cost (e.g., LLM API call)
cost.record_cost(0.05)

# Record savings (e.g., cache hit avoided $0.05 call)
cost.record_savings(0.05)

# Get metrics
total_cost = cost.get_total_cost()
total_savings = cost.get_total_savings()
savings_rate = cost.get_savings_rate()

print(f"Total cost: ${total_cost:.2f}")
print(f"Total savings: ${total_savings:.2f}")
print(f"Savings rate: {savings_rate:.1%}")

# Get comprehensive stats
stats = cost.get_stats()
print(f"Cost: ${stats['total_cost']:.2f}")
print(f"Savings: ${stats['total_savings']:.2f}")
print(f"Rate: {stats['savings_rate']:.1%}")
```

**When to Use:**
- Infrastructure cost tracking
- ROI measurement for caching
- Budget monitoring

---

### 5. EnhancedMetricsCollector

**Purpose:** Unified collector integrating all metrics types.

**Key Features:**
- Single interface for all metrics
- Per-primitive configuration
- Thread-safe global singleton
- Automatic metric collection

**Usage:**
```python
from tta_dev_primitives.observability import (
    EnhancedMetricsCollector,
    SLOConfig,
    get_enhanced_metrics_collector,
)

# Get global collector
collector = get_enhanced_metrics_collector()

# Configure SLO for a primitive
collector.configure_slo(
    "api_call",
    SLOConfig(
        name="api_latency",
        target=0.95,
        threshold_ms=1000.0
    )
)

# Record execution
collector.start_request("api_call")
try:
    # Execute primitive
    collector.record_execution(
        primitive_name="api_call",
        duration_ms=450.0,
        success=True,
        cost=0.05
    )
except Exception as e:
    collector.record_execution(
        primitive_name="api_call",
        duration_ms=1250.0,
        success=False,
        error_type=type(e).__name__,
        cost=0.05
    )

# Record savings from cache hit
collector.record_savings("api_call", 0.05)

# Get comprehensive metrics
metrics = collector.get_all_metrics("api_call")
print("Basic metrics:", metrics.get("basic"))
print("Percentiles:", metrics.get("percentiles"))
print("SLO:", metrics.get("slo"))
print("Throughput:", metrics.get("throughput"))
print("Cost:", metrics.get("cost"))
```

**When to Use:**
- Production workflows
- Comprehensive monitoring
- Integrated observability

---

## Integration

### Automatic Integration (Recommended)

The collector integrates automatically with instrumented primitives:

```python
from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.observability import get_enhanced_metrics_collector

class MyPrimitive(WorkflowPrimitive):
    async def execute(self, input_data, context):
        collector = get_enhanced_metrics_collector()
        collector.start_request("my_primitive")
        
        start_time = time.time()
        try:
            result = await self._do_work(input_data)
            duration_ms = (time.time() - start_time) * 1000
            
            collector.record_execution(
                primitive_name="my_primitive",
                duration_ms=duration_ms,
                success=True,
                cost=self._calculate_cost(result)
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            collector.record_execution(
                primitive_name="my_primitive",
                duration_ms=duration_ms,
                success=False,
                error_type=type(e).__name__
            )
            raise
```

### Prometheus Export

```python
from tta_dev_primitives.observability import get_prometheus_exporter

# Get exporter
exporter = get_prometheus_exporter()

# Record in Prometheus
exporter.record_execution(
    primitive_name="api_call",
    primitive_type="HTTPPrimitive",
    duration_ms=450.0,
    success=True,
    cost=0.05
)

# Update gauges
metrics = collector.get_all_metrics("api_call")
exporter.update_gauges("api_call", metrics)

# Export for scraping
metrics_text = exporter.get_metrics_text()
```

---

## Best Practices

### 1. Metric Collection

**DO:**
- Use global singleton: `get_enhanced_metrics_collector()`
- Record metrics in `finally` blocks for reliability
- Track both successes and failures
- Include error types for debugging

**DON'T:**
- Create multiple collector instances
- Skip recording on errors
- Record metrics in hot loops (too frequent)
- Forget to call `start_request()` before `end_request()`

### 2. SLO Configuration

**DO:**
- Set realistic targets based on historical data
- Use 30-day windows for stability
- Monitor error budget consumption
- Configure separate SLOs for latency and availability

**DON'T:**
- Set unrealistic targets (99.99% for new systems)
- Use very short windows (< 1 hour)
- Ignore error budget warnings
- Mix latency and availability in one SLO

### 3. Cost Tracking

**DO:**
- Track actual costs from providers
- Record savings from cache hits
- Use consistent currency units
- Monitor cost per request

**DON'T:**
- Estimate costs without data
- Forget to track savings
- Mix currency units
- Ignore cost anomalies

### 4. Performance Optimization

**DO:**
- Use sliding windows appropriately
- Monitor cardinality (unique label combinations)
- Aggregate metrics for dashboards
- Clean up old metrics periodically

**DON'T:**
- Use very large windows (> 10000 samples)
- Create too many unique metrics
- Store all-time metrics in memory
- Query metrics synchronously in hot paths

---

## Troubleshooting

### Issue: Percentiles seem incorrect

**Symptoms:** p95/p99 values don't match expectations

**Solutions:**
1. Check window size - may be too small
2. Verify data distribution - outliers affect percentiles
3. Ensure enough samples (>100 for reliable percentiles)
4. Use numpy for accurate calculation

### Issue: SLO always shows 100% compliance

**Symptoms:** Compliance never drops below target

**Possible Causes:**
1. Threshold too high (all requests conform)
2. Window not reset (using stale data)
3. Not recording failures

**Solutions:**
1. Review SLO configuration
2. Ensure window resets properly
3. Verify failure recording

### Issue: High memory usage

**Symptoms:** Memory grows over time

**Possible Causes:**
1. Too many unique primitives
2. Window sizes too large
3. Metrics not cleaned up

**Solutions:**
1. Reduce cardinality
2. Use smaller windows
3. Implement metric expiration

### Issue: Metrics not appearing in Prometheus

**Symptoms:** No metrics in /metrics endpoint

**Possible Causes:**
1. prometheus-client not installed
2. Metrics not exported
3. Cardinality limit reached

**Solutions:**
1. Install: `pip install prometheus-client`
2. Call `exporter.record_execution()`
3. Check cardinality stats

---

## Reference

### Metric Names (Prometheus)

- `primitive_duration_seconds` - Histogram for latency percentiles
- `primitive_requests_total` - Counter for total requests
- `primitive_active_requests` - Gauge for concurrent requests
- `primitive_slo_compliance` - Gauge for SLO compliance rate
- `primitive_error_budget_remaining` - Gauge for error budget
- `primitive_cost_total` - Counter for total costs
- `primitive_cost_savings_total` - Counter for savings
- `primitive_requests_per_second` - Gauge for RPS

### Labels

- `primitive_name` - Name of the primitive
- `primitive_type` - Type/class of the primitive
- `slo_name` - Name of the SLO
- `status` - Request status (success/error)

---

## Next Steps

- [Prometheus Setup Guide](PROMETHEUS_SETUP.md)
- [Grafana Dashboards](../../packages/tta-dev-primitives/grafana/README.md)
- [AlertManager Rules](../../packages/tta-dev-primitives/alertmanager/README.md)

---

**Questions or Issues?**  
- GitHub Issues: https://github.com/theinterneti/TTA.dev/issues
- Documentation: `docs/observability/`
