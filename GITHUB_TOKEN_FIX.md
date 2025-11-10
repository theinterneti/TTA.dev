# GitHub Token Issue - Resolution Guide

## ❌ Current Issue

Your GitHub Personal Access Token appears to be expired or revoked.

**Error**: `Bad credentials (401)`

## 🔧 Solution: Generate New Token

### Step 1: Go to GitHub Token Settings

Visit: **https://github.com/settings/tokens**

Or navigate:
1. GitHub.com → Click your profile picture (top-right)
2. Settings → Developer settings
3. Personal access tokens → Tokens (classic)

### Step 2: Generate New Token

1. **Click**: "Generate new token" → "Generate new token (classic)"

2. **Configure**:
   - **Note**: `n8n-tta-dev-automation-$(date +%Y-%m-%d)`
   - **Expiration**: 90 days (recommended) or "No expiration" (less secure)

3. **Select scopes** (check these boxes):

   ```
   ✅ repo (Full control of private repositories)
      ✅ repo:status (Access commit status)
      ✅ repo_deployment (Access deployment status)
      ✅ public_repo (Access public repositories)
      ✅ repo:invite (Access repository invitations)
      ✅ security_events (Read and write security events)

   ✅ workflow (Update GitHub Action workflows)

   ✅ write:packages (Upload packages)
   ✅ read:packages (Download packages)

   ✅ admin:repo_hook (Full control of repository hooks)
      ✅ write:repo_hook
      ✅ read:repo_hook

   ✅ read:org (Read org and team membership)

   ✅ read:user (Read ALL user profile data)
   ✅ user:email (Access user email addresses)
   ```

4. **Click**: "Generate token" (bottom of page)

5. **COPY THE TOKEN IMMEDIATELY** - You won't see it again!
   - Format: `ghp_YOUR_GITHUB_TOKEN_HERE`
   - Length: 40 characters

### Step 3: Update Your .env File

1. **Open .env**:
   ```bash
   nano /home/thein/repos/TTA.dev/.env
   ```

2. **Replace the GitHub token line**:
   ```bash
   # OLD (expired)
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_YOUR_GITHUB_TOKEN_HERE

   # NEW (your fresh token)
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_YOUR_NEW_TOKEN_HERE
   ```

3. **Save** (Ctrl+O, Enter, Ctrl+X in nano)

### Step 4: Test the New Token

```bash
cd /home/thein/repos/TTA.dev
./scripts/test-n8n-setup.sh
```

**Expected output**:
```
GitHub API: ✅ Connected as theinterneti
GitHub Repo Access: ✅ Can access repository
```

## 🔒 Token Security

### ✅ DO

- Keep token in `.env` file only
- Add `.env` to `.gitignore` (already done ✅)
- Use environment variables
- Rotate tokens every 90 days
- Use minimal required scopes

### ❌ DON'T

- Commit tokens to git
- Share tokens in screenshots
- Use same token everywhere
- Grant excessive permissions
- Ignore expiration warnings

## 🆘 Alternative: Check Existing Token

If you think the token should work:

1. **Verify on GitHub**:
   - Visit: https://github.com/settings/tokens
   - Find your token in the list
   - Check if it's expired or revoked
   - Check if scopes are sufficient

2. **Test manually**:
   ```bash
   curl -H "Authorization: token ghp_YOUR_TOKEN" https://api.github.com/user
   ```

   Should return your GitHub user info.

## 📋 Quick Reference

**Token Format**: `ghp_` followed by 36 characters
**Total Length**: 40 characters
**Required Scopes**: `repo`, `workflow`, `read:org`, `read:user`
**Recommended Expiration**: 90 days

## 🚀 After Fixing

Once you have a valid token:

1. ✅ Test setup: `./scripts/test-n8n-setup.sh`
2. ✅ Start n8n: `./scripts/start-n8n.sh`
3. ✅ Import workflow in n8n UI
4. ✅ Activate automation

---

**Need help?** Just ask! I can guide you through any step.
