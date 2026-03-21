# Functional Specification: DevelopmentCycle

**Date:** 2026-03-21
**Phase:** 3 — The loop as a single composable primitive
**Status:** Draft — awaiting approval
**Depends on:** `CodeGraphPrimitive` (Phase 2a, complete), `AgentMemory` (Phase 2b, complete)
**Leads to:** Phase 4 — Automation (hooks, pre-commit, auto-retain)

---

## Overview

`DevelopmentCycle` is a **composable `InstrumentedPrimitive`** that executes the full five-step development loop — Orient → Recall → Write → Validate → Retain — as a single, observable unit.

It composes three previously-built primitives (`CodeGraphPrimitive`, `AgentMemory`, `CodeExecutionPrimitive`) with an LLM call (via `get_llm_client()`) into one typed, traceable operation that any workflow or agent can invoke.

> **Design note:** `DevelopmentCycle` is an `InstrumentedPrimitive[DevelopmentTask, DevelopmentResult]`. It lives in `ttadev/workflows/development_cycle.py` because it composes workflow-level concerns (LLM provider strategy, E2B validation, memory persistence) that belong at the workflow layer, not the primitive layer.

---

## Motivation

`CodeGraphPrimitive` answers: *"What does this code touch?"*
`AgentMemory` answers: *"What do we already know about this task?"*
`DevelopmentCycle` answers: *"What should be built, given what we know — and does it work?"*

Together these three form the complete Orient + Recall + Write + Validate + Retain loop that turns a free Ollama model into a grounded, context-aware, self-improving development agent.

---

## The Five Steps

```
CGC            Hindsight       LLM (free)     E2B            Hindsight
  |                |               |              |               |
[1. Orient] → [2. Recall] → [3. Write] → [4. Validate] → [5. Retain]
```

| Step | Primitive | Failure behaviour |
|---|---|---|
| Orient | `CodeGraphPrimitive` | Unavailable → empty `ImpactReport`, `cgc_available=False` |
| Recall | `AgentMemory.build_context_prefix` | Unavailable → empty string prefix |
| Write | `get_llm_client()` + OpenAI chat | Raises — Write failure is not silent |
| Validate | `CodeExecutionPrimitive` | Unavailable or no tests → `validated=False`, not an error |
| Retain | `AgentMemory.retain` | Unavailable → no-op, `memories_retained=0` |

---

## User Journeys

### Journey 1 — Basic development task

```python
cycle = DevelopmentCycle(bank_id="tta-dev")
context = WorkflowContext()

result = await cycle.execute(
    DevelopmentTask(
        instruction="Add a timeout parameter to RetryPrimitive",
        target_files=["ttadev/primitives/recovery/retry.py"],
    ),
    context,
)
# result.response     → LLM-generated implementation plan or code
# result.validated    → True if E2B ran related tests and they passed
# result.impact_report → callers, complexity, related_tests from CGC
# result.memories_retained → number of facts stored to Hindsight
```

### Journey 2 — Graceful degradation when CGC is offline

```python
cycle = DevelopmentCycle(bank_id="tta-dev")
result = await cycle.execute(
    DevelopmentTask(instruction="Refactor the cache primitive"),
    context,
)
# CGC unavailable → ImpactReport with cgc_available=False
# Recall still runs, Write still runs with partial context
# result.impact_report.cgc_available == False
# result.response contains the LLM output — cycle did not abort
```

### Journey 3 — Graceful degradation when Hindsight is offline

```python
# Hindsight down → recall returns "", retain is a no-op
result = await cycle.execute(
    DevelopmentTask(instruction="Add logging to the timeout primitive"),
    context,
)
# result.response is still produced — LLM ran with no memory prefix
# result.memories_retained == 0
```

### Journey 4 — Graceful degradation when E2B is offline

```python
# E2B unavailable or no related tests found → validated=False, not an error
result = await cycle.execute(
    DevelopmentTask(instruction="Update the README example"),
    context,
)
# result.validated == False (no executable tests to run)
# result.response still contains the LLM output
```

### Journey 5 — Custom role (agent_hint)

```python
cycle = DevelopmentCycle(bank_id="tta-dev")
result = await cycle.execute(
    DevelopmentTask(
        instruction="Review the retry primitive for security issues",
        agent_hint="security",  # changes the system prompt persona
    ),
    context,
)
```

### Journey 6 — Composition with other primitives

```python
# DevelopmentCycle composes like any InstrumentedPrimitive
dev = DevelopmentCycle(bank_id="tta-dev")
review = DevelopmentCycle(bank_id="tta-dev", agent_hint="qa")

# Sequential: dev writes, then review validates
pipeline = SequentialPrimitive([dev, review])
```

### Journey 7 — Custom bank for an app

```python
# App-specific bank — not tied to "tta-dev"
cycle = DevelopmentCycle(bank_id="myapp.assistant")
result = await cycle.execute(
    DevelopmentTask(instruction="Generate a data pipeline"),
    context,
)
```

---

## Input/Output Contract

### `DevelopmentTask`

```python
class DevelopmentTask(TypedDict, total=False):
    instruction: str          # Required: task description for the LLM
    target_files: list[str]   # Optional: file paths/names to orient CGC on
    agent_hint: str           # Optional: role persona for Write step (default: "developer")
```

`instruction` is required. `target_files` and `agent_hint` are optional (default `[]` and `"developer"` respectively).

Raises `ValueError("instruction must not be empty")` if instruction is missing or blank.

### `DevelopmentResult`

```python
class DevelopmentResult(TypedDict):
    response: str             # LLM output (code, plan, analysis, etc.)
    validated: bool           # True if E2B ran tests and they passed
    impact_report: ImpactReport   # From Orient step (may be empty if CGC unavailable)
    memories_retained: int    # Number of facts stored to Hindsight (0 if unavailable)
    context_prefix: str       # The memory prefix injected into the LLM system prompt
```

### `DevelopmentCycle` constructor

```python
class DevelopmentCycle(InstrumentedPrimitive[DevelopmentTask, DevelopmentResult]):
    def __init__(
        self,
        bank_id: str = "tta-dev",
        base_url: str | None = None,    # Hindsight base URL (default: HINDSIGHT_URL or localhost:8888)
        agent_hint: str = "developer",  # Default role persona for Write step
        timeout: float = 10.0,          # Hindsight and CGC timeout
        _memory: AgentMemory | None = None,           # injected in tests
        _graph: CodeGraphPrimitive | None = None,     # injected in tests
        _executor: CodeExecutionPrimitive | None = None,  # injected in tests
    ) -> None: ...
```

`agent_hint` on the constructor sets the default for all executions; `DevelopmentTask.agent_hint` overrides it per-call.

---

## Step Specifications

### Step 1 — Orient

- If `task.target_files` is non-empty: run `CodeGraphPrimitive` with `CGCOp.find_code` + `CGCOp.get_relationships` + `CGCOp.find_tests` on each target file (up to 3 files; extras ignored).
- If `task.target_files` is empty: skip orient, use `_empty_impact_report()`.
- If CGC is unavailable: use `_empty_impact_report()` with `cgc_available=False`.
- Orient result is placed in `result.impact_report`.

### Step 2 — Recall

- Call `AgentMemory.build_context_prefix(query=task.instruction)`.
- Returns a formatted string with directives + relevant memories, or `""` if Hindsight unavailable.
- Result is placed in `result.context_prefix` and injected as a prefix to the Write step system prompt.

### Step 3 — Write

- Build system prompt: `_system_prompt(agent_hint, context_prefix)` → role persona + memory prefix.
- Call `get_llm_client()` to get provider config.
- Make OpenAI-compatible chat completion (`httpx.AsyncClient` POST to `{base_url}/chat/completions`).
- User message: `task.instruction`.
- If the LLM call fails: **re-raise** — Write failure is not silently swallowed. The caller must handle it (e.g. via `RetryPrimitive` or `FallbackPrimitive`).
- Result placed in `result.response`.

### Step 4 — Validate

- If `impact_report.related_tests` is empty: skip, `validated=False`.
- Otherwise: run `CodeExecutionPrimitive` with the test files as a `pytest` invocation.
- If E2B is unavailable or errors: `validated=False` (not an error — logged as warning).
- `validated=True` only when E2B ran and all tests passed.

### Step 5 — Retain

- Call `AgentMemory.retain(content, async_=True)` with a structured summary:
  `f"[type: decision] {task.instruction[:80]} → {result.response[:120]}"`.
- If Hindsight unavailable: no-op, `memories_retained=0`.
- If retain succeeds: `memories_retained=1`.

---

## OTel Trace Structure

Each step emits a child span under the root `DevelopmentCycle` span:

```
development_cycle.execute              [root span, from InstrumentedPrimitive]
├─ development_cycle.orient            [cgc_available, target_files, risk]
├─ development_cycle.recall            [context_chars, hindsight_available]
├─ development_cycle.write             [provider, model, response_chars]
├─ development_cycle.validate          [validated, n_tests, sandbox_id?]
└─ development_cycle.retain            [memories_retained, hindsight_available]
```

Span attributes use plain names (no dotted prefix within span), consistent with `CodeGraphPrimitive` pattern.

---

## Edge Cases

| Scenario | Behaviour |
|---|---|
| `instruction` empty | Raise `ValueError("instruction must not be empty")` before any step runs |
| CGC unreachable | Steps 2–5 run normally; `impact_report.cgc_available=False` |
| Hindsight unreachable | Orient + Write run; `context_prefix=""`, `memories_retained=0` |
| E2B unreachable | Steps 1–3 + 5 run; `validated=False` |
| LLM call fails (network error) | Re-raise — not silently swallowed |
| LLM call returns empty response | Re-raise `ValueError("LLM returned empty response")` |
| `target_files` has > 3 entries | First 3 used; extras silently ignored |
| `agent_hint` not in known roles | Used as-is in system prompt; no error |
| All infrastructure down | Orient returns empty, Recall returns "", Write runs with bare instruction, Validate skipped, Retain no-op |

---

## System Prompt Templates

The Write step injects the agent role as a system prompt persona. The `agent_hint` maps to a short persona prefix prepended before the context prefix:

| `agent_hint` | Persona |
|---|---|
| `"developer"` | `"You are an expert Python developer. Write clean, testable code."` |
| `"qa"` | `"You are a QA engineer. Review code for correctness, edge cases, and test coverage."` |
| `"security"` | `"You are a security engineer. Review code for vulnerabilities and unsafe patterns."` |
| Any other value | `f"You are a {agent_hint}."` |

The full system prompt is: `{persona}\n\n{context_prefix}` (context_prefix omitted if empty).

---

## File Layout

| Action | Path | Purpose |
|---|---|---|
| Create | `ttadev/workflows/development_cycle.py` | `DevelopmentCycle`, `DevelopmentTask`, `DevelopmentResult` |
| Modify | `ttadev/workflows/__init__.py` | Export the three new names |
| Create | `tests/workflows/test_development_cycle.py` | Unit tests (all dependencies mocked) |

---

## Success Criteria

1. `DevelopmentCycle(bank_id="tta-dev")` constructs without errors
2. `execute(DevelopmentTask(instruction="..."), context)` returns `DevelopmentResult` — all five steps run
3. Each step degrades independently: CGC, Hindsight, or E2B unavailability does not abort the cycle
4. `instruction=""` raises `ValueError` before any step runs
5. Write step failure re-raises (not silently swallowed)
6. `result.validated=True` only when E2B ran tests and they passed
7. `result.memories_retained=1` when Hindsight is available; `0` when unavailable
8. OTel span `development_cycle.execute` is emitted; each of the 5 sub-spans is emitted
9. `DevelopmentCycle`, `DevelopmentTask`, `DevelopmentResult` importable from `ttadev.workflows`
10. 100% test coverage using mocked dependencies — no live CGC, Hindsight, E2B, or LLM calls in unit tests
11. `agent_hint` on constructor is overridden per-call by `DevelopmentTask.agent_hint`

---

## Out of Scope

- Quality gates / `confidence` scoring on LLM output (Phase 4)
- Multi-model fallback chains via `FallbackPrimitive` (Phase 4)
- `feature_dev_workflow` and `quick_fix_workflow` updates (Phase 4)
- `Artifact` extraction / structured output parsing from LLM response
- Streaming LLM responses
- Mental model refresh after structural code changes
- Pre-commit and session hooks (Phase 4)
- `AgentRegistry` integration (`agent_hint` is a string persona, not a registry lookup)
- Parallel orient across multiple target files (runs sequentially, first 3 only)

---

## Relationship to Prior Phases

```python
# Phase 2a — what does this code touch?
impact = await CodeGraphPrimitive().execute(CodeGraphQuery(...), context)

# Phase 2b — what do we know about this task?
prefix = await AgentMemory("tta-dev").build_context_prefix(query)

# Phase 3 — what should be built, and does it work? (this spec)
result = await DevelopmentCycle("tta-dev").execute(
    DevelopmentTask(instruction=query, target_files=[...]),
    context,
)
# All three phases run inside DevelopmentCycle._execute_impl
```
