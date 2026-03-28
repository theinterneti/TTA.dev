# AgentAutonomy — Technical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add prompt-reframe retry, per-call provider/threshold config, and pre-built agent factories to `DevelopmentCycle`.
Spec: `docs/superpowers/specs/2026-03-21-agentautonomy.md`

---

## Architecture Overview

```
ttadev/workflows/development_cycle.py    ← MODIFY: DevelopmentTask, DevelopmentResult, _write, _execute_impl
ttadev/workflows/agents.py               ← NEW: coding_assistant(), code_reviewer(), qa_agent() factories
tests/workflows/test_development_cycle.py ← MODIFY: per-call config + reframe retry tests
tests/workflows/test_agents.py           ← NEW: factory unit tests
```

No new packages. No new primitives. All changes inside `ttadev/workflows/`.

---

## Design Decisions

### `_write` returns a 4-tuple, not 3-tuple
Current: `-> tuple[str, float, str]` → `(response, confidence, provider)`
New: `-> tuple[str, float, str, int]` → `(response, confidence, provider, retry_count)`

`retry_count` is 0 when first attempt passed gate, 1 when reframe was triggered (regardless of reframe outcome). Returning it from `_write` keeps all Write-step state in one place; `_execute_impl` just unpacks.

### `_reframe_instruction` is a module-level helper, not a method
Pure function — takes `instruction: str`, returns a structured string. No `self` reference. Easy to test in isolation. Located just below `_build_system_prompt`.

### Per-call config validated in `_execute_impl`, not in `_write`
Validation (empty chain, threshold range) happens before entering the span, at the top of `_execute_impl`. `_write` receives already-validated values. This keeps `_write` focused on the loop logic.

### `_write` signature — keyword args for new params
```python
async def _write(
    self,
    instruction: str,
    agent_hint: str,
    context_prefix: str,
    *,
    chain: list[LLMClientConfig] | None = None,
    threshold: float | None = None,
) -> tuple[str, float, str, int]:
```
`chain` and `threshold` are keyword-only (`*`). `None` means "use defaults". Inside `_write`:
- `chain = chain or get_llm_provider_chain()`
- `threshold = threshold if threshold is not None else _DEFAULT_THRESHOLD`

### Reframe: one pass of the full chain
After original pass fails all-gate: call `_reframe_instruction(instruction)` → run full chain again with reframed instruction. Same threshold. Best response from ALL passes (original + reframe) is returned. `retry_count = 1` once reframe is triggered.

### Factory functions: thin constructors only
`coding_assistant()` etc. call `DevelopmentCycle(agent_hint=..., ...)` directly. No subclassing. No extra state. Tests verify the `agent_hint` and other constructor args on the returned instance.

---

## Function Signatures

### `DevelopmentTask` (updated)

```python
class DevelopmentTask(TypedDict, total=False):
    instruction: str                       # Required
    target_files: list[str]                # Optional (existing)
    agent_hint: str                        # Optional (existing)
    provider_chain: list[LLMClientConfig]  # NEW: per-call override
    quality_threshold: float               # NEW: per-call threshold override
```

### `DevelopmentResult` (updated)

```python
class DevelopmentResult(TypedDict):
    response: str
    validated: bool
    impact_report: ImpactReport
    memories_retained: int
    context_prefix: str
    confidence: float
    provider: str
    retry_count: int    # NEW: 0 = no retry, 1 = reframe attempted
```

### `_reframe_instruction` (new module-level helper)

```python
_REFRAME_TEMPLATE = (
    "Task: {instruction}\n\n"
    "Instructions:\n"
    "- Respond with a concrete, actionable answer\n"
    "- Be specific and direct\n"
    "- Do not refuse or hedge\n"
    "- Format: start with the implementation, then explain briefly"
)

def _reframe_instruction(instruction: str) -> str:
    """Wrap instruction in explicit structure to improve weak-model compliance."""
    return _REFRAME_TEMPLATE.format(instruction=instruction)
```

### `_write` (updated signature)

```python
async def _write(
    self,
    instruction: str,
    agent_hint: str,
    context_prefix: str,
    *,
    chain: list[LLMClientConfig] | None = None,
    threshold: float | None = None,
) -> tuple[str, float, str, int]:
    """Step 3 — Write: try each provider in chain, reframe once on all-gate-fail.

    Returns (response, confidence, provider, retry_count).
    retry_count = 0 if gate passed on first pass; 1 if reframe was triggered.
    """
```

### `_execute_impl` (updated)

```python
# New: extract per-call config
raw_chain = task.get("provider_chain")
if raw_chain is not None and len(raw_chain) == 0:
    raise ValueError("provider_chain must not be empty")
raw_threshold = task.get("quality_threshold")
if raw_threshold is not None and not (0.0 <= raw_threshold <= 1.0):
    raise ValueError("quality_threshold must be in [0.0, 1.0]")

# Step 3 — Write (updated call)
response, confidence, provider, retry_count = await self._write(
    instruction, agent_hint, context_prefix,
    chain=raw_chain,
    threshold=raw_threshold,
)

# Return (updated)
return DevelopmentResult(
    ...,
    confidence=confidence,
    provider=provider,
    retry_count=retry_count,    # NEW
)
```

### `ttadev/workflows/agents.py` (new file)

```python
def coding_assistant(
    bank_id: str = "project-tta.dev-9af638ec",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for code generation (agent_hint='developer')."""
    return DevelopmentCycle(bank_id=bank_id, base_url=base_url, agent_hint="developer", timeout=timeout)

def code_reviewer(
    bank_id: str = "project-tta.dev-9af638ec",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for code review (agent_hint='qa')."""
    return DevelopmentCycle(bank_id=bank_id, base_url=base_url, agent_hint="qa", timeout=timeout)

def qa_agent(
    bank_id: str = "project-tta.dev-9af638ec",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for test generation (agent_hint='qa')."""
    return DevelopmentCycle(bank_id=bank_id, base_url=base_url, agent_hint="qa", timeout=timeout)
```

---

## Reframe Retry Logic (pseudocode inside `_write`)

```python
effective_chain = chain or get_llm_provider_chain()
effective_threshold = threshold if threshold is not None else _DEFAULT_THRESHOLD

# Pass 1 — original instruction
best_response, best_score, best_provider, last_exc = await _run_chain_pass(
    effective_chain, system, instruction, effective_threshold
)

retry_count = 0

# Reframe if pass 1 failed quality gate
if best_response and not quality_gate_passed(best_response, effective_threshold):
    logger.info("DevelopmentCycle write: reframing instruction for retry")
    reframed = _reframe_instruction(instruction)
    retry_response, retry_score, retry_provider, retry_exc = await _run_chain_pass(
        effective_chain, system, reframed, effective_threshold
    )
    retry_count = 1
    # Keep best across both passes
    if retry_score > best_score:
        best_response, best_score, best_provider = retry_response, retry_score, retry_provider
    elif not best_response and retry_response:
        best_response, best_score, best_provider = retry_response, retry_score, retry_provider

if not best_response:
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("LLM provider chain returned no response")

# span attributes: write.retry_count, write.reframe_triggered, write.final_confidence
return best_response, best_score, best_provider, retry_count
```

`_run_chain_pass` is an internal helper that encapsulates the `for cfg in chain:` loop (currently inline in `_write`). Extracting it avoids duplicating the loop for reframe.

---

## OTel Span Additions (on `development_cycle.write`)

| Attribute | Type | Value |
|-----------|------|-------|
| `write.retry_count` | int | 0 or 1 |
| `write.reframe_triggered` | bool | `True` if reframe pass was attempted |
| `write.final_confidence` | float | Confidence of the returned response |
| (existing) `write.confidence` | float | Kept for backwards compat |
| (existing) `write.provider` | str | Kept |
| (existing) `write.fallback_attempts` | int | Count from pass 1 only |

---

## Test Plan Summary

### `test_development_cycle.py` additions (~10 new tests in two new classes)

**`TestDevelopmentCyclePerCallConfig`**

| Test | Scenario |
|------|----------|
| `test_per_call_chain_overrides_env_chain` | `provider_chain` provided → that chain used, not `get_llm_provider_chain()` |
| `test_per_call_threshold_overrides_default` | `quality_threshold=0.0` → no reframe ever triggered |
| `test_empty_provider_chain_raises` | `provider_chain=[]` → `ValueError` before LLM call |
| `test_invalid_threshold_high_raises` | `quality_threshold=1.5` → `ValueError` |
| `test_invalid_threshold_low_raises` | `quality_threshold=-0.1` → `ValueError` |
| `test_retry_count_zero_on_first_pass` | Good primary response → `result["retry_count"] == 0` |

**`TestDevelopmentCycleReframe`**

| Test | Scenario |
|------|----------|
| `test_reframe_triggered_when_all_fail_gate` | All providers return refusal → reframe attempted, `retry_count == 1` |
| `test_reframe_passes_gate_uses_reframe_response` | Reframe response passes gate → `result["response"]` is reframe result |
| `test_reframe_also_fails_returns_best_of_all` | Reframe also fails gate → best response across all passes returned, no exception |
| `test_no_reframe_when_primary_passes` | Primary passes gate → `retry_count == 0`, http called once per provider |

### `tests/workflows/test_agents.py` (new, ~8 tests)

| Test | Scenario |
|------|----------|
| `test_coding_assistant_returns_development_cycle` | Returns `DevelopmentCycle` instance |
| `test_coding_assistant_agent_hint_is_developer` | `._agent_hint == "developer"` |
| `test_coding_assistant_zero_config` | `coding_assistant()` works with no args |
| `test_code_reviewer_returns_development_cycle` | Returns `DevelopmentCycle` instance |
| `test_code_reviewer_agent_hint_is_qa` | `._agent_hint == "qa"` |
| `test_qa_agent_returns_development_cycle` | Returns `DevelopmentCycle` instance |
| `test_qa_agent_agent_hint_is_qa` | `._agent_hint == "qa"` |
| `test_factories_accept_bank_id` | `coding_assistant(bank_id="myapp")._bank_id == "myapp"` |

### `test_reframe_instruction` (in a standalone class or module)

| Test | Scenario |
|------|----------|
| `test_contains_original_instruction` | Reframed output contains original instruction |
| `test_contains_structure_markers` | Contains "Task:", "Instructions:", "Format:" |
| `test_different_from_original` | Reframed != original |

---

## External Dependencies

None. All changes use existing imports.

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `ttadev/workflows/development_cycle.py` | Per-call config, reframe retry, retry_count |
| Create | `ttadev/workflows/agents.py` | Three factory functions |
| Modify | `tests/workflows/test_development_cycle.py` | ~10 new tests |
| Create | `tests/workflows/test_agents.py` | ~8 factory tests |

---

## Task Breakdown

### Task 1 — Per-call config + `retry_count` field (independent)

- [ ] Add `provider_chain` and `quality_threshold` to `DevelopmentTask`
- [ ] Add `retry_count: int` to `DevelopmentResult`
- [ ] Add validation in `_execute_impl` (empty chain, threshold range)
- [ ] Update `_write` signature to accept `chain` and `threshold` keyword args
- [ ] Update `_write` to use `effective_chain` and `effective_threshold` derived from args + defaults
- [ ] Change `_write` return type to `tuple[str, float, str, int]` (add `retry_count=0`)
- [ ] Update `_execute_impl` to pass per-call config to `_write` and unpack 4-tuple
- [ ] Add `retry_count` to `DevelopmentResult(...)` constructor call
- [ ] Add `TestDevelopmentCyclePerCallConfig` with 6 tests
- [ ] Run `uv run pytest tests/workflows/test_development_cycle.py -v` — all 36+ pass
- [ ] Run `uvx pyright ttadev/workflows/development_cycle.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/development_cycle.py --fix` — clean
- [ ] Commit: `feat(agent-autonomy): add per-call provider_chain + quality_threshold to DevelopmentTask`

### Task 2 — Prompt-reframe retry (depends on Task 1)

- [ ] Add `_REFRAME_TEMPLATE` constant (module-level)
- [ ] Add `_reframe_instruction(instruction: str) -> str` helper (module-level, below `_build_system_prompt`)
- [ ] Extract `_run_chain_pass` private method from existing `_write` loop
- [ ] Extend `_write`: after all-gate-fail, call `_reframe_instruction`, run `_run_chain_pass` again, set `retry_count=1`
- [ ] Add OTel span attributes: `write.retry_count`, `write.reframe_triggered`, `write.final_confidence`
- [ ] Add `TestDevelopmentCycleReframe` with 4 tests + 3 `_reframe_instruction` tests
- [ ] Run `uv run pytest tests/workflows/test_development_cycle.py -v` — all 43+ pass
- [ ] Run `uvx pyright ttadev/workflows/development_cycle.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/development_cycle.py --fix` — clean
- [ ] Commit: `feat(agent-autonomy): add prompt-reframe retry to DevelopmentCycle._write`

### Task 3 — Agent factories (independent)

- [ ] Create `ttadev/workflows/agents.py` with `coding_assistant()`, `code_reviewer()`, `qa_agent()`
- [ ] Create `tests/workflows/test_agents.py` with 8 tests
- [ ] Run `uv run pytest tests/workflows/test_agents.py -v` — all pass
- [ ] Run `uvx pyright ttadev/workflows/agents.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/agents.py --fix` — clean
- [ ] Commit: `feat(agent-autonomy): add coding_assistant, code_reviewer, qa_agent factories`

---

## Dependencies

```
Task 1 ─── independent
Task 2 ─── depends on Task 1 (_write signature must be updated first)
Task 3 ─── independent
```

Tasks 1 and 3 can be executed in parallel. Task 2 must follow Task 1.

---

## Quality Gate (before each commit)

```bash
uv run pytest tests/workflows/ -v                              # all pass
uvx pyright ttadev/workflows/                                  # 0 errors
uv run ruff check ttadev/workflows/ --fix                      # clean
uv run pytest tests/workflows/ --cov=ttadev/workflows --cov-report=term-missing
```
