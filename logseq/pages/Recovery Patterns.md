# Recovery Patterns

**Resilience and error handling patterns for production workflows.**

## Overview

Recovery Patterns provide battle-tested strategies for handling errors, transient failures, and maintaining system reliability in production environments.

## Recovery Primitives

### Retry Strategies
- [[TTA.dev/Primitives/RetryPrimitive]] - Automatic retry with exponential backoff
  - Constant backoff
  - Linear backoff
  - Exponential backoff with jitter

### Fallback Strategies
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation cascade
  - Multiple fallback options
  - Automatic failover
  - Cost/quality tradeoffs

### Circuit Breaking
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Prevent hanging operations
- [[TTA.dev/Primitives/CircuitBreakerPrimitive]] - Stop cascade failures

### Transaction Patterns
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern for distributed transactions
  - Forward recovery
  - Backward compensation
  - Partial rollback

## Common Patterns

### Resilient API Call
```python
workflow = (
    TimeoutPrimitive(seconds=30) >>
    RetryPrimitive(max_attempts=3, backoff="exponential") >>
    FallbackPrimitive(primary=api_call, fallback=cached_response)
)
```

### Multi-Model Fallback
```python
workflow = FallbackPrimitive(
    primary=gpt4,
    fallbacks=[claude, gemini, local_llm]
)
```

## Related Categories

- [[Core Primitives]] - Basic workflow patterns
- [[Performance Primitives]] - Optimization patterns

## Documentation

- [[TTA.dev/Guides/Error Handling]] - Error handling guide
- [[TTA.dev/Examples/Error Handling Patterns]] - Code examples
- [[PRIMITIVES CATALOG]] - Recovery section

## Tags

category:: recovery
type:: patterns


---
**Logseq:** [[TTA.dev/Logseq/Pages/Recovery patterns]]
