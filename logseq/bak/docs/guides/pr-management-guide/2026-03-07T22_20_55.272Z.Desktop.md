# PR Management Guide

**Intelligent PR management for TTA.dev**

## Overview

The PR Management system provides intelligent oversight, analytics, and automation for managing pull requests in the TTA.dev repository.

## Features

### 1. **PR Dashboard** 📊

Interactive overview of all open PRs with categorization and status.

```bash
python scripts/pr_manager.py dashboard
```

**Categories:**
- 🔴 Critical - Urgent PRs requiring immediate attention
- ✅ Ready to Merge - Approved and passing all checks
- ⚠️ Approved (Failing Checks) - Approved but CI failing
- 🔧 Changes Requested - Reviewer requested modifications
- 👀 Needs Review - Awaiting reviewer attention
- 📝 Draft - Work in progress
- 🕸️ Stale - No activity for 7+ days
- ⏳ Old - Open for 14+ days
- 🟢 Active - Recently updated

### 2. **PR Analytics** 🔍

Detailed metrics and insights on PR health.

```bash
python scripts/pr_manager.py analyze
```

**Metrics Provided:**
- Age distribution (average, min, max)
- Activity levels (staleness)
- Review status breakdown
- Size metrics (lines changed, files)
- Priority distribution

### 3. **PR Triage** 🏥

Automated categorization and prioritization of PRs.

```bash
python scripts/pr_manager.py triage
```

**Priority Scoring (0-100):**
- Critical/urgent labels: +50
- Security labels: +30
- Dependencies: +20
- Large changes (500+ lines): +20
- Approved: +15
- Passing CI: +10
- Recent activity: +10
- Engagement (comments): +5
- Age penalty: -5 per week

### 4. **Health Check** 🏥

Identifies PRs requiring attention or intervention.

```bash
python scripts/pr_manager.py health-check
```

**Health Indicators:**
- Very old PRs (30+ days)
- Very stale PRs (14+ days no activity)
- Approved but not merged
- Changes requested with no response
- Very large PRs (1000+ lines)

### 5. **Recommendations** 💡

Actionable suggestions for each PR.

```bash
python scripts/pr_manager.py recommend
```

**Recommendation Types:**
- 🚀 Ready to merge
- 👀 Needs review
- 🔧 Needs changes addressed
- 🗑️ Consider closing (stale/inactive)

## Quick Start

### Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Python 3.11+
- Access to theinterneti/TTA.dev repository

### Installation

1. Ensure GitHub CLI is authenticated:
   ```bash
   gh auth status
   ```

2. Script is ready to use:
   ```bash
   python scripts/pr_manager.py dashboard
   ```

## Usage Examples

### Daily PR Review Workflow

```bash
# 1. Check dashboard for overview
python scripts/pr_manager.py dashboard

# 2. Run health check for issues
python scripts/pr_manager.py health-check

# 3. Get recommendations
python scripts/pr_manager.py recommend
```

### Weekly PR Audit

```bash
# 1. Analyze metrics
python scripts/pr_manager.py analyze

# 2. Triage all PRs
python scripts/pr_manager.py triage

# 3. Make decisions based on recommendations
python scripts/pr_manager.py recommend
```

### Quick Status Check

```bash
# Just the dashboard
python scripts/pr_manager.py dashboard
```

## Integration with Logseq TODOs

The PR manager can be integrated with the Logseq TODO system:

### Linking PRs to TODOs

When working on a PR, add a reference in your Logseq journal:

```markdown
- TODO Review PR #123 [[#dev-todo]]
  type:: code-review
  priority:: high
  pr:: #123
  related:: [[TTA.dev/PR Management]]
```

### Creating TODOs from PR Recommendations

After running recommendations:

```markdown
## [[2025-11-13]] PR Management

### Actions from PR Manager

- TODO Merge PR #456 (ready-to-merge) [[#dev-todo]]
  type:: deployment
  priority:: high
  pr:: #456
  
- TODO Review PR #789 (needs-review, 5d old) [[#dev-todo]]
  type:: code-review
  priority:: medium
  pr:: #789
  
- TODO Close PR #321 (stale, 45d inactive) [[#dev-todo]]
  type:: maintenance
  priority:: low
  pr:: #321
```

## VS Code Integration

Add these tasks to `.vscode/tasks.json`:

```json
{
  "label": "📊 PR Dashboard",
  "type": "shell",
  "command": "python scripts/pr_manager.py dashboard",
  "group": "none",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "panel": "shared"
  }
},
{
  "label": "🔍 PR Analytics",
  "type": "shell",
  "command": "python scripts/pr_manager.py analyze",
  "group": "none",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "panel": "shared"
  }
},
{
  "label": "🏥 PR Health Check",
  "type": "shell",
  "command": "python scripts/pr_manager.py health-check",
  "group": "none",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "panel": "shared"
  }
},
{
  "label": "💡 PR Recommendations",
  "type": "shell",
  "command": "python scripts/pr_manager.py recommend",
  "group": "none",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "panel": "shared"
  }
}
```

## Automation Opportunities

### GitHub Actions Integration

Create a scheduled workflow to run health checks:

```yaml
name: PR Health Check

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install GitHub CLI
        run: |
          type -p curl >/dev/null || sudo apt update && sudo apt install curl -y
          curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
            sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
          sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
          echo "deb [arch=$(dpkg --print-architecture) \
            signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
            https://cli.github.com/packages stable main" | \
            sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
          sudo apt update
          sudo apt install gh -y
      
      - name: Run health check
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          python scripts/pr_manager.py health-check >> $GITHUB_STEP_SUMMARY
```

### Slack/Discord Notifications

Extend the script to send notifications:

```python
# Example: Send Slack notification for critical PRs
async def send_slack_notification(prs: list[PRData]) -> None:
    """Send Slack notification for critical PRs."""
    critical_prs = [pr for pr in prs if 'critical' in categorize_pr(pr)]
    if critical_prs:
        # Send to Slack webhook
        pass
```

## Best Practices

### Daily Routine

1. **Morning:** Check dashboard for overnight PRs
2. **Midday:** Run health check for issues
3. **End of day:** Review recommendations and take action

### Weekly Review

1. **Monday:** Full analytics + triage
2. **Mid-week:** Quick dashboard check
3. **Friday:** Final recommendations before weekend

### PR Hygiene

- Merge approved PRs within 1 day
- Review new PRs within 2 days
- Address stale PRs weekly
- Close inactive PRs after 30 days (if no longer needed)
- Break large PRs (1000+ lines) into smaller ones

## Troubleshooting

### GitHub CLI Not Authenticated

```bash
gh auth login
```

Follow the prompts to authenticate.

### Permission Denied

Ensure you have read access to the repository:

```bash
gh repo view theinterneti/TTA.dev
```

### No PRs Shown

Check if there are actually open PRs:

```bash
gh pr list --repo theinterneti/TTA.dev
```

## Advanced Usage

### Custom Filters

Modify `get_open_prs()` to add custom filters:

```python
async def get_open_prs(self, label: str | None = None) -> list[PRData]:
    """Fetch PRs with optional label filter."""
    cmd = ["gh", "pr", "list", "--repo", self.repo, ...]
    if label:
        cmd.extend(["--label", label])
    # ...
```

### Export to CSV

Add export functionality:

```python
async def export_csv(self, filename: str) -> None:
    """Export PR data to CSV."""
    prs = await self.get_open_prs()
    # Write to CSV
```

### Custom Scoring

Adjust `prioritize_pr()` for your needs:

```python
# Example: Prioritize documentation PRs
labels = [label["name"] for label in pr.get("labels", [])]
if "documentation" in labels:
    score += 15
```

## Contributing

When enhancing the PR manager:

1. Follow TTA.dev coding standards (Ruff, Pyright)
2. Add tests for new features
3. Update this documentation
4. Use Google-style docstrings
5. Maintain type hints

## Related Documentation

- [PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) - PR template
- [COPILOT_REVIEWER_FLOW.md](../.github/COPILOT_REVIEWER_FLOW.md) - Automated review flow
- [TODO Management System](../logseq/pages/TODO%20Management%20System.md) - TODO integration

---

**Last Updated:** 2025-11-13
**Maintainer:** @theinterneti
