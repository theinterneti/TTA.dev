# TTA.dev Worktree Quick Reference

**Fast lookup for multi-agent Git worktree operations**

## 📍 Worktree Locations

```bash
Main:    ~/repos/TTA.dev              # Hub (main branch)
Copilot: ~/repos/TTA.dev-copilot      # agent/copilot
Cline:   ~/repos/TTA.dev-cline        # agent/cline
Augment: ~/repos/TTA.dev-augment      # agent/augment
```

## ⚡ Common Commands

### List All Worktrees
```bash
cd ~/repos/TTA.dev && git worktree list
```

### Switch Worktrees
```bash
cd ~/repos/TTA.dev-copilot  # Work with Copilot
cd ~/repos/TTA.dev-cline    # Work with Cline
cd ~/repos/TTA.dev-augment  # Work with Augment
```

### Daily Sync (Morning Routine)
```bash
# Sync main
cd ~/repos/TTA.dev && git pull origin main

# Sync all agent worktrees
cd ~/repos/TTA.dev-copilot && git fetch origin && git rebase origin/main
cd ~/repos/TTA.dev-cline && git fetch origin && git rebase origin/main
cd ~/repos/TTA.dev-augment && git fetch origin && git rebase origin/main
```

### Create Feature Branch
```bash
# From any worktree
cd ~/repos/TTA.dev-copilot
git checkout -b feature/my-feature
# ... work ...
git push -u origin feature/my-feature
```

### Open Workspace
```bash
code ~/repos/TTA.dev-copilot/workspace.code-workspace
code ~/repos/TTA.dev-cline/workspace.code-workspace
code ~/repos/TTA.dev-augment/workspace.code-workspace
```

## 🔧 Worktree Management

### Add New Worktree
```bash
cd ~/repos/TTA.dev
git worktree add ~/repos/TTA.dev-newagent -b agent/newagent
```

### Remove Worktree
```bash
cd ~/repos/TTA.dev
git worktree remove ~/repos/TTA.dev-oldagent
```

### Prune Deleted Worktrees
```bash
cd ~/repos/TTA.dev
git worktree prune
```

## 🛡️ Safety Checks

### Check Current Branch
```bash
cd ~/repos/TTA.dev-copilot && git branch
```

### Verify Clean State
```bash
cd ~/repos/TTA.dev-copilot && git status
```

### See Uncommitted Changes
```bash
cd ~/repos/TTA.dev-copilot && git diff
```

## 🚀 Setup Scripts

### Initial Setup
```bash
~/repos/TTA.dev/scripts/setup-worktrees.sh
```

### Create Virtual Environments
```bash
cd ~/repos/TTA.dev-copilot && uv venv && uv sync
cd ~/repos/TTA.dev-cline && uv venv && uv sync
cd ~/repos/TTA.dev-augment && uv venv && uv sync
```

## 🔍 Git Configuration

### View Worktree-Specific Config
```bash
cd ~/repos/TTA.dev-copilot
git config --worktree --list
```

### Set Worktree Config
```bash
cd ~/repos/TTA.dev-copilot
git config --worktree user.email "copilot@tta.dev"
git config --worktree user.name "GitHub Copilot Agent"
```

## 📊 Status Overview

### All Worktrees Status
```bash
for dir in ~/repos/TTA.dev-*; do
    echo "=== $(basename $dir) ==="
    cd "$dir" && git status -sb
    echo ""
done
```

### All Branches
```bash
cd ~/repos/TTA.dev
git branch -a
```

## 🧹 Cleanup

### Remove Backup Worktree
```bash
rm -rf ~/repos/TTA.dev-copilot-backup
```

### Clean Untracked Files
```bash
cd ~/repos/TTA.dev-copilot
git clean -fd  # Careful! This deletes untracked files
```

## 🆘 Troubleshooting

### Worktree on Wrong Branch
```bash
cd ~/repos/TTA.dev-copilot
git checkout agent/copilot
```

### Detached HEAD State
```bash
cd ~/repos/TTA.dev-copilot
git checkout agent/copilot
```

### Conflicts After Rebase
```bash
cd ~/repos/TTA.dev-copilot
git rebase --abort  # Start over
# Or resolve conflicts and:
git add .
git rebase --continue
```

## 📚 Full Documentation

See: `~/repos/TTA.dev/WORKTREE_SETUP_GUIDE.md`


---
**Logseq:** [[TTA.dev/Docs/Reference/Worktree_quick_reference]]
