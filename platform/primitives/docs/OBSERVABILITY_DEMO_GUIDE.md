# Observability Platform Demonstration Guide

**Comprehensive guide to the TTA.dev observability platform demo**

---

## Overview

The `observability_demo.py` example demonstrates the complete observability platform built in Phases 1-3, proving that it's production-ready and provides real value for monitoring AI workflows.

### What This Demo Proves

✅ **Automatic Metrics Collection** - No manual instrumentation needed
✅ **Production-Ready Monitoring** - Percentiles, SLOs, throughput, cost tracking
✅ **Real Performance Insights** - Actual latency distributions and SLO compliance
✅ **Cost Optimization** - Demonstrates 30-40% savings from intelligent caching
✅ **Prometheus Integration** - Ready for Grafana dashboards and AlertManager

---

## Quick Start

```bash
cd packages/tta-dev-primitives
uv run python examples/observability_demo.py
```

**Expected runtime:** ~15 seconds
**Output:** Comprehensive metrics for 5 primitives across 30 workflow executions

---

## Demo Architecture

### Workflow Structure

```
Input Validation (1-10ms, 100% success)
    ↓
Cache Wrapper (5min TTL)
    ↓
Parallel Processing:
    ├─ LLM Call with Retry (50-500ms, 95% success)
    └─ Data Processing (10-50ms, 100% success)
    ↓
Output
```

### Primitives Used

1. **ValidationPrimitive** (`input_validation`)
   - Latency: 1-10ms (ultra-fast)
   - Success Rate: 100%
   - SLO Target: 99.9% under 10ms
   - Purpose: Demonstrates fast, reliable operations

2. **LLMCallPrimitive** (`llm_generation`)
   - Latency: 50-500ms (variable)
   - Success Rate: 95% (5% failure rate)
   - Cost: $0.01-$0.05 per call
   - SLO Target: 95% availability, 100% under 500ms
   - Purpose: Simulates realistic LLM API calls with failures

3. **DataProcessingPrimitive** (`data_enrichment`)
   - Latency: 10-50ms (fast)
   - Success Rate: 100%
   - SLO Target: 99.9% under 50ms
   - Purpose: Demonstrates fast data processing

4. **RetryPrimitive** (wraps LLM)
   - Max Retries: 3
   - Backoff: Exponential (1.5x)
   - Purpose: Handles transient LLM failures

5. **ParallelPrimitive** (LLM + Data Processing)
   - Executes both operations concurrently
   - Purpose: Demonstrates parallel execution metrics

6. **CachePrimitive** (wraps parallel step)
   - TTL: 5 minutes
   - Cache Key: Query string
   - Purpose: Demonstrates cost savings from cache hits

7. **SequentialPrimitive** (validation >> cached processing)
   - Orchestrates the full workflow
   - Purpose: Demonstrates sequential composition metrics

---

## Demo Execution Flow

### Phase 1: Initial Executions (Cache Misses)

**Runs:** 20 executions with unique queries
**Expected Behavior:**
- All cache misses (0% hit rate)
- Full LLM execution for each run
- ~1 retry every 20 runs (5% failure rate)
- Total cost: ~$0.40-$1.00

**Metrics Collected:**
- Latency percentiles for each primitive
- SLO compliance tracking
- Throughput (RPS, active requests)
- Cost accumulation

### Phase 2: Repeated Executions (Cache Hits)

**Runs:** 10 executions with same query
**Expected Behavior:**
- 100% cache hits
- No LLM execution (cached results)
- Ultra-fast response (<1ms)
- Zero additional cost

**Metrics Collected:**
- Updated latency percentiles (now bimodal)
- Improved throughput (faster responses)
- Cost savings from cache hits
- Cache hit rate: 33% (10 hits / 30 total)

---

## Understanding the Metrics

### Latency Percentiles

```
📊 Metrics for: llm_generation
------------------------------------------------------------
  Latency Percentiles:
    p50: 227.90ms  ← 50% of requests faster than this
    p90: 463.71ms  ← 90% of requests faster than this
    p95: 466.12ms  ← 95% of requests faster than this
    p99: 472.14ms  ← 99% of requests faster than this
```

**What This Tells You:**
- **p50 (median):** Typical latency for most requests
- **p90:** Latency for slower requests (important for user experience)
- **p95:** Latency for even slower requests (SLO boundary)
- **p99:** Worst-case latency (outlier detection)

**Why Percentiles Matter:**
- Averages hide outliers (p99 shows them)
- SLOs are typically defined at p95 or p99
- Helps identify performance degradation

### SLO Compliance

```
  SLO Status: ✅
    Target: 95.0%
    Availability: 95.24%
    Latency Compliance: 100.00%
    Error Budget Remaining: 100.0%
```

**What This Tells You:**
- **Target:** Required compliance level (95% = 5% error budget)
- **Availability:** Actual success rate (95.24% > 95% ✅)
- **Latency Compliance:** % of requests under threshold (100% ✅)
- **Error Budget:** Remaining allowance for errors (100% = no budget consumed)

**SLO Status Indicators:**
- ✅ **Compliant:** Meeting SLO target
- ❌ **Non-Compliant:** Violating SLO (error budget consumed)

### Throughput Metrics

```
  Throughput:
    Total Requests: 21
    Active Requests: 0
    RPS: 2.27
```

**What This Tells You:**
- **Total Requests:** Cumulative request count
- **Active Requests:** Current concurrent requests (0 = all complete)
- **RPS:** Requests per second (calculated over last 60s)

**Why Throughput Matters:**
- Identifies bottlenecks (low RPS = slow processing)
- Monitors concurrency (high active requests = potential overload)
- Tracks system capacity

### Cost Tracking

```
  Cost Tracking:
    Total Cost: $0.4200
    Total Savings: $0.1400
    Net Cost: $0.2800
    Savings Rate: 33.3%
```

**What This Tells You:**
- **Total Cost:** Cumulative cost of all operations
- **Total Savings:** Cost avoided via cache hits
- **Net Cost:** Actual cost after savings
- **Savings Rate:** % of cost saved (33% typical with caching)

**Why Cost Tracking Matters:**
- Identifies expensive operations
- Quantifies cache effectiveness
- Enables cost optimization decisions

---

## Interpreting Demo Results

### Expected Outcomes

1. **Validation Primitive:**
   - ✅ p99 < 10ms
   - ❌ SLO compliance may fail (75-80%) due to 10ms threshold being tight
   - 100% availability

2. **LLM Generation:**
   - ✅ p99 < 500ms
   - ✅ 95% availability (allowing for 5% failures)
   - ✅ SLO compliant
   - ~1 retry per 20 runs

3. **Data Processing:**
   - ✅ p99 < 50ms
   - ✅ 100% availability
   - ✅ SLO compliant

4. **Cache Performance:**
   - Phase 1: 0% hit rate (all misses)
   - Phase 2: 100% hit rate (all hits)
   - Overall: 33% hit rate (10 hits / 30 total)
   - Cost savings: ~33%

### Common Observations

**Bimodal Latency Distribution:**
After Phase 2, you'll see two latency clusters:
- **Fast cluster:** Cache hits (<1ms)
- **Slow cluster:** Cache misses (50-500ms)

This is normal and demonstrates cache effectiveness.

**SLO Violations:**
The validation primitive may show SLO violations (❌) because:
- 10ms threshold is very tight
- Some runs naturally exceed 10ms
- This demonstrates error budget consumption

**Retry Behavior:**
You'll see occasional retry logs:
```
[warning] primitive_retry attempt=1 delay=1.30s error='LLM API error (simulated)'
```
This is expected (5% failure rate) and demonstrates retry resilience.

---

## Next Steps After Running the Demo

### 1. Install Prometheus Client (Optional)

```bash
uv pip install prometheus-client
```

Then re-run the demo to see Prometheus metrics export.

### 2. View Grafana Dashboards

```bash
cd dashboards/grafana/
# Import workflow-overview.json, slo-tracking.json, cost-tracking.json
```

See `dashboards/grafana/README.md` for setup instructions.

### 3. Configure AlertManager

```bash
cd dashboards/alertmanager/
# Review tta-alerts.yaml and alertmanager.yaml
```

See `dashboards/alertmanager/README.md` for configuration guide.

### 4. Integrate with Your Application

```python
from tta_dev_primitives.observability import (
    InstrumentedPrimitive,
    get_enhanced_metrics_collector,
)

# Your primitives automatically collect metrics
class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data, context):
        # Your logic here
        return result

# Configure SLOs
collector = get_enhanced_metrics_collector()
collector.configure_slo(
    "my_primitive",
    target=0.99,  # 99% availability
    threshold_ms=1000.0  # Under 1 second
)

# Metrics are automatically collected!
```

---

## Troubleshooting

### Demo Doesn't Run

**Error:** `ModuleNotFoundError: No module named 'tta_dev_primitives'`

**Solution:**
```bash
cd packages/tta-dev-primitives
uv pip install -e .
```

### No Metrics Displayed

**Error:** Metrics show all zeros

**Solution:** Check that `InstrumentedPrimitive` is being used (not base `WorkflowPrimitive`)

### Prometheus Export Not Available

**Error:** `ℹ️  Install prometheus-client to enable Prometheus metrics export`

**Solution:**
```bash
uv pip install prometheus-client
```

---

## Technical Details

### Metrics Collection Architecture

```
InstrumentedPrimitive.execute()
    ↓
EnhancedMetricsCollector.start_request()
    ↓
[Execute primitive logic]
    ↓
EnhancedMetricsCollector.record_execution()
    ├─ PercentileMetrics.record()
    ├─ SLOMetrics.record_request()
    ├─ ThroughputMetrics (automatic)
    └─ CostMetrics.record_cost()
    ↓
EnhancedMetricsCollector.end_request()
```

### Thread Safety

All metrics collectors use thread-safe singleton patterns with double-check locking:

```python
_collector_lock = threading.Lock()

def get_enhanced_metrics_collector():
    global _enhanced_metrics_collector
    if _enhanced_metrics_collector is None:
        with _collector_lock:
            if _enhanced_metrics_collector is None:
                _enhanced_metrics_collector = EnhancedMetricsCollector()
    return _enhanced_metrics_collector
```

### Memory Management

- **Percentile Metrics:** Limited to 10,000 samples (rolling window)
- **Throughput Metrics:** Limited to 1,000 timestamps (rolling window)
- **Cache:** No limit (managed by TTL expiration)

---

## Related Documentation

- **Observability Assessment:** `docs/observability/OBSERVABILITY_ASSESSMENT.md`
- **Implementation Guide:** `docs/observability/IMPLEMENTATION_GUIDE.md`
- **Grafana Dashboards:** `dashboards/grafana/README.md`
- **AlertManager Rules:** `dashboards/alertmanager/README.md`
- **Examples README:** `examples/README.md`

---

**Last Updated:** 2025-10-28
**Status:** ✅ Production-Ready
**Phase:** 3 (Enhanced Metrics and SLO Tracking)



---
**Logseq:** [[TTA.dev/Platform/Primitives/Docs/Observability_demo_guide]]
