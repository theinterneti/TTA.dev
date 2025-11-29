# Production Deployment

type:: [[Guide]]
category:: [[Production]]
difficulty:: [[Advanced]]
estimated-time:: 45 minutes
target-audience:: [[DevOps]], [[Platform Engineers]], [[Architects]]

---

## Overview

- id:: production-deployment-overview
  **Deploy TTA.dev workflows to production** with confidence. This guide covers environment setup, configuration management, monitoring, scaling, CI/CD integration, and best practices for running AI workflows in production environments.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Observability]] - Monitoring setup
- [[TTA.dev/Guides/Error Handling Patterns]] - Resilience patterns

**Should understand:**
- Docker basics
- Environment variables
- CI/CD concepts
- Cloud deployment (AWS/GCP/Azure)

---

## Deployment Checklist

### Pre-Deployment

- [ ] All workflows tested locally
- [ ] Unit tests pass (100% coverage)
- [ ] Integration tests pass
- [ ] Load testing completed
- [ ] Error handling validated
- [ ] Observability configured
- [ ] Secrets management configured
- [ ] Environment variables documented
- [ ] Rollback plan prepared

### Deployment

- [ ] Docker image built and pushed
- [ ] Environment-specific configs applied
- [ ] Health checks configured
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Load balancers configured (if needed)
- [ ] Auto-scaling policies set

### Post-Deployment

- [ ] Health checks passing
- [ ] Metrics flowing to Prometheus
- [ ] Logs flowing to aggregator
- [ ] Traces visible in Jaeger/Datadog
- [ ] Smoke tests passing
- [ ] Performance within SLOs
- [ ] On-call team notified

---

## Environment Configuration

### Development

```python
# config/development.py
from dataclasses import dataclass

@dataclass
class DevelopmentConfig:
    """Development environment configuration."""

    # Service
    service_name: str = "my-ai-app"
    environment: str = "development"
    debug: bool = True

    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    prometheus_port: int = 9464
    jaeger_endpoint: str = "http://localhost:14268/api/traces"

    # LLM
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 3
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 1000

    # Logging
    log_level: str = "DEBUG"
    structured_logging: bool = True
```

### Staging

```python
# config/staging.py
from dataclasses import dataclass

@dataclass
class StagingConfig:
    """Staging environment configuration."""

    # Service
    service_name: str = "my-ai-app"
    environment: str = "staging"
    debug: bool = False

    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    prometheus_port: int = 9464
    jaeger_endpoint: str = "https://jaeger-staging.company.com/api/traces"

    # LLM
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 5
    cache_ttl_seconds: int = 7200  # 2 hours
    cache_max_size: int = 10000

    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True
```

### Production

```python
# config/production.py
from dataclasses import dataclass
import os

@dataclass
class ProductionConfig:
    """Production environment configuration."""

    # Service
    service_name: str = "my-ai-app"
    environment: str = "production"
    debug: bool = False

    # Observability (from env vars for security)
    enable_tracing: bool = True
    enable_metrics: bool = True
    prometheus_port: int = 9464
    jaeger_endpoint: str = os.getenv("JAEGER_ENDPOINT")

    # LLM (from env vars)
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY")
    llm_timeout_seconds: float = 120.0
    llm_max_retries: int = 5
    cache_ttl_seconds: int = 14400  # 4 hours
    cache_max_size: int = 50000

    # Logging
    log_level: str = "WARNING"
    structured_logging: bool = True
    log_json: bool = True  # For log aggregation

def get_config():
    """Get configuration for current environment."""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ProductionConfig()
    elif env == "staging":
        return StagingConfig()
    else:
        return DevelopmentConfig()
```

---

## Secrets Management

### Using Environment Variables

**Never commit secrets to git:**

```bash
# .env (gitignored)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://user:pass@host:6379
JAEGER_ENDPOINT=https://jaeger.company.com/api/traces
```

**Load in application:**

```python
# app.py
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Access secrets
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY not set!")
```

### Using AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name: str, region: str = "us-east-1") -> dict:
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except Exception as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {e}")

# Usage
secrets = get_secret("my-ai-app/production")
openai_key = secrets["OPENAI_API_KEY"]
```

### Using Kubernetes Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-app-secrets
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
```

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: ai-app
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-app-secrets
              key: openai-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-app-secrets
              key: anthropic-api-key
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Expose ports
EXPOSE 8000 9464

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uv", "run", "python", "-m", "src.main"]
```

### Docker Compose (Local Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "9464:9464"
    environment:
      - ENVIRONMENT=development
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./src:/app/src  # Hot reload
    depends_on:
      - redis
      - prometheus

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
```

### Build and Run

```bash
# Build image
docker build -t my-ai-app:latest .

# Run locally
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop
docker-compose down
```

---

## Kubernetes Deployment

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-app
  labels:
    app: ai-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-app
  template:
    metadata:
      labels:
        app: ai-app
    spec:
      containers:
      - name: ai-app
        image: my-registry/ai-app:v1.0.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9464
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-app-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-app
  labels:
    app: ai-app
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  - port: 9464
    targetPort: 9464
    protocol: TCP
    name: metrics
  selector:
    app: ai-app
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment
kubectl get pods
kubectl get svc

# View logs
kubectl logs -f deployment/ai-app

# Scale manually
kubectl scale deployment ai-app --replicas=5

# Rollback if needed
kubectl rollout undo deployment/ai-app
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --all-extras

      - name: Run tests
        run: uv run pytest -v --cov=src

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            myregistry/ai-app:latest
            myregistry/ai-app:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/ai-app \
            ai-app=myregistry/ai-app:${{ github.sha }}
          kubectl rollout status deployment/ai-app

      - name: Verify deployment
        run: |
          kubectl get pods
          kubectl get svc
```

---

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-app'
    static_configs:
      - targets: ['ai-app:9464']
    metrics_path: '/metrics'

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: ai-app
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        action: keep
        regex: 9464
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "AI Workflow Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(workflow_executions_total[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(workflow_execution_failure_total[5m])) / sum(rate(workflow_executions_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(workflow_execution_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100"
          }
        ]
      }
    ]
  }
}
```

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: ai_app_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(workflow_execution_failure_total[5m])) /
          sum(rate(workflow_executions_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in AI workflows"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(workflow_execution_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency"
          description: "P95 latency is {{ $value }}s (threshold: 2s)"

      - alert: LowCacheHitRate
        expr: |
          sum(rate(cache_hits_total[5m])) /
          (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100 < 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}% (threshold: 30%)"
```

---

## Health Checks

### Application Health Endpoints

```python
# src/health.py
from fastapi import FastAPI, Response
from tta_dev_primitives import WorkflowContext # Keep import for now, will address later if needed
import time

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check - is service running?"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/ready")
async def readiness_check():
    """Readiness check - can service handle requests?"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "llm_api": await check_llm_api(),
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return Response(
        content={"status": "ready" if all_healthy else "not ready", "checks": checks},
        status_code=status_code
    )

async def check_database() -> bool:
    """Check database connectivity."""
    try:
        # Test DB connection
        return True
    except Exception:
        return False

async def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        # Test Redis connection
        return True
    except Exception:
        return False

async def check_llm_api() -> bool:
    """Check LLM API connectivity."""
    try:
        # Test LLM API with simple call
        return True
    except Exception:
        return False
```

---

## Scaling Strategies

### Horizontal Scaling

**When to use:** Increased traffic, need more throughput

```yaml
# Scale up
kubectl scale deployment ai-app --replicas=10

# Auto-scaling based on CPU
kubectl autoscale deployment ai-app --min=3 --max=20 --cpu-percent=70
```

### Vertical Scaling

**When to use:** Complex workflows, need more memory/CPU per pod

```yaml
# k8s/deployment.yaml
resources:
  requests:
    memory: "2Gi"      # Increased from 512Mi
    cpu: "1000m"       # Increased from 250m
  limits:
    memory: "4Gi"      # Increased from 2Gi
    cpu: "2000m"       # Increased from 1000m
```

### Caching Strategy

**When to use:** High repetition, reduce LLM costs

```python
# Use distributed cache (Redis)
from tta_dev_primitives.performance import CachePrimitive
import redis

redis_client = redis.Redis(host='redis', port=6379)

# Cache with Redis backend
cached_workflow = CachePrimitive(
    primitive=expensive_llm,
    ttl_seconds=7200,
    max_size=100000,
    backend=redis_client  # Shared across all pods
)
```

---

## Rollback Strategy

### Blue-Green Deployment

```bash
# Deploy new version (green)
kubectl apply -f k8s/deployment-green.yaml

# Test green deployment
curl https://green.ai-app.company.com/health

# Switch traffic to green
kubectl patch service ai-app -p '{"spec":{"selector":{"version":"green"}}}'

# If issues, rollback to blue
kubectl patch service ai-app -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Canary Deployment

```yaml
# 90% traffic to stable, 10% to canary
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: ai-app
spec:
  hosts:
  - ai-app
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: ai-app
        subset: canary
  - route:
    - destination:
        host: ai-app
        subset: stable
      weight: 90
    - destination:
        host: ai-app
        subset: canary
      weight: 10
```

---

## Best Practices

### Configuration

✅ **Use environment variables** for all secrets
✅ **Different configs per environment** (dev/staging/prod)
✅ **Validate configuration on startup** (fail fast)
✅ **Document all environment variables**
✅ **Use secret managers** (AWS Secrets Manager, Vault)

### Observability

✅ **Enable all observability** (logs, traces, metrics)
✅ **Set up dashboards** before deployment
✅ **Configure alerts** for critical metrics
✅ **Monitor costs** in production
✅ **Use structured logging** (JSON format)

### Reliability

✅ **Health checks required** (liveness + readiness)
✅ **Retry with exponential backoff**
✅ **Fallback strategies** for graceful degradation
✅ **Circuit breakers** for external services
✅ **Timeouts on all operations**

### Scaling

✅ **Start small** (3 replicas)
✅ **Use auto-scaling** (HPA)
✅ **Monitor resource usage** (CPU, memory)
✅ **Load test** before production
✅ **Plan for 10x growth**

---

## Troubleshooting

### High Memory Usage

**Symptoms:** Pods OOM killed, frequent restarts

**Solutions:**
1. Increase memory limits
2. Reduce cache size
3. Check for memory leaks
4. Profile application

### High CPU Usage

**Symptoms:** Slow response times, high P95 latency

**Solutions:**
1. Increase replicas (horizontal scaling)
2. Optimize expensive operations
3. Add caching
4. Profile hot paths

### Deployment Failures

**Symptoms:** Pods not starting, health checks failing

**Solutions:**
1. Check logs: `kubectl logs deployment/ai-app`
2. Verify secrets: `kubectl get secrets`
3. Check resource limits
4. Verify image exists

---

## Next Steps

- **Monitor workflows:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Handle errors:** [[TTA.dev/Guides/Error Handling Patterns]]

---

## Key Takeaways

1. **Environment-specific configs** - Different settings for dev/staging/prod
2. **Secrets management** - Never commit secrets, use env vars or secret managers
3. **Health checks** - Required for Kubernetes deployments
4. **Observability first** - Set up monitoring before deploying
5. **Start small, scale up** - Begin with 3 replicas, use auto-scaling
6. **Rollback plan** - Always have a way to revert changes

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 45 minutes
**Difficulty:** [[Advanced]]

- [[Project Hub]]
