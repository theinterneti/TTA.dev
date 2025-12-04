# MemoryPrimitive

type:: [[Primitive]]
category:: [[Performance]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 90
complexity:: [[Medium]]
python-class:: `MemoryPrimitive`
import-path:: `from tta_dev_primitives.performance import MemoryPrimitive`
related-primitives:: [[TTA.dev/Primitives/CachePrimitive]], [[TTA.dev/Primitives/WorkflowPrimitive]]

---

## Overview

- id:: memory-primitive-overview
  Hybrid conversational memory with zero-setup fallback. Works immediately with in-memory storage and automatically upgrades to Redis when available. Perfect for multi-turn conversations and agent memory.

  **Think of it as:** A smart working memory for AI agents that "just works" locally but scales with Redis for production.

---

## Use Cases

- id:: memory-primitive-use-cases
  - **Multi-turn conversations:** Remember context across turns
  - **Agent memory:** Store and recall past interactions
  - **Session context:** Track user session state
  - **Personalization:** Remember user preferences
  - **Task context:** Maintain state across workflow steps

---

## Key Benefits

- id:: memory-primitive-benefits
  - ✅ **Zero setup** - Works immediately without Docker/Redis
  - ✅ **Hybrid architecture** - Automatic upgrade to Redis if available
  - ✅ **Graceful degradation** - Falls back to in-memory if Redis fails
  - ✅ **Same API** - No code changes when upgrading backends
  - ✅ **LRU eviction** - Built-in memory management
  - ✅ **Keyword search** - Search across stored memories

---

## API Reference

- id:: memory-primitive-api

### Constructor

```python
MemoryPrimitive(
    redis_url: str | None = None,
    max_size: int = 1000,
    enable_redis: bool = True
)
```

**Parameters:**

- `redis_url`: Optional Redis connection URL (enhances but not required)
- `max_size`: Maximum items for in-memory fallback store
- `enable_redis`: Whether to attempt Redis connection

### Methods

```python
async def add(self, key: str, value: dict[str, Any]) -> None:
    """Add or update memory entry."""

async def get(self, key: str) -> dict[str, Any] | None:
    """Retrieve memory by key."""

async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search memories by keyword."""

async def clear(self) -> None:
    """Clear all memories."""
```

### Helper Functions

```python
from tta_dev_primitives.performance import create_memory_key

key = create_memory_key(
    user_id="user_123",
    session_id="session_abc",
    context={"task": "coding"}  # Optional
)
# Returns: "user_123:session_abc" or "user_123:session_abc:a1b2c3d4"
```

---

## Examples

### Zero-Setup Mode (Default)

- id:: memory-zero-setup-example

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Works immediately - no Docker, no Redis, no setup!
memory = MemoryPrimitive(max_size=100)

# Add conversation turns
await memory.add("user_turn_1", {
    "role": "user",
    "content": "What is a primitive?",
    "timestamp": "2025-12-03T10:00:00Z"
})

await memory.add("assistant_turn_1", {
    "role": "assistant",
    "content": "A primitive is a composable building block...",
    "timestamp": "2025-12-03T10:00:01Z"
})

# Retrieve by key
result = await memory.get("user_turn_1")

# Search by keyword
results = await memory.search("primitive")
```

### Conversational Agent Pattern

- id:: memory-conversation-example

```python
from tta_dev_primitives.performance import MemoryPrimitive, create_memory_key
import time

memory = MemoryPrimitive(max_size=1000)

async def handle_conversation(
    user_id: str,
    session_id: str,
    user_input: str
) -> str:
    """Handle a conversation turn with memory."""
    timestamp = str(int(time.time()))

    # Store user message
    user_key = create_memory_key(user_id, session_id, {"turn": "user", "ts": timestamp})
    await memory.add(user_key, {
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    # Search for relevant context
    history = await memory.search(user_input.split()[0], limit=5)

    # Generate response with context
    response = await llm_generate(user_input, context=history)

    # Store assistant response
    assistant_key = create_memory_key(user_id, session_id, {"turn": "assistant", "ts": timestamp})
    await memory.add(assistant_key, {
        "role": "assistant",
        "content": response,
        "timestamp": timestamp
    })

    return response

# Multi-turn conversation
r1 = await handle_conversation("u1", "s1", "What is a primitive?")
r2 = await handle_conversation("u1", "s1", "Give me an example")  # Has context!
```

### With Redis Enhancement (Production)

- id:: memory-redis-example

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Optional: Enable Redis for persistence and scaling
# Falls back to in-memory if Redis unavailable
memory = MemoryPrimitive(
    redis_url="redis://localhost:6379",
    enable_redis=True,
    max_size=10000  # Fallback capacity
)

# Same API - no code changes needed!
await memory.add("key", {"data": "value"})
result = await memory.get("key")

# Check which backend is active
if memory.using_redis:
    print("Using Redis backend")
else:
    print("Using in-memory fallback")
```

---

## Architecture

- id:: memory-architecture

```
┌─────────────────────────────────────────────────┐
│               MemoryPrimitive                    │
│                                                  │
│   ┌───────────────┐    ┌───────────────┐        │
│   │ Redis Backend │    │  InMemoryStore │        │
│   │  (Optional)   │    │   (Fallback)   │        │
│   │               │    │                │        │
│   │ - Persistence │    │ - Zero setup   │        │
│   │ - Semantic    │    │ - LRU cache    │        │
│   │   search      │    │ - Keyword      │        │
│   │ - Scaling     │    │   search       │        │
│   └───────────────┘    └───────────────┘        │
│                                                  │
│        ↓ Tries Redis first ↓                    │
│        ↓ Falls back to InMemory ↓               │
└─────────────────────────────────────────────────┘
```

### When to Use Each Backend

| Scenario | Backend | Setup |
|----------|---------|-------|
| Learning/Examples | InMemory | None |
| Local Development | InMemory | None |
| Single Process | InMemory | None |
| Multi-Process | Redis | `docker run redis` |
| Production | Redis | Redis cluster |
| CI/CD Tests | InMemory | None |

---

## InMemoryStore Class

- id:: memory-inmemory-class

```python
from tta_dev_primitives.performance import InMemoryStore

# Direct usage (if you don't need async API)
store = InMemoryStore(max_size=500)

store.add("key1", {"data": "value1"})
store.add("key2", {"data": "value2"})

result = store.get("key1")  # Returns {"data": "value1"}

# Search
results = store.search("value", limit=10)

# Management
print(store.size())   # 2
print(store.keys())   # ["key1", "key2"]
store.clear()         # Empty store
```

---

## Best Practices

- id:: memory-best-practices

✅ **Start with zero-setup** - Don't add Redis until you need it
✅ **Use descriptive keys** - Include user_id, session_id, context
✅ **Set appropriate max_size** - Based on expected memory per session
✅ **Search before generating** - Use context for better responses
✅ **Clear old sessions** - Implement session cleanup logic

❌ **Don't store sensitive data** - Memory may be logged
❌ **Don't assume persistence** - InMemory clears on restart
❌ **Don't skip the key helper** - Use `create_memory_key()`

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/CachePrimitive]] - Cache expensive operations
- [[TTA.dev/Primitives/RouterPrimitive]] - Route based on memory context
- [[TTA.dev/Primitives/SequentialPrimitive]] - Multi-step workflows with memory

### Related Documentation

- [[TTA.dev/Guides/Context Management]] - Managing agent context
- [[TTA.dev/Examples/Memory Workflow]] - Example memory workflows

---

## Metadata

**Source Code:** [memory.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/performance/memory.py)
**Tests:** [test_memory.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/performance/test_memory.py)

**Created:** [[2025-12-03]]
**Last Updated:** [[2025-12-03]]
**Status:** [[Stable]] - Production Ready
