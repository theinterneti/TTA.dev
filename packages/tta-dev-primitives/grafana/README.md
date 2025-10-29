# Grafana Dashboards for TTA.dev Observability

This directory contains production-ready Grafana dashboards for monitoring TTA.dev workflows with Phase 3 enhanced metrics.

## 📊 Available Dashboards

### 1. Workflow Overview (`workflow-overview.json`)

**Purpose:** High-level monitoring of all workflow primitives

**Panels:**
- **Request Rate (RPS)**: Requests per second by primitive and status
- **Active Requests**: Currently executing requests
- **Latency Percentiles**: p50, p90, p95, p99 latency by primitive
- **Success Rate**: Success rate percentage by primitive
- **Error Rate**: Error rate by primitive
- **Throughput by Primitive**: Detailed throughput metrics

**Use Cases:**
- Monitor overall system health
- Identify high-traffic primitives
- Detect latency degradation
- Track error rates

**Recommended Refresh:** 30 seconds

---

### 2. SLO Tracking (`slo-tracking.json`)

**Purpose:** Monitor Service Level Objectives and error budgets

**Panels:**
- **SLO Compliance Gauge**: Current compliance vs. target (color-coded)
- **Error Budget Remaining Gauge**: Remaining error budget (color-coded)
- **SLO Compliance Over Time**: Trend of SLO compliance
- **Error Budget Burn Rate**: Rate of error budget consumption
- **Error Budget Trend**: Historical error budget
- **SLO Violations Table**: List of primitives currently violating SLOs
- **Latency vs SLO Threshold**: Compare actual latency to SLO thresholds

**Use Cases:**
- Track SLO compliance
- Monitor error budgets
- Identify SLO violations before they become critical
- Plan capacity and improvements

**Color Coding:**
- **Green**: Healthy (>99% compliance, >50% error budget)
- **Yellow**: Warning (95-99% compliance, 30-50% error budget)
- **Orange**: Concerning (90-95% compliance, 10-30% error budget)
- **Red**: Critical (<90% compliance, <10% error budget)

**Recommended Refresh:** 30 seconds

---

### 3. Cost Tracking (`cost-tracking.json`)

**Purpose:** Monitor costs and savings from optimizations

**Panels:**
- **Total Cost**: Cumulative cost across all primitives
- **Total Savings**: Cumulative savings from optimizations (e.g., caching)
- **Savings Rate Gauge**: Percentage of potential cost saved
- **Cost Efficiency Score**: Overall efficiency score
- **Cost Over Time**: Cost and savings rates
- **Savings Over Time**: Savings rate by primitive
- **Cost by Primitive (Pie Chart)**: Cost distribution
- **Savings by Primitive (Pie Chart)**: Savings distribution
- **Cost Breakdown Table**: Detailed cost and savings table

**Use Cases:**
- Track infrastructure costs
- Measure ROI of caching and optimizations
- Identify cost-heavy primitives
- Optimize resource allocation

**Recommended Refresh:** 1 minute

---

## 🚀 Quick Start

### Prerequisites

- Grafana 8.0 or later
- Prometheus data source configured
- TTA.dev with Phase 3 metrics enabled
- Prometheus exporter running (see `docs/observability/PROMETHEUS_SETUP.md`)

### Installation

#### Option 1: Grafana UI

1. **Open Grafana** (http://localhost:3000)
2. **Navigate** to Dashboards → Import
3. **Upload** one of the JSON files from `grafana/dashboards/`
4. **Select** your Prometheus data source
5. **Import**

#### Option 2: Provisioning (Recommended for Production)

1. **Create provisioning directory**:
   ```bash
   mkdir -p /etc/grafana/provisioning/dashboards
   ```

2. **Create dashboard provider config**:
   ```yaml
   # /etc/grafana/provisioning/dashboards/tta-dev.yml
   apiVersion: 1

   providers:
     - name: 'TTA.dev Dashboards'
       orgId: 1
       folder: 'TTA.dev'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       allowUiUpdates: true
       options:
         path: /var/lib/grafana/dashboards/tta-dev
   ```

3. **Copy dashboard files**:
   ```bash
   sudo cp grafana/dashboards/*.json /var/lib/grafana/dashboards/tta-dev/
   sudo chown -R grafana:grafana /var/lib/grafana/dashboards/tta-dev
   ```

4. **Restart Grafana**:
   ```bash
   sudo systemctl restart grafana-server
   ```

#### Option 3: Docker Compose

```yaml
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - ./grafana/provisioning:/etc/grafana/provisioning
```

---

## ⚙️ Configuration

### Prometheus Data Source

Ensure your Prometheus data source is configured:

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Dashboard Variables

Dashboards support the following variables (auto-configured):

- `$datasource`: Prometheus data source
- `$interval`: Auto-calculated scrape interval
- `$primitive_name`: Filter by primitive name (multi-select)

To add custom variables:
1. Dashboard Settings → Variables → Add variable
2. Configure query and options

---

## 🎨 Customization

### Adjust Refresh Rate

1. Dashboard Settings → General
2. Set "Refresh" to desired interval (e.g., 5s, 30s, 1m, 5m)

### Modify Thresholds

**For Gauges and Stats:**
1. Edit panel
2. Field → Thresholds
3. Adjust values and colors

**Common Thresholds:**
- SLO Compliance: Red <0.9, Yellow 0.9-0.95, Green >0.95
- Error Budget: Red <0.1, Orange 0.1-0.3, Yellow 0.3-0.5, Green >0.5

### Add Annotations

To mark deployments or incidents:

```yaml
# grafana/provisioning/dashboards/annotations.yml
apiVersion: 1

annotations:
  - name: Deployments
    datasource: Prometheus
    expr: up{job="tta-dev"} == 1
    step: 60s
    tagKeys: "version,env"
```

### Customize Time Ranges

Default time range: Last 1 hour

To change:
1. Top-right time picker
2. Select preset (e.g., Last 24 hours)
3. Or custom range

---

## 📈 Metrics Reference

### Histogram Metrics

```promql
primitive_duration_seconds_bucket{primitive_name="api_call", le="1.0"}
```

**Calculate percentiles:**
```promql
histogram_quantile(0.95, sum(rate(primitive_duration_seconds_bucket[5m])) by (le, primitive_name))
```

### Counter Metrics

```promql
primitive_requests_total{primitive_name="api_call", status="success"}
```

**Calculate rate:**
```promql
rate(primitive_requests_total{status="success"}[5m])
```

### Gauge Metrics

```promql
primitive_active_requests{primitive_name="api_call"}
primitive_slo_compliance{primitive_name="api_call", slo_name="latency"}
primitive_error_budget_remaining{primitive_name="api_call", slo_name="latency"}
```

### Cost Metrics

```promql
primitive_cost_total{primitive_name="llm_call"}
primitive_cost_savings_total{primitive_name="llm_call"}
```

**Calculate savings rate:**
```promql
sum(primitive_cost_savings_total) / (sum(primitive_cost_total) + sum(primitive_cost_savings_total))
```

---

## 🔧 Troubleshooting

### Dashboard shows "No data"

**Check:**
1. Prometheus data source is configured and reachable
2. Metrics are being exported (check Prometheus targets)
3. Time range includes recent data
4. Query syntax is correct

**Debug:**
```bash
# Check if Prometheus is scraping metrics
curl http://localhost:9090/api/v1/targets

# Check if metrics exist
curl http://localhost:9090/api/v1/query?query=primitive_requests_total
```

### Percentiles are incorrect

**Possible causes:**
1. Histogram buckets don't match data distribution
2. Not enough data points
3. Query time range too short

**Fix:**
- Adjust histogram buckets in `prometheus.py`
- Increase scrape interval
- Use longer time range in queries

### High cardinality warning

**Symptom:** Grafana is slow or crashes

**Cause:** Too many unique label combinations

**Fix:**
1. Reduce number of primitives or SLOs
2. Increase `MAX_LABEL_CARDINALITY` in `prometheus.py` (not recommended)
3. Use aggregation in queries:
   ```promql
   sum(rate(primitive_requests_total[5m])) by (status)
   ```

### Colors don't match SLOs

**Fix:**
1. Edit panel
2. Field → Thresholds
3. Set thresholds to match your SLO targets

---

## 📚 Best Practices

### 1. Alert Integration

Link dashboards to AlertManager rules:
- Add annotation queries for alerts
- Include "Silenced Alerts" panel
- Document alert thresholds in panel descriptions

### 2. Team Dashboards

Create team-specific views:
```promql
primitive_requests_total{team="backend"}
```

### 3. Performance Optimization

- Use recording rules for expensive queries
- Limit time ranges for high-cardinality metrics
- Cache dashboard JSON in version control

### 4. Documentation

- Add panel descriptions explaining metrics
- Include links to runbooks
- Document threshold rationale

### 5. Regular Review

- Review dashboards monthly
- Update thresholds based on SLO changes
- Archive unused panels

---

## 🔗 Related Documentation

- [Phase 3 Enhanced Metrics](../../docs/observability/METRICS_GUIDE.md)
- [Prometheus Setup Guide](../../docs/observability/PROMETHEUS_SETUP.md)
- [AlertManager Rules](../alertmanager/README.md)
- [Observability Assessment](../../docs/observability/OBSERVABILITY_ASSESSMENT.md)

---

## 💡 Tips

### Quick Filters

Use dashboard variables to filter:
- By primitive: `$primitive_name`
- By environment: `$env`
- By team: `$team`

### Drill-Down

Click on any panel to:
- Zoom to time range
- View raw data
- Explore in Prometheus

### Share Dashboards

- **Snapshot**: Dashboard → Share → Snapshot
- **Link**: Dashboard → Share → Link (with current time range)
- **Export**: Dashboard → Settings → JSON Model

---

## 📞 Support

For issues or questions:
- **GitHub Issues**: https://github.com/theinterneti/TTA.dev/issues
- **Documentation**: `docs/observability/`
- **Examples**: `packages/tta-dev-primitives/examples/`

---

**Last Updated:** 2025-10-29  
**Dashboard Version:** 1.0.0  
**Grafana Compatibility:** 8.0+
