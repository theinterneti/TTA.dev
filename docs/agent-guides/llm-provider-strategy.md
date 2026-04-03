# LLM Provider Strategy

This document separates two related but different concerns:

1. `TTA.dev` application/provider-chain defaults for repo code.
2. The local **Hindsight runtime** used for memory, recall, reflect, and MCP.

They should not be treated as the same config surface.

---

## Current Recommendation

### Hindsight runtime

Use:

```text
provider = groq
model    = openai/gpt-oss-20b
```

Why:

- Live-tested with the current `GROQ_API_KEY`
- Healthy startup and provider verification
- Completed real Hindsight mental-model refreshes cleanly
- Avoids the Gemini preview/tool-calling compatibility issue seen below

Validated alternative:

```text
provider = gemini
model    = gemini-3.1-flash-lite-preview
```

This Gemini 3 model does work for plain calls and completed a refresh, but tool-calling produced `thought_signature` warnings and a much slower refresh path.

Last-resort fallback:

```text
provider = ollama
model    = llama3.2:3b
```

This works locally but is slow on the current homelab hardware.

---

## Hindsight Runtime: Global + Multi-Project Setup

For Copilot and other agent sessions, use:

- Global bank: `adam-global`
- Project/workspace bank: auto-derived from the git root

Examples:

```text
adam-global
project-tta-dev-9af638ec
workspace-adam-5b52748e
```

Rules:

- Put durable cross-project preferences and reusable workflow standards in `adam-global`
- Put repository-specific architecture, conventions, failures, and decisions in the derived project/workspace bank
- Prefer recalling `adam-global` first, then the current project/workspace bank

Do **not** collapse all work back into a single legacy `tta-dev` bank unless you are intentionally using older repo-local tooling that still expects it.

---

## Hindsight Runtime Commands

### Preferred Groq runtime

```bash
docker rm -f hindsight && docker run -d --name hindsight \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=groq \
  -e HINDSIGHT_API_LLM_API_KEY=$GROQ_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-20b \
  -e HINDSIGHT_API_LLM_GROQ_SERVICE_TIER=on_demand \
  -v $HOME/.local/share/hindsight:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

### Gemini alternative

```bash
docker rm -f hindsight && docker run -d --name hindsight \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=gemini \
  -e HINDSIGHT_API_LLM_API_KEY=$GOOGLE_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gemini-3.1-flash-lite-preview \
  -v $HOME/.local/share/hindsight:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

### Ollama fallback

```bash
docker rm -f hindsight && docker run -d --name hindsight \
  -p 8888:8888 -p 9999:9999 \
  --network hindsight-local \
  -e HINDSIGHT_API_LLM_PROVIDER=ollama \
  -e HINDSIGHT_API_LLM_BASE_URL=http://ollama:11434/v1 \
  -e HINDSIGHT_API_LLM_MODEL=llama3.2:3b \
  -e HINDSIGHT_API_RETAIN_MAX_COMPLETION_TOKENS=16000 \
  -v $HOME/.local/share/hindsight:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

---

## Expected Gemini Behavior

`gemini-3.1-flash-lite-preview` is viable for Hindsight because it clears the output-token bar Hindsight needs for retain/reflect pipelines.

Caveats:

- It is a **preview** model, so rate limits may be tighter than stable models
- Free-tier quotas are project-specific in Google AI Studio
- Large retain backfills or lots of concurrent background work can still hit `429`
- Hindsight tool-calling may hit Gemini-specific `thought_signature` errors on some reflect/tool iterations

For normal day-to-day personal use, it may be acceptable, but Groq is the safer default today.

---

## TTA.dev Repo Code: Existing Provider Chain

`ttadev.workflows.llm_provider` is still a separate, older repo-specific chain:

- Primary: OpenRouter via `OPENROUTER_API_KEY`
- Fallback: Ollama via `OLLAMA_*`

That code path currently reads:

- `OPENROUTER_API_KEY`
- `HINDSIGHT_LLM_MODEL`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

Important:

- `HINDSIGHT_LLM_MODEL` in `.env` is **not** the live Hindsight API runtime model setting
- It is only the current model selector for the repo's older OpenRouter-based helper chain

Do not set `HINDSIGHT_LLM_MODEL=gemini-3.1-flash-lite-preview` unless the repo provider-chain code is explicitly migrated away from OpenRouter.

---

## Practical Rule of Thumb

- For the running Hindsight server: prefer Groq `openai/gpt-oss-20b`
- If you want to stay on Google free tier: use Gemini `gemini-3.1-flash-lite-preview`
- Keep Ollama available only as a local emergency fallback
- Keep global and per-project Hindsight banks separate

---

## TTA.dev Application Routing

For application code inside TTA.dev, `ModelRouterPrimitive` is the recommended way to call LLMs. It provides 3-tier fallback (Ollama → Groq → Gemini) and now supports **task-aware model selection** via `TaskProfile`.

### Recommended: `AgentPrimitive.with_router()`

Instead of constructing agents with a hard-coded model, pass a `ModelRouterPrimitive` and let each agent's `default_task_profile` drive model selection:

```python
from ttadev.agents import DeveloperAgent
from ttadev.primitives.llm import ModelRouterPrimitive, RouterModeConfig, RouterTierConfig
import os

router = ModelRouterPrimitive(
    modes={
        "default": RouterModeConfig(
            tiers=[
                RouterTierConfig(provider="ollama"),
                RouterTierConfig(provider="groq"),
                RouterTierConfig(provider="gemini"),
            ]
        )
    },
    groq_api_key=os.environ["GROQ_API_KEY"],
    gemini_api_key=os.environ["GEMINI_API_KEY"],
)

# DeveloperAgent auto-uses TaskProfile(TASK_CODING, COMPLEXITY_COMPLEX)
agent = DeveloperAgent.with_router(router)
result = await agent.execute(task, ctx)
```

### How Task Profiles Map to Tiers

| Agent | Task type | Complexity | Preferred tier |
|-------|-----------|------------|----------------|
| DeveloperAgent | `TASK_CODING` | `COMPLEXITY_COMPLEX` | Groq / Gemini |
| SecurityAgent | `TASK_REASONING` | `COMPLEXITY_COMPLEX` | Groq / Gemini |
| PerformanceAgent | `TASK_REASONING` | `COMPLEXITY_MODERATE` | Groq |
| DevOpsAgent | `TASK_GENERAL` | `COMPLEXITY_MODERATE` | Groq |
| QAAgent | `TASK_GENERAL` | `COMPLEXITY_MODERATE` | Groq |
| GitAgent | `TASK_GENERAL` | `COMPLEXITY_SIMPLE` | Ollama |
| GitHubAgent | `TASK_GENERAL` | `COMPLEXITY_SIMPLE` | Ollama |

Simple tasks are served by the local Ollama tier (fast, free, private); complex coding and reasoning tasks automatically escalate to Groq or Gemini.

The scoring logic that ranks models against a `TaskProfile` lives in `ttadev/primitives/llm/task_selector.py`.

---

## Live Benchmark Data

The model catalog is backed by two live benchmark sources in addition to curated static data:

### Sources

| Source | Coverage | Key scores |
|--------|----------|-----------|
| **Artificial Analysis** | 457+ models (cloud + open) | `aa_intelligence`, `aa_coding`, `aa_math`, `aa_speed_tok_per_sec`, `aa_ttft_seconds`, `aa_price_per_1m_input`, `mmlu_pro`, `gpqa`, `livecodebench`, `aime` |
| **HF Open LLM Leaderboard 2** | Open-source models | `mmlu_pro`, `bbh`, `math_lvl5`, `gpqa`, `musr`, `ifeval`, `hf_avg` |

### Setup

Add your Artificial Analysis key to `.env`:

```bash
ARTIFICIAL_ANALYSIS_API_KEY=your-aa-key-here
```

HF Leaderboard 2 requires no auth key.

### Refreshing the Cache

```bash
uv run python -m ttadev.primitives.llm.benchmark_fetcher          # refresh if >24h old
uv run python -m ttadev.primitives.llm.benchmark_fetcher --force  # force refresh now
uv run python -m ttadev.primitives.llm.benchmark_fetcher --list-slugs  # audit slug mapping
```

Cache lives at `~/.cache/ttadev/benchmark_data.json` (24-hour TTL). The module
`model_benchmarks.py` loads this cache at import time — static curated entries take
priority over live data for the same `(model_id, benchmark)` pair.

### Capability Baseline Rule

Every model in `BENCHMARK_DATA` must have at least one capability baseline benchmark:
`mmlu`, `humaneval`, `mmlu_pro`, or `aa_intelligence`. Live-sourced models typically
provide `mmlu_pro` or `aa_intelligence`; curated static entries use `mmlu`/`humaneval`.
