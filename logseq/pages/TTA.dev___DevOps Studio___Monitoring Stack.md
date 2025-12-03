# TTA.dev Monitoring Stack Guide

component-type:: observability
tech-stack:: prometheus, grafana, jaeger, loki, opentelemetry
stage:: all-stages
complexity:: intermediate-to-advanced
related:: [[TTA.dev/DevOps Studio Architecture]], [[TTA.dev/Packages/tta-observability-integration]], [[TTA.dev/Observability]]

Complete monitoring stack implementation with stage-appropriate deployment patterns

---

## 🎯 Monitoring Stack Overview

The TTA.dev monitoring stack provides **comprehensive observability** across all development stages, from local development to production operations. Built on industry-standard tools with **intelligent defaults** and **progressive complexity**.

### Core Philosophy

- **Stage-Appropriate Monitoring** - Different complexity levels for different stages
- **Production-Ready from Day One** - Battle-tested components and configurations
- **Cost-Conscious** - Optimized resource usage and retention policies
- **Developer-Friendly** - Easy setup with minimal configuration
- **AI-Agent Compatible** - Designed for automated operations and analysis

### Technology Stack

- **Prometheus** - Metrics collection, storage, and alerting
- **Grafana** - Visualization, dashboards, and unified observability
- **Jaeger** - Distributed tracing and performance analysis
- **Loki** - Log aggregation and analysis
- **OpenTelemetry** - Unified observability data collection
- **AlertManager** - Intelligent alert routing and notification

---

## 🏗️ Stack Architecture by Stage

### Architecture Evolution

```text
┌─────────────────────────────────────────────────────────────────┐
│                  PRODUCTION STAGE                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │  Grafana    │ │ Prometheus  │ │   Jaeger    │ │  Loki    │  │
│  │ Multi-tenant│ │ Federation  │ │ Distributed │ │ Cluster  │  │
│  │ RBAC + SSO  │ │ HA + Remote │ │ Elasticsearch│ │ S3 Store │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                   STAGING STAGE                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │  Grafana    │ │ Prometheus  │ │   Jaeger    │ │  Loki    │  │
│  │ Production  │ │ Single Node │ │ All-in-One  │ │ Single   │  │
│  │ Dashboards  │ │ 30d Retain  │ │ + Storage   │ │ Node     │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                 TESTING STAGE                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Grafana    │ │ Prometheus  │ │   Jaeger    │              │
│  │ Basic Setup │ │ 7d Retention│ │ All-in-One  │              │
│  │ Dev Dash    │ │ Local Store │ │ Memory Store│              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│               DEVELOPMENT STAGE                                 │
│  ┌─────────────┐ ┌─────────────┐                              │
│  │ Development │ │ Prometheus  │                              │
│  │ Grafana     │ │ Local       │                              │
│  │ + Jaeger UI │ │ 1d Retain   │                              │
│  └─────────────┘ └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Stage-Specific Deployments

### Development Stage - Local Monitoring

**Purpose:** Immediate feedback during development with minimal resource usage

**Components:**

- Prometheus (local, 1-day retention)
- Jaeger All-in-One (memory storage)
- Basic Grafana (development dashboards)

**Setup:**

```bash
# Quick start for development
cd platform/primitives
docker-compose -f docker-compose.integration.yml up -d

# Access services
# Prometheus: http://localhost:9090
# Jaeger UI: http://localhost:16686
# Grafana: http://localhost:3000 (admin/admin)
```

**Configuration:**

```yaml
# docker-compose.integration.yml (simplified)
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:v2.48.1
    ports: ["9090:9090"]
    volumes:
      - ./config/prometheus-dev.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=1d'
      - '--web.enable-lifecycle'

  jaeger:
    image: jaegertracing/all-in-one:1.52
    ports:
      - "16686:16686" # UI
      - "14268:14268" # Collector
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  grafana:
    image: grafana/grafana:10.2.3
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./config/grafana-dev-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
```

**Prometheus Configuration:**

```yaml
# config/prometheus-dev.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tta-dev-primitives'
    static_configs:
      - targets: ['host.docker.internal:9464']
    scrape_interval: 5s
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

**Benefits:**
- ✅ **Fast Setup** - Up and running in <1 minute
- ✅ **Low Resource Usage** - ~500MB RAM total
- ✅ **Immediate Feedback** - Real-time metrics during development
- ✅ **TTA.dev Integration** - Automatic primitive metrics collection

---

### Testing Stage - CI/CD Integration

**Purpose:** Automated testing with observability validation and performance benchmarks

**Components:**
- Prometheus (7-day retention, persistent storage)
- Jaeger All-in-One (file storage)
- Grafana (testing dashboards)

**CI/CD Integration:**

```yaml
# .github/workflows/observability-tests.yml
name: Observability Tests

on:
  push:
    branches: [main, experiment/*]
  pull_request:
    branches: [main]

jobs:
  monitoring-stack-test:
    runs-on: ubuntu-latest
    services:
      prometheus:
        image: prom/prometheus:v2.48.1
        ports:
          - 9090:9090
        volumes:
          - ${{ github.workspace }}/config/prometheus-ci.yml:/etc/prometheus/prometheus.yml:ro

      jaeger:
        image: jaegertracing/all-in-one:1.52
        ports:
          - 16686:16686
          - 14268:14268
        env:
          COLLECTOR_OTLP_ENABLED: true

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python Environment
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          pip install uv
          uv sync --all-extras

      - name: Start Application with Observability
        run: |
          # Start app with observability enabled
          OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:14268/api/traces \
          PROMETHEUS_PORT=9464 \
          uv run python -m pytest tests/integration/test_observability.py &

          # Wait for metrics to be available
          sleep 10

      - name: Validate Metrics Collection
        run: |
          # Check Prometheus has TTA.dev metrics
          curl -f http://localhost:9090/api/v1/query?query=tta_primitive_executions_total
          curl -f http://localhost:9090/api/v1/query?query=tta_cache_hit_ratio
          curl -f http://localhost:9090/api/v1/query?query=tta_router_model_selection_total

      - name: Validate Tracing
        run: |
          # Check Jaeger has traces
          curl -f http://localhost:16686/api/services
          curl -f http://localhost:16686/api/traces?service=tta-dev-primitives

      - name: Performance Benchmarks
        run: |
          # Run performance tests with metrics collection
          uv run python tests/benchmarks/primitive_performance.py

          # Validate performance metrics are within acceptable ranges
          python scripts/validate_performance_metrics.py
```

**Testing Configuration:**

```yaml
# config/prometheus-ci.yml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'tta-integration-tests'
    static_configs:
      - targets: ['localhost:9464']
    scrape_interval: 1s
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

# Alert rules for CI/CD
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

**Benefits:**
- ✅ **Automated Validation** - Observability tested in every PR
- ✅ **Performance Regression Detection** - Benchmarks with metrics
- ✅ **Integration Testing** - Full stack observability validation
- ✅ **Quality Gates** - Fail builds if observability broken

---

### Staging Stage - Production Preview

**Purpose:** Full production environment testing with production-like monitoring

**Components:**
- Prometheus (30-day retention, persistent storage)
- Jaeger with Elasticsearch backend
- Grafana (production dashboards)
- AlertManager (test alert routing)

**Kubernetes Deployment:**

```yaml
# k8s/staging/monitoring/prometheus.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: tta-staging
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: 'tta-staging'
        environment: 'staging'

    rule_files:
      - "/etc/prometheus/rules/*.yml"

    scrape_configs:
      - job_name: 'kubernetes-pods'
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

      - job_name: 'tta-applications'
        kubernetes_sd_configs:
          - role: endpoints
            namespaces:
              names:
                - tta-staging
        relabel_configs:
          - source_labels: [__meta_kubernetes_service_label_app]
            action: keep
            regex: tta-.*

    alerting:
      alertmanagers:
        - kubernetes_sd_configs:
            - role: pod
              namespaces:
                names:
                  - tta-staging
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_app]
              action: keep
              regex: alertmanager
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: tta-staging
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
        image: prom/prometheus:v2.48.1
        ports:
        - containerPort: 9090
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
          - '--storage.tsdb.retention.time=30d'
          - '--web.console.libraries=/usr/share/prometheus/console_libraries'
          - '--web.console.templates=/usr/share/prometheus/consoles'
          - '--web.enable-lifecycle'
          - '--storage.tsdb.min-block-duration=2h'
          - '--storage.tsdb.max-block-duration=2h'
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
        resources:
          requests:
            memory: 1Gi
            cpu: 500m
          limits:
            memory: 2Gi
            cpu: 1000m
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        persistentVolumeClaim:
          claimName: prometheus-storage
```

**Grafana Dashboard Configuration:**

```yaml
# k8s/staging/monitoring/grafana-dashboards.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tta-staging-dashboards
  namespace: tta-staging
data:
  tta-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "TTA.dev Staging Overview",
        "tags": ["tta", "staging"],
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Primitive Execution Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "rate(tta_primitive_executions_total[5m])",
                "legendFormat": "{{primitive_type}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "reqps",
                "min": 0
              }
            }
          },
          {
            "id": 2,
            "title": "Cache Hit Ratio",
            "type": "stat",
            "targets": [
              {
                "expr": "tta_cache_hit_ratio",
                "legendFormat": "Hit Ratio"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "yellow", "value": 50},
                    {"color": "green", "value": 80}
                  ]
                }
              }
            }
          },
          {
            "id": 3,
            "title": "Router Model Selection",
            "type": "piechart",
            "targets": [
              {
                "expr": "rate(tta_router_model_selection_total[1h])",
                "legendFormat": "{{model}}"
              }
            ]
          },
          {
            "id": 4,
            "title": "Primitive Execution Duration",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(tta_primitive_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              },
              {
                "expr": "histogram_quantile(0.50, rate(tta_primitive_duration_seconds_bucket[5m]))",
                "legendFormat": "50th percentile"
              }
            ],
            "yAxes": [
              {
                "unit": "s",
                "min": 0
              }
            ]
          }
        ],
        "time": {
          "from": "now-1h",
          "to": "now"
        },
        "refresh": "10s"
      }
    }
```

**Benefits:**
- ✅ **Production Testing** - Full monitoring stack validation
- ✅ **Alert Testing** - Validate alert rules and routing
- ✅ **Dashboard Validation** - Test production dashboards
- ✅ **Performance Analysis** - Staging performance characteristics

---

### Production Stage - Full Observability

**Purpose:** High-availability, scalable monitoring with comprehensive alerting

**Components:**
- Prometheus Federation (HA setup)
- Jaeger with distributed storage
- Grafana with RBAC and SSO
- Loki for log aggregation
- AlertManager cluster

**High-Availability Prometheus:**

```yaml
# k8s/production/monitoring/prometheus-ha.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: prometheus
  namespace: tta-production
spec:
  serviceName: prometheus-headless
  replicas: 2
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
        image: prom/prometheus:v2.48.1
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
          - '--storage.tsdb.retention.time=90d'
          - '--web.console.libraries=/usr/share/prometheus/console_libraries'
          - '--web.console.templates=/usr/share/prometheus/consoles'
          - '--web.enable-lifecycle'
          - '--web.enable-admin-api'
          - '--storage.tsdb.min-block-duration=2h'
          - '--storage.tsdb.max-block-duration=2h'
          - '--web.external-url=https://prometheus.tta.dev'
        ports:
        - containerPort: 9090
          name: web
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: rules
          mountPath: /etc/prometheus/rules
        - name: storage
          mountPath: /prometheus
        resources:
          requests:
            memory: 4Gi
            cpu: 2000m
          limits:
            memory: 8Gi
            cpu: 4000m
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 9090
          initialDelaySeconds: 30
          timeoutSeconds: 30
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 9090
          initialDelaySeconds: 30
          timeoutSeconds: 30
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: rules
        configMap:
          name: prometheus-rules
  volumeClaimTemplates:
  - metadata:
      name: storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 200Gi
      storageClassName: fast-ssd
```

**Production Alert Rules:**

```yaml
# k8s/production/monitoring/alert-rules.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: tta-production
data:
  tta-applications.yml: |
    groups:
    - name: tta-applications
      rules:
      # High-level application health
      - alert: TTAServiceDown
        expr: up{job=~"tta-.*"} == 0
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "TTA service {{ $labels.job }} is down"
          description: "{{ $labels.job }} has been down for more than 2 minutes"
          runbook_url: "https://runbooks.tta.dev/service-down"

      # Performance alerts
      - alert: TTAHighLatency
        expr: histogram_quantile(0.95, rate(tta_primitive_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High latency in TTA primitives"
          description: "95th percentile latency is {{ $value }}s for primitive {{ $labels.primitive_type }}"
          runbook_url: "https://runbooks.tta.dev/high-latency"

      # Cost optimization alerts
      - alert: TTACacheHitRateLow
        expr: tta_cache_hit_ratio < 50
        for: 10m
        labels:
          severity: warning
          team: cost-optimization
        annotations:
          summary: "Low cache hit ratio in TTA"
          description: "Cache hit ratio is {{ $value }}% which may indicate increased costs"
          runbook_url: "https://runbooks.tta.dev/cache-optimization"

      # Error rate alerts
      - alert: TTAHighErrorRate
        expr: rate(tta_primitive_errors_total[5m]) / rate(tta_primitive_executions_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High error rate in TTA primitives"
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.primitive_type }}"
          runbook_url: "https://runbooks.tta.dev/high-error-rate"

      # Resource utilization
      - alert: TTAResourceUtilizationHigh
        expr: tta_resource_utilization_ratio > 0.9
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High resource utilization in TTA"
          description: "{{ $labels.resource_type }} utilization is {{ $value | humanizePercentage }}"
          runbook_url: "https://runbooks.tta.dev/resource-scaling"

  tta-infrastructure.yml: |
    groups:
    - name: tta-infrastructure
      rules:
      # Kubernetes cluster health
      - alert: KubernetesNodeNotReady
        expr: kube_node_status_condition{condition="Ready",status="true"} == 0
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Kubernetes node not ready"
          description: "Node {{ $labels.node }} has been not ready for more than 5 minutes"

      # Database connectivity
      - alert: DatabaseConnectionFailure
        expr: tta_database_connection_failures_total > 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Database connection failures detected"
          description: "{{ $value }} database connection failures in the last minute"
          runbook_url: "https://runbooks.tta.dev/database-issues"
```

**Production Grafana Configuration:**

```yaml
# k8s/production/monitoring/grafana-production.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-config
  namespace: tta-production
data:
  grafana.ini: |
    [server]
    domain = grafana.tta.dev
    root_url = https://grafana.tta.dev

    [security]
    admin_user = admin
    admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
    secret_key = ${GF_SECURITY_SECRET_KEY}

    [auth]
    disable_login_form = false
    disable_signout_menu = false

    [auth.generic_oauth]
    enabled = true
    name = OAuth
    allow_sign_up = true
    client_id = ${GF_AUTH_GENERIC_OAUTH_CLIENT_ID}
    client_secret = ${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET}
    scopes = openid profile email
    auth_url = https://auth.tta.dev/oauth/authorize
    token_url = https://auth.tta.dev/oauth/token
    api_url = https://auth.tta.dev/oauth/userinfo
    role_attribute_path = contains(groups[*], 'tta-admin') && 'Admin' || contains(groups[*], 'tta-editor') && 'Editor' || 'Viewer'

    [users]
    allow_sign_up = false
    auto_assign_org = true
    auto_assign_org_role = Viewer

    [smtp]
    enabled = true
    host = ${GF_SMTP_HOST}:587
    user = ${GF_SMTP_USER}
    password = ${GF_SMTP_PASSWORD}
    from_address = grafana@tta.dev
    from_name = TTA.dev Grafana

    [alerting]
    enabled = true
    execute_alerts = true

    [metrics]
    enabled = true

    [log]
    mode = console
    level = info

  dashboards.yml: |
    apiVersion: 1
    providers:
    - name: 'tta-production-dashboards'
      orgId: 1
      folder: 'TTA Production'
      type: file
      disableDeletion: false
      editable: true
      options:
        path: /var/lib/grafana/dashboards/tta-production

  datasources.yml: |
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus:9090
      isDefault: true
      jsonData:
        timeInterval: 15s
        httpMethod: POST

    - name: Jaeger
      type: jaeger
      access: proxy
      url: http://jaeger-query:16686
      jsonData:
        tracesToLogs:
          datasourceUid: loki
          tags: ['job', 'instance', 'pod', 'namespace']

    - name: Loki
      type: loki
      access: proxy
      url: http://loki:3100
      jsonData:
        derivedFields:
        - datasourceUid: jaeger
          matcherRegex: '"trace_id":"(\w+)"'
          name: TraceID
          url: '$${__value.raw}'
```

**Benefits:**
- ✅ **High Availability** - Multi-replica Prometheus with failover
- ✅ **Enterprise Security** - SSO integration and RBAC
- ✅ **Comprehensive Alerting** - 24/7 monitoring with intelligent routing
- ✅ **Long-term Storage** - 90-day retention with efficient compression
- ✅ **Multi-tenant** - Isolated monitoring for different teams/projects

---

## 🎯 TTA.dev Observability Integration

### Automatic Primitive Instrumentation

**Built-in Metrics Collection:**

```python
# From tta-observability-integration package
from observability_integration import initialize_observability
from observability_integration.primitives import (
    RouterPrimitive,
    CachePrimitive,
    TimeoutPrimitive,
)

# Initialize observability (call once at startup)
success = initialize_observability(
    service_name="tta-production",
    environment="production",
    enable_prometheus=True,
    prometheus_port=9464
)

# All primitives automatically expose metrics
workflow = (
    RouterPrimitive(routes={
        "fast": gpt4_mini,
        "quality": gpt4,
        "cost": claude_haiku
    }) >>
    CachePrimitive(expensive_operation, ttl_seconds=3600) >>
    TimeoutPrimitive(timeout_seconds=30)
)

# Metrics automatically available at /metrics endpoint:
# - tta_primitive_executions_total{primitive_type="router", model="gpt4_mini"}
# - tta_cache_hit_ratio{primitive_type="cache"}
# - tta_primitive_duration_seconds{primitive_type="timeout"}
# - tta_router_model_selection_total{model="gpt4_mini", reason="fast"}
```

### Custom Metrics for Business Logic

**Application-Specific Monitoring:**

```python
from observability_integration.metrics import get_meter
from opentelemetry import metrics

# Get TTA.dev meter instance
meter = get_meter("tta-business-logic")

# Create custom metrics
user_sessions = meter.create_counter(
    "tta_user_sessions_total",
    description="Total number of user sessions started"
)

narrative_quality = meter.create_histogram(
    "tta_narrative_quality_score",
    description="Quality score of generated narratives"
)

cost_per_session = meter.create_histogram(
    "tta_cost_per_session_dollars",
    description="Cost per user session in dollars"
)

# Use in application code
async def handle_user_session(user_id: str, session_data: dict):
    user_sessions.add(1, {"user_type": "premium"})

    # Generate narrative with cost tracking
    start_cost = get_current_cost()
    narrative = await narrative_workflow.execute(session_data, context)
    end_cost = get_current_cost()

    # Record business metrics
    narrative_quality.record(narrative.quality_score)
    cost_per_session.record(end_cost - start_cost)

    return narrative
```

### Distributed Tracing Integration

**Automatic Trace Propagation:**

```python
from tta_dev_primitives import WorkflowContext
from observability_integration.tracing import get_tracer

tracer = get_tracer("tta-main-workflow")

async def process_user_request(request_data: dict):
    with tracer.start_as_current_span("user_request_processing") as span:
        span.set_attribute("user_id", request_data["user_id"])
        span.set_attribute("request_type", request_data["type"])

        # Create context with trace information
        context = WorkflowContext(
            correlation_id=f"req-{uuid.uuid4()}",
            user_id=request_data["user_id"],
            trace_id=span.get_span_context().trace_id
        )

        # All primitives in workflow automatically inherit tracing
        result = await main_workflow.execute(request_data, context)

        span.set_attribute("narrative_length", len(result.narrative))
        span.set_attribute("total_cost", result.cost)

        return result
```

---

## 📊 Dashboard Gallery

### Executive Dashboard

**High-level KPIs and Business Metrics:**

```json
{
  "dashboard": {
    "title": "TTA.dev Executive Overview",
    "panels": [
      {
        "title": "Active Users (24h)",
        "type": "stat",
        "targets": [{"expr": "increase(tta_user_sessions_total[24h])"}],
        "fieldConfig": {"defaults": {"unit": "short"}}
      },
      {
        "title": "Revenue Impact",
        "type": "stat",
        "targets": [{"expr": "sum(increase(tta_cost_per_session_dollars[24h]))"}],
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}}
      },
      {
        "title": "Cost Optimization Savings",
        "type": "stat",
        "targets": [{"expr": "tta_cache_hit_ratio * 100"}],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 40},
                {"color": "green", "value": 60}
              ]
            }
          }
        }
      },
      {
        "title": "Service Availability",
        "type": "stat",
        "targets": [{"expr": "avg(up{job=~'tta-.*'}) * 100"}],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 99,
            "max": 100
          }
        }
      }
    ]
  }
}
```

### Engineering Dashboard

**Technical Metrics and Performance:**

```json
{
  "dashboard": {
    "title": "TTA.dev Engineering Metrics",
    "panels": [
      {
        "title": "Primitive Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tta_primitive_executions_total[5m])",
            "legendFormat": "{{primitive_type}}"
          }
        ]
      },
      {
        "title": "Error Rate by Primitive",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tta_primitive_errors_total[5m]) / rate(tta_primitive_executions_total[5m]) * 100",
            "legendFormat": "{{primitive_type}} errors"
          }
        ],
        "yAxes": [{"unit": "percent"}]
      },
      {
        "title": "Cache Performance",
        "type": "graph",
        "targets": [
          {"expr": "tta_cache_hit_ratio", "legendFormat": "Hit Ratio"},
          {"expr": "rate(tta_cache_size_bytes[5m])", "legendFormat": "Cache Size"}
        ]
      },
      {
        "title": "Router Model Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "rate(tta_router_model_selection_total[1h])",
            "legendFormat": "{{model}}"
          }
        ]
      }
    ]
  }
}
```

### Cost Optimization Dashboard

**Cost Analysis and Optimization Tracking:**

```json
{
  "dashboard": {
    "title": "TTA.dev Cost Optimization",
    "panels": [
      {
        "title": "Cost Savings from Caching",
        "type": "stat",
        "targets": [
          {
            "expr": "tta_cache_hit_ratio * avg(tta_cost_per_session_dollars) * increase(tta_user_sessions_total[24h])",
            "legendFormat": "Savings (24h)"
          }
        ],
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}}
      },
      {
        "title": "Model Selection Cost Impact",
        "type": "bargraph",
        "targets": [
          {
            "expr": "avg by (model) (tta_primitive_duration_seconds) * on (model) group_left rate(tta_router_model_selection_total[1h])",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "Resource Utilization vs Cost",
        "type": "graph",
        "targets": [
          {"expr": "tta_resource_utilization_ratio", "legendFormat": "Utilization"},
          {"expr": "rate(tta_cost_per_session_dollars[5m])", "legendFormat": "Cost Rate"}
        ]
      }
    ]
  }
}
```

---

## 🚨 Alerting Strategy

### Alert Severity Levels

**Critical Alerts (P0):**
- Service completely down
- Data loss or corruption
- Security breaches
- >5% error rate sustained >5 minutes

**Warning Alerts (P1):**
- Performance degradation
- Resource exhaustion approaching
- Cache hit ratio below thresholds
- Alert rule failures

**Info Alerts (P2):**
- Capacity planning notifications
- Scheduled maintenance reminders
- Deployment completion notifications

### Alert Routing Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.tta.dev:587'
  smtp_from: 'alerts@tta.dev'
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 0s
    repeat_interval: 5m
  - match:
      team: platform
    receiver: 'platform-team'
  - match:
      team: cost-optimization
    receiver: 'cost-team'

receivers:
- name: 'default'
  slack_configs:
  - channel: '#tta-alerts'
    title: 'TTA.dev Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'critical-alerts'
  slack_configs:
  - channel: '#tta-critical'
    title: '🚨 CRITICAL: TTA.dev Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}{{ end }}'
  pagerduty_configs:
  - service_key: '${PAGERDUTY_SERVICE_KEY}'
    description: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'platform-team'
  email_configs:
  - to: 'platform-team@tta.dev'
    subject: 'TTA.dev Platform Alert'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Runbook: {{ .Annotations.runbook_url }}
      {{ end }}

- name: 'cost-team'
  slack_configs:
  - channel: '#tta-cost-optimization'
    title: 'TTA.dev Cost Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## 🎓 Best Practices

### Monitoring Design Principles

**1. Monitor User Experience, Not Just Infrastructure**
```python
# Good: Monitor end-to-end user experience
user_satisfaction_score = meter.create_histogram(
    "tta_user_satisfaction_score",
    description="User satisfaction rating (1-5)"
)

# Also good: Technical metrics that impact users
narrative_generation_time = meter.create_histogram(
    "tta_narrative_generation_seconds",
    description="Time to generate complete narrative"
)
```

**2. Design for Troubleshooting**
```python
# Include context in metrics for effective debugging
cache_misses.add(1, {
    "cache_type": "narrative",
    "user_tier": "premium",
    "narrative_complexity": "high",
    "reason": "ttl_expired"
})
```

**3. Cost-Conscious Monitoring**
```python
# Sample high-volume metrics to control costs
@sampling_rate(0.1)  # Sample 10% of requests
def record_detailed_metrics(request_data):
    detailed_timing.record(request_data.processing_time)
```

### Alert Design Guidelines

**1. Alerts Should Be Actionable**
```yaml
# Good: Specific, actionable alert
- alert: TTACacheHitRateLow
  expr: tta_cache_hit_ratio < 50
  annotations:
    summary: "Cache performance degraded - investigate immediately"
    description: "Hit ratio {{ $value }}% indicates cache inefficiency, potential 2x cost increase"
    runbook_url: "https://runbooks.tta.dev/cache-optimization"
    action: "Check cache size limits and TTL configuration"
```

**2. Group Related Alerts**
```yaml
# Group alerts to prevent alert storms
route:
  group_by: ['alertname', 'primitive_type', 'environment']
  group_wait: 30s
  group_interval: 5m
```

**3. Use Alert Inhibition**
```yaml
# Don't alert on consequences of known issues
inhibit_rules:
- source_match:
    alertname: 'TTAServiceDown'
  target_match:
    alertname: 'TTAHighLatency'
  equal: ['service', 'environment']
```

---

## 🔧 Deployment Automation

### Monitoring Stack Deployment Script

```bash
#!/bin/bash
# scripts/deploy-monitoring-stack.sh

set -euo pipefail

ENVIRONMENT=${1:-"development"}
NAMESPACE="tta-${ENVIRONMENT}"

echo "=== Deploying TTA.dev Monitoring Stack ==="
echo "Environment: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"
echo "=========================================="

# Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
echo "Deploying Prometheus..."
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
    --namespace $NAMESPACE \
    --values k8s/$ENVIRONMENT/monitoring/prometheus-values.yml \
    --wait

# Deploy Jaeger
echo "Deploying Jaeger..."
helm upgrade --install jaeger jaegertracing/jaeger \
    --namespace $NAMESPACE \
    --values k8s/$ENVIRONMENT/monitoring/jaeger-values.yml \
    --wait

# Deploy Loki (production only)
if [[ $ENVIRONMENT == "production" ]]; then
    echo "Deploying Loki..."
    helm upgrade --install loki grafana/loki-stack \
        --namespace $NAMESPACE \
        --values k8s/$ENVIRONMENT/monitoring/loki-values.yml \
        --wait
fi

# Configure Grafana dashboards
echo "Configuring Grafana dashboards..."
kubectl apply -f k8s/$ENVIRONMENT/monitoring/grafana-dashboards.yml

# Validate deployment
echo "Validating monitoring stack..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE

# Test Prometheus connectivity
PROMETHEUS_URL=$(kubectl get service prometheus -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if curl -f "http://$PROMETHEUS_URL:9090/-/healthy"; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus health check failed"
    exit 1
fi

echo "🎉 Monitoring stack deployment completed successfully!"
echo "Access URLs:"
echo "  Prometheus: http://$PROMETHEUS_URL:9090"
echo "  Grafana: http://$PROMETHEUS_URL:3000"
echo "  Jaeger: http://$PROMETHEUS_URL:16686"
```

### CI/CD Integration

```yaml
# .github/workflows/deploy-monitoring.yml
name: Deploy Monitoring Stack

on:
  push:
    branches: [main]
    paths: ['k8s/*/monitoring/**']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production

jobs:
  deploy-monitoring:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'staging' }}

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Install kubectl and helm
        run: |
          curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
          chmod +x kubectl
          sudo mv kubectl /usr/local/bin/

          curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --region us-west-2 --name tta-${{ github.event.inputs.environment || 'staging' }}

      - name: Deploy Monitoring Stack
        run: |
          ./scripts/deploy-monitoring-stack.sh ${{ github.event.inputs.environment || 'staging' }}

      - name: Run Monitoring Tests
        run: |
          # Wait for services to be ready
          kubectl wait --for=condition=ready pod -l app=prometheus -n tta-${{ github.event.inputs.environment || 'staging' }} --timeout=300s

          # Test Prometheus metrics endpoint
          kubectl port-forward service/prometheus 9090:9090 -n tta-${{ github.event.inputs.environment || 'staging' }} &
          sleep 10
          curl -f http://localhost:9090/-/healthy

          # Test Grafana
          kubectl port-forward service/grafana 3000:3000 -n tta-${{ github.event.inputs.environment || 'staging' }} &
          sleep 10
          curl -f http://localhost:3000/api/health
```

---

## 📚 Related Resources

### Core Documentation

- [[TTA.dev/DevOps Studio Architecture]] - Complete studio architecture
- [[TTA.dev/Packages/tta-observability-integration]] - TTA.dev observability integration
- [[TTA.dev/Observability]] - Observability strategy

### Implementation Guides

- [[TTA.dev/DevOps Studio/Infrastructure as Code]] - IaC setup for monitoring
- [[TTA.dev/DevOps Studio/Container Orchestration]] - Kubernetes deployment
- [[TTA.dev/DevOps Studio/Security Pipeline]] - Security monitoring

### Stage Guides

- [[TTA.dev/Stage Guides/Development Stage]] - Development monitoring setup
- [[TTA.dev/Stage Guides/Testing Stage]] - CI/CD monitoring integration
- [[TTA.dev/Stage Guides/Staging Stage]] - Pre-production monitoring
- [[TTA.dev/Stage Guides/Production Stage]] - Production monitoring operations

### Learning Resources

- [[TTA.dev/Learning Paths]] - Structured learning progression
- [[Observability Learning Path]] - Monitoring and observability mastery
- [[TTA.dev/Best Practices]] - Operational best practices

---

**Last Updated:** November 7, 2025
**Stage Integration:** All stages supported
**Maintained by:** TTA.dev Platform Team
