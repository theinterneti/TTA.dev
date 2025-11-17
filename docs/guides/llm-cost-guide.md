# LLM Cost Optimization Guide: Free Tiers & Paid Models

**For AI Agents & Developers:** Navigate the landscape of LLM costs and optimize your spending

**Last Updated:** October 30, 2025 *(Pricing changes frequently - verify current rates)*

---

## 📖 Table of Contents

- [Free Tier Comparison](#-free-tier-comparison-table)
- [Free Access to Flagship Models](#-free-access-to-flagship-models)
- [When to Use Paid Models](#-when-to-use-paid-models)
- [Paid Model Cost Comparison](#-paid-model-cost-comparison)
- [Cost Optimization Quick Wins](#-cost-optimization-quick-wins)
- [Provider Details](#provider-details)
- [Decision Guide](#-decision-guide-which-free-tier)
- [Related Documentation](#-related-documentation)

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
| **OpenRouter** | ✅ Yes | Free flagship models (DeepSeek R1, Qwen) | API key | No | Daily reset |
| **Groq** | ✅ Yes | 14K-30K RPD (Llama 3.3 70B, Mixtral) | API key | No | Never |
| **Hugging Face** | ✅ Yes | 300 req/hour (thousands of models) | API key | No | Never |
| **Together.ai** | ✅ $25 credits | $25 free credits for new users | API key | Yes | After credits used |
| **Ollama** | ✅ Yes | Unlimited | Local install | No | Never |

**Legend:**
- RPD = Requests Per Day
- BYOK = Bring Your Own Key

---

## 🎁 Free Access to Flagship Models

**NEW!** Several providers now offer free access to flagship-quality models that rival GPT-4 and Claude Sonnet. Here's how to access them:

### 🚀 OpenRouter Free Models

OpenRouter provides free access to several high-quality models with daily limits:

| Model | Quality Score | Context Window | Rate Limits | Best For |
|-------|--------------|----------------|-------------|----------|
| **DeepSeek R1** | 90/100 | 64K | Daily limit (resets) | Complex reasoning, coding |
| **DeepSeek R1 Qwen3 8B** | 85/100 | 32K | Daily limit (resets) | General tasks, fast inference |
| **Qwen 32B** | 88/100 | 32K | Daily limit (resets) | Multilingual, coding |

**Setup:**
```python
from tta_dev_primitives.integrations import OpenRouterPrimitive

# Use DeepSeek R1 for free
deepseek = OpenRouterPrimitive(
    model="deepseek/deepseek-r1:free",
    api_key="your-openrouter-key"  # Free tier, no credit card
)

# Performance on par with OpenAI o1, but free!
result = await deepseek.execute(context, {
    "prompt": "Explain quantum computing in simple terms"
})
```

**Key Benefits:**
- ✅ No credit card required
- ✅ Performance comparable to GPT-4/Claude
- ✅ Daily limits reset automatically
- ✅ Open-source models (DeepSeek, Qwen)

**Rate Limits:**
- Daily limits vary by model
- Limits reset at midnight UTC
- No hard cap on total usage per month

---

### 🌟 Google AI Studio (Gemini Pro & Flash)

Google AI Studio provides **free access to Gemini Pro and Flash** models - flagship-quality models with generous limits:

| Model | Quality Score | Context Window | Free Tier Limits | Paid Tier Cost |
|-------|--------------|----------------|------------------|----------------|
| **Gemini 2.5 Pro** | 89/100 | 2M tokens | Free of charge | $1.25/$10.00 per 1M tokens |
| **Gemini 2.5 Flash** | 85/100 | 1M tokens | Free of charge | $0.30/$2.50 per 1M tokens |
| **Gemini 2.5 Flash-Lite** | 82/100 | 1M tokens | Free of charge | $0.10/$0.40 per 1M tokens |

**Setup:**
```python
from tta_dev_primitives.integrations import GoogleAIStudioPrimitive

# Free Gemini Pro access via AI Studio
gemini_pro = GoogleAIStudioPrimitive(
    model="gemini-2.5-pro",
    api_key="your-google-ai-studio-key"  # Free tier, no credit card
)

# Free Gemini Flash for faster responses
gemini_flash = GoogleAIStudioPrimitive(
    model="gemini-2.5-flash",
    api_key="your-google-ai-studio-key"
)
```

**Key Benefits:**
- ✅ **Free Gemini Pro** - Flagship model at no cost
- ✅ 1500 requests per day (RPD) free tier
- ✅ No credit card required
- ✅ 2M token context window (Pro)
- ✅ Grounding with Google Search (500 RPD free)

**Rate Limits (Free Tier):**
- **Gemini Pro:** 1500 RPD, 32K RPM (requests per minute)
- **Gemini Flash:** 1500 RPD, 15 RPM
- **Gemini Flash-Lite:** 1500 RPD, 15 RPM

**⚠️ Important:** Google AI Studio vs Vertex AI
- **AI Studio:** Free tier with generous limits (recommended for development)
- **Vertex AI:** Paid only, enterprise features, higher rate limits

---

### ⚡ Groq (Ultra-Fast Inference)

Groq provides **free access to several models** with ultra-fast inference speeds:

| Model | Quality Score | Speed | Free Tier Limits | Best For |
|-------|--------------|-------|------------------|----------|
| **Llama 3.3 70B** | 87/100 | 300+ tokens/sec | 14,400 RPD | General tasks, coding |
| **Llama 3.1 8B** | 82/100 | 500+ tokens/sec | 30,000 RPD | Fast responses, simple tasks |
| **Mixtral 8x7B** | 85/100 | 400+ tokens/sec | 14,400 RPD | Multilingual, reasoning |

**Setup:**
```python
from tta_dev_primitives.integrations import GroqPrimitive

# Ultra-fast inference with Llama 3.3 70B
groq = GroqPrimitive(
    model="llama-3.3-70b-versatile",
    api_key="your-groq-key"  # Free tier, no credit card
)

# 300+ tokens/second - fastest free LLM API
result = await groq.execute(context, {
    "prompt": "Write a Python function to sort a list"
})
```

**Key Benefits:**
- ✅ **Ultra-fast inference** (300-500 tokens/sec)
- ✅ No credit card required
- ✅ High daily rate limits (14K-30K RPD)
- ✅ Production-ready quality

**Rate Limits (Free Tier):**
- **Llama 3.3 70B:** 14,400 RPD, 30 RPM
- **Llama 3.1 8B:** 30,000 RPD, 30 RPM
- **Mixtral 8x7B:** 14,400 RPD, 30 RPM

---

### 🤗 Hugging Face Inference API

Hugging Face provides free access to thousands of models via their Inference API:

| Tier | Rate Limits | Models Available | Best For |
|------|-------------|------------------|----------|
| **Unregistered** | 1 request/hour | All public models | Testing |
| **Registered (Free)** | 300 requests/hour | All public models | Development |
| **Pro ($9/month)** | 10,000 requests/hour | All models + priority | Production |

**Setup:**
```python
from tta_dev_primitives.integrations import HuggingFacePrimitive

# Free access to Llama, Mistral, and more
hf = HuggingFacePrimitive(
    model="meta-llama/Llama-3.3-70B-Instruct",
    api_key="your-hf-token"  # Free tier, no credit card
)

# Access thousands of open-source models
result = await hf.execute(context, {
    "prompt": "Explain machine learning"
})
```

**Key Benefits:**
- ✅ Access to **thousands of models**
- ✅ 300 requests/hour (free tier)
- ✅ No credit card required
- ✅ Includes Llama, Mistral, Falcon, and more

**Rate Limits (Free Tier):**
- **Registered:** 300 requests/hour
- **Unregistered:** 1 request/hour
- **Pro ($9/month):** 10,000 requests/hour

---

### 💡 Together.ai Free Credits

Together.ai offers **$25 in free credits** for new users:

| Model | Quality Score | Free Credits | Cost After Credits | Best For |
|-------|--------------|--------------|-------------------|----------|
| **Llama 4 Scout** | 88/100 | $25 free | $0.20/$0.80 per 1M tokens | General tasks |
| **FLUX.1 Schnell** | N/A | 3 months free | Image generation | Image generation |

**Setup:**
```python
from tta_dev_primitives.integrations import TogetherAIPrimitive

# $25 in free credits for new users
together = TogetherAIPrimitive(
    model="meta-llama/Llama-4-Scout",
    api_key="your-together-key"  # $25 free credits
)

# Use credits for text or image generation
result = await together.execute(context, {
    "prompt": "Generate a business plan"
})
```

**Key Benefits:**
- ✅ **$25 in free credits** for new users
- ✅ 3 months of unlimited FLUX.1 image generation
- ✅ Access to latest Llama models
- ✅ Fast inference speeds

**Free Credits:**
- **New users:** $25 in credits
- **FLUX.1 Schnell:** 3 months unlimited (image generation)
- **After credits:** Pay-as-you-go pricing

---

### 📊 Free Flagship Model Comparison

| Provider | Best Free Model | Quality vs GPT-4 | Rate Limits | Credit Card? | Best For |
|----------|----------------|------------------|-------------|--------------|----------|
| **OpenRouter** | DeepSeek R1 | 90% | Daily limits | ❌ No | Complex reasoning |
| **Google AI Studio** | Gemini 2.5 Pro | 89% | 1500 RPD | ❌ No | Production apps |
| **Groq** | Llama 3.3 70B | 87% | 14,400 RPD | ❌ No | Ultra-fast inference |
| **Hugging Face** | Llama 3.3 70B | 87% | 300 req/hour | ❌ No | Model variety |
| **Together.ai** | Llama 4 Scout | 88% | $25 credits | ✅ Yes | New users |

**Quality Scoring:**
- 90-100: Matches or exceeds GPT-4/Claude Sonnet
- 85-89: Flagship-quality, suitable for production
- 80-84: High-quality, suitable for most tasks

---

### 🎯 Recommended Free Flagship Strategy

**For Production Apps:**
1. **Primary:** Google AI Studio (Gemini 2.5 Pro) - Free, flagship quality, 1500 RPD
2. **Fallback:** OpenRouter (DeepSeek R1) - Free, daily limits reset
3. **Speed:** Groq (Llama 3.3 70B) - Ultra-fast, 14,400 RPD

**For Development:**
1. **Primary:** Hugging Face (300 req/hour) - Model variety
2. **Testing:** OpenRouter (DeepSeek R1) - Free, no limits
3. **Prototyping:** Together.ai ($25 credits) - Latest models

**Example Workflow:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    OpenRouterPrimitive,
    GroqPrimitive
)

# Free flagship model fallback chain
workflow = FallbackPrimitive(
    primary=GoogleAIStudioPrimitive(model="gemini-2.5-pro"),  # Free, flagship
    fallbacks=[
        OpenRouterPrimitive(model="deepseek/deepseek-r1:free"),  # Free, daily limits
        GroqPrimitive(model="llama-3.3-70b-versatile")  # Free, ultra-fast
    ]
)

# 100% uptime with free flagship models!
result = await workflow.execute(context, input_data)
```

---

### 🚀 Quick Start Guide: Set Up Free Flagship Access in 10 Minutes

Follow these steps to get free flagship model access working immediately:

#### Step 1: Install TTA.dev Primitives

```bash
cd platform/primitives
uv sync --extra integrations
```

#### Step 2: Obtain API Keys

**Google AI Studio (Recommended - Best Free Flagship):**
1. Go to [https://aistudio.google.com/](https://aistudio.google.com/)
2. Click "Get API key" in the top right
3. Create new API key
4. Copy the key (starts with `AIza...`)

**OpenRouter (DeepSeek R1 - On Par with OpenAI o1):**
1. Go to [https://openrouter.ai/](https://openrouter.ai/)
2. Sign up for free account (no credit card required)
3. Go to "Keys" in dashboard
4. Create new API key
5. Copy the key (starts with `sk-or-...`)

**Groq (Ultra-Fast Inference):**
1. Go to [https://console.groq.com/](https://console.groq.com/)
2. Sign up for free account (no credit card required)
3. Go to "API Keys" in dashboard
4. Create new API key
5. Copy the key (starts with `gsk_...`)

#### Step 3: Set Environment Variables

Create a `.env` file in your project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your keys
GOOGLE_API_KEY=AIza...your-key-here
OPENROUTER_API_KEY=sk-or-...your-key-here
GROQ_API_KEY=gsk_...your-key-here
```

#### Step 4: Test Your Setup

Run the free flagship models example:

```bash
cd platform/primitives
uv run python examples/free_flagship_models.py
```

**Expected Output:**
```
✅ Model: gemini-2.5-pro
📝 Response: [AI-generated response]
📊 Usage: {'prompt_tokens': 10, 'completion_tokens': 50, 'total_tokens': 60}
🎯 Quality: 89/100 (flagship)
💰 Cost: $0.00 (FREE)
```

#### Step 5: Verify Free Tier Access

**Google AI Studio:**
- Check usage: [https://aistudio.google.com/](https://aistudio.google.com/)
- Free tier: 1500 RPD
- No credit card required

**OpenRouter:**
- Check usage: [https://openrouter.ai/activity](https://openrouter.ai/activity)
- Free tier: Daily limits reset at midnight UTC
- No credit card required

**Groq:**
- Check usage: [https://console.groq.com/](https://console.groq.com/)
- Free tier: 14,400-30,000 RPD
- No credit card required

#### Step 6: Implement in Your App

Use the fallback chain pattern for 100% uptime:

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    OpenRouterPrimitive,
    GroqPrimitive
)

# Create fallback chain
llm = FallbackPrimitive(
    primary=GoogleAIStudioPrimitive(model="gemini-2.5-pro"),
    fallbacks=[
        OpenRouterPrimitive(model="deepseek/deepseek-r1:free"),
        GroqPrimitive(model="llama-3.3-70b-versatile")
    ]
)

# Use in your app
response = await llm.execute(request, context)
```

#### Troubleshooting

**Issue: "Invalid API key"**
- Solution: Verify key is correct and not expired
- Check environment variable is set: `echo $GOOGLE_API_KEY`

**Issue: "Rate limit exceeded"**
- Solution: Switch to fallback provider or wait for limit reset
- Google AI Studio: 1500 RPD limit
- OpenRouter: Daily limits reset at midnight UTC
- Groq: 14,400-30,000 RPD limit

**Issue: "Model not found"**
- Solution: Verify model name is correct
- Google AI Studio: `gemini-2.5-pro`, `gemini-2.5-flash`
- OpenRouter: `deepseek/deepseek-r1:free`, `qwen/qwen-32b:free`
- Groq: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`

**Issue: "Connection timeout"**
- Solution: Check internet connection and provider status
- Use fallback chain for automatic failover

#### Next Steps

1. **Monitor Usage:** Check provider dashboards regularly
2. **Set Up Alerts:** Configure alerts before hitting limits
3. **Optimize Routing:** Use RouterPrimitive to route simple queries to faster models
4. **Add Caching:** Use CachePrimitive to reduce API calls by 30-40%
5. **Production Deployment:** Implement fallback chain for 100% uptime

**Full Documentation:**
- [Free Flagship Models Example](../../platform/primitives/examples/free_flagship_models.py)
- [Cost Optimization Patterns](./cost-optimization-patterns.md)
- [Integration Primitives Quick Reference](./integration-primitives-quickref.md)

---

## 💰 When to Use Paid Models

While free tiers are great for learning and prototyping, production use cases often require paid models. Here's when to make the switch:

### ✅ Use Paid Models When:

**1. Quality Requirements Exceed Free Tier Capabilities**
- Complex reasoning tasks (legal analysis, medical research, advanced coding)
- Creative writing requiring nuance and consistency
- Multi-step problem solving with high accuracy requirements
- **Example:** Claude Sonnet 4.5 (90/100 quality) vs Llama 3.2 8B (78/100 quality)

**2. Rate Limits Become a Bottleneck**
- Processing >1500 requests/day (exceeds Gemini free tier)
- Batch processing large datasets
- Production applications with unpredictable traffic
- **Example:** Google Gemini free tier = 1500 RPD, paid tier = unlimited

**3. Latency/Reliability Requirements**
- Real-time applications (chatbots, live coding assistants)
- SLA requirements (99.9% uptime)
- Consistent response times (<2s)
- **Example:** Paid APIs offer guaranteed uptime, free tiers have no SLA

**4. Context Window Requirements**
- Processing long documents (>8K tokens)
- Multi-turn conversations with extensive history
- Code analysis across multiple files
- **Example:** GPT-4o (128K context) vs free local models (4K-8K context)

### ❌ Stick with Free Models When:

- **Learning/Prototyping:** Experimenting with AI features
- **Low-volume use:** <100 requests/day
- **Privacy-critical:** Data cannot leave your infrastructure (use Ollama)
- **Budget constraints:** No budget for API costs
- **Simple tasks:** Basic text generation, simple Q&A

### 🎯 Hybrid Approach (Best Practice)

Use TTA.dev primitives to combine free and paid models intelligently:

```python
from tta_dev_primitives.integrations import OpenAIPrimitive, OllamaPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive

# Start with paid (quality), fallback to free (cost savings)
workflow = FallbackPrimitive(
    primary=OpenAIPrimitive(model="gpt-4o"),  # Paid, high quality
    fallbacks=[
        OllamaPrimitive(model="llama3.2:8b")  # Free, unlimited
    ]
)
```

---

## 💵 Paid Model Cost Comparison

**Cost per 1M tokens (October 2025):**

| Model | Provider | Input Cost | Output Cost | Quality Score | Best For |
|-------|----------|-----------|-------------|---------------|----------|
| **GPT-4o** | OpenAI | $2.50 | $10.00 | 92/100 | Complex reasoning, code generation |
| **GPT-4o-mini** | OpenAI | $0.15 | $0.60 | 82/100 | General purpose, cost-effective |
| **Claude Sonnet 4.5** | Anthropic | $3.00 | $15.00 | 90/100 | Creative writing, analysis |
| **Claude Opus** | Anthropic | $15.00 | $75.00 | 88/100 | Highest quality, complex tasks |
| **Gemini Pro 2.5** | Google | $1.25 | $5.00 | 89/100 | Multimodal, cost-effective |
| **Gemini Flash 2.5** | Google | $0.075 | $0.30 | 85/100 | Fast, cheap, good quality |

**Cost Calculation Example:**

```python
# Example: 10K requests/day, 500 tokens input, 1000 tokens output

# GPT-4o-mini (most cost-effective paid option)
daily_cost = (10000 * 500 / 1_000_000 * 0.15) + (10000 * 1000 / 1_000_000 * 0.60)
# = $0.75 + $6.00 = $6.75/day = $202.50/month

# Gemini Flash 2.5 (cheapest paid option)
daily_cost = (10000 * 500 / 1_000_000 * 0.075) + (10000 * 1000 / 1_000_000 * 0.30)
# = $0.375 + $3.00 = $3.375/day = $101.25/month

# Claude Sonnet 4.5 (highest quality)
daily_cost = (10000 * 500 / 1_000_000 * 3.00) + (10000 * 1000 / 1_000_000 * 15.00)
# = $15.00 + $150.00 = $165.00/day = $4,950/month
```

**💡 Cost Optimization Insight:**

Using TTA.dev's `CachePrimitive` can reduce costs by **30-40%** by avoiding redundant API calls:

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive LLM calls
cached_llm = CachePrimitive(
    primitive=OpenAIPrimitive(model="gpt-4o"),
    ttl_seconds=3600,  # 1 hour cache
    max_size=1000
)

# 30-40% of requests hit cache → 30-40% cost reduction
# $202.50/month → $121.50-$141.75/month savings
```

---

## 🎯 Cost Optimization Quick Wins

TTA.dev primitives help you maximize value from paid models:

### 1. **Cache Expensive Calls** (30-40% cost reduction)
Use `CachePrimitive` to avoid redundant API calls for identical inputs.
- **Savings:** $60-80/month on a $200/month budget
- **See:** [Cost Optimization Patterns Guide](cost-optimization-patterns.md#pattern-1-cache--router)

### 2. **Route to Cheaper Models** (20-50% cost reduction)
Use `RouterPrimitive` to route simple tasks to cheaper models (GPT-4o-mini, Gemini Flash).
- **Savings:** $40-100/month on a $200/month budget
- **See:** [Cost Optimization Patterns Guide](cost-optimization-patterns.md#pattern-1-cache--router)

### 3. **Fallback to Free Models** (Reliability + Cost Control)
Use `FallbackPrimitive` to start with paid models, fall back to free when budget exceeded.
- **Savings:** Prevents unexpected overages
- **See:** [Cost Optimization Patterns Guide](cost-optimization-patterns.md#pattern-2-fallback-paid--free)

### 4. **Retry with Exponential Backoff** (Prevent Wasted Calls)
Use `RetryPrimitive` to avoid wasting API calls on transient failures.
- **Savings:** 5-10% reduction in failed requests
- **See:** [Cost Optimization Patterns Guide](cost-optimization-patterns.md#pattern-4-retry-with-cost-control)

### 📚 For Detailed Implementation

See the comprehensive [**Cost Optimization Patterns Guide**](cost-optimization-patterns.md) for:
- Production-ready code examples
- Real-world case studies
- Monitoring and alerting best practices
- Troubleshooting common issues (e.g., Gemini Pro → Flash downgrades)

---

## Provider Details

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

### Cost Optimization
- **🎯 Cost Optimization Patterns Guide:** [cost-optimization-patterns.md](cost-optimization-patterns.md) - Detailed implementation patterns for reducing LLM costs with TTA.dev primitives

### LLM Selection
- **LLM Selection Guide:** [llm-selection-guide.md](llm-selection-guide.md) - Decision matrix for choosing the right LLM
- **Integration Primitives Quick Reference:** [integration-primitives-quickref.md](integration-primitives-quickref.md) - Quick reference for all integration primitives

### Implementation
- **OpenAI Primitive:** [`platform/primitives/src/tta_dev_primitives/integrations/openai_primitive.py`](../../platform/primitives/src/tta_dev_primitives/integrations/openai_primitive.py)
- **Anthropic Primitive:** [`platform/primitives/src/tta_dev_primitives/integrations/anthropic_primitive.py`](../../platform/primitives/src/tta_dev_primitives/integrations/anthropic_primitive.py)
- **Ollama Primitive:** [`platform/primitives/src/tta_dev_primitives/integrations/ollama_primitive.py`](../../platform/primitives/src/tta_dev_primitives/integrations/ollama_primitive.py)
- **Cache Primitive:** [`platform/primitives/src/tta_dev_primitives/performance/cache.py`](../../platform/primitives/src/tta_dev_primitives/performance/cache.py)
- **Router Primitive:** [`platform/primitives/src/tta_dev_primitives/core/routing.py`](../../platform/primitives/src/tta_dev_primitives/core/routing.py)
- **Fallback Primitive:** [`platform/primitives/src/tta_dev_primitives/recovery/fallback.py`](../../platform/primitives/src/tta_dev_primitives/recovery/fallback.py)

---

**Last Updated:** October 30, 2025
**For:** AI Agents & Developers (all skill levels)
**Maintained by:** TTA.dev Team

**⚠️ Important:** Free tier limits change frequently. Always verify current limits on provider websites before relying on this information for production use.
