# n8n Git Automation - Quick Start Guide

**Your complete guide to automated git workflows with n8n + Cline** 🚀

## ✅ What You Have

- ✅ All API keys configured in `.env`
- ✅ n8n startup script ready
- ✅ Git automation workflow ready to import

## 🚀 Quick Start (3 Steps)

### Step 1: Start n8n

```bash
cd /home/thein/repos/TTA.dev
./scripts/start-n8n.sh
```

This will:
- Load all your API keys from `.env`
- Verify they're present
- Start n8n on http://localhost:5678

### Step 2: Configure GitHub Credentials in n8n

1. **Open n8n**: http://localhost:5678
2. **Go to Settings** → **Credentials**
3. **Add GitHub API credential**:
   - Click "+ Add credential"
   - Search for "GitHub API"
   - Name: `GitHub API`
   - Access Token: `ghp_YOUR_GITHUB_TOKEN_HERE` (from your .env)
   - Save

4. **Add Gemini API credential**:
   - Click "+ Add credential"
   - Search for "Google Gemini"
   - API Key: `AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE` (from your .env)
   - Save

### Step 3: Import Git Automation Workflow

1. **In n8n interface**: Click "+ Add workflow"
2. **Import**: Click "..." menu → "Import from file"
3. **Select**: `n8n_git_automation_workflow.json`
4. **Update credentials** in these nodes:
   - "AI: Generate Commit Message" → Select Gemini API
   - "Create GitHub Issue" → Select GitHub API
5. **Save workflow**
6. **Activate**: Toggle the workflow to active

## 🎯 What This Workflow Does

```
Every 5 minutes:
  ↓
Check for git changes
  ↓
If changes found:
  → Get diff details
  → AI generates commit message (Gemini)
  → Git add & commit
  → Run fast tests
  → If tests pass:
      → Push to main ✅
  → If tests fail:
      → Rollback commit ↩️
      → Create GitHub issue 🚨
```

## 🔧 Customization Options

### Change Check Frequency

In the "Every 5 Minutes" node:
- Change interval to your preference (1 min, 10 min, hourly, etc.)

### Modify Test Command

In the "Run Fast Tests" node:
- Replace `./scripts/test_fast.sh` with your test command
- Or use: `uv run pytest -v`

### Change Target Branch

In the "Git Push" node:
- Replace `main` with your branch name
- Or make it dynamic: `git push origin $(git branch --show-current)`

### Add Notifications

Add after "Git Push":
- Slack notification
- Email notification
- Discord webhook
- Custom API call

## 🎨 Advanced Workflows

### Workflow 2: Smart PR Creator

```
On git push:
  → Check if on feature branch
  → If yes:
      → AI analyzes commits
      → Creates PR with AI-generated description
      → Adds labels
      → Requests reviewers
```

### Workflow 3: Automated Code Review

```
On PR opened:
  → Fetch PR diff
  → AI analyzes code changes
  → Posts review comments
  → Suggests improvements
  → Runs security checks
```

### Workflow 4: Issue to Branch

```
On issue labeled "in-progress":
  → Create feature branch
  → Add starter files
  → Commit with issue reference
  → Post comment with branch name
```

## 🐛 Troubleshooting

### "No changes detected"

Check:
```bash
cd /home/thein/repos/TTA.dev
git status
```

If you have uncommitted changes but n8n doesn't see them:
- Verify the command path in "Check Git Status" node
- Check file permissions
- Ensure git is in PATH

### "Tests always fail"

Check:
```bash
cd /home/thein/repos/TTA.dev
./scripts/test_fast.sh
echo $?  # Should be 0 if passing
```

If tests fail locally:
- Fix tests first
- Then activate workflow

### "Can't push to main"

If you get rejected:
- Check branch protection rules
- Verify push permissions
- Consider pushing to feature branch instead

### "Gemini API errors"

Check quota:
- Visit: https://makersuite.google.com/app/apikey
- Verify rate limits
- Check billing (if applicable)

## 🔐 Security Best Practices

### ✅ DO

- Keep API keys in `.env` only
- Add `.env` to `.gitignore`
- Use environment variables in n8n: `{{ $env.VAR_NAME }}`
- Rotate keys regularly
- Use minimal required permissions

### ❌ DON'T

- Hardcode API keys in workflow
- Commit `.env` to git
- Share API keys in screenshots
- Use production keys for testing
- Grant excessive permissions

## 🎓 Next Steps

### Learn n8n

- **Docs**: https://docs.n8n.io/
- **Templates**: https://n8n.io/workflows/
- **Community**: https://community.n8n.io/

### Extend Your Workflows

1. **Add PR automation**
2. **Implement code review bot**
3. **Set up deployment triggers**
4. **Create issue management**
5. **Build custom dashboards**

### Integration Ideas

- **Slack**: Team notifications
- **Jira**: Sync issues
- **Sentry**: Error tracking
- **DataDog**: Metrics monitoring
- **Linear**: Project management

## 📊 Monitoring Your Automation

### Check Workflow Executions

In n8n:
- Go to "Executions" tab
- View success/failure rate
- Debug failed runs
- Export execution data

### Git Statistics

```bash
# Today's automated commits
git log --since="1 day ago" --oneline

# Total automated commits
git log --grep="^(feat|fix|docs|style|refactor|test|chore)" --oneline | wc -l

# Test pass rate
# Check GitHub issues labeled "ci-failed"
```

## 💡 Pro Tips

1. **Start with manual testing**
   - Run workflow manually first
   - Verify each node works
   - Then enable automatic schedule

2. **Use execution logs**
   - Check node outputs
   - Debug with console.log
   - Export execution data

3. **Version your workflows**
   - Export JSON regularly
   - Commit to git (without credentials)
   - Track changes

4. **Test in separate branch**
   - Create `n8n-test` branch
   - Test automation there
   - Merge when confident

## 🆘 Getting Help

**Need more help?** I can create:

1. **Custom workflows** for your specific needs
2. **Integration guides** for other tools
3. **Troubleshooting scripts** for debugging
4. **Advanced automation** patterns

Just ask! 🚀

---

**Your API Keys Status**: ✅ All configured
**n8n Status**: Ready to start
**Next Action**: Run `./scripts/start-n8n.sh`


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_git_automation_quickstart]]
