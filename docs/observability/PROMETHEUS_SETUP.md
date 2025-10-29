# Prometheus Setup Guide for TTA.dev Phase 3 Metrics

**Version:** 1.0.0  
**Last Updated:** 2025-10-29  
**Status:** ✅ Production Ready

---

## Overview

This guide covers setting up Prometheus to scrape and store TTA.dev Phase 3 enhanced metrics. Includes configuration, deployment, and optimization best practices.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Deployment Options](#deployment-options)
4. [Optimization](#optimization)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Prometheus

**Docker (Recommended):**
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest
```

**Binary:**
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xvfz prometheus-2.48.0.linux-amd64.tar.gz
cd prometheus-2.48.0.linux-amd64
./prometheus --config.file=prometheus.yml
```

### 2. Configure Scraping

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tta-dev'
    static_configs:
      - targets: ['localhost:8000']  # Your application metrics endpoint
```

### 3. Expose Metrics Endpoint

In your application:

```python
from flask import Flask, Response
from tta_dev_primitives.observability import get_prometheus_exporter

app = Flask(__name__)
exporter = get_prometheus_exporter()

@app.route('/metrics')
def metrics():
    return Response(
        exporter.get_metrics_text(),
        mimetype='text/plain'
    )

if __name__ == '__main__':
    app.run(port=8000)
```

### 4. Verify Scraping

Visit: http://localhost:9090/targets

Should show `tta-dev` target as `UP`.

---

## Configuration

### Basic Configuration

```yaml
global:
  scrape_interval: 15s      # How often to scrape targets
  evaluation_interval: 15s  # How often to evaluate rules
  external_labels:
    cluster: 'production'
    environment: 'prod'

# Alert rules
rule_files:
  - '/etc/prometheus/rules/*.yml'

# AlertManager integration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'

# Scrape configurations
scrape_configs:
  - job_name: 'tta-dev-primitives'
    scrape_interval: 15s
    static_configs:
      - targets:
          - 'app1:8000'
          - 'app2:8000'
          - 'app3:8000'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

### Service Discovery

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
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

**Docker Swarm:**
```yaml
scrape_configs:
  - job_name: 'tta-dev-swarm'
    dockerswarm_sd_configs:
      - host: unix:///var/run/docker.sock
        role: tasks
    relabel_configs:
      - source_labels: [__meta_dockerswarm_service_label_prometheus_enable]
        action: keep
        regex: true
```

### Alert Rules

Add Phase 3 alert rules to `prometheus.yml`:

```yaml
rule_files:
  - '/etc/prometheus/rules/slo-alerts.yml'
  - '/etc/prometheus/rules/performance-alerts.yml'
  - '/etc/prometheus/rules/cost-alerts.yml'
  - '/etc/prometheus/rules/availability-alerts.yml'
```

Copy alert rule files:
```bash
cp packages/tta-dev-primitives/alertmanager/rules/*.yml /etc/prometheus/rules/
```

---

## Deployment Options

### Option 1: Docker Compose (Development)

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./rules:/etc/prometheus/rules
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager-data:/alertmanager

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  alertmanager-data:
  grafana-data:
```

Start:
```bash
docker-compose up -d
```

### Option 2: Kubernetes (Production)

**ConfigMap for Prometheus config:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    # Paste prometheus.yml content here
```

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: data
          mountPath: /prometheus
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
          - '--storage.tsdb.retention.time=30d'
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: data
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

**Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus
spec:
  selector:
    app: prometheus
  ports:
    - protocol: TCP
      port: 9090
      targetPort: 9090
```

### Option 3: Prometheus Operator (Kubernetes)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: tta-dev-metrics
spec:
  selector:
    matchLabels:
      app: tta-dev
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

---

## Optimization

### 1. Storage Optimization

**Retention Policy:**
```yaml
# In prometheus command args
--storage.tsdb.retention.time=30d
--storage.tsdb.retention.size=50GB
```

**Compaction:**
```yaml
--storage.tsdb.min-block-duration=2h
--storage.tsdb.max-block-duration=2h
```

### 2. Cardinality Management

**Monitor cardinality:**
```promql
# Top 10 metrics by cardinality
topk(10, count by(__name__)({__name__!=""}))

# Cardinality per job
count by(job)({__name__!=""})
```

**Relabel to reduce cardinality:**
```yaml
relabel_configs:
  # Drop high-cardinality labels
  - source_labels: [__name__]
    regex: 'primitive_.*'
    action: keep
  
  # Limit instance labels
  - source_labels: [instance]
    regex: '([^:]+).*'
    target_label: instance
    replacement: '$1'
```

### 3. Query Performance

**Recording Rules:**
```yaml
# /etc/prometheus/rules/recordings.yml
groups:
  - name: tta_dev_recordings
    interval: 1m
    rules:
      # Pre-calculate p95 latency
      - record: job:primitive_latency:p95
        expr: |
          histogram_quantile(0.95,
            sum(rate(primitive_duration_seconds_bucket[5m])) by (job, le)
          )
      
      # Pre-calculate error rate
      - record: job:primitive_errors:rate5m
        expr: |
          sum(rate(primitive_requests_total{status="error"}[5m])) by (job)
          /
          sum(rate(primitive_requests_total[5m])) by (job)
```

### 4. Remote Storage

**For long-term storage:**
```yaml
remote_write:
  - url: "https://prometheus-remote-storage.example.com/write"
    queue_config:
      capacity: 10000
      max_shards: 50
      batch_send_deadline: 5s

remote_read:
  - url: "https://prometheus-remote-storage.example.com/read"
```

---

## Troubleshooting

### Issue: Targets showing as DOWN

**Check:**
1. Application is running: `curl http://localhost:8000/metrics`
2. Network connectivity: `telnet localhost 8000`
3. Prometheus config: Check `targets` in prometheus.yml
4. Firewall rules

**Solutions:**
```bash
# Test metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus logs
docker logs prometheus

# Reload config
curl -X POST http://localhost:9090/-/reload
```

### Issue: High memory usage

**Symptoms:** Prometheus using excessive memory

**Causes:**
1. Too many metrics (high cardinality)
2. Long retention period
3. Too many targets

**Solutions:**
```yaml
# Reduce retention
--storage.tsdb.retention.time=7d

# Limit sample rate
scrape_interval: 30s  # Instead of 15s

# Use relabeling to drop metrics
relabel_configs:
  - source_labels: [__name__]
    regex: 'unnecessary_metric.*'
    action: drop
```

### Issue: Queries are slow

**Solutions:**
1. Use recording rules for expensive queries
2. Reduce query time range
3. Use aggregation in queries
4. Check for high cardinality

**Example recording rule:**
```yaml
- record: api:latency_p95:5m
  expr: histogram_quantile(0.95, sum(rate(primitive_duration_seconds_bucket[5m])) by (le))
```

### Issue: Metrics not appearing

**Check:**
1. Prometheus is scraping: http://localhost:9090/targets
2. Metrics are exported: `curl http://localhost:8000/metrics`
3. Cardinality limit not reached
4. Label names are valid (alphanumeric + underscore)

---

## Best Practices

### 1. Configuration

- Use service discovery when possible
- Set appropriate scrape intervals (15-30s)
- Configure alerts for Prometheus itself
- Use external labels for multi-cluster

### 2. Monitoring

- Monitor Prometheus metrics:
  - `prometheus_tsdb_head_series` - Active time series
  - `prometheus_tsdb_head_samples_appended_total` - Samples ingested
  - `prometheus_target_scrapes_total` - Scrape success rate
- Set up alerts for Prometheus health
- Monitor disk usage

### 3. Security

- Enable basic auth:
  ```yaml
  basic_auth_users:
    admin: $2y$10$... # bcrypt hash
  ```
- Use TLS for scraping
- Restrict network access
- Use read-only mode for Grafana

### 4. Operations

- Regular backups of Prometheus data
- Test config before reloading: `promtool check config prometheus.yml`
- Use `--web.enable-lifecycle` for hot reload
- Monitor scrape duration

---

## Next Steps

- [Metrics Guide](METRICS_GUIDE.md) - Comprehensive metrics reference
- [Grafana Dashboards](../../packages/tta-dev-primitives/grafana/README.md)
- [AlertManager Rules](../../packages/tta-dev-primitives/alertmanager/README.md)

---

**Questions or Issues?**  
- GitHub Issues: https://github.com/theinterneti/TTA.dev/issues
- Prometheus Docs: https://prometheus.io/docs/
