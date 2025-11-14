# Langfuse Integration Architecture

## Overview

The `tta-langfuse-integration` package provides specialized LLM observability for TTA.dev applications. It complements the existing OpenTelemetry-based observability with LLM-specific analytics.

## Design Principles

### 1. Complementary, Not Redundant

Langfuse works **alongside** existing observability, not as a replacement:

- **OpenTelemetry**: General distributed tracing, workflow metrics, infrastructure monitoring
- **Langfuse**: LLM-specific analytics, prompt management, cost tracking, quality evaluation

### 2. Seamless Integration

Langfuse primitives integrate naturally with existing TTA.dev primitives:

```python
from tta_dev_primitives import SequentialPrimitive
from langfuse_integration import LangfusePrimitive

# OpenTelemetry tracks entire workflow
workflow = (
    data_loader >>              # Traced by OpenTelemetry
    LangfusePrimitive(llm) >>   # Traced by BOTH OpenTelemetry AND Langfuse
    output_formatter            # Traced by OpenTelemetry
)
```

### 3. Graceful Degradation

If Langfuse is unavailable or not configured:
- Application continues normally
- Only Langfuse-specific features are disabled
- OpenTelemetry tracing still works

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     TTA.dev Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Workflow Primitives                        │    │
│  │                                                          │    │
│  │  InputProcessor >> LangfusePrimitive(LLM) >> Formatter │    │
│  │                           │                              │    │
│  │                           │                              │    │
│  │                    ┌──────▼────────┐                    │    │
│  │                    │ InstrumentedP │                    │    │
│  │                    │   (base)      │                    │    │
│  │                    └───┬───────┬───┘                    │    │
│  │                        │       │                        │    │
│  └────────────────────────┼───────┼────────────────────────┘    │
│                           │       │                             │
│         ┌─────────────────┘       └─────────────────┐           │
│         │                                           │           │
│         ▼                                           ▼           │
│  ┌──────────────┐                          ┌──────────────┐    │
│  │OpenTelemetry │                          │   Langfuse   │    │
│  │              │                          │              │    │
│  │ • Spans      │                          │ • Traces     │    │
│  │ • Metrics    │                          │ • Generations│    │
│  │ • Logs       │                          │ • Scores     │    │
│  └──────┬───────┘                          └──────┬───────┘    │
│         │                                           │           │
│         │                                           │           │
│         ▼                                           ▼           │
│  ┌──────────────┐                          ┌──────────────┐    │
│  │  Prometheus  │                          │   Langfuse   │    │
│  │   + Grafana  │                          │   Dashboard  │    │
│  │              │                          │              │    │
│  │ • Metrics    │                          │ • LLM calls  │    │
│  │ • Alerts     │                          │ • Costs      │    │
│  │ • Dashboards │                          │ • Prompts    │    │
│  └──────────────┘                          │ • Evaluations│    │
│                                             └──────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

       Shared Context: correlation_id, workflow_id, session_id
```

## Component Design

### 1. Initialization Layer

**File**: `initialization.py`

```python
# Global client management
_langfuse_client: Langfuse | None = None

def initialize_langfuse(
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str = "https://cloud.langfuse.com",
    enabled: bool = True,
) -> bool:
    """Initialize Langfuse client."""
    # Setup global client
    # Configure batching/flushing
    # Return success/failure
```

**Key Features**:
- Global client singleton
- Environment variable support
- Graceful failure handling
- Flush management on shutdown

### 2. Primitive Layer

**File**: `primitives.py`

Two primitive implementations:

#### a. LangfusePrimitive (Manual API)

```python
class LangfusePrimitive(InstrumentedPrimitive):
    """Wrap primitives with explicit Langfuse tracing."""

    async def _execute_impl(self, input_data, context):
        # Create trace
        trace = client.trace(
            name=self.operation_name,
            session_id=context.correlation_id,
            metadata={
                "workflow_id": context.workflow_id,
                ...
            }
        )

        # Create generation span
        generation = trace.generation(
            input=input_data,
            ...
        )

        # Execute wrapped primitive
        result = await self.wrapped_primitive.execute(...)

        # Update with output/usage
        generation.update(output=result, usage=...)
```

**Use Case**: Full control over tracing, custom metadata, cost tracking

#### b. LangfuseObservablePrimitive (Decorator-based)

```python
class LangfuseObservablePrimitive(InstrumentedPrimitive):
    """Simpler alternative using @observe decorator."""

    @observe(as_type="generation")
    async def _execute_impl(self, input_data, context):
        # Decorator handles trace creation
        langfuse_context.update_current_trace(
            session_id=context.correlation_id,
            ...
        )
        return await self.wrapped_primitive.execute(...)
```

**Use Case**: Quick integration, automatic capture, less boilerplate

### 3. Context Propagation

Langfuse integrates with WorkflowContext:

```python
# TTA.dev context
context = WorkflowContext(
    workflow_id="story-gen-001",
    correlation_id="req-12345"
)

# Langfuse uses same IDs for correlation
trace = client.trace(
    name="narrative_gen",
    session_id=context.correlation_id,  # Links to workflow
    metadata={
        "workflow_id": context.workflow_id,
        "correlation_id": context.correlation_id
    }
)
```

**Result**: Unified correlation across both systems

## Integration Patterns

### Pattern 1: Side-by-Side (Recommended)

Both systems active, each doing what they do best:

```python
# Initialize both
initialize_observability(service_name="tta-app")
initialize_langfuse(public_key="...", secret_key="...")

# Build workflow
workflow = (
    InputProcessor() >>           # OTel only
    LangfusePrimitive(LLM()) >>   # OTel + Langfuse
    OutputFormatter()             # OTel only
)
```

**Benefits**:
- Full observability coverage
- LLM-specific insights
- Infrastructure monitoring
- Cost optimization

### Pattern 2: Langfuse-Only (LLM-focused apps)

For apps that are purely LLM-focused:

```python
# Only Langfuse
initialize_langfuse(public_key="...", secret_key="...")

# All primitives wrapped
workflow = (
    LangfusePrimitive(InputProcessor(), name="input") >>
    LangfusePrimitive(LLM(), name="generation") >>
    LangfusePrimitive(Formatter(), name="format")
)
```

**Benefits**:
- Simpler setup
- Focused on LLM metrics
- Unified dashboard

### Pattern 3: OpenTelemetry-Only (No Langfuse)

If Langfuse not needed:

```python
# Only OTel
initialize_observability(service_name="tta-app")

# No Langfuse primitives
workflow = InputProcessor() >> LLM() >> Formatter()
```

**Benefits**:
- One less dependency
- Simpler for non-LLM workloads

## Data Flow

### Trace Creation Flow

```
1. Request arrives
   └─> WorkflowContext created (workflow_id, correlation_id)

2. Primitive execution starts
   ├─> OpenTelemetry span created
   │   └─> Tags: workflow_id, correlation_id, primitive_type
   │
   └─> Langfuse trace created (if LangfusePrimitive)
       └─> Session ID: correlation_id
       └─> Metadata: workflow_id, correlation_id

3. LLM call executed
   ├─> OpenTelemetry records: latency, success/failure
   │
   └─> Langfuse records:
       ├─> Prompt
       ├─> Completion
       ├─> Tokens (input/output/total)
       ├─> Model
       ├─> Cost (calculated)
       └─> Latency

4. Result returned
   └─> Both systems close spans/traces
       └─> Data sent to respective backends
```

### Correlation Example

**OpenTelemetry Span**:
```json
{
  "trace_id": "abc123",
  "span_id": "def456",
  "name": "llm_call",
  "attributes": {
    "workflow_id": "story-gen-001",
    "correlation_id": "req-12345",
    "primitive_type": "LangfusePrimitive"
  }
}
```

**Langfuse Trace**:
```json
{
  "id": "trace-xyz789",
  "name": "narrative_gen",
  "session_id": "req-12345",
  "metadata": {
    "workflow_id": "story-gen-001",
    "correlation_id": "req-12345"
  },
  "observations": [
    {
      "type": "generation",
      "input": "Tell me a story...",
      "output": "Once upon a time...",
      "usage": {"input": 10, "output": 50, "total": 60},
      "model": "gpt-4",
      "cost": 0.0042
    }
  ]
}
```

**Correlation**: Search either system by `correlation_id: req-12345` to find related data

## Cost Tracking

Langfuse automatically calculates costs when model pricing is configured:

```python
# In Langfuse dashboard, configure model pricing:
# gpt-4: $0.03/1K input, $0.06/1K output

# Primitive automatically tracks usage
llm = LangfusePrimitive(
    name="narrative_gen",
    metadata={"model": "gpt-4"}
)

# After execution, Langfuse shows:
# - Tokens: 10 input, 50 output
# - Cost: $0.0042 (10 * 0.03/1000 + 50 * 0.06/1000)
```

## Evaluation Support

Langfuse supports automated evaluation (future enhancement):

```python
from langfuse_integration.evaluation import evaluate_output

# Execute LLM
result = await llm.execute(context, input_data)

# Evaluate result
score = await evaluate_output(
    result=result,
    criteria=["coherence", "relevance", "safety"]
)

# Score appears in Langfuse dashboard
```

## Performance Considerations

### Batching

Langfuse batches events before sending:

```python
initialize_langfuse(
    flush_at=15,          # Batch 15 events
    flush_interval=1.0    # Or flush every 1 second
)
```

### Async Sending

Events are sent asynchronously to avoid blocking:

```python
# Non-blocking
result = await llm.execute(...)  # Returns immediately
# Langfuse sends data in background
```

### Shutdown Handling

Flush remaining events on shutdown:

```python
import atexit
from langfuse_integration import shutdown_langfuse

atexit.register(shutdown_langfuse)
```

## Security

### API Keys

Never commit keys to version control:

```python
# ✅ Good: Environment variables
initialize_langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)

# ❌ Bad: Hardcoded
initialize_langfuse(
    public_key="pk-lf-...",  # Don't do this!
    secret_key="sk-lf-..."
)
```

### Self-Hosted Option

For sensitive data, use self-hosted Langfuse:

```python
initialize_langfuse(
    host="https://langfuse.internal.company.com"
)
```

## Future Enhancements

1. **Prompt Management**: Version control for prompts
2. **Automated Evaluation**: Built-in quality scoring
3. **Datasets**: Test sets for regression testing
4. **A/B Testing**: Compare prompt versions
5. **Fine-tuning Support**: Track fine-tuning data and results

## References

- [Langfuse Documentation](https://langfuse.com/docs)
- [OpenTelemetry Integration](https://langfuse.com/docs/integrations/opentelemetry)
- [TTA.dev Observability](../../observability-integration/README.md)
