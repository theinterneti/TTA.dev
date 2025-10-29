# Prometheus Setup Guide

**Complete guide for integrating TTA.dev metrics with Prometheus.**

---

## Overview

This guide covers:
1. Installing and configuring Prometheus
2. Exposing TTA.dev metrics
3. Configuring scrape endpoints
4. Verifying metric collection
5. Querying metrics

---

## Prerequisites

- Python 3.11+
- TTA.dev primitives installed
- Prometheus 2.x+

---

## Installation

### 1. Install prometheus-client (Optional)

```bash
# Install with prometheus support
pip install prometheus-client

# Or with uv
uv pip install prometheus-client
```

**Note:** TTA.dev works without prometheus-client (graceful degradation), but it's required for actual Prometheus integration.

### 2. Install Prometheus

**macOS (Homebrew):**
```bash
brew install prometheus
```

**Linux (Download):**
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64
```

**Docker:**
```bash
docker pull prom/prometheus:latest
```

---

## Configuration

### 1. Expose Metrics Endpoint

Add a metrics endpoint to your application:

```python
# app.py
from flask import Flask, Response
from prometheus_client import generate_latest, REGISTRY
from tta_dev_primitives.observability import get_prometheus_exporter

app = Flask(__name__)

# Initialize Prometheus exporter (singleton)
exporter = get_prometheus_exporter()

@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    # Export current metrics from enhanced collector
    exporter.export_metrics(primitive_type="app")
    
    # Return Prometheus formatted metrics
    return Response(generate_latest(REGISTRY), mimetype="text/plain")

@app.route("/api/process")
def process_request():
    """Example API endpoint with metrics."""
    import time
    start = time.time()
    
    try:
        # ... process request ...
        duration = time.time() - start
        
        # Record metrics
        exporter.record_execution(
            primitive_name="api_process",
            primitive_type="api",
            duration_seconds=duration,
            success=True
        )
        
        return {"status": "success"}
    except Exception as e:
        duration = time.time() - start
        exporter.record_execution(
            primitive_name="api_process",
            primitive_type="api",
            duration_seconds=duration,
            success=False
        )
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### 2. Configure Prometheus Scraping

Create `prometheus.yml`:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s      # Scrape every 15 seconds
  evaluation_interval: 15s   # Evaluate rules every 15 seconds

scrape_configs:
  - job_name: 'tta-dev-app'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Multiple instances:**
```yaml
scrape_configs:
  - job_name: 'tta-dev-prod'
    static_configs:
      - targets:
          - 'app1.example.com:5000'
          - 'app2.example.com:5000'
          - 'app3.example.com:5000'
    metrics_path: '/metrics'
    
  - job_name: 'tta-dev-staging'
    static_configs:
      - targets:
          - 'staging.example.com:5000'
    metrics_path: '/metrics'
```

### 3. Start Prometheus

```bash
# Direct execution
./prometheus --config.file=prometheus.yml

# Docker
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest
```

---

## Verification

### 1. Test Metrics Endpoint

```bash
curl http://localhost:5000/metrics
```

Expected output:
```
# HELP primitive_duration_seconds Primitive execution duration in seconds
# TYPE primitive_duration_seconds histogram
primitive_duration_seconds_bucket{le="0.001",primitive_name="api_process",primitive_type="api"} 0.0
primitive_duration_seconds_bucket{le="0.01",primitive_name="api_process",primitive_type="api"} 5.0
...
primitive_duration_seconds_sum{primitive_name="api_process",primitive_type="api"} 12.3
primitive_duration_seconds_count{primitive_name="api_process",primitive_type="api"} 100.0

# HELP primitive_requests_total Total number of primitive executions
# TYPE primitive_requests_total counter
primitive_requests_total{primitive_name="api_process",primitive_type="api",status="success"} 95.0
primitive_requests_total{primitive_name="api_process",primitive_type="api",status="failure"} 5.0

# HELP primitive_slo_compliance SLO compliance ratio (0.0 to 1.0)
# TYPE primitive_slo_compliance gauge
primitive_slo_compliance{primitive_name="api_process",primitive_type="api"} 0.99
...
```

### 2. Verify Scraping

Open Prometheus UI:
```
http://localhost:9090
```

Go to **Status → Targets** and verify:
- Target is "UP"
- Last scrape was recent
- No scrape errors

### 3. Query Metrics

In Prometheus UI (**Graph** tab):

**Check latency histogram:**
```promql
primitive_duration_seconds_bucket{primitive_name="api_process"}
```

**Check request count:**
```promql
primitive_requests_total{primitive_name="api_process"}
```

**Check SLO compliance:**
```promql
primitive_slo_compliance{primitive_name="api_process"}
```

---

## Common Queries

### Latency Percentiles

**95th percentile over 5 minutes:**
```promql
histogram_quantile(0.95, 
  sum(rate(primitive_duration_seconds_bucket[5m])) by (le, primitive_name)
)
```

**99th percentile by primitive type:**
```promql
histogram_quantile(0.99, 
  sum(rate(primitive_duration_seconds_bucket[5m])) by (le, primitive_type)
)
```

### Request Rate

**Requests per second:**
```promql
rate(primitive_requests_total[5m])
```

**Success rate:**
```promql
sum(rate(primitive_requests_total{status="success"}[5m])) /
sum(rate(primitive_requests_total[5m]))
```

**Error rate:**
```promql
sum(rate(primitive_requests_total{status="failure"}[5m])) /
sum(rate(primitive_requests_total[5m]))
```

### SLO Monitoring

**SLO compliance:**
```promql
primitive_slo_compliance{primitive_name="critical_workflow"}
```

**Error budget remaining:**
```promql
primitive_error_budget_remaining{primitive_name="critical_workflow"}
```

**SLO burn rate (error budget consumption rate):**
```promql
(1 - primitive_error_budget_remaining{primitive_name="critical_workflow"}) / 
(time() - primitive_error_budget_remaining{primitive_name="critical_workflow"} * 3600)
```

### Cost Tracking

**Cost per hour:**
```promql
rate(primitive_cost_total[1h]) * 3600
```

**Savings rate:**
```promql
rate(primitive_cost_savings[5m]) / 
(rate(primitive_cost_total[5m]) + rate(primitive_cost_savings[5m]))
```

**Cost by category:**
```promql
sum(rate(primitive_cost_total[5m])) by (category)
```

### Throughput

**Active requests:**
```promql
primitive_active_requests
```

**Peak active requests:**
```promql
max_over_time(primitive_active_requests[1h])
```

**Request rate trend:**
```promql
rate(primitive_requests_total[5m]) - rate(primitive_requests_total[5m] offset 1h)
```

---

## Advanced Configuration

### Service Discovery

For dynamic environments, use Prometheus service discovery:

**Kubernetes:**
```yaml
scrape_configs:
  - job_name: 'tta-dev-k8s'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

**AWS EC2:**
```yaml
scrape_configs:
  - job_name: 'tta-dev-ec2'
    ec2_sd_configs:
      - region: us-west-2
        port: 5000
    relabel_configs:
      - source_labels: [__meta_ec2_tag_Environment]
        action: keep
        regex: production
```

### Recording Rules

Pre-compute expensive queries:

```yaml
# recording_rules.yml
groups:
  - name: tta_dev_metrics
    interval: 30s
    rules:
      # Pre-compute p95 latency
      - record: primitive:latency:p95
        expr: |
          histogram_quantile(0.95, 
            sum(rate(primitive_duration_seconds_bucket[5m])) by (le, primitive_name)
          )
      
      # Pre-compute error rate
      - record: primitive:error_rate:5m
        expr: |
          sum(rate(primitive_requests_total{status="failure"}[5m])) by (primitive_name) /
          sum(rate(primitive_requests_total[5m])) by (primitive_name)
```

Add to `prometheus.yml`:
```yaml
rule_files:
  - 'recording_rules.yml'
```

### Metric Relabeling

Add custom labels or filter metrics:

```yaml
scrape_configs:
  - job_name: 'tta-dev-app'
    static_configs:
      - targets: ['localhost:5000']
    metric_relabel_configs:
      # Add environment label
      - source_labels: []
        target_label: environment
        replacement: production
      
      # Drop high-cardinality metrics
      - source_labels: [__name__]
        regex: 'primitive_duration_seconds_bucket'
        action: drop
```

---

## Troubleshooting

### Metrics Not Appearing

**Check metrics endpoint:**
```bash
curl http://localhost:5000/metrics | grep primitive
```

**Verify Prometheus scraping:**
```bash
# Check Prometheus logs
docker logs <prometheus-container> | grep error
```

**Common issues:**
- Port not accessible
- Firewall blocking scraping
- Incorrect `metrics_path`
- prometheus-client not installed

### High Cardinality

If seeing "too many metrics" warnings:

```python
# Check cardinality
from tta_dev_primitives.observability import get_prometheus_exporter

exporter = get_prometheus_exporter()
metrics = exporter.get_metrics_count()

print(f"Label combinations: {metrics['label_combinations']}")
print(f"Max allowed: {metrics['max_combinations']}")
```

**Solutions:**
- Limit primitive name variations
- Use fewer primitive types
- Drop unnecessary labels in Prometheus config

### Performance Issues

If scraping takes too long:

1. **Reduce scrape frequency:**
   ```yaml
   scrape_interval: 30s  # Instead of 15s
   ```

2. **Enable compression:**
   ```yaml
   scrape_configs:
     - job_name: 'tta-dev'
       honor_labels: true
       scheme: http
       metrics_path: '/metrics'
       params:
         compression: ['gzip']
   ```

3. **Limit metrics:**
   ```python
   # Only export critical primitives
   exporter.export_metrics(primitive_type="critical")
   ```

---

## Best Practices

### 1. Metric Naming

Follow Prometheus naming conventions:
- Use `primitive_` prefix
- Include units in name (`_seconds`, `_total`)
- Use snake_case

### 2. Label Management

- Keep label cardinality low (< 1000 combinations)
- Use `primitive_name` and `primitive_type` consistently
- Avoid high-cardinality labels (user IDs, request IDs)

### 3. Scrape Configuration

- Scrape interval: 10-30s for production
- Scrape timeout: < scrape interval
- Monitor target health

### 4. Retention

Configure Prometheus retention:
```bash
./prometheus \
  --config.file=prometheus.yml \
  --storage.tsdb.retention.time=30d \
  --storage.tsdb.retention.size=100GB
```

---

## Next Steps

- [Metrics Guide](METRICS_GUIDE.md) - Understand all available metrics
- [Grafana Dashboards](../grafana/README.md) - Visualize metrics
- [AlertManager Rules](../alertmanager/README.md) - Set up alerting

---

**Last Updated:** 2025-10-29
