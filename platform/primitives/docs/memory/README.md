# Memory Primitives

**Context-aware memory for AI workflows. Works immediately, enhanced with Redis.**

## Quick Start (Zero Setup)

```python
from tta_dev_primitives.performance.memory import MemoryPrimitive

# Works immediately - no Docker, no Redis, no setup!
memory = MemoryPrimitive()

# Store context
await memory.add("user:123:session:abc", {
    "conversation": "User asked about weather",
    "intent": "weather_query"
})

# Retrieve context
context = await memory.get("user:123:session:abc")

# Search memories
results = await memory.search("weather")
```

**Run the example:**
```bash
python examples/memory_workflow.py
```

## Why This Design?

**Problem:** Many memory solutions require complex setup (Docker, Redis, vector databases).
This creates a barrier to entry and makes examples difficult to run.

**Solution:** Hybrid architecture with automatic fallback:

- ✅ **Works immediately** - InMemoryStore with no dependencies
- ✅ **Enhanced when ready** - Optional Redis for persistence
- ✅ **Same API** - Code works identically in both modes
- ✅ **Graceful degradation** - Automatic fallback if Redis unavailable

## Components

### InMemoryStore

Simple LRU cache for working memory. Perfect for learning, examples, and development.

```python
from tta_dev_primitives.performance.memory import InMemoryStore

store = InMemoryStore(max_size=1000)

# Add memory
store.add("key1", {"data": "value"})

# Retrieve memory
result = store.get("key1")

# Search (keyword matching)
results = store.search("keyword", limit=5)
```

**Features:**
- LRU eviction (least recently used items removed when full)
- Keyword search (simple substring matching)
- Thread-safe for asyncio
- No external dependencies

**Limitations:**
- No persistence (data lost on restart)
- No semantic search (keyword matching only)
- Not shared across processes
- Limited by available RAM

### MemoryPrimitive

Hybrid memory primitive with automatic fallback.

```python
from tta_dev_primitives.performance.memory import MemoryPrimitive

# Option 1: In-memory only (default)
memory = MemoryPrimitive()

# Option 2: With Redis (optional)
memory = MemoryPrimitive(redis_url="redis://localhost:6379")

# Same API regardless of backend
await memory.add(key, value)
result = await memory.get(key)
results = await memory.search(query)
```

**Features:**
- Hybrid architecture (in-memory fallback + optional Redis)
- Automatic graceful degradation
- Consistent API across backends
- Optional TTL support (Redis only)

### Helper Functions

```python
from tta_dev_primitives.performance.memory import create_memory_key

# Create deterministic keys
key = create_memory_key(
    user_id="user123",
    session_id="session456",
    context={"turn": 1, "task": "summarize"}
)
# Returns: "user123:session456:a1b2c3d4"
```

## Usage Patterns

### Multi-Turn Conversations

```python
from tta_dev_primitives.performance.memory import MemoryPrimitive, create_memory_key

memory = MemoryPrimitive()

# Store conversation turns
for turn_num in range(1, 4):
    key = create_memory_key(
        user_id="user_123",
        session_id="session_abc",
        context={"turn": turn_num}
    )

    await memory.add(key, {
        "user_message": f"Message {turn_num}",
        "assistant_response": f"Response {turn_num}",
        "timestamp": datetime.now().isoformat()
    })

# Search conversation history
weather_context = await memory.search("weather")
```

### Task-Specific Context

```python
# Store task context
task_key = create_memory_key(
    user_id="user_123",
    session_id="session_abc",
    context={"task": "code_review", "file": "main.py"}
)

await memory.add(task_key, {
    "file_path": "main.py",
    "review_notes": ["Line 42: Consider error handling"],
    "status": "in_progress"
})

# Retrieve task context later
task_context = await memory.get(task_key)
```

### Persistent Context (with Redis)

```python
# Upgrade to Redis for persistence
memory = MemoryPrimitive(redis_url="redis://localhost:6379")

# Add with TTL (time-to-live)
await memory.add(
    key="temp_context",
    value={"data": "temporary"},
    ttl=3600  # Expires in 1 hour
)

# Data persists across restarts!
```

## When to Use Each Mode

### Use In-Memory Mode When:
- Learning TTA.dev
- Running examples
- Local development
- Docker not available
- Quick prototyping
- Context doesn't need persistence

### Upgrade to Redis When:
- Need persistence across restarts
- Sharing memory across processes
- Production deployments
- Large working memory (>1GB)
- Want semantic search (with RediSearch)

## Adding Redis (Optional)

### 1. Install Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
# macOS: brew install redis
# Ubuntu: apt-get install redis-server
```

### 2. Install redis-py

```bash
pip install redis
```

### 3. Update Your Code

```python
# Before (in-memory only)
memory = MemoryPrimitive()

# After (with Redis)
memory = MemoryPrimitive(redis_url="redis://localhost:6379")

# That's it! Same API, enhanced features
```

### 4. Automatic Fallback

If Redis is unavailable, MemoryPrimitive automatically falls back:

```python
# Tries Redis, falls back to in-memory if unavailable
memory = MemoryPrimitive(redis_url="redis://invalid:9999")

# Your code still works!
await memory.add("key", {"data": "value"})
```

## Architecture Decision

This hybrid approach was chosen to solve a critical problem: **Docker is a barrier**.

Traditional memory solutions require:
- Docker installed and running ❌
- Redis container setup ❌
- Volume configuration ❌
- Network configuration ❌
- API keys and credentials ❌

Our solution:
- Works immediately ✅
- Enhanced when ready ✅
- Same API always ✅
- Agent-friendly ✅

See [REDIS_MEMORY_SPIKE.md](../../docs/architecture/REDIS_MEMORY_SPIKE.md) for full design discussion.

## API Reference

### InMemoryStore

```python
class InMemoryStore:
    def __init__(self, max_size: int = 1000) -> None: ...
    def add(self, key: str, value: dict[str, Any]) -> None: ...
    def get(self, key: str) -> dict[str, Any] | None: ...
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]: ...
    def clear(self) -> None: ...
    def size(self) -> int: ...
    def keys(self) -> list[str]: ...
```

### MemoryPrimitive

```python
class MemoryPrimitive:
    def __init__(
        self,
        redis_url: str | None = None,
        max_size: int = 1000,
        enable_redis: bool = True
    ) -> None: ...

    async def add(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None
    ) -> None: ...

    async def get(self, key: str) -> dict[str, Any] | None: ...
    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]: ...
    async def clear(self) -> None: ...
    def size(self) -> int: ...
    def is_using_redis(self) -> bool: ...
    def get_backend_info(self) -> dict[str, Any]: ...
```

### Helper Functions

```python
def create_memory_key(
    user_id: str,
    session_id: str,
    context: dict[str, Any] | None = None
) -> str: ...
```

## Testing

```bash
# Run tests
uv run pytest packages/tta-dev-primitives/tests/performance/test_memory.py -v

# With coverage
uv run pytest packages/tta-dev-primitives/tests/performance/test_memory.py --cov

# Run example
uv run python packages/tta-dev-primitives/examples/memory_workflow.py
```

## Future Enhancements

Potential additions (PRs welcome!):

1. **Semantic Search**: RediSearch integration for vector similarity
2. **Namespacing**: Better key isolation for multi-tenant scenarios
3. **Async Redis**: Use `redis.asyncio` for true async operations
4. **Memory Compression**: Compress large contexts automatically
5. **Memory Summarization**: Auto-summarize old contexts to save space
6. **Memory Primitive Integration**: Extend `InstrumentedPrimitive` for full observability

## Related

- **External Repo Analysis**: [EXTERNAL_REPO_ANALYSIS_SUMMARY.md](../../docs/architecture/EXTERNAL_REPO_ANALYSIS_SUMMARY.md)
- **Architecture Spike**: [REDIS_MEMORY_SPIKE.md](../../docs/architecture/REDIS_MEMORY_SPIKE.md)
- **Integration Experiments**: [INTEGRATION_EXPERIMENTS.md](../../docs/architecture/INTEGRATION_EXPERIMENTS.md)

## License

See package license (MIT expected, inherits from tta-dev-primitives)


---
**Logseq:** [[TTA.dev/Platform/Primitives/Docs/Memory/Readme]]
