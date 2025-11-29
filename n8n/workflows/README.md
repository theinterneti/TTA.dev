# TTA.dev n8n Automation System

**Production-ready GitHub automation workflows for TTA.dev**

---

## 🎯 Overview

This directory contains a comprehensive suite of n8n workflows designed specifically for TTA.dev's GitHub automation needs. Each workflow is production-ready with AI integration, error handling, and TTA.dev-specific logic.

---

## 📦 Workflows

### 1. Smart Commit & Test (`n8n_1_smart_commit_test.json`)

**Purpose:** Automatically commit changes with AI-generated messages and run tests

**Trigger:** Schedule (every 10 minutes)

**Features:**
- Detects uncommitted changes via `git status`
- Generates conventional commit messages using Gemini AI
- Understands TTA.dev package structure (primitives, observability, workspace)
- Runs fast test suite (`./scripts/test_fast.sh`)
- **On test pass:** Pushes to main
- **On test fail:** Rolls back + creates GitHub issue with test output
- Automatic labeling: `automated`, `ci-failed`, `tests`, `high-priority`

**Use Cases:**
- Continuous integration of working changes
- Automatic commit message generation
- Test-driven development workflow
- Rollback protection for main branch

---

### 2. PR Manager (`n8n_2_pr_manager.json`)

**Purpose:** Automated PR review with AI analysis and quality checks

**Trigger:** GitHub webhook on PR events (opened, synchronized, reopened)

**Features:**
- **AI Code Review:** Uses Gemini to analyze PR and provide structured feedback
  - Summary of changes
  - Architecture impact assessment
  - Quality checks (tests, docs, patterns)
  - Risk analysis
  - Specific recommendations
- **Missing Tests Warning:** Auto-comments if PR lacks test changes
- **Primitives Detection:**
  - Labels PRs modifying `tta-dev-primitives`
  - Posts requirements checklist (examples, docs, catalog update)
- **TTA.dev Standards:** Enforces 100% test coverage, type hints, documentation

**Use Cases:**
- Automated PR review feedback
- Quality gate enforcement
- Documentation reminder
- Primitives workflow guidance

---

### 3. Issue-to-Branch (`n8n_3_issue_to_branch.json`)

**Purpose:** Automatically create branches from labeled issues with AI implementation plans

**Trigger:** GitHub webhook when issue labeled with `auto-branch`

**Features:**
- **Smart Branch Naming:**
  - `fix/issue-123-description` for bugs
  - `feat/issue-456-description` for enhancements
  - `chore/issue-789-description` for other
- **AI Implementation Plan:** Generates structured plan with:
  - Scope assessment (affected packages)
  - Implementation steps (numbered checklist)
  - Testing strategy
  - Documentation requirements
  - Complexity estimate
- **Auto-labeling:** `in-progress`, `has-branch`
- **Feature Requirements:** Posts additional checklist for features

**Use Cases:**
- Quick issue-to-development workflow
- Standardized branch naming
- AI-powered planning assistance
- Feature documentation reminders

---

### 4. Release Automation (`n8n_4_release_automation.json`)

**Purpose:** Weekly automated release preparation with version bumping and changelog generation

**Trigger:** Schedule (Mondays at midnight)

**Features:**
- **Commit Analysis:**
  - Parses last 7 days of commits
  - Groups by conventional commit type (feat, fix, chore, docs)
  - Detects breaking changes
- **Smart Versioning:**
  - BREAKING CHANGE → major bump
  - feat → minor bump
  - fix → patch bump
- **AI Changelog:** Generates professional CHANGELOG entry using Gemini
- **Automated Workflow:**
  1. Analyzes commits
  2. Calculates new version
  3. Creates release branch
  4. Updates `pyproject.toml` version
  5. Prepends CHANGELOG.md
  6. Commits changes
  7. Creates release PR with stats and checklist

**Use Cases:**
- Weekly release cadence
- Semantic versioning automation
- Professional changelog generation
- Release PR standardization

---

## 🚀 Setup Instructions

### Prerequisites

1. **n8n installed** (`npm install -g n8n`)
2. **Environment variables configured** (`.env` file)
3. **GitHub PAT token** with repo access
4. **Gemini API key** for AI features
5. **n8n running** (`./launch-n8n.sh`)

### Import Workflows

**Option 1: Manual Import (Recommended for first-time)**

1. Open n8n: `http://localhost:5678`
2. Go to Workflows → Import from File
3. Import each workflow:
   - `n8n_1_smart_commit_test.json`
   - `n8n_2_pr_manager.json`
   - `n8n_3_issue_to_branch.json`
   - `n8n_4_release_automation.json`

**Option 2: Automated Import (Coming Soon)**

```bash
# Will be added to launch-n8n.sh
./launch-n8n.sh --auto-import
```

### Configure Credentials

Each workflow requires credentials to be configured in n8n:

1. **GitHub API Credential**
   - Name: `GitHub API - TTA.dev`
   - Type: GitHub API
   - Authentication: Access Token
   - Token: `{{ GITHUB_PERSONAL_ACCESS_TOKEN }}` from `.env`

2. **Google Gemini API Credential**
   - Name: `Google Gemini API`
   - Type: Google Gemini API
   - API Key: `{{ GEMINI_API_KEY }}` from `.env`

### Activate Workflows

After importing and configuring credentials:

1. Open each workflow
2. Click "Activate" toggle in top-right
3. Verify webhook URLs are registered (for PR Manager and Issue-to-Branch)
4. Test schedule triggers (Smart Commit, Release Automation)

---

## 📋 Workflow Dependencies

### Smart Commit & Test
- **Git:** Configured with user.name and user.email
- **Test Script:** `./scripts/test_fast.sh` must exist and be executable
- **GitHub API:** For creating issues on test failure
- **Gemini API:** For AI commit message generation

### PR Manager
- **GitHub Webhooks:** Must be configured for PR events
- **Gemini API:** For AI code review
- **GitHub API:** For posting comments, adding labels

### Issue-to-Branch
- **GitHub Webhooks:** Must be configured for issue labeled events
- **Git:** Write access to repository
- **Gemini API:** For implementation plan generation
- **GitHub API:** For posting comments, adding labels

### Release Automation
- **Git:** Full commit history access
- **Gemini API:** For changelog generation
- **GitHub API:** For creating PRs and labels
- **Write Permissions:** To create branches and push changes

---

## 🔧 Customization

### Modify Schedule Triggers

**Smart Commit & Test** (default: every 10 minutes)
```json
"rule": {
  "interval": [{"field": "minutes", "minutesInterval": 10}]
}
```

**Release Automation** (default: Mondays at midnight)
```json
"rule": {
  "interval": [{"field": "cronExpression", "expression": "0 0 * * 1"}]
}
```

### Adjust AI Prompts

Each workflow has Gemini AI nodes with prompts. Edit in n8n:

1. Open workflow
2. Find "AI:" nodes (e.g., "AI: Review PR")
3. Edit `text` parameter
4. Save and test

### Change Branch Naming

**Issue-to-Branch** branch format:
```javascript
// Current: fix/issue-123-short-description
branch_name: `${branch_type}/issue-${issue_number}-${issue_title.toLowerCase().replace(/[^a-z0-9]+/g, '-').substring(0, 50)}`
```

### Modify Test Commands

**Smart Commit & Test** runs:
```bash
cd /home/thein/repos/TTA.dev && ./scripts/test_fast.sh
```

Change in "Run Tests" node if using different test command.

---

## 🎯 Best Practices

### For Developers

1. **Use conventional commits** - Workflows parse commit messages
2. **Add tests to PRs** - PR Manager warns if missing
3. **Label issues** - Use `auto-branch` for automatic branch creation
4. **Review AI feedback** - PR Manager provides actionable suggestions
5. **Check release PRs** - Review weekly release PRs before merging

### For Workflow Maintenance

1. **Monitor executions** - Check n8n execution history for errors
2. **Update AI prompts** - Refine Gemini prompts based on output quality
3. **Adjust schedules** - Tune frequencies based on team workflow
4. **Version workflows** - Export workflows before major changes
5. **Test in staging** - Clone repo and test workflows before production

---

## 📊 Monitoring

### Execution History

View in n8n:
- Workflows → [Workflow Name] → Executions
- Filter by success/error
- View execution details and logs

### Common Issues

**Issue:** Webhook not triggering
- **Solution:** Check GitHub webhook configuration in repo settings
- **Verify:** Webhook URL matches n8n workflow webhook node

**Issue:** Git operations failing
- **Solution:** Check git configuration in repository
- **Verify:** `git config user.name` and `git config user.email` are set

**Issue:** AI responses incomplete
- **Solution:** Check Gemini API quota
- **Verify:** API key is valid and has credits

**Issue:** Tests failing in Smart Commit
- **Solution:** This is expected behavior - workflow creates GitHub issue
- **Action:** Review issue and fix tests manually

---

## 🔐 Security

### Credentials Storage

- **Never commit credentials** to git
- **Use n8n credential management** - credentials encrypted at rest
- **Environment variables** - Load from `.env` (already in `.gitignore`)

### Webhook Security

- **GitHub webhooks** use secret tokens (configured in n8n)
- **Validate webhook signatures** (n8n handles automatically)
- **HTTPS only** for production webhooks

### Git Operations

- **Branch protection** - Configure on `main` branch in GitHub
- **Require PR reviews** - Don't allow direct pushes to main
- **Smart Commit workflow** - Only pushes if tests pass

---

## 📈 Future Enhancements

### Planned Workflows

1. **Deployment Trigger** - Auto-deploy on merge to main
2. **Dependency Update Bot** - Weekly dependency check and PR creation
3. **Documentation Sync** - Auto-update docs site on changes
4. **Performance Monitor** - Track and alert on performance regressions
5. **Security Scan** - Weekly security audit with GitHub Security API

### Workflow Improvements

1. **Smart Commit & Test**
   - Add coverage delta tracking
   - Integrate with code quality tools (ruff, pyright)
   - Support multiple test suites

2. **PR Manager**
   - Add automated suggestions (not just review)
   - Integration with CI/CD status
   - Assign reviewers based on CODEOWNERS

3. **Issue-to-Branch**
   - Template support for different issue types
   - Integration with project boards
   - Auto-assignment based on labels

4. **Release Automation**
   - Auto-create GitHub releases
   - Publish to PyPI if applicable
   - Generate release notes with contributor list

---

## 🤝 Contributing

### Adding New Workflows

1. **Design workflow** in n8n UI
2. **Test thoroughly** with real data
3. **Export as JSON** from n8n
4. **Add to this directory** with descriptive name
5. **Document in this README** with all details
6. **Update setup scripts** if needed

### Workflow Naming Convention

```
n8n_[number]_[short-description].json
```

Examples:
- `n8n_1_smart_commit_test.json`
- `n8n_5_dependency_update.json`
- `n8n_6_performance_monitor.json`

---

## 📞 Support

### Resources

- **n8n Documentation:** https://docs.n8n.io
- **TTA.dev Documentation:** `../docs/`
- **Setup Guide:** `../N8N_EXPERT_SETUP_GUIDE.md`
- **Quickstart:** `../N8N_GIT_AUTOMATION_QUICKSTART.md`

### Troubleshooting

1. **Check logs:** n8n execution history
2. **Verify credentials:** n8n credentials page
3. **Test APIs:** `./scripts/test-n8n-setup.sh`
4. **Review documentation:** This README and workflow files

---

**Last Updated:** 2025-01-09
**Maintained by:** TTA.dev Team
**License:** See project LICENSE
