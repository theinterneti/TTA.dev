# Langfuse Integration Guide

## Installation

### 1. Add Package

```bash
# Add to your project
uv add tta-langfuse-integration

# Or add to workspace
# In pyproject.toml:
[tool.uv.workspace]
members = [
    "packages/tta-langfuse-integration",
    # ... other packages
]
```

### 2. Get Langfuse Credentials

**Option A: Langfuse Cloud** (easiest)

1. Sign up at [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a project
3. Copy public key and secret key

**Option B: Self-Hosted**

1. Deploy Langfuse (Docker): [https://langfuse.com/docs/deployment](https://langfuse.com/docs/deployment)
2. Create project in web UI
3. Copy keys and host URL

### 3. Configure Environment

```bash
# .env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

## Quick Start

### Basic Usage

```python
from langfuse_integration import initialize_langfuse, LangfusePrimitive
from tta_dev_primitives import WorkflowContext

# Initialize Langfuse
initialize_langfuse()  # Reads from environment variables

# Wrap your LLM primitive
llm = LangfusePrimitive(
    name="story_generator",
    metadata={"model": "gpt-4", "temperature": 0.7}
)

# Execute
context = WorkflowContext(workflow_id="story-001", correlation_id="req-123")
result = await llm.execute(
    {"prompt": "Tell me a story about a robot"},
    context
)

# View in Langfuse dashboard at https://cloud.langfuse.com
```

### With Existing Primitives

```python
from tta_dev_primitives import SequentialPrimitive
from langfuse_integration import LangfusePrimitive

# Your existing LLM logic
async def call_gpt4(input_data, context):
    # ... LLM call logic
    return {"response": "...", "usage": {...}}

# Wrap with Langfuse tracking
tracked_llm = LangfusePrimitive(
    primitive=SequentialPrimitive(call_gpt4),
    name="gpt4_call"
)

# Use in workflow
workflow = input_processor >> tracked_llm >> output_formatter
```

## Integration Patterns

### Pattern 1: Full Observability Stack

Use both OpenTelemetry and Langfuse:

```python
from observability_integration import initialize_observability
from langfuse_integration import initialize_langfuse

# OpenTelemetry for infrastructure/workflow metrics
initialize_observability(
    service_name="tta-app",
    enable_prometheus=True,
    prometheus_port=9464
)

# Langfuse for LLM-specific analytics
initialize_langfuse()

# Build workflow
from observability_integration.primitives import CachePrimitive
from langfuse_integration import LangfusePrimitive

workflow = (
    input_validator >>
    CachePrimitive(                    # Cached, tracked by OTel
        LangfusePrimitive(llm_call),   # LLM tracked by both OTel + Langfuse
        ttl_seconds=3600
    ) >>
    output_formatter
)
```

**What gets tracked:**
- **OpenTelemetry**: Cache hits/misses, workflow latency, error rates
- **Langfuse**: LLM prompts, completions, tokens, costs

### Pattern 2: Multi-Model Routing

Track different models separately:

```python
from langfuse_integration import LangfusePrimitive

# Fast model for simple queries
fast_llm = LangfusePrimitive(
    name="fast_model",
    metadata={"provider": "openrouter", "model": "llama-3.1-8b"}
)

# Premium model for complex queries
premium_llm = LangfusePrimitive(
    name="premium_model",
    metadata={"provider": "openai", "model": "gpt-4"}
)

# Router logic
async def route_by_complexity(input_data, context):
    if is_complex(input_data):
        return await premium_llm.execute(input_data, context)
    return await fast_llm.execute(input_data, context)

# Langfuse dashboard shows:
# - Cost comparison: fast vs premium
# - Usage distribution
# - Performance by model
```

### Pattern 3: Session Tracking

Group related calls into sessions:

```python
# User starts conversation
session_id = generate_session_id()  # e.g., "user-123-session-456"

# All calls in conversation use same session_id
llm = LangfusePrimitive(
    name="chat",
    session_id=session_id,
    user_id="user-123"
)

# Execute multiple turns
for user_message in conversation:
    result = await llm.execute(
        {"prompt": user_message},
        context
    )

# Langfuse groups all calls by session_id
# View entire conversation in one trace
```

### Pattern 4: Prompt Versioning

Track which prompt version was used:

```python
# Version 1: Original prompt
llm_v1 = LangfusePrimitive(
    name="narrative_gen",
    metadata={"prompt_version": "v1.0"}
)

# Version 2: Improved prompt
llm_v2 = LangfusePrimitive(
    name="narrative_gen",
    metadata={"prompt_version": "v2.0"}
)

# A/B test or gradual rollout
if random.random() < 0.5:
    result = await llm_v1.execute(input_data, context)
else:
    result = await llm_v2.execute(input_data, context)

# Langfuse shows performance by prompt version
```

## Advanced Usage

### Custom Metadata

Add any metadata for filtering/analysis:

```python
llm = LangfusePrimitive(
    name="content_gen",
    metadata={
        "model": "gpt-4",
        "temperature": 0.7,
        "genre": "fantasy",
        "difficulty": "medium",
        "user_tier": "premium"
    }
)

# Query in Langfuse:
# - Show all "fantasy" generations
# - Compare performance by "difficulty"
# - Cost analysis by "user_tier"
```

### Tags

Categorize traces:

```python
llm = LangfusePrimitive(
    name="narrative_gen",
    tags=["production", "critical", "user-facing"]
)

# Filter by tag in Langfuse dashboard
```

### Manual Trace Creation

For more control:

```python
from langfuse_integration.initialization import get_langfuse_client

client = get_langfuse_client()

# Create custom trace
trace = client.trace(
    name="complex_workflow",
    session_id=context.correlation_id,
    metadata={"workflow_type": "multi-step"}
)

# Add multiple generations
gen1 = trace.generation(
    name="step_1",
    input=step1_input,
    model="gpt-4"
)
result1 = await execute_step1()
gen1.update(output=result1)

gen2 = trace.generation(
    name="step_2",
    input=result1,
    model="claude-3-opus"
)
result2 = await execute_step2()
gen2.update(output=result2)

# Langfuse shows multi-step workflow
```

### Using @observe Decorator

Alternative to LangfusePrimitive:

```python
from langfuse.decorators import observe

@observe()
async def my_llm_call(prompt: str, context: WorkflowContext):
    """Call LLM with automatic Langfuse tracing."""
    # Decorator handles trace creation
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Use as normal function
result = await my_llm_call("Tell me a story", context)
```

## Cost Tracking

### Automatic Cost Calculation

Configure model pricing in Langfuse dashboard, then costs are calculated automatically:

```python
# No code changes needed
llm = LangfusePrimitive(
    name="narrative_gen",
    metadata={"model": "gpt-4"}  # Model name must match Langfuse config
)

result = await llm.execute(input_data, context)

# Langfuse automatically calculates cost based on:
# - Token usage (from result['usage'])
# - Model pricing (from dashboard config)
```

### Custom Cost Tracking

For custom pricing:

```python
from langfuse_integration.initialization import get_langfuse_client

client = get_langfuse_client()
trace = client.trace(name="custom_llm")

generation = trace.generation(
    name="llm_call",
    model="custom-model",
    usage={
        "input": 100,
        "output": 200,
        "total": 300
    },
    metadata={
        "cost_usd": 0.05  # Manual cost
    }
)
```

## Monitoring and Dashboards

### Key Metrics

Langfuse dashboard shows:

1. **Request Volume**: Calls per day/hour
2. **Token Usage**: Input/output tokens over time
3. **Cost**: Total and per-model costs
4. **Latency**: P50/P95/P99 response times
5. **Model Distribution**: Which models are used most
6. **Error Rate**: Failed calls percentage
7. **User Activity**: Calls per user/session

### Alerting

Set up alerts in Langfuse:

- Cost exceeds budget
- Error rate spikes
- Latency degradation
- Unusual token usage

## Debugging

### Finding Traces

```python
# Use correlation_id to find related traces
context = WorkflowContext(
    workflow_id="story-gen-001",
    correlation_id="req-12345"
)

# In Langfuse UI:
# - Filter by session_id: "req-12345"
# - Or search metadata.workflow_id: "story-gen-001"
```

### Error Tracking

Errors are automatically captured:

```python
llm = LangfusePrimitive(name="llm_call")

try:
    result = await llm.execute(input_data, context)
except Exception as e:
    # Error recorded in Langfuse with:
    # - Error message
    # - Stack trace (if enabled)
    # - Input that caused error
    # - Timing information
    pass
```

## Best Practices

### 1. Use Environment Variables

```python
# ✅ Good
initialize_langfuse()  # Reads from env vars

# ❌ Bad
initialize_langfuse(
    public_key="pk-lf-...",  # Hardcoded
    secret_key="sk-lf-..."
)
```

### 2. Consistent Naming

```python
# ✅ Good: Descriptive, consistent names
narrative_gen = LangfusePrimitive(name="narrative_generation")
dialogue_gen = LangfusePrimitive(name="dialogue_generation")

# ❌ Bad: Vague, inconsistent
llm1 = LangfusePrimitive(name="llm")
llm2 = LangfusePrimitive(name="model_call")
```

### 3. Add Context

```python
# ✅ Good: Rich metadata
llm = LangfusePrimitive(
    name="content_gen",
    metadata={
        "model": "gpt-4",
        "temperature": 0.7,
        "use_case": "story_generation",
        "version": "v2.1"
    }
)

# ❌ Bad: No metadata
llm = LangfusePrimitive(name="llm")
```

### 4. Flush on Shutdown

```python
import atexit
from langfuse_integration import shutdown_langfuse

# Ensure events are sent before exit
atexit.register(shutdown_langfuse)
```

### 5. Use Sessions for Conversations

```python
# ✅ Good: Group related calls
llm = LangfusePrimitive(
    name="chat",
    session_id=conversation_id
)

# ❌ Bad: No session tracking
llm = LangfusePrimitive(name="chat")
```

## Troubleshooting

### Traces Not Appearing

**Check 1: Is Langfuse initialized?**
```python
from langfuse_integration import is_langfuse_enabled

if not is_langfuse_enabled():
    print("Langfuse not enabled!")
```

**Check 2: Are credentials correct?**
```bash
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
```

**Check 3: Is client flushing?**
```python
from langfuse_integration import shutdown_langfuse

# Manually flush
shutdown_langfuse()
```

### High Latency

Langfuse sends events asynchronously, but batching can cause delays:

```python
# Increase flush frequency
initialize_langfuse(
    flush_at=5,          # Smaller batches
    flush_interval=0.5   # More frequent flushes
)
```

### Missing Token Usage

Ensure your LLM response includes usage data:

```python
result = {
    "response": "...",
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 50,
        "total_tokens": 60
    },
    "model": "gpt-4"  # Model name for cost calculation
}
```

## Migration Guide

### From Manual Langfuse Usage

**Before:**
```python
from langfuse import Langfuse

client = Langfuse(public_key="...", secret_key="...")
trace = client.trace(name="llm")
# ... manual trace management
```

**After:**
```python
from langfuse_integration import initialize_langfuse, LangfusePrimitive

initialize_langfuse()
llm = LangfusePrimitive(name="llm")
# Automatic trace management
```

### From OpenTelemetry Only

**Before:**
```python
from observability_integration import initialize_observability

initialize_observability(service_name="tta")
workflow = input >> llm >> output
```

**After:**
```python
from observability_integration import initialize_observability
from langfuse_integration import initialize_langfuse, LangfusePrimitive

initialize_observability(service_name="tta")
initialize_langfuse()  # Add Langfuse

workflow = input >> LangfusePrimitive(llm) >> output
```

## References

- [Langfuse Documentation](https://langfuse.com/docs)
- [TTA.dev Observability](../../tta-observability-integration/README.md)
- [Architecture Details](ARCHITECTURE.md)
- [Examples](EXAMPLES.md)
