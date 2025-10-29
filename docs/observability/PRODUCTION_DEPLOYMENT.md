# Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-29  
**Status:** Production Ready

This guide covers deploying TTA.dev observability with Phase 4 production hardening features including sampling, optimization, and operational tooling.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Sampling Strategy](#sampling-strategy)
4. [Metric Cardinality Controls](#metric-cardinality-controls)
5. [Storage Optimization](#storage-optimization)
6. [Health Monitoring](#health-monitoring)
7. [Performance Tuning](#performance-tuning)
8. [Deployment Steps](#deployment-steps)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- Python 3.11 or higher
- Memory: Minimum 2GB RAM (4GB recommended for production)
- CPU: 2+ cores recommended
- Network: Low latency connection to observability backend

### Dependencies

```bash
# Install with all observability features
pip install tta-dev-primitives[apm,tracing]

# Or with uv
uv pip install "tta-dev-primitives[apm,tracing]"
```

### Environment Variables

Set these environment variables for production:

```bash
export ENVIRONMENT=production
export SERVICE_NAME=tta-api
export SERVICE_VERSION=1.0.0
```

---

## Configuration

### Environment-Based Configuration

TTA.dev provides pre-configured settings for different environments:

```python
from tta_dev_primitives.observability import ObservabilityConfig

# Production configuration (automatic when ENVIRONMENT=production)
config = ObservabilityConfig.from_environment("production")
```

**Production defaults:**
- **Sampling rate:** 5% (0.05)
- **Adaptive sampling:** Enabled
- **Cardinality limit:** 100 unique values per label
- **Trace TTL:** 7 days
- **Compression:** Enabled

### Custom Configuration

For fine-tuned control:

```python
from tta_dev_primitives.observability import (
    ObservabilityConfig,
    TracingConfig,
    SamplingConfig,
    MetricsConfig,
    StorageConfig,
    set_observability_config,
)

config = ObservabilityConfig(
    environment="production",
    service_name="tta-api",
    service_version="1.0.0",
    tracing=TracingConfig(
        enabled=True,
        sampling=SamplingConfig(
            default_rate=0.05,  # 5% base sampling
            always_sample_errors=True,
            always_sample_slow=True,
            slow_threshold_ms=1000.0,
            adaptive_enabled=True,
            adaptive_min_rate=0.01,  # Never below 1%
            adaptive_max_rate=0.2,   # Never above 20%
            adaptive_target_overhead=0.02,  # Target 2% overhead
        ),
        export_interval_seconds=60.0,
        batch_size=512,
    ),
    metrics=MetricsConfig(
        enabled=True,
        max_label_values=100,
        hash_high_cardinality=True,
        export_interval_seconds=60.0,
    ),
    storage=StorageConfig(
        trace_ttl_days=7,
        compression_enabled=True,
        compression_level=6,
    ),
)

set_observability_config(config)
```

---

## Sampling Strategy

### Head-Based Sampling

Initial sampling decision at trace start:

```python
from tta_dev_primitives.observability import CompositeSampler, SamplingConfig

# Configure sampler
config = SamplingConfig(default_rate=0.05)  # 5% sampling
sampler = CompositeSampler(config)

# Make sampling decision
decision = sampler.should_sample_head(
    trace_id=context.correlation_id,
    current_overhead=0.02,  # Optional: for adaptive sampling
)

if decision.decision == SamplingDecision.SAMPLE:
    # Enable tracing for this request
    pass
```

### Tail-Based Sampling

Override head decision based on actual execution:

```python
# After trace completion
tail_decision = sampler.should_sample_tail(
    trace_id=context.correlation_id,
    has_error=execution_failed,
    duration_ms=elapsed_time,
    head_decision=head_decision,
)

# Tail-based rules:
# - Always sample if has_error=True
# - Always sample if duration_ms > slow_threshold_ms
# - Otherwise, preserve head decision
```

### Adaptive Sampling

Automatically adjusts rate based on system load:

```python
from tta_dev_primitives.observability import AdaptiveSampler

sampler = AdaptiveSampler(
    base_rate=0.1,
    min_rate=0.01,
    max_rate=0.5,
    target_overhead=0.02,  # 2% target overhead
    adjustment_interval=60.0,  # Adjust every 60 seconds
)

# Sampler automatically adjusts based on overhead measurements
decision = sampler.should_sample(
    trace_id="trace-123",
    current_overhead=0.035,  # Current overhead from monitoring
)

# Check current rate
stats = sampler.get_stats()
print(f"Current rate: {stats['current_rate']}")
```

### Sampling Rate Guidelines

| Environment | Base Rate | Use Case |
|-------------|-----------|----------|
| Development | 100% (1.0) | Full visibility for debugging |
| Staging | 20% (0.2) | Representative sampling |
| Production (low volume) | 10% (0.1) | <100K requests/day |
| Production (high volume) | 5% (0.05) | >100K requests/day |
| Production (very high volume) | 1% (0.01) | >1M requests/day |

---

## Metric Cardinality Controls

### Understanding Cardinality

High-cardinality labels (e.g., user IDs, trace IDs) can cause:
- Increased memory usage
- Slower query performance
- Higher storage costs

### Configuring Limits

```python
from tta_dev_primitives.observability import MetricsConfig

config = MetricsConfig(
    max_label_values=100,  # Max unique values per label
    hash_high_cardinality=True,  # Hash values beyond limit
    export_interval_seconds=60.0,
)
```

### Monitoring Cardinality

```python
from tta_dev_primitives.observability import get_metrics_collector

collector = get_metrics_collector()
stats = collector.get_cardinality_stats()

print(f"Total unique labels: {stats['total_labels']}")
print(f"Dropped labels: {stats['dropped_labels']}")

# Alert if cardinality limit reached
if stats['dropped_labels']:
    print(f"WARNING: Cardinality limit reached for: {stats['dropped_labels']}")
```

### Best Practices

1. **Avoid high-cardinality labels:**
   - ❌ User IDs, trace IDs, timestamps
   - ✅ Primitive names, error types, environments

2. **Use label hashing for necessary high-cardinality:**
   ```python
   config = MetricsConfig(hash_high_cardinality=True)
   ```

3. **Monitor cardinality regularly:**
   ```python
   # Set up monitoring
   stats = collector.get_cardinality_stats()
   if stats['total_labels'] > 800:  # 80% of limit
       alert("Approaching cardinality limit")
   ```

---

## Storage Optimization

### Trace Retention

Configure retention based on compliance and cost:

```python
from tta_dev_primitives.observability import StorageConfig

config = StorageConfig(
    trace_ttl_days=7,  # Keep traces for 7 days
    metric_ttl_days=30,  # Keep metrics for 30 days
)
```

### Compression

Enable compression to reduce storage costs:

```python
config = StorageConfig(
    compression_enabled=True,
    compression_level=6,  # 1=fast, 9=best compression
)
```

**Compression levels:**
- Level 1-3: Fast compression, lower ratio (~40% reduction)
- Level 4-6: Balanced (recommended) (~60% reduction)
- Level 7-9: Best compression, slower (~70% reduction)

### Storage Estimates

| Volume | Daily Traces | Storage/Day (uncompressed) | Storage/Day (compressed) |
|--------|--------------|----------------------------|--------------------------|
| Low | 10K | 100 MB | 40 MB |
| Medium | 100K | 1 GB | 400 MB |
| High | 1M | 10 GB | 4 GB |
| Very High | 10M | 100 GB | 40 GB |

*With 5% sampling rate and compression level 6*

---

## Health Monitoring

### Health Check Endpoint

```python
from tta_dev_primitives.observability import get_health_checker

health = get_health_checker()

# Get health status
result = health.check_health()

print(f"Status: {result.status.value}")  # healthy, degraded, unhealthy
print(f"Message: {result.message}")
print(f"Details: {result.details}")
```

### HTTP Endpoint Example

```python
from fastapi import FastAPI
from tta_dev_primitives.observability import get_health_checker

app = FastAPI()

@app.get("/health")
async def health_check():
    health = get_health_checker()
    result = health.check_health()
    
    return {
        "status": result.status.value,
        "message": result.message,
        "details": result.details,
        "timestamp": result.timestamp,
    }

@app.get("/health/full")
async def full_status():
    health = get_health_checker()
    return health.get_full_status()

@app.get("/health/sampling")
async def sampling_status():
    health = get_health_checker()
    return health.get_sampling_status()

@app.get("/health/metrics")
async def metrics_status():
    health = get_health_checker()
    return health.get_metrics_status()
```

### Monitoring Alerts

Set up alerts for:

1. **Unhealthy status:**
   ```python
   if result.status == HealthStatus.UNHEALTHY:
       alert("Observability system unhealthy")
   ```

2. **High cardinality:**
   ```python
   metrics_status = health.get_metrics_status()
   if metrics_status['cardinality']['dropped_labels']:
       alert("Cardinality limit reached")
   ```

3. **Low sampling rate:**
   ```python
   sampling_status = health.get_sampling_status()
   if sampling_status['sampling_rate'] < 0.01:
       alert("Sampling rate very low (<1%)")
   ```

---

## Performance Tuning

### Target Performance Metrics

- **Observability overhead:** <2% CPU, <1% memory
- **Trace export latency:** <100ms p99
- **Metric export latency:** <50ms p99

### Async Export

Enable async export for better performance:

```python
config = ObservabilityConfig(
    async_export=True,
    max_export_workers=4,
)
```

### Batch Configuration

Tune batch sizes for your volume:

```python
config = TracingConfig(
    batch_size=512,  # Higher for high volume
    max_queue_size=2048,
    export_interval_seconds=60.0,
)
```

**Guidelines:**
- Low volume (<1K req/s): batch_size=256
- Medium volume (1K-10K req/s): batch_size=512
- High volume (>10K req/s): batch_size=1024

---

## Deployment Steps

### 1. Pre-Deployment

```bash
# Verify configuration
python -c "
from tta_dev_primitives.observability import ObservabilityConfig
config = ObservabilityConfig.from_environment('production')
print(config.to_dict())
"

# Run tests
pytest tests/test_sampling.py tests/test_observability_config.py -v
```

### 2. Deployment

```python
# In your application startup
from tta_dev_primitives.observability import (
    ObservabilityConfig,
    set_observability_config,
)

# Load production config
config = ObservabilityConfig.from_environment("production")
set_observability_config(config)

# Verify
from tta_dev_primitives.observability import get_health_checker
health = get_health_checker()
result = health.check_health()

if result.status != HealthStatus.HEALTHY:
    raise RuntimeError(f"Observability unhealthy: {result.message}")

print("✅ Observability initialized successfully")
```

### 3. Verification

See [Verification](#verification) section below.

### 4. Monitoring

Set up monitoring dashboards for:
- Sampling rate over time
- Cardinality metrics
- Health check status
- Export latency

---

## Verification

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "All observability systems operational",
  "details": {
    "config_loaded": true,
    "environment": "production",
    "metrics_collector": "available",
    "tracing_available": true,
    "uptime_seconds": 120.5
  }
}
```

### 2. Sampling Verification

```python
from tta_dev_primitives.observability import get_health_checker

health = get_health_checker()
status = health.get_sampling_status()

assert status['enabled'] == True
assert 0.0 < status['sampling_rate'] <= 1.0
assert status['always_sample_errors'] == True

print("✅ Sampling configured correctly")
```

### 3. Metrics Verification

```python
from tta_dev_primitives.observability import get_metrics_collector

collector = get_metrics_collector()

# Record test execution
collector.record_execution("test_primitive", 100.0, success=True)

# Verify
metrics = collector.get_metrics("test_primitive")
assert metrics['total_executions'] == 1

print("✅ Metrics collection working")
```

### 4. Load Testing

```bash
# Run load test (example)
ab -n 10000 -c 100 http://localhost:8000/api/endpoint

# Check overhead
python -c "
from tta_dev_primitives.observability import get_health_checker
health = get_health_checker()
status = health.get_full_status()
print(f\"Sampling rate: {status['sampling']['sampling_rate']}\")
print(f\"Total executions: {status['metrics']['total_executions']}\")
"
```

---

## Troubleshooting

### Issue: High Overhead

**Symptoms:** CPU usage >5%, memory growth

**Solutions:**
1. Reduce sampling rate:
   ```python
   config.tracing.sampling.default_rate = 0.01  # 1%
   ```

2. Enable adaptive sampling:
   ```python
   config.tracing.sampling.adaptive_enabled = True
   config.tracing.sampling.adaptive_target_overhead = 0.01  # 1%
   ```

3. Increase export interval:
   ```python
   config.tracing.export_interval_seconds = 120.0  # 2 minutes
   ```

### Issue: Cardinality Explosion

**Symptoms:** Dropped labels, slow queries

**Solutions:**
1. Enable hashing:
   ```python
   config.metrics.hash_high_cardinality = True
   ```

2. Increase limit (with caution):
   ```python
   config.metrics.max_label_values = 200
   ```

3. Review label usage:
   ```python
   stats = collector.get_cardinality_stats()
   print(stats['label_cardinality'])
   ```

### Issue: Missing Traces

**Symptoms:** Expected traces not appearing

**Solutions:**
1. Check sampling rate:
   ```python
   status = health.get_sampling_status()
   print(f"Current rate: {status['sampling_rate']}")
   ```

2. Verify tail-based sampling:
   ```python
   # Errors should always be sampled
   assert status['always_sample_errors'] == True
   ```

3. Check export status:
   ```bash
   curl http://localhost:8000/health/full
   ```

### Issue: Storage Growth

**Symptoms:** Disk usage increasing rapidly

**Solutions:**
1. Reduce retention:
   ```python
   config.storage.trace_ttl_days = 3
   ```

2. Enable compression:
   ```python
   config.storage.compression_enabled = True
   config.storage.compression_level = 9  # Best compression
   ```

3. Reduce sampling rate:
   ```python
   config.tracing.sampling.default_rate = 0.02  # 2%
   ```

---

## Performance Benchmarks

### Expected Overhead

| Sampling Rate | CPU Overhead | Memory Overhead | Storage/Day (1M req) |
|---------------|--------------|-----------------|----------------------|
| 1% (0.01) | <0.5% | <0.2% | 400 MB |
| 5% (0.05) | <1.0% | <0.5% | 2 GB |
| 10% (0.1) | <1.5% | <0.8% | 4 GB |
| 20% (0.2) | <2.0% | <1.0% | 8 GB |

*With compression enabled, batch_size=512*

---

## Additional Resources

- [IMPLEMENTATION_GUIDE.md](../observability/IMPLEMENTATION_GUIDE.md) - Detailed implementation guide
- [OBSERVABILITY_ASSESSMENT.md](../observability/OBSERVABILITY_ASSESSMENT.md) - Assessment and design
- [EXECUTIVE_SUMMARY.md](../observability/EXECUTIVE_SUMMARY.md) - Executive summary

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review health check output: `curl /health/full`
3. Open an issue on GitHub

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0  
**Status:** Production Ready
