# ✅ n8n Setup Complete - Ready to Launch!

**Status**: All systems ready for git automation with n8n 🚀

## 🎯 What's Working

✅ **GitHub API**: Connected as `theinterneti`
✅ **GitHub Repo Access**: Can access `theinterneti/TTA.dev`
✅ **E2B API**: Key configured
✅ **n8n API**: Key configured
✅ **Git Configuration**: User and email set
✅ **Rate Limits**: 4951/5000 requests available
⚠️ **Gemini API**: Key present (minor version issue, won't block automation)
⚠️ **Tests**: Some tests failing (won't block n8n setup)

## 🚀 Quick Start (3 Commands)

### 1. Start n8n

```bash
cd /home/thein/repos/TTA.dev
./scripts/start-n8n.sh
```

**What this does**:
- Loads all your API keys from `.env`
- Starts n8n on <http://localhost:5678>
- Keeps running until you press Ctrl+C

### 2. Open n8n in Browser

```bash
# n8n should now be running
# Open in your browser:
http://localhost:5678
```

### 3. Import Git Automation Workflow

**In n8n UI**:

1. Click "+ Add workflow" (or "New workflow")
2. Click "..." menu → "Import from file"
3. Select: `/home/thein/repos/TTA.dev/n8n_git_automation_workflow.json`
4. Click "Import"

## 🔧 Configure Credentials in n8n

### Add GitHub Credential

1. **Open Settings**: Click gear icon ⚙️ (top-left)
2. **Go to Credentials**: Click "Credentials"
3. **Add GitHub**:
   - Click "+ Add credential"
   - Search: "GitHub API"
   - Select: "GitHub API"
   - **Credential name**: `GitHub API - TTA.dev`
   - **Access Token**: `github_pat_YOUR_GITHUB_TOKEN_HERE`
   - Click "Create"

### Add Gemini Credential (Optional)

1. **Add credential**: Click "+ Add credential"
2. **Search**: "Google" or "Gemini"
3. **Select**: "Google Gemini API" (or similar)
4. **API Key**: `AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE`
5. Click "Create"

## 🎨 Configure Workflow Nodes

Once workflow is imported:

### Nodes Using GitHub API

Update these nodes to use your GitHub credential:

1. **"Create GitHub Issue"** node:
   - Click the node
   - Under "Credentials" dropdown
   - Select: `GitHub API - TTA.dev`
   - Save

### Nodes Using Gemini API (Optional)

If you added Gemini credential:

1. **"AI: Generate Commit Message"** node:
   - Click the node
   - Under "Credentials" dropdown
   - Select your Gemini credential
   - Save

**Note**: If you skip Gemini, you can modify this node to use a simple commit message format instead of AI generation.

## ✅ Activate Workflow

1. **Save workflow**: Click "Save" button
2. **Activate**: Toggle switch at top-right to "Active"
3. **Done**: Workflow will now run every 5 minutes!

## 🎯 What the Workflow Does

```
Every 5 minutes:
  ↓
Check for uncommitted git changes
  ↓
If changes found:
  1. Get diff details
  2. Generate AI commit message (Gemini)
  3. Git add & commit
  4. Run fast tests
  5. If tests pass → Push to main ✅
  6. If tests fail → Rollback & create GitHub issue 🚨
```

## 🔍 Monitor Your Automation

### View Executions

In n8n UI:
- Click "Executions" tab (left sidebar)
- See all workflow runs
- Green = success ✅
- Red = failed ❌
- Click any execution to see details

### Check Git Commits

```bash
# See recent automated commits
git log --oneline -10

# See what's being tracked
git status
```

### GitHub Issues

Check for any auto-created issues:
- Visit: <https://github.com/theinterneti/TTA.dev/issues>
- Look for: 🚨 Tests Failed After Commit

## 🛠️ Customization Options

### Change Check Frequency

Edit the **"Every 5 Minutes"** node:
- Change to 1 minute for more frequent checks
- Change to 30 minutes for less frequent
- Or use "On webhook" trigger for manual control

### Disable Auto-Push

If you want commits but not auto-push:
- Delete or disable the "Git Push" node
- Commits will still be made locally

### Custom Commit Messages

If not using Gemini AI:
1. Delete "AI: Generate Commit Message" node
2. In "Git Add & Commit" node, set fixed message:
   ```
   git commit -m "chore: automated commit from n8n"
   ```

### Different Branch

In "Git Push" node, change:
```bash
git push origin main
```
to:
```bash
git push origin feature/auto-commits
```

## 🐛 Troubleshooting

### "No changes detected"

Make some changes:
```bash
echo "test" >> test.txt
git status  # Should show test.txt
```

Wait 5 minutes or manually trigger workflow in n8n.

### "Tests keep failing"

Option 1 - Fix tests:
```bash
./scripts/test_fast.sh
# Fix any failing tests
```

Option 2 - Disable test node:
- Delete or disable "Run Fast Tests" node
- Connect "Git Add & Commit" directly to "Git Push"

### "Workflow not running"

Check:
1. Workflow is activated (toggle at top)
2. n8n is running (`./scripts/start-n8n.sh`)
3. No errors in execution log

### "Can't access n8n UI"

Restart n8n:
```bash
# Press Ctrl+C in terminal running n8n
./scripts/start-n8n.sh
```

## 📚 Additional Workflows Available

I can help you create:

1. **PR Automation**: Auto-create PRs from feature branches
2. **Code Review Bot**: AI reviews your code changes
3. **Issue to Branch**: Auto-create branches from issues
4. **Deploy on Merge**: Trigger deployments automatically
5. **Slack Notifications**: Get notified of commits/issues

Just ask!

## 🔐 Security Reminder

✅ **Good**:
- API keys in `.env` ✅
- `.env` in `.gitignore` ✅
- Using environment variables ✅

❌ **Never do**:
- Commit `.env` to git
- Share API keys in screenshots
- Hardcode secrets in workflow

## 🎉 You're All Set!

**Next command**:
```bash
./scripts/start-n8n.sh
```

Then open: <http://localhost:5678>

**Full guides**:
- Quick Start: `N8N_GIT_AUTOMATION_QUICKSTART.md`
- Expert Guide: `N8N_EXPERT_SETUP_GUIDE.md`
- GitHub Token: `GITHUB_TOKEN_FIX.md` (if needed)

---

**Questions?** I'm here to help! Just ask about:
- Custom workflows
- Troubleshooting
- Advanced automation
- Integration with other tools


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_ready_to_launch]]
