# n8n Credential Configuration Guide

## Overview

Based on your n8n GitHub Health Dashboard workflow, you need **only 2 credentials** configured. Here's exactly what you need and how to set it up.

## Required Credentials

### 1. GitHub API Credential (REQUIRED)

**Credential Name in n8n:** `GitHub API`

**What it does:**

- Fetches repository information
- Gets issues, pull requests, contributors
- Collects commit activity data

**How to configure:**

1. Go to n8n: <http://localhost:5678>
2. Click **Settings** (gear icon) → **Credentials**
3. Click **Add Credential**
4. Search for **"GitHub"** or **"GitHub API"**
5. Configure:
   - **Name:** `GitHub API` (exact match required)
   - **Access Token:** `GITHUB_PERSONAL_ACCESS_TOKEN` from your .env file
6. **Required Scopes for your token:**
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `user:email` (Access commits user email)

### 2. Gemini API Key (ALREADY CONFIGURED)

**Configuration Type:** Environment Variable

**What it does:**

- Provides AI analysis of repository health
- Generates insights and recommendations

**How it's configured:**

- Your workflow already references `={{$env.GEMINI_API_KEY}}`
- n8n will automatically use the GEMINI_API_KEY from your .env file
- **No additional setup needed!**

## Credentials You DON'T Need

### E2B Keys (NOT REQUIRED)

- `E2B_API_KEY` and `E2B_KEY` from your .env
- These are not used in your current n8n workflow
- You can ignore these for now

### N8N_API_KEY (NOT FOR WORKFLOW)

- This is for n8n's own API access
- Not used in the GitHub Health Dashboard workflow

## Step-by-Step Setup

### Step 1: Set up GitHub Credential

1. **Access n8n:** <http://localhost:5678>
2. **Navigate:** Settings → Credentials → Add Credential
3. **Select:** GitHub API
4. **Configure:**
   - Name: `GitHub API`
   - Access Token: `ghp_YOUR_GITHUB_TOKEN_HERE`
5. **Test:** Click "Test Connection"
6. **Save:** Click "Save"

### Step 2: Verify Environment Variables

1. **In n8n:** Settings → Environment Variables
2. **Check:** `GEMINI_API_KEY` is present
3. **Value:** Should match your .env file

### Step 3: Test Your Workflow

1. **Open:** Your GitHub Health Dashboard workflow
2. **Execute:** Click "Test workflow"
3. **Check:** All nodes should show green checkmarks
4. **Verify:** Dashboard output appears

## Quick Verification

Test your credentials before configuring:

```bash
# Test GitHub token
curl -H "Authorization: token ghp_YOUR_GITHUB_TOKEN_HERE" \
     https://api.github.com/repos/theinterneti/TTA.dev

# Test Gemini API
curl -X POST -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE"
```

## Troubleshooting

### GitHub Credential Issues

- **Error:** "Bad credentials"
- **Solution:** Check token hasn't expired and has correct scopes
- **Solution:** Regenerate token with required scopes

### Gemini API Issues

- **Error:** "API key not valid"
- **Solution:** Verify GEMINI_API_KEY environment variable in n8n
- **Solution:** Check API key hasn't been revoked

### Workflow Execution Issues

- **Error:** Nodes show red X
- **Solution:** Check each node's credential reference matches exactly
- **Solution:** Verify workflow is active and properly connected

## Summary

**You only need to configure 1 credential in n8n:**

✅ **GitHub API** - Using your GITHUB_PERSONAL_ACCESS_TOKEN
✅ **Gemini** - Already configured via environment variable
❌ **E2B** - Not needed for this workflow
❌ **N8N API** - Not needed for this workflow

Once configured, your workflow will automatically:

- Monitor the TTA.dev repository every 6 hours
- Calculate health scores and metrics
- Generate AI-powered insights
- Provide actionable recommendations


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_credential_configuration_guide]]
