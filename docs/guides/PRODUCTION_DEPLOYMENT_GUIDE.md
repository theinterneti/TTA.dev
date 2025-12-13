# TTA.dev API Production Deployment Guide

**Upgrade from mock to real Gemini AI in 3 minutes**

---

## 🎯 Quick Start

### Current Status: Mock Mode ✅

Your API server is working in **mock mode** with demonstration responses. This is perfect for:
- Testing the n8n integration
- Validating the workflow
- Understanding the API structure
- Demonstrating to stakeholders

### Upgrade to Production: Real Gemini AI 🚀

When ready for real AI analysis, follow these steps:

---

## Step 1: Get Free Gemini API Key (2 minutes)

1. **Visit Gemini AI Studio:**
   ```
   https://ai.google.dev/
   ```

2. **Click "Get API Key"**
   - Sign in with your Google account
   - Click "Create API Key"
   - Select your Google Cloud project (or create new one)

3. **Copy Your Key:**
   ```
   AIza...your_key_here
   ```

   ⚠️ Save it somewhere secure - you won't see it again!

4. **Free Tier Limits:**
   - **15 requests per minute** (plenty for development)
   - **1,500 requests per day**
   - **1 million tokens per day**
   - Perfect for testing and small production workloads

---

## Step 2: Configure API Key (30 seconds)

### Option A: Environment Variable (Recommended for Development)

```bash
# Add to your ~/.bashrc or ~/.zshrc
export GEMINI_API_KEY='your_key_here'

# Or just for this session:
export GEMINI_API_KEY='your_key_here'
```

### Option B: .env File (Recommended for Production)

```bash
# Create .env file in TTA.dev root
echo "GEMINI_API_KEY=your_key_here" >> .env

# Load it
source .env
```

### Option C: TTA Secrets Manager (Most Secure)

```bash
# Create secrets file
mkdir -p tta_secrets/.secrets
echo "GEMINI_API_KEY=your_key_here" > tta_secrets/.secrets/secrets.env

# Or use the secrets manager
python3 -c "
from tta_secrets import SecretsManager
manager = SecretsManager()
manager.set_secret('GEMINI_API_KEY', 'your_key_here')
"
```

---

## Step 3: Restart Production Server (30 seconds)

```bash
# Stop old server
pkill -f tta_api_server

# Start production server
./scripts/api/start_production_api.sh
```

**You should see:**
```
✅ Gemini API key found
✅ TTA.dev primitives loaded
✅ Using real Gemini LLM
✅ Production primitives active
  ✅ CachePrimitive (1 hour TTL, 1000 entries)
  ✅ RetryPrimitive (3 retries, exponential backoff)

🚀 TTA.dev API Server - Production Ready
Gemini: ✅ ENABLED
Primitives: ✅ ACTIVE
Cache: ✅ ENABLED
```

---

## Step 4: Test Production API (1 minute)

```bash
./scripts/api/test_production_api.sh
```

**Expected results:**
```
✅ Gemini ENABLED - using real AI
✅ Analysis successful
   Tokens used: 247
   Estimated cost: $0.000037
✅ Cache working (2nd call faster)
🎉 All tests passed! (9/9)
```

---

## What Changes in Production Mode?

### Mock Mode (Current) 🤖
```json
{
  "response": "🤖 MOCK MODE - Gemini API key not configured...",
  "model_used": "mock-demo",
  "tokens_used": 42,
  "estimated_cost_usd": 0.0
}
```

### Production Mode (After Setup) 🚀
```json
{
  "response": "Based on the repository analysis, here are the key insights:\n\n1. Health Score: 85/100...",
  "model_used": "gemini-1.5-flash",
  "tokens_used": 247,
  "estimated_cost_usd": 0.000037
}
```

**Key Differences:**
- ✅ **Real AI analysis** instead of static demo text
- ✅ **Actual cost tracking** for budget management
- ✅ **Token usage** for optimization
- ✅ **Better quality responses** tailored to your data

---

## Production Features Automatically Enabled

Once Gemini is configured, these TTA.dev primitives activate:

### 1. CachePrimitive (40-60% Cost Reduction)
```python
cached_llm = CachePrimitive(
    primitive=llm,
    ttl_seconds=3600,  # 1 hour
    max_size=1000      # 1000 cached responses
)
```

**Benefits:**
- Identical queries use cached responses
- Reduce API calls by 40-60%
- 100x faster response time (cache hit)
- Automatic TTL expiration

**Example:**
```bash
# First call: 247 tokens, 850ms
curl -X POST http://localhost:8000/api/v1/analyze -d '{"prompt":"What is TTA.dev?"}'

# Second call (within 1 hour): 0 tokens, 8ms (cached!)
curl -X POST http://localhost:8000/api/v1/analyze -d '{"prompt":"What is TTA.dev?"}'
```

### 2. RetryPrimitive (Resilience)
```python
resilient_llm = RetryPrimitive(
    primitive=cached_llm,
    max_retries=3,
    backoff_strategy="exponential"
)
```

**Benefits:**
- Automatic retry on transient failures
- Exponential backoff (1s, 2s, 4s)
- Jitter to prevent thundering herd
- Graceful error handling

**Example:**
```
Attempt 1: Network timeout
Attempt 2: (1s later) API rate limit
Attempt 3: (2s later) Success!
```

### 3. Cost Tracking
```json
{
  "tokens_used": 247,
  "estimated_cost_usd": 0.000037
}
```

**Track your spending:**
- Input tokens: $0.15 per 1M
- Output tokens: $0.60 per 1M
- Typical request: $0.00003 - $0.0001
- 10,000 requests: ~$0.50 - $1.00

---

## Troubleshooting

### Error: "GEMINI_API_KEY must be provided"

**Solution:**
```bash
# Check if set
echo $GEMINI_API_KEY

# If empty, export it
export GEMINI_API_KEY='your_key_here'

# Restart server
./scripts/api/start_production_api.sh
```

### Error: "API key not valid"

**Solution:**
1. Verify key is correct (should start with `AIza`)
2. Check you copied the entire key
3. Generate a new key if needed: https://ai.google.dev/

### Error: "Rate limit exceeded"

**Free tier limits:**
- 15 RPM (requests per minute)
- 1,500 RPD (requests per day)

**Solutions:**
1. **Use caching** (already enabled) - reduces API calls by 40-60%
2. **Batch requests** - combine multiple queries
3. **Upgrade to paid tier** - 1,000 RPM, no daily limit

### Server shows "Using mock LLM"

**Check:**
1. `echo $GEMINI_API_KEY` - should show your key
2. Restart server - may need to reload environment
3. Check logs - look for "✅ Gemini API key found"

---

## Cost Estimation

### Development/Testing
- **Requests:** ~100/day
- **Cost:** ~$0.01/day
- **Monthly:** ~$0.30

### Production (Small)
- **Requests:** ~1,000/day
- **Cache hit rate:** 50%
- **Actual API calls:** ~500/day
- **Cost:** ~$0.05/day
- **Monthly:** ~$1.50

### Production (Medium)
- **Requests:** ~10,000/day
- **Cache hit rate:** 60%
- **Actual API calls:** ~4,000/day
- **Cost:** ~$0.40/day
- **Monthly:** ~$12

**With TTA.dev primitives:**
- Cache reduces costs by 40-60%
- Retry avoids lost requests
- Batch processing optimizes token usage

---

## Production Checklist

Before going live:

- [ ] Gemini API key configured
- [ ] Production server tested (`test_production_api.sh`)
- [ ] n8n workflow updated and working
- [ ] Cache settings reviewed (TTL, size)
- [ ] Retry strategy configured
- [ ] Cost tracking enabled
- [ ] Monitoring setup (optional)
- [ ] Rate limits understood

---

## Next Enhancements (Optional)

### 1. Add FallbackPrimitive

```python
from tta_dev_primitives.recovery import FallbackPrimitive

workflow = FallbackPrimitive(
    primary=gemini_llm,
    fallbacks=[openrouter_llm, anthropic_llm]
)
```

**Benefit:** High availability - if Gemini is down, use backup

### 2. Add Monitoring

```python
from observability_integration import initialize_observability

initialize_observability(
    service_name="tta-api",
    enable_prometheus=True
)
```

**Benefit:** Track metrics in Grafana

### 3. Add Authentication

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")
```

**Benefit:** Secure your API from unauthorized access

---

## Summary

**Current State:**
- ✅ Mock mode working
- ✅ n8n integration complete
- ✅ All tests passing

**After Gemini Setup (~3 minutes):**
- ✅ Real AI analysis
- ✅ Automatic caching (40-60% cost reduction)
- ✅ Automatic retry (resilience)
- ✅ Cost tracking
- ✅ Production ready

**Total Time:** 3 minutes
**Total Cost:** ~$0.01/day (development), ~$1.50/month (small production)

---

**Ready to upgrade?** Get your Gemini key and run `./scripts/api/start_production_api.sh`!

**Questions?** Check the main guides:
- `TTA_API_COMPLETE.md` - Complete API documentation
- `TTA_API_N8N_INTEGRATION_GUIDE.md` - n8n integration details
- `N8N_GITHUB_CREDENTIAL_SETUP.md` - Credential configuration


---
**Logseq:** [[TTA.dev/Docs/Guides/Production_deployment_guide]]
