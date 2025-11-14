# Langfuse v2 → v3.10.0 Migration Guide

## Overview

This guide documents the API changes when migrating from Langfuse v2.x to v3.10.0, based on the Context7 documentation of the latest stable SDK.

---

## Breaking Changes

### 1. Import Path Changes

**v2.x (Old):**
```python
from langfuse.decorators import langfuse_context, observe
```

**v3.10.0 (New):**
```python
from langfuse import get_client, observe
```

**Why?** The `langfuse.decorators` module was removed. All decorators and client functions are now top-level imports.

---

### 2. Trace Creation API

**v2.x (Old - Manual Lifecycle):**
```python
trace = client.trace(
    name="my_operation",
    session_id="session-123",
    user_id="user-456",
    metadata={"key": "value"}
)

generation = trace.generation(
    name="llm_call",
    input={"prompt": "Hello"},
    metadata={"model": "gpt-4"}
)

# ... do work ...

generation.update(output="Response")
generation.end()
trace.update()
```

**v3.10.0 (New - Context Managers):**
```python
with client.start_as_current_span(
    name="my_operation",
    input={"prompt": "Hello"},
    metadata={"key": "value"},
    level="INFO"
) as span:
    span.update_trace(
        session_id="session-123",
        user_id="user-456",
        tags=["production"]
    )
    
    with span.start_as_current_generation(
        name="llm_call",
        input={"prompt": "Hello"},
        metadata={"model": "gpt-4"}
    ) as generation:
        # ... do work ...
        generation.update(output="Response")
        # Automatic cleanup on exit
```

**Benefits:**
- Automatic span lifecycle management
- No need for manual `end()` calls
- Exception handling built-in
- Cleaner, more readable code

---

### 3. Context Updates

**v2.x (Old):**
```python
from langfuse.decorators import langfuse_context

langfuse_context.update_current_trace(
    session_id="session-123",
    metadata={"key": "value"}
)
```

**v3.10.0 (New):**
```python
from langfuse import get_client

langfuse = get_client()
langfuse.update_current_trace(
    session_id="session-123",
    metadata={"key": "value"}
)
```

**Key Change:** Use `get_client()` to access the current Langfuse instance, then call update methods.

---

### 4. Generation Metadata

**v2.x (Old):**
```python
generation.update(
    usage={
        "input": 150,
        "output": 85,
        "total": 235
    },
    cost=0.0047
)
```

**v3.10.0 (New):**
```python
generation.update(
    usage_details={
        "input": 150,
        "output": 85,
        "total": 235
    },
    cost_details={
        "total_cost": 0.0047
    }
)
```

**Changes:**
- `usage` → `usage_details`
- `cost` → `cost_details` (nested object)

---

### 5. Updating Current Observation

**v2.x (Old):**
```python
# Not well-defined in v2
```

**v3.10.0 (New):**
```python
langfuse = get_client()

# For generations
langfuse.update_current_generation(
    model="gpt-4",
    model_parameters={"temperature": 0.7},
    usage_details={"input": 120, "output": 85, "total": 205},
    cost_details={"total_cost": 0.0042},
    output={"analysis": "positive"}
)

# For spans
langfuse.update_current_span(
    metadata={"query_length": 150},
    version="v2.0",
    level="INFO"
)
```

**New Feature:** Explicit methods for updating the current generation or span from any nested function.

---

## Migration Strategy

### Step 1: Update Imports

```python
# Before
from langfuse.decorators import langfuse_context, observe

# After
from langfuse import get_client, observe
```

### Step 2: Replace Manual Lifecycle with Context Managers

```python
# Before
trace = client.trace(name="workflow")
generation = trace.generation(name="llm_call", input=data)
try:
    result = call_llm(data)
    generation.update(output=result)
finally:
    generation.end()
    trace.update()

# After
with client.start_as_current_span(name="workflow", input=data) as span:
    with span.start_as_current_generation(name="llm_call", input=data) as generation:
        result = call_llm(data)
        generation.update(output=result)
```

### Step 3: Update Context Access

```python
# Before
langfuse_context.update_current_trace(session_id="123")

# After
langfuse = get_client()
langfuse.update_current_trace(session_id="123")
```

### Step 4: Update Metadata Fields

```python
# Before
generation.update(
    usage={"input": 100, "output": 50},
    cost=0.003
)

# After
generation.update(
    usage_details={"input": 100, "output": 50, "total": 150},
    cost_details={"total_cost": 0.003}
)
```

---

## New Features in v3.10.0

### 1. Observation Types

v3 introduces explicit observation types:

```python
@observe(as_type="generation")  # For LLM calls
@observe(as_type="span")        # General operations
@observe(as_type="agent")       # Agent operations
@observe(as_type="tool")        # Tool calls
@observe(as_type="chain")       # Chain executions
@observe(as_type="retriever")   # Retrieval operations
@observe(as_type="embedding")   # Embedding operations
@observe(as_type="evaluator")   # Evaluation operations
@observe(as_type="guardrail")   # Guardrail operations
```

### 2. Enhanced Error Handling

```python
@observe()
def function_with_error():
    try:
        risky_operation()
    except Exception as e:
        langfuse = get_client()
        langfuse.update_current_span(
            level="ERROR",
            status_message=str(e),
            metadata={"error_type": type(e).__name__}
        )
        raise
```

### 3. Scores and Evaluation

```python
with client.start_as_current_span(name="user-query") as span:
    result = process_query(data)
    
    span.score(
        name="response_quality",
        value=0.87,
        data_type="NUMERIC",
        comment="High quality response"
    )
    
    span.score_trace(
        name="user_satisfaction",
        value=True,
        data_type="BOOLEAN"
    )
```

### 4. Trace Parameters

```python
result = main_workflow(
    "What is AI?",
    langfuse_trace_id="custom-trace-id",      # Optional custom trace ID
    langfuse_parent_observation_id="parent-id" # Optional parent observation
)
```

---

## Common Patterns

### Pattern 1: Nested Observations

**Before (v2.x):**
```python
trace = client.trace(name="workflow")
span1 = trace.span(name="step1")
span1.end()
span2 = trace.span(name="step2")
span2.end()
trace.update()
```

**After (v3.10.0):**
```python
with client.start_as_current_span(name="workflow") as span:
    with span.start_as_current_span(name="step1") as step1:
        # Do work
        pass
    
    with span.start_as_current_span(name="step2") as step2:
        # Do work
        pass
```

### Pattern 2: Decorator with Context Updates

**Before (v2.x):**
```python
from langfuse.decorators import observe, langfuse_context

@observe()
def process_query(query: str):
    langfuse_context.update_current_trace(
        session_id="session-123",
        metadata={"query_length": len(query)}
    )
    return query.upper()
```

**After (v3.10.0):**
```python
from langfuse import observe, get_client

@observe()
def process_query(query: str):
    langfuse = get_client()
    langfuse.update_current_trace(
        session_id="session-123",
        metadata={"query_length": len(query)}
    )
    langfuse.update_current_span(
        metadata={"processed": True}
    )
    return query.upper()
```

### Pattern 3: OpenAI Integration

**Before (v2.x):**
```python
from langfuse.openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**After (v3.10.0):**
```python
from langfuse.openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    name="greeting",                    # NEW: Named generation
    metadata={"source": "chat"},        # NEW: Custom metadata
    langfuse_prompt=prompt,             # NEW: Link to prompt version
    trace_id="custom-trace-id"          # NEW: Custom trace ID
)
```

---

## Testing Migration

### 1. Enable Debug Mode

```python
from langfuse import Langfuse

langfuse = Langfuse(debug=True)  # Enable verbose logging
```

### 2. Verify Traces

Check the Langfuse dashboard to ensure:
- Traces are created correctly
- Spans are nested properly
- Metadata is captured
- Token usage is tracked
- Errors are logged

### 3. Check for Deprecation Warnings

Run your code and watch for warnings:
```bash
python -W all your_script.py
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'langfuse.decorators'`

**Solution:** Update imports to use top-level `langfuse` module:
```python
# Wrong
from langfuse.decorators import observe

# Correct
from langfuse import observe
```

### Issue: `AttributeError: 'Langfuse' object has no attribute 'trace'`

**Solution:** Use `start_as_current_span()` instead:
```python
# Wrong
trace = client.trace(name="my_trace")

# Correct
with client.start_as_current_span(name="my_trace") as span:
    pass
```

### Issue: `TypeError: update() got an unexpected keyword argument 'usage'`

**Solution:** Update to `usage_details` and `cost_details`:
```python
# Wrong
generation.update(usage={"input": 100}, cost=0.003)

# Correct
generation.update(
    usage_details={"input": 100, "output": 50, "total": 150},
    cost_details={"total_cost": 0.003}
)
```

---

## Backward Compatibility

There is **no backward compatibility** between v2 and v3 for the decorator module. You must update all code using `langfuse.decorators`.

However, the core client initialization remains similar:
```python
from langfuse import Langfuse

# This works in both versions
langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    base_url="https://cloud.langfuse.com"
)
```

---

## Resources

- **Langfuse Python SDK**: https://github.com/langfuse/langfuse-python
- **v3 Documentation**: https://langfuse.com/docs/sdk/python
- **Migration Support**: https://langfuse.com/docs/sdk/python/migration
- **Context7 Documentation**: Retrieved via `mcp_context7_get-library-docs`

---

## Summary

| Feature | v2.x | v3.10.0 |
|---------|------|---------|
| Import | `from langfuse.decorators` | `from langfuse` |
| Trace Creation | `client.trace()` | `client.start_as_current_span()` |
| Lifecycle | Manual `end()` | Context managers |
| Context Updates | `langfuse_context.*` | `get_client().*` |
| Usage Field | `usage={}` | `usage_details={}` |
| Cost Field | `cost=0.003` | `cost_details={"total_cost": 0.003}` |
| Observation Types | Limited | 9 types (`generation`, `agent`, `tool`, etc.) |

**Migration Effort**: Medium (2-4 hours for typical codebase)  
**Benefits**: Improved API, automatic cleanup, better type safety, more features
