# TTA.dev/Services/ObservabilityStack

type:: [S] Service
status:: stable
service-type:: observability
tags:: #service, #observability, #monitoring, #infrastructure
context-level:: 2-Operational
deployment:: docker
exposes:: Prometheus metrics endpoint (9090), Jaeger traces UI (16686), Grafana dashboards (3000)
depends-on:: Docker, docker-compose
configuration:: [[TTA.dev/Data/SLOConfig]]
monitoring:: Prometheus /metrics endpoint, Grafana dashboards
created-date:: [[2025-11-11]]
last-updated:: [[2025-11-11]]

---

## Overview

**ObservabilityStack** is TTA.dev's comprehensive monitoring and tracing infrastructure, providing real-time visibility into workflow execution, performance metrics, and distributed traces. Built on industry-standard tools (Prometheus, Jaeger, Grafana), it delivers production-grade observability with zero configuration.

**Service Type:** observability
**Deployment:** Docker Compose
**Status:** stable

**Components:**
- **Prometheus** - Metrics collection and alerting
- **Jaeger** - Distributed tracing
- **Grafana** - Dashboards and visualization
- **OTLP Collector** - OpenTelemetry collector
- **Pushgateway** - Metrics push endpoint

---

## Architecture

### Components

1. **Prometheus (Port 9090)** - Time-series metrics database
   - Scrapes metrics from primitives
   - Stores historical data (15d retention)
   - Provides PromQL query language

2. **Jaeger (Port 16686)** - Distributed tracing UI
   - Visualizes execution traces
   - Tracks request flows across primitives
   - Identifies performance bottlenecks

3. **Grafana (Port 3000)** - Visualization and dashboards
   - Pre-built dashboards for TTA.dev workflows
   - Alert management
   - Multi-datasource support

4. **OTLP Collector (Port 4318)** - OpenTelemetry gateway
   - Receives traces and metrics
   - Exports to Prometheus and Jaeger
   - Protocol translation

5. **Pushgateway (Port 9091)** - Metrics push endpoint
   - Accept push-based metrics
   - Bridge for short-lived jobs

### Dependencies

This service depends on:

- **Docker** - Container runtime (required)
- **docker-compose** - Multi-container orchestration (required)
- Network connectivity - Services communicate via internal network

---

## Installation

### Docker Deployment (Recommended)

```bash
# One-command setup
./scripts/setup-observability.sh

# Manual setup
docker-compose -f docker-compose.observability.yml up -d

# Verify all services running
docker-compose -f docker-compose.observability.yml ps
```

### Custom Deployment

```bash
# Use custom compose file
cp docker-compose.observability.yml docker-compose.custom.yml
# Edit docker-compose.custom.yml
docker-compose -f docker-compose.custom.yml up -d
```

---

## Configuration

### Environment Variables

```bash
# Prometheus settings
export PROMETHEUS_RETENTION="15d"
export PROMETHEUS_PORT="9090"

# Jaeger settings
export JAEGER_PORT="16686"
export JAEGER_OTLP_PORT="4318"

# Grafana settings
export GRAFANA_PORT="3000"
export GRAFANA_ADMIN_PASSWORD="admin"
```

### Docker Compose Configuration

```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4318:4318"    # OTLP
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

---

## Usage

### Starting the Stack

```bash
# Development - with logs
./scripts/start-observability.sh

# Production - detached
docker-compose -f docker-compose.observability.yml up -d

# Check status
./scripts/check-observability-health.sh
```

### Accessing Services

Once started, access via browser:

- **Prometheus:** http://localhost:9090
- **Jaeger:** http://localhost:16686
- **Grafana:** http://localhost:3000 (admin/admin)

### Connecting from TTA.dev

Primitives automatically export metrics when observability is enabled:

```python
from observability_integration import initialize_observability
from tta_dev_primitives import WorkflowContext

# Initialize (one-time setup)
initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    prometheus_port=9464
)

# Use primitives - metrics auto-exported!
context = WorkflowContext(trace_id="req-123")
result = await workflow.execute(data, context)

# View metrics at http://localhost:9090
# View traces at http://localhost:16686
```

---

## API / Interface

### Prometheus API

**Query metrics:**
```bash
# Query via HTTP API
curl http://localhost:9090/api/v1/query?query=up

# Example PromQL queries
primitive_duration_seconds{primitive="CachePrimitive"}
rate(primitive_errors_total[5m])
```

### Jaeger API

**Search traces:**
```bash
# Get trace by ID
curl http://localhost:16686/api/traces/{trace_id}

# Search traces by service
curl http://localhost:16686/api/traces?service=my-app&limit=20
```

### Grafana API

**Dashboard access:**
```bash
# Get dashboards
curl -u admin:admin http://localhost:3000/api/dashboards/home

# Create alert
curl -X POST -u admin:admin http://localhost:3000/api/alerts \
  -H "Content-Type: application/json" \
  -d @alert_rule.json
```

### Python Interface

```python
from observability_integration import (
    initialize_observability,
    get_prometheus_metrics,
    query_jaeger_traces
)

# Initialize observability
initialize_observability(service_name="my-service")

# Query metrics programmatically
metrics = get_prometheus_metrics(
    query="rate(primitive_requests_total[5m])",
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now()
)

# Query traces
traces = query_jaeger_traces(
    service="my-service",
    operation="workflow.execute",
    limit=10
)
```

---

## Monitoring

### Health Checks

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Jaeger
curl http://localhost:16686/

# Check Grafana
curl http://localhost:3000/api/health

# All-in-one health check
./scripts/check-observability-health.sh
```

### Key Metrics

**Prometheus Endpoint:** `http://localhost:9090/metrics`

**TTA.dev Workflow Metrics:**
- `primitive_duration_seconds` - Execution latency by primitive
- `primitive_requests_total` - Request count by primitive
- `primitive_errors_total` - Error count by primitive
- `workflow_active_requests` - Current in-flight workflows
- `cache_hit_rate` - Cache effectiveness

**Infrastructure Metrics:**
- `up` - Service availability (1=up, 0=down)
- `prometheus_tsdb_storage_blocks_bytes` - Storage usage
- `jaeger_spans_received_total` - Traces received

### Logs

```bash
# Prometheus logs
docker logs prometheus -f

# Jaeger logs
docker logs jaeger -f

# Grafana logs
docker logs grafana -f

# All service logs
docker-compose -f docker-compose.observability.yml logs -f
```

---

## Observability

### Pre-Built Dashboards

Grafana dashboards included:

1. **TTA.dev Workflows** - Workflow execution overview
   - Request rate, latency percentiles (p50, p90, p95, p99)
   - Error rates and success rates
   - Active workflows and throughput

2. **Primitive Performance** - Per-primitive metrics
   - Execution duration by primitive type
   - Cache hit rates
   - Retry/fallback frequencies

3. **Infrastructure Health** - Service health monitoring
   - Service uptime
   - Resource usage (CPU, memory)
   - Network I/O

**Import dashboards:**
```bash
# Dashboards auto-loaded from config/grafana/dashboards/
# Or manually import via Grafana UI
```

### Alert Rules

**Prometheus alert rules** (`config/prometheus/alerts.yml`):

```yaml
groups:
  - name: tta_dev_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(primitive_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowPrimitive
        expr: histogram_quantile(0.95, primitive_duration_seconds_bucket) > 5
        for: 10m
        annotations:
          summary: "Primitive p95 latency > 5s"
```

---

## Scaling

### Horizontal Scaling (Not Recommended)

Observability stack typically runs as singleton:
- Prometheus has single-node architecture
- Jaeger supports multi-instance but complex
- Grafana can scale but needs shared backend

**For high-scale deployments:**
- Consider managed services (Datadog, New Relic)
- Use Thanos for Prometheus federation
- Deploy Jaeger with Cassandra/Elasticsearch backend

### Vertical Scaling

Increase resources per service:

```yaml
# docker-compose.observability.yml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

**Recommended Resources:**
- **Development:** 2 CPU, 4GB RAM
- **Production:** 4-8 CPU, 8-16GB RAM
- **High-Scale:** 16+ CPU, 32+ GB RAM

---

## Backup & Recovery

### Backup Prometheus Data

```bash
# Snapshot Prometheus data
docker exec prometheus promtool tsdb snapshot /prometheus

# Backup snapshot
docker cp prometheus:/prometheus/snapshots/ ./backups/prometheus/

# Automated backup
./scripts/backup-observability.sh
```

### Backup Grafana Dashboards

```bash
# Export dashboards
curl -u admin:admin http://localhost:3000/api/search?type=dash-db \
  | jq -r '.[].uid' \
  | xargs -I {} curl -u admin:admin http://localhost:3000/api/dashboards/uid/{} \
  > backups/grafana_dashboards.json
```

### Recovery

```bash
# Restore Prometheus from snapshot
docker cp ./backups/prometheus/snapshots/ prometheus:/prometheus/
docker restart prometheus

# Restore Grafana dashboards
curl -X POST -u admin:admin http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @backups/grafana_dashboards.json
```

---

## Troubleshooting

### Issue: Services Won't Start

**Symptom:** `docker-compose up` fails
**Solution:**
1. Check Docker is running: `docker ps`
2. Check port conflicts: `lsof -i :9090`
3. Review logs: `docker-compose logs`
4. Restart Docker daemon

### Issue: No Metrics Appearing

**Symptom:** Prometheus shows no data
**Solution:**
1. Verify primitives exporting metrics: Check `http://localhost:9464/metrics`
2. Check Prometheus targets: `http://localhost:9090/targets`
3. Verify network connectivity
4. Check `prometheus.yml` scrape config

### Issue: Traces Not Showing in Jaeger

**Symptom:** Jaeger UI is empty
**Solution:**
1. Verify OTLP collector running: `curl http://localhost:4318/v1/traces`
2. Check primitives have tracing enabled
3. Verify trace IDs in logs
4. Check Jaeger storage backend

### Issue: High Memory Usage

**Symptom:** Prometheus uses excessive memory
**Solution:**
1. Reduce retention period: `--storage.tsdb.retention.time=7d`
2. Limit scrape frequency
3. Add resource limits in docker-compose.yml
4. Consider using Thanos for long-term storage

---

## Performance Tuning

### Prometheus Optimization

```yaml
# prometheus.yml
global:
  scrape_interval: 15s      # Balance freshness vs load
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tta-dev'
    scrape_interval: 10s    # Higher frequency for critical metrics
```

### Jaeger Optimization

```bash
# Use sampling for high-volume traces
export JAEGER_SAMPLER_TYPE="probabilistic"
export JAEGER_SAMPLER_PARAM="0.1"  # Sample 10% of traces
```

### Resource Limits

```yaml
# docker-compose.observability.yml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## Security

### Authentication

**Grafana:**
- Default: admin/admin
- Change on first login
- Configure LDAP/OAuth for production

**Prometheus:**
- No built-in auth (use reverse proxy)
- Example nginx config in `config/nginx/prometheus.conf`

**Jaeger:**
- UI has no auth by default
- Use OAuth2 proxy for production

### Network Security

```yaml
# Restrict access via firewall
# Only expose ports on localhost in production
services:
  prometheus:
    ports:
      - "127.0.0.1:9090:9090"  # Localhost only

  jaeger:
    ports:
      - "127.0.0.1:16686:16686"  # Localhost only
```

### TLS Configuration

```yaml
# prometheus.yml
tls_config:
  cert_file: /etc/prometheus/certs/server.crt
  key_file: /etc/prometheus/certs/server.key
```

---

## Related Services

- [[TTA.dev/Services/RedisCache]] - Often monitored via this stack
- Docker - Required runtime dependency

---

## Related Primitives

Primitives that integrate with this service:

- [[TTA.dev/Primitives/Core/WorkflowPrimitive]] - Base observability integration
- [[TTA.dev/Primitives/Observability/InstrumentedPrimitive]] - Enhanced tracing
- All primitives - Automatic metrics export

---

## Source Code

**Location:** `docker-compose.observability.yml`
**Configuration:** `config/prometheus/`, `config/grafana/`
**Scripts:** `scripts/setup-observability.sh`, `scripts/check-observability-health.sh`

---

## External Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry](https://opentelemetry.io/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## Quick Start Commands

```bash
# Setup (one-time)
./scripts/setup-observability.sh

# Start services
docker-compose -f docker-compose.observability.yml up -d

# Check health
./scripts/check-observability-health.sh

# View logs
docker-compose -f docker-compose.observability.yml logs -f

# Stop services
docker-compose -f docker-compose.observability.yml down

# Full cleanup (removes data!)
docker-compose -f docker-compose.observability.yml down -v
```

---

## Tags

#service #observability #monitoring #prometheus #jaeger #grafana #infrastructure
