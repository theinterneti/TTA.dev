# Backend Developers

**Guide for backend developers using TTA.dev primitives in production systems.**

## Overview

This page provides guidance for backend developers integrating TTA.dev primitives into production backend systems and APIs.

## Quick Start for Backend Devs

### 1. Install TTA.dev

```bash
pip install tta-dev-primitives

# Or with uv
uv pip install tta-dev-primitives
```

### 2. Build Your First Workflow

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

# Production-ready LLM endpoint
llm_endpoint = (
    CachePrimitive(ttl=3600) >>
    RetryPrimitive(your_llm_primitive, max_retries=3) >>
    format_response
)

# Use in API handler
async def handle_request(request_data: dict) -> dict:
    context = WorkflowContext(correlation_id=request_data["request_id"])
    return await llm_endpoint.execute(request_data, context)
```

## Common Backend Use Cases

### API Endpoints

#### FastAPI Integration

```python
from fastapi import FastAPI
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

app = FastAPI()

workflow = step1 >> step2 >> step3

@app.post("/api/process")
async def process(data: dict):
    context = WorkflowContext(correlation_id=data.get("id"))
    result = await workflow.execute(data, context)
    return result
```

#### Flask Integration

```python
from flask import Flask, request, jsonify
import asyncio

app = Flask(__name__)

@app.route("/api/process", methods=["POST"])
def process():
    data = request.json
    context = WorkflowContext()
    
    # Run async workflow in sync context
    result = asyncio.run(workflow.execute(data, context))
    return jsonify(result)
```

### Background Jobs

#### Celery Integration

```python
from celery import Celery
from tta_dev_primitives import SequentialPrimitive

app = Celery('tasks')

workflow = data_pipeline >> ml_model >> store_results

@app.task
async def process_batch(batch_id: str):
    context = WorkflowContext(correlation_id=batch_id)
    return await workflow.execute({"batch_id": batch_id}, context)
```

#### Redis Queue Integration

```python
from rq import Queue
from redis import Redis

redis_conn = Redis()
q = Queue(connection=redis_conn)

async def background_workflow(job_data):
    context = WorkflowContext()
    return await workflow.execute(job_data, context)

# Enqueue jobs
job = q.enqueue(background_workflow, job_data)
```

### Database Integration

#### With SQLAlchemy

```python
from sqlalchemy.ext.asyncio import AsyncSession
from tta_dev_primitives import SequentialPrimitive

async def db_workflow(session: AsyncSession, data: dict):
    workflow = (
        validate_data >>
        query_database(session) >>
        transform_results >>
        update_database(session)
    )
    
    context = WorkflowContext()
    return await workflow.execute(data, context)
```

#### With Redis

```python
from redis.asyncio import Redis
from tta_dev_primitives.performance import CachePrimitive

redis = Redis()

cached_workflow = CachePrimitive(
    primitive=expensive_operation,
    ttl=3600,
    storage=redis  # Use Redis as cache backend
)
```

## Production Patterns

### Error Handling

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

# Robust production workflow
production_workflow = (
    validate_input >>
    RetryPrimitive(
        primary_service,
        max_retries=3,
        backoff_strategy="exponential"
    ) >>
    FallbackPrimitive(
        primary=primary_processor,
        fallbacks=[backup_processor, cached_response]
    )
)
```

### Monitoring & Observability

```python
from observability_integration import initialize_observability

# Initialize once at startup
initialize_observability(
    service_name="my-backend-api",
    enable_prometheus=True
)

# All primitives automatically instrumented
# - Prometheus metrics on :9464/metrics
# - OpenTelemetry traces to Jaeger
# - Structured logs
```

### Rate Limiting

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

rate_limited_api = (
    check_rate_limit >>
    TimeoutPrimitive(
        external_api_call,
        timeout_seconds=30
    ) >>
    process_response
)
```

## Deployment Considerations

### Environment Configuration

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    cache_ttl: int = 3600
    max_retries: int = 3
    
    class Config:
        env_file = ".env"

settings = Settings()

# Use in workflow
llm = OpenAIPrimitive(api_key=settings.openai_api_key)
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    # Test workflow is operational
    test_context = WorkflowContext()
    try:
        await health_workflow.execute({}, test_context)
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
```

### Graceful Shutdown

```python
import signal
import asyncio

async def shutdown(signal, loop):
    """Cleanup tasks on shutdown."""
    # Cancel running workflows
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

# Register signal handlers
loop = asyncio.get_event_loop()
for sig in (signal.SIGTERM, signal.SIGINT):
    loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))
```

## Performance Optimization

### Caching Strategy

```python
from tta_dev_primitives.performance import CachePrimitive

# Multi-layer caching
workflow = (
    CachePrimitive(ttl=300, max_size=1000) >>  # Fast in-memory
    expensive_llm_call >>
    CachePrimitive(ttl=3600, storage=redis)    # Persistent cache
)
```

### Connection Pooling

```python
from httpx import AsyncClient

# Reuse HTTP clients
http_client = AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100)
)

class APICallPrimitive(WorkflowPrimitive):
    def __init__(self):
        self.client = http_client  # Reuse connection pool
```

## Security

### API Key Management

```python
from cryptography.fernet import Fernet

# Encrypt API keys at rest
cipher = Fernet(key)
encrypted_key = cipher.encrypt(api_key.encode())

# Decrypt when needed
api_key = cipher.decrypt(encrypted_key).decode()
```

### Input Validation

```python
from pydantic import BaseModel, validator

class WorkflowInput(BaseModel):
    text: str
    max_length: int
    
    @validator("max_length")
    def check_max_length(cls, v):
        if v > 10000:
            raise ValueError("max_length too large")
        return v

# Validate before workflow
validated_input = WorkflowInput(**request_data)
result = await workflow.execute(validated_input.dict(), context)
```

## Related Resources

### Documentation
- [[GETTING STARTED]] - Quick start guide
- [[PRIMITIVES CATALOG]] - All primitives
- [[TTA.dev/Examples]] - Working examples
- [[TTA.dev/Guides/Production Deployment]] - Deployment guide

### Audience Pages
- [[Developers]] - General developer guide
- [[Architects]] - Architecture guidance
- [[AI Engineers]] - AI-specific patterns

## Tags

audience:: backend-developers
type:: guide
focus:: production
