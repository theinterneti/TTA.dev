# n8n GitHub Credential Setup Guide

**Fix: "Credentials not found" error in GitHub API nodes**

---

## 🎯 Problem

When running your n8n workflow, the "Get GitHub Repository Stats" node shows:

```
❌ Credentials not found
```

The node configuration shows a red border on "Select Credential" dropdown.

---

## ✅ Solution

### Method 1: Using GitHub API Credential (Recommended)

This is the proper way to configure GitHub authentication in n8n.

#### Step 1: Create GitHub Personal Access Token

1. **Go to GitHub Settings:**
   - Visit: <https://github.com/settings/tokens>
   - Or: GitHub.com → Profile → Settings → Developer settings → Personal access tokens

2. **Generate New Token:**
   - Click **"Generate new token"** → **"Generate new token (classic)"**

3. **Configure Token:**
   - **Note:** `n8n workflow access`
   - **Expiration:** Choose your preferred duration (90 days recommended)
   - **Select scopes:**
     - ✅ `repo` (Full control of private repositories)
     - ✅ `read:org` (Read org and team membership, read-only)
     - ✅ `read:user` (Read user profile data)

4. **Generate and Copy:**
   - Click **"Generate token"** at the bottom
   - **Copy the token immediately** - you won't see it again!
   - Save it somewhere secure temporarily

#### Step 2: Add Credential to n8n

1. **Open n8n:**

   ```bash
   # n8n should already be running on:
   http://localhost:5678
   ```

2. **Navigate to Credentials:**
   - Click **"Credentials"** in the left sidebar
   - Click **"Add Credential"** button (top right)

3. **Search for GitHub:**
   - In the search box, type: `GitHub`
   - Select **"GitHub API"** from the results

4. **Configure Credential:**
   - **Credential Name:** `GitHub API` (or any name you prefer)
   - **Access Token:** Paste your token from Step 1
   - Click **"Save"**

5. **Verify:**
   - You should see "Credential created successfully"
   - The credential will appear in your credentials list

#### Step 3: Update Workflow Node

1. **Open Your Workflow:**
   - Go to **"Workflows"** in left sidebar
   - Open **"TTA.dev API GitHub Health"** workflow

2. **Click on GitHub Node:**
   - Find the **"Get GitHub Repository Stats"** node
   - Click to open its configuration panel

3. **Select Credential:**
   - Find the **"Credential to connect with"** dropdown
   - Select **"GitHub API"** (or whatever you named it)
   - The red error border should disappear

4. **Save and Test:**
   - Click anywhere outside the panel to save
   - Click **"Save"** (top right) to save the workflow
   - Click **"Execute Workflow"** to test

---

### Method 2: Using HTTP Request Node (Alternative)

If you prefer not to use the GitHub credential system, you can configure the HTTP Request node directly:

#### Current Node Configuration (What's Failing)

```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "url": "https://api.github.com/repos/{{ $json.repo_owner }}/{{ $json.repo_name }}"
  }
}
```

#### Fix: Add Header Auth Credential

1. **Create Header Auth Credential:**
   - Credentials → Add Credential → Search: "Header Auth"
   - Select **"Header Auth"**
   - Configure:
     - **Name:** `GitHub Header Auth`
     - **Header Name:** `Authorization`
     - **Value:** `token YOUR_GITHUB_TOKEN_HERE`
   - Click **"Save"**

2. **Update Node:**
   - Open the **"Get GitHub Repository Stats"** node
   - In **"Header Auth"** section:
     - Click **"Select Credential"** dropdown
     - Choose **"GitHub Header Auth"**
   - Save workflow and test

---

## 🧪 Testing Your Configuration

### Test 1: Verify Token Works

```bash
# Export your GitHub token
export GITHUB_TOKEN='your_token_here'

# Test API access
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/theinterneti/TTA.dev
```

**Expected:** JSON response with repository data (stars, forks, etc.)

### Test 2: Run n8n Workflow

1. Open workflow in n8n
2. Click **"Execute Workflow"** (not just single node)
3. Watch execution flow:
   - ✅ Manual Trigger
   - ✅ Check TTA.dev API Health
   - ✅ IF Healthy → TRUE
   - ✅ Set Repo Data
   - ✅ Get GitHub Repository Stats ← Should work now!
   - ✅ Format Prompt
   - ✅ Call TTA.dev API
   - ✅ Format Result

4. **Check Output:**
   - Final node should show JSON with analysis
   - Should include: `analysis`, `execution_time_ms`, `correlation_id`, `model_used`

---

## 🔧 Troubleshooting

### Error: "401 Unauthorized"

**Cause:** Invalid or expired token

**Fix:**

- Generate a new GitHub token
- Update credential in n8n
- Make sure token has correct scopes (`repo`, `read:org`)

### Error: "403 Forbidden"

**Cause:** Token doesn't have required permissions

**Fix:**

- Check token scopes: <https://github.com/settings/tokens>
- Ensure `repo` scope is selected
- Re-generate token if needed

### Error: "Rate limit exceeded"

**Cause:** Too many API requests without authentication OR authenticated but exceeded limits

**Fix:**

- With authentication: 5,000 requests/hour (should be plenty)
- Without authentication: 60 requests/hour
- Wait for rate limit to reset OR use authenticated requests

### Credential Dropdown Empty

**Cause:** No credentials created OR wrong credential type

**Fix:**

- Verify you created the credential: Credentials page → should see "GitHub API"
- Check credential type matches node requirement
- Try refreshing the n8n page (Ctrl+R)

### Node Still Shows Red Border

**Cause:** Credential not saved to node

**Fix:**

- Click outside the node configuration panel
- Click "Save" workflow button (top right)
- Refresh page and check again

---

## 📚 Additional Resources

### GitHub Token Documentation

- **Creating tokens:** <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>
- **Token scopes:** <https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps>
- **Rate limits:** <https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting>

### n8n Documentation

- **Credentials:** <https://docs.n8n.io/credentials/>
- **GitHub node:** <https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.github/>
- **HTTP Request node:** <https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/>

### TTA.dev API Documentation

- **Main guide:** `TTA_API_COMPLETE.md`
- **Integration guide:** `TTA_API_N8N_INTEGRATION_GUIDE.md`
- **Success report:** `TTA_API_SUCCESS.md`

---

## ✨ Quick Reference

### Get GitHub Token Fast

```
1. https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: repo, read:org, read:user
4. Generate and copy token
```

### Add to n8n Fast

```
1. n8n → Credentials → Add Credential
2. Search: "GitHub API"
3. Name: "GitHub API"
4. Access Token: [paste token]
5. Save
```

### Update Workflow Fast

```
1. Open workflow
2. Click GitHub node
3. Select credential: "GitHub API"
4. Save workflow
5. Execute
```

---

## 🎯 What's Next?

Once GitHub credentials are working:

1. **Test Complete Workflow:**
   - Execute full workflow end-to-end
   - Verify TTA.dev API receives GitHub data
   - Check analysis output

2. **Replace Mock LLM:**
   - Add real Gemini API key
   - Update `scripts/api/tta_api_server.py`
   - Get real AI analysis instead of mock

3. **Add TTA.dev Primitives:**
   - Wrap LLM with CachePrimitive (40-60% cost savings)
   - Add RetryPrimitive (resilience)
   - Enable FallbackPrimitive (high availability)

4. **Create More Workflows:**
   - GitHub PR analyzer
   - Issue auto-labeler
   - Scheduled health monitoring
   - Slack notifications

---

**Created:** 2025-10-29
**Status:** Production Ready
**Version:** 1.0


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_github_credential_setup]]
