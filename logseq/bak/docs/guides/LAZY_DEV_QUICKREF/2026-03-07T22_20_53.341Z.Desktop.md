# 🚀 Lazy Dev Quick Reference

**Never remember git commands again!**

---

## 📖 Essential Commands

```bash
# Check what's happening
./scripts/lazy_dev.py status

# Start working on something
./scripts/lazy_dev.py work-on "your feature description"

# Create PR with AI magic
./scripts/lazy_dev.py pr

# See milestone progress
./scripts/issue_manager.py progress

# Auto-label an issue
./scripts/issue_manager.py auto-label <issue-number>

# Interactive mode (menu)
./scripts/lazy_dev.py
```

---

## 🔥 Shell Aliases (Recommended)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias work='./scripts/lazy_dev.py work-on'
alias pr='./scripts/lazy_dev.py pr'  
alias status='./scripts/lazy_dev.py status'
alias ship='git add . && git commit -m "update" && ./scripts/lazy_dev.py pr'
```

Then use:
```bash
work "add authentication"  # Create branch
# ... code code code ...
ship                       # Commit + create PR
```

---

## 📝 Common Workflows

### Start New Feature
```bash
work "user profiles"
# → Creates: feature/user-profiles-20251116
# → From: latest main
```

### Create PR
```bash
git add .
git commit -m "Add feature X"
pr
# → AI generates description
# → Creates PR  
# → @copilot reviews automatically
```

### Check Status
```bash
status
# → Shows: branch, changes, PRs, issues
```

### Manage Issues
```bash
./scripts/issue_manager.py create-milestones  # Setup phases
./scripts/issue_manager.py auto-label 123     # Smart labels
./scripts/issue_manager.py assign-milestone 123  # Auto-assign
./scripts/issue_manager.py progress           # See dashboard
```

---

## 🤖 Agent Collaboration

### @copilot (Automatic)
Every PR auto-requests @copilot review

### @cline (Manual)
Comment on PRs:
```
@cline please implement the suggested changes
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "gh: command not found" | Install: `brew install gh` or `sudo apt install gh` |
| "Permission denied" | Run: `chmod +x scripts/lazy_dev.py` |
| "Cannot create PR from main" | First: `work "your feature"` |
| Branch naming issues | Use quotes: `work "feature name"` |

---

## 📚 Full Docs

[LAZY_DEV_GUIDE.md](docs/guides/LAZY_DEV_GUIDE.md)

---

**Made with ❤️ for lazy developers**
