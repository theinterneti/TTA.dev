# TTA.dev Observability Implementation Quickstart

**Fast-track guide to implement the 3-pillar observability strategy**

Related Documents:
- Full Strategy: [TTA_OBSERVABILITY_STRATEGY.md](./TTA_OBSERVABILITY_STRATEGY.md)
- Detailed Implementation: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)

---

## Quick Implementation Path

### Phase 1: Semantic Tracing (Day 1-2)

**Goal:** Make traces human-readable with semantic naming and rich attributes.

**Quick Wins:**

1. **Update span names to semantic format:**
   ```python
   # Before: span_name = f"primitive.{self.name}"
   # After:  span_name = f"primitive.{self.primitive_type}.{self.action}"

   # Examples:
   "primitive.sequential.execute"
   "primitive.router.route_decision"
   "llm.openai.generate"
   "cache.redis.lookup"
   ```

2. **Add WorkflowContext fields:**
   ```python
   # Add to core/base.py WorkflowContext:
   agent_id: str | None = None
   agent_type: str | None = None
   workflow_name: str | None = None
   llm_provider: str | None = None
   llm_model_name: str | None = None
   ```

3. **Set attributes in InstrumentedPrimitive:**
   ```python
   # In execute() method:
   span.set_attribute("agent.id", context.agent_id or "unknown")
   span.set_attribute("workflow.name", context.workflow_name or "unknown")
   span.set_attribute("primitive.type", self.primitive_type)
   ```

**Test:**
```bash
uv run python examples/observability_demo.py
# Check Jaeger: http://localhost:16686
# Verify semantic span names appear
```

---

### Phase 2: Core Metrics (Day 3-4)

**Goal:** Get the 7 essential metrics flowing to Prometheus.

**Quick Implementation:**

1. **Create metrics module** (`observability/metrics_v2.py`):
   ```python
   from opentelemetry import metrics

   meter = metrics.get_meter("tta.primitives")

   execution_counter = meter.create_counter(
       "primitive.execution.count",
       description="Total executions",
       unit="1",
   )

   duration_histogram = meter.create_histogram(
       "primitive.execution.duration",
       description="Execution duration",
       unit="ms",
   )
   ```

2. **Record metrics in InstrumentedPrimitive:**
   ```python
   # In execute() after execution:
   metrics = get_metrics_collector()
   metrics.record_execution(
       primitive_name=self.name,
       primitive_type=self.primitive_type,
       duration_ms=duration_ms,
       status="success" if no error else "error",
   )
   ```

**Test:**
```bash
# Run demo
uv run python examples/observability_demo.py

# Check Prometheus: http://localhost:9090
# Run query: primitive_execution_count
# Should see data
```

---

### Phase 3: Basic Dashboard (Day 5)

**Goal:** Create a simple Grafana dashboard showing system health.

**Quick Dashboard Panels:**

1. **Total Executions:**
   ```promql
   sum(rate(primitive_execution_count[5m]))
   ```

2. **Error Rate:**
   ```promql
   sum(rate(primitive_execution_count{execution_status="error"}[5m])) /
   sum(rate(primitive_execution_count[5m])) * 100
   ```

3. **P95 Latency:**
   ```promql
   histogram_quantile(0.95, primitive_execution_duration_bucket)
   ```

4. **Top 5 Slowest Primitives:**
   ```promql
   topk(5, histogram_quantile(0.95, sum by (primitive_name, le) (primitive_execution_duration_bucket)))
   ```

**Import:**
- Grafana UI → Dashboards → Import
- Paste JSON from `configs/grafana/dashboards/`

---

## File Checklist

**Files to create:**
- [ ] `src/tta_dev_primitives/observability/metrics_v2.py` - Metrics definitions
- [ ] `configs/grafana/dashboards/tta_basic.json` - Basic dashboard

**Files to update:**
- [ ] `src/tta_dev_primitives/core/base.py` - Add WorkflowContext fields
- [ ] `src/tta_dev_primitives/observability/instrumented_primitive.py` - Semantic naming + metrics
- [ ] `src/tta_dev_primitives/core/sequential.py` - Connection metrics
- [ ] `src/tta_dev_primitives/performance/cache.py` - Cache metrics
- [ ] `packages/tta-observability-integration/src/observability_integration/apm_setup.py` - Service name config

---

## Key PromQL Queries

**Copy-paste these into Grafana:**

```promql
# Total executions per second
sum(rate(primitive_execution_count[5m]))

# Error rate percentage
(sum(rate(primitive_execution_count{execution_status="error"}[5m])) /
 sum(rate(primitive_execution_count[5m]))) * 100

# P95 latency
histogram_quantile(0.95, sum(rate(primitive_execution_duration_bucket[5m])))

# Top 5 slowest primitives (P95)
topk(5, histogram_quantile(0.95, sum by (primitive_name, le) (primitive_execution_duration_bucket)))

# Active workflows
sum(agent_workflows_active)

# Cache hit rate
(sum(rate(cache_hits[5m])) / sum(rate(cache_total[5m]))) * 100

# Service map (connection graph)
sum by (source_primitive, target_primitive) (rate(primitive_connection_count[5m]))
```

---

## Testing Your Implementation

### Minimal Test Script

```python
#!/usr/bin/env python3
"""Minimal test for observability."""

import asyncio
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive
from observability_integration import initialize_observability

# Initialize
initialize_observability(service_name="tta-test", enable_prometheus=True)

class TestPrimitive(InstrumentedPrimitive):
    async def _execute_impl(self, input_data, context):
        await asyncio.sleep(0.01)
        return {"processed": True}

async def main():
    workflow = SequentialPrimitive([TestPrimitive(), TestPrimitive()])
    context = WorkflowContext(
        workflow_id="test",
        workflow_name="test_workflow",
        agent_type="test_agent",
    )

    for i in range(10):
        await workflow.execute({"i": i}, context)

    print("✅ Done. Check:")
    print("  Jaeger: http://localhost:16686")
    print("  Prometheus: http://localhost:9090")
    print("  Grafana: http://localhost:3000")

asyncio.run(main())
```

**Run:**
```bash
uv run python test_observability.py
```

**Verify:**
1. Jaeger shows traces with semantic names
2. Prometheus shows metrics: `primitive_execution_count`, `primitive_execution_duration`
3. Grafana dashboard displays data

---

## Common Issues & Fixes

### "No traces in Jaeger"
```bash
# Check OTLP endpoint
docker ps | grep jaeger
# Ensure running on port 4317

# Check environment
echo $OTEL_EXPORTER_OTLP_ENDPOINT
# Should be: http://localhost:4317
```

### "No metrics in Prometheus"
```bash
# Check metrics endpoint
curl http://localhost:9464/metrics | head -20

# Should see OpenTelemetry metrics

# Check Prometheus targets
open http://localhost:9090/targets
# Should show target UP
```

### "Dashboard shows 'No Data'"
```bash
# Run test script to generate data
uv run python test_observability.py

# Check metrics exist
curl http://localhost:9464/metrics | grep primitive_execution

# Refresh Grafana dashboard
```

---

## Next Steps After Basic Implementation

1. **Add LLM-specific attributes** to LLM primitives
2. **Add cache metrics** to CachePrimitive
3. **Create advanced dashboards** with service maps
4. **Set up alerting** for error rates > 5%
5. **Document patterns** for other developers

---

## Reference Architecture

```
┌─────────────────────────────────────────────────────┐
│  Application Code                                    │
│  ├─ InstrumentedPrimitive (automatic tracing)       │
│  ├─ WorkflowContext (rich attributes)               │
│  └─ Metrics Recording (counters, histograms)        │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ↓                ↓
┌─────────────┐  ┌──────────────┐
│ OTLP        │  │ Prometheus   │
│ (Traces)    │  │ (Metrics)    │
└──────┬──────┘  └──────┬───────┘
       │                │
       ↓                ↓
┌─────────────┐  ┌──────────────┐
│ Jaeger      │  │ Grafana      │
│ (UI)        │  │ (Dashboards) │
└─────────────┘  └──────────────┘
```

---

**Quick Start Time:** 1 day for basic implementation
**Full Implementation:** 5 days for all 3 pillars
**Maintenance:** Minimal (built into primitives)

**Questions?** See full strategy doc: [TTA_OBSERVABILITY_STRATEGY.md](./TTA_OBSERVABILITY_STRATEGY.md)
