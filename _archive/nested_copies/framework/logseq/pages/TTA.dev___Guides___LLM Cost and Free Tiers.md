type:: [[Guide]], [[Reference]]
category:: [[Cost Optimization]], [[LLM Selection]], [[Free Tiers]]
difficulty:: [[Beginner]]
estimated-time:: 45 minutes
target-audience:: [[Developers]], [[AI Engineers]], [[Product Managers]]

---

# LLM Cost Optimization: Free Tiers & Paid Models

**Navigate the LLM cost landscape and maximize your AI budget**

---

## Overview
id:: llm-cost-overview

**⚠️ Pricing changes frequently** - Last updated: October 30, 2025

**This guide covers:**

1. **Free tier comparison** across all major providers
2. **Free flagship models** (DeepSeek R1, Gemini 2.5 Pro, Llama 3.3 70B)
3. **When to use paid models** vs staying free
4. **Cost optimization strategies** with TTA.dev primitives
5. **Provider-specific details** and gotchas

---

## Common Confusion: Web UI vs API
id:: llm-cost-confusion

**⚠️ CRITICAL DISTINCTION:**

- **Web UI** (ChatGPT, Claude.ai, Gemini) - Free to use in browser
- **API Access** - Usually requires payment (with exceptions)

**Example:** ChatGPT web interface is free forever, but OpenAI API costs money after $5 credit.

---

## Free Tier Comparison
id:: llm-cost-free-tiers

### Quick Reference Table
id:: llm-cost-free-tiers-table

| Provider | Free Tier? | What's Included | Credit Card? | Expires? |
|----------|-----------|-----------------|--------------|----------|
| **OpenAI API** | ⚠️ $5 credit | $5 one-time credit | Yes | After $5 used |
| **Anthropic API** | ❌ No | None | Yes | N/A |
| **Google Gemini** | ✅ Yes | 1500 RPD free | No | Never |
| **OpenRouter** | ✅ Yes | Free flagship models | No | Daily reset |
| **Groq** | ✅ Yes | 14K-30K RPD | No | Never |
| **Hugging Face** | ✅ Yes | 300 req/hour | No | Never |
| **Together.ai** | ✅ $25 credits | $25 free credits | Yes | After credits |
| **Ollama** | ✅ Yes | Unlimited (local) | No | Never |

**Legend:** RPD = Requests Per Day

---

## Free Flagship Models
id:: llm-cost-free-flagship

**🚀 NEW!** Access flagship-quality models (rivals GPT-4/Claude Sonnet) for FREE:

### OpenRouter Free Models
id:: llm-cost-openrouter-free

**Free access to high-quality models with daily limits:**

| Model | Quality | Context | Best For |
|-------|---------|---------|----------|
| **DeepSeek R1** | 90/100 | 64K | Complex reasoning, coding |
| **DeepSeek R1 Qwen3 8B** | 85/100 | 32K | General tasks, fast |
| **Qwen 32B** | 88/100 | 32K | Multilingual, coding |

**Setup:**

```python
from tta_dev_primitives.integrations import OpenRouterPrimitive

# Use DeepSeek R1 for free (comparable to OpenAI o1!)
deepseek = OpenRouterPrimitive(
    model="deepseek/deepseek-r1:free",
    api_key="your-openrouter-key"  # Free tier, no credit card
)

result = await deepseek.execute(context, {
    "prompt": "Explain quantum computing"
})
```

**Benefits:**
- ✅ No credit card required
- ✅ Performance rivals GPT-4/Claude
- ✅ Daily limits reset automatically
- ✅ Open-source models

**Rate Limits:** Daily limits reset at midnight UTC

---

### Google AI Studio (Gemini)
id:: llm-cost-gemini-free

**Free flagship-quality models with generous limits:**

| Model | Quality | Context | Free Limits | Paid Cost |
|-------|---------|---------|-------------|-----------|
| **Gemini 2.5 Pro** | 89/100 | 2M tokens | Free | $1.25/$10 per 1M |
| **Gemini 2.5 Flash** | 85/100 | 1M tokens | Free | $0.30/$2.50 per 1M |
| **Gemini 2.5 Flash-Lite** | 82/100 | 1M tokens | Free | $0.10/$0.40 per 1M |

**Setup:**

```python
from tta_dev_primitives.integrations import GoogleAIStudioPrimitive

# Free Gemini Pro access
gemini_pro = GoogleAIStudioPrimitive(
    model="gemini-2.5-pro",
    api_key="your-google-ai-studio-key"  # Free, no credit card
)

# Free Gemini Flash for speed
gemini_flash = GoogleAIStudioPrimitive(
    model="gemini-2.5-flash",
    api_key="your-google-ai-studio-key"
)
```

**Benefits:**
- ✅ Free Gemini Pro (flagship model)
- ✅ 1500 requests/day free
- ✅ No credit card required
- ✅ 2M token context (Pro)
- ✅ Google Search grounding (500 RPD free)

**Rate Limits (Free):**
- **Gemini Pro:** 1500 RPD, 32K RPM
- **Gemini Flash:** 1500 RPD, 15 RPM

**⚠️ AI Studio vs Vertex AI:**
- **AI Studio:** Free tier (recommended for dev)
- **Vertex AI:** Paid only, enterprise features

---

### Groq (Ultra-Fast)
id:: llm-cost-groq-free

**Free models with 300+ tokens/second inference:**

| Model | Quality | Speed | Free Limits | Best For |
|-------|---------|-------|-------------|----------|
| **Llama 3.3 70B** | 87/100 | 300+ tok/sec | 14,400 RPD | General, coding |
| **Llama 3.1 8B** | 82/100 | 500+ tok/sec | 30,000 RPD | Fast, simple |
| **Mixtral 8x7B** | 85/100 | 400+ tok/sec | 14,400 RPD | Multilingual |

**Setup:**

```python
from tta_dev_primitives.integrations import GroqPrimitive

# Ultra-fast inference with Llama 3.3 70B
groq = GroqPrimitive(
    model="llama-3.3-70b-versatile",
    api_key="your-groq-key"  # Free, no credit card
)

# 300+ tokens/second - fastest free LLM API
result = await groq.execute(context, {
    "prompt": "Write a Python function to sort"
})
```

**Benefits:**
- ✅ Ultra-fast (300-500 tokens/sec)
- ✅ No credit card required
- ✅ High rate limits (14K-30K RPD)
- ✅ Production-ready quality

**Rate Limits (Free):**
- **Llama 3.3 70B:** 14,400 RPD, 30 RPM
- **Llama 3.1 8B:** 30,000 RPD, 30 RPM
- **Mixtral 8x7B:** 14,400 RPD, 30 RPM

---

### Free Flagship Comparison
id:: llm-cost-flagship-comparison

| Provider | Best Free Model | vs GPT-4 | Rate Limits | Card? | Best For |
|----------|----------------|----------|-------------|-------|----------|
| **OpenRouter** | DeepSeek R1 | 90% | Daily limits | ❌ | Complex reasoning |
| **Google AI Studio** | Gemini 2.5 Pro | 89% | 1500 RPD | ❌ | Production apps |
| **Groq** | Llama 3.3 70B | 87% | 14,400 RPD | ❌ | Ultra-fast |
| **Hugging Face** | Llama 3.3 70B | 87% | 300 req/hour | ❌ | Model variety |
| **Together.ai** | Llama 4 Scout | 88% | $25 credits | ✅ | New users |

**Quality Scoring:**
- **90-100:** Matches/exceeds GPT-4/Claude
- **85-89:** Flagship-quality, production-ready
- **80-84:** High-quality, most tasks

---

## Recommended Free Strategy
id:: llm-cost-free-strategy

### For Production Apps
id:: llm-cost-production-strategy

**1. Primary:** Google AI Studio (Gemini 2.5 Pro)
   - Free, flagship quality, 1500 RPD

**2. Fallback:** OpenRouter (DeepSeek R1)
   - Free, daily limits reset

**3. Speed:** Groq (Llama 3.3 70B)
   - Ultra-fast, 14,400 RPD

**Example workflow:**

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    OpenRouterPrimitive,
    GroqPrimitive
)

# Free flagship fallback chain
workflow = FallbackPrimitive(
    primary=GoogleAIStudioPrimitive(model="gemini-2.5-pro"),
    fallbacks=[
        OpenRouterPrimitive(model="deepseek/deepseek-r1:free"),
        GroqPrimitive(model="llama-3.3-70b-versatile")
    ]
)

# 100% uptime with free flagship models!
result = await workflow.execute(context, input_data)
```

### For Development
id:: llm-cost-development-strategy

**1. Primary:** Hugging Face (300 req/hour) - Model variety
**2. Testing:** OpenRouter (DeepSeek R1) - Free, no limits
**3. Prototyping:** Together.ai ($25 credits) - Latest models

---

## Quick Start: Free Flagship in 10 Minutes
id:: llm-cost-quick-start

### Step 1: Install TTA.dev
id:: llm-cost-quickstart-install

```bash
cd packages/tta-dev-primitives
uv sync --extra integrations
```

### Step 2: Get API Keys
id:: llm-cost-quickstart-keys

**Google AI Studio (Recommended):**
1. Go to [aistudio.google.com](https://aistudio.google.com/)
2. Click "Get API key"
3. Create new key
4. Copy key (starts with `AIza...`)

**OpenRouter (DeepSeek R1):**
1. Go to [openrouter.ai](https://openrouter.ai/)
2. Sign up (no credit card)
3. Create API key
4. Copy key (starts with `sk-or-...`)

**Groq (Ultra-Fast):**
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up (no credit card)
3. Create API key
4. Copy key (starts with `gsk_...`)

### Step 3: Set Environment Variables
id:: llm-cost-quickstart-env

```bash
# Create .env file
cp .env.example .env

# Add your keys
GOOGLE_API_KEY=AIza...your-key
OPENROUTER_API_KEY=sk-or-...your-key
GROQ_API_KEY=gsk_...your-key
```

### Step 4: Test Setup
id:: llm-cost-quickstart-test

```bash
cd packages/tta-dev-primitives
uv run python examples/free_flagship_models.py
```

**Expected output:**

```
✅ Model: gemini-2.5-pro
📝 Response: [AI response]
📊 Usage: {'prompt_tokens': 10, 'completion_tokens': 50}
🎯 Quality: 89/100 (flagship)
💰 Cost: $0.00 (FREE)
```

### Step 5: Implement in App
id:: llm-cost-quickstart-implement

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    OpenRouterPrimitive
)

# Create fallback chain
llm = FallbackPrimitive(
    primary=GoogleAIStudioPrimitive(model="gemini-2.5-pro"),
    fallbacks=[
        OpenRouterPrimitive(model="deepseek/deepseek-r1:free")
    ]
)

# Use in app
response = await llm.execute(request, context)
```

---

## When to Use Paid Models
id:: llm-cost-when-paid

### ✅ Use Paid When:
id:: llm-cost-paid-when-use

**1. Quality exceeds free capabilities**
- Complex reasoning (legal, medical, advanced coding)
- Creative writing with nuance
- Multi-step problem solving with high accuracy
- **Example:** Claude Sonnet 4.5 (90/100) vs Llama 3.2 8B (78/100)

**2. Rate limits become bottleneck**
- Processing >1500 requests/day (exceeds Gemini free)
- Batch processing large datasets
- Unpredictable production traffic
- **Example:** Gemini free = 1500 RPD, paid = unlimited

**3. Latency/reliability requirements**
- Real-time applications (chatbots, coding assistants)
- SLA requirements (99.9% uptime)
- Consistent response times (<2s)
- **Example:** Paid APIs guarantee uptime, free have no SLA

**4. Context window requirements**
- Long documents (>8K tokens)
- Multi-turn conversations with history
- Code analysis across multiple files
- **Example:** GPT-4o (128K) vs free models (4K-8K)

### ❌ Stick with Free When:
id:: llm-cost-paid-when-avoid

- **Learning/Prototyping:** Experimenting with AI
- **Low-volume:** <100 requests/day
- **Privacy-critical:** Data can't leave infrastructure (Ollama)
- **Budget constraints:** No API budget
- **Simple tasks:** Basic text generation, simple Q&A

### Hybrid Approach (Best Practice)
id:: llm-cost-hybrid-approach

```python
from tta_dev_primitives.integrations import OpenAIPrimitive, OllamaPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive

# Paid quality, free cost savings
workflow = FallbackPrimitive(
    primary=OpenAIPrimitive(model="gpt-4o"),  # Paid, high quality
    fallbacks=[
        OllamaPrimitive(model="llama3.2:8b")  # Free, unlimited
    ]
)
```

---

## Paid Model Costs
id:: llm-cost-paid-models

### Cost per 1M Tokens (October 2025)
id:: llm-cost-paid-pricing

| Model | Provider | Input | Output | Quality | Best For |
|-------|----------|-------|--------|---------|----------|
| **GPT-4o** | OpenAI | $2.50 | $10.00 | 92/100 | Complex reasoning |
| **GPT-4o-mini** | OpenAI | $0.15 | $0.60 | 82/100 | Cost-effective |
| **Claude Sonnet 4.5** | Anthropic | $3.00 | $15.00 | 90/100 | Creative writing |
| **Claude Opus** | Anthropic | $15.00 | $75.00 | 88/100 | Highest quality |
| **Gemini Pro 2.5** | Google | $1.25 | $5.00 | 89/100 | Multimodal |
| **Gemini Flash 2.5** | Google | $0.075 | $0.30 | 85/100 | Fast, cheap |

### Cost Calculation Example
id:: llm-cost-calculation

**Scenario:** 10K requests/day, 500 input tokens, 1000 output tokens

**GPT-4o-mini (most cost-effective):**
```
Daily = (10K * 500 / 1M * $0.15) + (10K * 1000 / 1M * $0.60)
      = $0.75 + $6.00 = $6.75/day = $202.50/month
```

**Gemini Flash 2.5 (cheapest):**
```
Daily = (10K * 500 / 1M * $0.075) + (10K * 1000 / 1M * $0.30)
      = $0.375 + $3.00 = $3.375/day = $101.25/month
```

**Claude Sonnet 4.5 (highest quality):**
```
Daily = (10K * 500 / 1M * $3.00) + (10K * 1000 / 1M * $15.00)
      = $15.00 + $150.00 = $165/day = $4,950/month
```

---

## Cost Optimization Quick Wins
id:: llm-cost-optimization

### 1. Cache Expensive Calls (30-40% savings)
id:: llm-cost-caching

```python
from tta_dev_primitives.performance import CachePrimitive

cached_llm = CachePrimitive(
    primitive=OpenAIPrimitive(model="gpt-4o"),
    ttl_seconds=3600,  # 1 hour
    max_size=1000
)

# 30-40% cache hit rate → 30-40% cost reduction
# $202.50/month → $121.50-$141.75/month savings
```

### 2. Route to Cheaper Models (20-50% savings)
id:: llm-cost-routing

```python
from tta_dev_primitives import RouterPrimitive

def select_model(input_data, context):
    complexity = estimate_complexity(input_data["prompt"])

    if complexity == "simple":
        return "fast"  # GPT-4o-mini
    elif complexity == "medium":
        return "balanced"  # Gemini Flash
    else:
        return "complex"  # GPT-4o

router = RouterPrimitive(
    routes={
        "fast": gpt4o_mini,
        "balanced": gemini_flash,
        "complex": gpt4o
    },
    route_selector=select_model
)

# 20-50% cost reduction typical
```

### 3. Fallback to Free (Reliability + Control)
id:: llm-cost-fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

workflow = FallbackPrimitive(
    primary=paid_model,
    fallbacks=[free_model]
)

# Prevents unexpected overages
# Maintains uptime when budget exceeded
```

---

## Provider Details
id:: llm-cost-providers

### OpenAI - $5 Credit (Then Paid)
id:: llm-cost-provider-openai

**What's free:**
- $5 one-time credit for new accounts
- Expires after 3 months or when used
- Access to GPT-4o-mini, GPT-4o, GPT-4

**⚠️ Confusion:** ChatGPT Web UI vs API
- **Web UI** (chat.openai.com): Free forever
- **API**: $5 credit, then paid
- **They are NOT the same!**

**Rate limits (free):**
- 500 RPM (requests per minute)
- 30,000 TPM (tokens per minute)
- $100/month spend limit

**Setup:**
```bash
# Sign up at platform.openai.com/signup
# Add payment method (required even for $5 credit)
# Get key from platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

**Cost after credit:**
- GPT-4o-mini: $0.15/$0.60 per 1M tokens
- GPT-4o: $2.50/$10.00 per 1M tokens

### Anthropic - No Free Tier
id:: llm-cost-provider-anthropic

**What's free:** Nothing - paid only

**⚠️ Confusion:** Claude.ai Web UI vs API
- **Web UI** (claude.ai): Free with message limits
- **API**: Paid only, no free tier
- **They are NOT the same!**

**Setup:**
```bash
# Sign up at console.anthropic.com
# Add payment method (required)
# Get API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Cost (paid only):**
- Claude 3.5 Sonnet: $3.00/$15.00 per 1M tokens
- Claude 3 Opus: $15.00/$75.00 per 1M tokens

### Google Gemini - Truly Free
id:: llm-cost-provider-google

**What's free:**
- 1500 requests/day (shared across Flash/Flash-Lite)
- Free forever (no expiration)
- Gemini 2.5 Flash, Flash-Lite, Pro models
- **No credit card required**

**⚠️ AI Studio vs Vertex AI:**
- **AI Studio**: Free tier (1500 RPD) - Use this!
- **Vertex AI**: Paid only, enterprise features

**Setup:**
```bash
# Go to aistudio.google.com
# Sign in with Google account
# Click "Get API key"
export GOOGLE_API_KEY="AIza..."
```

**Verify free tier:**
- Check aistudio.google.com usage dashboard
- Under 1500 RPD = free tier
- No billing page = still on free tier

**Cost after free:**
- Gemini 2.5 Flash: $0.30/$2.50 per 1M tokens
- Gemini 2.5 Pro: $1.25/$10.00 per 1M tokens

### Ollama - Always Free (Local)
id:: llm-cost-provider-ollama

**What's free:**
- Unlimited requests (runs on your machine)
- No API key needed
- 100% private (data never leaves machine)
- Llama 3.2, Mistral, Gemma, etc.

**Requirements:**
- **Minimum:** 8GB RAM, CPU (slow)
- **Recommended:** 16GB RAM, NVIDIA GPU
- **Optimal:** 32GB RAM, RTX 3090+

**Setup:**
```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama3.2

# Run (no API key)
ollama run llama3.2
```

**Cost:** $0 forever (uses your hardware)
**Electricity:** ~$0.10-$0.50/day (GPU usage)

---

## Integration with TTA.dev
id:: llm-cost-integration

### Maximize Free Tier Usage
id:: llm-cost-integration-maximize

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.integrations import (
    OllamaPrimitive,
    OpenAIPrimitive,
)
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Free → Paid fallback
free_llm = OllamaPrimitive(model="llama3.2")
paid_llm = OpenAIPrimitive(model="gpt-4o-mini")

workflow = FallbackPrimitive(
    primary=free_llm,
    fallbacks=[paid_llm]
)

# Add caching
cached_workflow = CachePrimitive(
    primitive=workflow,
    ttl_seconds=3600
)
```

### Rate Limiting Best Practices
id:: llm-cost-integration-rate-limiting

```python
import time

class UsageTracker:
    def __init__(self, daily_limit=1500):
        self.daily_limit = daily_limit
        self.requests_today = 0
        self.last_reset = time.time()

    def can_make_request(self):
        # Reset daily
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
        raise Exception("Daily limit - use fallback")

    tracker.record_request()
    # Make API call...
```

### Multi-Provider Strategy
id:: llm-cost-integration-multi-provider

```python
from tta_dev_primitives import RouterPrimitive

router = RouterPrimitive(
    routes={
        "local": OllamaPrimitive(),  # Free, unlimited
        "cloud_free": GoogleGeminiPrimitive(),  # 1500 RPD
        "paid_backup": OpenAIPrimitive()  # $5 credit
    },
    default_route="local"
)

def select_route(task):
    if task.is_simple:
        return "local"  # Free Ollama
    elif task.is_urgent:
        return "cloud_free"  # Gemini (faster)
    else:
        return "paid_backup"  # OpenAI credit
```

---

## Decision Guide
id:: llm-cost-decision

### For Learning/Prototyping
id:: llm-cost-decision-learning

1. **Start:** Ollama (unlimited, local)
2. **Then:** Google Gemini (1500 RPD, no card)
3. **Finally:** OpenAI $5 credit (best quality)

### For Production (Free)
id:: llm-cost-decision-production

1. **Best:** Google Gemini (1500 RPD, reliable)
2. **Backup:** OpenRouter BYOK (1M requests/month)
3. **Local:** Ollama (unlimited, but slower)

### For Privacy-Critical
id:: llm-cost-decision-privacy

1. **Only option:** Ollama (100% local)
2. **Avoid:** All cloud APIs

---

## Key Takeaways
id:: llm-cost-summary

**Free Flagship Models Available:**

- **DeepSeek R1** via OpenRouter (90/100 quality, free)
- **Gemini 2.5 Pro** via AI Studio (89/100, 1500 RPD free)
- **Llama 3.3 70B** via Groq (87/100, 14,400 RPD free)

**Best Free Strategy:**

1. Primary: Google AI Studio (Gemini 2.5 Pro)
2. Fallback: OpenRouter (DeepSeek R1)
3. Speed: Groq (Llama 3.3 70B)

**When to Pay:**

- Quality requirements exceed free (complex reasoning)
- Rate limits bottleneck (>1500 RPD)
- Latency/SLA requirements (real-time, 99.9% uptime)
- Large context windows needed (>8K tokens)

**Cost Optimization:**

- Cache: 30-40% savings
- Router: 20-50% savings
- Fallback: Reliability + control
- All three: 70-95% savings possible

---

## Related Documentation

- [[TTA.dev/Guides/Cost Optimization]] - TTA.dev primitive cost optimization strategies
- [[TTA.dev/Guides/LLM Selection]] - Decision matrix for choosing LLMs
- [[TTA.dev/Guides/Integration Primitives]] - Using integration primitives
- [[TTA.dev/Primitives/CachePrimitive]] - Caching implementation
- [[TTA.dev/Primitives/RouterPrimitive]] - Smart routing
- [[TTA.dev/Primitives/FallbackPrimitive]] - Fallback chains

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team

**⚠️ Important:** Free tier limits change frequently. Always verify current rates on provider websites before production use.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___guides___llm cost and free tiers]]
