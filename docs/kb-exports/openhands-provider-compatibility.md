# OpenHands SDK — Free LLM Provider Compatibility

Quick reference for which free-tier LLM providers work with the **OpenHands SDK** and which do not.

> Last updated: 2026-04-04. Confirmed-working models verified empirically.
> Model discovery now uses **native Google API** (not the OpenAI-compat shim) — see [Model Discovery](#model-discovery) section.

## Compatibility Matrix

| Provider / Model | Status | Notes |
|---|---|---|
| `openrouter/qwen/qwen3.6-plus:free` | ✅ WORKS | Function calling + array-content messages fully supported |
| `openrouter/openai/gpt-oss-20b:free` | ✅ WORKS | Function calling + array-content messages fully supported |
| Google Gemini Flash (free tier) | ⚠️ RATE-LIMITED | Works but hits free quota; use `best_google_free_model()` for auto-skip |
| Gemma (any version, any provider) | ❌ FAILS | Function calling not enabled |
| Groq (free tier) | ❌ FAILS | 12 K TPM rate limit; OpenHands needs ~36 K tokens per request |
| `openrouter/openai/gpt-oss-120b:free` | ❌ FAILS | Provider rejects array-content messages with HTTP 422 |
| `openrouter/meta-llama/llama-3.3-70b-instruct:free` | ❌ FAILS | Rate limited (provider 429) |
| Ollama Gemma3 | ❌ FAILS | Error: "does not support thinking" — SDK sends `reasoning_effort=high` |

## Failure Reason Details

### Gemma (any version, any provider — incl. Google AI Studio)

Gemma models do not have function calling enabled by default. OpenHands relies on tool-use /
function-calling to execute tasks, so any Gemma model will fail at runtime with a
function-calling error. This applies to:

- `openrouter/google/gemma-3-27b-it:free` — "No endpoints found that support tool use"
- `gemini/gemma-3-27b-it` (Google AI Studio) — "Function calling is not enabled for
  models/gemma-3-*-it"
- `ollama/gemma3:4b` — see Ollama section below

### Groq (free tier)

Groq's free tier enforces a **12 K tokens-per-minute (TPM)** rate limit. A single OpenHands
agent request typically consumes **~36 K tokens** (prompt + response), which immediately
exceeds the quota and triggers rate-limit errors. This is a structural incompatibility — not
fixable by retrying or using a different Groq model on the free tier.

### `openrouter/openai/gpt-oss-120b:free`

This particular OpenRouter free-tier route does not accept **array-content** message formats
(e.g., `content` as a list of `{"type": "text", ...}` blocks). The OpenHands SDK sends
messages in this format by default, and the provider responds with an **HTTP 422 Unprocessable
Entity** error.

### Ollama Gemma3 (local)

The OpenHands SDK sets `reasoning_effort=high` on outgoing requests. Ollama's Gemma3
integration does not support the thinking / reasoning parameter and returns an error stating it
**"does not support thinking"**. Other Ollama models that support function calling may work if
they also tolerate the `reasoning_effort` field being ignored.

## Using in TTA.dev

```python
from ttadev.primitives.integrations import (
    OPENHANDS_COMPATIBLE_FREE_MODELS,
    OpenHandsPrimitive,
)
from ttadev.primitives.core.base import WorkflowContext

# Always start with a known-good free model
prim = OpenHandsPrimitive(model=OPENHANDS_COMPATIBLE_FREE_MODELS[0])
ctx = WorkflowContext(workflow_id="my-task")
result = await prim.execute("your task here", ctx)
```

The `OPENHANDS_COMPATIBLE_FREE_MODELS` list in
`ttadev/primitives/integrations/openhands_primitive.py` is the canonical source of truth.

## Model Discovery

`ProviderModelDiscovery` in `ttadev/primitives/llm/model_discovery.py` provides live model list
discovery with caching and exhaustion tracking.

### Native Google API (`for_google()`)

For Gemini models, prefer `ProviderModelDiscovery.for_google()` and the `best_google_free_model()`
helper over the generic `for_provider()`. The native endpoint:

- Hits `/v1beta/models?key=<API_KEY>` directly (not the OpenAI-compat shim)
- Returns the **full** authoritative model list (the OpenAI-compat shim only exposes a subset)
- Uses `?key=` query-param auth — matching how LiteLLM routes `gemini/` prefixed model IDs

```python
from ttadev.primitives.llm.model_discovery import (
    ProviderModelDiscovery,
    best_google_free_model,
    default_discovery,
)
import os

# Recommended Google alias — always tracks the latest best lite model
best = await best_google_free_model(api_key=os.environ["GOOGLE_API_KEY"])
# → "gemini/gemini-flash-lite-latest"

# Full list, best-first (sorted by preference patterns defined in model_discovery.py)
models = await default_discovery.for_google(api_key=os.environ["GOOGLE_API_KEY"])
# → ['gemini/gemini-flash-lite-latest', 'gemini/gemini-3.1-flash-lite-preview', ...]

# When a model hits quota, mark it exhausted — best_google_free_model() skips it
default_discovery.mark_exhausted("gemini/gemini-2.5-flash", ttl_seconds=86400)
```

### Preference Pattern Ordering

Models returned by `for_google()` are sorted by patterns defined in `_GEMINI_PREFER_PATTERNS`
(in `model_discovery.py`). Current order (highest priority first):

1. `flash-lite-latest` — alias, always tracks best lite model ⭐ recommended
2. `flash-latest` — alias, tracks best flash
3. `3.1-flash-lite` — latest-generation lite (good quota)
4. `3-flash` — gen 3 flash
5. `2.0-flash-lite` — gen 2 lite (known free tier)
6. `2.5-flash-lite` — gen 2.5 lite
7. `2.0-flash` — gen 2 flash
8. `2.5-flash` — gen 2.5 flash
9. `2.5-pro` — gen 2.5 pro (quota-heavy)

## Recommendation

**OpenRouter (for coding tasks / OpenHands):**
- **`openrouter/qwen/qwen3.6-plus:free`** — best overall compatibility (default in `OpenHandsPrimitive`)
- **`openrouter/openai/gpt-oss-20b:free`** — solid fallback

Use `rank_models_for_role()` from `free_model_tracker.py` to automatically pick the
highest-ranked AA-benchmark model that is confirmed OpenHands-compatible.

**Google Gemini (for general LLM tasks):**
- **`gemini/gemini-flash-lite-latest`** — recommended alias (always tracks latest best)
- Use `best_google_free_model()` to automatically skip exhausted models

For future OpenRouter candidates, a model must support **both**:
1. Function calling / tool use
2. Array-content message format (`content` as a list, not a plain string)

See **[`examples/openhands_with_free_models.py`](../../examples/openhands_with_free_models.py)**
for a full runnable demo of the Langfuse + OpenHands + Artificial Analysis integration.
