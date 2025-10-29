# Observability Configuration Reference

**Version:** 1.0.0  
**Last Updated:** 2025-10-29

Complete reference for configuring TTA.dev observability with Phase 4 production hardening features.

---

## Table of Contents

1. [Overview](#overview)
2. [SamplingConfig](#samplingconfig)
3. [TracingConfig](#tracingconfig)
4. [MetricsConfig](#metricsconfig)
5. [StorageConfig](#storageconfig)
6. [ObservabilityConfig](#observabilityconfig)
7. [Environment Presets](#environment-presets)
8. [Configuration Examples](#configuration-examples)

---

## Overview

TTA.dev observability is configured using Pydantic models that provide validation and type safety. Configuration can be:

- **Environment-based:** Use presets for dev/staging/production
- **Custom:** Fine-tune all parameters
- **Runtime:** Update configuration without restart (some settings)

### Basic Usage

```python
from tta_dev_primitives.observability import (
    ObservabilityConfig,
    set_observability_config,
)

# Use environment preset
config = ObservabilityConfig.from_environment("production")
set_observability_config(config)
```

---

## SamplingConfig

Controls trace sampling strategies.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `default_rate` | `float` | `0.1` | Base sampling rate (0.0-1.0). 0.1 = 10% of traces sampled |
| `always_sample_errors` | `bool` | `True` | Always sample traces with errors (tail-based) |
| `always_sample_slow` | `bool` | `True` | Always sample slow traces (tail-based) |
| `slow_threshold_ms` | `float` | `1000.0` | Threshold in milliseconds for slow traces |
| `adaptive_enabled` | `bool` | `False` | Enable adaptive sampling based on load |
| `adaptive_min_rate` | `float` | `0.01` | Minimum sampling rate for adaptive (1%) |
| `adaptive_max_rate` | `float` | `1.0` | Maximum sampling rate for adaptive (100%) |
| `adaptive_target_overhead` | `float` | `0.02` | Target overhead percentage (0.02 = 2%) |

### Example

```python
from tta_dev_primitives.observability import SamplingConfig

config = SamplingConfig(
    default_rate=0.05,  # 5% base sampling
    always_sample_errors=True,  # Always sample errors
    always_sample_slow=True,  # Always sample slow traces
    slow_threshold_ms=1000.0,  # >1s is slow
    adaptive_enabled=True,  # Enable adaptive
    adaptive_min_rate=0.01,  # Never below 1%
    adaptive_max_rate=0.2,  # Never above 20%
    adaptive_target_overhead=0.02,  # Target 2% overhead
)
```

### Validation

- `default_rate`: Must be between 0.0 and 1.0
- `slow_threshold_ms`: Must be >= 0.0
- `adaptive_min_rate` <= `adaptive_max_rate`
- All rate parameters must be between 0.0 and 1.0

### Guidelines

| Environment | Recommended `default_rate` |
|-------------|----------------------------|
| Development | 1.0 (100%) |
| Staging | 0.2 (20%) |
| Production (low volume) | 0.1 (10%) |
| Production (high volume) | 0.05 (5%) |
| Production (very high volume) | 0.01 (1%) |

---

## TracingConfig

Controls distributed tracing configuration.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `bool` | `True` | Enable distributed tracing |
| `sampling` | `SamplingConfig` | See SamplingConfig | Sampling configuration |
| `export_interval_seconds` | `float` | `30.0` | Interval between trace exports |
| `batch_size` | `int` | `512` | Number of spans to batch before export |
| `max_queue_size` | `int` | `2048` | Maximum span queue size |

### Example

```python
from tta_dev_primitives.observability import TracingConfig, SamplingConfig

config = TracingConfig(
    enabled=True,
    sampling=SamplingConfig(default_rate=0.05),
    export_interval_seconds=60.0,  # Export every minute
    batch_size=512,  # Batch 512 spans
    max_queue_size=2048,  # Queue up to 2048 spans
)
```

### Validation

- `export_interval_seconds`: Must be >= 1.0
- `batch_size`: Must be >= 1
- `max_queue_size`: Must be >= 1

### Tuning Guidelines

#### Low Volume (<1K req/s)
```python
TracingConfig(
    export_interval_seconds=30.0,
    batch_size=256,
    max_queue_size=1024,
)
```

#### Medium Volume (1K-10K req/s)
```python
TracingConfig(
    export_interval_seconds=60.0,
    batch_size=512,
    max_queue_size=2048,
)
```

#### High Volume (>10K req/s)
```python
TracingConfig(
    export_interval_seconds=60.0,
    batch_size=1024,
    max_queue_size=4096,
)
```

---

## MetricsConfig

Controls metrics collection and cardinality.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `bool` | `True` | Enable metrics collection |
| `max_label_values` | `int` | `100` | Maximum unique values per label key |
| `hash_high_cardinality` | `bool` | `True` | Hash high-cardinality values |
| `export_interval_seconds` | `float` | `60.0` | Interval between metric exports |
| `batch_size` | `int` | `100` | Number of metrics to batch |

### Example

```python
from tta_dev_primitives.observability import MetricsConfig

config = MetricsConfig(
    enabled=True,
    max_label_values=100,  # Limit to 100 unique values
    hash_high_cardinality=True,  # Hash beyond limit
    export_interval_seconds=60.0,  # Export every minute
    batch_size=100,  # Batch 100 metrics
)
```

### Validation

- `max_label_values`: Must be >= 1
- `export_interval_seconds`: Must be >= 1.0
- `batch_size`: Must be >= 1

### Cardinality Guidelines

| Environment | `max_label_values` | `hash_high_cardinality` |
|-------------|--------------------|-------------------------|
| Development | 1000 | False (readable) |
| Staging | 200 | True |
| Production | 100 | True |

**Important:** Keep `max_label_values` < 1000 to avoid performance issues.

---

## StorageConfig

Controls trace and metric storage.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trace_ttl_days` | `int` | `7` | Trace retention in days |
| `metric_ttl_days` | `int` | `30` | Metric retention in days |
| `compression_enabled` | `bool` | `True` | Enable data compression |
| `compression_level` | `int` | `6` | Compression level (1-9) |

### Example

```python
from tta_dev_primitives.observability import StorageConfig

config = StorageConfig(
    trace_ttl_days=7,  # Keep traces for 7 days
    metric_ttl_days=30,  # Keep metrics for 30 days
    compression_enabled=True,  # Enable compression
    compression_level=6,  # Balanced compression
)
```

### Validation

- `trace_ttl_days`: Must be >= 1
- `metric_ttl_days`: Must be >= 1
- `compression_level`: Must be 1-9

### Compression Levels

| Level | Description | Ratio | Speed |
|-------|-------------|-------|-------|
| 1-3 | Fast | ~40% | Fast |
| 4-6 | Balanced (recommended) | ~60% | Medium |
| 7-9 | Best | ~70% | Slow |

---

## ObservabilityConfig

Main configuration combining all settings.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `environment` | `str` | `"development"` | Environment name |
| `service_name` | `str` | `"tta"` | Service name |
| `service_version` | `str` | `"0.1.0"` | Service version |
| `tracing` | `TracingConfig` | Default | Tracing configuration |
| `metrics` | `MetricsConfig` | Default | Metrics configuration |
| `storage` | `StorageConfig` | Default | Storage configuration |
| `async_export` | `bool` | `True` | Use async export |
| `max_export_workers` | `int` | `4` | Max concurrent export workers |

### Example

```python
from tta_dev_primitives.observability import ObservabilityConfig

config = ObservabilityConfig(
    environment="production",
    service_name="tta-api",
    service_version="1.0.0",
    tracing=TracingConfig(...),
    metrics=MetricsConfig(...),
    storage=StorageConfig(...),
    async_export=True,
    max_export_workers=4,
)
```

### Methods

#### `from_environment(environment: str) -> ObservabilityConfig`

Create configuration from environment preset.

```python
# Development preset
config = ObservabilityConfig.from_environment("development")

# Staging preset
config = ObservabilityConfig.from_environment("staging")

# Production preset
config = ObservabilityConfig.from_environment("production")
```

#### `to_dict() -> dict`

Convert configuration to dictionary.

```python
config = ObservabilityConfig.from_environment("production")
config_dict = config.to_dict()
```

---

## Environment Presets

### Development

**Use Case:** Local development and debugging

```python
ObservabilityConfig(
    environment="development",
    tracing=TracingConfig(
        sampling=SamplingConfig(
            default_rate=1.0,  # 100% sampling
            adaptive_enabled=False,
        ),
        export_interval_seconds=10.0,  # Fast export
    ),
    metrics=MetricsConfig(
        max_label_values=1000,  # High limit
        hash_high_cardinality=False,  # Keep readable
    ),
    storage=StorageConfig(
        trace_ttl_days=1,  # Short retention
    ),
)
```

**Characteristics:**
- ✅ Full visibility (100% sampling)
- ✅ Fast feedback (10s export interval)
- ✅ Readable labels (no hashing)
- ⚠️ High overhead (not for production)

### Staging

**Use Case:** Pre-production testing

```python
ObservabilityConfig(
    environment="staging",
    tracing=TracingConfig(
        sampling=SamplingConfig(
            default_rate=0.2,  # 20% sampling
            adaptive_enabled=True,
        ),
        export_interval_seconds=30.0,
    ),
    metrics=MetricsConfig(
        max_label_values=200,  # Moderate limit
        hash_high_cardinality=True,
    ),
    storage=StorageConfig(
        trace_ttl_days=3,  # Medium retention
    ),
)
```

**Characteristics:**
- ✅ Representative sampling (20%)
- ✅ Adaptive enabled
- ✅ Cardinality controlled
- ✅ Moderate retention

### Production

**Use Case:** Production deployment

```python
ObservabilityConfig(
    environment="production",
    tracing=TracingConfig(
        sampling=SamplingConfig(
            default_rate=0.05,  # 5% sampling
            adaptive_enabled=True,
            adaptive_min_rate=0.01,  # 1% minimum
            adaptive_max_rate=0.2,  # 20% maximum
        ),
        export_interval_seconds=60.0,  # Less frequent export
    ),
    metrics=MetricsConfig(
        max_label_values=100,  # Strict limit
        hash_high_cardinality=True,
    ),
    storage=StorageConfig(
        trace_ttl_days=7,  # Standard retention
        compression_enabled=True,
    ),
)
```

**Characteristics:**
- ✅ Low overhead (<2%)
- ✅ Cost-efficient (5% sampling)
- ✅ Adaptive to load
- ✅ Cardinality controlled
- ✅ Compression enabled

---

## Configuration Examples

### Minimal Configuration

```python
from tta_dev_primitives.observability import (
    ObservabilityConfig,
    set_observability_config,
)

# Use environment preset
config = ObservabilityConfig.from_environment("production")
set_observability_config(config)
```

### Custom Configuration

```python
from tta_dev_primitives.observability import (
    ObservabilityConfig,
    TracingConfig,
    SamplingConfig,
    MetricsConfig,
    StorageConfig,
)

config = ObservabilityConfig(
    environment="custom",
    service_name="my-service",
    service_version="2.0.0",
    tracing=TracingConfig(
        enabled=True,
        sampling=SamplingConfig(
            default_rate=0.1,
            always_sample_errors=True,
            adaptive_enabled=True,
        ),
    ),
    metrics=MetricsConfig(
        max_label_values=150,
        hash_high_cardinality=True,
    ),
    storage=StorageConfig(
        trace_ttl_days=14,
        compression_enabled=True,
    ),
)
```

### Environment Variable Configuration

```python
import os
from tta_dev_primitives.observability import ObservabilityConfig

# Read from environment
env = os.getenv("ENVIRONMENT", "development")
service = os.getenv("SERVICE_NAME", "tta")
version = os.getenv("SERVICE_VERSION", "0.1.0")

config = ObservabilityConfig.from_environment(env)
config.service_name = service
config.service_version = version
```

### Dynamic Configuration Update

```python
from tta_dev_primitives.observability import (
    get_observability_config,
    set_observability_config,
)

# Get current config
config = get_observability_config()

# Modify sampling rate
config.tracing.sampling.default_rate = 0.02  # Reduce to 2%

# Apply updated config
set_observability_config(config)
```

---

## Validation

All configuration uses Pydantic for validation:

```python
from tta_dev_primitives.observability import SamplingConfig
from pydantic import ValidationError

try:
    # This will raise ValidationError
    config = SamplingConfig(default_rate=1.5)  # Invalid: > 1.0
except ValidationError as e:
    print(f"Validation error: {e}")
```

---

## Best Practices

1. **Start with environment presets:**
   ```python
   config = ObservabilityConfig.from_environment("production")
   ```

2. **Tune sampling for your volume:**
   - <100K req/day: 10% sampling
   - 100K-1M req/day: 5% sampling
   - >1M req/day: 1-2% sampling

3. **Always sample errors:**
   ```python
   config.tracing.sampling.always_sample_errors = True
   ```

4. **Enable adaptive sampling in production:**
   ```python
   config.tracing.sampling.adaptive_enabled = True
   ```

5. **Control cardinality:**
   ```python
   config.metrics.max_label_values = 100
   config.metrics.hash_high_cardinality = True
   ```

---

## See Also

- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Deployment guide
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Implementation details
- [OBSERVABILITY_ASSESSMENT.md](OBSERVABILITY_ASSESSMENT.md) - Architecture and design

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0
