# TTA.dev Worktree Coordination - System Architecture

**Visual guide to understanding the 4-worktree coordination system**

---

## 🏗️ System Overview

```
                    ┌──────────────────────────────────────┐
                    │   TTA.dev (ORCHESTRATOR)             │
                    │   Branch: experimental/...           │
                    │                                      │
                    │   Responsibilities:                  │
                    │   • Sync patterns from all agents    │
                    │   • Review and approve patterns      │
                    │   • Maintain shared knowledge base   │
                    │   • Distribute approved learnings    │
                    │   • Monitor coordination health      │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │    Periodic Sync (sync-learnings.py)│
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ↓                          ↓                          ↓
┌───────────────┐          ┌───────────────┐        ┌───────────────┐
│ TTA-Augment   │          │ TTA-Cline     │        │ TTA-Copilot   │
│ agent/augment │          │ experimental/ │        │ agent/copilot │
│               │          │ issue-collab  │        │               │
│ Fast coding   │          │ Research      │        │ GitHub        │
│ Completion    │          │ Deep analysis │        │ workflows     │
└───────┬───────┘          └───────┬───────┘        └───────┬───────┘
        │                          │                          │
        │  Creates patterns        │  Creates patterns        │
        │  in .worktree/           │  in .worktree/           │
        │  local-patterns/         │  local-patterns/         │
        └──────────────────────────┴──────────────────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │    Shared Knowledge Base     │
                    │    logseq/shared/            │
                    │    (Symlinked to all)        │
                    └──────────────────────────────┘
```

---

## 📁 Directory Architecture

### Orchestrator (TTA.dev)

```
/home/thein/repos/TTA.dev/
│
├── .worktree/                          # Coordination infrastructure
│   ├── coordination/                   # Central coordination hub
│   │   ├── agent-augment/              # Patterns from Augment
│   │   │   ├── 20251117-pattern1.md
│   │   │   └── 20251117-pattern2.md
│   │   │
│   │   ├── agent-cline/                # Patterns from Cline
│   │   │   ├── 20251117-pattern3.md
│   │   │   └── 20251117-pattern4.md
│   │   │
│   │   ├── agent-copilot/              # Patterns from Copilot
│   │   │   └── 20251117-pattern5.md
│   │   │
│   │   └── integration-queue/          # Ready for distribution
│   │       ├── approved-pattern1.md
│   │       └── approved-pattern2.md
│   │
│   ├── sync-status.json                # Last sync metadata
│   └── coordination.log                # Coordination activity log
│
├── logseq/
│   ├── journals/                       # Orchestrator's daily work
│   ├── pages/                          # Orchestrator's private pages
│   │
│   └── shared/                         # 🌟 SHARED KB (canonical)
│       ├── pages/
│       │   ├── Worktree Patterns/      # Approved patterns
│       │   │   ├── Cache Optimization.md
│       │   │   ├── Retry Strategy.md
│       │   │   └── Error Handling.md
│       │   │
│       │   ├── Cross-Agent Learnings/  # Collaborative discoveries
│       │   │   └── Multi-Agent Workflow.md
│       │   │
│       │   └── Integration Decisions/  # Why patterns were chosen
│       │       └── 2025-11-17 Integration.md
│       │
│       └── coordination-dashboard.md   # Live status dashboard
│
├── scripts/
│   └── worktree/
│       ├── sync-learnings.py           # Sync automation
│       ├── coordination-status.py      # Status dashboard
│       ├── init-coordination.sh        # Setup script
│       └── templates/
│           └── pattern-template.md     # Pattern template
│
└── WORKTREE_COORDINATION_PROTOCOL.md   # This system's docs
```

### Agent Worktree (Example: TTA-Cline)

```
/home/thein/repos/TTA.dev-cline/
│
├── .worktree/                          # Agent-specific (gitignored)
│   ├── local-patterns/                 # 🎯 CREATE PATTERNS HERE
│   │   ├── 20251117-performance-cache.md
│   │   ├── 20251117-testing-retry.md
│   │   └── 20251118-architecture-new-primitive.md
│   │
│   ├── experiments/                    # Active experiments
│   │   └── llm-routing-test/
│   │
│   ├── session-logs/                   # Activity logs
│   │   └── 2025-11-17.log
│   │
│   └── agent-config.yml                # Agent preferences
│
├── logseq/
│   ├── journals/                       # Agent's daily work
│   ├── pages/                          # Agent's private pages
│   │
│   └── shared/                         # 🔗 SYMLINK → TTA.dev/logseq/shared/
│                                       # (Read-only access to shared KB)
│
└── [rest of git worktree structure]
```

**Same structure for:**
- `/home/thein/repos/TTA.dev-augment/`
- `/home/thein/repos/TTA.dev-copilot/`

---

## 🔄 Data Flow

### Pattern Discovery → Integration

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Agent Discovers Pattern                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Agent (Cline):                                                 │
│  ┌──────────────────────────────────────┐                      │
│  │ Working on feature...                │                      │
│  │ Discovers: Retry with exponential    │                      │
│  │            backoff works better      │                      │
│  │                                      │                      │
│  │ Creates:                             │                      │
│  │ .worktree/local-patterns/            │                      │
│  │   20251117-recovery-retry.md         │                      │
│  │                                      │                      │
│  │ Tags: #ready-to-share                │                      │
│  └──────────────────────────────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Orchestrator Syncs                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Orchestrator (TTA.dev):                                        │
│  ┌──────────────────────────────────────┐                      │
│  │ Runs: sync-learnings.py --sync-all   │                      │
│  │                                      │                      │
│  │ Scans:                               │                      │
│  │ - TTA-Cline/.worktree/local-patterns/│                      │
│  │ - Logseq pages with #ready-to-share  │                      │
│  │                                      │                      │
│  │ Copies to:                           │                      │
│  │ .worktree/coordination/agent-cline/  │                      │
│  │   20251117-recovery-retry.md         │                      │
│  └──────────────────────────────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Orchestrator Reviews                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Human (or AI Orchestrator):                                    │
│  ┌──────────────────────────────────────┐                      │
│  │ Reads pattern file                   │                      │
│  │ Evaluates:                           │                      │
│  │   • Quality (code, docs)             │                      │
│  │   • Applicability (all agents?)      │                      │
│  │   • Conflicts (other patterns?)      │                      │
│  │                                      │                      │
│  │ Decision: APPROVE                    │                      │
│  └──────────────────────────────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Add to Shared KB                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Orchestrator:                                                  │
│  ┌──────────────────────────────────────┐                      │
│  │ Moves to integration queue:          │                      │
│  │ .worktree/coordination/               │                      │
│  │   integration-queue/                 │                      │
│  │     20251117-recovery-retry.md       │                      │
│  │                                      │                      │
│  │ Creates shared KB page:              │                      │
│  │ logseq/shared/pages/                 │                      │
│  │   Worktree Patterns/                 │                      │
│  │     Exponential Retry.md             │                      │
│  │                                      │                      │
│  │ Tags: #approved-pattern #integrated  │                      │
│  └──────────────────────────────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Other Agents Consume                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  All Agents (Augment, Copilot):                                 │
│  ┌──────────────────────────────────────┐                      │
│  │ Open Logseq                          │                      │
│  │ See: logseq/shared/pages/            │                      │
│  │        Worktree Patterns/            │                      │
│  │          Exponential Retry.md        │                      │
│  │                                      │                      │
│  │ Read pattern                         │                      │
│  │ Apply to their work                  │                      │
│  │                                      │                      │
│  │ ✓ Cross-pollination complete!        │                      │
│  └──────────────────────────────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏷️ Tagging Lifecycle

```
Pattern Journey Through States
═══════════════════════════════

┌─────────────────┐
│  Created        │   Agent creates pattern file
│  (no tag)       │   Status: Local only
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ #local-pattern  │   Agent tags as "discovered"
│                 │   Status: Local only, working on it
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ #ready-to-share │   Agent: "This is good, share it"
│                 │   Status: Will be synced next cycle
└────────┬────────┘
         │
         ↓ (sync)
┌─────────────────┐
│ #under-review   │   Orchestrator: "I'm reviewing this"
│                 │   Status: In coordination/agent-{name}/
└────────┬────────┘
         │
         ↓ (decision)
    ┌────┴────┐
    │         │
    ↓         ↓
┌─────────┐ ┌──────────┐
│REJECTED │ │ APPROVED │
└─────────┘ └────┬─────┘
               │
               ↓
        ┌─────────────────┐
        │ #approved-pattern│  Orchestrator: "This is good"
        │                 │  Status: In integration queue
        └────────┬────────┘
                 │
                 ↓
        ┌─────────────────┐
        │ #integrated     │  Orchestrator: "Added to shared KB"
        │                 │  Status: In logseq/shared/pages/
        └─────────────────┘
                 │
                 ↓
        All agents can now see it!
```

---

## 🔐 Isolation & Safety

### Git Isolation (Built-in)

```
Git Repository (TTA.dev)
│
├── .git/              ← Shared (metadata only)
│   ├── HEAD           ← Points to worktree branches
│   ├── objects/       ← Shared (commits, blobs)
│   └── worktrees/     ← Worktree metadata
│       ├── TTA.dev-augment/
│       ├── TTA.dev-cline/
│       └── TTA.dev-copilot/
│
├── TTA.dev/           ← Worktree 1: Independent working dir
│   ├── index          ← Separate staging area
│   └── [files]        ← Checked out files (branch 1)
│
├── TTA.dev-augment/   ← Worktree 2: Independent working dir
│   ├── index          ← Separate staging area
│   └── [files]        ← Checked out files (branch 2)
│
├── TTA.dev-cline/     ← Worktree 3: Independent working dir
│   ├── index          ← Separate staging area
│   └── [files]        ← Checked out files (branch 3)
│
└── TTA.dev-copilot/   ← Worktree 4: Independent working dir
    ├── index          ← Separate staging area
    └── [files]        ← Checked out files (branch 4)

✓ Each worktree has its own working directory
✓ Each has its own staging area (index)
✓ Each can checkout different branch
✓ NO FILE CONFLICTS POSSIBLE (different directories!)
```

### File System Isolation

```
                    ISOLATED                 SHARED

TTA.dev/
  .worktree/        ✓ (gitignored)
  logseq/
    journals/       ✓
    pages/          ✓
    shared/                                  ✓ (canonical)
  [code files]      ✓

TTA.dev-augment/
  .worktree/        ✓ (gitignored)
  logseq/
    journals/       ✓
    pages/          ✓
    shared/                                  ✓ (symlink)
  [code files]      ✓

TTA.dev-cline/
  .worktree/        ✓ (gitignored)
  logseq/
    journals/       ✓
    pages/          ✓
    shared/                                  ✓ (symlink)
  [code files]      ✓

TTA.dev-copilot/
  .worktree/        ✓ (gitignored)
  logseq/
    journals/       ✓
    pages/          ✓
    shared/                                  ✓ (symlink)
  [code files]      ✓

SAFETY GUARANTEES:
✓ Agents cannot modify each other's working files
✓ Agents cannot interfere with each other's git state
✓ Only orchestrator modifies shared KB (canonical)
✓ Agents read shared KB via symlink (read-only in practice)
✓ If symlink breaks, agent still works (just no shared KB)
```

---

## 📊 Metrics & Monitoring

### Dashboard View

```
╔═══════════════════════════════════════════════════════════════╗
║          TTA.dev Worktree Coordination Status                 ║
╚═══════════════════════════════════════════════════════════════╝

📍 Worktrees
───────────────────────────────────────────────────────────────
✓ orchestrator      experimental/workflow-agent-integrations
• augment           agent/augment
• cline             experimental/issue-collaboration
• copilot           agent/copilot

🔄 Sync Status
───────────────────────────────────────────────────────────────
Last Sync:          2 hours ago
Next Sync:          Auto (in 4 hours) or manual

📋 Pending Reviews
───────────────────────────────────────────────────────────────
Cline:              5 patterns (3 high priority)
Augment:            2 patterns
Copilot:            1 pattern
───────────────────────────────────────────────────────────────
Total:              8 patterns awaiting review

🚀 Integration Queue
───────────────────────────────────────────────────────────────
Ready:              3 patterns approved, ready to distribute

📈 Metrics (Last 7 Days)
───────────────────────────────────────────────────────────────
Pattern Discovery:  15 patterns (avg 2.1/day)
Approval Rate:      85% (13 of 15 approved)
Avg Review Time:    1.8 days
Cross-Pollination:  60% (9 patterns used by 2+ agents)

💡 Recommendations
───────────────────────────────────────────────────────────────
→ Review 3 high-priority patterns from Cline
→ Sync is due soon - run sync-learnings.py
→ Integration queue ready - distribute approved patterns
```

---

## 🎯 Summary

**What This Architecture Provides:**

1. **Complete Isolation**
   - Each agent has independent workspace
   - No risk of file conflicts
   - Parallel development

2. **Structured Knowledge Sharing**
   - Explicit pattern export/import
   - Centralized review process
   - Shared knowledge base

3. **Orchestrated Coordination**
   - Central authority (TTA.dev)
   - Clear workflows
   - Automated sync

4. **Production-Ready Safety**
   - Fail-safe design
   - Git-native isolation
   - Graceful degradation

5. **TTA.dev Alignment**
   - Uses primitives concepts
   - Dogfoods orchestration
   - Validates patterns

---

**Created:** November 17, 2025
**Status:** Production-Ready
**Purpose:** Visual guide to worktree coordination architecture


---
**Logseq:** [[TTA.dev/Docs/Development/Git/Worktree_coordination_architecture]]
