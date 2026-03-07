# 🤖 Lazy Dev Repo Manager

**Never think about git/GitHub again!** Your AI-powered assistant handles everything.

## Quick Start

```bash
# Interactive mode (easiest!)
./scripts/lazy_dev.py

# Or use commands directly
./scripts/lazy_dev.py status              # What's happening?
./scripts/lazy_dev.py work-on "feature"   # Start working
./scripts/lazy_dev.py pr                  # Create PR
```

---

## Features

### 🌿 Smart Branch Management
- **Auto-naming**: Converts "fix login bug" → `fix/login-bug-20251116`
- **Type-based**: feature/, fix/, docs/, test/, refactor/, chore/
- **Auto-sync**: Always starts from latest main

### 📋 AI-Powered PRs
- **Auto-description**: AI generates comprehensive PR description
- **Auto-review**: Requests @copilot review automatically  
- **Draft support**: Create draft PRs for WIP
- **Smart titles**: Extracts from branch name

### 🤝 Agent Collaboration
- **@copilot integration**: Automatic code reviews
- **@cline support**: CLI-based agent collaboration  
- **Multi-agent**: Coordinate multiple AI agents
- **Real-time**: Agents respond in PR comments

### 📊 Status Dashboard
- **Current branch** and changes
- **Open PRs** and issues
- **Sync status** (ahead/behind)
- **Quick actions**

---

## Commands

### Interactive Mode

```bash
./scripts/lazy_dev.py
```

**Menu:**
1. 🌿 Start working on something (create branch)
2. 📋 Create a PR  
3. 🤝 Collaborate with agents on PR
4. 🎯 Assign agents to an issue
5. 📊 Show status
6. 🚀 Push current work
7. 🔄 Sync with main

### Direct Commands

```bash
# Check status
./scripts/lazy_dev.py status

# Start working
./scripts/lazy_dev.py work-on "add authentication"
./scripts/lazy_dev.py work-on "fix dashboard crash"

# Create PR (auto-generates description)
./scripts/lazy_dev.py pr
./scripts/lazy_dev.py pr "Custom PR title"
```

---

## Workflows

### 1️⃣ Start New Feature

```bash
# One command!
./scripts/lazy_dev.py work-on "user profiles"

# Creates: feature/user-profiles-20251116
# Based on: latest main
# Status: Ready to code
```

### 2️⃣ Create PR with AI Review

```bash
# Make changes
git add .
git commit -m "Add user profile endpoints"

# Create PR (AI does the rest)
./scripts/lazy_dev.py pr

# What happens:
# ✅ Pushes changes
# ✅ Generates PR description with AI
# ✅ Creates PR
# ✅ Requests @copilot review automatically
# ✅ Returns PR link
```

### 3️⃣ Collaborate with Multiple Agents

```bash
# Interactive
./scripts/lazy_dev.py
# → Choose "3. Collaborate with agents on PR"
# → Enter PR number
# → Agents start reviewing

# Or programmatically
python3 << EOF
from scripts.lazy_dev import LazyDevManager
import asyncio

async def collaborate():
    manager = LazyDevManager()
    await manager.collaborate_on_pr(
        pr_number=109,
        agents=["copilot", "cline"]
    )

asyncio.run(collaborate())
EOF
```

### 4️⃣ Assign Issue to Copilot

```bash
# Copilot will create branch, implement, and PR
./scripts/lazy_dev.py
# → Choose "4. Assign agents to an issue"  
# → Enter issue number
# → Enter task description
# → @copilot gets assigned and starts work
```

---

## Advanced Usage

### Python API

```python
from scripts.lazy_dev import LazyDevManager, WorkType
import asyncio

async def main():
    manager = LazyDevManager()
    
    # Create feature branch
    branch = await manager.create_branch(
        "authentication system",
        WorkType.FEATURE
    )
    
    # Later... create PR
    pr_number = await manager.create_pr(
        title="feat: Add OAuth authentication",
        draft=False
    )
    
    # Start agent collaboration
    await manager.collaborate_on_pr(
        pr_number,
        agents=["copilot", "cline"]
    )

asyncio.run(main())
```

### Git State Checking

```python
manager = LazyDevManager()
state = manager.get_repo_state()

print(f"Branch: {state.current_branch}")
print(f"Changes: {state.has_changes}")
print(f"PRs: {len(state.open_prs)}")
```

---

## Agent Integration

### @copilot

**Automatic Review:**
```bash
# Every PR auto-requests @copilot review
./scripts/lazy_dev.py pr
# → @copilot reviews code
# → Comments on issues
# → Suggests improvements
```

**Issue Assignment:**
```bash
# Assign @copilot to implement feature
gh issue develop <issue-number>
# Or use lazy_dev interactive mode
```

### @cline

**CLI Collaboration:**
```bash
# Cline can be referenced in PR comments
# Example:
"@cline please review the error handling in this PR"
```

**Real-time Commands:**
```bash
# Use gh CLI with cline
gh pr comment <number> --body "@cline implement the suggested changes"
```

---

## Automation Features

### Auto-Generated PR Descriptions

**Before (manual):**
```
PR #109: docs stuff
```

**After (AI-powered):**
```
PR #109: docs: Add comprehensive MCP server reference documentation

## Summary
Adds complete reference docs for all 14 MCP servers used in TTA.dev

## Changes
- Created docs/mcp-references/ with API refs for each server
- Added integration guides 
- Documented Context7, E2B, GitHub, Grafana, and more

## Impact
Better MCP understanding, faster integration, complete coverage
```

### Auto-Branch Naming

```bash
# You type: "fix the login bug in authentication"
# Creates: fix/login-bug-authentication-20251116

# You type: "add prometheus metrics"  
# Creates: feature/prometheus-metrics-20251116
```

### Auto-Sync

```bash
# Every new branch:
✅ Checks out main
✅ Pulls latest changes
✅ Creates new branch from HEAD
✅ No merge conflicts
```

---

## Troubleshooting

### "gh: command not found"

```bash
# Install GitHub CLI
brew install gh
# or
sudo apt install gh

# Authenticate
gh auth login
```

### "Permission denied"

```bash
chmod +x scripts/lazy_dev.py
```

### "Cannot create PR from main"

```bash
# Create a feature branch first
./scripts/lazy_dev.py work-on "your feature"
```

### Agent not responding

```bash
# Check agent is available
gh copilot --version

# Verify CODEOWNERS file
cat .github/CODEOWNERS
# Should include: * @Copilot
```

---

## Integration with Existing Tools

### Works With

✅ **PR Manager** (`scripts/pr_manager.py`)
- lazy_dev creates PRs
- pr_manager monitors and analyzes them

✅ **GitHub Actions**  
- Auto-assign-copilot.yml
- PR validation workflows
- Gemini dispatch

✅ **Copilot Toolsets**
- Use `@workspace #tta-pr-review`
- Complements lazy_dev workflows

✅ **Logseq TODO System**
- Track work in Logseq
- Create branches for TODOs
- Link PRs to knowledge base

---

## Pro Tips

### 1. Alias for Speed

```bash
# Add to ~/.bashrc or ~/.zshrc
alias work='./scripts/lazy_dev.py work-on'
alias pr='./scripts/lazy_dev.py pr'
alias status='./scripts/lazy_dev.py status'

# Usage
work "add caching"
pr
```

### 2. Git Hooks Integration

```bash
# Auto-run lazy_dev status before push
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
python3 scripts/lazy_dev.py status
EOF

chmod +x .git/hooks/pre-push
```

### 3. VS Code Integration

```json
// .vscode/tasks.json
{
  "tasks": [
    {
      "label": "Create PR",
      "type": "shell",
      "command": "./scripts/lazy_dev.py pr",
      "problemMatcher": []
    },
    {
      "label": "Start Work",
      "type": "shell",
      "command": "./scripts/lazy_dev.py",
      "problemMatcher": []
    }
  ]
}
```

### 4. Automated Workflows

```bash
# Create alias for full workflow
alias ship='git add . && git commit -m "$(git branch --show-current | sed "s/.*\///g" | tr "-" " ")" && ./scripts/lazy_dev.py pr'

# Usage: make changes, then just type "ship"
```

---

## Future Enhancements

- [ ] AI-powered commit message generation
- [ ] Automatic milestone assignment
- [ ] Smart PR reviewer selection  
- [ ] Integration with project boards
- [ ] Slack/Discord notifications
- [ ] Automatic changelog updates

---

## Related Documentation

- **PR Manager**: `scripts/pr_manager.py` - Advanced PR analytics
- **Copilot Setup**: `.github/COPILOT_REVIEWER_SETUP.md` - Review automation
- **Workflows**: `.github/workflows/` - GitHub Actions
- **MCP Integration**: `MCP_SERVERS.md` - Model Context Protocol

---

**Made with ❤️ for lazy developers who love automation**
