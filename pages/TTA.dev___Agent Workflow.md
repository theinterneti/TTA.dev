type:: guide
status:: active
audience:: agents
created:: 2025-12-04

# TTA.dev Agent Workflow Guide

**How AI agents should work within the TTA.dev multi-agent development environment.**

---

## Quick Start

1. **Check your worktree**: You operate in one of 4 isolated worktrees
2. **Read KB first**: Check `pages/` for context before making changes
3. **Journal your work**: Write daily notes to `logseq/journals/`
4. **Link everything**: Connect code ↔ KB ↔ journals
5. **Commit with context**: Use `[agent:name]` prefix in commits

---

## Worktree Architecture

Each agent operates in an isolated git worktree:

| Worktree | Branch | Location |
|----------|--------|----------|
| **main** | `main` | `/home/thein/repos/TTA.dev` |
| **augment** | `agent/augment` | `/home/thein/repos/TTA.dev-augment` |
| **cline** | `agent/cline` | `/home/thein/repos/TTA.dev-cline` |
| **copilot** | `agent/copilot` | `/home/thein/repos/TTA.dev-copilot` |

**Key principle:** Work on your branch, then merge to `main` when ready.

---

## Directory Guide

```
TTA.dev/
├── platform/           # 🔧 Core packages (primitives, integrations, etc.)
├── pages/              # 📚 Canonical KB (shared, git-tracked)
├── journals/           # 📝 Shared thinking (synced from all agents)
├── logseq/journals/    # 📓 YOUR daily notes (gitignored, per-worktree)
├── docs/               # 📖 Detailed documentation
├── scripts/            # 🛠️ Utility scripts
└── .github/            # 🔄 CI/CD workflows
```

---

## Development Workflow

### 1. Before Starting Work

```bash
# Check for coordination notices
cat .COORDINATION_NOTICE

# Update from main
git fetch TTA.dev
git merge TTA.dev/main  # or rebase

# Check relevant KB pages
cat pages/TTA.dev___Primitives.md  # if working on primitives
```

### 2. During Development

- **Journal your progress**: Write to `logseq/journals/YYYY-MM-DD.md`
- **Link code to KB**: Add `# See: [[TTA.dev/Primitives/X]]` comments
- **Run pre-commit hooks**: They catch security issues automatically

### 3. Committing Changes

```bash
# Pre-commit hooks run automatically:
# - Semgrep security scan
# - Bandit security scan
# - Ruff lint/format
# - Secret detection

git add -A
git commit -m "[agent:augment] feat(primitives): add retry backoff

# See: [[TTA.dev/Primitives/RetryPrimitive]]"
```

### 4. After Completing Work

```bash
# Push to your branch
git push TTA.dev agent/augment

# Sync journals to shared location
python scripts/sync_journals.py

# Update KB if you added new primitives
python scripts/generate_kb_pages.py
```

---

## KB Conventions

### Page Naming

- Use `TTA.dev___Category___Name.md` format
- Slashes become triple underscores: `TTA.dev/Primitives/X` → `TTA.dev___Primitives___X.md`

### Required Sections

Every KB page should have:
1. **Frontmatter** (type, status, created)
2. **Overview** - What is this?
3. **Usage/Examples** - How to use it?
4. **Source** - Link to code
5. **Related** - Links to other pages

### Code-KB Linking

```python
# In code: Link to KB
# See: [[TTA.dev/Primitives/MyPrimitive]]

# In KB: Link to code
**Source:** `platform/primitives/src/.../my_primitive.py`
```

---

## Pre-Commit Hooks

These run automatically on every commit:

| Hook | Purpose |
|------|---------|
| 🔒 Semgrep | Security vulnerabilities |
| 🛡️ Bandit | Python security issues |
| ⚡ Ruff | Linting and formatting |
| 🔐 detect-secrets | Prevent secret leaks |

**Emergency bypass:** `git commit --no-verify` (use sparingly!)

---

## Related

- [[TTA.dev/KB Structure]] - Knowledge base organization
- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Architecture]] - System architecture
- [[TTA.dev/Journal Sync]] - How journals are synchronized

---

**Tags:** #guide #agent #workflow #development
