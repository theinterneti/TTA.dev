# TTA.dev Examples

Working code examples demonstrating TTA.dev primitives and composition patterns.

## Available Examples

- [primitive-composition.md](primitive-composition.md) — Core composition patterns:
  sequential (`>>`), parallel (`|`), retry, fallback, timeout, caching, routing,
  and composed resilient workflows
- [custom_tool.md](custom_tool.md) — Dynamic tool creation
- [feature-dev-l0-workflow.md](feature-dev-l0-workflow.md) — The first L0-backed
  Phase 2 proof path for running `feature_dev` and inspecting it through
  `tta control`

---

## ModelRouterPrimitive — YAML Configuration Reference

These YAML files are ready-to-copy routing configurations for
[`ModelRouterPrimitive`](../../ttadev/primitives/llm/model_router.py).
Each file defines one or more named **modes**; each mode has an ordered list of
**tiers** that the router tries in sequence, falling through on HTTP 4xx/5xx.

| File | Strategy | Providers |
|------|----------|-----------|
| [groq_rotation.yaml](groq_rotation.yaml) | Multi-bucket Groq rotation — multiplies effective rate-limit budget | Groq only |
| [gemini_config.yaml](gemini_config.yaml) | Gemini-first with Groq fallback | Gemini → Groq |
| [multi_provider.yaml](multi_provider.yaml) | Free tiers first, paid tiers as safety net | Gemini, OpenRouter, Groq |

### Quick start

```python
from pathlib import Path
from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    ModelRouterRequest,
)
from ttadev.primitives.core import WorkflowContext

# Load any of the three configs (swap the filename as needed)
router = ModelRouterPrimitive.from_yaml(
    Path("docs/examples/groq_rotation.yaml"),
    tier_cooldown_seconds=30,   # skip a tier for N seconds after a 429
)

response = await router.execute(
    ModelRouterRequest(mode="chat", prompt="Explain async Python in one paragraph."),
    WorkflowContext(workflow_id="demo"),
)
print(response.content)
```

### YAML schema

```yaml
# Top-level key — required
modes:
  <mode_name>:                   # arbitrary name, referenced in ModelRouterRequest.mode
    description: "Human-readable description"
    tier1:                       # tiers are tried in numeric order (tier1 → tier2 → …)
      provider: groq             # groq | gemini | openrouter | ollama | together | auto
      model: llama-3.3-70b-versatile   # omit or set to "auto" for openrouter/auto providers
      params:
        temperature: 0.7         # forwarded verbatim to the provider API
        max_tokens: 2048
    tier2:
      provider: gemini
      model: models/gemini-2.5-flash   # ← always include the "models/" prefix for Gemini
      params:
        temperature: 0.7
        max_tokens: 2048
```

**Key schema notes:**

- `temperature`, `max_tokens`, and all other generation parameters go inside
  the `params:` block; they are forwarded verbatim to the provider's API.
- `tier_cooldown_seconds` is **not** parsed from YAML — pass it as a Python
  keyword argument to `from_yaml()` (see snippet above).
- `strip_thinking` defaults to `True` in `RouterTierConfig`; it is not yet
  configurable from YAML.

### Gemini — critical `models/` prefix

Gemini's OpenAI-compatible endpoint requires all model IDs to be prefixed with
`models/`.  Bare IDs (e.g. `gemini-2.5-flash`) return a **misleading HTTP 429**
instead of a descriptive 404, making the failure look like a rate-limit problem.

```yaml
# ✅ Correct
model: models/gemini-2.5-flash

# ❌ Returns 429 (not 404) — very confusing to debug
model: gemini-2.5-flash
```

`ModelRouterPrimitive` auto-prepends the prefix at runtime as a safety net
(Issue #283), but being explicit in config files avoids any ambiguity.

### Provider → env var reference

| Provider string | Auth env var | Notes |
|----------------|--------------|-------|
| `groq` | `GROQ_API_KEY` | Free tier: 14 400 RPM for 8B models |
| `gemini` | `GOOGLE_API_KEY` | Free tier: 15 RPM / 1 500 RPD |
| `openrouter` | `OPENROUTER_API_KEY` | Free models available; also proxies OpenAI, Anthropic, etc. |
| `ollama` | *(none)* | Local only; requires `model` to be set |
| `together` | `TOGETHER_API_KEY` | Requires explicit `model` |
| `auto` | `OPENROUTER_API_KEY` | FreeModelTracker picks the best free OpenRouter model |

### Further reading

- [`docs/models/`](../models/) — benchmark data (HumanEval, MMLU, speed)
- [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md) — full primitive inventory
- [`ttadev/primitives/llm/model_router.py`](../../ttadev/primitives/llm/model_router.py) — source with full docstring

---

## Contributing Examples

When contributing examples:

1. Create a new Markdown file with a descriptive name.
2. Include a clear description of what the example demonstrates.
3. Provide complete, working code snippets (copy-paste runnable).
4. Include all imports in every example.
5. Explain key concepts and patterns.
6. Update this README to include your example.


---
**Logseq:** [[TTA.dev/Docs/Examples/Readme]]
