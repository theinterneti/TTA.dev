# LLM Provider Strategy

**Rule:** OpenRouter free models first, Ollama as fallback.

This applies to **all** LLM calls in TTA.dev — agent conductors, memory synthesis
(`reflect()`), integrations, and any AI-native apps built on top of TTA.dev.

---

## Why This Hierarchy

| Layer | Provider | Cost | Availability |
|---|---|---|---|
| Primary | OpenRouter `:free` models | $0 | High; upstream 429s possible |
| Fallback | Ollama (local) | $0 | Always available, CPU-only |

OpenRouter free models provide large capable models (up to 120B+) at no cost.
The catch is upstream provider rate limits — not OpenRouter account limits — that
cause intermittent 429s during peak hours. Ollama eliminates that risk entirely for
non-interactive/background tasks (memory synthesis, batch jobs) at the cost of speed.

---

## OpenRouter: What You Need to Know

- **Account type:** Non-free tier (`is_free_tier: false`) → **1,000 req/day**, 20 RPM
- **Limit source:** Upstream provider saturation, not account quota
- **Failed requests count** toward your daily quota — don't hammer on 429
- **No per-key isolation:** multiple keys share the same account limits

### Preferred Model Rotation (largest → most available)

Try in order; skip any that return 429 or 404:

```
1. google/gemma-3n-e4b-it:free              # confirmed working, returns non-null content
2. mistralai/mistral-small-3.1-24b-instruct:free  # fallback if gemma 429s
3. openai/gpt-oss-20b:free                  # second fallback
4. openrouter/free                          # auto-router, picks best available
```

> **Warning:** `nvidia/nemotron-3-super-120b-a12b:free` is a reasoning-only model —
> it returns `content: null` (output is in `reasoning_content`). Do NOT use it as a
> default for any pipeline that reads `content`.

Check live availability:
```bash
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)
free = [m for m in d['data'] if m.get('pricing',{}).get('prompt','1') == '0']
for m in sorted(free, key=lambda x: x.get('context_length', 0), reverse=True):
    print(f\"{m['context_length']:>8,}  {m['id']}\")
"
```

---

## Ollama: Fallback Setup

**Hardware (homelab):** i5-4670, 4 cores, ~17GB RAM, CPU-only.

### Install
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Recommended models (CPU-viable)

| Model | RAM | Quality | Use case |
|---|---|---|---|
| `qwen2.5:7b` | ~4.5GB | Best for CPU | Default fallback |
| `phi3.5:mini` | ~2.2GB | Fast, smaller | Low-memory situations |
| `qwen2.5:3b` | ~2GB | Fastest | High-throughput batch |

```bash
ollama pull qwen2.5:7b   # one-time download
ollama serve             # starts API at http://localhost:11434
```

### Ollama is OpenAI-compatible
```python
# Works identically to OpenAI SDK calls:
base_url = "http://localhost:11434/v1"
model    = "qwen2.5:7b"
api_key  = "ollama"  # any non-empty string  # pragma: allowlist secret
```

---

## Implementation Pattern for TTA.dev Code

```python
from ttadev.integrations.llm_provider import get_llm_client

# Automatically tries OpenRouter first, falls back to Ollama on 429/503/connection error
client, model = get_llm_client()
```

The `get_llm_client()` function (in `ttadev/integrations/llm_provider.py`) encapsulates
the provider selection logic so callers never hard-code a model or base URL.

---

## Hindsight Container

Hindsight uses this strategy for its `reflect()` synthesis calls. Start command:

```bash
docker run -d \
  --name hindsight \
  -p 8888:8888 -p 9999:9999 \
  --user $(id -u):$(id -g) \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENROUTER_API_KEY \
  -e HINDSIGHT_API_LLM_BASE_URL=https://openrouter.ai/api/v1 \
  -e HINDSIGHT_API_LLM_MODEL=$HINDSIGHT_LLM_MODEL \
  -v $HOME/.local/share/hindsight:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

If the model is rate-limited at startup (429 during `verify_connection`), restart with
the next model in the rotation list above. The container does not retry automatically.

To switch to Ollama:
```bash
docker rm -f hindsight && docker run -d --name hindsight \
  -p 8888:8888 -p 9999:9999 \
  --user $(id -u):$(id -g) \
  -e HINDSIGHT_API_LLM_API_KEY=ollama \
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434/v1 \
  -e HINDSIGHT_API_LLM_MODEL=qwen2.5:7b \
  --add-host=host.docker.internal:host-gateway \
  -v $HOME/.local/share/hindsight:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

---

## Env Vars (`.env`)

```bash
OPENROUTER_API_KEY=...
HINDSIGHT_LLM_MODEL=google/gemma-3n-e4b-it:free
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b
```
