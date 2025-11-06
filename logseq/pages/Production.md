# Production

**Production deployment guide for TTA.dev applications**

---

## Overview

This guide covers deploying TTA.dev workflows to production environments with proper observability, error handling, and performance optimization.

---

## Production Checklist

### 1. Code Quality ✅

- [ ] All tests passing (100% critical path coverage)
- [ ] Type hints on all public APIs
- [ ] Linting passes (Ruff)
- [ ] Type checking passes (Pyright)
- [ ] Security scan clean (Bandit, Safety)

### 2. Error Handling ✅

- [ ] [[RetryPrimitive]] on external API calls
- [ ] [[FallbackPrimitive]] for degraded operation
- [ ] [[TimeoutPrimitive]] to prevent hanging
- [ ] [[CompensationPrimitive]] for distributed transactions
- [ ] Structured error logging with correlation IDs

### 3. Observability ✅

- [ ] [[tta-observability-integration]] configured
- [ ] OpenTelemetry tracing enabled
- [ ] Prometheus metrics exposed
- [ ] Structured logging (JSON format)
- [ ] Correlation IDs in all [[WorkflowContext]]

### 4. Performance ✅

- [ ] [[CachePrimitive]] on expensive operations
- [ ] [[RouterPrimitive]] for model selection
- [ ] Connection pooling for databases
- [ ] Async I/O throughout
- [ ] Load testing completed

### 5. Security ✅

- [ ] API keys in environment variables (not code)
- [ ] Secrets in secure storage (AWS Secrets Manager, etc.)
- [ ] Rate limiting on external APIs
- [ ] Input validation on all user data
- [ ] HTTPS/TLS for all external communication

---

## Deployment Patterns

### Pattern 1: FastAPI + Docker

**Project Structure:**

```
app/
├── main.py                 # FastAPI application
├── workflows/              # TTA.dev workflows
│   ├── rag_workflow.py
│   └── agent_workflow.py
├── config.py               # Configuration
├── Dockerfile
└── docker-compose.yml
```

**main.py:**

```python
from fastapi import FastAPI, BackgroundTasks
from tta_dev_primitives import WorkflowContext
from tta_observability_integration import initialize_observability
from workflows.rag_workflow import rag_workflow
import structlog

# Initialize observability
initialize_observability(
    service_name="tta-app",
    enable_prometheus=True,
    enable_tracing=True
)

app = FastAPI(title="TTA.dev Production App")
logger = structlog.get_logger(__name__)

@app.post("/query")
async def query_endpoint(
    request: QueryRequest,
    background_tasks: BackgroundTasks
):
    """Execute RAG workflow with production safeguards."""

    # Create context with correlation ID
    context = WorkflowContext(
        workflow_id=f"query-{uuid.uuid4()}",
        correlation_id=request.correlation_id or f"req-{uuid.uuid4()}",
        user_id=request.user_id
    )

    logger.info(
        "query_received",
        correlation_id=context.correlation_id,
        query=request.query
    )

    try:
        # Execute workflow
        result = await rag_workflow.execute(
            {"query": request.query},
            context
        )

        # Schedule cleanup in background
        background_tasks.add_task(cleanup_context, context)

        return {
            "correlation_id": context.correlation_id,
            "result": result,
            "duration_ms": result.get("duration_ms", 0),
            "cost": result.get("cost", 0.0)
        }

    except Exception as e:
        logger.error(
            "query_failed",
            correlation_id=context.correlation_id,
            error=str(e),
            exc_info=True
        )
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "checks": {
            "vector_db": await check_vector_db(),
            "llm_api": await check_llm_api(),
            "cache": await check_cache()
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy application
COPY . .

# Expose ports
EXPOSE 8000 9464

# Run with gunicorn + uvicorn workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "9464:9464"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
    depends_on:
      - redis
      - jaeger
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4318:4318"    # OTLP gRPC
    restart: unless-stopped
```

### Pattern 2: AWS Lambda

**Serverless deployment with Lambda:**

```python
# lambda_handler.py
import json
from tta_dev_primitives import WorkflowContext
from workflows.rag_workflow import rag_workflow

def lambda_handler(event, context):
    """AWS Lambda handler."""

    # Parse request
    body = json.loads(event.get("body", "{}"))

    # Create workflow context
    workflow_context = WorkflowContext(
        workflow_id=context.request_id,
        correlation_id=event["headers"].get("X-Correlation-ID"),
        user_id=body.get("user_id")
    )

    # Execute workflow (async)
    import asyncio
    result = asyncio.run(
        rag_workflow.execute(
            {"query": body["query"]},
            workflow_context
        )
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "X-Correlation-ID": workflow_context.correlation_id
        },
        "body": json.dumps(result)
    }
```

**serverless.yml:**

```yaml
service: tta-app

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    OPENAI_API_KEY: ${env:OPENAI_API_KEY}
  timeout: 30
  memorySize: 1024

functions:
  query:
    handler: lambda_handler.lambda_handler
    events:
      - http:
          path: query
          method: post
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
```

---

## Monitoring & Alerting

### Prometheus Alerts

```yaml
# alerts.yml
groups:
  - name: tta_workflows
    rules:
      - alert: HighErrorRate
        expr: |
          rate(workflow_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in workflows"

      - alert: SlowWorkflows
        expr: |
          histogram_quantile(0.95,
            rate(workflow_duration_seconds_bucket[5m])
          ) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Workflows taking too long"

      - alert: HighLLMCost
        expr: |
          rate(llm_cost_dollars_total[1h]) > 10
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "LLM costs exceeding budget"
```

### Grafana Dashboards

Import pre-built dashboards from [[tta-observability-integration]]:

```bash
# Export dashboard
curl http://localhost:3000/api/dashboards/uid/tta-workflows > dashboard.json

# Import to production
curl -X POST \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @dashboard.json \
  https://grafana.production.com/api/dashboards/db
```

---

## Performance Optimization

### 1. Caching Strategy

```python
from tta_dev_primitives.performance import CachePrimitive

# Multi-level caching
workflow = (
    # L1: Memory cache (fast, small)
    CachePrimitive(
        primitive=retrieval_step,
        ttl_seconds=300,      # 5 minutes
        max_size=100
    ) >>

    # L2: Redis cache (distributed, larger)
    CachePrimitive(
        primitive=llm_generation,
        ttl_seconds=3600,     # 1 hour
        max_size=10000,
        backend="redis"
    ) >>

    formatting_step
)
```

### 2. Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine

# Create connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Concurrent connections
    max_overflow=10,        # Overflow connections
    pool_pre_ping=True,     # Verify connections
    pool_recycle=3600       # Recycle after 1 hour
)
```

### 3. Load Balancing

```python
from tta_dev_primitives.core import RouterPrimitive

# Distribute load across multiple LLM endpoints
router = RouterPrimitive(
    routes={
        "endpoint_1": llm_endpoint_1,
        "endpoint_2": llm_endpoint_2,
        "endpoint_3": llm_endpoint_3
    },
    router_fn=lambda d, c: f"endpoint_{hash(c.correlation_id) % 3 + 1}"
)
```

---

## Scaling Strategies

### Horizontal Scaling

**Auto-scaling with Kubernetes:**

```yaml
# deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tta-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tta-app
  template:
    metadata:
      labels:
        app: tta-app
    spec:
      containers:
      - name: app
        image: tta-app:latest
        ports:
        - containerPort: 8000
        - containerPort: 9464
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tta-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tta-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Cost Management

### Budget Tracking

```python
from tta_dev_primitives.observability import CostTracker

# Track LLM costs
cost_tracker = CostTracker(
    budget_daily=100.0,
    budget_monthly=2000.0,
    alert_threshold=0.8
)

# Wrap expensive operations
@cost_tracker.track
async def llm_call(data, context):
    result = await openai.chat.completions.create(
        model="gpt-4",
        messages=data["messages"]
    )

    # Record cost
    cost_tracker.record_cost(
        operation="llm_call",
        model="gpt-4",
        tokens=result.usage.total_tokens,
        cost=calculate_cost(result.usage)
    )

    return result
```

---

## Related Documentation

- [[TTA.dev/Deployment]] - Detailed deployment guides
- [[TTA.dev/Observability]] - Monitoring setup
- [[tta-observability-integration]] - Observability package
- [[GitHub Actions]] - CI/CD setup

---

## Related Primitives

- [[CachePrimitive]] - Performance optimization
- [[RetryPrimitive]] - Reliability
- [[FallbackPrimitive]] - Graceful degradation
- [[RouterPrimitive]] - Load distribution

---

**Status:** Production-ready
**Category:** Operations
