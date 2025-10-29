# Metrics Guide

**Complete reference for TTA.dev enhanced metrics, SLO tracking, and observability.**

---

## Overview

TTA.dev provides production-quality metrics for monitoring workflow performance, tracking SLOs, and optimizing costs. This guide covers all available metrics, their meanings, and how to use them effectively.

## Metrics Categories

### 1. Latency Metrics (Percentiles)

Track response time distributions using percentiles instead of averages for accurate performance monitoring.

**Metrics:**
- `p50` - 50th percentile (median latency)
- `p90` - 90th percentile  
- `p95` - 95th percentile
- `p99` - 99th percentile

**Usage:**
```python
from tta_dev_primitives.observability import get_enhanced_metrics_collector

collector = get_enhanced_metrics_collector()

# Record execution
collector.record_execution(
    primitive_name="llm_call",
    duration_seconds=0.542,
    success=True
)

# Get percentiles
metrics = collector.get_all_metrics("llm_call")
print(f"p50: {metrics['percentiles']['p50']:.3f}s")
print(f"p95: {metrics['percentiles']['p95']:.3f}s")
print(f"p99: {metrics['percentiles']['p99']:.3f}s")
```

**Best Practices:**
- Use p95/p99 for SLO targets, not averages
- Monitor p99 for worst-case user experience
- Alert on p95 degradation for early warning
- Track p50 for typical performance

### 2. SLO Metrics

Monitor Service Level Objectives and error budgets for proactive incident management.

**Metrics:**
- `slo_compliance` - Ratio of requests meeting SLO (0.0-1.0)
- `error_budget_remaining` - Remaining error budget (0.0-1.0)
- `availability` - Success rate (0.0-1.0)
- `latency_compliance` - Requests within latency target (0.0-1.0)
- `total_requests` - Total request count
- `successful_requests` - Successful request count
- `latency_violations` - Requests exceeding latency SLO

**Usage:**
```python
from tta_dev_primitives.observability import (
    SLOConfig,
    get_enhanced_metrics_collector
)

collector = get_enhanced_metrics_collector()

# Configure SLO: 99% of requests under 1 second
slo = SLOConfig(
    target=0.99,                      # 99% target
    latency_threshold_seconds=1.0,    # < 1s latency
    availability_target=0.999         # 99.9% availability
)
collector.configure_slo("critical_workflow", slo)

# Record executions
collector.record_execution("critical_workflow", 0.8, True)
collector.record_execution("critical_workflow", 0.5, True)
collector.record_execution("critical_workflow", 1.2, True)  # SLO violation

# Check SLO status
metrics = collector.get_all_metrics("critical_workflow")
slo_status = metrics["slo"]

print(f"SLO Compliance: {slo_status['slo_compliance']:.2%}")
print(f"Error Budget: {slo_status['error_budget_remaining']:.2%}")
print(f"Latency Violations: {slo_status['latency_violations']}")
```

**Best Practices:**
- Set realistic SLO targets based on business requirements
- Monitor error budget burn rate
- Alert at 50% error budget consumed
- Review and adjust SLOs quarterly
- Use separate SLOs for critical vs non-critical paths

### 3. Throughput Metrics

Track request rate and concurrency for capacity planning.

**Metrics:**
- `total_requests` - Total executions
- `active_requests` - Currently executing requests
- `requests_per_second` - Request rate (60s window)

**Usage:**
```python
collector = get_enhanced_metrics_collector()

# Record request lifecycle
request_id = "req-12345"
collector.record_request_start("api_handler", request_id)

# ... process request ...

collector.record_request_end("api_handler", request_id)

# Get throughput stats
metrics = collector.get_all_metrics("api_handler")
throughput = metrics["throughput"]

print(f"RPS: {throughput['requests_per_second']:.2f}")
print(f"Active: {throughput['active_requests']}")
print(f"Total: {throughput['total_requests']}")
```

**Best Practices:**
- Monitor RPS trends for capacity planning
- Alert on sudden RPS spikes
- Track active_requests for concurrency limits
- Use for auto-scaling decisions

### 4. Cost Metrics

Track spending and savings for cost optimization.

**Metrics:**
- `total_cost` - Total cost in dollars
- `total_savings` - Total savings in dollars
- `net_cost` - Cost minus savings
- `savings_rate` - Percentage saved (0.0-1.0)
- `cost_breakdown` - Costs by category
- `savings_breakdown` - Savings by category

**Usage:**
```python
collector = get_enhanced_metrics_collector()

# Record cost for LLM call
collector.record_execution(
    primitive_name="gpt4_call",
    duration_seconds=1.2,
    success=True,
    cost=0.002  # $0.002
)

# Record savings from cache hit
collector.record_execution(
    primitive_name="gpt4_call",
    duration_seconds=0.05,
    success=True,
    savings=0.002  # Saved $0.002
)

# Get cost analysis
metrics = collector.get_all_metrics("gpt4_call")
cost_stats = metrics["cost"]

print(f"Total Cost: ${cost_stats['total_cost']:.4f}")
print(f"Total Savings: ${cost_stats['total_savings']:.4f}")
print(f"Savings Rate: {cost_stats['savings_rate']:.2%}")
print(f"Net Cost: ${cost_stats['net_cost']:.4f}")
```

**Best Practices:**
- Track cost by model, operation, and user tier
- Monitor savings rate for cache effectiveness
- Set cost budgets and alert on exceedance
- Use for pricing optimization
- Review monthly cost trends

---

## Prometheus Export

Export metrics to Prometheus for visualization and alerting.

### Available Prometheus Metrics

**Histograms:**
```
primitive_duration_seconds{primitive_name="...", primitive_type="..."}
```

**Gauges:**
```
primitive_active_requests{primitive_name="...", primitive_type="..."}
primitive_requests_per_second{primitive_name="...", primitive_type="..."}
primitive_slo_compliance{primitive_name="...", primitive_type="..."}
primitive_error_budget_remaining{primitive_name="...", primitive_type="..."}
```

**Counters:**
```
primitive_requests_total{primitive_name="...", primitive_type="...", status="success|failure"}
primitive_cost_total{primitive_name="...", primitive_type="...", category="..."}
primitive_cost_savings{primitive_name="...", primitive_type="...", category="..."}
```

### Usage

```python
from tta_dev_primitives.observability import get_prometheus_exporter

exporter = get_prometheus_exporter()

# Record metrics directly to Prometheus
exporter.record_execution(
    primitive_name="workflow_step",
    primitive_type="llm",
    duration_seconds=0.8,
    success=True
)

exporter.record_cost(
    primitive_name="workflow_step",
    primitive_type="llm",
    cost=0.002,
    category="gpt4"
)

# Or export from enhanced collector
exporter.export_metrics(primitive_type="workflow")
```

### Prometheus Queries

**95th percentile latency:**
```promql
histogram_quantile(0.95, sum(rate(primitive_duration_seconds_bucket[5m])) by (le, primitive_name))
```

**SLO compliance:**
```promql
primitive_slo_compliance{primitive_name="critical_workflow"}
```

**Request rate:**
```promql
rate(primitive_requests_total[5m])
```

**Error rate:**
```promql
rate(primitive_requests_total{status="failure"}[5m]) / rate(primitive_requests_total[5m])
```

**Cost per hour:**
```promql
rate(primitive_cost_total[1h]) * 3600
```

---

## Common Patterns

### Pattern 1: Comprehensive Monitoring

Monitor all aspects of a critical workflow:

```python
from tta_dev_primitives.observability import (
    SLOConfig,
    get_enhanced_metrics_collector,
    get_prometheus_exporter
)

collector = get_enhanced_metrics_collector()
exporter = get_prometheus_exporter()

# Configure SLO
slo = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
collector.configure_slo("critical_workflow", slo)

# Execute with comprehensive tracking
request_id = "req-123"
collector.record_request_start("critical_workflow", request_id)

try:
    # ... execute workflow ...
    duration = 0.8
    cost = 0.002
    
    collector.record_execution(
        primitive_name="critical_workflow",
        duration_seconds=duration,
        success=True,
        cost=cost,
        request_id=request_id
    )
    
    # Export to Prometheus
    exporter.record_execution("critical_workflow", "workflow", duration, True)
    exporter.record_cost("critical_workflow", "workflow", cost)
    
finally:
    collector.record_request_end("critical_workflow", request_id)
```

### Pattern 2: Cost Optimization Monitoring

Track cost and savings for optimization:

```python
# With caching
cache_key = f"query:{user_query}"
if cache_key in cache:
    # Cache hit - record savings
    collector.record_execution(
        primitive_name="llm_query",
        duration_seconds=0.05,  # Fast cache lookup
        success=True,
        savings=0.002  # Would have cost $0.002
    )
else:
    # Cache miss - record actual cost
    result = call_llm(user_query)
    cache[cache_key] = result
    collector.record_execution(
        primitive_name="llm_query",
        duration_seconds=1.2,
        success=True,
        cost=0.002
    )

# Analyze cache effectiveness
metrics = collector.get_all_metrics("llm_query")
print(f"Cache savings rate: {metrics['cost']['savings_rate']:.2%}")
```

### Pattern 3: SLO-Driven Routing

Route based on error budget:

```python
def route_request(query):
    metrics = collector.get_all_metrics("premium_model")
    slo = metrics.get("slo", {})
    
    # Check error budget
    if slo.get("error_budget_remaining", 1.0) < 0.2:
        # Low error budget - use cheaper, faster model
        return fallback_model(query)
    else:
        # Healthy error budget - use premium model
        return premium_model(query)
```

---

## Troubleshooting

### High p99 Latency

**Symptoms:** p99 much higher than p95

**Diagnosis:**
```python
metrics = collector.get_all_metrics("slow_primitive")
percentiles = metrics["percentiles"]

print(f"p50: {percentiles['p50']:.3f}s")
print(f"p95: {percentiles['p95']:.3f}s")
print(f"p99: {percentiles['p99']:.3f}s")

# Large gap indicates outliers
gap = percentiles['p99'] - percentiles['p95']
if gap > 1.0:
    print(f"⚠️ Large p95-p99 gap: {gap:.3f}s - investigate outliers")
```

**Solutions:**
- Add timeout protection
- Implement retry with backoff
- Use caching for repeated queries
- Profile slow requests

### SLO Violations

**Symptoms:** error_budget_remaining approaching 0

**Diagnosis:**
```python
slo = metrics["slo"]
print(f"Compliance: {slo['slo_compliance']:.2%}")
print(f"Budget: {slo['error_budget_remaining']:.2%}")
print(f"Violations: {slo['latency_violations']}")

# Calculate burn rate
if slo['error_budget_remaining'] < 0.5:
    print("⚠️ >50% error budget consumed")
```

**Solutions:**
- Add faster fallback paths
- Increase latency SLO if unrealistic
- Scale infrastructure
- Optimize slow operations

### High Costs

**Symptoms:** Cost growing faster than usage

**Diagnosis:**
```python
cost = metrics["cost"]
print(f"Savings rate: {cost['savings_rate']:.2%}")
print(f"Cost breakdown: {cost['cost_breakdown']}")

# Low savings rate indicates optimization opportunity
if cost['savings_rate'] < 0.3:
    print("⚠️ Low cache hit rate - optimize caching strategy")
```

**Solutions:**
- Implement/improve caching
- Use cheaper models for non-critical paths
- Batch similar requests
- Implement request deduplication

---

## Reference

### SLOConfig

```python
@dataclass
class SLOConfig:
    target: float                          # Target percentage (e.g., 0.99)
    latency_threshold_seconds: float       # Max latency in seconds
    availability_target: float | None      # Target success rate
    window_seconds: float                  # SLO window (default 30 days)
```

### EnhancedMetricsCollector API

```python
collector = get_enhanced_metrics_collector()

# Configure SLO
collector.configure_slo(primitive_name, slo_config)

# Record execution
collector.record_execution(
    primitive_name, duration_seconds, success,
    cost=None, savings=None, request_id=None
)

# Throughput tracking
collector.record_request_start(primitive_name, request_id)
collector.record_request_end(primitive_name, request_id)

# Get metrics
metrics = collector.get_all_metrics(primitive_name)  # Single primitive
all_metrics = collector.get_all_metrics()            # All primitives

# Reset metrics
collector.reset(primitive_name)  # Single primitive
collector.reset()                # All primitives
```

### PrometheusExporter API

```python
exporter = get_prometheus_exporter()

# Record metrics
exporter.record_execution(primitive_name, primitive_type, duration_seconds, success)
exporter.record_cost(primitive_name, primitive_type, cost, category)
exporter.record_savings(primitive_name, primitive_type, savings, category)

# Batch export from collector
exporter.export_metrics(primitive_type)

# Check cardinality
metrics_count = exporter.get_metrics_count()
```

---

## Next Steps

- [Prometheus Setup Guide](PROMETHEUS_SETUP.md) - Configure Prometheus scraping
- [Grafana Dashboards](../grafana/README.md) - Visualize metrics
- [Alert Rules](../alertmanager/README.md) - Set up alerting

---

**Last Updated:** 2025-10-29
