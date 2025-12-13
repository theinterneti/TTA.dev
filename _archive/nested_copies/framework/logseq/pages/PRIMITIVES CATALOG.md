# PRIMITIVES CATALOG

**Complete reference catalog for all TTA.dev workflow primitives.**

## Overview

`PRIMITIVES_CATALOG.md` is the comprehensive reference documentation for all TTA.dev primitives, organized by category with usage examples and import paths.

## Document Location

**File:** `PRIMITIVES_CATALOG.md` (repository root)

## What's Included

### Core Workflow Primitives
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base class
- [[TTA.dev/Primitives/SequentialPrimitive]] - Sequential composition
- [[TTA.dev/Primitives/ParallelPrimitive]] - Parallel execution
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Branching logic
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing

### Recovery Primitives
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry with backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

### Performance Primitives
- [[TTA.dev/Primitives/CachePrimitive]] - LRU cache with TTL
- [[TTA.dev/Primitives/MemoryPrimitive]] - Conversational memory

### Testing Primitives
- [[TTA.dev/Primitives/MockPrimitive]] - Testing and mocking

## How to Use

### Quick Reference
Each primitive entry includes:
- **Import path**: Where to import from
- **Purpose**: What it does
- **Usage example**: Code snippet
- **Properties**: Key features
- **Metrics**: Available metrics

### Example Entry Format
```
### CachePrimitive

**Import:** `from tta_dev_primitives.performance import CachePrimitive`

**Purpose:** LRU cache with TTL for expensive operations

**Usage:**
```python
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000
)
```
```

## Related Pages

- [[TTA.dev/Primitives]] - Primitives overview
- [[Core Primitives]] - Core patterns
- [[Recovery Patterns]] - Recovery strategies
- [[GETTING STARTED]] - Getting started guide

## External References

- Repository: [PRIMITIVES_CATALOG.md](file://../../PRIMITIVES_CATALOG.md)
- Online: <https://github.com/theinterneti/TTA.dev/blob/main/PRIMITIVES_CATALOG.md>

## Tags

reference:: primitives-catalog
type:: documentation


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Primitives catalog]]
