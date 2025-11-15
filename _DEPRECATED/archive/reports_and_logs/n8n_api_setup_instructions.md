# N8N GitHub Health Dashboard - API Setup Instructions

## Current Status ✅

- n8n service: Running at <http://localhost:5678>
- Workflow: Successfully imported as "GitHub Health Dashboard"
- Todo: API keys found but need fresh/working credentials

## Required Actions

### 🔐 Step 1: Get New GitHub Personal Access Token

1. **Go to GitHub:** <https://github.com/settings/tokens>
2. **Click:** "Generate new token (classic)"
3. **Configure Token:**
   - **Note:** "n8n GitHub Health Dashboard"
   - **Expiration:** 30 days (recommended for testing)
   - **Select scopes:** ✅ Check these boxes:
     - `repo` (Full control of private repositories)
     - `read:org` (Read org and team membership)
     - `user:email` (Access commits user email)
4. **Generate & Copy:** The token (starts with `ghp_`)

### 🤖 Step 2: Get New Gemini API Key

1. **Go to Google AI Studio:** <https://aistudio.google.com>
2. **Sign in** with your Google account
3. **Get API Key:**
   - Click "Get API key" in left sidebar
   - Click "Create API key"
   - Select your Google Cloud project
   - Copy the generated key (starts with `AIza`)

## Next Steps After Getting API Keys

Once you provide the new API keys, I will:

1. **Configure n8n credentials** automatically
2. **Test both APIs** for connectivity
3. **Update workflow nodes** with the new credentials
4. **Execute testing** to verify everything works
5. **Enable 6-hour automated scheduling**

## Quick Test Commands

You can verify the tokens work before providing them:

```bash
# Test GitHub token
curl -H "Authorization: token YOUR_GITHUB_TOKEN" https://api.github.com/repos/theinterneti/TTA.dev

# Should return: {"name": "TTA.dev", "stargazers_count": X, ...}
```

```bash
# Test Gemini API
curl -X POST -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_GEMINI_KEY"

# Should return JSON response with generated text
```

## 🎯 Final Result

With working API keys, your n8n dashboard will:

- ✅ Monitor TTA.dev repository every 6 hours
- ✅ Generate health scores (0-100) with letter grades (A-F)
- ✅ Provide AI-powered insights via Gemini
- ✅ Track community engagement, code quality metrics
- ✅ Send automated alerts for repository health issues
- ✅ Show trends and recommendations for improvement

**Please provide both new API keys and I'll complete the setup in 2-3 minutes!**
