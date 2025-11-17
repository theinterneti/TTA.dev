# Git Worktree & Branch Quick Reference

**Date:** November 16, 2025  
**Purpose:** Quick reference for managing TTA.dev git setup

---

## 📍 Current Setup

### Worktrees
```bash
# View all worktrees
git worktree list

# Current setup:
/home/thein/repos/TTA.dev          -> feature/mcp-documentation (main repo)
/home/thein/repos/TTA.dev-augment  -> agent/augment
/home/thein/repos/TTA.dev-cline    -> hypertool
/home/thein/repos/TTA.dev-copilot  -> agent/copilot
```

### Remotes
```bash
# View remotes
git remote -v

# Should be:
TTA.dev -> git@github.com:theinterneti/TTA.dev.git
```

---

## 🎯 Common Tasks

### Switch Between Worktrees
```bash
# Go to augment worktree
cd /home/thein/repos/TTA.dev-augment

# Go to cline worktree
cd /home/thein/repos/TTA.dev-cline

# Go to copilot worktree
cd /home/thein/repos/TTA.dev-copilot

# Go to main repo
cd /home/thein/repos/TTA.dev
```

### Check Branch Status
```bash
# Current branch status
git status

# See all branches with tracking info
git branch -vv

# See only local branches
git branch

# See only remote branches
git branch -r

# See all branches (local + remote)
git branch -a
```

### Sync with Remote
```bash
# Fetch all updates
git fetch --all --prune

# Pull current branch
git pull

# Push current branch
git push TTA.dev HEAD
```

### Create New Branch
```bash
# Create and switch to new branch
git checkout -b feature/my-feature

# Push to remote and set tracking
git push -u TTA.dev feature/my-feature
```

### Delete Branches
```bash
# Delete local branch (safe - won't delete if not merged)
git branch -d branch-name

# Force delete local branch
git branch -D branch-name

# Delete remote branch
git push TTA.dev --delete branch-name
```

---

## 🧹 Cleanup Commands

### Run Automated Cleanup
```bash
# Interactive cleanup script
./scripts/git_branch_cleanup.sh
```

### Manual Cleanup Steps
```bash
# 1. Create backup
git branch backup/cleanup-$(date +%Y%m%d_%H%M%S)

# 2. Fetch and prune
git fetch --all --prune

# 3. Delete merged branches
git branch --merged main | grep -v "^\*" | grep -v "main" | xargs git branch -d

# 4. Delete remote copilot sub-PR branches
git branch -r | grep "TTA.dev/copilot/sub-pr-" | \
  sed 's/.*TTA.dev\///' | \
  xargs -I {} git push TTA.dev --delete {}
```

---

## 🔍 Investigation Commands

### View Branch History
```bash
# Commits on current branch not in main
git log --oneline main..HEAD

# Graph view of branches
git log --oneline --graph --all --decorate

# See what changed in a branch
git diff main...branch-name
```

### Check Branch Status
```bash
# Branches merged to main
git branch --merged main

# Branches not merged to main
git branch --no-merged main

# Branches ahead/behind main
git branch -vv
```

### Find Stale Branches
```bash
# Branches not updated in 30 days
git for-each-ref --sort=-committerdate --format='%(committerdate:short) %(refname:short)' refs/heads/

# Remote branches only
git for-each-ref --sort=-committerdate --format='%(committerdate:short) %(refname:short)' refs/remotes/TTA.dev/
```

---

## 🚨 Current Issues & Solutions

### Issue 1: "origin" Remote Points to Fork
```bash
# Option A: Rename
git remote rename origin copilot-fork

# Option B: Remove
git remote remove origin
```

### Issue 2: 18 Stale Copilot Sub-PR Branches
```bash
# Delete all at once (CAREFUL!)
git branch -r | grep "TTA.dev/copilot/sub-pr-" | \
  sed 's/.*TTA.dev\///' | \
  xargs -I {} git push TTA.dev --delete {}

# Or use the cleanup script (safer, interactive)
./scripts/git_branch_cleanup.sh
```

### Issue 3: Merged Local Branches Still Exist
```bash
# Check what's merged
git branch --merged main

# Delete merged branches
git branch --merged main | grep -v "^\*" | grep -v "main" | xargs git branch -d
```

---

## 📊 Current Branch Categories

### Active Worktree Branches (Keep)
- `agent/augment` - Augment agent development
- `agent/copilot` - Copilot agent development
- `hypertool` - Hypertool development
- `feature/mcp-documentation` - Current work

### Active Feature Branches (Keep)
- `feature/phase5-apm-integration` - Observability
- `feature/docs-reorganization-clean` - Documentation
- `feature/tta-dev-cli-architecture` - CLI planning
- `agentic/core-architecture` - Architecture
- `experiment/ace-integration` - ACE framework

### Fix Branches (Review)
- `fix/gemini-api-key-secret-name`
- `fix/gemini-cli-auth-config`
- `fix/gemini-cli-write-permissions`
- `fix/update-mcp-server-to-v0.20.1`
- `fix/use-ai-studio-not-vertex-ai`

### Stale Remote Branches (Delete)
- All `copilot/sub-pr-*` branches (18 total)

---

## 🛠️ Worktree Management

### Add New Worktree
```bash
# Create new worktree for branch
git worktree add /home/thein/repos/TTA.dev-newbranch branch-name

# Create worktree with new branch
git worktree add -b new-branch /home/thein/repos/TTA.dev-newbranch
```

### Remove Worktree
```bash
# Remove worktree
git worktree remove /home/thein/repos/TTA.dev-oldworktree

# Or manually delete directory and prune
rm -rf /home/thein/repos/TTA.dev-oldworktree
git worktree prune
```

### Check Worktree Status
```bash
# List all worktrees
git worktree list

# Check for issues
git worktree prune
```

---

## 📋 Pre-Commit Checklist

Before committing in any worktree:

```bash
# 1. Check you're on the right branch
git branch

# 2. See what changed
git status

# 3. See detailed changes
git diff

# 4. Stage changes
git add <files>

# 5. Commit
git commit -m "type: description"

# 6. Push to remote
git push TTA.dev HEAD
```

---

## 🔗 Documentation References

- **Full Analysis:** `GIT_WORKTREE_BRANCH_ANALYSIS.md`
- **Cleanup Script:** `scripts/git_branch_cleanup.sh`
- **Branch Organization:** `BRANCH_ORGANIZATION_COMPLETE.md`
- **Git Management:** `GIT_MANAGEMENT_SUMMARY.md`

---

## 💡 Tips

1. **Always fetch before starting work:** `git fetch --all --prune`
2. **Create backups before cleanup:** `git branch backup/before-cleanup-$(date +%Y%m%d)`
3. **Use worktrees for concurrent work:** Keep each agent in separate worktree
4. **Review before deleting:** Use `git log` to check branch history
5. **Keep branch names descriptive:** Use `feature/`, `fix/`, `docs/` prefixes

---

**Quick Help:**
```bash
# Run automated cleanup
./scripts/git_branch_cleanup.sh

# View detailed analysis
less GIT_WORKTREE_BRANCH_ANALYSIS.md

# Check current status
git worktree list && git branch -vv
```
