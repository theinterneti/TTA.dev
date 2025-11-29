# Quick Start - Manual Testing

**Quick 15-minute validation of Phase 5 APM Integration**

## Prerequisites (5 minutes)

### 1. Start Observability Stack

```bash
# Start Prometheus + Grafana
docker-compose -f docker-compose.test.yml up -d

# Verify services
curl http://localhost:9090/-/healthy   # Prometheus
curl http://localhost:3000/api/health  # Grafana
```

### 2. Install Langfuse SDK (Optional)

```bash
# Add Langfuse to project
uv pip install langfuse

# Or skip if testing without Langfuse
# (system will gracefully degrade)
```

### 3. Set Langfuse Environment Variables (Optional)

```bash
# Add to .env file
cat >> .env << EOF
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
EOF
```

## Quick Test (5 minutes)

### Run Baseline Test

```bash
# Run the instrumented workflow
python -m .hypertool.instrumentation.test_instrumented_workflow
```

**Expected Output:**
```
🚀 Starting Package Release Workflow
============================================================

📝 Stage 1: Version Bump
   Persona: backend-engineer
   ✅ Backend task completed: Update version to 1.2.0
   📊 Tokens: 650
   💰 Budget remaining: 1350

🧪 Stage 2: Quality Validation
   Persona: testing-specialist
   ✅ Testing task completed: Run full test suite
   📊 Tokens: 720
   💰 Budget remaining: 780

🚀 Stage 3: Deployment
   Persona: devops-engineer
   ✅ DevOps task completed: Deploy: Deploy to production
   📊 Tokens: 550
   💰 Budget remaining: 1250

✅ Workflow Complete
```

## Verify Data (5 minutes)

### 1. Check Prometheus Metrics

```bash
# Query Hypertool metrics
curl -s -G http://localhost:9090/api/v1/label/__name__/values | \
  jq '.data[] | select(contains("hypertool"))'
```

**Expected Metrics:**
- `hypertool_persona_switches_total`
- `hypertool_token_usage_total`
- `hypertool_token_budget_remaining`
- `hypertool_workflow_stage_duration_seconds`
- `hypertool_quality_gate_status`
- `hypertool_persona_duration_seconds`

### 2. View Grafana Dashboards

1. Open http://localhost:3000
2. Login: admin / admin
3. Navigate to Dashboards
4. Import dashboards:
   - `.hypertool/instrumentation/dashboards/persona_overview.json`
   - `.hypertool/instrumentation/dashboards/workflow_performance.json`

**What to Look For:**
- Persona switch rate graph shows activity
- Token usage bars appear
- Workflow duration heatmap populated
- Quality gate metrics showing 100% success

### 3. Check Langfuse Traces (If Configured)

1. Open https://cloud.langfuse.com
2. Go to "Traces"
3. Find "package-release-workflow"
4. Verify:
   - 3 generations (stages)
   - Persona names visible
   - Token counts correct

## Automated Testing

For comprehensive testing with all checks:

```bash
# Run automated test suite
python .hypertool/instrumentation/run_manual_tests.py
```

This will:
- ✅ Check all prerequisites
- ✅ Run baseline workflow
- ✅ Verify Prometheus metrics
- ✅ Verify Grafana dashboards exist
- ✅ Verify alert rules configured
- ✅ Generate summary report

## Success Criteria

✅ **Minimum for "Working":**
1. Baseline test runs without errors
2. At least 3 Hypertool metrics in Prometheus
3. Dashboard JSON files exist
4. Alert rules file exists

✅ **Full Production Ready:**
1. All of the above
2. Grafana dashboards imported and showing data
3. Langfuse traces visible (if configured)
4. All 7 alerts configured in Prometheus

## Troubleshooting

### Grafana Not Starting

```bash
# Check Docker logs
docker-compose -f docker-compose.test.yml logs grafana

# Restart if needed
docker-compose -f docker-compose.test.yml restart grafana
```

### No Metrics in Prometheus

```bash
# Check if metrics endpoint is accessible
curl http://localhost:9464/metrics

# Verify Prometheus scrape config includes :9464
curl http://localhost:9090/api/v1/targets
```

### Langfuse Import Error

```bash
# Install Langfuse SDK
uv pip install langfuse

# Or run without Langfuse (graceful degradation)
# System will work, just without LLM call tracing
```

## Next Steps

After successful quick test:

1. **Import Dashboards to Grafana:**
   - Use Grafana UI → Import → Upload JSON
   - Import both dashboard files

2. **Configure Prometheus Alerts:**
   - Add `persona_alerts.yml` to Prometheus config
   - Reload Prometheus

3. **Test Real Workflows:**
   - See `MANUAL_TESTING_PLAN.md` for full workflow tests
   - Execute Augment, Cline, GitHub Copilot workflows

4. **Document Findings:**
   - Create `MANUAL_TESTING_FEEDBACK.md`
   - Note any issues or improvements

## Time Estimate

- **Prerequisites:** 5 minutes
- **Quick Test:** 5 minutes
- **Verification:** 5 minutes
- **Total:** 15 minutes

---

**For comprehensive testing:** See `MANUAL_TESTING_PLAN.md` (2-3 hours)
