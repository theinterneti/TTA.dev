# TTA.dev Worktree Coordination Scripts

**Purpose:** Automate coordination between 4 git worktrees representing different AI coding assistants.

---

## Scripts Overview

### 1. `sync-learnings.py`

**Purpose:** Sync patterns from agent worktrees to orchestrator

**Usage:**
```bash
# Sync all agents
python sync-learnings.py --sync-all

# Sync specific agent
python sync-learnings.py --from augment

# Dry run (see what would be synced)
python sync-learnings.py --sync-all --dry-run
```

**What it does:**
- Scans `.worktree/local-patterns/` in each agent worktree
- Copies new/updated patterns to orchestrator's `.worktree/coordination/agent-{name}/`
- Scans Logseq pages for `#ready-to-share` tag
- Generates sync report
- Updates `.worktree/sync-status.json`

**Output:**
```
Sync Report: 2025-11-17 12:00 UTC
=====================================

Agent: augment
  New patterns: 3
  Updated patterns: 1
  Logseq patterns: 2

Agent: cline
  New patterns: 5
  Updated patterns: 0
  Logseq patterns: 1

Summary:
  Total new patterns: 8
  Total updated patterns: 1
  Total Logseq patterns: 3

Action Required:
  → Review 9 patterns in .worktree/coordination/
```

---

### 2. `coordination-status.py`

**Purpose:** Display coordination dashboard

**Usage:**
```bash
python coordination-status.py
```

**What it shows:**
- Active worktrees and branches
- Last sync timestamp
- Pending pattern reviews by agent
- Integration queue count
- Recommendations for next actions

**Output:**
```
======================================================================
              TTA.dev Worktree Coordination Status
======================================================================

📍 Worktrees:
----------------------------------------------------------------------
✓ orchestrator  - experimental/workflow-agent-integrations (orchestrator)
• augment       - agent/augment
• cline         - experimental/issue-collaboration
• copilot       - agent/copilot

🔄 Last Sync: 2 hours ago

📋 Pending Pattern Reviews:
----------------------------------------------------------------------
  cline        - 5 patterns (3 high priority)
  augment      - 2 patterns
  copilot      - 1 pattern

🚀 Integration Queue: 3 patterns ready

💡 Recommendations:
----------------------------------------------------------------------
  → Review pending patterns before next integration
  → 3 patterns ready for integration

======================================================================
```

---

### 3. `init-coordination.sh`

**Purpose:** One-time setup of coordination infrastructure

**Usage:**
```bash
bash init-coordination.sh
```

**What it does:**
1. Creates orchestrator coordination directories
2. Sets up shared Logseq KB structure
3. Creates coordination dashboard template
4. Initializes agent worktrees:
   - Creates `.worktree/` structure
   - Links shared KB via symlink
   - Creates agent config template
   - Adds to `.gitignore`
5. Makes scripts executable
6. Creates initial sync status

**Run this once** when setting up the coordination system.

---

## Directory Structure Created

### Orchestrator (TTA.dev)

```
TTA.dev/
├── .worktree/
│   ├── coordination/
│   │   ├── agent-augment/        # Patterns from augment
│   │   ├── agent-cline/          # Patterns from cline
│   │   ├── agent-copilot/        # Patterns from copilot
│   │   └── integration-queue/    # Ready for integration
│   └── sync-status.json          # Sync metadata
│
├── logseq/
│   └── shared/                   # Shared KB (canonical)
│       ├── pages/
│       │   ├── Worktree Patterns/
│       │   ├── Cross-Agent Learnings/
│       │   └── Integration Decisions/
│       └── coordination-dashboard.md
│
└── scripts/
    └── worktree/
        ├── sync-learnings.py
        ├── coordination-status.py
        ├── init-coordination.sh
        └── README.md (this file)
```

### Agent Worktrees

```
TTA.dev-{agent}/
├── .worktree/                    # Gitignored
│   ├── local-patterns/           # Patterns discovered locally
│   ├── experiments/              # Active experiments
│   ├── session-logs/             # Session activity
│   └── agent-config.yml          # Agent settings
│
└── logseq/
    └── shared/                   # Symlink → TTA.dev/logseq/shared/
```

---

## Workflows

### Daily Workflow (Orchestrator)

```bash
# 1. Check status
python scripts/worktree/coordination-status.py

# 2. Sync latest patterns
python scripts/worktree/sync-learnings.py --sync-all

# 3. Review patterns in:
#    .worktree/coordination/agent-*/

# 4. Move approved patterns to integration queue:
mv .worktree/coordination/agent-cline/20251117-pattern-name.md \
   .worktree/coordination/integration-queue/

# 5. Update shared KB with approved pattern:
#    Create page in logseq/shared/pages/Worktree Patterns/
```

### Daily Workflow (Agent Worktree)

```bash
# 1. Work on your feature

# 2. Document useful pattern:
#    Create: .worktree/local-patterns/YYYYMMDD-category-name.md

# 3. Or tag Logseq page with #ready-to-share

# 4. Continue working - orchestrator will sync during next run
```

---

## Pattern File Template

**Filename:** `.worktree/local-patterns/YYYYMMDD-category-name.md`

**Content:**
```markdown
# Pattern Name

**Discovered By:** agent/augment
**Date:** 2025-11-17
**Category:** performance | security | architecture | testing | tooling
**Impact:** high | medium | low
**Status:** #ready-to-share

## Problem

[What problem does this solve?]

## Pattern

[Description of the pattern/solution]

## Implementation

```python
# Code example
```

## Evidence

[Why this works - metrics, examples, reasoning]

## Applicability

- [ ] Useful for all agents
- [ ] Specific to this agent type
- [ ] Requires orchestrator review
- [ ] Needs adaptation for other contexts

## Related

- Link to Logseq pages
- Link to issues
- Link to PRs
```

---

## Sync Schedule

**Recommended:**

```bash
# Add to crontab (optional)
# Every 6 hours
0 */6 * * * cd /home/thein/repos/TTA.dev && python scripts/worktree/sync-learnings.py --sync-all >> logs/coordination.log 2>&1

# Or run manually before/after work sessions
```

**Manual is fine for start** - automate later if needed.

---

## Troubleshooting

### Script fails with "No such file or directory"

**Solution:** Run `init-coordination.sh` first to create directory structure

### Symlink broken in agent worktree

**Solution:**
```bash
cd /home/thein/repos/TTA.dev-{agent}
rm -f logseq/shared
ln -s /home/thein/repos/TTA.dev/logseq/shared logseq/shared
```

### Pattern not syncing

**Check:**
1. Is pattern in `.worktree/local-patterns/` directory?
2. Is file named correctly (`YYYYMMDD-category-name.md`)?
3. Run with `--dry-run` to see what would be synced

### Agent worktree not found

**Solution:** Update `WORKTREES` dict in scripts with actual paths

---

## Future Enhancements

**Planned (but not yet implemented):**

1. `integrate-pattern.py` - Auto-create PRs in target worktrees
2. `validate-pattern.py` - Check pattern quality before sharing
3. `pattern-stats.py` - Analytics on pattern discovery and integration
4. GitHub Actions integration for automatic syncing
5. Logseq plugin for easier pattern tagging

---

## Related Documentation

- **Main Protocol:** `WORKTREE_COORDINATION_PROTOCOL.md`
- **Git Worktrees:** `GIT_WORKTREE_SUMMARY.md`
- **AI Workspaces:** `AI_CODER_WORKSPACES_GUIDE.md`

---

**Last Updated:** November 17, 2025
