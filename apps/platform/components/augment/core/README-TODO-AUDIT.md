# TTA TODO & GitHub Issue Audit System

**Status**: ✅ Active
**Last Updated**: 2025-11-01
**Maintainer**: TTA Development Team

---

## 🎯 Overview

This system provides intelligent organization and tracking of TODOs and GitHub issues across the TTA project using Logseq features for powerful querying, linking, and prioritization.

## 📁 Structure

```
.augment/
├── TODO-AUDIT.md              # Main audit document (Logseq compatible)
├── logseq/
│   ├── config.edn            # Logseq configuration
│   └── pages/                # Auto-generated issue pages
└── README-TODO-AUDIT.md      # This file

scripts/
└── todo-audit.py             # Automation script
```

## 🚀 Quick Start

### View the Audit

Open `.augment/TODO-AUDIT.md` in:
- **Logseq**: Full query support, linked references, hierarchical views
- **Obsidian**: Partial support (markdown with wiki-links)
- **VS Code**: Basic markdown viewing
- **Any text editor**: Fallback to plain text

### Run Audit Commands

```bash
# Generate comprehensive report
python scripts/todo-audit.py report

# Scan codebase for TODOs
python scripts/todo-audit.py scan

# Sync GitHub issues
python scripts/todo-audit.py sync

# Find orphaned TODOs (referencing closed issues)
python scripts/todo-audit.py orphans

# Export to Logseq pages
python scripts/todo-audit.py export
```

## 📊 Features

### 1. Intelligent Organization

- **Priority Matrix**: 3x3 grid (Urgent/Normal × High/Medium/Low)
- **Component Grouping**: By source component/module
- **Label Categorization**: GitHub issue labels
- **Status Tracking**: TODO → DOING → DONE workflow

### 2. Logseq Integration

**Query Blocks**: Dynamic views that auto-update
```logseq
#+BEGIN_QUERY
{:title "MVP Blockers"
 :query [:find (pull ?b [*])
         :where
         [?b :block/marker "TODO"]
         [?b :block/content ?content]
         [(clojure.string/includes? ?content "#mvp-blocker")]]}
#+END_QUERY
```

**Linked References**: `[[Issue #55]]` auto-links everywhere
**Tags**: `#mvp-blocker` `#security` `#high-priority`
**Properties**: Structured metadata on each item

### 3. GitHub Integration

- Auto-fetch issues via `gh` CLI
- Track issue status (OPEN/CLOSED)
- Link code TODOs to issues
- Identify orphaned TODOs (closed issue references)

### 4. Code Scanning

- Searches for TODO/FIXME/XXX/HACK patterns
- Extracts GitHub issue references (`#123`)
- Categorizes by component
- Prioritizes by keywords

## 📖 Usage Patterns

### For Developers

#### Adding a TODO
```python
# TODO(#55): Implement component_registry module
# Links to GitHub issue #55 automatically

# TODO: [HIGH] Add authentication tests
# Keyword-based priority detection

# TODO(@username): Review error handling
# Assignment tracking
```

#### Checking TODOs Before Commit
```bash
# Scan your changes
python scripts/todo-audit.py scan

# Check for orphaned references
python scripts/todo-audit.py orphans
```

### For Project Managers

#### Weekly Sprint Planning
1. Open `.augment/TODO-AUDIT.md` in Logseq
2. Use query blocks to view:
   - MVP blockers
   - High priority items
   - Blocked items
3. Update GitHub issues based on audit
4. Re-run audit to sync

#### Tracking Progress
```bash
# Generate weekly report
python scripts/todo-audit.py report > reports/todo-$(date +%Y-%m-%d).txt

# Export to Logseq for visualization
python scripts/todo-audit.py export
```

### For QA Engineers

#### Pre-Release Checklist
1. Run `python scripts/todo-audit.py orphans`
2. Ensure no TODOs block critical paths
3. Verify GitHub issues match code state
4. Check security-tagged items

## 🎓 Logseq Tips

### Essential Shortcuts

- `Ctrl/Cmd + K`: Command palette
- `Ctrl/Cmd + Shift + K`: Open linked references
- `/query`: Insert query block
- `[[` : Create page link
- `#`: Add tag

### Custom Queries for TTA

**View by Effort (Sprint Planning)**:
```clojure
#+BEGIN_QUERY
{:title "Quick Wins (1-2 days)"
 :query [:find (pull ?b [*])
         :where
         [?b :block/marker "TODO"]
         [?b :block/content ?content]
         [(clojure.string/includes? ?content "Effort: 1")]]}
#+END_QUERY
```

**Security Items**:
```clojure
#+BEGIN_QUERY
{:title "Security TODOs"
 :query [:find (pull ?b [*])
         :where
         [?b :block/content ?content]
         (or
           [(clojure.string/includes? ?content "#security")]
           [(clojure.string/includes? ?content "HIPAA")])]}
#+END_QUERY
```

**Component-Specific View**:
```clojure
#+BEGIN_QUERY
{:title "Authentication TODOs"
 :query [:find (pull ?b [*])
         :where
         [?b :block/content ?content]
         [(clojure.string/includes? ?content "src/player_experience")]
         [?b :block/marker "TODO"]]}
#+END_QUERY
```

## 🔧 Configuration

### Logseq Setup

1. **Install Logseq**: https://logseq.com/
2. **Add Graph**: File → Add new graph → Select `.augment/` directory
3. **Enable Features**: Settings → Enable block timestamps, journals
4. **Import Config**: Copy `.augment/logseq/config.edn`

### Script Configuration

Edit `scripts/todo-audit.py`:
```python
# Customize TODO patterns
self.todo_patterns = [
    r"#\s*TODO:?\s*(.+)",
    r"@todo\s+(.+)",
    # Add custom patterns
]

# Customize excluded paths
self.exclude_patterns = [
    "*.pyc",
    "node_modules",
    # Add custom exclusions
]
```

## 📈 Metrics Tracked

### Key Metrics
- Total open GitHub issues
- Code TODOs count
- Orphaned TODO count
- TODOs by priority (High/Medium/Low)
- TODOs by category
- Issues by label
- Component promotion status

### Reports Generated
- **Audit Report**: Comprehensive overview (`.augment/TODO-AUDIT.md`)
- **Summary Stats**: Quick metrics
- **Orphaned TODOs**: Stale issue references
- **Logseq Pages**: Individual issue pages

## 🔄 Automation

### Git Hooks

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Check for orphaned TODOs before commit
python scripts/todo-audit.py orphans
if [ $? -ne 0 ]; then
    echo "❌ Found orphaned TODOs. Please update or remove."
    exit 1
fi
```

### CI/CD Integration

Add to `.github/workflows/`:
```yaml
- name: TODO Audit
  run: |
    python scripts/todo-audit.py report
    python scripts/todo-audit.py orphans
```

### Weekly Cron Job
```bash
# Update audit every Monday at 9 AM
0 9 * * 1 cd /path/to/TTA && python scripts/todo-audit.py export
```

## 🎯 Best Practices

### Writing Good TODOs

**DO**:
```python
# TODO(#55): Implement component_registry - Blocked by architecture decision
# Clear, linked to issue, explains blocker

# TODO: [SECURITY] Validate user input for SQL injection
# Tagged with priority/category

# TODO: Add Redis connection pooling (Effort: 2 days)
# Includes effort estimate
```

**DON'T**:
```python
# TODO: fix this
# Vague, no context

# TODO: implement everything
# Too broad, not actionable

# todo refactor
# Not following format, hard to parse
```

### Maintaining the Audit

**Weekly**:
1. Run `python scripts/todo-audit.py report`
2. Update GitHub issue statuses
3. Close completed TODOs
4. Review orphaned TODOs

**Sprint Planning**:
1. Export to Logseq: `python scripts/todo-audit.py export`
2. Use Logseq queries for sprint selection
3. Update priorities based on roadmap
4. Re-generate audit

**Pre-Release**:
1. Verify zero critical TODOs in release path
2. Check all security TODOs resolved
3. Update documentation TODOs
4. Generate final audit for release notes

## 🐛 Troubleshooting

### GitHub CLI Not Found
```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Authenticate
gh auth login
```

### Logseq Queries Not Working
- Ensure Logseq version ≥0.10.0
- Check `.augment/logseq/config.edn` is valid EDN
- Verify query syntax in Logseq docs

### Script Errors
```bash
# Check Python version (need 3.10+)
python --version

# Install dependencies if needed
pip install -r requirements.txt
```

## 📚 Resources

- **Logseq Documentation**: https://docs.logseq.com/
- **GitHub CLI**: https://cli.github.com/manual/
- **TTA Development Guide**: `AGENTS.md`
- **Component Maturity Workflow**: `.augment/instructions/component-maturity.instructions.md`

## 🤝 Contributing

### Adding New Features

1. Update `scripts/todo-audit.py` with new functionality
2. Add Logseq queries to `TODO-AUDIT.md`
3. Update this README
4. Submit PR with examples

### Suggesting Improvements

- Open GitHub issue with label `audit-system`
- Describe use case and proposed solution
- Include example queries/outputs

---

**Questions?** Check `.augment/memory/workflow-learnings.memory.md` or open an issue.

**Next Steps**: See "📖 Usage Patterns" section above for your role (Developer/PM/QA).


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Readme-todo-audit]]
