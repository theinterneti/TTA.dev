# Quick Start: TTA.dev Observability Dashboard

**⏱️ Setup Time:** 5 minutes
**Prerequisites:** Docker, uv

---

## 1. Start Observability Stack (2 minutes)

```bash
# Start Prometheus, Jaeger, and Grafana
./scripts/setup-observability.sh

# Verify services are running
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:16686           # Jaeger UI
curl http://localhost:3000/api/health # Grafana
```

**Services:**
- 📊 Prometheus: http://localhost:9090
- 🔍 Jaeger: http://localhost:16686
- 📈 Grafana: http://localhost:3000 (admin/admin)

---

## 2. Import Dashboard (1 minute)

### Option A: Automated Script
```bash
./scripts/import-dashboard.sh
```

### Option B: Manual Import
1. Open http://localhost:3000
2. Login: admin/admin
3. Navigate: Dashboards → Import
4. Upload: `configs/grafana/dashboards/tta_agent_observability.json`
5. Select Prometheus datasource
6. Click Import

---

## 3. Generate Test Data (2 minutes)

```bash
# Run Phase 1 test (semantic tracing)
PYTHONPATH=$PWD/packages \
  uv run python packages/tta-dev-primitives/examples/test_semantic_tracing.py

# Run Phase 2 test (core metrics)
PYTHONPATH=$PWD/packages \
  uv run python packages/tta-dev-primitives/examples/test_core_metrics.py
```

**Expected Output:**
```
Phase 1: Semantic Tracing Test - ALL TESTS PASSED ✅
Phase 2: Core Metrics Test - ALL TESTS PASSED ✅
```

---

## 4. View Dashboard

Open the dashboard and explore all 4 tabs:

**Overview Tab:**
- System Health Score (should be >95%)
- Service Map showing primitive connections
- System Throughput graph
- Active Workflows count
- Error Rate (should be 0%)

**Workflows Tab:**
- Top 10 Workflows by latency
- Success rates table
- Error distribution pie chart

**Primitives Tab:**
- Performance heatmap
- Execution count by type
- Cache hit rate
- Top 5 slowest primitives

**Resources Tab:**
- LLM tokens by model
- Estimated LLM cost
- Cache hit rate by primitive
- Cache cost savings

---

## 5. Validate Installation

### Check Prometheus Metrics

Open http://localhost:9090 and run these queries:

```promql
# Should return data
primitive_execution_count

# Should show success rate (0-1)
sum(rate(primitive_execution_count{execution_status="success"}[5m])) / sum(rate(primitive_execution_count[5m]))

# Should show connections
primitive_connection_count
```

### Check Jaeger Traces

1. Open http://localhost:16686
2. Service: Should see `tta-dev-primitives`
3. Find traces with semantic names:
   - `primitive.sequential.execute`
   - `primitive.processor.process`
4. Click trace to see 20+ attributes

### Check Grafana Panels

All 16 panels should show data:
- ✅ Service Map has nodes and edges
- ✅ Health Score shows percentage
- ✅ Throughput graph has data points
- ✅ Active Workflows shows count
- ✅ Error Rate shows percentage

---

## 6. Use in Your Code

```python
from tta_dev_primitives import WorkflowContext, SequentialPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive

# Create workflow with context
context = WorkflowContext(
    agent_id="my-agent-123",
    agent_type="coordinator",
    workflow_name="My Workflow",
    llm_provider="openai",
    llm_model_name="gpt-4",
    llm_model_tier="quality"
)

# Execute workflow
workflow = step1 >> step2 >> step3
result = await workflow.execute(input_data, context)

# Check dashboard - your workflow will appear automatically!
```

**What You'll See:**
- Spans in Jaeger with semantic names
- Metrics in Prometheus
- Real-time updates in Grafana dashboard
- Service map showing your workflow steps

---

## Common Questions

### "Is my system working?"
Look at **System Health Score** (Overview tab)
- Green (>95%) = All good
- Yellow (80-95%) = Some issues
- Red (<80%) = Problems need attention

### "Which workflow is slow?"
Check **Top 10 Workflows by P95 Latency** (Workflows tab)
- Top bars = slowest workflows
- Click to see which primitives are bottlenecks

### "Why are requests failing?"
Look at **Error Distribution** (Workflows tab)
- Pie chart shows error types
- Largest slice = most common error

### "Am I wasting money?"
Check **Cache Hit Rate** (Primitives tab)
- <80% = Opportunity to optimize
- Also check **Cache Cost Savings** (Resources tab)

### "How much am I spending?"
See **Estimated LLM Cost** (Resources tab)
- Shows hourly USD cost
- Also see **LLM Tokens by Model** for breakdown

---

## Troubleshooting

### No Data in Dashboard

**Symptoms:** All panels empty, "No data" messages

**Solutions:**
1. Generate test data (see Step 3 above)
2. Check Prometheus has metrics: `curl http://localhost:9090/api/v1/query?query=primitive_execution_count`
3. Verify time range (top-right) is set to "Last 1 hour"
4. Wait 10 seconds for auto-refresh

### Dashboard Import Failed

**Symptoms:** Error when importing JSON

**Solutions:**
1. Verify Grafana is running: `curl http://localhost:3000/api/health`
2. Check credentials: Default is admin/admin
3. Validate JSON syntax: `jq '.' configs/grafana/dashboards/tta_agent_observability.json`
4. Use automated script: `./scripts/import-dashboard.sh`

### Service Map Empty

**Symptoms:** No nodes/edges in service map panel

**Solutions:**
1. Run test with multiple primitives (test_semantic_tracing.py does this)
2. Check connection metrics: `curl http://localhost:9090/api/v1/query?query=primitive_connection_count`
3. Verify SequentialPrimitive is recording connections
4. Refresh dashboard

---

## Next Steps

### Production Usage
1. **Add to your workflows:** Use WorkflowContext in all primitives
2. **Set up alerts:** Configure Prometheus alert rules
3. **Monitor costs:** Track LLM spend in Resources tab
4. **Optimize cache:** Target <80% hit rate primitives

### Optional Enhancements
1. **LLM Integration:** Add llm.* attributes to LLM primitives (30 min)
2. **Cache Integration:** Add cache.* attributes to CachePrimitive (30 min)
3. **Custom Dashboards:** Create per-agent or per-environment dashboards
4. **Alert Rules:** Set up notifications for errors and costs

---

## Documentation

- **Full Strategy:** `docs/observability/TTA_OBSERVABILITY_STRATEGY.md`
- **Implementation:** `docs/observability/ALL_PHASES_COMPLETE.md`
- **Phase Details:**
  - Phase 1 & 2: `docs/observability/PHASES_1_2_COMPLETE.md`
  - Phase 3: `docs/observability/PHASE3_DASHBOARDS_COMPLETE.md`

---

## Support

**Questions?**
- Check documentation in `docs/observability/`
- Run tests to verify setup
- Review Grafana dashboard examples

**Issues?**
- Verify all services running
- Check test output for errors
- Validate Prometheus has metrics

---

**That's it!** You now have production-ready observability for TTA.dev. 🎉

The dashboard updates every 10 seconds with real-time data. Just run your workflows with WorkflowContext and watch the metrics appear!
