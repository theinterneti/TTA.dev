---
description: 'Refactor code to use workflow primitives instead of manual patterns'
agent: 'agent'
---

# Refactor to Primitives

Refactor ${file} to use TTA.dev workflow primitives instead of manual async patterns.

## Common Refactorings

### Manual Retry → RetryPrimitive

```python
# ❌ Before
for attempt in range(3):
    try:
        result = await api_call()
        break
    except Exception:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)

# ✅ After
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    primitive=api_call,
    max_attempts=3,
    backoff_factor=2.0
)
result = await workflow.execute(data, context)
```

### asyncio.wait_for → TimeoutPrimitive

```python
# ❌ Before
try:
    result = await asyncio.wait_for(operation(), timeout=30)
except asyncio.TimeoutError:
    result = fallback_value

# ✅ After
from tta_dev_primitives.recovery import TimeoutPrimitive

workflow = TimeoutPrimitive(
    primitive=operation,
    timeout_seconds=30.0
)
result = await workflow.execute(data, context)
```

### Manual Cache → CachePrimitive

```python
# ❌ Before
_cache = {}
async def get_data(key):
    if key in _cache:
        return _cache[key]
    result = await expensive_fetch(key)
    _cache[key] = result
    return result

# ✅ After
from tta_dev_primitives.performance import CachePrimitive

workflow = CachePrimitive(
    primitive=expensive_fetch,
    cache_key_fn=lambda d, c: d["key"],
    ttl_seconds=3600.0
)
result = await workflow.execute({"key": key}, context)
```

### try/except Fallback → FallbackPrimitive

```python
# ❌ Before
try:
    result = await primary()
except Exception:
    result = await backup()

# ✅ After
from tta_dev_primitives.recovery import FallbackPrimitive

workflow = FallbackPrimitive(
    primary=primary_operation,
    fallbacks=[backup_operation]
)
result = await workflow.execute(data, context)
```

## Instructions

1. Identify manual async patterns in the file
2. Replace with appropriate primitives
3. Compose primitives using `>>` and `|` operators
4. Add proper WorkflowContext usage
5. Update tests to use MockPrimitive

## Validation

```bash
uv run ruff format .
uv run pytest -v
```


---
**Logseq:** [[TTA.dev/.github/Prompts/Refactor-to-primitives.prompt]]
