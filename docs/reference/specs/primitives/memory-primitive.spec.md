# MemoryPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/performance/memory.py`

## 1. Purpose

`MemoryPrimitive` provides multi-turn conversational memory with a hybrid backend:
an always-available in-memory store (`InMemoryStore`) with optional Redis persistence.
It enables workflows to store, retrieve, and search contextual data across executions.

**Note:** `MemoryPrimitive` is NOT a `WorkflowPrimitive` subclass. It is a standalone
service class used directly by workflow code.

## 2. InMemoryStore Contract

### 2.1 Type Signature

```python
class InMemoryStore:
    def __init__(self, max_size: int = 1000): ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_size` | `int` | `1000` | Maximum number of items; LRU eviction when exceeded |

### 2.3 Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `add` | `(key: str, value: dict[str, Any]) -> None` | Add or update an item; moves existing keys to end (MRU); evicts LRU if over capacity |
| `get` | `(key: str) -> dict[str, Any] \| None` | Retrieve item by key; marks as recently used; returns `None` if not found |
| `search` | `(query: str, limit: int = 5) -> list[dict[str, Any]]` | Case-insensitive substring search across all string values; returns most recent first |
| `clear` | `() -> None` | Remove all items |
| `size` | `() -> int` | Get current item count |
| `keys` | `() -> list[str]` | Get all keys (oldest first, most recent last) |

### 2.4 Behavior Invariants

- `add()` MUST use `OrderedDict` for LRU ordering.
- `add()` MUST evict the oldest entry when `size >= max_size`.
- `get()` MUST move the accessed key to the end (mark as recently used).
- `search()` MUST be case-insensitive.
- `search()` MUST return results ordered most-recent-first.
- `search()` MUST respect the `limit` parameter.

## 3. MemoryPrimitive Contract

### 3.1 Type Signature

```python
class MemoryPrimitive:
    def __init__(
        self,
        redis_url: str | None = None,
        max_size: int = 1000,
        enable_redis: bool = True,
    ): ...
```

### 3.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `redis_url` | `str \| None` | `None` | Redis connection URL (e.g., `redis://localhost:6379`) |
| `max_size` | `int` | `1000` | Max size for in-memory fallback store |
| `enable_redis` | `bool` | `True` | Whether to attempt Redis connection |

### 3.3 Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `add` | `async (key: str, value: dict[str, Any], ttl: int \| None = None) -> None` | Store a memory; attempts Redis first, falls back to in-memory |
| `get` | `async (key: str) -> dict[str, Any] \| None` | Retrieve memory by key |
| `search` | `async (query: str, limit: int = 5) -> list[dict[str, Any]]` | Search memories (uses in-memory search) |
| `clear` | `async () -> None` | Clear all memories |
| `size` | `() -> int` | Get current memory count |
| `is_using_redis` | `() -> bool` | Check if Redis backend is active |
| `get_backend_info` | `() -> dict[str, Any]` | Returns `backend`, `fallback_available`, `size` |

### 3.4 Behavior Invariants

- Constructor MUST always create an `InMemoryStore` as fallback.
- If `enable_redis` is `True` and `redis_url` is provided, constructor MUST attempt Redis connection.
- If Redis connection fails, constructor MUST fall back to `InMemoryStore` silently (log warning).
- `add()` MUST NOT raise exceptions; on Redis failure, it MUST fall back to in-memory.
- `add()` with Redis MAY accept a `ttl` parameter for automatic expiration.
- `get()` MUST return `None` for non-existent keys (never raise `KeyError`).
- `search()` MUST use the in-memory store regardless of backend.
- All methods MUST gracefully degrade on Redis failure.

### 3.5 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Redis unavailable | *(none)* | Graceful fallback to in-memory store |
| Invalid `redis_url` | *(none)* | Logged as warning; falls back to in-memory |
| Key not found | *(none)* | Returns `None` |

### 3.6 Observability Contract

**Logging:**

| Event | Level | Description |
|-------|-------|-------------|
| Redis connection success | INFO | `"Connected to Redis"` |
| Redis connection failure | WARNING | `"Redis unavailable, using in-memory fallback"` |
| Redis operation failure | WARNING | `"Redis operation failed, falling back"` |

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| `redis_url = None`, `enable_redis = True` | Uses in-memory store only |
| `redis_url = "invalid://url"` | Logs warning, uses in-memory store |
| `max_size = 0` | Every `add()` immediately evicts the oldest entry |
| `search("")` (empty query) | Returns all items up to `limit` |
| `add()` with `ttl=0` on Redis | Behavior depends on Redis (may expire immediately) |

## 5. Cross-References

- [CachePrimitive Spec](cache-primitive.spec.md) — Short-term caching counterpart
- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class (MemoryPrimitive does NOT extend this)
