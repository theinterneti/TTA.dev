# Plan: Redis Coordination Primitive

- **Spec:** [redis-coordination-primitive.md](redis-coordination-primitive.md)
- **Issue:** [#240](https://github.com/theinterneti/TTA.dev/issues/240)
- **Status:** Ready to implement
- **SDD Phase:** `/plan`

---

## Package layout

```
ttadev/primitives/coordination/
├── __init__.py          # public exports
├── models.py            # QueueEndpoint, CoordinationMessage, MessagePriority,
│                        #   QueuedMessage, ReceivedMessage, FailureType,
│                        #   MessageResult, MessageSubscription
├── coordinator.py       # MessageCoordinator ABC
└── redis_coordinator.py # RedisMessageCoordinator
```

`pyproject.toml` — add `coordination` optional-dep group:
```toml
[project.optional-dependencies]
coordination = ["redis[asyncio]>=5.0"]
```

`PRIMITIVES_CATALOG.md` — add coordination section.

---

## Implementation steps

### Step 1 — models.py

Port and generalize from TTA's `messaging.py` + `models.py`:

| TTA type | TTA.dev type | Change |
|---|---|---|
| `AgentType` (enum IPA/WBA/NGA) | removed | callers use plain strings |
| `AgentId(type, instance)` | `QueueEndpoint(queue_type: str, instance: str = "default")` | string-based |
| `AgentMessage` | `CoordinationMessage` | remove `sender`/`recipient` as `AgentId`; `sender: str`, `message_type: str`, `payload: dict` |
| `MessagePriority` (LOW=1,NORMAL=5,HIGH=9) | `MessagePriority` | identical |
| `QueueMessage` | `QueuedMessage` | wraps `CoordinationMessage` instead of `AgentMessage` |
| `ReceivedMessage` | `ReceivedMessage` | unchanged semantics |
| `FailureType` | `FailureType` | identical |
| `MessageResult` | `MessageResult` | identical |
| `MessageSubscription` | `MessageSubscription` | `endpoint_id: str` instead of `agent_id: AgentId` |

### Step 2 — coordinator.py

Port `interfaces.py` `MessageCoordinator` ABC. Replace all `AgentId` params with
`QueueEndpoint`. Remove `MessageType` list from `subscribe_to_messages` signature
(use `list[str]` instead).

### Step 3 — redis_coordinator.py

Port `RedisMessageCoordinator`. Key changes:

1. All `AgentId` params → `QueueEndpoint`.
2. Key helpers: use `endpoint.queue_type` and `endpoint.instance` in place of
   `agent_id.type.value` and `agent_id.instance or "default"`.
3. `recover_pending(endpoint=None)`: replace the hardcoded
   `for at in (AgentType.IPA, AgentType.WBA, AgentType.NGA)` loop with a
   `scan_iter(match=f"{pfx}:reserved_deadlines:*")` scan that parses
   `queue_type:instance` from the key suffix.
4. `MessageMetrics` inline: replace the imported `metrics.py` with a simple
   dataclass counter on the coordinator instance (no external dep).
5. Lazy `redis` import inside `__init__` with a clear error if not installed.

### Step 4 — __init__.py

Export the full public surface.

### Step 5 — pyproject.toml

Add `coordination = ["redis[asyncio]>=5.0"]` optional dep.

### Step 6 — tests

File: `tests/primitives/coordination/test_redis_coordinator.py`

Use `fakeredis.aioredis` (add to `dev` extra) for realistic async Redis.

Test groups (AAA pattern, 100% coverage for new code):

| Group | Cases |
|---|---|
| send/receive | happy path, queue full backpressure |
| ack | removes reservation + audit entry |
| nack transient | reschedules with backoff, increments attempts |
| nack permanent | routes to DLQ immediately |
| nack exceeds retries | routes to DLQ after N attempts |
| recover_pending | reclaims expired reservations; poison-pill goes to DLQ |
| recover_pending(None) | scans all queue types via key pattern |
| priority ordering | HIGH delivered before NORMAL before LOW |
| configure() | queue_size, retry_attempts, backoff params honoured |

### Step 7 — PRIMITIVES_CATALOG.md

Add a `## Coordination` section documenting `QueueEndpoint`,
`CoordinationMessage`, `RedisMessageCoordinator`, and the `[coordination]`
install extra.

---

## Dependencies to add

```toml
# pyproject.toml
[project.optional-dependencies]
coordination = ["redis[asyncio]>=5.0"]
dev = [
    ...,
    "fakeredis>=2.26",   # add to existing dev group
]
```

---

## Quality gate

```bash
uv run ruff check . --fix
uvx pyright ttadev/
uv run pytest tests/primitives/coordination/ -v
```

---

## Estimated scope

~300 lines of source + ~250 lines of tests. No migrations, no schema changes,
no breaking changes to existing primitives.
