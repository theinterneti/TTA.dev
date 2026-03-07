# Hypertool Observability Quick Reference Card

**Last Updated:** 2025-11-15
**Phase:** 5 Week 3 Complete
**Status:** Production Ready

---

## 🎯 Quick Access

### Dashboards

**Persona Overview**
- **URL:** `http://localhost:3000/d/hypertool-persona-overview`
- **File:** `.hypertool/instrumentation/dashboards/persona_overview.json`
- **Refresh:** 10 seconds
- **Panels:** 5 (switch rate, duration, token usage, budget, transitions)

**Workflow Performance**
- **URL:** `http://localhost:3000/d/hypertool-workflow-performance`
- **File:** `.hypertool/instrumentation/dashboards/workflow_performance.json`
- **Refresh:** 10 seconds
- **Panels:** 5 (stage duration, success rate, failures, slowest stages, trends)

### Alerts

**Prometheus Rules**
- **File:** `.hypertool/instrumentation/persona_alerts.yml`
- **Alerts:** 7 configured
- **View:** `http://localhost:9090/alerts`

**Alert Runbook**
- **File:** `.hypertool/instrumentation/ALERT_RUNBOOK.md`
- **Coverage:** All 7 alerts with investigation steps

---

## 📊 Dashboard Panels

### Persona Overview

| Panel | Type | Metric | Use Case |
|-------|------|--------|----------|
| Switch Rate | Graph | `rate(hypertool_persona_switches_total[5m])` | Identify switching patterns |
| Duration | Heatmap | `hypertool_persona_duration_seconds_bucket` | Time distribution |
| Token Usage | Bar Chart | `increase(hypertool_persona_tokens_used_total[1h])` | Budget tracking |
| Budget | Gauge | `hypertool_persona_token_budget_remaining` | Real-time budget |
| Transitions | Table | `topk(10, increase(hypertool_persona_switches_total[1h]))` | Common patterns |

### Workflow Performance

| Panel | Type | Metric | Use Case |
|-------|------|--------|----------|
| Stage Duration | Graph | `histogram_quantile(0.95, hypertool_workflow_stage_duration_seconds_bucket)` | Performance tracking |
| Success Rate | Stat | Quality gate pass rate | Quality monitoring |
| Failed Gates | Bar Chart | `topk(10, increase(...{result="fail"}[1h]))` | Identify issues |
| Slowest Stages | Table | `topk(10, histogram_quantile(0.95, ...))` | Optimization targets |
| Exec Trends | Timeseries | Pass/fail rates over time | Trend analysis |

---

## 🚨 Alerts Reference

### Critical Alerts

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| **TokenBudgetExceeded** | Budget < 0 | 1 minute | Increase budget or optimize |
| **HypertoolMetricsNotReported** | Endpoint down | 2 minutes | Restart service |

### Warning Alerts

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| **HighQualityGateFailureRate** | Failures > 20% | 5 minutes | Review prompts/criteria |
| **ExcessivePersonaSwitching** | > 2 switches/sec | 5 minutes | Add cooldown/batch tasks |
| **SlowWorkflowStage** | p95 > 5 minutes | 10 minutes | Optimize prompts/model |
| **LangfuseIntegrationFailing** | No traces | 5 minutes | Check credentials |

### Info Alerts

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| **TokenBudgetDepletionPredicted** | Budget exhaustion in 1h | 10 minutes | Monitor and prepare |

---

## 🔍 Quick Diagnostic Commands

### Check Metrics

```bash
# Verify metrics endpoint
curl http://localhost:9464/metrics | grep hypertool

# Check specific metric
curl http://localhost:9464/metrics | grep hypertool_persona_token_budget_remaining
```

### Query Prometheus

```bash
# Current token budgets
curl 'http://localhost:9090/api/v1/query?query=hypertool_persona_token_budget_remaining'

# Recent persona switches
curl 'http://localhost:9090/api/v1/query?query=rate(hypertool_persona_switches_total[5m])'

# Quality gate success rate
curl 'http://localhost:9090/api/v1/query?query=sum(rate(hypertool_workflow_quality_gate_total{result="pass"}[5m]))/sum(rate(hypertool_workflow_quality_gate_total[5m]))'
```

### Check Alerts

```bash
# Active alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component=="hypertool")'

# Alert rules
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="hypertool_persona_alerts")'
```

### Langfuse Access

```bash
# Open Langfuse UI
open https://cloud.langfuse.com

# Or self-hosted
open http://localhost:3000/langfuse
```

---

## 📊 PromQL Cheat Sheet

### Persona Metrics

```promql
# Persona switch rate (last 5 min)
rate(hypertool_persona_switches_total[5m])

# Average persona session duration
avg(rate(hypertool_persona_duration_seconds_sum[5m])) by (persona)

# Total tokens used (last hour)
sum(increase(hypertool_persona_tokens_used_total[1h])) by (persona)

# Current token budget
hypertool_persona_token_budget_remaining

# Top persona transitions
topk(10, sum(increase(hypertool_persona_switches_total[1h])) by (from_persona, to_persona))
```

### Workflow Metrics

```promql
# Workflow stage duration (p95)
histogram_quantile(0.95, sum(rate(hypertool_workflow_stage_duration_seconds_bucket[5m])) by (le, workflow, stage))

# Quality gate success rate
sum(rate(hypertool_workflow_quality_gate_total{result="pass"}[5m])) / sum(rate(hypertool_workflow_quality_gate_total[5m]))

# Failed quality gates (last hour)
sum(increase(hypertool_workflow_quality_gate_total{result="fail"}[1h])) by (workflow, stage)

# Slowest workflow stages
topk(10, histogram_quantile(0.95, sum(rate(hypertool_workflow_stage_duration_seconds_bucket[1h])) by (le, workflow, stage)))
```

---

## 🛠️ Import Dashboards

### Via Grafana UI

1. Go to Dashboards → Import
2. Click "Upload JSON file"
3. Select dashboard JSON file
4. Click "Import"

### Via API

```bash
# Import Persona Overview
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @.hypertool/instrumentation/dashboards/persona_overview.json

# Import Workflow Performance
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @.hypertool/instrumentation/dashboards/workflow_performance.json
```

---

## 🔧 Configure Alerts

### Add to Prometheus

```bash
# Copy alert rules
cp .hypertool/instrumentation/persona_alerts.yml /etc/prometheus/rules/

# Update prometheus.yml
cat >> /etc/prometheus/prometheus.yml << EOF
rule_files:
  - "rules/persona_alerts.yml"
EOF

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

### Verify Alerts Loaded

```bash
# Check rules
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="hypertool_persona_alerts")'

# Check active alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component=="hypertool")'
```

---

## 🎯 Common Investigations

### Budget Exceeded

```bash
# 1. Which persona?
curl 'http://localhost:9090/api/v1/query?query=hypertool_persona_token_budget_remaining<0'

# 2. Token usage by chatmode
curl 'http://localhost:9090/api/v1/query?query=sum(increase(hypertool_persona_tokens_used_total{persona="backend-engineer"}[1h]))by(chatmode,model)'

# 3. Check Langfuse for details
open https://cloud.langfuse.com
# Filter: user = persona name
```

### High Quality Gate Failures

```bash
# 1. Which stage failing?
curl 'http://localhost:9090/api/v1/query?query=sum(rate(hypertool_workflow_quality_gate_total{result="fail"}[5m]))by(workflow,stage)/sum(rate(hypertool_workflow_quality_gate_total[5m]))by(workflow,stage)>0.20'

# 2. Check Langfuse for failed generations
open https://cloud.langfuse.com
# Filter: workflow + stage metadata

# 3. Review quality gate criteria
grep -r "quality_gate" .augment/workflows/
```

### Excessive Switching

```bash
# 1. Current switch rate
curl 'http://localhost:9090/api/v1/query?query=sum(rate(hypertool_persona_switches_total[1m]))'

# 2. Switching patterns
curl 'http://localhost:9090/api/v1/query?query=topk(10,sum(rate(hypertool_persona_switches_total[5m]))by(from_persona,to_persona))'

# 3. Check for oscillation in Grafana
open http://localhost:3000/d/hypertool-persona-overview
# Look at "Top Persona Transitions" panel
```

### Slow Workflow Stage

```bash
# 1. Identify slow stage
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum(rate(hypertool_workflow_stage_duration_seconds_bucket[5m]))by(le,workflow,stage))>300'

# 2. Check Langfuse for slow LLM calls
open https://cloud.langfuse.com
# Filter: workflow + stage, sort by duration

# 3. Analyze traces in Jaeger/OTLP
# Look for bottlenecks in workflow execution
```

---

## 📚 Documentation Links

### Core Documentation

- **Technical Design:** `.hypertool/PHASE5_APM_LANGFUSE_INTEGRATION.md`
- **Quick Reference:** `.hypertool/PHASE5_QUICK_REFERENCE.md`
- **Week 1 Summary:** `.hypertool/PHASE5_IMPLEMENTATION_WEEK1_COMPLETE.md`
- **Week 2 Summary:** `.hypertool/PHASE5_IMPLEMENTATION_WEEK2_COMPLETE.md`
- **Week 3 Summary:** `.hypertool/PHASE5_IMPLEMENTATION_WEEK3_COMPLETE.md`

### Component Documentation

- **Langfuse Integration:** `.hypertool/instrumentation/LANGFUSE_INTEGRATION.md`
- **Alert Runbook:** `.hypertool/instrumentation/ALERT_RUNBOOK.md`
- **Next Session:** `.hypertool/NEXT_SESSION_PROMPT.md`

### Code Files

- **Persona Metrics:** `.hypertool/instrumentation/persona_metrics.py`
- **Workflow Tracing:** `.hypertool/instrumentation/workflow_tracing.py`
- **Langfuse Integration:** `.hypertool/instrumentation/langfuse_integration.py`
- **Observable LLM:** `.hypertool/instrumentation/observable_llm.py`

---

## 🔑 Key Thresholds

### Token Budgets (Default)

| Persona | Budget | Warning (< 50%) | Critical (< 0) |
|---------|--------|-----------------|----------------|
| backend-engineer | 2000 | 1000 | 0 |
| frontend-engineer | 1800 | 900 | 0 |
| devops-engineer | 1800 | 900 | 0 |
| testing-specialist | 1500 | 750 | 0 |
| observability-expert | 2000 | 1000 | 0 |
| data-scientist | 1700 | 850 | 0 |

### Performance Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Quality Gate Pass Rate | > 95% | 80-95% | < 80% |
| Workflow Stage Duration (p95) | < 30s | 30-60s | > 60s |
| Persona Switch Rate | < 1/sec | 1-2/sec | > 2/sec |

---

## 🚀 Production Checklist

### Before Deployment

- [ ] Grafana instance running (v9.0+)
- [ ] Prometheus configured with Hypertool scrape target
- [ ] Alertmanager configured for notifications
- [ ] Langfuse credentials set (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
- [ ] All dashboards imported
- [ ] Alert rules loaded
- [ ] Runbook distributed to on-call team

### Verification Steps

```bash
# 1. Check metrics endpoint
curl http://localhost:9464/metrics | grep hypertool

# 2. Verify Prometheus scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="hypertool")'

# 3. Check dashboards
open http://localhost:3000/dashboards
# Search: "Hypertool"

# 4. Verify alerts loaded
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="hypertool_persona_alerts")'

# 5. Test Langfuse connection
python -c "from .hypertool.instrumentation import get_langfuse_integration; print(get_langfuse_integration().enabled)"
```

---

**Status:** ✅ Production Ready
**Version:** 1.0
**Last Tested:** 2025-11-15


---
**Logseq:** [[TTA.dev/.hypertool/Observability_quick_reference]]
