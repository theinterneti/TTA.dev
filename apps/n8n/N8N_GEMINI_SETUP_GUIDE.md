# Google Gemini Setup Guide for n8n

**Complete guide to configuring and using Google Gemini in your n8n workflows**

---

## 🎯 Overview

Your **GitHub Health Dashboard** workflow uses Google Gemini Chat Model nodes for AI-powered analysis. This guide will help you:

1. Set up Google Gemini API credentials
2. Configure the credentials in n8n
3. Test the integration
4. Understand cost and usage limits

---

## 📋 Prerequisites

- ✅ n8n server running (localhost:5678) - **DONE**
- ✅ Workflows imported - **DONE**
- ⏳ Google Cloud account (free tier available)
- ⏳ Google AI Studio account (alternative, easier setup)

---

## 🔑 Getting Google Gemini API Access

You have **two options** for accessing Gemini:

### Option 1: Google AI Studio (Recommended for Testing)

**Pros:**
- ✅ Free tier available
- ✅ Simple setup (no billing required)
- ✅ Immediate API key generation
- ✅ Good for development and testing

**Cons:**
- ⚠️ Lower rate limits
- ⚠️ Not for production at scale

**Setup Steps:**

1. **Go to Google AI Studio:**
   - Visit: https://aistudio.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key:**
   - Click "Get API key"
   - Click "Create API key in new project" (or select existing project)
   - Copy the API key (starts with `AIza...`)
   - **⚠️ IMPORTANT:** Save this key securely - you can't view it again

3. **Free Tier Limits (as of Nov 2025):**
   - **Gemini 1.5 Flash:** 15 requests/minute, 1 million tokens/day
   - **Gemini 1.5 Pro:** 2 requests/minute, 50 requests/day
   - **No credit card required**

### Option 2: Google Cloud Platform (For Production)

**Pros:**
- ✅ Higher rate limits
- ✅ Production-ready
- ✅ Enterprise features
- ✅ SLA guarantees

**Cons:**
- ⚠️ Requires billing setup
- ⚠️ More complex configuration
- ⚠️ Costs apply beyond free tier

**Setup Steps:**

1. **Create Google Cloud Project:**
   - Go to: https://console.cloud.google.com/
   - Create new project or select existing
   - Note your Project ID

2. **Enable Vertex AI API:**
   - In Cloud Console, search for "Vertex AI API"
   - Click "Enable"
   - Wait for activation (may take a few minutes)

3. **Create Service Account:**
   - Navigate to: IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name: `n8n-gemini-access`
   - Grant role: "Vertex AI User"
   - Click "Create and Continue" → "Done"

4. **Generate JSON Key:**
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download the JSON file (keep it secure!)

5. **Billing Setup:**
   - Navigate to: Billing → Link a billing account
   - **Free Tier:** $300 credit for new users
   - **Pay-as-you-go:** After free tier

---

## 🔧 Configuring Credentials in n8n

### For Google AI Studio (Simpler)

1. **Open n8n UI:**
   ```bash
   # If not already open:
   http://localhost:5678
   ```

2. **Navigate to Credentials:**
   - Click your user icon (top right)
   - Select "Settings"
   - Click "Credentials" in left sidebar

3. **Create New Credential:**
   - Click "Add Credential"
   - Search for "Google Gemini"
   - Select "Google Gemini Chat Model"

4. **Configure API Key:**
   ```
   Credential Name: Google Gemini (AI Studio)
   API Key: [paste your AIza... key]
   ```

5. **Test Connection:**
   - Click "Save"
   - n8n will validate the key

### For Google Cloud Platform (Vertex AI)

1. **Create Credential:**
   - Click "Add Credential"
   - Search for "Google Vertex"
   - Select "Google Vertex Chat Model"

2. **Configure Service Account:**
   ```
   Credential Name: Google Vertex AI (Production)
   Service Account Key: [paste entire JSON content from downloaded file]
   Project ID: [your GCP project ID]
   Region: us-central1 (or your preferred region)
   ```

3. **Test Connection:**
   - Click "Save"
   - n8n will validate credentials

---

## 🧪 Testing Your Setup

### Method 1: Use the Safe Test Workflow (Already Created)

You have a pre-created test workflow:

```bash
# In n8n UI:
# 1. Go to Workflows
# 2. Find "LangChain_Gemini_Test_Safe"
# 3. Click to open
# 4. Click "Execute Workflow"
```

**Expected Result:**
- ✅ Workflow executes without errors
- ✅ Gemini responds to test prompt
- ✅ You see the AI-generated response

### Method 2: Create a Simple Test Workflow

1. **Create New Workflow:**
   - Click "Add Workflow" in n8n

2. **Add Nodes:**
   - **Manual Trigger** → Start workflow manually
   - **Basic LLM Chain** → Connect to trigger
     - Connect **Google Gemini Chat Model** sub-node
     - Select your credential
     - Set model: `gemini-1.5-flash` (fastest, cheapest)
   - Set prompt: `Say "Hello from Gemini!"`

3. **Execute:**
   - Click "Execute Workflow"
   - Check output

**Example Output:**
```json
{
  "response": "Hello from Gemini! How can I help you today?"
}
```

---

## 🎨 Using Gemini in Your GitHub Workflow

Your **GitHub Health Dashboard** workflow structure:

```
GitHub Trigger
   ↓
Get Repository Data
   ↓
AI Agent (Google Gemini)
   ├─ Google Gemini Chat Model ← NEEDS CREDENTIALS
   └─ Simple Memory
   ↓
Analyze Health Metrics
   ↓
Format Results
   ↓
Post to Slack/Discord
```

### Steps to Activate:

1. **Open Workflow:**
   - Go to: Workflows → `n8n_github_health_dashboard`

2. **Locate Gemini Nodes:**
   - Find all "Google Gemini Chat Model" sub-nodes
   - They'll show as disconnected/red if unconfigured

3. **Configure Each Node:**
   - Click on each Gemini node
   - Under "Credential to connect with:"
   - Select your created credential
   - Choose model version

4. **Select Model:**
   - **For Testing:** `gemini-1.5-flash` (fast, cheap)
   - **For Production:** `gemini-1.5-pro` (higher quality)

5. **Configure Parameters:**
   ```
   Model: gemini-1.5-flash
   Temperature: 0.7 (creativity level, 0-1)
   Max Tokens: 1024 (response length)
   ```

6. **Save Workflow:**
   - Click "Save" (Ctrl+S)

7. **Test Execution:**
   - Change workflow to `active: false` (keep it safe)
   - Click "Execute Workflow"
   - Monitor execution

---

## 💰 Understanding Costs

### Google AI Studio (Free Tier)

**Gemini 1.5 Flash:**
- Free: 15 RPM, 1M tokens/day
- After limits: Not available (upgrade to GCP)

**Gemini 1.5 Pro:**
- Free: 2 RPM, 50 requests/day
- After limits: Not available (upgrade to GCP)

**Your GitHub Workflow:**
- Estimated: 10-20 requests/day (checking health metrics)
- ✅ **Should fit in free tier**

### Google Cloud Platform (Vertex AI)

**Pricing (as of Nov 2025):**

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Gemini 1.5 Flash | $0.075 | $0.30 |
| Gemini 1.5 Pro | $1.25 | $5.00 |

**Example Calculation (GitHub Workflow):**

```
Assumptions:
- 20 executions/day
- 500 input tokens/execution (repo data)
- 1000 output tokens/execution (analysis)

Using Gemini 1.5 Flash:
Input:  20 * 500 * 30 days = 300,000 tokens/month
        (300,000 / 1,000,000) * $0.075 = $0.02

Output: 20 * 1000 * 30 days = 600,000 tokens/month
        (600,000 / 1,000,000) * $0.30 = $0.18

Total: ~$0.20/month
```

**✅ Recommendation:** Start with Google AI Studio free tier, migrate to GCP if needed.

---

## 🛡️ Best Practices

### 1. API Key Security

**✅ DO:**
- Store keys in n8n credentials (encrypted)
- Rotate keys every 90 days
- Use separate keys for dev/prod

**❌ DON'T:**
- Hardcode keys in workflows
- Share keys in public repos
- Use production keys in testing

### 2. Rate Limit Management

**Strategies:**
- Add delays between requests
- Implement retry logic with backoff
- Monitor usage via Google Cloud Console
- Set up alerts for quota usage

**n8n Implementation:**
```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 5000
}
```

### 3. Error Handling

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `UNAUTHENTICATED` | Invalid API key | Regenerate key, update credential |
| `RESOURCE_EXHAUSTED` | Rate limit exceeded | Reduce frequency, upgrade tier |
| `INVALID_ARGUMENT` | Malformed request | Check prompt format, token limits |
| `PERMISSION_DENIED` | API not enabled | Enable Vertex AI API in GCP |

**Error Handling Pattern:**
```
Try: Call Gemini
Catch Error:
  → If rate limit: Wait 60s, retry
  → If auth error: Alert admin
  → If other: Log and fallback
```

### 4. Prompt Optimization

**Tips for Better Results:**
- Be specific and clear
- Provide context
- Specify output format
- Use examples (few-shot learning)

**Example - GitHub Analysis Prompt:**
```
Analyze this GitHub repository data and provide:
1. Overall health score (0-100)
2. Top 3 strengths
3. Top 3 areas for improvement
4. Recommended next actions

Repository Data:
{repository_stats}

Format your response as JSON:
{
  "health_score": <number>,
  "strengths": [<string>, ...],
  "improvements": [<string>, ...],
  "actions": [<string>, ...]
}
```

### 5. Model Selection

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| **Simple classification** | Gemini 1.5 Flash | Fast, cheap, sufficient quality |
| **Complex analysis** | Gemini 1.5 Pro | Better reasoning, deeper insights |
| **High volume** | Gemini 1.5 Flash | Lower cost per request |
| **Streaming responses** | Either | Both support streaming |

---

## 🔍 Monitoring & Debugging

### In n8n

1. **Execution History:**
   - Click "Executions" in left sidebar
   - View all workflow runs
   - Check success/failure status

2. **Node Output:**
   - Click on any executed node
   - View input/output data
   - Check token usage (if available)

3. **Error Logs:**
   - Failed executions show error details
   - Check credential configuration
   - Verify API quotas

### In Google Cloud (for Vertex AI)

1. **Navigate to Vertex AI:**
   - Console → Vertex AI → Model Garden

2. **View Metrics:**
   - Request count
   - Token usage
   - Error rates
   - Latency

3. **Set Up Alerts:**
   - Billing alerts for cost thresholds
   - Quota alerts for rate limits

### In Google AI Studio

1. **Dashboard:**
   - Visit: https://aistudio.google.com/
   - View recent requests
   - Check quota usage

2. **Limitations:**
   - Less detailed than GCP
   - Basic usage stats only

---

## 🚀 Next Steps

### Immediate (Testing):

- [ ] Create Google AI Studio API key
- [ ] Configure credential in n8n
- [ ] Test with safe workflow
- [ ] Execute GitHub Health Dashboard (once, manually)

### Short-term (Validation):

- [ ] Verify Gemini responses are high quality
- [ ] Check token usage vs. expectations
- [ ] Ensure free tier limits are sufficient
- [ ] Add error handling to workflow

### Long-term (Production):

- [ ] Migrate to GCP Vertex AI (if needed for scale)
- [ ] Set up monitoring and alerts
- [ ] Implement rate limiting
- [ ] Optimize prompts for cost/quality
- [ ] Enable workflow (set `active: true`)

---

## 🆘 Troubleshooting

### Issue: "Invalid API Key"

**Symptoms:**
- Workflow fails with authentication error
- Credential test fails

**Solutions:**
1. Regenerate API key in Google AI Studio
2. Update credential in n8n
3. Clear browser cache
4. Restart n8n server

---

### Issue: "Rate Limit Exceeded"

**Symptoms:**
- Error: `RESOURCE_EXHAUSTED`
- Requests failing after initial success

**Solutions:**
1. Check quota usage in dashboard
2. Reduce workflow execution frequency
3. Upgrade to paid tier (GCP)
4. Add delays between requests

---

### Issue: "Gemini Node Not Found"

**Symptoms:**
- Workflow shows "Unrecognized node"
- Can't find Gemini in node palette

**Solutions:**
1. Ensure n8n version ≥ 1.0 (LangChain support)
2. Update n8n: `npm update -g n8n`
3. Search for "Google Gemini Chat Model" (exact name)
4. Check if LangChain nodes installed

---

### Issue: "Low Quality Responses"

**Symptoms:**
- Gemini returns generic/unhelpful answers
- Missing expected analysis

**Solutions:**
1. Improve prompt specificity
2. Provide more context in prompt
3. Add few-shot examples
4. Increase temperature (more creativity)
5. Switch to Gemini 1.5 Pro (higher quality)

---

## 📚 Additional Resources

### Documentation

- **Google AI Studio:** https://ai.google.dev/
- **Vertex AI Docs:** https://cloud.google.com/vertex-ai/docs
- **n8n Gemini Guide:** https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatgooglegemini/
- **Gemini API Docs:** https://ai.google.dev/gemini-api/docs

### Tutorials

- **Getting Started with Gemini:** https://ai.google.dev/gemini-api/docs/get-started/tutorial
- **n8n LangChain Tutorial:** https://docs.n8n.io/advanced-ai/langchain/
- **Prompt Engineering:** https://ai.google.dev/gemini-api/docs/prompting-strategies

### Community

- **n8n Community (Gemini Tag):** https://community.n8n.io/tag/gemini
- **Google AI Forum:** https://discuss.ai.google.dev/

---

## 🎯 Quick Reference

### API Key Format

**Google AI Studio:**
```
AIza... (39 characters)
```

**GCP Service Account:**
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  ...
}
```

### Model Names

```
gemini-1.5-flash      # Fast, cheap, good quality
gemini-1.5-pro        # Slower, expensive, best quality
gemini-1.0-pro        # Legacy, not recommended
```

### Credential Configuration Checklist

- [ ] API key or Service Account JSON obtained
- [ ] Credential created in n8n
- [ ] Credential selected in workflow nodes
- [ ] Model version specified
- [ ] Test execution successful
- [ ] Error handling configured

---

**Last Updated:** November 9, 2025
**Your Setup Status:**
- ✅ n8n server running
- ✅ Workflows imported
- ⏳ Gemini credentials pending
- ⏳ First test execution pending


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_gemini_setup_guide]]
