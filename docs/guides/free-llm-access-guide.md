# Free LLM Access Guide

**For AI Agents & Developers:** Navigate the confusing landscape of free LLM access

**Last Updated:** October 30, 2025 *(Free tiers change frequently - verify current limits)*

---

## ⚠️ Common Confusion: Web UI vs API Access

**Critical distinction:**
- **Web UI (ChatGPT, Claude.ai, Gemini)** - Free to use in browser
- **API Access** - Usually requires payment (with some exceptions)

**Example:** You can use ChatGPT for free in your browser, but the OpenAI API requires payment after $5 credit.

---

## 📊 Free Tier Comparison Table

| Provider | Free Tier? | What's Included | How to Access | Credit Card Required? | Expires? |
|----------|-----------|-----------------|---------------|----------------------|----------|
| **OpenAI API** | ⚠️ $5 credit only | $5 one-time credit | API key | Yes | After $5 used |
| **Anthropic API** | ❌ No | None | API key | Yes | N/A |
| **Google Gemini** | ✅ Yes | 1500 RPD free | Google AI Studio | No | Never |
| **OpenRouter BYOK** | ✅ Yes | 1M requests/month | API key | No | Monthly reset |
| **Ollama** | ✅ Yes | Unlimited | Local install | No | Never |

**Legend:**
- RPD = Requests Per Day
- BYOK = Bring Your Own Key

---

## 🟢 OpenAI API - $5 Credit (Then Paid)

### What's Free?

- **$5 one-time credit** for new accounts
- Expires after 3 months or when used up
- Access to GPT-4o-mini, GPT-4o, GPT-4

### ⚠️ Common Confusion

**Q: "Can I use ChatGPT for free?"**

**A:** Yes, but there are TWO different things:
1. **ChatGPT Web UI** (chat.openai.com) - Free forever
2. **OpenAI API** - $5 credit, then you pay

**They are NOT the same!**

### Rate Limits (Free Tier)

- **Tier 1** (after $5 credit used):
  - 500 RPM (requests per minute)
  - 30,000 TPM (tokens per minute)
  - $100/month spend limit

### How to Get Started

```bash
# 1. Sign up at https://platform.openai.com/signup
# 2. Add payment method (required even for $5 credit)
# 3. Get API key from https://platform.openai.com/api-keys
# 4. Set environment variable
export OPENAI_API_KEY="sk-..."
```

### How to Verify You're Not Being Charged

1. Go to https://platform.openai.com/usage
2. Check "Free trial usage" vs "Paid usage"
3. Set up billing alerts at $1, $5, $10

### Cost After Free Credit

- **GPT-4o-mini:** $0.15/1M input tokens, $0.60/1M output tokens
- **GPT-4o:** $2.50/1M input tokens, $10.00/1M output tokens

---

## 🔵 Anthropic Claude API - No Free Tier

### What's Free?

**Nothing.** Anthropic does not offer a free API tier.

### ⚠️ Common Confusion

**Q: "Can I use Claude for free?"**

**A:** Yes, but only the **web interface** (claude.ai):
1. **Claude.ai Web UI** - Free with limits (message caps)
2. **Anthropic API** - Paid only, no free tier

**They are NOT the same!**

### How to Get Started (Paid)

```bash
# 1. Sign up at https://console.anthropic.com/
# 2. Add payment method (required)
# 3. Get API key
# 4. Set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Cost (No Free Option)

- **Claude 3.5 Sonnet:** $3.00/1M input tokens, $15.00/1M output tokens
- **Claude 3 Opus:** $15.00/1M input tokens, $75.00/1M output tokens

---

## 🟢 Google Gemini - Truly Free API

### What's Free?

- **1500 requests per day (RPD)** - Shared across Flash and Flash-Lite
- **Free forever** (no expiration)
- Access to Gemini 2.5 Flash, Flash-Lite, Pro models
- **No credit card required**

### ⚠️ Common Confusion: AI Studio vs Vertex AI

**Q: "What's the difference between Google AI Studio and Vertex AI?"**

**A:** They are COMPLETELY different:

| Feature | Google AI Studio | Vertex AI |
|---------|------------------|-----------|
| **Free Tier** | ✅ Yes (1500 RPD) | ❌ No |
| **Target** | Developers, prototyping | Enterprise, production |
| **Setup** | Simple API key | GCP project, billing |
| **Best For** | Testing, learning | Production apps |

**Use Google AI Studio for free access!**

### Rate Limits (Free Tier)

- **Gemini 2.5 Flash:** 1500 RPD (shared with Flash-Lite)
- **Gemini 2.5 Flash-Lite:** 1500 RPD (shared with Flash)
- **Gemini 2.5 Pro:** Free of charge (rate limits apply)

### How to Get Started

```bash
# 1. Go to https://aistudio.google.com/
# 2. Sign in with Google account
# 3. Click "Get API key"
# 4. Set environment variable
export GOOGLE_API_KEY="AIza..."
```

### How to Verify You're on Free Tier

1. Go to https://aistudio.google.com/
2. Check "API usage" dashboard
3. Verify you're under 1500 RPD
4. **No billing page = you're on free tier**

### Cost After Free Tier

- **Gemini 2.5 Flash:** $0.30/1M input tokens, $2.50/1M output tokens
- **Gemini 2.5 Pro:** $1.25/1M input tokens, $10.00/1M output tokens

---

## 🟣 OpenRouter BYOK - 1M Free Requests/Month

### What's Free?

- **1 million BYOK requests per month**
- Resets monthly (midnight UTC)
- Use your own provider API keys
- Access to 60+ providers

### ⚠️ Common Confusion: BYOK vs Regular OpenRouter

**Q: "What's the difference between OpenRouter free tier and BYOK?"**

**A:** Two different things:

| Feature | OpenRouter (Regular) | OpenRouter BYOK |
|---------|---------------------|-----------------|
| **Who pays provider?** | OpenRouter | You (your API keys) |
| **Free tier** | Limited credits | 1M requests/month |
| **Your API keys** | Not used | Required |
| **Best for** | Quick testing | Production with your keys |

**BYOK = You bring your own OpenAI/Anthropic/etc. keys, OpenRouter routes for free (up to 1M/month)**

### How to Get Started

```bash
# 1. Sign up at https://openrouter.ai/
# 2. Go to https://openrouter.ai/settings/integrations
# 3. Add your provider API keys (OpenAI, Anthropic, etc.)
# 4. Get OpenRouter API key
# 5. Set environment variable
export OPENROUTER_API_KEY="sk-or-..."
```

### How to Verify You're on Free Tier

1. Go to https://openrouter.ai/activity
2. Check "BYOK requests" count
3. Verify you're under 1M/month
4. After 1M, 5% fee applies

### Cost After Free Tier

- **After 1M requests/month:** 5% fee on provider costs
- **Example:** $10 in provider costs = $0.50 OpenRouter fee

---

## 🟢 Ollama - Always Free (Local)

### What's Free?

- **Unlimited requests** (runs on your machine)
- **No API key needed**
- **100% private** (data never leaves your machine)
- Access to Llama 3.2, Mistral, Gemma, etc.

### ⚠️ Common Confusion: Local vs Cloud

**Q: "Is Ollama really free?"**

**A:** Yes, but it's **local**:
- Runs on your computer (not cloud)
- Requires GPU for good performance
- No internet needed after model download

### System Requirements

- **Minimum:** 8GB RAM, CPU only (slow)
- **Recommended:** 16GB RAM, NVIDIA GPU
- **Optimal:** 32GB RAM, RTX 3090 or better

### How to Get Started

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download a model
ollama pull llama3.2

# 3. Run locally (no API key needed)
ollama run llama3.2
```

### How to Verify It's Free

- **No API key = No charges**
- **No internet = No charges**
- **Runs locally = Always free**

### Cost

- **$0 forever** (uses your hardware)
- **Electricity cost:** ~$0.10-$0.50/day (GPU usage)

---

## 💻 Integration with TTA.dev Primitives

### Using Free Tiers with TTA.dev

```python
"""Example: Maximize free tier usage with RouterPrimitive"""

from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.integrations import (
    OllamaPrimitive,
    OpenAIPrimitive,
)
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive
import os

# Strategy: Free → Paid fallback
free_llm = OllamaPrimitive(model="llama3.2")  # Always free
paid_llm = OpenAIPrimitive(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"  # Cheapest paid option
)

# Try free first, fallback to paid
workflow = FallbackPrimitive(
    primary=free_llm,
    fallbacks=[paid_llm]
)

# Add caching to reduce API calls
cached_workflow = CachePrimitive(
    primitive=workflow,
    ttl_seconds=3600  # 1 hour cache
)
```

### Rate Limiting Best Practices

```python
"""Example: Stay within free tier limits"""

from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.integrations import OpenAIPrimitive
import time

# Track usage to stay within free tier
class UsageTracker:
    def __init__(self, daily_limit=1500):
        self.daily_limit = daily_limit
        self.requests_today = 0
        self.last_reset = time.time()
    
    def can_make_request(self):
        # Reset counter daily
        if time.time() - self.last_reset > 86400:
            self.requests_today = 0
            self.last_reset = time.time()
        
        return self.requests_today < self.daily_limit
    
    def record_request(self):
        self.requests_today += 1

# Use with Gemini (1500 RPD free)
tracker = UsageTracker(daily_limit=1500)

async def safe_llm_call(prompt):
    if not tracker.can_make_request():
        raise Exception("Daily limit reached - use fallback")
    
    tracker.record_request()
    # Make API call...
```

### Multi-Provider Strategy

```python
"""Example: Combine multiple free tiers"""

from tta_dev_primitives import RouterPrimitive

# Use different providers for different tasks
router = RouterPrimitive(
    routes={
        "local": OllamaPrimitive(),  # Free, unlimited
        "cloud_free": GoogleGeminiPrimitive(),  # 1500 RPD free
        "paid_backup": OpenAIPrimitive()  # $5 credit
    },
    default_route="local"
)

# Route based on task complexity
def select_route(task):
    if task.is_simple:
        return "local"  # Use free Ollama
    elif task.is_urgent:
        return "cloud_free"  # Use Gemini (faster)
    else:
        return "paid_backup"  # Use OpenAI credit
```

---

## 🎯 Decision Guide: Which Free Tier?

### For Learning/Prototyping

1. **Start with:** Ollama (unlimited, local)
2. **Then try:** Google Gemini (1500 RPD, no credit card)
3. **Finally:** OpenAI $5 credit (best quality)

### For Production (Free)

1. **Best option:** Google Gemini (1500 RPD, reliable)
2. **Backup:** OpenRouter BYOK (1M requests/month)
3. **Local:** Ollama (unlimited, but slower)

### For Privacy-Critical

1. **Only option:** Ollama (100% local)
2. **Avoid:** All cloud APIs (data sent to providers)

---

## 📚 Related Documentation

- **LLM Selection Guide:** [llm-selection-guide.md](llm-selection-guide.md)
- **Integration Primitives Quick Reference:** [integration-primitives-quickref.md](integration-primitives-quickref.md)
- **OpenAI Primitive:** [`packages/tta-dev-primitives/src/tta_dev_primitives/integrations/openai_primitive.py`](../../packages/tta-dev-primitives/src/tta_dev_primitives/integrations/openai_primitive.py)
- **Ollama Primitive:** [`packages/tta-dev-primitives/src/tta_dev_primitives/integrations/ollama_primitive.py`](../../packages/tta-dev-primitives/src/tta_dev_primitives/integrations/ollama_primitive.py)

---

**Last Updated:** October 30, 2025  
**For:** AI Agents & Developers (all skill levels)  
**Maintained by:** TTA.dev Team

**⚠️ Important:** Free tier limits change frequently. Always verify current limits on provider websites before relying on this information for production use.

