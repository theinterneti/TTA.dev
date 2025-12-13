# APM Integration for Workflow Primitives

OpenTelemetry-based Application Performance Monitoring for AI workflow primitives.

## Features

- ✅ **Automatic tracing** - Track execution flow through primitives
- ✅ **Metrics collection** - Counter and histogram metrics for performance
- ✅ **Prometheus export** - Native integration with existing Prometheus stack
- ✅ **Minimal overhead** - Gracefully degrades when APM is disabled
- ✅ **Easy to use** - Drop-in base class and decorators

## Installation

```bash
# Install with APM support
pip install tta-workflow-primitives[apm]

# Or install manually
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-prometheus
```

## Quick Start

### 1. Setup APM

```python
from tta_workflow_primitives.apm import setup_apm

# Setup with Prometheus export
setup_apm(
    service_name="my-ai-app",
    enable_prometheus=True
)
```

### 2. Use APM-Enabled Primitives

#### Option A: Inherit from APMWorkflowPrimitive

```python
from tta_workflow_primitives.apm.instrumented import APMWorkflowPrimitive
from tta_workflow_primitives.core.base import WorkflowContext

class MyPrimitive(APMWorkflowPrimitive):
    async def _execute_impl(self, input_data, context: WorkflowContext):
        # Your implementation
        return processed_data

# Automatically traced and metered!
primitive = MyPrimitive(name="my_processor")
result = await primitive.execute(data, context)
```

#### Option B: Use Decorators

```python
from tta_workflow_primitives.apm.decorators import trace_workflow, track_metric

@trace_workflow("data_processing")
@track_metric("processing_operations", "counter")
async def process_data(data):
    # Your code
    return processed_data
```

### 3. View Metrics

```bash
# Metrics available at:
curl http://localhost:9464/metrics

# Example metrics:
# primitive_processor_executions_total{status="success"} 42
# primitive_processor_duration_milliseconds_bucket{le="100"} 38
# primitive_processor_duration_milliseconds_bucket{le="500"} 42
```

## What Gets Tracked

### Traces
- Execution flow through primitives
- Parent-child relationships
- Timing information
- Error details

### Metrics
- **Execution counter**: Number of executions (success/error)
- **Duration histogram**: Execution time distribution
- **Error rates**: Failures by error type
- **Throughput**: Operations per second

## Architecture

```
Your Application
       ↓
APMWorkflowPrimitive
       ↓
OpenTelemetry SDK
       ↓
Prometheus Exporter → Prometheus → Grafana
```

## Examples

### Workflow Composition with APM

```python
from tta_workflow_primitives.apm import setup_apm
from tta_workflow_primitives.apm.instrumented import APMWorkflowPrimitive
from tta_workflow_primitives.core.base import WorkflowContext

# Setup APM
setup_apm("my-workflow")

# Create primitives
class Step1(APMWorkflowPrimitive):
    async def _execute_impl(self, data, context):
        return {"step1": "done", **data}

class Step2(APMWorkflowPrimitive):
    async def _execute_impl(self, data, context):
        return {"step2": "done", **data}

# Compose workflow
workflow = Step1() >> Step2()

# Execute (automatically tracked!)
context = WorkflowContext(workflow_id="wf-001")
result = await workflow.execute({"input": "data"}, context)

# Traces show: Step1 → Step2
# Metrics track both primitives
```

### Custom Metrics

```python
from tta_workflow_primitives.apm import get_meter

meter = get_meter(__name__)

# Create custom counter
api_calls = meter.create_counter(
    "api_calls_total",
    description="Total API calls"
)

# Increment
api_calls.add(1, {"endpoint": "/predict", "model": "gpt-4"})

# Create histogram
latency = meter.create_histogram(
    "api_latency_ms",
    description="API latency in milliseconds"
)

# Record value
latency.record(123.45, {"endpoint": "/predict"})
```

## Integration with Prometheus/Grafana

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-workflows'
    static_configs:
      - targets: ['localhost:9464']
```

### Example Grafana Queries

```promql
# Execution rate
rate(primitive_processor_executions_total[5m])

# P95 latency
histogram_quantile(0.95,
  rate(primitive_processor_duration_milliseconds_bucket[5m]))

# Error rate
rate(primitive_processor_executions_total{status="error"}[5m]) /
rate(primitive_processor_executions_total[5m])
```

## Performance Impact

APM adds minimal overhead:
- ~1-2ms per traced operation
- ~100KB memory per 10,000 spans
- Async export doesn't block execution
- Gracefully disables if not configured

## Best Practices

### 1. Name Your Primitives

```python
# Good
processor = DataProcessor(name="user_data_processor")

# Bad
processor = DataProcessor()  # Uses class name, less specific
```

### 2. Add Context

```python
context = WorkflowContext(
    workflow_id="unique-id",
    session_id="user-session",
    metadata={"user_tier": "premium"}
)
```

### 3. Use Appropriate Metric Types

```python
# Counter: Things that only go up
executions_counter = meter.create_counter("executions")

# Histogram: Distributions (latency, sizes)
duration_histogram = meter.create_histogram("duration_ms")
```

### 4. Add Attributes to Spans

```python
@trace_workflow("process", attributes={"version": "2.0"})
async def process(data):
    return result
```

## Troubleshooting

### APM Not Working

```python
from tta_workflow_primitives.apm import is_apm_enabled

if not is_apm_enabled():
    print("APM not enabled - call setup_apm() first")
```

### No Metrics Visible

1. Check Prometheus is scraping: `http://localhost:9464/metrics`
2. Verify port is accessible
3. Check firewall rules

### High Overhead

```python
# Reduce sampling
setup_apm(
    service_name="my-app",
    sample_rate=0.1  # Sample 10% of traces
)
```

## What's Next

- ✅ Phase 1: APM Integration (Current)
- ⏳ Phase 2: Context7 Integration
- ⏳ Phase 3: Intelligent Runtime
- ⏳ Phase 4: Auto-optimization

See `APM_CONTEXT7_RUNTIME_PACKAGE.md` for the full roadmap.

## Resources

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Prometheus](https://prometheus.io/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [APM Best Practices](https://opentelemetry.io/docs/concepts/signals/)


---
**Logseq:** [[TTA.dev/Platform/Primitives/Src/Tta_dev_primitives/Apm/Readme]]
