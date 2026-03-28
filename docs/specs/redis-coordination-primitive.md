# Spec: Redis Coordination Primitive

- **Issue:** [#240](https://github.com/theinterneti/TTA.dev/issues/240)
- **Status:** Draft — awaiting sign-off
- **Author:** Claude Code (session 2026-03-25)
- **SDD Phase:** `/specify`

---

## Problem

TTA owns a Redis-backed message coordination layer
(`src/agent_orchestration/coordinators/redis_message_coordinator.py`) that is
generic infrastructure — priority queues, visibility timeouts, ack/nack
semantics, DLQ routing, backpressure, `recover_pending` — but it is coupled to
TTA-specific types (`AgentId`, `AgentType`, `AgentMessage`).

This blocks TTA from pointing its coordination concerns at TTA.dev and prevents
other projects from reusing the pattern.

---

## Goal

Extract and generalize the Redis coordination layer into a
`ttadev/primitives/coordination/` package that:

- has **no TTA domain types** (no IPA/WBA/NGA, no therapeutic semantics)
- uses a generic string-based identity model
- preserves all reliability semantics: priority, visibility timeout, ack/nack,
  DLQ, backpressure, `recover_pending`
- is covered by unit tests (fake Redis) and documented

---

## Identity model

Replace `AgentId(type: AgentType, instance: str | None)` with:

```python
class QueueEndpoint(BaseModel):
    queue_type: str      # e.g. "worker", "ingester", "reviewer" — caller-defined
    instance: str = "default"  # shard/pool identifier
```

`queue_type` is a plain string — callers define their own taxonomy.  TTA wraps
`QueueEndpoint` with its own `AgentId` → `QueueEndpoint` adapter.

---

## Message model

Replace `AgentMessage(sender, recipient, message_type, payload, ...)` with:

```python
class CoordinationMessage(BaseModel):
    message_id: str
    sender: str          # opaque identifier, e.g. "worker:default"
    message_type: str    # caller-defined label
    payload: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str | None = None
```

`MessagePriority` (LOW=1, NORMAL=5, HIGH=9) is kept — it drives Redis zset
scoring and is domain-agnostic.

---

## Proposed package layout

```
ttadev/primitives/coordination/
├── __init__.py          # exports QueueEndpoint, CoordinationMessage,
│                        #   MessagePriority, QueuedMessage, ReceivedMessage,
│                        #   FailureType, MessageResult,
│                        #   MessageCoordinator (ABC),
│                        #   RedisMessageCoordinator
├── models.py            # QueueEndpoint, CoordinationMessage, MessagePriority,
│                        #   QueuedMessage, ReceivedMessage, FailureType,
│                        #   MessageResult
├── coordinator.py       # MessageCoordinator ABC
└── redis_coordinator.py # RedisMessageCoordinator implementation
```

The `redis` package (`redis[asyncio]`) is an **optional dependency** — imported
lazily inside `RedisMessageCoordinator.__init__`.  Projects without Redis can
still import and test the models and ABC.

---

## Key behavioral decisions

| Concern | Decision |
|---|---|
| `recover_pending` with no agent_id | Scans `{prefix}:reserved_deadlines:*` via `scan_iter` — no hardcoded queue-type enum |
| Metrics | Lightweight counters on `RedisMessageCoordinator` instance (`delivered_ok`, `delivered_error`, `retries_scheduled`, `nacks`, `dlq_enqueued`); callers wire to OTel if desired |
| Key scheme | Unchanged from TTA: `{pfx}:{role}:{queue_type}:{instance}` |
| Backoff | Configurable via `configure()`: `backoff_base`, `backoff_factor`, `backoff_max` |
| Queue size cap | Configurable via `configure()`: `queue_size` (default 10 000) |

---

## Out of scope

- Agent routing / discovery (companion registry) — tracked separately
- TTA-specific `AgentId` → `QueueEndpoint` adapter (lives in TTA, not TTA.dev)
- Narrative, therapeutic, or gameplay semantics
- Pub/sub (separate concern from queue coordination)

---

## TTA adoption path

Once the primitive lands, TTA should:

1. Add `ttadev` to its dependencies (already planned).
2. In `src/agent_orchestration/`, add an adapter:
   ```python
   def _to_endpoint(agent_id: AgentId) -> QueueEndpoint:
       return QueueEndpoint(queue_type=agent_id.type.value,
                            instance=agent_id.instance or "default")
   ```
3. Replace `RedisMessageCoordinator` instantiation with the TTA.dev import.
4. Keep `AgentMessage` → `CoordinationMessage` conversion at the TTA boundary.

---

## Acceptance criteria

- [ ] `ttadev/primitives/coordination/` package exists with the layout above
- [ ] No TTA-specific types (`AgentType`, `AgentId`, `AgentMessage`) anywhere in the package
- [ ] `recover_pending(None)` scans by key pattern, not by hardcoded type enum
- [ ] Unit tests cover: send/receive/ack/nack, DLQ routing, backpressure,
  `recover_pending`, backoff scheduling — using a fake/mock Redis client
- [ ] `redis[asyncio]` listed as optional dep (`[coordination]` extra in `pyproject.toml`)
- [ ] `PRIMITIVES_CATALOG.md` updated
- [ ] Issue #240 comment documents the registry/discovery decision (out of scope, separate issue)

---

## Open questions

1. **Registry/discovery scope** — confirm out of scope for this issue (separate tracking).
2. **Fake Redis for tests** — use `fakeredis` package or hand-rolled async mock?
   Preference: `fakeredis[aioredis]` as a dev-only dependency for realistic coverage.
