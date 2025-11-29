# TTA.dev Worktree Coordination - Quick Start

**Get up and running in 5 minutes**

---

## 🎯 What Is This?

You have 4 worktrees on the same machine:

1. **TTA.dev** (main) - Orchestrator, coordinates the other 3
2. **TTA.dev-augment** - Augment Code agent
3. **TTA.dev-cline** - Cline (Claude) agent  
4. **TTA.dev-copilot** - GitHub Copilot agent

This system lets them work independently but **share learnings** automatically.

---

## 🚀 Initial Setup (One-Time)

### Step 1: Initialize Coordination System

```bash
cd /home/thein/repos/TTA.dev
bash scripts/worktree/init-coordination.sh
```

**This creates:**
- Coordination directories in TTA.dev
- Shared knowledge base in Logseq
- Local pattern directories in each agent worktree
- Symlinks for shared KB

**Time:** ~1 minute

---

### Step 2: Verify Setup

```bash
python scripts/worktree/coordination-status.py
```

**Expected output:**
```
✓ orchestrator  - experimental/workflow-agent-integrations (orchestrator)
✓ augment       - agent/augment
✓ cline         - experimental/issue-collaboration
✓ copilot       - agent/copilot
```

**If any worktree shows "NOT FOUND"** - update the paths in the scripts.

---

## 📋 Daily Workflow

### As Orchestrator (TTA.dev main)

**Morning routine:**

```bash
# 1. Check what happened overnight
python scripts/worktree/coordination-status.py

# 2. Sync latest learnings from all agents
python scripts/worktree/sync-learnings.py --sync-all

# 3. Review new patterns (if any)
ls .worktree/coordination/agent-*/
```

**When you see new patterns:**

```bash
# Read the pattern
cat .worktree/coordination/agent-cline/20251117-performance-cache.md

# If good, move to integration queue
mv .worktree/coordination/agent-cline/20251117-performance-cache.md \
   .worktree/coordination/integration-queue/

# Create Logseq page for it (manual for now)
# File: logseq/shared/pages/Worktree Patterns/Cache Optimization.md
```

---

### As Agent Worktree (Augment/Cline/Copilot)

**When you discover something useful:**

```bash
cd /home/thein/repos/TTA.dev-{agent}

# Copy pattern template
cp /home/thein/repos/TTA.dev/scripts/worktree/templates/pattern-template.md \
   .worktree/local-patterns/20251117-performance-new-pattern.md

# Edit the pattern file
# Fill in: problem, solution, code, evidence

# Done! Orchestrator will sync it next time
```

**Or tag a Logseq page:**

```markdown
## [[My Useful Pattern]]

#ready-to-share

[Your pattern documentation]
```

---

## 🔄 Sync Schedule

### Option 1: Manual (Recommended Initially)

```bash
# Run whenever you want to sync
python scripts/worktree/sync-learnings.py --sync-all
```

### Option 2: Automated (Optional)

```bash
# Add to crontab for automatic syncing every 6 hours
crontab -e

# Add this line:
0 */6 * * * cd /home/thein/repos/TTA.dev && python scripts/worktree/sync-learnings.py --sync-all >> logs/coordination.log 2>&1
```

---

## 📁 Key Directories

### In Orchestrator (TTA.dev)

```
.worktree/
├── coordination/
│   ├── agent-augment/      ← Patterns from augment
│   ├── agent-cline/        ← Patterns from cline
│   ├── agent-copilot/      ← Patterns from copilot
│   └── integration-queue/  ← Ready to distribute

logseq/shared/              ← Shared knowledge base
```

### In Agent Worktrees

```
.worktree/
├── local-patterns/         ← Put your patterns here
├── experiments/            ← For experiments
└── agent-config.yml        ← Config (not used yet)

logseq/shared/              ← Symlink to TTA.dev's shared KB
```

---

## 🏷️ Tagging Guide

**In your Logseq pages:**

- `#local-pattern` - Just for me, not ready to share
- `#ready-to-share` - Ready for orchestrator to review
- `#approved-pattern` - Orchestrator approved (in shared KB)
- `#integrated` - Applied across all worktrees

**In pattern files:**

```markdown
**Status:** #ready-to-share
```

---

## 💡 Example Scenario

**Cline discovers a retry pattern:**

```bash
# In TTA.dev-cline worktree
cd /home/thein/repos/TTA.dev-cline

# Create pattern file
cat > .worktree/local-patterns/20251117-recovery-retry-optimization.md << 'EOF'
# Exponential Backoff Retry Pattern

**Discovered By:** agent/cline
**Category:** recovery
**Impact:** high

## Problem
Linear retry was causing delays...

## Pattern
Use exponential backoff with jitter...

[etc.]
EOF
```

**Orchestrator syncs:**

```bash
# In TTA.dev (main)
python scripts/worktree/sync-learnings.py --sync-all

# Output:
#   Agent: cline
#   ✓ New: 20251117-recovery-retry-optimization.md
```

**Orchestrator reviews and approves:**

```bash
# Move to integration queue
mv .worktree/coordination/agent-cline/20251117-recovery-retry-optimization.md \
   .worktree/coordination/integration-queue/

# Create shared KB page
# (Manual for now - future script will automate)
```

**Other agents see it:**

```bash
# In TTA.dev-augment or TTA.dev-copilot
# Check logseq/shared/pages/Worktree Patterns/
# Pattern is now visible to all!
```

---

## 🆘 Common Issues

### "Worktree not found"

**Problem:** Script can't find your worktree

**Solution:**
```bash
# Edit the script
nano scripts/worktree/sync-learnings.py

# Update WORKTREES dict with your actual paths
WORKTREES = {
    "augment": Path("/your/actual/path/TTA.dev-augment"),
    # ...
}
```

### "Symlink broken"

**Problem:** `logseq/shared` link not working in agent worktree

**Solution:**
```bash
cd /home/thein/repos/TTA.dev-{agent}
rm -f logseq/shared
ln -s /home/thein/repos/TTA.dev/logseq/shared logseq/shared
```

### "No patterns found"

**Problem:** Sync finds no patterns

**Solution:**
- Make sure patterns are in `.worktree/local-patterns/` directory
- Check file naming: `YYYYMMDD-category-name.md`
- Try `--dry-run` to see what would be synced

---

## 📚 Full Documentation

**For complete details, see:**

- **Main Protocol:** `WORKTREE_COORDINATION_PROTOCOL.md`
- **Scripts README:** `scripts/worktree/README.md`
- **Pattern Template:** `scripts/worktree/templates/pattern-template.md`

---

## ✅ Success Checklist

After setup, you should be able to:

- [ ] Run `coordination-status.py` and see all 4 worktrees
- [ ] Create a test pattern in agent worktree
- [ ] Sync with `sync-learnings.py --sync-all`
- [ ] See pattern appear in orchestrator's coordination directory
- [ ] View shared KB in Logseq (symlink works)

**If all checked, you're ready to go!** 🎉

---

**Questions?** Check the full docs or ask in the TTA.dev discussions.

---

**Last Updated:** November 17, 2025
