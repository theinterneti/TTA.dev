# Multi-Agent Oversight Quick Reference

## 🚀 Quick Start

```bash
# Install hooks (one-time setup)
bash scripts/install_agent_hooks.sh

# Check pending commits
python scripts/agent_oversight.py status

# Review commits
python scripts/agent_oversight.py review

# Quick approve
python scripts/agent_oversight.py approve <commit-id>

# Reject with reason
python scripts/agent_oversight.py reject <commit-id> "reason"
```

## 📋 Daily Workflow

### Morning (Start of Session)
```bash
cd /home/thein/repos/TTA.dev-copilot
python scripts/agent_oversight.py status
```

### When Notified of New Commit
```bash
# Quick review and approve
python scripts/agent_oversight.py review <commit-id>

# Or review all pending
python scripts/agent_oversight.py review
```

### Evening (End of Session)
```bash
# Check all pending reviews are handled
python scripts/agent_oversight.py status

# Should see: "✅ No pending commits to review"
```

## 🤖 For Other Agents (Augment/Cline)

Just commit normally - hooks handle everything:

```bash
cd /home/thein/repos/TTA.dev-augment  # or -cline
git add .
git commit -m "feat: your feature"

# Hook automatically:
# ✅ Validates syntax
# ✅ Adds [agent:name] tag
# ✅ Logs commit
# ✅ Notifies copilot
```

## 📊 What Gets Logged

### Commit Log (`.agent-commits/commits-{agent}.log`)
```
---
Timestamp: 2025-11-17T10:30:00Z
Agent: augment
Branch: agent/augment
Commit: a1b2c3d4
Message: [agent:augment] feat: implement feature
Files Changed:
M	src/file.py
A	tests/test_file.py
```

### Notification (`.agent-notifications/pending-*.json`)
```json
{
  "timestamp": "2025-11-17T10:30:00Z",
  "agent": "augment",
  "branch": "agent/augment",
  "commit": "a1b2c3d4",
  "message": "feat: implement feature",
  "worktree": "/home/thein/repos/TTA.dev-augment",
  "reviewed": false
}
```

### Review Log (`.agent-reviews.json`)
```json
[
  {
    "timestamp": "2025-11-17T11:00:00Z",
    "decision": "approved",
    "agent": "augment",
    "commit": "a1b2c3d4",
    "reviewer": "copilot"
  }
]
```

## 🔍 Commands Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `status` | Show pending commits | `python scripts/agent_oversight.py status` |
| `review` | Review commits interactively | `python scripts/agent_oversight.py review` |
| `review <id>` | Review specific commit | `python scripts/agent_oversight.py review augment-1234` |
| `approve <id>` | Quick approve | `python scripts/agent_oversight.py approve augment-1234` |
| `reject <id>` | Quick reject | `python scripts/agent_oversight.py reject cline-5678 "reason"` |

## 🎯 Review Criteria

When reviewing commits, check:

- ✅ **Code Quality** - Follows TTA.dev standards
- ✅ **Tests** - Has appropriate test coverage
- ✅ **Documentation** - Updates docs if needed
- ✅ **Security** - No secrets, safe code
- ✅ **Type Safety** - Proper type hints
- ✅ **Primitives** - Uses TTA.dev primitives correctly

## 🚨 Troubleshooting

### No Notifications
```bash
# Check hooks installed
ls -la /home/thein/repos/TTA.dev-augment/.git/worktrees/*/hooks/

# Reinstall if needed
bash scripts/install_agent_hooks.sh
```

### Hook Errors
```bash
# Check hook permissions
chmod +x /home/thein/repos/TTA.dev/.git-hooks/*

# Reinstall
bash scripts/install_agent_hooks.sh
```

### Python Script Issues
```bash
# Make script executable
chmod +x scripts/agent_oversight.py

# Run with python3
python3 scripts/agent_oversight.py status
```

## 📁 File Locations

```
Main Repo:
  .git-hooks/              # Hook source
  scripts/
    agent_oversight.py     # Review CLI
    install_agent_hooks.sh # Installer

Each Worktree:
  .git/worktrees/{name}/hooks/  # Installed hooks
  .agent-commits/               # Commit logs

Copilot Worktree:
  .agent-notifications/    # Pending reviews
  .agent-reviews.json      # Review history
```

## 🔗 Related

- Full docs: `docs/guides/development/MULTI_AGENT_OVERSIGHT.md`
- Copilot instructions: `.github/copilot-instructions.md`
- Coding standards: `docs/guides/development/CodingStandards.md`

---

**Quick Help:** `python scripts/agent_oversight.py --help`


---
**Logseq:** [[TTA.dev/Docs/Development/Agent_oversight_quickref]]
