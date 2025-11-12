# Prometheus Metrics Guide

**Quick reference for TTA.dev Prometheus metrics integration**

---

## 📊 Available Metrics

### Workflow Metrics

#### `tta_workflow_executions_total`
**Type:** Counter
**Description:** Total number of workflow executions
**Labels:**
- `workflow_name`: "SequentialPrimitive" | "ParallelPrimitive"
- `status`: "success" | "failure"
- `job`: "tta-primitives"

**Example Query:**
```promql
# Total workflow executions
sum(tta_workflow_executions_total)

# Success rate
sum(rate(tta_workflow_executions_total{status="success"}[5m])) /
sum(rate(tta_workflow_executions_total[5m]))

# Executions by workflow type
sum by (workflow_name) (tta_workflow_executions_total)
```

---

### Primitive Metrics

#### `tta_primitive_executions_total`
**Type:** Counter
**Description:** Total number of primitive executions
**Labels:**
- `primitive_type`: "sequential" | "parallel" | "cache" | "retry" | etc.
- `primitive_name`: "SequentialPrimitive" | "CachePrimitive" | etc.
- `status`: "success" | "failure"
- `job`: "tta-primitives"

**Example Query:**
```promql
# Total primitive executions
sum(tta_primitive_executions_total)

# Executions by primitive type
sum by (primitive_type) (tta_primitive_executions_total)

# Error rate by primitive
sum(rate(tta_primitive_executions_total{status="failure"}[5m])) by (primitive_type)
```

---

### Performance Metrics

#### `tta_execution_duration_seconds`
**Type:** Histogram
**Description:** Primitive execution duration in seconds
**Labels:**
- `primitive_type`: "sequential" | "parallel" | etc.
- `job`: "tta-primitives"

**Buckets:** 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, +Inf

**Example Query:**
```promql
# P95 latency
histogram_quantile(0.95, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))

# P50 latency
histogram_quantile(0.50, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))

# Average duration
rate(tta_execution_duration_seconds_sum[5m]) /
rate(tta_execution_duration_seconds_count[5m])

# P95 by primitive type
histogram_quantile(0.95,
  sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le, primitive_type)
)
```

---

### Cost Metrics

#### `tta_llm_cost_total`
**Type:** Counter
**Description:** Total LLM API costs in USD
**Labels:**
- `model`: "gpt-4" | "gpt-3.5-turbo" | "claude-3-opus" | etc.
- `provider`: "openai" | "anthropic" | "google" | etc.
- `job`: "tta-primitives"

**Status:** ⚠️ Structure created, pending LLM integration

**Example Query:**
```promql
# Total cost
sum(tta_llm_cost_total)

# Cost per hour
sum(rate(tta_llm_cost_total[1h]) * 3600)

# Cost by model
sum by (model) (tta_llm_cost_total)

# Cost by provider
sum by (provider) (tta_llm_cost_total)
```

---

### Cache Metrics

#### `tta_cache_hits_total`
**Type:** Counter
**Description:** Total cache hits
**Labels:**
- `job`: "tta-primitives"

**Status:** ⚠️ Structure created, pending CachePrimitive integration

#### `tta_cache_misses_total`
**Type:** Counter
**Description:** Total cache misses
**Labels:**
- `job`: "tta-primitives"

**Example Query:**
```promql
# Cache hit rate
sum(rate(tta_cache_hits_total[5m])) /
(sum(rate(tta_cache_hits_total[5m])) + sum(rate(tta_cache_misses_total[5m])))

# Total cache requests
sum(rate(tta_cache_hits_total[5m])) + sum(rate(tta_cache_misses_total[5m]))
```

---

## 🔄 Recording Rules

TTA.dev includes pre-computed recording rules for common queries:

### `tta:workflow_rate_5m`
**Expression:** `rate(tta_workflow_executions_total[5m])`
**Description:** 5-minute workflow execution rate

**Usage:**
```promql
# Current workflow rate
tta:workflow_rate_5m

# By workflow type
sum by (workflow_name) (tta:workflow_rate_5m)
```

---

### `tta:primitive_rate_5m`
**Expression:** `rate(tta_primitive_executions_total[5m])`
**Description:** 5-minute primitive execution rate

**Usage:**
```promql
# Current primitive rate
tta:primitive_rate_5m

# By primitive type
sum by (primitive_type) (tta:primitive_rate_5m)
```

---

### `tta:workflow_error_rate`
**Expression:**
```promql
sum(rate(tta_workflow_executions_total{status="failure"}[5m])) /
sum(rate(tta_workflow_executions_total[5m]))
```
**Description:** Percentage of failed workflows

**Usage:**
```promql
# Overall error rate
tta:workflow_error_rate

# Error rate above 5%
tta:workflow_error_rate > 0.05
```

---

### `tta:p95_latency_seconds`
**Expression:**
```promql
histogram_quantile(0.95,
  sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le)
)
```
**Description:** 95th percentile latency

**Usage:**
```promql
# Current P95
tta:p95_latency_seconds

# P95 above 1 second
tta:p95_latency_seconds > 1.0
```

---

### `tta:cost_per_hour_dollars`
**Expression:** `sum(rate(tta_llm_cost_total[1h]) * 3600)`
**Description:** Estimated LLM cost per hour in USD

**Status:** ⚠️ Pending LLM integration

**Usage:**
```promql
# Current hourly cost
tta:cost_per_hour_dollars

# Daily cost estimate
tta:cost_per_hour_dollars * 24
```

---

## 🚀 Quick Start

### 1. Start Metrics Server

```python
from tta_dev_primitives.observability import start_prometheus_exporter

# Start HTTP server on port 9464
start_prometheus_exporter(port=9464)
```

### 2. Execute Workflows

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# Your workflows automatically export metrics!
workflow = step1 >> step2 >> step3

context = WorkflowContext(trace_id="demo-123")
result = await workflow.execute(input_data, context)
```

### 3. View Metrics

**HTTP Endpoint:**
```bash
curl http://localhost:9464/metrics | grep tta_
```

**Prometheus UI:**
- http://localhost:9090
- Graph tab → Enter query → Execute

**Grafana:**
- http://localhost:3001
- System Overview dashboard

---

## 📈 Common Queries

### Request Rate

```promql
# Requests per second (RPS)
sum(rate(tta_workflow_executions_total[1m]))

# RPS by workflow type
sum by (workflow_name) (rate(tta_workflow_executions_total[1m]))
```

### Error Rate

```promql
# Error percentage
100 * (
  sum(rate(tta_workflow_executions_total{status="failure"}[5m])) /
  sum(rate(tta_workflow_executions_total[5m]))
)

# Failed requests per minute
sum(rate(tta_workflow_executions_total{status="failure"}[1m])) * 60
```

### Latency Percentiles

```promql
# P50 latency
histogram_quantile(0.50, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))

# P90 latency
histogram_quantile(0.90, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))

# P95 latency
histogram_quantile(0.95, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))

# P99 latency
histogram_quantile(0.99, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))
```

### Cost Analysis

```promql
# Total cost (all time)
sum(tta_llm_cost_total)

# Cost in last hour
sum(increase(tta_llm_cost_total[1h]))

# Cost per 1000 requests
sum(tta_llm_cost_total) / (sum(tta_workflow_executions_total) / 1000)

# Most expensive model
topk(3, sum by (model) (tta_llm_cost_total))
```

### Cache Performance

```promql
# Cache hit rate (percentage)
100 * (
  sum(rate(tta_cache_hits_total[5m])) /
  (sum(rate(tta_cache_hits_total[5m])) + sum(rate(tta_cache_misses_total[5m])))
)

# Cache requests per second
sum(rate(tta_cache_hits_total[5m])) + sum(rate(tta_cache_misses_total[5m]))

# Cache hits per second
sum(rate(tta_cache_hits_total[5m]))
```

---

## 🎨 Grafana Dashboard Panels

### Request Rate Panel

```json
{
  "title": "Request Rate",
  "targets": [{
    "expr": "sum(rate(tta_workflow_executions_total[5m]))",
    "legendFormat": "RPS"
  }]
}
```

### Error Rate Panel

```json
{
  "title": "Error Rate",
  "targets": [{
    "expr": "100 * (sum(rate(tta_workflow_executions_total{status=\"failure\"}[5m])) / sum(rate(tta_workflow_executions_total[5m])))",
    "legendFormat": "Error %"
  }]
}
```

### P95 Latency Panel

```json
{
  "title": "P95 Latency",
  "targets": [{
    "expr": "histogram_quantile(0.95, sum(rate(tta_execution_duration_seconds_bucket[5m])) by (le))",
    "legendFormat": "P95"
  }]
}
```

---

## 🔔 Alerting Rules

### High Error Rate Alert

```yaml
- alert: HighWorkflowErrorRate
  expr: tta:workflow_error_rate > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High workflow error rate detected"
    description: "Workflow error rate is {{ $value | humanizePercentage }}"
```

### High Latency Alert

```yaml
- alert: HighP95Latency
  expr: tta:p95_latency_seconds > 1.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High P95 latency detected"
    description: "P95 latency is {{ $value }}s"
```

### Cost Budget Alert

```yaml
- alert: HighLLMCost
  expr: tta:cost_per_hour_dollars > 10.0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "LLM costs exceeding budget"
    description: "Hourly cost is ${{ $value }}"
```

---

## 🛠️ Troubleshooting

### Metrics Not Appearing

**Check HTTP endpoint:**
```bash
curl http://localhost:9464/metrics
```

**Check Prometheus targets:**
```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.scrapeUrl | contains("9464"))'
```

**Check if server is running:**
```bash
ps aux | grep prometheus
netstat -tuln | grep 9464
```

### Zero Values in Dashboards

**Possible causes:**
1. No workflows executed recently
2. Recording rules need time to evaluate (wait 5 minutes)
3. Prometheus not scraping (check targets)

**Solution:**
```python
# Generate some traffic
for i in range(100):
    await workflow.execute(data, context)
```

### Recording Rules Not Updating

**Check rule evaluation:**
```bash
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name == "tta_workflow_metrics")'
```

**Force reload:**
```bash
curl -X POST http://localhost:9090/-/reload
```

---

## 📚 References

- **Prometheus Documentation:** https://prometheus.io/docs/
- **PromQL Guide:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Documentation:** https://grafana.com/docs/
- **TTA.dev Observability:** `OBSERVABILITY_SESSION_3_COMPLETE.md`

---

**Last Updated:** November 11, 2025
**Version:** 1.0
**Status:** ✅ Production Ready
