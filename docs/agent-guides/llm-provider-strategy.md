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
