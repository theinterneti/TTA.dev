# TTA.dev Git Worktree Setup Guide

**Your Multi-Agent Development Environment**

## 🎯 Current Setup

You have **4 Git worktrees** for TTA.dev:

| Worktree | Location | Branch | Purpose | AI Agent |
|----------|----------|--------|---------|----------|
| **Main (Hub)** | `~/repos/TTA.dev` | `main` | Central repository, integration point | All agents (shared) |
| **Copilot** | `~/repos/TTA.dev-copilot` | `agent/copilot` | GitHub Copilot development | GitHub Copilot |
| **Cline** | `~/repos/TTA.dev-cline` | `agent/cline` | Cline/Claude development | Cline |
| **Augment** | `~/repos/TTA.dev-augment` | `agent/augment` | Augment Code development | Augment |

**Backup:** `~/repos/TTA.dev-copilot-backup` (should be removed once stable)

---

## 📋 Git Worktree Architecture

### How It Works

```
TTA.dev (main repository)
├── .git/                          ← Main Git directory
│   └── worktrees/
│       ├── TTA.dev-copilot/       ← Worktree metadata
│       ├── TTA.dev-cline/
│       └── TTA.dev-augment/
├── [main branch files]
│
~/repos/TTA.dev-copilot/           ← Worktree checkout
├── .git → points to main .git
├── [agent/copilot branch files]
│
~/repos/TTA.dev-cline/
├── .git → points to main .git
├── [agent/cline branch files]
│
~/repos/TTA.dev-augment/
├── .git → points to main .git
├── [agent/augment branch files]
```

**Benefits:**
- ✅ Each agent has isolated workspace
- ✅ All share same Git history
- ✅ Easy to switch contexts
- ✅ No need to stash/commit when switching agents

---

## 🔧 Essential Git Configuration

### 1. Verify Worktree Setup

```bash
cd ~/repos/TTA.dev
git worktree list
```

**Expected Output:**
```
/home/thein/repos/TTA.dev                4481d58 [main]
/home/thein/repos/TTA.dev-copilot        a1b2c3d [agent/copilot]
/home/thein/repos/TTA.dev-cline          e4f5g6h [agent/cline]
/home/thein/repos/TTA.dev-augment        i7j8k9l [agent/augment]
```

### 2. Set Git Config (Per Worktree)

Some settings should be **per-worktree** (different for each agent):

```bash
# In each worktree, set agent-specific config
cd ~/repos/TTA.dev-copilot
git config --worktree user.email "copilot@tta.dev"
git config --worktree user.name "GitHub Copilot Agent"

cd ~/repos/TTA.dev-cline
git config --worktree user.email "cline@tta.dev"
git config --worktree user.name "Cline Agent"

cd ~/repos/TTA.dev-augment
git config --worktree user.email "augment@tta.dev"
git config --worktree user.name "Augment Agent"
```

### 3. Shared Git Config (Global)

Other settings should be **global** (same across all worktrees):

```bash
cd ~/repos/TTA.dev

# These apply to ALL worktrees
git config core.autocrlf input
git config pull.rebase false
git config init.defaultBranch main
git config fetch.prune true
git config diff.algorithm histogram
```

### 4. Agent-Specific .gitignore

Each worktree can have **different ignored files**:

```bash
# Example: Copilot worktree might ignore different temp files
cd ~/repos/TTA.dev-copilot
echo ".copilot-cache/" >> .git/info/exclude

cd ~/repos/TTA.dev-cline
echo ".cline-temp/" >> .git/info/exclude
```

**Note:** Use `.git/info/exclude` for worktree-specific ignores (not committed)

---

## 📂 File Management Strategy

### What Should Be Different Per Worktree?

**Agent-specific files (keep separate):**
- VS Code workspace files (`.code-workspace`)
- Agent configuration (`.cline/`, `.augment/`, etc.)
- Virtual environments (`.venv/`)
- Agent-specific temp files
- IDE settings (`.vscode/settings.json` if agent-specific)

**Shared files (commit to main):**
- Source code (`packages/`, `scripts/`)
- Documentation (`docs/`, `README.md`, etc.)
- Tests (`tests/`)
- Configuration templates (`.env.example`)
- Toolsets (`.vscode/copilot-toolsets.jsonc`)

### Handling Workspace Files

Your workspace files are currently in the main repo. **Move them to respective worktrees:**

```bash
# Move workspace files to their respective worktrees
mv ~/repos/TTA.dev/copilot-worktree.code-workspace ~/repos/TTA.dev-copilot/workspace.code-workspace
mv ~/repos/TTA.dev/cline-worktree.code-workspace ~/repos/TTA.dev-cline/workspace.code-workspace
mv ~/repos/TTA.dev/augment-worktree.code-workspace ~/repos/TTA.dev-augment/workspace.code-workspace

# Update .gitignore in main repo to ignore workspace files
cd ~/repos/TTA.dev
echo "*.code-workspace" >> .gitignore
```

### .venv Isolation

Each worktree should have its **own virtual environment**:

```bash
# Create separate venvs
cd ~/repos/TTA.dev-copilot && uv venv
cd ~/repos/TTA.dev-cline && uv venv
cd ~/repos/TTA.dev-augment && uv venv

# Add to .gitignore (already there, but verify)
cd ~/repos/TTA.dev
grep ".venv" .gitignore  # Should show .venv/
```

**Why?** Prevents conflicts when agents install different package versions.

---

## 🔀 Workflow Patterns

### Pattern 1: Feature Development (Agent-Specific)

```bash
# Agent works in their worktree
cd ~/repos/TTA.dev-copilot
git checkout -b feature/copilot-router-enhancement

# Make changes, commit
git add .
git commit -m "feat: Add smart routing to RouterPrimitive"

# Push to remote
git push -u origin feature/copilot-router-enhancement

# Create PR from this branch
gh pr create --title "feat: Smart routing enhancement" --base main
```

### Pattern 2: Syncing with Main

```bash
# From any worktree, sync with main
cd ~/repos/TTA.dev-copilot
git fetch origin
git rebase origin/main

# Or use main worktree to pull latest
cd ~/repos/TTA.dev
git pull origin main

# All worktrees see the update (shared .git)
```

### Pattern 3: Cross-Agent Collaboration

```bash
# Agent 1 (Copilot) creates feature
cd ~/repos/TTA.dev-copilot
git checkout -b feature/new-primitive
# ... work ...
git push -u origin feature/new-primitive

# Agent 2 (Cline) reviews and extends
cd ~/repos/TTA.dev-cline
git fetch origin
git checkout feature/new-primitive
# ... review, extend ...
git commit -m "test: Add tests for new primitive"
git push origin feature/new-primitive
```

### Pattern 4: Emergency Fix in Main

```bash
# Go to main worktree
cd ~/repos/TTA.dev
git checkout main
git pull origin main

# Make fix
# ... fix ...
git commit -m "fix: Critical bug in cache primitive"
git push origin main

# All agent worktrees can now sync
cd ~/repos/TTA.dev-copilot && git fetch origin
cd ~/repos/TTA.dev-cline && git fetch origin
cd ~/repos/TTA.dev-augment && git fetch origin
```

---

## 🛡️ Safety & Best Practices

### 1. Branch Protection

**Keep agent branches separate:**
- `agent/copilot` → Only GitHub Copilot works here
- `agent/cline` → Only Cline works here
- `agent/augment` → Only Augment works here
- Feature branches → Any agent can work

### 2. Commit Attribution

Use **worktree-specific git config** so you know which agent made changes:

```bash
git log --oneline --all | head -10
# Shows commits with agent-specific authors
```

### 3. Prevent Accidental Cross-Contamination

**Create coordination notices:**

```bash
# In each agent worktree, create a notice file
cd ~/repos/TTA.dev-copilot
cat > .COORDINATION_NOTICE << 'EOF'
⚠️ COORDINATION NOTICE

This is the GitHub Copilot agent worktree.
Branch: agent/copilot

Before making changes:
1. Check if another agent is working on related code
2. Sync with main: git fetch origin && git rebase origin/main
3. Coordinate via GitHub Issues/PRs

Other Agent Worktrees:
- Cline: ~/repos/TTA.dev-cline
- Augment: ~/repos/TTA.dev-augment
- Main: ~/repos/TTA.dev
EOF

# Repeat for other worktrees with appropriate names
```

### 4. Regular Cleanup

**Check for stale branches:**

```bash
cd ~/repos/TTA.dev
git fetch --prune
git branch -vv | grep 'gone]'  # Shows branches deleted on remote
```

**Remove old worktrees:**

```bash
# If you delete a branch, remove its worktree
git worktree remove ~/repos/TTA.dev-old-branch
```

---

## 🗂️ Directory Structure Best Practices

### Main Repository (`~/repos/TTA.dev`)

```
TTA.dev/
├── .git/                          # Git database
├── .gitignore                     # Shared ignore rules
├── packages/                      # Shared source code
├── docs/                          # Shared documentation
├── scripts/                       # Shared automation
├── tests/                         # Shared tests
└── README.md                      # Shared main README
```

**DO commit here:**
- Production code
- Documentation
- Tests
- Shared configuration

**DON'T commit here:**
- Workspace files (`.code-workspace`)
- Virtual environments (`.venv/`)
- Agent-specific temp files

### Agent Worktrees (`~/repos/TTA.dev-{agent}`)

```
TTA.dev-copilot/
├── .git                           # → points to main .git
├── .venv/                         # Agent-specific venv (ignored)
├── workspace.code-workspace       # Agent-specific workspace (ignored)
├── .copilot-temp/                 # Agent temp files (ignored)
├── .COORDINATION_NOTICE           # Agent identity (ignored)
├── packages/                      # Same as main (via git)
├── docs/                          # Same as main (via git)
└── README.md                      # Same as main (via git)
```

**Keep separate:**
- Virtual environments
- Workspace configurations
- Agent-specific settings
- Temporary files

**Share via Git:**
- All source code
- All documentation
- All tests

---

## 🚀 Quick Start Commands

### Daily Workflow

```bash
# Morning: Sync all worktrees with main
cd ~/repos/TTA.dev && git pull origin main
cd ~/repos/TTA.dev-copilot && git fetch origin && git rebase origin/main
cd ~/repos/TTA.dev-cline && git fetch origin && git rebase origin/main
cd ~/repos/TTA.dev-augment && git fetch origin && git rebase origin/main

# Start work in specific agent worktree
cd ~/repos/TTA.dev-copilot
code workspace.code-workspace
```

### Create New Feature Branch

```bash
# From any worktree
cd ~/repos/TTA.dev-copilot
git checkout -b feature/my-awesome-feature
# Work on feature...
git push -u origin feature/my-awesome-feature
```

### Switch Between Agents

```bash
# No need to commit/stash! Just switch directories
cd ~/repos/TTA.dev-copilot  # Work with Copilot
cd ~/repos/TTA.dev-cline    # Work with Cline
cd ~/repos/TTA.dev-augment  # Work with Augment
```

---

## 🧹 Cleanup Tasks

### Remove Backup Worktree

Once you're confident the setup is stable:

```bash
# Verify backup is not needed
cd ~/repos/TTA.dev-copilot-backup
git status  # Check for uncommitted changes

# If safe, remove
rm -rf ~/repos/TTA.dev-copilot-backup
```

### Fix Workspace File Locations

```bash
# Move workspace files out of main repo
cd ~/repos/TTA.dev

# Create workspace files in each worktree
cat > ~/repos/TTA.dev-copilot/workspace.code-workspace << 'EOF'
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"python.defaultInterpreterPath": ".venv/bin/python"
	}
}
EOF

cat > ~/repos/TTA.dev-cline/workspace.code-workspace << 'EOF'
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"python.defaultInterpreterPath": ".venv/bin/python"
	}
}
EOF

cat > ~/repos/TTA.dev-augment/workspace.code-workspace << 'EOF'
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"python.defaultInterpreterPath": ".venv/bin/python"
	}
}
EOF

# Remove old worktree files from main repo
git rm *-worktree.code-workspace
git commit -m "refactor: Move worktree workspace files to respective worktrees"
```

---

## 🔍 Troubleshooting

### Problem: Worktree shows wrong branch

```bash
cd ~/repos/TTA.dev-copilot
git branch  # Check current branch
git checkout agent/copilot  # Switch to correct branch
```

### Problem: Can't delete branch (in use by worktree)

```bash
# Remove worktree first
git worktree remove ~/repos/TTA.dev-old-branch
# Then delete branch
git branch -d old-branch
```

### Problem: Conflicts between worktrees

```bash
# This shouldn't happen! Worktrees share .git but have different working directories
# If you see conflicts, you're likely in the same branch across multiple worktrees (not recommended)

# Fix: Ensure each worktree is on a different branch
cd ~/repos/TTA.dev-copilot && git branch
cd ~/repos/TTA.dev-cline && git branch
cd ~/repos/TTA.dev-augment && git branch
```

### Problem: Lost track of which worktree is which

```bash
# List all worktrees with branches
cd ~/repos/TTA.dev
git worktree list

# Or create identification files
echo "COPILOT WORKTREE" > ~/repos/TTA.dev-copilot/.AGENT_ID
echo "CLINE WORKTREE" > ~/repos/TTA.dev-cline/.AGENT_ID
echo "AUGMENT WORKTREE" > ~/repos/TTA.dev-augment/.AGENT_ID
```

---

## 📊 Recommended .gitignore Updates

Add to `~/repos/TTA.dev/.gitignore`:

```gitignore
# Agent-specific files (don't commit these)
*.code-workspace
.COORDINATION_NOTICE
.AGENT_ID

# Virtual environments (per-worktree)
.venv/
venv/

# Agent-specific temp directories
.copilot-temp/
.cline-temp/
.augment-temp/

# Agent configuration (per-worktree)
.cline/sessions/
.augment/cache/
```

---

## 🎯 Summary & Action Items

### ✅ What You Have

- [x] Main repository at `~/repos/TTA.dev`
- [x] 3 agent worktrees (Copilot, Cline, Augment)
- [x] Git worktree setup working
- [x] Each agent can work independently

### 🔧 Immediate Actions

1. **Set worktree-specific git config** (agent names/emails)
2. **Move workspace files** to respective worktrees
3. **Create coordination notices** in each worktree
4. **Update .gitignore** to exclude workspace files
5. **Remove backup** once stable

### 📝 Ongoing Practices

1. **Daily sync** all worktrees with main
2. **Use feature branches** for agent work
3. **Coordinate via PRs** for cross-agent changes
4. **Keep main worktree clean** (integration point only)
5. **Document agent decisions** in commit messages

---

**Last Updated:** November 17, 2025
**Maintained by:** TTA.dev Team
