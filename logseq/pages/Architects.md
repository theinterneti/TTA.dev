# Architects

**Guide for system architects designing with TTA.dev primitives.**

## Overview

This page provides guidance for architects designing systems using TTA.dev's composable primitive patterns.

## Architecture Principles

### Composability First

TTA.dev primitives follow **composition over inheritance**:

```python
# ✅ Compose primitives
workflow = (
    CachePrimitive(ttl=3600) >>
    RouterPrimitive(tier="balanced") >>
    RetryPrimitive(max_retries=3)
)

# ❌ Don't create complex inheritance hierarchies
class ComplexWorkflow(BasePrimitive, CacheMixin, RouterMixin, RetryMixin):
    pass
```

### Type Safety

- All primitives are fully typed with generics
- Type checkers catch composition errors
- Runtime validation available

### Observability by Default

- OpenTelemetry traces automatic
- Prometheus metrics built-in
- Structured logging included

## Common Architecture Patterns

### 1. Multi-Tier LLM Architecture

**Pattern:** Route requests to appropriate model tier based on complexity.

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.performance import CachePrimitive

architecture = (
    CachePrimitive(ttl=3600) >>  # Layer 1: Cache
    RouterPrimitive(              # Layer 2: Smart routing
        routes={
            "fast": gpt4_mini,
            "balanced": claude_sonnet,
            "quality": gpt4
        },
        router_fn=classify_complexity
    ) >>
    validate_output               # Layer 3: Validation
)
```

**Benefits:**
- 30-40% cost reduction (cache)
- 20-30% additional savings (routing)
- Consistent quality

### 2. Fan-Out/Fan-In Pattern

**Pattern:** Parallel processing with aggregation.

```python
from tta_dev_primitives import ParallelPrimitive, SequentialPrimitive

fan_out_in = (
    split_input >>
    (process_branch_a | process_branch_b | process_branch_c) >>
    aggregate_results >>
    format_output
)
```

**Use Cases:**
- Multi-source data fetching
- A/B testing variants
- Ensemble models

### 3. Saga Pattern for Transactions

**Pattern:** Distributed transactions with compensation.

```python
from tta_dev_primitives.recovery import CompensationPrimitive

saga = CompensationPrimitive([
    (create_user, delete_user),
    (send_email, mark_email_failed),
    (activate_account, deactivate_account)
])
```

**Use Cases:**
- Multi-service workflows
- Long-running processes
- Financial transactions

### 4. Circuit Breaker + Fallback

**Pattern:** Resilience with graceful degradation.

```python
from tta_dev_primitives.recovery import FallbackPrimitive, TimeoutPrimitive

resilient_service = (
    TimeoutPrimitive(external_api, timeout=10) >>
    FallbackPrimitive(
        primary=expensive_accurate_model,
        fallbacks=[fast_approximate_model, cached_response]
    )
)
```

**Benefits:**
- High availability
- Predictable latency
- Cost optimization

## System Design Considerations

### Scalability

#### Horizontal Scaling

```python
# Primitives are stateless - scale by adding instances
# All state in WorkflowContext
workflow = step1 >> step2 >> step3

# Deploy to multiple workers
for worker in workers:
    worker.execute(workflow, context)
```

#### Vertical Scaling

```python
# Use parallelism for CPU-bound work
parallel_workflow = (
    (cpu_task_1 | cpu_task_2 | cpu_task_3 | cpu_task_4) >>
    aggregate
)
```

### Reliability

#### Multi-Layer Recovery

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# Layer 1: Timeout
# Layer 2: Retry
# Layer 3: Fallback
reliable = (
    TimeoutPrimitive(timeout=30) >>
    RetryPrimitive(max_retries=3, backoff="exponential") >>
    FallbackPrimitive(primary=service_a, fallbacks=[service_b, cache])
)
```

### Performance

#### Caching Strategy

```python
from tta_dev_primitives.performance import CachePrimitive

# Multi-tier caching
workflow = (
    CachePrimitive(ttl=60, max_size=100) >>    # L1: Fast, small
    expensive_computation >>
    CachePrimitive(ttl=3600, max_size=10000)   # L2: Larger, persistent
)
```

#### Async All the Way

```python
# ✅ Full async stack
async def handler(request):
    context = WorkflowContext()
    return await workflow.execute(request, context)

# ❌ Blocking operations
def handler(request):
    return workflow.execute_sync(request)  # Don't do this
```

## Integration Patterns

### Microservices Architecture

```python
# Service A
workflow_a = step1 >> step2 >> publish_to_queue

# Service B (consumes from queue)
workflow_b = consume_from_queue >> step3 >> step4

# WorkflowContext carries correlation_id across services
```

### Event-Driven Architecture

```python
# Event handler
async def handle_event(event: dict):
    context = WorkflowContext(
        correlation_id=event["id"],
        metadata=event["metadata"]
    )
    await event_workflow.execute(event, context)
```

### API Gateway Pattern

```python
# Gateway routes to appropriate workflow
gateway = RouterPrimitive(
    routes={
        "users": user_workflow,
        "orders": order_workflow,
        "analytics": analytics_workflow
    },
    router_fn=lambda data, ctx: data["service"]
)
```

## Deployment Architectures

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tta-workflow-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: workflow
        image: myapp:latest
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://jaeger:4317"
        - name: PROMETHEUS_PORT
          value: "9464"
```

### Serverless Deployment

```python
# AWS Lambda handler
def lambda_handler(event, context):
    workflow_context = WorkflowContext(
        correlation_id=event["requestId"]
    )
    result = asyncio.run(
        workflow.execute(event["body"], workflow_context)
    )
    return {"statusCode": 200, "body": result}
```

## Observability Architecture

### Metrics Collection

- **Prometheus:** Metrics on `:9464/metrics`
- **Grafana:** Dashboards for visualization
- **Alerts:** Based on error rates, latency

### Distributed Tracing

- **OpenTelemetry:** Automatic span creation
- **Jaeger:** Trace visualization
- **Context propagation:** Across service boundaries

### Logging

- **Structured logs:** JSON format
- **Correlation IDs:** Track requests
- **Log aggregation:** ELK, Loki, etc.

## Security Considerations

### API Key Management

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
# Keys never in code
```

### Input Validation

```python
from pydantic import BaseModel

class WorkflowInput(BaseModel):
    text: str
    max_tokens: int = 1000

# Validate before processing
validated = WorkflowInput(**request_data)
```

### Rate Limiting

```python
# Rate limit per user
workflow = (
    check_user_rate_limit >>
    process_request >>
    increment_user_counter
)
```

## Cost Optimization

### LLM Cost Reduction

1. **Caching:** 40-60% reduction
2. **Model routing:** 20-30% additional
3. **Prompt optimization:** 10-20% more

**Combined:** 60-80% cost reduction possible

### Infrastructure Cost

1. **Autoscaling:** Scale down during low traffic
2. **Spot instances:** Use for batch workloads
3. **Resource limits:** Set memory/CPU limits

## Anti-Patterns to Avoid

### ❌ Creating God Objects

```python
# DON'T
class WorkflowManager:
    def __init__(self):
        self.cache = Cache()
        self.router = Router()
        self.retry = Retry()

    def execute_everything(self, data):
        # 500 lines of code
```

```python
# DO
workflow = cache >> router >> retry
```

### ❌ Manual Async Orchestration

```python
# DON'T
async def workflow(data):
    result1 = await step1(data)
    result2 = await step2(result1)
    return await step3(result2)
```

```python
# DO
workflow = step1 >> step2 >> step3
```

### ❌ Tight Coupling

```python
# DON'T
class MyWorkflow(SequentialPrimitive):
    def __init__(self):
        super().__init__([HardcodedService()])
```

```python
# DO
def create_workflow(service):
    return step1 >> service >> step3
```

## Migration Strategies

### From Legacy Systems

1. **Wrap existing services** as primitives
2. **Gradual migration** service by service
3. **Run parallel** old + new systems
4. **Cut over** when validated

### From Other Frameworks

#### From LangChain

```python
# LangChain
chain = prompt | llm | output_parser

# TTA.dev equivalent
workflow = format_prompt >> llm_primitive >> parse_output
```

#### From Plain Async

```python
# Plain async
async def process():
    r1 = await api1()
    r2 = await api2(r1)
    return r2

# TTA.dev
workflow = api1 >> api2
```

## Related Resources

### Documentation
- [[TTA.dev/Architecture/Component Integration]] - Integration patterns
- [[TTA.dev (Meta-Project)]] - Project overview
- [[PRIMITIVES CATALOG]] - All primitives

### Audience Pages
- [[Developers]] - Developer guide
- [[Backend Developers]] - Backend patterns
- [[AI Engineers]] - AI-specific patterns

## Tags

audience:: architects
type:: guide
focus:: architecture


---
**Logseq:** [[TTA.dev/Logseq/Pages/Architects]]
