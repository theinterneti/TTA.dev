# LLM Provider Strategy for TTA.dev

## Benchmark Results (2026-04-09)

| Model | Provider | Latency | Best For |
|-------|----------|---------|----------|
| `groq/llama-3.1-8b-instant` | Groq | **142ms** | Fast responses, simple tasks |
| `groq/llama-3.3-70b-versatile` | Groq | **152ms** | **Recommended default** - balanced |
| `huggingface/Qwen/Qwen2.5-7B-Instruct` | HF | 615ms | Free backup, no rate limits |
| `openrouter/deepseek/deepseek-r1` | OpenRouter | 4254ms | Complex reasoning |
| `openrouter/qwen/qwen3.6-plus` | OpenRouter | 3953ms | High quality responses |
| `openrouter/qwen/qwen3-32b` | OpenRouter | 7727ms | Good but slow |

## Recommended Usage

### OpenCode (Current Session)

OpenCode is now configured to use **Groq Llama 3.3 70B** as the default model.

To change models in OpenCode:
```
/models
```

Or via CLI:
```bash
opencode -m groq/llama-3.1-8b-instant  # Fastest option
opencode -m groq/llama-3.3-70b-versatile  # Recommended default
```

### LiteLLM in Python Code

```python
import litellm

# Fastest (8B model, ~140ms)
response = litellm.completion(
    model="groq/llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Balanced (70B model, ~150ms) - RECOMMENDED
response = litellm.completion(
    model="groq/llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Complex reasoning (slower but capable)
response = litellm.completion(
    model="openrouter/deepseek/deepseek-r1",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
```

### With TTA.dev Primitives

```python
from ttadev.primitives import make_resilient_llm

llm = make_resilient_llm(
    model="groq/llama-3.3-70b-versatile",
    litellm_fallbacks=[
        "groq/llama-3.1-8b-instant",
        "openrouter/deepseek/deepseek-r1",
        "huggingface/Qwen/Qwen2.5-7B-Instruct",
    ]
)
```

## Provider-Specific Notes

### Groq (Recommended)
- **Latency**: 140-400ms
- **Rate Limits**: 30 RPM, 14,400-30,000 RPD
- **Pros**: Fastest inference, generous free tier
- **Cons**: Smaller context window compared to some

### OpenRouter
- **Latency**: 2-7 seconds (varies by model)
- **Rate Limits**: Varies by model, daily resets
- **Pros**: Many free models, good reasoning options
- **Cons**: Slower, rate limits vary

### HuggingFace
- **Latency**: ~600ms
- **Rate Limits**: 300 requests/hour
- **Pros**: Truly free, no rate limit pressure
- **Cons**: No function calling support

## OpenCode Configuration

Your OpenCode is configured in `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "groq/llama-3.3-70b-versatile",
  "mcp": {
    "hindsight": {
      "type": "remote",
      "url": "http://localhost:8888/mcp/"
    }
  }
}
```

## Quick Reference

| Task | Model | Why |
|------|-------|-----|
| Simple questions | `groq/llama-3.1-8b-instant` | Fastest |
| General coding | `groq/llama-3.3-70b-versatile` | Balanced |
| Complex reasoning | `openrouter/deepseek/deepseek-r1` | Best reasoning |
| High quality output | `openrouter/qwen/qwen3.6-plus` | Best quality |
| Free backup | `huggingface/Qwen/Qwen2.5-7B-Instruct` | No limits |
