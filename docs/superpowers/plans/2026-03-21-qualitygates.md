# QualityGates — Technical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add quality gate confidence scoring and multi-model fallback to `DevelopmentCycle.Write`.
Spec: `docs/superpowers/specs/2026-03-21-qualitygates.md`

---

## Architecture Overview

```
ttadev/workflows/quality_gate.py           ← NEW: heuristic response scorer
ttadev/workflows/llm_provider.py           ← MODIFY: add get_llm_provider_chain()
ttadev/workflows/development_cycle.py      ← MODIFY: upgrade _write, add confidence/provider to DevelopmentResult
tests/workflows/test_quality_gate.py       ← NEW: 100% coverage for scorer
tests/workflows/test_development_cycle.py  ← MODIFY: add fallback + new fields tests
```

No new packages. No new primitives. No changes to imports outside `ttadev/workflows/`.

---

## Design Decisions

### Heuristic scorer — no second LLM call
`score_response()` is a pure function with penalty rules applied to the response string.
No I/O, no model calls, deterministic. This keeps Write step latency unchanged when the primary
provider succeeds.

### `_write` signature change — returns tuple, not bare string
Current: `async def _write(...) -> str`
New: `async def _write(...) -> tuple[str, float, str]` → `(response, confidence, provider)`

The tuple stays internal to `DevelopmentCycle`. `_execute_impl` unpacks it and populates
`DevelopmentResult`. Existing tests that mock `mock_http.post` are unaffected — they already
return a response string; the new fields are derived from it by the scorer.

### `DevelopmentResult` additions — required TypedDict fields
Two new required fields added:
```python
confidence: float   # 0.0–1.0 quality score
    provider: str       # provider identifier from the configured workflow/app chain
```
Existing tests that construct `DevelopmentCycle` via `_make_mocks()` will now get these fields
populated automatically by the updated `_write`. No test fixtures need changes — tests that
check `result["response"]` etc. are unaffected; they don't assert on key exhaustiveness.

### Empty-response guard removed from `_write`
Current `_write` raises `ValueError("LLM returned empty response")` for empty content.
With the quality gate, empty content scores 0.0 and triggers fallback to the next provider.
The raise is removed; fallback exhaustion raises only if ALL providers raised exceptions.

### `get_llm_provider_chain()` — additive, doesn't break `get_llm_client()`
`get_llm_client()` stays unchanged (called by existing code). `get_llm_provider_chain()` is
a new function that returns an ordered list. `DevelopmentCycle._write` switches to using the
chain. No callers of `get_llm_client()` outside `development_cycle.py` are affected.

### OTel span attributes
Existing `write.provider`, `write.model`, `write.response_chars` kept. Three new attributes:
- `write.confidence` — float score of accepted response
- `write.provider` — final provider used (moved from `cfg.provider` to accepted provider)
- `write.fallback_attempts` — count of providers tried before accepting

---

## Function Signatures

### `ttadev/workflows/quality_gate.py`

```python
_REFUSAL_PATTERNS: tuple[str, ...] = (
    "i cannot", "i'm unable to", "i am unable to",
    "i don't have access", "i do not have access",
    "i can't help", "i cannot help",
)

_AI_APOLOGY_PATTERNS: tuple[str, ...] = (
    "as an ai", "as a language model", "as an llm",
    "i'm just an ai", "i am just an ai",
)

def score_response(response: str) -> float:
    """Score an LLM response for usefulness. Returns 0.0–1.0 (clamped)."""

def quality_gate_passed(response: str, threshold: float = _DEFAULT_THRESHOLD) -> bool:
    """Return True if score_response(response) >= threshold."""

_DEFAULT_THRESHOLD: float = 0.5
```

`_DEFAULT_THRESHOLD` is overridden at import time from `QUALITY_GATE_THRESHOLD` env var
(parsed as float, clamped to [0.0, 1.0], silently defaults to 0.5 on parse error).

### `ttadev/workflows/llm_provider.py`

```python
def get_llm_provider_chain() -> list[LLMClientConfig]:
    """Return ordered list of providers: primary first, fallback last.

    - LLM_FORCE_PROVIDER=ollama  →  [ollama]
    - OPENROUTER_API_KEY set     →  [openrouter, ollama]
    - otherwise                  →  [ollama]
    """
```

### `ttadev/workflows/development_cycle.py` — `_write` signature

```python
async def _write(
    self, instruction: str, agent_hint: str, context_prefix: str
) -> tuple[str, float, str]:
    """Write step: try each provider in chain, return (response, confidence, provider).

    Tries providers in order from get_llm_provider_chain().
    Accepts first response with score >= threshold (from quality_gate module).
    If all providers fail the gate: returns (best_response, best_score, best_provider).
    If all providers raise exceptions: re-raises the last one.
    """
```

`DevelopmentResult` additions:

```python
class DevelopmentResult(TypedDict):
    response: str
    validated: bool
    impact_report: ImpactReport
    memories_retained: int
    context_prefix: str
    confidence: float    # NEW
    provider: str        # NEW
```

---

## `_write` Logic (pseudocode)

```python
chain = get_llm_provider_chain()
best_response, best_score, best_provider = "", 0.0, chain[0].provider
last_exc: Exception | None = None
attempts = 0

for cfg in chain:
    attempts += 1
    try:
        content = await _call_llm(cfg, system, instruction)
    except Exception as exc:
        last_exc = exc
        logger.warning("Write step: %s failed: %s", cfg.provider, exc)
        continue
    score = score_response(content)
    if score > best_score:
        best_response, best_score, best_provider = content, score, cfg.provider
    if quality_gate_passed(content):
        break  # accepted
    logger.warning("Write step: %s quality gate failed (score=%.2f), trying fallback", cfg.provider, score)

if not best_response:
    # All providers raised exceptions
    raise last_exc  # type: ignore[misc]

if best_score < threshold:
    logger.warning("Write step: all providers below threshold (best=%.2f)", best_score)

# set span attributes: confidence, provider, fallback_attempts
return best_response, best_score, best_provider
```

The existing `_call_llm` logic (httpx POST, raise_for_status, extract content) is extracted
into a private `_call_llm(cfg, system, instruction)` helper to avoid duplication in the loop.

---

## Observability

No new OTel spans. Existing `development_cycle.write` span gains three attributes:

| Attribute | Type | Value |
|-----------|------|-------|
| `write.confidence` | float | Quality score of accepted response |
| `write.provider` | str | Provider that produced accepted response |
| `write.fallback_attempts` | int | Number of providers tried (1 = no fallback needed) |

---

## Test Plan Summary

### `tests/workflows/test_quality_gate.py` (new, ~20 tests)

| Class | Tests |
|-------|-------|
| `TestScoreResponse` | empty → 0.0, whitespace → 0.0, short (<20) → ≤0.2, refusal → <0.5, apology → <0.5, long+clean → ≥0.5, very long → ≥0.6, score clamped to [0,1] |
| `TestQualityGatePassed` | passes above threshold, fails below, respects custom threshold |
| `TestThresholdFromEnv` | reads `QUALITY_GATE_THRESHOLD` env var, defaults on bad value |

### `tests/workflows/test_llm_provider.py` (new, ~5 tests)

| Test | Scenario |
|------|----------|
| `test_chain_openrouter_then_ollama` | OPENROUTER_API_KEY set → [openrouter, ollama] |
| `test_chain_ollama_only_no_key` | no key → [ollama] |
| `test_chain_force_ollama` | LLM_FORCE_PROVIDER=ollama → [ollama] |
| `test_chain_minimum_one_entry` | always returns non-empty list |

### `tests/workflows/test_development_cycle.py` (additions, ~6 new tests)

| Test | Scenario |
|------|----------|
| `test_result_includes_confidence_and_provider` | happy path: result has both new fields |
| `test_write_fallback_on_low_confidence` | primary scores low → fallback called, result.provider = fallback |
| `test_write_uses_best_when_all_fail_gate` | all providers below threshold → best returned, no raise |
| `test_write_reraises_when_all_providers_raise` | all raise → last exception re-raised |
| `test_write_no_fallback_when_primary_passes` | primary passes gate → http called once only |
| `test_write_provider_exception_then_fallback_succeeds` | primary raises, fallback succeeds → fallback used |

---

## External Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `re` | stdlib | Pattern matching for quality gate |
| `os` | stdlib | `QUALITY_GATE_THRESHOLD` env var |
| All others | already present | httpx, opentelemetry, etc. |

**No new packages.**

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------|
| Create | `ttadev/workflows/quality_gate.py` | Heuristic scorer |
| Create | `tests/workflows/test_quality_gate.py` | Scorer unit tests |
| Create | `tests/workflows/test_llm_provider.py` | Provider chain tests |
| Modify | `ttadev/workflows/llm_provider.py` | Add `get_llm_provider_chain()` |
| Modify | `ttadev/workflows/development_cycle.py` | Upgrade `_write`, `DevelopmentResult` |
| Modify | `tests/workflows/test_development_cycle.py` | New fallback + confidence tests |

---

## Task Breakdown

### Task 1 — `quality_gate.py` + tests (independent)

- [ ] Create `ttadev/workflows/quality_gate.py` with `score_response()`, `quality_gate_passed()`, `_DEFAULT_THRESHOLD`
- [ ] Create `tests/workflows/test_quality_gate.py` with all scorer tests
- [ ] Run `uv run pytest tests/workflows/test_quality_gate.py -v` — all pass
- [ ] Run `uvx pyright ttadev/workflows/quality_gate.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/quality_gate.py --fix` — clean
- [ ] Commit: `feat(quality-gates): add quality_gate.py heuristic response scorer`

### Task 2 — `get_llm_provider_chain()` + tests (independent)

- [ ] Add `get_llm_provider_chain()` to `ttadev/workflows/llm_provider.py`
- [ ] Create `tests/workflows/test_llm_provider.py` with provider chain tests
- [ ] Run `uv run pytest tests/workflows/test_llm_provider.py -v` — all pass
- [ ] Run `uvx pyright ttadev/workflows/llm_provider.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/llm_provider.py --fix` — clean
- [ ] Commit: `feat(quality-gates): add get_llm_provider_chain() to llm_provider`

### Task 3 — Upgrade `DevelopmentCycle._write` (depends on Tasks 1 + 2)

- [ ] Add `confidence: float` and `provider: str` to `DevelopmentResult`
- [ ] Extract `_call_llm(cfg, system, instruction)` helper from `_write`
- [ ] Rewrite `_write` to iterate provider chain, score each response, return tuple
- [ ] Remove the `ValueError("LLM returned empty response")` guard (replaced by quality gate)
- [ ] Update OTel span: add `write.confidence`, `write.provider`, `write.fallback_attempts`
- [ ] Update `_execute_impl` to unpack `(response, confidence, provider)` from `_write`
- [ ] Add 6 new tests to `tests/workflows/test_development_cycle.py`
- [ ] Run `uv run pytest tests/workflows/test_development_cycle.py -v` — all 26+ pass
- [ ] Run `uvx pyright ttadev/workflows/development_cycle.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/development_cycle.py --fix` — clean
- [ ] Commit: `feat(quality-gates): upgrade DevelopmentCycle.Write with quality gate + fallback`

---

## Dependencies

```
Task 1 ─── independent
Task 2 ─── independent
Task 3 ─── depends on Task 1 (score_response) + Task 2 (get_llm_provider_chain)
```

Tasks 1 and 2 can be executed in parallel. Task 3 must follow both.

---

## Quality Gate (before each commit)

```bash
uv run pytest tests/workflows/ -v                          # all pass
uvx pyright ttadev/workflows/                             # 0 errors
uv run ruff check ttadev/workflows/ --fix                 # clean
uv run pytest tests/workflows/ --cov=ttadev/workflows --cov-report=term-missing  # 100% new code
```
