# TTA.dev Multi-Worktree Coordination Protocol

**Version:** 1.0
**Date:** November 17, 2025
**Status:** Production-Ready
**Purpose:** Orchestrate 4 AI coding agents working in parallel via git worktrees

---

## 🎯 Executive Summary

TTA.dev coordinates 4 git worktrees, each representing a different AI coding assistant:

| Worktree | Location | Branch | AI Agent | Role |
|----------|----------|--------|----------|------|
| **TTA.dev** (MAIN) | `/home/thein/repos/TTA.dev` | `experimental/workflow-agent-integrations` | GitHub Copilot | **ORCHESTRATOR** - Coordinates all agents |
| **Augment** | `/home/thein/repos/TTA.dev-augment` | `agent/augment` | Augment Code | Fast iteration, code completion |
| **Cline** | `/home/thein/repos/TTA.dev-cline` | `experimental/issue-collaboration` | Cline (Claude) | Research, complex problem-solving |
| **Copilot** | `/home/thein/repos/TTA.dev-copilot` | `agent/copilot` | GitHub Copilot | GitHub workflows, quality checks |

**Philosophy:** Like 4 developers on the same server - isolated workspaces, shared knowledge base, orchestrated by a lead developer.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TTA.dev (ORCHESTRATOR)                   │
│  Branch: experimental/workflow-agent-integrations           │
│  Role: Coordinate, synthesize, integrate learnings          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ↓             ↓             ↓             ↓
┌───────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
│  TTA-Augment  │ │ TTA-Cline │ │TTA-Copilot│ │ (Future) │
│  agent/augment│ │experimental│ │agent/     │ │          │
│               │ │issue-      │ │copilot    │ │          │
│ Fast coding   │ │collab      │ │GitHub     │ │          │
│ Completion    │ │Research    │ │workflows  │ │          │
└───────────────┘ └───────────┘ └──────────┘ └──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
              ┌───────▼───────┐
              │  Shared KB    │
              │ logseq/shared/│
              │ .worktree/    │
              └───────────────┘
```

---

## 🔒 Core Principles

### 1. Isolation First
- **Each worktree is completely independent**
- No direct interference with other worktrees
- Each agent works on its own branch
- No shared working directory modifications

### 2. Explicit Knowledge Sharing
- **All learning happens through designated channels**
- Logseq pages tagged for cross-worktree visibility
- Explicit "export to shared KB" workflow
- No implicit dependencies

### 3. Orchestrator Authority
- **TTA.dev (main) has final say on integration**
- Reviews patterns from all 3 agent worktrees
- Decides what gets promoted to main/shared branches
- Maintains consistency and quality

### 4. Bidirectional Learning
- **Patterns flow both ways:**
  - Agent worktrees discover patterns → Share to main
  - Main validates patterns → Distribute to all agents
- Continuous improvement loop

### 5. Fail-Safe Design
- **If coordination fails, agents still work independently**
- No coordination mechanism should block individual work
- Graceful degradation

---

## 📁 Directory Structure

### Per-Worktree Structure

Each worktree maintains:

```
TTA.dev-{worktree}/
├── .worktree/                    # Worktree-specific (gitignored)
│   ├── agent-config.yml          # Agent-specific settings
│   ├── local-patterns/           # Patterns discovered locally
│   ├── experiments/              # Active experiments
│   └── session-logs/             # Session activity logs
│
├── logseq/                       # Local Logseq graph
│   ├── journals/                 # Daily work logs
│   ├── pages/                    # Local pages
│   └── shared/                   # **SHARED KB** (symlink to main)
│
└── [rest of repo structure]
```

### Main TTA.dev Structure (Orchestrator)

```
TTA.dev/ (main)
├── .worktree/                    # Orchestrator-specific
│   ├── coordination/
│   │   ├── agent-augment/        # Learnings from augment
│   │   ├── agent-cline/          # Learnings from cline
│   │   ├── agent-copilot/        # Learnings from copilot
│   │   └── integration-queue/    # Patterns ready for integration
│   │
│   ├── sync-status.json          # Last sync timestamps
│   └── coordination.log          # Coordination activity
│
├── logseq/
│   ├── shared/                   # **SHARED KB** (canonical)
│   │   ├── pages/
│   │   │   ├── Worktree Patterns/
│   │   │   ├── Cross-Agent Learnings/
│   │   │   └── Integration Decisions/
│   │   └── coordination-dashboard.md
│   │
│   └── [standard logseq structure]
│
├── scripts/
│   ├── worktree/
│   │   ├── sync-learnings.py     # Extract learnings from agents
│   │   ├── integrate-pattern.py  # Promote pattern to all worktrees
│   │   ├── coordination-status.py # Show sync status
│   │   └── init-worktree.sh      # Setup new agent worktree
│   │
│   └── [existing scripts]
│
└── WORKTREE_COORDINATION_PROTOCOL.md  # This file
```

---

## 🔄 Workflows

### Workflow 1: Agent Discovers Pattern

**Trigger:** Agent (Augment/Cline/Copilot) discovers useful pattern

**Steps:**

1. **Agent documents in local Logseq:**
   ```markdown
   ## [[Worktree Pattern - {Name}]]

   **Discovered By:** agent/augment
   **Date:** 2025-11-17
   **Status:** #local-pattern
   **Impact:** High/Medium/Low

   ### Pattern
   [Description of pattern]

   ### Evidence
   [Why this works, examples, metrics]

   ### Applicability
   - [ ] Useful for all agents
   - [ ] Specific to this agent
   - [ ] Requires orchestrator review

   ### Export
   - [ ] Ready to share
   ```

2. **Agent marks for export:**
   - Tag: `#ready-to-share`
   - Add to `.worktree/local-patterns/YYYYMMDD-pattern-name.md`

3. **Orchestrator discovers during sync:**
   - Script: `scripts/worktree/sync-learnings.py --from augment`
   - Copies to `.worktree/coordination/agent-augment/`

4. **Orchestrator reviews:**
   - Evaluates pattern quality, applicability, conflicts
   - Decides: Integrate, Reject, Request Changes

5. **If approved, orchestrator distributes:**
   - Creates shared Logseq page: `logseq/shared/pages/Worktree Patterns/{Name}.md`
   - Notifies other agents via coordination dashboard
   - Optionally applies to other worktrees

---

### Workflow 2: Orchestrator Integrates Pattern

**Trigger:** Orchestrator decides pattern should be universal

**Steps:**

1. **Create integration task:**
   ```bash
   scripts/worktree/integrate-pattern.py \
     --pattern ".worktree/coordination/agent-cline/retry-optimization.md" \
     --target-worktrees "augment,copilot" \
     --strategy "create-pr"
   ```

2. **Integration strategies:**
   - **`create-pr`**: Creates PR in target worktree branches
   - **`auto-apply`**: Directly applies to target worktrees (destructive!)
   - **`notify-only`**: Just adds to shared KB, agents apply manually

3. **Orchestrator tracks integration:**
   - Updates `logseq/shared/coordination-dashboard.md`
   - Logs to `.worktree/coordination.log`
   - Updates `sync-status.json`

4. **Target agents review:**
   - See notification in shared KB
   - Review PR (if strategy: create-pr)
   - Apply or adapt to their context

---

### Workflow 3: Periodic Sync

**Trigger:** Cron job or manual invocation

**Command:**
```bash
scripts/worktree/sync-learnings.py --sync-all
```

**Actions:**

1. **For each agent worktree:**
   - Check `.worktree/local-patterns/` for new patterns
   - Check Logseq for pages tagged `#ready-to-share`
   - Extract and copy to orchestrator

2. **Generate sync report:**
   ```
   Sync Report: 2025-11-17 11:45 UTC
   =====================================

   Agent: augment
   - New patterns: 3
   - Updated patterns: 1
   - Issues discovered: 0

   Agent: cline
   - New patterns: 5
   - Updated patterns: 0
   - Issues discovered: 2

   Agent: copilot
   - New patterns: 2
   - Updated patterns: 1
   - Issues discovered: 1

   Action Required:
   - Review 10 new patterns in .worktree/coordination/
   - Address 3 issues flagged by agents
   ```

3. **Update coordination dashboard:**
   - Sync timestamps
   - Pending reviews
   - Integration queue

---

### Workflow 4: Cross-Worktree Collaboration

**Scenario:** Cline discovers issue, Augment has solution

**Steps:**

1. **Cline documents issue:**
   ```markdown
   ## [[Issue - Retry Logic Inefficient]]

   **Discovered By:** agent/cline
   **Type:** #performance-issue
   **Impact:** High
   **Status:** #needs-solution

   ### Problem
   Current retry logic uses linear backoff, causing delays...

   ### Looking For
   Exponential backoff implementation or pattern
   ```

2. **Orchestrator sees pattern in Augment's work:**
   - Augment has implemented exponential backoff in different context
   - Orchestrator connects the dots

3. **Orchestrator creates bridge:**
   ```markdown
   ## [[Cross-Agent Pattern - Exponential Backoff]]

   **Source:** agent/augment (retry_primitive.py)
   **Applicable To:** agent/cline (issue #234)
   **Status:** #ready-to-integrate

   ### Pattern from Augment
   [Code snippet, explanation]

   ### Application to Cline's Issue
   [Adapted version for Cline's context]
   ```

4. **Both agents benefit:**
   - Cline gets solution to their issue
   - Augment's pattern is validated in new context
   - Pattern added to shared KB for future use

---

## 🏷️ Tagging Convention

### Logseq Tags for Coordination

| Tag | Purpose | Who Uses | Visibility |
|-----|---------|----------|------------|
| `#local-pattern` | Pattern discovered locally | Any agent | Local only |
| `#ready-to-share` | Pattern ready for orchestrator review | Any agent | Agent + Orchestrator |
| `#under-review` | Pattern being evaluated | Orchestrator | All |
| `#approved-pattern` | Pattern validated for sharing | Orchestrator | All (in shared KB) |
| `#integration-pending` | Pattern queued for integration | Orchestrator | All |
| `#integrated` | Pattern applied across worktrees | Orchestrator | All |
| `#agent-specific` | Pattern only useful for one agent | Any | Flagged, not shared |
| `#needs-discussion` | Pattern requires multi-agent input | Any | All |
| `#performance-issue` | Performance problem discovered | Any agent | All |
| `#security-concern` | Security issue found | Any agent | All (high priority) |

### File Naming Convention

**In `.worktree/local-patterns/`:**
```
YYYYMMDD-{category}-{brief-name}.md

Examples:
20251117-performance-cache-optimization.md
20251117-pattern-retry-exponential-backoff.md
20251117-issue-import-circular-dependency.md
```

**In `.worktree/coordination/agent-{name}/`:**
```
{source-date}-{category}-{name}.md

Examples:
20251117-performance-cache-optimization.md
20251116-pattern-error-handling.md
```

---

## 🛠️ Automation Scripts

### Script 1: `sync-learnings.py`

**Purpose:** Extract learnings from agent worktrees to orchestrator

**Usage:**
```bash
# Sync all agents
scripts/worktree/sync-learnings.py --sync-all

# Sync specific agent
scripts/worktree/sync-learnings.py --from augment

# Dry run (show what would be synced)
scripts/worktree/sync-learnings.py --sync-all --dry-run
```

**Implementation:**
```python
#!/usr/bin/env python3
"""Sync learnings from agent worktrees to orchestrator."""

import argparse
import json
from datetime import datetime
from pathlib import Path
import shutil

WORKTREES = {
    "augment": "/home/thein/repos/TTA.dev-augment",
    "cline": "/home/thein/repos/TTA.dev-cline",
    "copilot": "/home/thein/repos/TTA.dev-copilot",
}

ORCHESTRATOR_ROOT = Path("/home/thein/repos/TTA.dev")
COORDINATION_DIR = ORCHESTRATOR_ROOT / ".worktree" / "coordination"

def sync_agent_patterns(agent_name: str, dry_run: bool = False):
    """Sync patterns from agent worktree to orchestrator."""
    worktree_path = Path(WORKTREES[agent_name])
    patterns_dir = worktree_path / ".worktree" / "local-patterns"

    if not patterns_dir.exists():
        print(f"No patterns directory for {agent_name}")
        return []

    target_dir = COORDINATION_DIR / f"agent-{agent_name}"
    target_dir.mkdir(parents=True, exist_ok=True)

    synced_patterns = []

    for pattern_file in patterns_dir.glob("*.md"):
        target_file = target_dir / pattern_file.name

        # Skip if already synced and not modified
        if target_file.exists():
            if target_file.stat().st_mtime >= pattern_file.stat().st_mtime:
                continue

        if not dry_run:
            shutil.copy2(pattern_file, target_file)

        synced_patterns.append(pattern_file.name)
        print(f"  ✓ Synced: {pattern_file.name}")

    return synced_patterns

# [Additional functions for Logseq scanning, report generation]
```

---

### Script 2: `integrate-pattern.py`

**Purpose:** Promote pattern from one worktree to others

**Usage:**
```bash
# Create PRs in target worktrees
scripts/worktree/integrate-pattern.py \
  --pattern .worktree/coordination/agent-cline/retry-optimization.md \
  --targets augment,copilot \
  --strategy create-pr

# Auto-apply (use with caution!)
scripts/worktree/integrate-pattern.py \
  --pattern .worktree/coordination/agent-augment/logging-format.md \
  --targets all \
  --strategy auto-apply \
  --confirm
```

---

### Script 3: `coordination-status.py`

**Purpose:** Show coordination dashboard

**Usage:**
```bash
scripts/worktree/coordination-status.py
```

**Output:**
```
TTA.dev Worktree Coordination Status
====================================

Worktrees:
✓ TTA.dev (orchestrator)     - experimental/workflow-agent-integrations
✓ TTA.dev-augment            - agent/augment
✓ TTA.dev-cline              - experimental/issue-collaboration
✓ TTA.dev-copilot            - agent/copilot

Last Sync: 2025-11-17 11:30 UTC (15 minutes ago)

Pending Reviews:
- agent-cline: 5 patterns (3 high priority)
- agent-augment: 2 patterns
- agent-copilot: 1 pattern

Integration Queue: 3 patterns ready
Active Integrations: 1 (PR #245 in augment worktree)

Issues Flagged:
⚠ agent-copilot: Circular dependency in framework/
⚠ agent-cline: Performance regression in search

Recommendations:
→ Review high-priority patterns from Cline
→ Address circular dependency before next integration
→ Run sync-learnings.py to get latest from all agents
```

---

### Script 4: `init-worktree.sh`

**Purpose:** Initialize new agent worktree with coordination setup

**Usage:**
```bash
scripts/worktree/init-worktree.sh --agent newagent --branch agent/newagent
```

**Actions:**
1. Creates git worktree
2. Creates `.worktree/` structure
3. Links `logseq/shared/` to main
4. Copies agent config template
5. Registers in orchestrator

---

## 📊 Coordination Dashboard

**Location:** `logseq/shared/coordination-dashboard.md`

**Content:**
```markdown
# Worktree Coordination Dashboard

**Last Updated:** [[2025-11-17]] 11:45 UTC

## Active Worktrees

{{query (and [[Worktree Config]] (property status active))}}

## Pending Pattern Reviews

{{query (and [[Worktree Pattern]] (property status #under-review))}}

## Integration Queue

{{query (and [[Worktree Pattern]] (property status #integration-pending))}}

## Recent Integrations

{{query (and [[Worktree Pattern]] (property status #integrated) (property date [[2025-11-17]]))}}

## Issues & Blockers

{{query (and (or [[#performance-issue]] [[#security-concern]]) (not (property resolved true)))}}

## Agent Activity (Last 24h)

| Agent | Patterns Shared | Issues Flagged | Integrations Applied |
|-------|----------------|----------------|---------------------|
| augment | 3 | 0 | 2 |
| cline | 5 | 2 | 1 |
| copilot | 2 | 1 | 0 |

## Coordination Metrics

- **Cross-pollination rate:** 75% (6/8 patterns applied to multiple agents)
- **Average integration time:** 2.3 days
- **Pattern quality:** 85% approved on first review
```

---

## 🔐 Security & Isolation

### Git Isolation

**Guaranteed by git worktree design:**
- Each worktree has own working directory
- No shared staging area
- Independent branch checkout
- Commits don't affect other worktrees

**Additional safeguards:**
```bash
# In each agent worktree, set push policy
git config push.default current  # Only push current branch
git config branch.autoSetupRebase always  # Prevent merge commits

# Prevent accidental main branch pushes
git config --add remote.origin.push 'refs/heads/main:refs/heads/main^'
```

### File System Isolation

**Isolated per worktree:**
- `.worktree/` directory (gitignored)
- `node_modules/`, `__pycache__/`, etc.
- Agent-specific configurations

**Shared (read-only):**
- `logseq/shared/` (symlink to canonical location in main)

**Never shared:**
- Working directory files
- Git staging area
- Local branches

### Logseq Isolation

**Strategy:** Shared namespace with clear ownership

**Structure:**
```
logseq/
├── pages/                  # Local agent pages (not synced)
├── journals/               # Local agent journals (not synced)
└── shared/                 # SYMLINK → ../../TTA.dev/logseq/shared/
    ├── pages/
    │   ├── Worktree Patterns/    # Cross-agent patterns
    │   ├── Cross-Agent Learnings/
    │   └── Integration Decisions/
    └── coordination-dashboard.md
```

**Rules:**
1. Agents can READ all shared pages
2. Agents can CREATE pages in shared namespace with tag `#from-{agent}`
3. Only orchestrator can MODIFY shared pages created by others
4. Conflicts resolved by orchestrator

---

## 🎓 Best Practices

### For Agent Worktrees (Augment/Cline/Copilot)

**DO:**
✅ Work independently on your branch
✅ Document patterns in local Logseq
✅ Tag patterns with `#ready-to-share` when confident
✅ Use `.worktree/local-patterns/` for experiments
✅ Check shared KB for existing patterns before reinventing
✅ Flag issues with `#performance-issue` or `#security-concern`

**DON'T:**
❌ Directly modify other worktrees
❌ Push to main branch
❌ Assume patterns in shared KB are immediately in other worktrees
❌ Delete or modify shared KB pages without orchestrator approval
❌ Work on same feature in multiple worktrees simultaneously

### For Orchestrator (TTA.dev main)

**DO:**
✅ Run `sync-learnings.py` regularly (at least daily)
✅ Review patterns within 24-48 hours
✅ Provide clear integration decisions
✅ Update coordination dashboard
✅ Validate patterns before promoting
✅ Document integration rationale

**DON'T:**
❌ Auto-integrate without review
❌ Ignore flagged issues
❌ Force patterns on agents without context
❌ Delay reviews indefinitely
❌ Modify agent worktree files directly

---

## 📈 Success Metrics

### Coordination Health

**Measure these weekly:**

1. **Pattern Discovery Rate:** New patterns shared per agent
2. **Integration Velocity:** Time from discovery to integration
3. **Cross-Pollination:** % of patterns applied to multiple agents
4. **Quality Score:** % of patterns approved without changes
5. **Issue Resolution Time:** Time from flag to fix
6. **Sync Latency:** Time between sync runs

**Targets:**
- Pattern discovery: 5-10 per agent per week
- Integration velocity: < 3 days
- Cross-pollination: > 60%
- Quality score: > 80%
- Issue resolution: < 48 hours
- Sync latency: < 24 hours

### Warning Signs

🚨 **Red flags indicating coordination breakdown:**
- Sync hasn't run in > 48 hours
- Integration queue > 20 patterns
- Same pattern discovered independently by 2+ agents
- Security concern unaddressed for > 24 hours
- Agent worktree diverged > 100 commits from main

---

## 🚀 Quick Start Guide

### Initial Setup (One-Time)

```bash
# 1. Setup orchestrator coordination directory
cd /home/thein/repos/TTA.dev
mkdir -p .worktree/coordination/{agent-augment,agent-cline,agent-copilot,integration-queue}

# 2. Create shared Logseq KB
mkdir -p logseq/shared/pages/{Worktree\ Patterns,Cross-Agent\ Learnings,Integration\ Decisions}
cp scripts/worktree/templates/coordination-dashboard.md logseq/shared/

# 3. Setup agent worktrees
for worktree in TTA.dev-augment TTA.dev-cline TTA.dev-copilot; do
  cd /home/thein/repos/$worktree
  mkdir -p .worktree/local-patterns
  ln -s /home/thein/repos/TTA.dev/logseq/shared logseq/shared
done

# 4. Install coordination scripts
cd /home/thein/repos/TTA.dev
# Scripts created above

# 5. Setup cron job for periodic sync (optional)
# crontab -e
# 0 */6 * * * cd /home/thein/repos/TTA.dev && scripts/worktree/sync-learnings.py --sync-all
```

### Daily Usage

**As agent worktree (Augment/Cline/Copilot):**
```bash
# 1. Check shared KB for new patterns
# Open logseq/shared/coordination-dashboard.md

# 2. Work on your feature

# 3. Document useful pattern
# Create: .worktree/local-patterns/YYYYMMDD-category-name.md

# 4. Tag for sharing in Logseq
# Add #ready-to-share tag
```

**As orchestrator (TTA.dev main):**
```bash
# 1. Check coordination status
scripts/worktree/coordination-status.py

# 2. Sync learnings from agents
scripts/worktree/sync-learnings.py --sync-all

# 3. Review new patterns
ls .worktree/coordination/agent-*/

# 4. Integrate approved patterns
scripts/worktree/integrate-pattern.py \
  --pattern .worktree/coordination/agent-cline/20251117-pattern-name.md \
  --targets augment,copilot \
  --strategy create-pr

# 5. Update dashboard
# Edit: logseq/shared/coordination-dashboard.md
```

---

## 🔄 Integration with TTA.dev Primitives

**This coordination protocol is itself a TTA.dev pattern!**

### Conceptual Mapping

| Worktree Concept | TTA.dev Primitive Equivalent |
|------------------|------------------------------|
| Agent worktrees | `ParallelPrimitive` (concurrent agents) |
| Orchestrator | `SequentialPrimitive` (review → integrate → distribute) |
| Sync process | `RetryPrimitive` (reliable sync with backoff) |
| Pattern review | `ConditionalPrimitive` (approve/reject/modify) |
| Integration | `RouterPrimitive` (route to appropriate worktrees) |
| Shared KB | `CachePrimitive` (shared knowledge cache) |

### Future: Automate with TTA.dev

**Vision:** Replace scripts with TTA.dev workflow primitives

```python
# Future: Coordination as a workflow primitive
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.orchestration import (
    WorktreeCoordinationPrimitive,
    PatternSyncPrimitive,
    IntegrationPrimitive
)

# Define coordination workflow
coordination_workflow = (
    PatternSyncPrimitive(worktrees=["augment", "cline", "copilot"]) >>
    ReviewPrimitive(auto_approve_threshold=0.8) >>
    IntegrationPrimitive(strategy="create-pr") >>
    NotificationPrimitive(targets="all-agents")
)

# Run coordination
context = WorkflowContext(workflow_id="worktree-coordination")
results = await coordination_workflow.execute({}, context)
```

---

## 📚 Reference

### Related Documentation

- **Git Worktree Guide:** `GIT_WORKTREE_SUMMARY.md`
- **AI Coder Workspaces:** `AI_CODER_WORKSPACES_GUIDE.md`
- **Logseq KB:** `logseq/ADVANCED_FEATURES.md`
- **Agent Instructions:** `AGENTS.md`

### External Resources

- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
- [Logseq Graph Sharing](https://docs.logseq.com/)
- [TTA.dev Primitives Catalog](PRIMITIVES_CATALOG.md)

---

## 🆘 Troubleshooting

### Issue: Sync script fails

**Symptom:** `sync-learnings.py` exits with error

**Solutions:**
1. Check worktree paths in script match actual locations
2. Ensure `.worktree/` directories exist in agent worktrees
3. Verify file permissions (need write access to orchestrator)
4. Check disk space

### Issue: Shared KB conflicts

**Symptom:** Logseq shows merge conflicts in shared pages

**Solutions:**
1. Only orchestrator should modify shared pages
2. Agents create new pages with `#from-{agent}` tag
3. If conflict occurs, orchestrator resolves manually
4. Consider using Logseq's conflict resolution UI

### Issue: Pattern not appearing in target worktree

**Symptom:** Integrated pattern not visible in agent worktree

**Solutions:**
1. Check if `logseq/shared/` symlink is correct
2. Refresh Logseq in agent worktree
3. Verify pattern was actually added to shared KB
4. Check integration strategy (create-pr vs auto-apply)

### Issue: Worktrees diverged significantly

**Symptom:** Agent worktree has 100+ commits difference from main

**Solutions:**
1. This is EXPECTED if agents work on different features
2. Only concern if blocking integration
3. Rebase agent branch if needed: `git rebase main`
4. Consider if agent should merge back to main

---

## 🎯 Summary

**The Elegant Solution:**

1. **Isolation:** Git worktrees provide natural isolation
2. **Coordination:** Shared Logseq KB + orchestrator scripts
3. **Learning:** Explicit pattern export/import workflow
4. **Integration:** Orchestrator reviews and promotes patterns
5. **Automation:** Scripts handle mechanical sync tasks
6. **Safety:** Multi-layer safeguards prevent conflicts

**Like 4 developers, but better:**
- No context switching (each agent has dedicated environment)
- Shared knowledge base (Logseq)
- Clear roles (orchestrator vs agents)
- Automated coordination (scripts)
- Explicit communication (tagged patterns)

**This is TTA.dev eating its own dog food** - using agent coordination principles to coordinate actual AI agents. 🎉

---

**Last Updated:** November 17, 2025
**Maintained By:** TTA.dev Orchestrator
**Version:** 1.0 (Production-Ready)


---
**Logseq:** [[TTA.dev/Docs/Development/Git/Worktree_coordination_protocol]]
