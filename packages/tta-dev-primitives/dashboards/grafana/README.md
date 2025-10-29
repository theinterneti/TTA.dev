# Grafana Dashboards for TTA Dev Primitives

This directory contains pre-built Grafana dashboard templates for visualizing TTA workflow metrics collected via Prometheus.

## 📊 Available Dashboards

### 1. Workflow Overview (`workflow-overview.json`)

**Purpose:** High-level view of workflow health and performance

**Panels:**
- **Request Rate (RPS)**: Success and failure rates per primitive
- **SLO Compliance**: Current SLO compliance gauges
- **Latency Percentiles**: p50, p95, p99 latency over time

**Use Cases:**
- Quick health check of all workflows
- Identifying performance degradation
- Monitoring request patterns

**Refresh Rate:** 10 seconds  
**Default Time Range:** Last 1 hour

---

### 2. SLO Tracking (`slo-tracking.json`)

**Purpose:** Monitor Service Level Objectives and error budgets

**Panels:**
- **Availability SLO Compliance**: Gauge showing current availability SLO
- **Error Budget Remaining**: Remaining error budget before SLO violation
- **SLO Compliance Over Time**: Historical SLO compliance trends
- **Error Budget Burn Rate**: Rate at which error budget is consumed

**Use Cases:**
- Tracking SLO compliance
- Identifying when to slow down deployments
- Planning capacity and reliability improvements

**Refresh Rate:** 10 seconds  
**Default Time Range:** Last 6 hours

---

### 3. Cost Tracking (`cost-tracking.json`)

**Purpose:** Monitor operational costs and savings from optimizations

**Panels:**
- **Total Cost**: Cumulative cost across all primitives
- **Total Savings**: Cumulative savings from caching and optimizations
- **Savings Rate**: Percentage of potential cost saved
- **Cost by Primitive & Operation**: Breakdown by primitive and operation type
- **Savings by Primitive**: Savings breakdown by primitive

**Use Cases:**
- Tracking LLM API costs
- Measuring cache effectiveness
- Identifying cost optimization opportunities

**Refresh Rate:** 10 seconds  
**Default Time Range:** Last 24 hours

---

## 🚀 Quick Start

### Prerequisites

1. **Prometheus** running and scraping metrics from your application
2. **Grafana** installed and configured
3. **TTA Dev Primitives** with Prometheus exporter enabled

### Installation

#### Option 1: Import via Grafana UI

1. Open Grafana web interface
2. Navigate to **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select one of the dashboard JSON files
5. Configure the Prometheus data source
6. Click **Import**

#### Option 2: Import via API

```bash
# Set your Grafana URL and API key
GRAFANA_URL="http://localhost:3000"
GRAFANA_API_KEY="your-api-key"

# Import workflow overview dashboard
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @workflow-overview.json

# Import SLO tracking dashboard
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @slo-tracking.json

# Import cost tracking dashboard
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @cost-tracking.json
```

#### Option 3: Provisioning (Recommended for Production)

Create a provisioning file in Grafana's provisioning directory:

```yaml
# /etc/grafana/provisioning/dashboards/tta-dashboards.yaml
apiVersion: 1

providers:
  - name: 'TTA Dashboards'
    orgId: 1
    folder: 'TTA Observability'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /path/to/tta-dev-primitives/dashboards/grafana
```

---

## ⚙️ Configuration

### Data Source Setup

All dashboards use a Prometheus data source variable `${DS_PROMETHEUS}`. Configure this in Grafana:

1. Navigate to **Configuration** → **Data Sources**
2. Add a **Prometheus** data source
3. Set the URL to your Prometheus instance (e.g., `http://localhost:9090`)
4. Click **Save & Test**

### Dashboard Variables

The dashboards currently use static queries. To add filtering by primitive or time range:

1. Open a dashboard
2. Click **Dashboard settings** (gear icon)
3. Navigate to **Variables**
4. Add a new variable:
   - **Name:** `primitive`
   - **Type:** Query
   - **Data source:** Prometheus
   - **Query:** `label_values(tta_workflow_requests_total, primitive_name)`
5. Update panel queries to use `{primitive_name=~"$primitive"}`

---

## 📈 Metrics Reference

### Prometheus Metrics Used

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `tta_workflow_requests_total` | Counter | Total requests processed | `primitive_name`, `status` |
| `tta_workflow_active_requests` | Gauge | Current active requests | `primitive_name` |
| `tta_workflow_primitive_duration_seconds` | Histogram | Execution duration | `primitive_name`, `primitive_type` |
| `tta_workflow_slo_compliance_ratio` | Gauge | SLO compliance (0-1) | `primitive_name`, `slo_type` |
| `tta_workflow_error_budget_remaining` | Gauge | Remaining error budget (0-1) | `primitive_name` |
| `tta_workflow_cost_total` | Counter | Total cost in USD | `primitive_name`, `operation` |
| `tta_workflow_savings_total` | Counter | Total savings in USD | `primitive_name` |

### Histogram Buckets

Latency histogram uses the following buckets (in seconds):
- `0.001` (1ms)
- `0.005` (5ms)
- `0.01` (10ms)
- `0.025` (25ms)
- `0.05` (50ms)
- `0.1` (100ms)
- `0.25` (250ms)
- `0.5` (500ms)
- `1.0` (1s)
- `2.5` (2.5s)
- `5.0` (5s)
- `10.0` (10s)

---

## 🎨 Customization

### Changing Thresholds

To adjust alert thresholds (e.g., SLO compliance):

1. Open the dashboard
2. Click on a panel title → **Edit**
3. Navigate to **Field** → **Thresholds**
4. Adjust the threshold values and colors
5. Click **Apply**

### Adding New Panels

To add custom panels:

1. Click **Add panel** in the dashboard
2. Select **Add a new panel**
3. Choose visualization type
4. Write PromQL query (see examples below)
5. Configure display options
6. Click **Apply**

### Example PromQL Queries

**Error rate:**
```promql
rate(tta_workflow_requests_total{status="failure"}[5m]) / 
rate(tta_workflow_requests_total[5m])
```

**Average latency:**
```promql
rate(tta_workflow_primitive_duration_seconds_sum[5m]) / 
rate(tta_workflow_primitive_duration_seconds_count[5m])
```

**Cost per request:**
```promql
rate(tta_workflow_cost_total[5m]) / 
rate(tta_workflow_requests_total[5m])
```

---

## 🔧 Troubleshooting

### No Data Showing

1. **Check Prometheus is scraping:**
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. **Verify metrics are being exported:**
   ```bash
   curl http://localhost:8000/metrics | grep tta_workflow
   ```

3. **Check Grafana data source connection:**
   - Navigate to **Configuration** → **Data Sources**
   - Click on your Prometheus data source
   - Click **Save & Test**

### Incorrect Time Range

- Ensure your system clocks are synchronized
- Check Grafana's timezone settings
- Verify Prometheus retention period

### Missing Metrics

- Ensure `prometheus-client` is installed: `uv pip install prometheus-client`
- Verify Prometheus exporter is initialized in your application
- Check that primitives are being executed (metrics only appear after execution)

---

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [TTA Dev Primitives Observability Guide](../../docs/observability/)

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0

