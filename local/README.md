# local/ Directory

**Purpose:** Personal workspace for experimental code, session notes, and temporary files

**NOT for production code** - See organization guide below

## 📁 Directory Structure

```
local/
├── session-reports/    # Session completion reports and progress tracking
├── planning/          # Planning documents and strategy docs
├── analysis/          # Analysis reports and investigations
├── summaries/         # Implementation summaries and reviews
└── README.md          # This file
```

## 🚫 What NOT to Put Here

- Production code (use `packages/` or `src/`)
- Public documentation (use `docs/`)
- Logseq knowledge base (use separate TTA-notes repo)
- Quick reference guides (keep in repository root if referenced by AGENTS.md)

## ✅ What to Put Here

- Session notes and completion reports
- Temporary analysis documents
- Planning docs for features in progress
- Personal experiments and prototypes
- Implementation summaries (before moving to docs/)

## 🔄 Lifecycle

Files in `local/` should be:
1. **Temporary** - Move to appropriate location when finalized
2. **Personal** - Not shared via git (directory is gitignored)
3. **Experimental** - Safe to delete when no longer needed

---

**Note:** This directory is gitignored. Content here is local to your machine only.
