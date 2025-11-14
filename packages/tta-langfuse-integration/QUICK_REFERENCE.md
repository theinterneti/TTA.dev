# Langfuse Quick Reference

## Installation

```bash
# Add to workspace
cd packages/tta-langfuse-integration
uv sync

# Get credentials from https://cloud.langfuse.com
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
```

## Basic Usage

```python
from langfuse_integration import initialize_langfuse, LangfusePrimitive

# 1. Initialize
initialize_langfuse()  # Reads from environment

# 2. Wrap LLM
llm = LangfusePrimitive(
    name="narrative_gen",
    metadata={"model": "gpt-4"}
)

# 3. Execute
result = await llm.execute(
    {"prompt": "Tell a story..."},
    context
)

# 4. View in dashboard at https://cloud.langfuse.com
```

## Common Patterns

### With OpenTelemetry
```python
from observability_integration import initialize_observability
from langfuse_integration import initialize_langfuse

# Both systems active
initialize_observability(service_name="tta")
initialize_langfuse()

workflow = input >> LangfusePrimitive(llm) >> output
```

### Multi-Model Tracking
```python
fast = LangfusePrimitive(
    name="fast",
    metadata={"model": "llama-3.1-8b", "provider": "openrouter"}
)

premium = LangfusePrimitive(
    name="premium",
    metadata={"model": "gpt-4", "provider": "openai"}
)
```

### Session Tracking
```python
llm = LangfusePrimitive(
    name="chat",
    session_id=conversation_id,
    user_id=user_id,
    tags=["production", "customer-facing"]
)
```

## What Gets Tracked

- ✅ Prompts and completions
- ✅ Token usage (input/output/total)
- ✅ Cost (calculated from usage + pricing)
- ✅ Latency
- ✅ Model and provider
- ✅ Errors and failures
- ✅ Custom metadata and tags
- ✅ Session grouping
- ✅ Correlation with WorkflowContext

## Environment Variables

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...       # Required
LANGFUSE_SECRET_KEY=sk-lf-...       # Required
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional
```

## API Reference

### `initialize_langfuse()`
```python
initialize_langfuse(
    public_key: str | None = None,      # Or from env
    secret_key: str | None = None,      # Or from env
    host: str = "https://cloud.langfuse.com",
    enabled: bool = True,
    flush_at: int = 15,                 # Batch size
    flush_interval: float = 1.0         # Flush frequency
) -> bool
```

### `LangfusePrimitive`
```python
LangfusePrimitive(
    primitive: WorkflowPrimitive | None = None,  # Optional wrapped primitive
    name: str = "llm_call",             # Operation name
    metadata: dict | None = None,       # Custom metadata
    session_id: str | None = None,      # Session grouping
    user_id: str | None = None,         # User tracking
    tags: list[str] | None = None       # Categorization
)
```

## Troubleshooting

### Traces not appearing?
```python
from langfuse_integration import is_langfuse_enabled, shutdown_langfuse

# Check if enabled
if not is_langfuse_enabled():
    print("Langfuse not initialized!")

# Manually flush
shutdown_langfuse()
```

### Missing token usage?
Ensure your LLM result includes:
```python
result = {
    "response": "...",
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 50,
        "total_tokens": 60
    },
    "model": "gpt-4"
}
```

## Dashboard Access

- Cloud: https://cloud.langfuse.com
- View by session: Filter by `session_id`
- View by workflow: Search `metadata.workflow_id`
- View by user: Filter by `user_id`

## Cost Tracking

1. Configure model pricing in Langfuse dashboard
2. Costs calculated automatically from token usage
3. View cost breakdown by:
   - Model
   - Provider
   - User
   - Time period

## Best Practices

✅ Use environment variables for credentials
✅ Add descriptive metadata
✅ Use sessions for multi-turn conversations
✅ Include model name for cost tracking
✅ Flush on shutdown with `atexit.register(shutdown_langfuse)`

❌ Don't hardcode credentials
❌ Don't use vague operation names
❌ Don't forget to include usage data
