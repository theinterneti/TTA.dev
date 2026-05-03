# LiteLLM Provider Configuration

This config provides intelligent routing across multiple LLM providers with automatic fallback.

## Status (Tested 2026-04-09)

| Provider | Model | Status | Latency | Notes |
|----------|-------|--------|---------|-------|
| **Groq** | llama-3.3-70b-versatile | ✅ Working | ~250ms | Fastest, use first |
| **Groq** | llama-3.1-8b-instant | ✅ Working | ~150ms | Fastest, use first |
| **OpenRouter** | deepseek/deepseek-r1 | ✅ Working | ~5500ms | Good for reasoning |
| **OpenRouter** | qwen/qwen3-32b | ✅ Working | ~2000ms | Fast reasoning |
| **OpenRouter** | qwen/qwen3.6-plus | ✅ Working | ~6000ms | Good quality |
| **HuggingFace** | Qwen/Qwen2.5-7B-Instruct | ✅ Working | ~600ms | Good free option |
| **Gemini** | gemini-2.5-flash | ✅ Working | ~600ms | Rate limits may apply |
| **Anthropic** | claude-3-5-sonnet | ❌ No credits | - | Add credits to use |
| **OpenAI** | gpt-4o-mini | ❌ Placeholder key | - | Add real key to use |
| **Together.ai** | llama-4-scout | ⚠️ Not tested | - | Needs $25 credits |

## Recommended Provider Order (Free Tier)

1. **Groq** - Fastest (150-400ms), generous limits, use for everything
2. **HuggingFace** - Good backup (600ms), truly free
3. **OpenRouter/Qwen** - Fast reasoning models
4. **OpenRouter/DeepSeek** - For complex reasoning tasks
5. **Gemini** - Backup option (rate limited)

## Usage

### Direct Python Usage

```python
import litellm

# Fast option (Groq)
response = litellm.completion(
    model="groq/llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)

# OpenRouter option
response = litellm.completion(
    model="openrouter/qwen/qwen3-32b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### With TTA.dev Primitives

```python
from ttadev.primitives import LiteLLMPrimitive, make_resilient_llm

# Create resilient LLM with fallbacks
llm = make_resilient_llm(
    model="groq/llama-3.3-70b-versatile",
    litellm_fallbacks=[
        "groq/llama-3.1-8b-instant",
        "openrouter/qwen/qwen3-32b",
        "huggingface/Qwen/Qwen2.5-7B-Instruct",
    ]
)
```

### Start LiteLLM Proxy

```bash
# Start the proxy server
litellm --config litellm_config.yaml

# Then in your app, use:
# http://localhost:4000/v1
```

## Adding Your Keys

All keys are loaded from environment variables. Ensure they're in your `.env`:

```bash
GROQ_API_KEY=your-groq-key
OPENROUTER_API_KEY=your-openrouter-key
GOOGLE_API_KEY=your-google-key
HF_TOKEN=your-huggingface-token
```

## Rate Limits

- **Groq**: 30 RPM, 14,400-30,000 RPD
- **Gemini**: 1500 RPM (project-specific)
- **OpenRouter**: Varies by model, daily limits
- **HuggingFace**: 300 requests/hour (free tier)

## Notes

- Gemini models may hit rate limits with heavy usage
- Anthropic requires paid credits
- OpenAI key is placeholder - needs real key
- Test your providers: `uv run python scripts/test_providers.py`
