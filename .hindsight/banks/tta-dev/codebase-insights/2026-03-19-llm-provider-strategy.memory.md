---
category: codebase-insights
date: 2026-03-19
component: llm-providers
severity: critical
tags: [llm-providers, openrouter, ollama, nemotron-bug, model-selection]
related_memories: []
---
# LLM Provider Strategy & Known Bugs

## Strategy: OpenRouter free models → Ollama CPU fallback

`get_llm_client()` exists in TWO places (both identical logic):
- `ttadev/workflows/llm_provider.py`
- `ttadev/integrations/llm_provider.py`

Selection order:
1. `LLM_FORCE_PROVIDER=ollama` → Ollama unconditionally
2. `OPENROUTER_API_KEY` set → OpenRouter with `HINDSIGHT_LLM_MODEL`
3. Else → Ollama fallback

## Env Vars

| Var | Purpose | Current Value |
|---|---|---|
| `OPENROUTER_API_KEY` | OpenRouter authentication | set in .env |
| `HINDSIGHT_LLM_MODEL` | Model for OpenRouter | `google/gemma-3n-e4b-it:free` |
| `LLM_FORCE_PROVIDER` | Force Ollama | unset |
| `OLLAMA_BASE_URL` | Ollama API | `http://localhost:11434/v1` |
| `OLLAMA_MODEL` | Ollama model | `qwen2.5:7b` |

## CRITICAL BUG: Nemotron is reasoning-only

`nvidia/nemotron-3-super-120b-a12b:free` returns `content: null` on OpenRouter.
It's a reasoning-only model — output is in `reasoning_content`, not `content`.
This caused Hindsight's LLM pipeline to fail with JSON parse errors.

**Affected files (stale defaults, not yet fixed in source):**
- `ttadev/workflows/llm_provider.py` line 18: `_DEFAULT_OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"`
- `docs/agent-guides/llm-provider-strategy.md` — lists nemotron as #1 preferred model

**Fix:** `.env` updated to `google/gemma-3n-e4b-it:free`. Source files need updating.

## Working Model Rotation (non-reasoning)

1. `google/gemma-3n-e4b-it:free` ← confirmed working
2. `mistralai/mistral-small-3.1-24b-instruct:free`
3. `openai/gpt-oss-20b:free`

## Ollama Homelab Specs

Hardware: i5-4670, 4 cores, ~17GB RAM, CPU-only (no GPU, no Docker GPU passthrough).
Best model: `qwen2.5:7b` (~4.5GB RAM).

## Hindsight Docker

- API: `http://localhost:8888`, Dashboard: `http://localhost:9999`
- Volume: `~/.local/share/hindsight`
- If container dies uncleanly → delete `~/.local/share/hindsight/instances/hindsight/data/postmaster.pid` before restart

---

**Created:** 2026-03-19
**Last Updated:** 2026-03-19
**Verified:** [x] Yes
