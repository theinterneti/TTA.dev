# LLM Provider Reference

Full table of common model strings for `LiteLLMPrimitive` and `LLMRequest.model`.

All strings follow the litellm convention: `"<provider>/<model-name>"`.

---

## Groq (Free tier, fast inference)

| Model string | Context | Notes |
|---|---|---|
| `groq/llama-3.1-8b-instant` | 128k | Fast, cheap — good for simple tasks |
| `groq/llama-3.3-70b-versatile` | 128k | Balanced quality + speed |
| `groq/llama-3.1-70b-versatile` | 128k | Slightly older version |
| `groq/mixtral-8x7b-32768` | 32k | MoE model, good reasoning |
| `groq/gemma2-9b-it` | 8k | Google Gemma 2, instruction-tuned |

**Env var:** `GROQ_API_KEY`
**Free tier:** Yes — generous rate limits at `console.groq.com`

---

## Anthropic

| Model string | Context | Notes |
|---|---|---|
| `anthropic/claude-3-5-haiku-20241022` | 200k | Fast, cheapest Claude |
| `anthropic/claude-3-5-sonnet-20241022` | 200k | Best balance quality/cost |
| `anthropic/claude-3-opus-20240229` | 200k | Most capable, most expensive |
| `anthropic/claude-3-haiku-20240307` | 200k | Previous gen haiku — good fallback |

**Env var:** `ANTHROPIC_API_KEY`

---

## OpenAI

| Model string | Context | Notes |
|---|---|---|
| `openai/gpt-4o-mini` | 128k | Fast, cheap GPT-4 class |
| `openai/gpt-4o` | 128k | Full GPT-4o |
| `openai/gpt-4-turbo` | 128k | GPT-4 Turbo |
| `openai/gpt-3.5-turbo` | 16k | Legacy — cheap |
| `openai/o1-mini` | 128k | Reasoning model |

**Env var:** `OPENAI_API_KEY`

---

## Google Gemini

| Model string | Context | Notes |
|---|---|---|
| `gemini/gemini-2.0-flash` | 1M | Fast, large context |
| `gemini/gemini-2.0-flash-lite` | 1M | Lighter/cheaper version |
| `gemini/gemini-1.5-pro` | 2M | Largest context window |
| `gemini/gemini-1.5-flash` | 1M | Balanced |

**Env var:** `GOOGLE_API_KEY`

---

## Ollama (Local — no key required)

Requires Ollama running at `localhost:11434`. Start with `ollama serve`.

| Model string | RAM needed | Notes |
|---|---|---|
| `ollama/llama3.2` | ~4 GB | Meta Llama 3.2 3B — very fast |
| `ollama/llama3.1` | ~8 GB | Llama 3.1 8B |
| `ollama/mistral` | ~4 GB | Mistral 7B — general purpose |
| `ollama/phi3` | ~2 GB | Microsoft Phi-3 — tiny, capable |
| `ollama/codellama` | ~4 GB | Code-specialised Llama |
| `ollama/qwen2.5-coder` | ~5 GB | Alibaba coding model |
| `ollama/deepseek-r1` | ~5 GB | Reasoning model |

**Pull a model:** `ollama pull llama3.2`
**Env var:** none — uses `http://localhost:11434`
**Custom host:** `LiteLLMPrimitive(api_base="http://myhost:11434")`

---

## OpenRouter (Aggregator — 200+ models)

| Model string | Notes |
|---|---|
| `openrouter/meta-llama/llama-3-70b-instruct` | Llama 70B via OpenRouter |
| `openrouter/anthropic/claude-3.5-sonnet` | Claude via OpenRouter |
| `openrouter/google/gemini-flash-1.5` | Gemini via OpenRouter |
| `openrouter/mistralai/mixtral-8x7b-instruct` | Mixtral via OpenRouter |

**Env var:** `OPENROUTER_API_KEY`
**Docs:** https://openrouter.ai/models

---

## xAI / Grok

| Model string | Notes |
|---|---|
| `xai/grok-beta` | xAI Grok (beta) |
| `xai/grok-vision-beta` | Vision-capable Grok |

**Env var:** `XAI_API_KEY`

---

## Together AI

| Model string | Notes |
|---|---|
| `together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` | Fast Llama 70B |
| `together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1` | Mixtral |

**Env var:** `TOGETHER_API_KEY`

---

## Recommended Stacks

### Fastest / Cheapest
```python
llm = make_resilient_llm(
    litellm_fallbacks=["groq/llama-3.1-8b-instant", "ollama/llama3.2"],
)
```

### Quality + Fallback
```python
llm = make_resilient_llm(
    litellm_fallbacks=[
        "anthropic/claude-3-5-haiku-20241022",
        "groq/llama-3.3-70b-versatile",
        "ollama/llama3.1",
    ],
)
```

### Local-First (no cloud dependency)
```python
from ttadev.primitives.llm import LiteLLMPrimitive

llm = LiteLLMPrimitive(
    fallbacks=["ollama/mistral", "ollama/phi3"],
)
```

### Development / CI (free tier, no key)
```python
from ttadev.primitives.llm import LiteLLMPrimitive

llm = LiteLLMPrimitive()
# Set GROQ_API_KEY in CI — Groq free tier is generous
```

---

## Model String Shorthand (provider-bound primitive)

When you bind a provider to the primitive, model names without `/` are auto-prefixed:

```python
from ttadev.primitives.llm import LiteLLMPrimitive, LLMProvider, LLMRequest

groq = LiteLLMPrimitive(provider=LLMProvider.GROQ)
# These two are equivalent:
req1 = LLMRequest(model="llama-3.1-8b-instant", messages=[...])
req2 = LLMRequest(model="groq/llama-3.1-8b-instant", messages=[...])
```

---

## LLMProvider Enum → litellm prefix mapping

| `LLMProvider` value | litellm prefix |
|---|---|
| `LLMProvider.GROQ` | `groq` |
| `LLMProvider.ANTHROPIC` | `anthropic` |
| `LLMProvider.OPENAI` | `openai` |
| `LLMProvider.OLLAMA` | `ollama` |
| `LLMProvider.GOOGLE` | `gemini` |
| `LLMProvider.OPENROUTER` | `openrouter` |
| `LLMProvider.TOGETHER` | `together_ai` |
| `LLMProvider.XAI` | `xai` |
