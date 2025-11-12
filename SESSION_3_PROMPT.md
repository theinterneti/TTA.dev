# Session 3: Add Missing Metrics to TTA.dev Codebase

**Status:** Ready to begin
**Prerequisites:** ✅ Session 1 (Trace Propagation) complete, ✅ Session 2 (Recording Rules & Dashboard Consolidation) complete
**Infrastructure:** ✅ Prometheus running on port 9090, ✅ Grafana running on port 3001, ✅ Jaeger running on port 16686

---

## 🎯 Session Objectives

### Primary Goal
Implement missing Prometheus metrics in TTA.dev primitives codebase so that recording rules and dashboards can display real data.

### Success Criteria
1. ✅ `tta_workflow_executions_total` counter exported by workflow primitives
2. ✅ `tta_primitive_executions_total` counter exported by all primitives
3. ✅ `tta_llm_cost_total` counter exported by LLM-calling primitives
4. ✅ Recording rules evaluate with non-zero values (not just `vector(0)` fallbacks)
5. ✅ System Overview dashboard displays real metrics data
6. ✅ End-to-end test validates full observability stack

---

## 📊 Current State

### Infrastructure (Deployed & Verified)

**Prometheus (port 9090):**
- 14 rule groups loaded
- 33 recording rules active
- 7 alerting rule groups configured
- API endpoint: http://localhost:9090

**Grafana (port 3001):**
- Version: 10.2.3
- Dashboards provisioned: `01-system-overview.json`, `04-adaptive-primitives.json`
- Access: http://localhost:3001 (admin/admin)
- Status: Healthy, but showing "No data" (expected - metrics not implemented yet)

**Jaeger (port 16686):**
- Trace collection active
- Access: http://localhost:16686

### Recording Rules Status

**Business Metrics Group (tta_dev_business_metrics):**
```yaml
- record: tta:cost_per_hour_dollars
  expr: sum by (job) (rate(tta_llm_cost_total[1h]) * 3600) or vector(0)
  # ⚠️ Falls back to vector(0) because tta_llm_cost_total doesn't exist

- record: tta:p95_latency_seconds
  expr: histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))
  # ⚠️ May work if tta_execution_duration_seconds exists

- record: tta:total_executions_24h
  expr: sum(increase(tta_workflow_executions_total[24h]))
  # ⚠️ Falls back because tta_workflow_executions_total doesn't exist
```

**SLI Metrics Group (tta_dev_sli):**
```yaml
- record: tta:workflow_rate_5m
  expr: sum by (job) (rate(tta_workflow_executions_total[5m]))
  # ⚠️ Depends on tta_workflow_executions_total

- record: tta:primitive_rate_5m
  expr: sum by (primitive_type) (rate(tta_primitive_executions_total[5m]))
  # ⚠️ Depends on tta_primitive_executions_total
```

### Dashboard Panels Waiting for Data

**01-system-overview.json panels:**
1. **System Health** - Uses `up{job=~"tta-.*"}` (may work if services register)
2. **Request Rate** - Uses `tta:request_rate_5m` recording rule
3. **Cost per Hour** - Uses `tta:cost_per_hour_dollars` (needs tta_llm_cost_total)
4. **Workflow Executions** - Uses `tta_workflow_executions_total` (not implemented)
5. **Primitive Performance** - Uses `tta_execution_duration_seconds` (may exist)
6. **Cache Performance** - Uses `tta:cache_hit_rate_5m` (needs tta_cache_*)

---

## 🔍 Required Metrics Discovery

### Task 1: Find Existing Metrics Export Code

**Search locations:**
```bash
packages/tta-dev-primitives/src/tta_dev_primitives/observability/
packages/tta-dev-primitives/src/tta_dev_primitives/core/
packages/tta-observability-integration/src/
```

**Look for:**
- Classes: `InstrumentedPrimitive`, `ObservablePrimitive`, `PrimitiveMetrics`
- Files: `*metric*.py`, `*instrument*.py`, `*telemetry*.py`
- Imports: `from prometheus_client import Counter, Histogram`
- Existing metrics: `tta_execution_duration_seconds`, `tta_cache_*`

**Questions to answer:**
1. Where is the metrics export infrastructure already implemented?
2. Which primitives already export metrics?
3. What's the metric naming convention? (prefix, labels, etc.)
4. How are metrics registered with Prometheus? (pushgateway? exporter?)

### Task 2: Identify Metric Implementation Points

**Required Counter: `tta_workflow_executions_total`**
- Labels: `{workflow_name, status, job}`
- Increment location: Workflow execution completion (success/failure)
- Files to modify: `SequentialPrimitive`, `ParallelPrimitive`, `WorkflowPrimitive`

**Required Counter: `tta_primitive_executions_total`**
- Labels: `{primitive_type, primitive_name, status, job}`
- Increment location: Primitive execution completion
- Files to modify: `InstrumentedPrimitive` base class (affects all primitives)

**Required Counter: `tta_llm_cost_total`**
- Labels: `{model, provider, job}`
- Increment location: LLM API call completion
- Files to modify: LLM wrapper primitives, router primitives
- Note: May need cost calculation logic (tokens × price per token)

**Optional Histogram: `tta_execution_duration_seconds`**
- Labels: `{primitive_type, job}`
- If not exists: Add `.observe()` calls in primitive execution
- If exists: Verify it's working correctly

---

## 📝 Implementation Plan

### Step 1: Code Discovery (15 min)

```bash
# Search for existing metrics code
grep -r "prometheus_client" packages/tta-dev-primitives/
grep -r "Counter\|Histogram" packages/tta-dev-primitives/
grep -r "tta_" packages/ --include="*.py" | grep -i metric

# Find InstrumentedPrimitive class
find packages/ -name "*.py" -exec grep -l "InstrumentedPrimitive" {} \;

# Check for existing metric exports
grep -r "executions_total\|cost_total" packages/
```

### Step 2: Implement Missing Metrics (60 min)

**2.1 Add Workflow Execution Counter**
- File: `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py` (or workflow primitives)
- Code pattern:
  ```python
  from prometheus_client import Counter

  workflow_executions = Counter(
      'tta_workflow_executions_total',
      'Total number of workflow executions',
      ['workflow_name', 'status', 'job']
  )

  # In execute() method:
  try:
      result = await self._execute(data, context)
      workflow_executions.labels(
          workflow_name=self.__class__.__name__,
          status='success',
          job='tta-primitives'
      ).inc()
      return result
  except Exception as e:
      workflow_executions.labels(
          workflow_name=self.__class__.__name__,
          status='failure',
          job='tta-primitives'
      ).inc()
      raise
  ```

**2.2 Add Primitive Execution Counter**
- File: `packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py`
- Modify base class so ALL primitives inherit metric export
- Similar pattern to workflow counter

**2.3 Add LLM Cost Counter**
- Files: Router primitives, LLM wrapper code
- Requires cost calculation logic:
  ```python
  llm_cost = Counter(
      'tta_llm_cost_total',
      'Total LLM API costs in USD',
      ['model', 'provider', 'job']
  )

  # After LLM call:
  cost_usd = (prompt_tokens * PRICE_PER_INPUT_TOKEN +
              completion_tokens * PRICE_PER_OUTPUT_TOKEN)
  llm_cost.labels(
      model='gpt-4',
      provider='openai',
      job='tta-primitives'
  ).inc(cost_usd)
  ```

**2.4 Verify/Add Execution Duration Histogram**
- Check if `tta_execution_duration_seconds` exists
- If not, add `.observe()` calls in primitive execution

### Step 3: Configure Metric Export (30 min)

**3.1 Ensure Prometheus Pushgateway Integration**
- Check if primitives push metrics to pushgateway (port 9091)
- If not, add push logic:
  ```python
  from prometheus_client import push_to_gateway

  # After execution:
  push_to_gateway('localhost:9091', job='tta-primitives', registry=registry)
  ```

**3.2 Or Use HTTP Exporter**
- Alternative: Start HTTP server exposing /metrics endpoint
- Prometheus scrapes from configured targets

### Step 4: End-to-End Testing (30 min)

**4.1 Run Test Workflow**
```bash
# Execute a complete workflow using primitives
uv run python packages/tta-dev-primitives/examples/observability_demo.py

# Or create new test script:
uv run python test_metrics_export.py
```

**4.2 Verify Metrics in Prometheus**
```bash
# Check metrics appear in Prometheus
curl -s "http://localhost:9090/api/v1/query?query=tta_workflow_executions_total" | jq '.'

curl -s "http://localhost:9090/api/v1/query?query=tta_primitive_executions_total" | jq '.'

curl -s "http://localhost:9090/api/v1/query?query=tta_llm_cost_total" | jq '.'

# Verify recording rules evaluate with real values
curl -s "http://localhost:9090/api/v1/query?query=tta:workflow_rate_5m" | jq '.'

curl -s "http://localhost:9090/api/v1/query?query=tta:cost_per_hour_dollars" | jq '.'
```

**4.3 Check Grafana Dashboards**
- Open http://localhost:3001
- Navigate to "TTA.dev Production" → "01-system-overview"
- Verify all 6 panels show data (not "No data")
- Check that request rate, cost, workflow execution charts populate

**4.4 Validate Jaeger Traces**
- Open http://localhost:16686
- Search for service "tta-primitives"
- Verify traces appear with correct span structure

### Step 5: Documentation (15 min)

**Update files:**
- `OBSERVABILITY_SESSION_3_COMPLETE.md` - Document metrics added, test results
- `packages/tta-dev-primitives/README.md` - Add metrics export documentation
- `config/prometheus/README.md` - Document metric schemas and labels

---

## 🧪 Test Scenarios

### Scenario 1: Basic Workflow Execution
```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

workflow = SequentialPrimitive([step1, step2, step3])
context = WorkflowContext(correlation_id="test-123")

# Execute workflow
result = await workflow.execute({"input": "test"}, context)

# Expected metrics:
# tta_workflow_executions_total{workflow_name="SequentialPrimitive",status="success",job="tta-primitives"} 1
# tta_primitive_executions_total{primitive_type="step1",status="success",job="tta-primitives"} 1
```

### Scenario 2: LLM Router with Cost Tracking
```python
from tta_dev_primitives.core import RouterPrimitive

router = RouterPrimitive(
    routes={"fast": gpt_4_mini, "quality": gpt_4},
    default="fast"
)

result = await router.execute({"prompt": "test"}, context)

# Expected metrics:
# tta_llm_cost_total{model="gpt-4-mini",provider="openai",job="tta-primitives"} 0.0001
```

### Scenario 3: Cache Hit Tracking
```python
from tta_dev_primitives.performance import CachePrimitive

cached = CachePrimitive(primitive=expensive_op, ttl=3600)

# First call - cache miss
result1 = await cached.execute(data, context)
# tta_cache_operations_total{operation="miss",primitive="expensive_op"} 1

# Second call - cache hit
result2 = await cached.execute(data, context)
# tta_cache_operations_total{operation="hit",primitive="expensive_op"} 1
```

---

## 📋 Success Checklist

- [ ] Code search completed - identified metric export infrastructure
- [ ] `tta_workflow_executions_total` counter implemented
- [ ] `tta_primitive_executions_total` counter implemented
- [ ] `tta_llm_cost_total` counter implemented (with cost calculation)
- [ ] `tta_execution_duration_seconds` histogram verified/added
- [ ] Metrics pushed to Prometheus (pushgateway or HTTP exporter)
- [ ] Test workflow executed successfully
- [ ] Prometheus queries return non-zero metric values
- [ ] Recording rules evaluate with real data (not vector(0) fallbacks)
- [ ] Grafana System Overview dashboard shows data in all 6 panels
- [ ] Jaeger traces correlate with metric exports
- [ ] Documentation updated (OBSERVABILITY_SESSION_3_COMPLETE.md)
- [ ] Code committed to agent/copilot branch

---

## 🚀 Getting Started

**Step 1: Review Previous Sessions**
```bash
# Session 1 summary
cat OBSERVABILITY_SESSION_1_COMPLETE.md

# Session 2 summary
cat OBSERVABILITY_SESSION_2_COMPLETE.md

# Audit report (original plan)
cat OBSERVABILITY_AUDIT_REPORT.md
```

**Step 2: Verify Infrastructure**
```bash
# Check all services running
docker ps | grep -E 'tta-prometheus|tta-grafana|jaeger'

# Expected output:
# tta-prometheus   (port 9090)
# tta-grafana-new  (port 3001)
# tta-jaeger       (port 16686)

# Test Prometheus API
curl -s http://localhost:9090/api/v1/rules | jq -r '.data.groups[].name'

# Test Grafana API
curl -s http://localhost:3001/api/health | jq '.'
```

**Step 3: Begin Code Discovery**
```bash
# Search for existing metrics code (as shown in Step 1 above)
grep -r "prometheus_client" packages/tta-dev-primitives/

# Find InstrumentedPrimitive
grep -r "class InstrumentedPrimitive" packages/

# Check for existing tta_* metrics
grep -r "tta_execution\|tta_workflow\|tta_primitive" packages/ --include="*.py"
```

**Step 4: Start Implementation**
- Open identified metric files
- Add missing counters following existing patterns
- Test incrementally with small workflows

---

## 📞 Support & References

**Documentation:**
- Prometheus Python Client: https://github.com/prometheus/client_python
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- TTA.dev Primitives: `packages/tta-dev-primitives/README.md`

**Configuration Files:**
- Recording Rules: `config/prometheus/rules/recording_rules.yml`
- Prometheus Config: `config/prometheus/prometheus.yml`
- System Overview Dashboard: `config/grafana/dashboards/production/01-system-overview.json`

**Previous Work:**
- Session 1: Trace propagation fixes in WorkflowContext
- Session 2: Recording rules, dashboard consolidation, infrastructure deployment

**Key Context:**
- All infrastructure is ready and verified
- Dashboards show "No data" because metrics don't exist in code yet
- Recording rules fall back to `vector(0)` when metrics are missing
- Goal is to make dashboards show REAL data from executing primitives

---

## 🎯 Expected Outcomes

**After Session 3:**
1. ✅ TTA.dev primitives export Prometheus metrics
2. ✅ Recording rules calculate real SLI values
3. ✅ System Overview dashboard displays live data
4. ✅ Complete observability stack validated end-to-end
5. ✅ Developer dashboard ready for enhancement (Session 4)

**Deliverables:**
- Modified Python files with metric export code
- Test script demonstrating metric collection
- `OBSERVABILITY_SESSION_3_COMPLETE.md` report
- Updated package documentation
- Validated Prometheus queries showing real data

---

**Ready to begin Session 3!** 🚀

Start with code discovery to understand existing metric infrastructure, then implement the three required counters (workflow executions, primitive executions, LLM cost). Test iteratively and validate with Prometheus queries before moving to dashboard verification.

**Estimated Duration:** 2-3 hours
**Complexity:** Medium (requires understanding TTA.dev primitive architecture)
**Blockers:** None (all prerequisites met)
