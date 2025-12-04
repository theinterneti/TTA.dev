type:: primitive
category:: Performance
status:: documented
generated:: 2025-12-04

# MemoryPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/performance/memory.py`

## Overview

Hybrid memory primitive with automatic fallback.

Works immediately with in-memory storage, enhanced with Redis when available.

Basic usage (no setup required):
    >>> memory = MemoryPrimitive()  # Uses InMemoryStore
    >>> await memory.add("user:123:session:abc", {"context": "data"})
    >>> result = await memory.get("user:123:session:abc")

With Redis (optional enhancement):
    >>> memory = MemoryPrimitive(redis_url="redis://localhost:6379")
    >>> # Automatically falls back to InMemoryStore if Redis unavailable

The API is identical regardless of backend. Your code works the same way.

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Performance]] - Performance primitives
