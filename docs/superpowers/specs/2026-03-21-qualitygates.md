# Functional Specification: QualityGates

**Date:** 2026-03-21
**Phase:** 4c — Quality Gates + Multi-model Fallback
**Status:** Approved — 2026-03-25
**Depends on:** `DevelopmentCycle` (Phase 3, complete), `CIMergeGate` (Phase 4b, complete)
**Leads to:** Phase 5 — Full agent autonomy

---

## Overview

`QualityGates` adds two complementary capabilities to the `DevelopmentCycle.Write` step:

1. **Quality Gate** — a heuristic scorer that evaluates LLM responses for usefulness before accepting them. Assigns a `confidence` score (0.0–1.0) and a boolean `quality_gate_passed` flag.

2. **Multi-model Fallback** — if the primary provider produces a low-confidence response, the Write step automatically retries with the next provider in the configured workflow/app provider chain (for example the historical OpenRouter → Ollama chain used by `ttadev/workflows/llm_provider.py`). The best response seen is returned.

Together these ensure that `DevelopmentCycle` never silently returns a refusal or empty output when another provider might do better — without adding latency when the primary provider succeeds.

---

## Motivation

`DevelopmentCycle` currently calls one LLM provider (selected by `get_llm_client()`). This is about the workflow/app provider chain, not the separate live Hindsight runtime. Lower-cost or weaker models can return:
- Refusals ("I cannot help with that")
- Hallucinated apologies ("As an AI language model…")
- Empty or near-empty completions
- Repetitive filler with no substantive content

These failures are currently invisible — `result.response` contains useless text, `result.validated` may still be `True` (tests pass on unrelated code), and no signal exists to retry.

Quality Gates close this gap by:
1. Scoring every Write response before accepting it
2. Automatically retrying with the next provider if the score is below threshold
3. Surfacing `confidence` and `provider` in `DevelopmentResult` for observability

---

## User Journeys

### Journey 1 — Primary provider responds well

```python
cycle = DevelopmentCycle(bank_id="project-tta.dev-9af638ec")
result = await cycle.execute(
    DevelopmentTask(instruction="Add a timeout parameter to RetryPrimitive"),
    context,
)
# OpenRouter free model responds with clear implementation
# result.confidence == 0.82
# result.provider   == "openrouter"
# result.response   contains actual Python code
```

### Journey 2 — Primary provider returns a refusal, fallback succeeds

```python
# Primary workflow provider refuses: "I cannot modify production code."
# → Quality gate scores it 0.1 (refusal pattern detected)
# → Write step retries with the configured fallback provider
# → fallback returns useful code
# result.confidence == 0.71
# result.provider   == "ollama"
# result.response   contains actual Python code
```

### Journey 3 — All providers return low-confidence output

```python
# Both providers return borderline responses
# Best response has confidence 0.38 (below threshold 0.5)
# → Write step uses best available, logs warning
# result.confidence == 0.38
# result.provider   == "openrouter"  # whichever scored higher
# result.response   contains the best available output (not silently dropped)
# ← caller sees low confidence and can decide to retry or escalate
```

### Journey 4 — All providers raise exceptions

```python
# Primary provider times out, fallback connection refused
# → Write step re-raises the last exception (existing behaviour)
# Same as current DevelopmentCycle behaviour — no regression
```

### Journey 5 — Only one provider configured (Ollama only)

```python
# OPENROUTER_API_KEY not set → chain is [Ollama]
# Single provider: quality gate scores response, no fallback possible
# result.confidence = score of Ollama response
# result.provider   = "ollama"
# No retries attempted (chain exhausted after first attempt)
```

### Journey 6 — Observing confidence in practice

```python
# Low-confidence result triggers caller to retain a memory and escalate
result = await cycle.execute(task, context)
if result["confidence"] < 0.5:
    await memory.retain(f"[type: failure] Low-confidence Write on: {task['instruction']}")
    raise ValueError("Write step produced low-confidence output — manual review needed")
```

---

## Components

### 1. `ttadev/workflows/quality_gate.py` — Heuristic response scorer

A standalone module with no external dependencies. Scores an LLM response string using heuristic rules.

```python
def score_response(response: str) -> float:
    """Score an LLM response for usefulness. Returns 0.0–1.0."""

def quality_gate_passed(response: str, threshold: float = 0.5) -> bool:
    """Return True if score >= threshold."""
```

**Scoring rules** (applied in order, additive penalties from 1.0):

| Rule | Penalty | Rationale |
|------|---------|-----------|
| Empty response | −1.0 (score = 0.0) | Nothing to use |
| Length < 20 chars | −0.8 | Almost certainly useless |
| Length < 80 chars | −0.3 | Probably incomplete |
| Refusal pattern match | −0.6 | "I cannot", "I'm unable to", "I don't have access" |
| AI apology pattern | −0.4 | "As an AI", "As a language model", "I'm just an AI" |
| No alphabetic content | −0.5 | Junk output |
| Length > 200 chars | +0.1 bonus | Substantive length |
| Length > 500 chars | +0.1 bonus | Rich response |

Score is clamped to [0.0, 1.0]. Penalties stack.

**Threshold:** default `0.5`. Configurable via `QUALITY_GATE_THRESHOLD` env var (float, 0.0–1.0).

### 2. `ttadev/workflows/llm_provider.py` — Provider chain

Add one new function alongside `get_llm_client()`:

```python
def get_llm_provider_chain() -> list[LLMClientConfig]:
    """Return ordered list of providers to try, from primary to fallback.

    - If LLM_FORCE_PROVIDER=ollama: [Ollama] only
    - If OPENROUTER_API_KEY set: [OpenRouter, Ollama]
    - Otherwise: [Ollama] only
    """
```

This replaces the single-provider `get_llm_client()` call inside `DevelopmentCycle._write`.

### 3. `ttadev/workflows/development_cycle.py` — Updated Write step

The `_write` method is upgraded to:

1. Call `get_llm_provider_chain()` to get the ordered provider list
2. For each provider in the chain:
   a. Make the LLM call (existing httpx logic, unchanged)
   b. Score the response with `score_response()`
   c. If `score >= threshold`: accept, stop iterating
   d. If `score < threshold`: log warning, continue to next provider
3. After exhausting the chain: return the best response seen (highest score), with its score and provider
4. If all providers raised exceptions: re-raise the last one (existing behaviour)

`DevelopmentResult` gains two new fields:

```python
class DevelopmentResult(TypedDict):
    response: str
    validated: bool
    impact_report: ImpactReport
    memories_retained: int
    context_prefix: str
    confidence: float   # NEW: quality gate score of the accepted response (0.0–1.0)
    provider: str       # NEW: provider that produced the accepted response
```

The Write step's OTel span gains two new attributes:
- `write.confidence` — score of accepted response
- `write.provider` — provider used
- `write.fallback_attempts` — number of providers tried before accepting

---

## Input/Output Contract

### `score_response(response: str) -> float`

- Input: raw LLM response string (may be empty)
- Output: float in [0.0, 1.0]
- No side effects, no I/O, deterministic

### `quality_gate_passed(response: str, threshold: float = 0.5) -> bool`

- Input: response string, optional threshold override
- Output: `score_response(response) >= threshold`

### `get_llm_provider_chain() -> list[LLMClientConfig]`

- Input: environment variables (`OPENROUTER_API_KEY`, `LLM_FORCE_PROVIDER`, `OLLAMA_*`)
- Output: ordered list of 1–2 `LLMClientConfig` objects
- First element is always the primary provider
- Never empty (at minimum returns `[ollama_config()]`)

### `DevelopmentResult` additions

| Field | Type | Meaning |
|-------|------|---------|
| `confidence` | `float` | Quality gate score of the accepted response (0.0–1.0) |
| `provider` | `str` | Provider that produced the accepted response (`"openrouter"` or `"ollama"`) |

---

## Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| Response is empty string | Score = 0.0, try next provider |
| Response contains only whitespace | Score = 0.0, try next provider |
| All providers score below threshold | Return best response, `confidence` = best score, log warning |
| All providers raise exceptions | Re-raise last exception (unchanged from current behaviour) |
| One provider raises, next succeeds | Use the successful one; exception is logged, not re-raised |
| `QUALITY_GATE_THRESHOLD=0.0` | Every non-raising response passes; first provider always wins |
| `QUALITY_GATE_THRESHOLD=1.0` | Only perfect responses pass; will almost always fall through to best-available |
| Only Ollama configured | Chain has one entry; no fallback attempted |
| `LLM_FORCE_PROVIDER=ollama` | Chain = [Ollama], OpenRouter not attempted even if key is set |

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------|
| Create | `ttadev/workflows/quality_gate.py` | Heuristic response scorer |
| Create | `tests/workflows/test_quality_gate.py` | Unit tests for scorer |
| Modify | `ttadev/workflows/llm_provider.py` | Add `get_llm_provider_chain()` |
| Modify | `tests/workflows/test_llm_provider.py` | Tests for `get_llm_provider_chain()` |
| Modify | `ttadev/workflows/development_cycle.py` | Upgrade `_write`, update `DevelopmentResult` |
| Modify | `tests/workflows/test_development_cycle.py` | Add tests for fallback + confidence fields |

---

## Out of Scope

- Second LLM call to evaluate output quality (too slow; heuristic is sufficient for Phase 4c)
- Adaptive/ML-based learning of which provider to try first (`AdaptiveFallbackPrimitive` is out of scope; deterministic chain is enough)
- Adding a third paid OpenRouter model to the chain (two providers are sufficient; adding a paid tier is a separate feature)
- Persisting per-provider confidence metrics to Hindsight (observability concern for a later phase)
- Quality gate on Recall or Retain steps (only the Write step produces LLM output that needs scoring)
- Configuring the fallback chain per-call (single global chain per env; per-call override is Phase 5)

---

## Success Criteria

1. `score_response("")` returns `0.0`
2. `score_response("I cannot help with that.")` returns `< 0.5`
3. `score_response("<200+ char Python implementation>")` returns `>= 0.5`
4. `quality_gate_passed("I'm just an AI and cannot write code")` returns `False`
5. `get_llm_provider_chain()` returns `[openrouter, ollama]` when `OPENROUTER_API_KEY` is set
6. `get_llm_provider_chain()` returns `[ollama]` when key is absent
7. `DevelopmentCycle` accepts a low-confidence primary response without raising, tries fallback, returns best result
8. `DevelopmentResult` always includes `confidence` and `provider` fields
9. When primary passes quality gate, no fallback call is made (no extra latency)
10. `tests/workflows/test_quality_gate.py` covers all scoring rules with 100% coverage
11. `uvx pyright ttadev/workflows/` — 0 errors after changes
