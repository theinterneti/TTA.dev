# Workspace Maintenance Quick Reference

**Keep TTA.dev elegant, graceful, and exemplary**

## 🎯 Root Level Policy

**Only 9 essential markdown files allowed:**
1. README.md
2. AGENTS.md
3. GETTING_STARTED.md
4. CONTRIBUTING.md
5. MCP_SERVERS.md
6. PRIMITIVES_CATALOG.md
7. ROADMAP.md
8. CHANGELOG.md
9. (Plus essential configs: pyproject.toml, package.json, etc.)

**If you add a new file at root, categorize it immediately!**

## 📂 Where Does It Go?

```bash
# Status reports & completion summaries
docs/status-reports/

# User guides & tutorials
docs/guides/

# Quick reference cards
docs/guides/quick-actions/

# Architecture & design docs
docs/architecture/

# Git & worktree documentation
docs/development/git/

# Problem-solving guides
docs/troubleshooting/

# Workspace configuration files
.vscode/workspaces/

# Historical & one-time docs
_archive/historical/

# Package-specific docs
platform/{package}/docs/
```

## 🧹 Regular Cleanup

### Weekly Check
```bash
# Count root markdown files (should be ≤9)
ls -1 *.md | wc -l

# Find stray log files
find . -maxdepth 1 -name "*.log"

# Check for temporary test folders
ls -d verification_test_* 2>/dev/null
```

### Monthly Cleanup
```bash
# Run automated cleanup
./scripts/cleanup_workspace.sh

# Remove generated files
rm -rf __pycache__/ .pytest_cache/ .ruff_cache/ htmlcov/

# Clean demo outputs
rm -rf auto_learning_demo/ production_adaptive_demo/
```

## 🚫 Never Commit

- ✗ `*.log` files
- ✗ `*_output.log` files
- ✗ `verification_test_*/` folders
- ✗ `__pycache__/` directories
- ✗ `.pytest_cache/` directories
- ✗ `htmlcov/` directories
- ✗ `tta_traces.db` database
- ✗ Demo output folders
- ✗ Cache directories

**These are in `.gitignore` - keep them there!**

## ✅ Always Categorize

When creating new documentation:

1. **Determine type**: Guide? Status? Architecture? Troubleshooting?
2. **Check existing structure**: Is there a category for this?
3. **Place correctly**: Move to appropriate `docs/` subdirectory
4. **Update indexes**: Add to `docs/README.md` if needed
5. **Link from AGENTS.md**: If relevant for AI agents

## 🔄 Workspace File Management

**All `.code-workspace` files go in:**
```
.vscode/workspaces/
```

**Don't keep at root!**

## 📝 File Naming Conventions

```bash
# Status reports
{TOPIC}_{STATUS}.md
# Examples: MIGRATION_COMPLETE.md, SETUP_VALIDATION.md

# Guides
{TOPIC}_GUIDE.md or {TOPIC}_QUICKREF.md
# Examples: PRODUCTION_DEPLOYMENT_GUIDE.md, GIT_QUICKREF.md

# Architecture
{COMPONENT}_{TYPE}.md
# Examples: PACKAGE_INVESTIGATION_ANALYSIS.md, OBSERVABILITY_UI_DESIGN.md
```

## 🎨 Keep It Clean

**Signs your workspace needs cleanup:**
- More than 9 markdown files at root
- Log files in root directory
- Temporary test folders hanging around
- Multiple `.code-workspace` files at root
- "Old" or "backup" files accumulating

**Action:** Run `./scripts/cleanup_workspace.sh`

## 📖 Reference Docs

Full details in:
- **Organization Guide**: `docs/WORKSPACE_ORGANIZATION.md`
- **Cleanup Plan**: `WORKSPACE_CLEANUP_PLAN.md`
- **Completion Report**: `docs/status-reports/WORKSPACE_CLEANUP_COMPLETE.md`

## 🤖 For AI Agents

When working on TTA.dev:

1. **Check AGENTS.md first** - Primary navigation hub
2. **Keep root clean** - Don't create files at root
3. **Categorize immediately** - Place new docs in correct location
4. **Update documentation** - Keep organization guides current
5. **Use cleanup script** - Run when making major changes

## 💡 Quick Decisions

| "I have a..." | "Put it in..." |
|--------------|----------------|
| New status report | `docs/status-reports/` |
| User guide | `docs/guides/` |
| Quick reference | `docs/guides/quick-actions/` |
| Architecture doc | `docs/architecture/` |
| Git workflow doc | `docs/development/git/` |
| Debugging guide | `docs/troubleshooting/` |
| Workspace config | `.vscode/workspaces/` |
| Old migration doc | `_archive/historical/` |
| Test output | Delete or add to `.gitignore` |

---

**Last Updated:** 2025-11-17
**Cleanup Script:** `./scripts/cleanup_workspace.sh`
**Full Guide:** `docs/WORKSPACE_ORGANIZATION.md`


---
**Logseq:** [[TTA.dev/Docs/Guides/Quick-actions/Workspace_maintenance]]
