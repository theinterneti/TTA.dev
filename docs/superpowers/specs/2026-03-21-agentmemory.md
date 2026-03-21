# Functional Specification: AgentMemory

**Date:** 2026-03-21
**Phase:** 2b — Recall Step of the DevelopmentCycle
**Status:** Draft — awaiting approval
**Depends on:** `CodeGraphPrimitive` (Phase 2a, complete)
**Leads to:** `DevelopmentCycle` (Phase 3)

---

## Overview

`AgentMemory` is the **Recall step** of the DevelopmentCycle loop. It wraps the Hindsight HTTP API as a typed Python service class, giving agents and workflows programmatic access to:

- **Recall** — retrieve semantically relevant memories before a task
- **Retain** — save decisions, patterns, and failures after a task
- **Directives** — load persistent rules that prefix every agent system prompt
- **Mental models** — load synthesized module summaries for context orientation

> **Design note:** `AgentMemory` is a *service class*, not an `InstrumentedPrimitive`. It is a collaborator attached to a workflow or agent, not a pipeline step. Agents call it before and after their `execute()`, not during.

---

## Motivation

`CodeGraphPrimitive` answers: *"What does this code touch?"*
`AgentMemory` answers: *"What do we already know about this task?"*

Together they form the Orient + Recall prologue that grounds every LLM call with structured, codebase-aware context — making free models (Ollama, OpenRouter `:free`) produce reliably better output without prompt engineering in every agent.

---

## User Journeys

### Journey 1 — DevelopmentCycle recall prologue

```python
memory = AgentMemory(bank_id="tta-dev")
context_prefix = await memory.build_context_prefix(query="adding a new primitive")
# Returns directives + relevant memories formatted as a system prompt prefix
# → injected into the agent's system_prompt before the LLM call
```

### Journey 2 — Retain a decision after a task

```python
await memory.retain(
    "[type: decision] Used FalkorDB direct socket instead of CLI. "
    "Rationale: CLI output is Rich tables, not JSON-parseable."
)
# Hindsight stores the memory; async=True to avoid rate-limiting LLM synthesis
```

### Journey 3 — Get directives for system prompt

```python
directives = await memory.get_directives()
# Returns list of directive texts: ["Always orient with CGC...", "Use uv, never pip..."]
```

### Journey 4 — Recall targeted memories for a query

```python
memories = await memory.recall("retry primitive timeout handling")
# Returns list of MemoryResult(id, text, type) ordered by relevance
```

### Journey 5 — Graceful degradation

```python
memory = AgentMemory(bank_id="tta-dev", base_url="http://localhost:8888")
# If Hindsight is not running → recall() returns [], retain() is a no-op
# No exceptions raised — DevelopmentCycle continues without memory context
```

### Journey 6 — Custom bank for an app

```python
# App-specific memory bank: myapp.assistant
memory = AgentMemory(bank_id="myapp.assistant")
await memory.retain("User prefers concise responses")
memories = await memory.recall("user communication style")
```

---

## Input/Output Contract

### `AgentMemory` constructor

```python
class AgentMemory:
    def __init__(
        self,
        bank_id: str,
        base_url: str | None = None,  # default: env HINDSIGHT_URL or http://localhost:8888
        timeout: float = 10.0,
    ) -> None: ...
```

### `recall(query, budget="mid", types=None)` → `list[MemoryResult]`

```python
class MemoryResult(TypedDict):
    id: str
    text: str
    type: str | None  # "world", "experience", "observation"

async def recall(
    self,
    query: str,
    budget: Literal["low", "mid", "high"] = "mid",
    types: list[str] | None = None,
) -> list[MemoryResult]: ...
```

Returns empty list if Hindsight unavailable or query returns no results.

### `retain(content, async_=True)` → `RetainResult`

```python
class RetainResult(TypedDict):
    success: bool
    operation_id: str | None  # None if sync or unavailable

async def retain(
    self,
    content: str,
    async_: bool = True,  # True = background, no rate-limit risk
) -> RetainResult: ...
```

Returns `RetainResult(success=False, operation_id=None)` if Hindsight unavailable.

### `get_directives()` → `list[str]`

```python
async def get_directives(self) -> list[str]: ...
```

Returns list of directive text strings from the bank. Returns `[]` if unavailable.

### `get_mental_model(name)` → `str | None`

```python
async def get_mental_model(self, name: str) -> str | None: ...
```

Returns the mental model content text, or `None` if not found or Hindsight unavailable.

### `build_context_prefix(query)` → `str`

```python
async def build_context_prefix(self, query: str) -> str: ...
```

Calls `get_directives()` and `recall(query)` in parallel, then formats the combined result as a system-prompt-friendly string:

```
## Directives
- Always orient with CGC before editing...
- Use uv, never pip...

## Relevant context
- [decision] Used FalkorDB direct socket instead of CLI...
- [pattern] InstrumentedPrimitive._execute_impl...
```

Returns `""` if both calls return empty.

### `is_available()` → `bool`

```python
def is_available(self) -> bool: ...
```

Synchronous HTTP GET `/health` with 1s timeout. Returns `True` if Hindsight responds.

---

## Five Operations (internal)

| Method | HTTP call | Purpose |
|---|---|---|
| `recall` | `POST /v1/default/banks/{id}/memories/recall` | Semantic search over memories |
| `retain` | `POST /v1/default/banks/{id}/memories` | Store new memory |
| `get_directives` | `GET /v1/default/banks/{id}/directives` | Load persistent rules |
| `get_mental_model` | `GET /v1/default/banks/{id}/mental-models/{name}` | Load a mental model |
| `is_available` | `GET /health` | Liveness check |

---

## Edge Cases

| Scenario | Behaviour |
|---|---|
| Hindsight not running | All methods degrade gracefully: `recall` → `[]`, `retain` → `RetainResult(success=False)`, `get_directives` → `[]`, `get_mental_model` → `None`, `build_context_prefix` → `""` |
| HTTP timeout (>10s) | Same as not running — log warning, return safe default |
| `recall` with empty query | Raise `ValueError("query must not be empty")` |
| `retain` with empty content | Raise `ValueError("content must not be empty")` |
| Bank does not exist | `recall` → `[]`, `get_directives` → `[]` (Hindsight returns 404 → treat as empty) |
| `get_mental_model` name not found | Returns `None` (not an error) |
| `build_context_prefix` with empty query | Raise `ValueError("query must not be empty")` — same as `recall` |
| Network error mid-stream | Catch all `httpx.HTTPError` → log warning → return safe default |

---

## File Layout

| Action | Path | Purpose |
|---|---|---|
| Create | `ttadev/primitives/memory/__init__.py` | Package exports |
| Create | `ttadev/primitives/memory/types.py` | `MemoryResult`, `RetainResult` TypedDicts |
| Create | `ttadev/primitives/memory/client.py` | `HindsightClient` — HTTP transport layer |
| Create | `ttadev/primitives/memory/agent_memory.py` | `AgentMemory` — the public service class |
| Modify | `ttadev/primitives/__init__.py` | Export `AgentMemory`, `MemoryResult`, `RetainResult` |
| Create | `tests/primitives/memory/__init__.py` | Test package |
| Create | `tests/primitives/memory/test_client.py` | `HindsightClient` unit tests |
| Create | `tests/primitives/memory/test_agent_memory.py` | `AgentMemory` unit tests |

---

## Success Criteria

1. `AgentMemory("tta-dev")` constructs without errors whether or not Hindsight is running
2. `recall(query)` returns a `list[MemoryResult]` — never raises on connectivity failures
3. `retain(content)` returns `RetainResult` — never raises on connectivity failures
4. `get_directives()` returns `list[str]` — never raises on connectivity failures
5. `get_mental_model(name)` returns `str | None` — never raises on connectivity failures
6. `build_context_prefix(query)` calls `get_directives` and `recall` concurrently (not serially)
7. `is_available()` completes in ≤1s (synchronous socket check or fast HTTP GET)
8. Empty `query` or `content` raises `ValueError` immediately (before any HTTP call)
9. `AgentMemory`, `MemoryResult`, `RetainResult` importable from `ttadev.primitives`
10. 100% test coverage using mocked `httpx` responses — no live Hindsight calls in unit tests
11. `HindsightClient` uses `httpx.AsyncClient` (not `requests`) for all HTTP calls

---

## Out of Scope

- Mental model creation or update (`retain_mental_model`) — Hindsight synthesizes these automatically from retained memories
- Bank creation (`create_bank`) — banks must be pre-created via Hindsight MCP tools or CLI
- Directive creation (`create_directive`) — managed via Hindsight tools, not programmatically
- Observation history, entity state, or graph APIs — advanced Hindsight features not needed for DevelopmentCycle
- Streaming recall responses
- Caching recalled memories (a `CachePrimitive` wrapper can be added later)
- Authentication / API keys (Hindsight runs locally, no auth required)

---

## Relationship to `DevelopmentCycle`

When `DevelopmentCycle` (Phase 3) is built, it will use `AgentMemory` like this:

```python
class DevelopmentCycle(InstrumentedPrimitive[DevelopmentTask, DevelopmentResult]):
    def __init__(self, bank_id: str = "tta-dev", ...):
        self._memory = AgentMemory(bank_id=bank_id)
        self._graph = CodeGraphPrimitive()

    async def _execute_impl(self, task, context):
        # Step 1 — Orient
        impact = await self._graph.execute(CodeGraphQuery(...), context)
        # Step 2 — Recall
        prefix = await self._memory.build_context_prefix(task.instruction)
        # Step 3 — Write (agent call with prefix injected)
        ...
        # Step 5 — Retain
        await self._memory.retain(f"[type: decision] {result.summary}")
```

`AgentMemory` is infrastructure that `DevelopmentCycle` consumes — it has no knowledge of the cycle itself.
