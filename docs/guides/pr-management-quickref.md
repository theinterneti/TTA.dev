# PR Management Quick Reference

**TTA.dev Intelligent PR Management**

## Quick Commands

```bash
# Dashboard - Visual overview
python scripts/pr_manager.py dashboard

# Analytics - Metrics and insights
python scripts/pr_manager.py analyze

# Triage - Categorize and prioritize
python scripts/pr_manager.py triage

# Health Check - Identify issues
python scripts/pr_manager.py health-check

# Recommendations - Next actions
python scripts/pr_manager.py recommend
```

## VS Code Tasks

Press `Cmd/Ctrl+Shift+P` → "Task: Run Task" → Select:

- 📊 PR Dashboard
- 🔍 PR Analytics
- 🏥 PR Triage
- 🏥 PR Health Check
- 💡 PR Recommendations

## PR Categories

| Category | Icon | Meaning |
|----------|------|---------|
| Critical | 🔴 | Urgent, requires immediate attention |
| Ready to Merge | ✅ | Approved and passing checks |
| Approved (Failing) | ⚠️ | Approved but CI failing |
| Changes Requested | 🔧 | Reviewer asked for modifications |
| Needs Review | 👀 | Waiting for reviewer |
| Draft | 📝 | Work in progress |
| Stale | 🕸️ | No activity for 7+ days |
| Old | ⏳ | Open for 14+ days |
| Active | 🟢 | Recently updated |

## Priority Score (0-100)

| Range | Priority | Action |
|-------|----------|--------|
| 70+ | High | Address immediately |
| 40-69 | Medium | Review this week |
| <40 | Low | Review when possible |

**Factors:**
- Critical/urgent labels: +50
- Security labels: +30
- Dependencies: +20
- Large changes (500+ lines): +20
- Approved: +15
- Passing CI: +10
- Recent activity: +10
- Engagement: +5
- Age penalty: -5 per week

## Daily Workflow

1. **Morning:** Check dashboard
   ```bash
   python scripts/pr_manager.py dashboard
   ```

2. **Midday:** Run health check
   ```bash
   python scripts/pr_manager.py health-check
   ```

3. **End of day:** Review recommendations
   ```bash
   python scripts/pr_manager.py recommend
   ```

## Weekly Review

1. **Monday:** Full analytics + triage
   ```bash
   python scripts/pr_manager.py analyze
   python scripts/pr_manager.py triage
   ```

2. **Friday:** Final recommendations
   ```bash
   python scripts/pr_manager.py recommend
   ```

## Common Actions

### Merge Ready PR
```bash
gh pr merge <number> --squash
```

### Request Review
```bash
gh pr review <number> --request-reviewer <username>
```

### Close Stale PR
```bash
gh pr close <number> --comment "Closing due to inactivity"
```

### Review PR
```bash
gh pr review <number>
```

## Logseq Integration

### Link PR to TODO

```markdown
- TODO Review PR #123 [[#dev-todo]]
  type:: code-review
  priority:: high
  pr:: #123
```

### Create TODO from Recommendation

After running `recommend`:

```markdown
## [[2025-11-13]] PR Actions

- TODO Merge PR #456 (ready) [[#dev-todo]]
  type:: deployment
  priority:: high
  pr:: #456

- TODO Review PR #789 (5d old) [[#dev-todo]]
  type:: code-review
  priority:: medium
  pr:: #789
```

## Health Indicators

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Very Old | 30+ days open | Consider closing |
| Very Stale | 14+ days inactive | Follow up |
| Approved Not Merged | Any | Merge soon |
| Large PR | 1000+ lines | Break into smaller PRs |

## Best Practices

✅ **DO:**
- Review new PRs within 2 days
- Merge approved PRs within 1 day
- Address stale PRs weekly
- Break large PRs into smaller ones
- Close inactive PRs after 30 days

❌ **DON'T:**
- Let PRs sit without review for >3 days
- Ignore stale PRs
- Create PRs with >1000 lines
- Merge PRs with failing checks
- Leave approved PRs unmerged

## Troubleshooting

### GitHub CLI not authenticated
```bash
gh auth login
```

### Permission denied
```bash
gh repo view theinterneti/TTA.dev
```

### No PRs shown
```bash
gh pr list --repo theinterneti/TTA.dev
```

## Quick Links

- [Full Guide](../guides/pr-management-guide.md)
- [PR Template](../../.github/PULL_REQUEST_TEMPLATE.md)
- [Copilot Review Flow](../../.github/COPILOT_REVIEWER_FLOW.md)
- [TODO Management](../../logseq/pages/TODO%20Management%20System.md)

---

**Last Updated:** 2025-11-13
**Quick Access:** `Cmd/Ctrl+Shift+P` → "Task: Run Task" → PR commands
