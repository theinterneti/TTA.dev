# Functional Specification: AgentAutonomy

**Date:** 2026-03-21
**Phase:** 5 — Full agent autonomy
**Status:** Draft — awaiting approval
**Depends on:** `QualityGates` (Phase 4c, complete)
**Leads to:** Phase 6 — Multi-agent orchestration

---

## Overview

`AgentAutonomy` closes the loop between Phase 4c's quality gate (which can detect bad output) and truly autonomous operation (which acts on that detection without human intervention).

Three targeted additions to `DevelopmentCycle`:

1. **Prompt-reframe retry** — when all providers fail the quality gate, the cycle rewrites the instruction into a more structured form and retries automatically, rather than returning a low-confidence result to the caller.

2. **Per-call configuration** — callers can supply their own provider chain and quality threshold per task, instead of relying solely on global env vars. Essential for apps building on TTA.dev.

3. **Pre-built agent factories** — three convenience constructors (`coding_assistant`, `code_reviewer`, `qa_agent`) that return a properly configured `DevelopmentCycle` with sensible defaults for their role. A user building on TTA.dev can start with `coding_assistant()` and get good results immediately.

---

## Motivation

After Phase 4c, `DevelopmentCycle` can detect that a response is bad (low `confidence`) — but it still returns it. The caller has to decide what to do. For an autonomous agent, that is the wrong boundary: the cycle should self-heal before surfacing a result.

The integration design's layman's view is: *"Build me a data analysis tool." `DevelopmentCycle` runs. The user gets a proven artifact. They never see any of this.* That requires the cycle to resolve its own failures invisibly, not pass them to the caller.

Prompt reframing is the key missing mechanism: when a free model fails the quality gate, the problem is usually prompt mismatch (too vague, wrong format expectation, ambiguous role), not model capability. A structured reformulation — explicit output format, concrete scope, simplified role — dramatically improves success rate on the same model.

---

## User Journeys

### Journey 1 — Autonomous recovery from a weak first response

```python
cycle = DevelopmentCycle(bank_id="tta-dev")
result = await cycle.execute(
    DevelopmentTask(instruction="improve the retry primitive"),
    context,
)
# First attempt: Ollama returns vague filler, confidence=0.3
# → _write detects all providers failed quality gate
# → automatically reformulates instruction with explicit structure
# → second attempt: Ollama returns focused implementation, confidence=0.74
# result.confidence == 0.74
# result.retry_count == 1   ← caller can see a retry happened
# result.response   contains usable output
```

### Journey 2 — App builder overrides provider chain per task

```python
# An app building on TTA.dev wants to use a specific model for complex tasks
from ttadev.workflows.llm_provider import LLMClientConfig

fast_cfg = LLMClientConfig(
    base_url="http://localhost:11434/v1",
    model="qwen2.5:7b",
    api_key="ollama",  # pragma: allowlist secret
    provider="ollama",
)
precise_cfg = LLMClientConfig(
    base_url="https://openrouter.ai/api/v1",
    model="google/gemma-3n-e4b-it:free",
    api_key=os.environ["OPENROUTER_API_KEY"],
    provider="openrouter",
)

cycle = DevelopmentCycle(bank_id="myapp")
result = await cycle.execute(
    DevelopmentTask(
        instruction="generate a SQL migration for adding an index",
        provider_chain=[precise_cfg, fast_cfg],  # ← per-call override
        quality_threshold=0.6,                   # ← stricter threshold for this task
    ),
    context,
)
# Uses caller's chain instead of env-based chain
# Uses 0.6 threshold instead of global default
```

### Journey 3 — Zero-config app builder with pre-built factories

```python
from ttadev.workflows.agents import coding_assistant, code_reviewer

# No config needed — sensible defaults for each role
developer = coding_assistant()
reviewer  = code_reviewer()

dev_result = await developer.execute(
    DevelopmentTask(instruction="add input validation to the user endpoint"),
    WorkflowContext(),
)
review_result = await reviewer.execute(
    DevelopmentTask(instruction=dev_result["response"]),
    WorkflowContext(),
)
```

### Journey 4 — Autonomous retry transparent to caller

```python
# Caller does not know a retry happened — result looks identical
cycle = DevelopmentCycle()
result = await cycle.execute(DevelopmentTask(instruction="..."), context)
assert "confidence" in result
assert "provider"   in result
assert "retry_count" in result   # NEW — 0 if first attempt passed, 1+ if retry fired
```

### Journey 5 — Retry exhausted, best result returned

```python
# All providers fail quality gate, reframe also fails → return best seen
# Caller still gets a result — never blocked
# result.confidence is low, result.retry_count == 1
# Caller can inspect confidence and decide to escalate
if result["confidence"] < 0.5:
    await memory.retain(f"[type: failure] Low confidence on: {task['instruction']}")
```

### Journey 6 — Custom quality_threshold per task type

```python
# Documentation tasks are acceptable at lower confidence than code tasks
await cycle.execute(
    DevelopmentTask(
        instruction="update the README example section",
        quality_threshold=0.3,   # ← looser threshold for docs
    ),
    context,
)
# Code tasks
await cycle.execute(
    DevelopmentTask(
        instruction="implement the circuit breaker reset logic",
        quality_threshold=0.7,   # ← stricter threshold for code
    ),
    context,
)
```

---

## Components

### 1. `DevelopmentTask` — two new optional fields

```python
class DevelopmentTask(TypedDict, total=False):
    instruction: str             # Required
    target_files: list[str]      # Optional (existing)
    agent_hint: str              # Optional (existing)
    provider_chain: list[LLMClientConfig]  # NEW: per-call override; falls back to get_llm_provider_chain()
    quality_threshold: float     # NEW: per-call threshold; falls back to _DEFAULT_THRESHOLD from quality_gate.py
```

### 2. `DevelopmentResult` — one new field

```python
class DevelopmentResult(TypedDict):
    response: str
    validated: bool
    impact_report: ImpactReport
    memories_retained: int
    context_prefix: str
    confidence: float            # (existing)
    provider: str                # (existing)
    retry_count: int             # NEW: number of prompt-reframe retries before accepting result (0 = no retry)
```

### 3. Prompt-reframe retry in `DevelopmentCycle._write`

After all providers in the chain fail the quality gate (existing behaviour: returns best result with low confidence), the cycle now performs one additional attempt using a **reformulated prompt**.

The reframe strategy:
- Wrap the original instruction in an explicit structure template:
  ```
  Task: {original_instruction}

  Instructions:
  - Respond with a concrete, actionable answer
  - Be specific and direct
  - Do not refuse or hedge
  - Format: start with the implementation, then explain briefly
  ```
- Use the same provider chain (starting from the beginning)
- Apply the same quality gate
- If the reframe attempt passes the gate: accept it, set `retry_count=1`
- If the reframe attempt also fails: return the best result seen across ALL attempts (original + reframe), `retry_count=1`

Maximum one reframe per `_write` call (no infinite loops). The reframe is logged at `INFO` level.

### 4. `ttadev/workflows/agents.py` — pre-built factories

```python
def coding_assistant(
    bank_id: str = "tta-dev",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for code generation tasks."""

def code_reviewer(
    bank_id: str = "tta-dev",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for code review tasks (agent_hint='qa')."""

def qa_agent(
    bank_id: str = "tta-dev",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for test generation tasks (agent_hint='qa')."""
```

Each factory returns a `DevelopmentCycle` with:
- Role-appropriate `agent_hint` preset
- Same graceful-degradation behaviour as the base class
- No extra configuration required — works out of the box

These are thin constructors, not subclasses. They call `DevelopmentCycle(agent_hint=..., ...)` internally.

---

## Input/Output Contract

### `DevelopmentTask` new fields

| Field | Type | Default | Behaviour |
|-------|------|---------|-----------|
| `provider_chain` | `list[LLMClientConfig]` | `None` | If `None`: uses `get_llm_provider_chain()`. If provided: uses this chain for all attempts including reframe retry. Never empty (validated at call time). |
| `quality_threshold` | `float` | `None` | If `None`: uses `_DEFAULT_THRESHOLD` from `quality_gate`. If provided: must be in [0.0, 1.0]. Applied to both initial and reframe attempts. |

### `DevelopmentResult` new field

| Field | Type | Meaning |
|-------|------|---------|
| `retry_count` | `int` | `0` = first attempt passed gate or reframe not triggered. `1` = reframe was attempted (regardless of outcome). |

### OTel span additions (on `development_cycle.write`)

| Attribute | Type | Value |
|-----------|------|-------|
| `write.retry_count` | int | 0 or 1 |
| `write.reframe_triggered` | bool | True if reframe attempt was made |
| `write.final_confidence` | float | Confidence of the returned response |

---

## Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| `provider_chain=[]` | Raises `ValueError("provider_chain must not be empty")` before LLM call |
| `quality_threshold=1.5` | Raises `ValueError("quality_threshold must be in [0.0, 1.0]")` |
| Reframe passes gate on first provider | No second-provider attempt needed; `retry_count=1`, no extra latency from fallback |
| Reframe all providers fail gate | Return best of all attempts; no exception |
| Reframe provider raises exception | Exception logged, not re-raised; try next provider in reframe attempt |
| All providers raise in both original and reframe | Re-raise last exception (same as current behaviour) |
| `quality_threshold=0.0` | Every response passes; reframe never triggered |
| `DevelopmentTask` with no `provider_chain` | Uses `get_llm_provider_chain()` — existing behaviour preserved |

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `ttadev/workflows/development_cycle.py` | Add `retry_count` to result, per-call config to task, reframe logic to `_write` |
| Modify | `tests/workflows/test_development_cycle.py` | Tests for reframe retry, per-call chain, per-call threshold |
| Create | `ttadev/workflows/agents.py` | `coding_assistant()`, `code_reviewer()`, `qa_agent()` factories |
| Create | `tests/workflows/test_agents.py` | Tests for each factory |

---

## Out of Scope

- `AgentSpec` DSL (declarative agent definition) — deferred; factories cover the use case without a new language
- More than one reframe per `_write` call — single retry keeps latency bounded; multiple retries is Phase 6
- Prompt-reframe strategies beyond the single structured template (adaptive templates, per-model tuning) — Phase 6
- Paid model integration (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` in provider chain) — separate billing concern, not in Phase 5
- Multi-step autonomous agents that chain multiple `DevelopmentCycle` calls — Phase 6
- `provider_chain` as a constructor default on `DevelopmentCycle` (only per-call via `DevelopmentTask`) — avoids state management complexity

---

## Success Criteria

1. `DevelopmentTask` accepts `provider_chain` and `quality_threshold`; both are optional with working fallbacks
2. When all providers fail quality gate: `_write` automatically reformulates and retries once
3. Reframe attempt uses the same provider chain from the start
4. `result["retry_count"] == 0` when first attempt passes gate
5. `result["retry_count"] == 1` when reframe was triggered (regardless of outcome)
6. `DevelopmentResult` always has `retry_count` field
7. `coding_assistant()`, `code_reviewer()`, `qa_agent()` return correctly configured `DevelopmentCycle` instances
8. All three factories work with no arguments (zero-config)
9. `provider_chain=[]` raises `ValueError` before any LLM call
10. Existing 26 `test_development_cycle.py` tests still pass unmodified
11. 100% test coverage on all new code paths
12. `uvx pyright ttadev/workflows/` — 0 errors
