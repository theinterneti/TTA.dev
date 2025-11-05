# Integration

**Integration patterns for connecting TTA.dev with external services**

---

## Overview

TTA.dev integrates with various external services and frameworks to provide comprehensive AI application capabilities. This page documents integration patterns, best practices, and available connectors.

---

## Integration Categories

### 1. LLM Providers

**Supported:**
- OpenAI (GPT-4, GPT-4 Mini, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Google (Gemini 1.5 Pro, Gemini 1.5 Flash)
- Ollama (Local LLMs)
- Azure OpenAI

**Pattern:**

```python
from tta_dev_primitives.core import RouterPrimitive
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Configure clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Create LLM wrappers
async def openai_llm(data, context):
    response = await openai_client.chat.completions.create(
        model=data.get("model", "gpt-4-mini"),
        messages=data["messages"]
    )
    return {"response": response.choices[0].message.content}

async def anthropic_llm(data, context):
    response = await anthropic_client.messages.create(
        model=data.get("model", "claude-3-5-sonnet"),
        messages=data["messages"]
    )
    return {"response": response.content[0].text}

# Route between providers
router = RouterPrimitive(
    routes={
        "openai": openai_llm,
        "anthropic": anthropic_llm
    },
    router_fn=lambda d, c: d.get("provider", "openai")
)
```

### 2. Vector Databases

**Supported:**
- Pinecone
- Weaviate
- Qdrant
- ChromaDB
- FAISS

**Pattern:**

```python
from tta_dev_primitives.performance import CachePrimitive
import pinecone

# Initialize Pinecone
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone.Index("document-embeddings")

# Create retrieval primitive with caching
async def retrieve_documents(data, context):
    # Get embedding for query
    query_embedding = await get_embedding(data["query"])
    
    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=data.get("top_k", 5),
        include_metadata=True
    )
    
    return {
        "documents": [
            {
                "id": match["id"],
                "score": match["score"],
                "content": match["metadata"]["content"]
            }
            for match in results["matches"]
        ]
    }

# Add caching
cached_retrieval = CachePrimitive(
    primitive=retrieve_documents,
    ttl_seconds=1800,  # 30 minutes
    key_fn=lambda d, c: d["query"]
)
```

### 3. Observability Platforms

**Supported:**
- Prometheus (metrics)
- Grafana (dashboards)
- Jaeger (tracing)
- Loki (logs)

**Pattern:**

```python
from tta_observability_integration import initialize_observability
from prometheus_client import Counter, Histogram

# Initialize observability
initialize_observability(
    service_name="tta-app",
    enable_prometheus=True,
    prometheus_port=9464
)

# Define custom metrics
request_counter = Counter(
    'app_requests_total',
    'Total application requests',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

# Use in workflow
async def tracked_endpoint(data, context):
    with request_duration.labels(endpoint="process").time():
        try:
            result = await process(data, context)
            request_counter.labels(endpoint="process", status="success").inc()
            return result
        except Exception as e:
            request_counter.labels(endpoint="process", status="error").inc()
            raise
```

### 4. Message Queues

**Supported:**
- Redis (pub/sub, streams)
- RabbitMQ
- Apache Kafka

**Pattern:**

```python
import redis.asyncio as redis

# Redis pub/sub integration
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

# Publisher primitive
async def publish_event(data, context):
    await redis_client.publish(
        channel=data["channel"],
        message=json.dumps({
            "event": data["event"],
            "payload": data["payload"],
            "correlation_id": context.correlation_id
        })
    )
    return {"published": True}

# Subscriber primitive
async def subscribe_events(data, context):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(data["channel"])
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            event_data = json.loads(message["data"])
            await handle_event(event_data, context)
```

---

## Integration Patterns

### Pattern 1: External API Integration with Retry

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive
import httpx

# Create resilient API client
async def call_external_api(data, context):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=data["api_url"],
            json=data["payload"],
            headers={
                "Authorization": f"Bearer {data['api_key']}",
                "X-Correlation-ID": context.correlation_id
            }
        )
        response.raise_for_status()
        return response.json()

# Add retry and timeout
resilient_api = TimeoutPrimitive(
    primitive=RetryPrimitive(
        primitive=call_external_api,
        max_retries=3,
        backoff_strategy="exponential"
    ),
    timeout_seconds=30.0
)
```

### Pattern 2: Database Integration with Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine
engine = create_async_engine(
    os.getenv("DATABASE_URL"),
    pool_size=10,
    max_overflow=20
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Database primitive
async def query_database(data, context):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(data["query"]),
            data.get("params", {})
        )
        return {
            "rows": [dict(row) for row in result.mappings()]
        }
```

### Pattern 3: Multi-Service Orchestration

```python
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive

# Orchestrate multiple services
workflow = (
    fetch_user_profile >>              # Service 1: User DB
    ParallelPrimitive([
        fetch_recommendations,          # Service 2: ML service
        fetch_recent_activity,         # Service 3: Analytics DB
        fetch_user_preferences         # Service 4: Config service
    ]) >>
    aggregate_user_context >>          # Combine results
    personalize_content >>             # Service 5: Content service
    format_response                    # Final formatting
)
```

---

## Framework Integrations

### LangChain Integration

```python
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from tta_dev_primitives import WorkflowPrimitive

class LangChainPrimitive(WorkflowPrimitive):
    """Wrap LangChain agent as TTA primitive."""
    
    def __init__(self, agent: AgentExecutor):
        super().__init__()
        self.agent = agent
    
    async def _execute_impl(self, data: dict, context: WorkflowContext) -> dict:
        result = await self.agent.ainvoke({
            "input": data["input"],
            "chat_history": context.get_state("chat_history", [])
        })
        
        return {
            "output": result["output"],
            "intermediate_steps": result.get("intermediate_steps", [])
        }

# Usage
llm = ChatOpenAI(model="gpt-4")
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

langchain_primitive = LangChainPrimitive(agent_executor)
```

### FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from tta_dev_primitives import WorkflowContext

app = FastAPI()

@app.post("/workflow")
async def execute_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Execute TTA workflow via HTTP endpoint."""
    
    # Create context
    context = WorkflowContext(
        workflow_id=f"req-{uuid.uuid4()}",
        correlation_id=request.headers.get("X-Correlation-ID")
    )
    
    # Execute workflow
    result = await workflow.execute(request.data, context)
    
    # Schedule background cleanup
    background_tasks.add_task(cleanup_context, context)
    
    return {
        "workflow_id": context.workflow_id,
        "result": result
    }
```

### Streamlit Integration

```python
import streamlit as st
from tta_dev_primitives import WorkflowContext

st.title("TTA.dev Workflow Demo")

# User input
user_input = st.text_area("Enter your query:")

if st.button("Execute"):
    # Create context
    context = WorkflowContext(
        workflow_id=f"session-{st.session_state.get('session_id')}",
        user_id=st.session_state.get("user_id")
    )
    
    # Execute with progress
    with st.spinner("Processing..."):
        result = await workflow.execute(
            {"query": user_input},
            context
        )
    
    # Display result
    st.success("Complete!")
    st.json(result)
    
    # Show metrics
    st.metric("Duration", f"{result['duration_ms']}ms")
    st.metric("Cost", f"${result['cost']:.4f}")
```

---

## Authentication & Security

### API Key Management

```python
from functools import wraps
import os

def with_api_key(key_name: str):
    """Decorator to inject API key from environment."""
    def decorator(func):
        @wraps(func)
        async def wrapper(data, context):
            api_key = os.getenv(key_name)
            if not api_key:
                raise ValueError(f"Missing API key: {key_name}")
            
            data["api_key"] = api_key
            return await func(data, context)
        return wrapper
    return decorator

# Usage
@with_api_key("OPENAI_API_KEY")
async def call_openai(data, context):
    client = AsyncOpenAI(api_key=data["api_key"])
    # ... rest of implementation
```

### OAuth Integration

```python
from authlib.integrations.httpx_client import AsyncOAuth2Client

async def oauth_authenticated_api(data, context):
    """Call API with OAuth token."""
    
    # Get or refresh token
    token = await get_oauth_token(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET")
    )
    
    # Make authenticated request
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=data["url"],
            headers={"Authorization": f"Bearer {token['access_token']}"}
        )
        return response.json()
```

---

## Error Handling in Integrations

### Graceful Degradation

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Primary: Cloud service
async def cloud_service_call(data, context):
    return await call_cloud_api(data)

# Fallback: Local cache
async def local_cache_fallback(data, context):
    return await get_from_cache(data["cache_key"])

# Workflow with fallback
workflow = FallbackPrimitive(
    primary=cloud_service_call,
    fallbacks=[local_cache_fallback]
)
```

### Circuit Breaker Pattern

```python
from tta_dev_primitives.recovery import CircuitBreakerPrimitive

# Protect external service with circuit breaker
protected_service = CircuitBreakerPrimitive(
    primitive=external_service_call,
    failure_threshold=5,      # Open after 5 failures
    timeout_seconds=60,       # Try again after 60s
    half_open_calls=3        # Test with 3 calls before fully closing
)
```

---

## Monitoring Integrations

### Health Checks

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """Check health of all integrations."""
    
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "vector_db": await check_vector_db_connection(),
        "llm_api": await check_llm_api_availability()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks
    }
```

### Integration Metrics

```promql
# Query integration health

# API response time
histogram_quantile(0.95, 
  rate(integration_api_duration_seconds_bucket[5m])
)

# Error rate by integration
rate(integration_errors_total[5m]) 
  by (integration_name)

# Integration availability
integration_health{integration_name="openai"} == 1
```

---

## Related Documentation

- [[TTA.dev/Examples/RAG Workflow]] - Vector DB integration example
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Multi-service orchestration
- [[tta-observability-integration]] - Observability integration

---

## Related Primitives

- [[RouterPrimitive]] - Route between integrations
- [[FallbackPrimitive]] - Graceful degradation
- [[RetryPrimitive]] - Retry failed integrations
- [[CachePrimitive]] - Cache integration results

---

## External Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [LangChain Documentation](https://python.langchain.com/)

---

**Category:** Integration patterns
**Status:** Production-ready
