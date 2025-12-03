# FallbackPrimitive

type:: [[Primitive]]
category:: [[Recovery]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Low]]
python-class:: `FallbackPrimitive`
import-path:: `from tta_dev_primitives.recovery import FallbackPrimitive`
related-primitives:: [[TTA.dev/Primitives/RetryPrimitive]], [[TTA.dev/Primitives/RouterPrimitive]]

---

## Overview

- id:: fallback-primitive-overview
  Implement graceful degradation by trying a primary primitive and falling back to alternatives if it fails. Essential for building resilient systems.

  **Think of it as:** A safety net - if the primary operation fails, try alternatives in order until one succeeds.

---

## Use Cases

- id:: fallback-primitive-use-cases
  - **LLM fallback:** Try GPT-4, fall back to Claude, then to local model
  - **Service redundancy:** Primary API fails → backup API → cached response
  - **Cost optimization:** Expensive service unavailable → use cheaper alternative
  - **Data sources:** Primary database down → read replica → cache
  - **Geographic failover:** Primary region down → secondary region → degraded mode

---

## Key Benefits

- id:: fallback-primitive-benefits
  - ✅ **Graceful degradation** - System stays operational despite failures
  - ✅ **Automatic failover** - No manual intervention needed
  - ✅ **Ordered alternatives** - Try fallbacks in priority order
  - ✅ **Built-in observability** - Track which fallback was used
  - ✅ **Composable** - Fallbacks can be complex workflows
  - ✅ **Type-safe** - All alternatives must have same input/output types

---

## API Reference

- id:: fallback-primitive-api

### Constructor

```python
FallbackPrimitive(
    primary: WorkflowPrimitive[T, U],
    fallbacks: list[WorkflowPrimitive[T, U]],
    suppress_primary_error: bool = True
)
```

**Parameters:**

- `primary`: The primary primitive to try first
- `fallbacks`: List of fallback primitives to try in order
- `suppress_primary_error`: If False, raise primary error if all fallbacks also fail

**Returns:** A new `FallbackPrimitive` instance

---

## Examples

### LLM Fallback Chain

- id:: fallback-llm-chain

```python
{{embed ((standard-imports))}}
from tta_dev_primitives.recovery import FallbackPrimitive

# Define LLM primitives in order of preference
gpt4 = LambdaPrimitive(lambda data, ctx: call_gpt4(data))
claude = LambdaPrimitive(lambda data, ctx: call_claude(data))
llama_local = LambdaPrimitive(lambda data, ctx: call_llama(data))

# Create fallback chain
resilient_llm = FallbackPrimitive(
    primary=gpt4,
    fallbacks=[claude, llama_local]
)

context = WorkflowContext(correlation_id="llm-001")
result = await resilient_llm.execute(
    input_data={"prompt": "Explain quantum computing"},
    context=context
)

# Tries GPT-4 first, falls back to Claude, then Llama if both fail
```

### API with Cached Fallback

- id:: fallback-api-cache

```python
# Primary: Live API call
# Fallback 1: Backup API
# Fallback 2: Cached response

primary_api = LambdaPrimitive(lambda data, ctx: call_primary_api(data))
backup_api = LambdaPrimitive(lambda data, ctx: call_backup_api(data))
cached_response = LambdaPrimitive(lambda data, ctx: get_cached_response(data))

workflow = FallbackPrimitive(
    primary=primary_api,
    fallbacks=[backup_api, cached_response]
)

# Always returns something, even if all APIs are down (uses cache)
```

---

## Composition Patterns

- id:: fallback-composition-patterns

### Fallback + Retry

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry primary, then fallback
primary_with_retry = RetryPrimitive(expensive_service, max_retries=3)

workflow = FallbackPrimitive(
    primary=primary_with_retry,
    fallbacks=[cheap_service, cached_data]
)
```

### Sequential with Fallback

```python
# Add fallback to specific steps
workflow = (
    input_validator >>
    FallbackPrimitive(
        primary=expensive_processor,
        fallbacks=[cheap_processor]
    ) >>
    output_formatter
)
```

---

## Best Practices

- id:: fallback-best-practices

✅ **Order by preference** - Primary = best, fallbacks = progressively degraded
✅ **Match types** - All alternatives must have same input/output types
✅ **Monitor fallback usage** - High fallback rate indicates primary issues
✅ **Set timeouts** - Prevent hanging on slow primary
✅ **Log fallback reasons** - Track why primary failed
✅ **Test all paths** - Ensure all fallbacks actually work

❌ **Don't hide problems** - Monitor when fallbacks are used
❌ **Don't infinite fallback** - Limit number of fallbacks (3-5 max)
❌ **Don't use as retry** - Use [[TTA.dev/Primitives/RetryPrimitive]] for that

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/RetryPrimitive]] - Retry primary before fallback
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Timeout primary attempt
- [[TTA.dev/Primitives/RouterPrimitive]] - Route to different fallback chains
- [[TTA.dev/Primitives/CachePrimitive]] - Cache as final fallback

### Used In Examples

{{query (and [[Example]] [[FallbackPrimitive]])}}

---

## Observability

### Tracing

```
workflow_execution
└── fallback_execution
    ├── primary_attempt (failed)
    ├── fallback_1_attempt (failed)
    └── fallback_2_attempt (success)
```

### Metrics

- `fallback.primary_success_rate` - How often primary succeeds
- `fallback.fallback_usage_count` - Which fallbacks are used
- `fallback.total_attempts` - Total attempts before success

---

## Metadata

**Source Code:** [fallback.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/recovery/fallback.py)
**Tests:** [test_fallback.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/test_fallback.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready
