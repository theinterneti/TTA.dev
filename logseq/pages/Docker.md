# Docker

**Tag page for Docker containers, compose, and observability infrastructure**

---

## Overview

**Docker** in TTA.dev includes:
- 🐳 Observability stack containers
- 📦 Development environment
- 🔧 Container orchestration
- 📊 Monitoring infrastructure
- 🚀 Deployment containers

**Goal:** Containerized infrastructure for development and production observability.

**See:** [[Infrastructure]], [[TTA.dev/Observability]]

---

## Pages Tagged with #Docker

{{query (page-tags [[Docker]])}}

---

## Docker Infrastructure

### 1. Observability Stack

**Docker Compose configuration:**

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    restart: unless-stopped

  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
      - "8888:8888"    # Metrics
    depends_on:
      - jaeger
      - prometheus
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped

  pushgateway:
    image: prom/pushgateway:latest
    ports:
      - "9091:9091"
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

**See:** `docker-compose.test.yml`

---

### 2. Starting the Stack

**Quick start:**

```bash
# Start all services
docker-compose -f docker-compose.test.yml up -d

# View logs
docker-compose -f docker-compose.test.yml logs -f

# Check status
docker-compose -f docker-compose.test.yml ps

# Stop services
docker-compose -f docker-compose.test.yml down

# Stop and remove volumes
docker-compose -f docker-compose.test.yml down -v
```

---

**Service URLs:**

```
Prometheus: http://localhost:9090
Grafana:    http://localhost:3000 (admin/admin)
Jaeger:     http://localhost:16686
Loki:       http://localhost:3100
Pushgateway: http://localhost:9091
```

---

### 3. Prometheus Configuration

**Scrape configuration:**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # TTA.dev primitives metrics
  - job_name: 'tta-primitives'
    static_configs:
      - targets: ['host.docker.internal:9464']

  # Application metrics
  - job_name: 'application'
    static_configs:
      - targets: ['host.docker.internal:8000']

  # Pushgateway for batch jobs
  - job_name: 'pushgateway'
    honor_labels: true
    static_configs:
      - targets: ['pushgateway:9091']
```

**See:** `prometheus.yml`

---

### 4. Grafana Dashboards

**Dashboard provisioning:**

```yaml
# grafana/dashboards/dashboard.yaml
apiVersion: 1

providers:
  - name: 'TTA.dev Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

**Datasource provisioning:**

```yaml
# grafana/datasources/datasource.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
```

---

### 5. OpenTelemetry Collector

**Collector configuration:**

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"

  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, logging]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
```

---

## Docker Patterns

### Pattern: Local Development Stack

**Complete local environment:**

```bash
# 1. Start observability stack
docker-compose -f docker-compose.test.yml up -d

# 2. Initialize observability in code
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    prometheus_port=9464
)

# 3. Run application
uv run python app.py

# 4. View traces in Jaeger
open http://localhost:16686

# 5. View metrics in Prometheus
open http://localhost:9090

# 6. View dashboards in Grafana
open http://localhost:3000
```

---

### Pattern: Production-Like Testing

**Test with production infrastructure:**

```python
import pytest
from observability_integration import initialize_observability

@pytest.fixture(scope="session")
def observability_stack():
    """Start Docker stack for tests."""
    import subprocess

    # Start stack
    subprocess.run([
        "docker-compose", "-f", "docker-compose.test.yml",
        "up", "-d"
    ], check=True)

    # Wait for services
    time.sleep(10)

    # Initialize observability
    initialize_observability(service_name="test")

    yield

    # Teardown
    subprocess.run([
        "docker-compose", "-f", "docker-compose.test.yml",
        "down", "-v"
    ], check=True)

async def test_with_observability(observability_stack):
    """Test with full observability."""
    workflow = step1 >> step2 >> step3
    result = await workflow.execute(data, context)

    # Verify traces in Jaeger
    # Verify metrics in Prometheus
    assert result is not None
```

---

### Pattern: Persistent Observability

**Long-running observability:**

```bash
# Start with persistent volumes
docker-compose -f docker-compose.test.yml up -d

# Metrics persist across restarts
# Dashboards saved in Grafana
# Traces available for retention period

# Backup volumes
docker run --rm \
  -v tta-dev_prometheus-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz /data

# Restore volumes
docker run --rm \
  -v tta-dev_prometheus-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/prometheus-backup.tar.gz -C /
```

---

## Docker Best Practices

### ✅ DO

**Use Named Volumes:**
```yaml
# ✅ Good: Named volumes persist data
volumes:
  prometheus-data:
  grafana-data:

# Data survives container recreation
```

**Set Restart Policies:**
```yaml
# ✅ Good: Auto-restart on failure
restart: unless-stopped

# Services recover automatically
```

**Use Health Checks:**
```yaml
# ✅ Good: Health checks
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Resource Limits:**
```yaml
# ✅ Good: Limit resources
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

---

### ❌ DON'T

**Don't Use Latest Tag in Production:**
```yaml
# ❌ Bad: Unpredictable updates
image: prometheus:latest

# ✅ Good: Pin versions
image: prometheus:v2.45.0
```

**Don't Store Secrets in Images:**
```yaml
# ❌ Bad: Secrets in image
ENV API_KEY=secret-key

# ✅ Good: Use secrets management
env_file:
  - .env.secret
```

**Don't Run as Root:**
```dockerfile
# ❌ Bad: Root user
USER root

# ✅ Good: Non-root user
USER nobody
```

---

## Docker Metrics

### Container Metrics

```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Container memory usage
container_memory_usage_bytes / container_spec_memory_limit_bytes

# Container restart count
container_restart_count

# Network I/O
rate(container_network_transmit_bytes_total[5m])
rate(container_network_receive_bytes_total[5m])
```

---

### Observability Stack Health

```promql
# Prometheus up
up{job="prometheus"}

# Grafana up
up{job="grafana"}

# Jaeger up
up{job="jaeger"}

# Scrape duration
scrape_duration_seconds{job="tta-primitives"}
```

---

## Docker Commands Reference

### Common Operations

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# View logs
docker logs -f <container-name>

# Execute command in container
docker exec -it <container-name> /bin/sh

# Inspect container
docker inspect <container-name>

# View container stats
docker stats

# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune
```

---

### Docker Compose Operations

```bash
# Start services in background
docker-compose up -d

# Start specific service
docker-compose up -d prometheus

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f prometheus

# Scale service
docker-compose up -d --scale worker=3

# Remove everything
docker-compose down -v --remove-orphans
```

---

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port
lsof -i :9090

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "9091:9090"  # Map to different host port
```

**Container Won't Start:**
```bash
# Check logs
docker-compose logs <service-name>

# Check container status
docker-compose ps

# Restart service
docker-compose restart <service-name>

# Recreate container
docker-compose up -d --force-recreate <service-name>
```

**Volume Issues:**
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect <volume-name>

# Remove volume
docker volume rm <volume-name>

# Backup volume
docker run --rm -v <volume-name>:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
```

---

## Related Concepts

- [[Infrastructure]] - Infrastructure setup
- [[TTA.dev/Observability]] - Observability guide
- [[Production]] - Production deployment
- [[Prometheus]] - Prometheus metrics
- [[Grafana]] - Grafana dashboards

---

## Documentation

- `docker-compose.test.yml` - Compose configuration
- `prometheus.yml` - Prometheus config
- `otel-collector-config.yaml` - OTLP collector config
- [[TTA.dev/Observability]] - Observability setup guide

---

**Tags:** #docker #containers #observability #infrastructure #monitoring #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Docker]]
