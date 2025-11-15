# Cline Configuration for TTA.dev

**Production Configuration Guide**

**Date:** November 6, 2025
**Status:** Active Configuration

---

## Overview

TTA.dev uses a **dual-model configuration** for optimal cost-performance balance:

- **VS Code Extension**: DeepSeek R1 (Plan) + Llama 4 Scout (Act)
- **CLI**: Mistral Small 3.2

This configuration provides excellent results at minimal cost (~$5/month).

---

## VS Code Extension Configuration

### Current Setup

**Provider:** OpenRouter
**Plan Model:** DeepSeek R1
**Act Model:** Llama 4 Scout

### Configuration Steps

1. Open Cline panel in VS Code
2. Click Settings (gear icon)
3. Select "OpenRouter" as API Provider
4. Enter OpenRouter API Key
5. Configure models:

```json
{
  "apiProvider": "openrouter",
  "openRouterApiKey": "sk-or-v1-...",
  "apiModelId": "deepseek/deepseek-r1",
  "actApiProvider": "openrouter",
  "actApiModelId": "meta-llama/llama-4-scout"
}
```

### Why These Models?

**DeepSeek R1 (Planning):**
- ✅ Excellent reasoning and task decomposition
- ✅ Strong understanding of complex requirements
- ✅ Cost: ~$0.14/1M input tokens, ~$0.28/1M output tokens
- ✅ Best for: Architecture decisions, planning, analysis

**Llama 4 Scout (Execution):**
- ✅ Fast code generation
- ✅ Good at following specific instructions
- ✅ Cost: ~$0.02/1M tokens (very affordable)
- ✅ Best for: Writing code, making edits, running tests

**Combined Benefits:**
- Smart planning with DeepSeek R1
- Efficient execution with Llama 4 Scout
- Total cost: ~$2-5/month for moderate use
- Better results than single model approach

---

## CLI Configuration

### Current Setup

**Provider:** OpenRouter
**Model:** Mistral Small 3.2

### Configuration Steps

```bash
# Set provider
cline config set api-provider openrouter

# Set API key (same as VS Code extension)
cline config set api-key sk-or-v1-YOUR_KEY_HERE

# Set model
cline config set api-model-id mistralai/mistral-small-3.2

# Verify
cline config list
```

### Why Mistral Small 3.2?

- ✅ Fast response times (~2-3 seconds)
- ✅ Very cost-effective (~$0.10/1M tokens)
- ✅ Good code quality
- ✅ Perfect for automation and scripting
- ✅ Reliable for GitHub Actions

---

## OpenRouter Setup

### 1. Create Account

1. Go to https://openrouter.ai
2. Sign up with GitHub or email
3. Verify email

### 2. Get API Key

1. Navigate to "Keys" section
2. Click "Create Key"
3. Name it "TTA.dev Development"
4. Copy key (starts with `sk-or-v1-`)
5. Store securely (you won't see it again)

### 3. Add Credits (Optional)

OpenRouter offers free tier credits for testing:

- New users: $1 free credit
- Many models available on free tier
- Pay-as-you-go after free credits

**Recommended:** Add $10-20 for uninterrupted development

### 4. Monitor Usage

Dashboard: https://openrouter.ai/activity

- View daily usage
- Set budget alerts
- Track cost per model
- Export usage data

---

## Cost Analysis

### Expected Monthly Costs

**Light Usage (10 tasks/day):**
- DeepSeek R1: ~$0.50
- Llama 4 Scout: ~$0.30
- Mistral Small (CLI): ~$0.20
- **Total: ~$1/month**

**Moderate Usage (30 tasks/day):**
- DeepSeek R1: ~$2.00
- Llama 4 Scout: ~$1.00
- Mistral Small (CLI): ~$0.50
- **Total: ~$3.50/month**

**Heavy Usage (100 tasks/day):**
- DeepSeek R1: ~$7.00
- Llama 4 Scout: ~$3.00
- Mistral Small (CLI): ~$2.00
- **Total: ~$12/month**

**vs. Claude 3.7 Sonnet:**
- Light: ~$30/month
- Moderate: ~$100/month
- Heavy: ~$400/month

**Savings: 90-95%** while maintaining excellent quality.

---

## Model Comparison

| Feature | DeepSeek R1 | Llama 4 Scout | Mistral Small | Claude 3.7 |
|---------|-------------|---------------|---------------|------------|
| **Planning** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Coding** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Context** | 64K | 128K | 32K | 200K |
| **Best For** | Analysis | Coding | Scripts | Everything |

---

## Configuration Files

### VS Code Settings Location

**Linux/macOS:**
```bash
~/.config/Code/User/settings.json
```

**Windows:**
```
%APPDATA%\Code\User\settings.json
```

**Cline Settings Section:**

```json
{
  "cline.apiProvider": "openrouter",
  "cline.openRouterApiKey": "sk-or-v1-...",
  "cline.apiModelId": "deepseek/deepseek-r1",
  "cline.actApiProvider": "openrouter",
  "cline.actApiModelId": "meta-llama/llama-4-scout",
  "cline.mcpEnabled": true
}
```

### CLI Config Location

**Linux/macOS:**
```bash
~/.clinerc
```

**Windows:**
```
%USERPROFILE%\.clinerc
```

**Contents:**

```ini
api-provider=openrouter
api-key=sk-or-v1-...
api-model-id=mistralai/mistral-small-3.2
```

---

## MCP Integration

Cline automatically detects MCP servers from:

```bash
~/.config/mcp/mcp_settings.json
```

**TTA.dev MCP Servers Available:**

- ✅ Context7 (library documentation)
- ✅ Grafana (observability)
- ✅ Pylance (Python tools)
- ✅ Logseq (knowledge base)
- ✅ Database Client (SQL operations)

**No additional configuration needed** - Cline discovers these automatically.

---

## Troubleshooting

### Issue: API Key Invalid

**Solution:**

```bash
# Verify key format
echo $OPENROUTER_API_KEY  # Should start with sk-or-v1-

# Re-configure
cline config set api-key sk-or-v1-YOUR_KEY_HERE

# Test
cline "Hello, test message"
```

### Issue: Model Not Available

**Solution:**

```bash
# Check available models
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Verify model ID exactly matches
cline config set api-model-id deepseek/deepseek-r1  # Exact case
```

### Issue: High Costs

**Solution:**

1. Switch to cheaper models:
   ```bash
   # CLI: Use Mistral Small
   cline config set api-model-id mistralai/mistral-small-3.2
   ```

2. Set budget alerts in OpenRouter dashboard

3. Use local models for simple tasks:
   ```bash
   cline config set api-provider ollama
   cline config set api-model-id codellama
   ```

### Issue: Slow Response

**Models ranked by speed:**

1. ⚡ Llama 4 Scout (fastest)
2. ⚡ Mistral Small 3.2
3. 🔄 DeepSeek R1
4. 🐌 Claude 3.7 Sonnet

**For speed-critical tasks:** Use Llama 4 Scout or Mistral Small

---

## Best Practices

### 1. Use Right Model for Right Task

**Planning/Analysis → DeepSeek R1:**
```
"Review the architecture of tta-dev-primitives and suggest improvements"
```

**Code Generation → Llama 4 Scout:**
```
"Add type hints to all functions in cache.py"
```

**Quick Scripts → Mistral Small (CLI):**
```bash
cat error.log | cline -y "Fix the issues in this log"
```

### 2. Monitor Usage Weekly

```bash
# Check OpenRouter dashboard
open https://openrouter.ai/activity

# Export usage data
curl https://openrouter.ai/api/v1/usage \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### 3. Set Budget Alerts

1. Go to OpenRouter Settings
2. Set monthly budget: $10-20
3. Enable email alerts at 50%, 80%, 100%

### 4. Use Local Models for Experimentation

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull codellama
ollama pull deepseek-coder

# Configure Cline CLI for local
cline config set api-provider ollama
cline config set api-model-id codellama

# Test
cline "Write a hello world function"
```

---

## Upgrading Configuration

### When to Upgrade to Premium Models

**Consider upgrading if:**

- Budget allows ($100-400/month)
- Need maximum code quality
- Working on critical/complex features
- Team collaboration requires consistency

**Premium Setup:**

```json
{
  "apiProvider": "anthropic",
  "apiKey": "sk-ant-...",
  "apiModelId": "claude-3-5-sonnet-20241022"
}
```

### Hybrid Approach

**Development:** OpenRouter (DeepSeek + Llama)
**Production/Critical:** Claude 3.7 Sonnet

Switch per task based on importance.

---

## Team Configuration

### Recommended Team Setup

**Individual Developers:**
- VS Code: DeepSeek R1 + Llama 4 Scout
- CLI: Mistral Small 3.2
- Cost: ~$3-5/developer/month

**Team Lead/Senior:**
- Option for Claude 3.7 Sonnet on complex tasks
- Cost: ~$20-50/month

**CI/CD:**
- CLI only: Mistral Small 3.2
- Cost: ~$1-2/month

**Total Team Cost (5 developers):**
- ~$25-35/month vs $500-2000/month with Claude

---

## Verification

### Test Your Configuration

**VS Code Extension:**

1. Open Cline panel
2. Type: "Hello, can you confirm you're using DeepSeek R1 for planning?"
3. Verify response mentions DeepSeek

**CLI:**

```bash
# Test CLI
cline "What model are you using?"

# Should respond with Mistral Small 3.2
```

**MCP Integration:**

```bash
# Test Context7
cline "Using Context7, find httpx async documentation"

# Should call Context7 MCP server
```

---

## Resources

- **OpenRouter:** https://openrouter.ai
- **DeepSeek R1:** https://openrouter.ai/models/deepseek/deepseek-r1
- **Llama 4 Scout:** https://openrouter.ai/models/meta-llama/llama-4-scout
- **Mistral Small:** https://openrouter.ai/models/mistralai/mistral-small-3.2
- **Pricing:** https://openrouter.ai/docs/pricing

---

**Configuration Complete! Ready to collaborate with Cline at 90% cost savings. 🚀💰**
