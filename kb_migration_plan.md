# KB Migration Plan: Logseq → TTA-notes + MCP + Atomic Notes

**Status:** AWAITING APPROVAL — no files have been modified
**Author:** Claude Code (main agent)
**Date:** 2026-03-04

---

## Overview

Replacing the in-repo Logseq KB + bidirectional sync with:
1. A centralized `TTA-notes` repo (clearinghouse for TTA + TTA.dev)
2. A read-only MCP server (`tta-notes-kb`) for querying context
3. An "Atomic Notes" agent skill for structured documentation export

---

## Phase 1: Eradicate Destructive Automation

### 1A. Scripts to Delete

| File | Why |
|------|-----|
| `scripts/sync_journals.py` | Multi-worktree journal sync — replaces by MCP workflow |
| `scripts/pre-commit-logseq.sh` | Pre-commit hook that runs `logseq_graph_sync.py` |
| `scripts/kb-pre-commit-hook.sh` | Lightweight pre-commit KB validation against TTA-notes |
| `scripts/kb-validation-hook.sh` | Unused variant of the above |
| `scripts/setup-logseq-mcp.sh` | Sets up local Logseq MCP server (replaced by `tta-notes-kb`) |
| `scripts/validate-logseq-mcp.py` | Validates local Logseq MCP connectivity |
| `scripts/validate_kb_links.py` | Validates KB links within Logseq graph |
| `scripts/generate_kb_pages.py` | Generates Logseq pages from code metadata |

### 1B. Platform Packages to Remove

| Package / Path | Why |
|----------------|-----|
| `platform/documentation/` | Entire package — `tta-documentation-primitives` — wraps Logseq sync with Gemini AI; replaced by Atomic Notes export |
| `platform/kb-automation/` | Entire package — `tta-kb-automation` — one-way code→KB sync tools; replaced by MCP query |

> **Note:** `platform/kb-automation/tools/logseq_graph_sync.py` is the primary write-path to the KB. Removing this package eliminates all automated KB mutation from this repo.

### 1C. Logseq Markdown Files to Delete

The entire `logseq/` directory:

```
logseq/
├── config.edn                                              # Logseq app config
├── journals/
│   └── 2024_12_20.md
└── pages/ (27 files)
    ├── TTA.dev.md
    ├── TTA.dev___Architecture.md
    ├── TTA.dev___Learning Paths.md
    ├── TTA.dev___Packages.md
    ├── TTA.dev___Primitives.md
    ├── TTA.dev___TODO Architecture.md
    ├── TTA.dev___TODO Metrics Dashboard.md
    ├── TTA.dev___TODOs.md
    ├── TTA.dev___Packages___tta-dev-primitives___TODOs.md
    ├── TTA.dev___Packages___tta-observability-integration___TODOs.md
    ├── TTA.dev___Packages___universal-agent-context___TODOs.md
    ├── TODO Management System.md
    ├── TODO Templates.md
    ├── TODO Architecture Quick Reference.md
    ├── RetryPrimitive.md
    ├── TimeoutPrimitive.md
    ├── (other primitive reference pages)
    ├── tta-dev-primitives.md
    ├── (other package reference pages)
    ├── dev-todo.md
    ├── learning-todo.md
    └── ops-todo.md
```

> **Recommendation:** Before deletion, copy `logseq/` into the `TTA-notes` repo so no content is lost. This is a manual step outside this repo's scope.

### 1D. CI Workflow Unwiring

**Three files affected:**

| File | Action | Detail |
|------|--------|--------|
| `.github/workflows/kb-validation.yml` | **DELETE entire file** | Entire workflow validates Logseq KB links using `tta-kb-automation`; has a scheduled cron at `0 3 * * *` — nothing to salvage |
| `.github/workflows/publish.yml` | **Edit** — remove 2 lines | Lines 55–56: `["documentation"]="tta-documentation-primitives"` and `["kb-automation"]="tta-kb-automation"` in the package map array |
| `.github/workflows/release.yml` | **Edit** — remove 2 lines | Lines 50–51: same two entries in the release package map |

### 1E. pyproject.toml / uv.lock Cleanup

After removing `platform/documentation/` and `platform/kb-automation/`, remove them from:
- Root `pyproject.toml` workspace members list (lines 15–16: `"platform/documentation"` and `"platform/kb-automation"`)
- `uv.lock` (regenerated automatically via `uv sync`)

---

## Phase 2: Atomic Notes Export Pipeline

### 2A. Create Export Directory

```
docs/kb-exports/
└── .gitkeep          # keeps the directory tracked; actual exports are ephemeral
```

Optionally add a `docs/kb-exports/README.md` explaining the directory purpose.

### 2B. Create Agent Skill: `create-atomic-note`

**File:** `.claude/skills/create-atomic-note/SKILL.md`

```markdown
# Skill: create-atomic-note

## Purpose
Save a single-topic documentation note to `docs/kb-exports/` for ingestion into the TTA-notes KB.

## When to Use
After completing any significant task: new feature, bug fix, architectural decision, or research finding.

## Rules
- ONE topic per file. If you have two topics, create two files.
- Filename: `YYYY-MM-DD_<slug>.md` (e.g., `2026-03-04_persistence-primitives-design.md`)
- All notes MUST include YAML frontmatter (see template below).
- Never write more than ~300 lines. If it's longer, split it.

## Template

```yaml
---
type: <note-type>          # architecture | decision | bug-fix | feature | research | todo
priority: <1-3>            # 1=high (action needed) | 2=medium | 3=low/reference
status: draft              # draft | review | stable
tags: [tta-dev]            # always include repo tag; add: dev-todo | learning-todo | ops-todo | template-todo
source_agent: claude-code  # which agent created this
date: YYYY-MM-DD
related_files: []          # list of repo paths this note documents
---
```

## Content Structure

After frontmatter, use this structure:

```markdown
# <Short Title>

## Summary
One paragraph: what this is and why it matters.

## Context
What led to this? What problem was being solved?

## Decision / Finding
The actual content.

## Consequences / Next Steps
What does this enable? What should happen next?
```

## Example Filename Patterns

- `2026-03-04_retry-primitive-timeout-interaction.md` — architectural finding
- `2026-03-04_uow-abstract-base-class-design.md` — design decision
- `2026-03-04_kb-migration-completed.md` — ops event
```

---

## Phase 3: Configure MCP Search Integration

### 3A. Add `tta-notes-kb` to `.mcp.json`

**Current `.mcp.json`** has only the `hypertool` server with Logseq env vars.

**Changes:**
1. Add `tta-notes-kb` server entry
2. Remove `LOGSEQ_API_TOKEN` and `LOGSEQ_API_URL` env vars from `hypertool` (or leave as no-ops if hypertool is kept for other tools)

```json
{
  "mcpServers": {
    "hypertool": {
      "command": "npx",
      "args": [
        "-y",
        "@toolprint/hypertool-mcp@0.0.45",
        "mcp",
        "run",
        "--mcp-config",
        ".hypertool/mcp_servers.json",
        "--quiet"
      ],
      "env": {
        "HYPERTOOL_CONFIG_DIR": "/home/thein/repos/TTA.dev/.hypertool",
        "HYPERTOOL_SERVERS_FILE": "/home/thein/repos/TTA.dev/.hypertool/mcp_servers.json",
        "HYPERTOOL_ENABLE_CONFIG_TOOLS_MENU": "false",
        "GITHUB_TOKEN": "${GITHUB_TOKEN}",
        "HOME": "${HOME}"
      }
    },
    "tta-notes-kb": {
      "command": "python",
      "args": ["/PLACEHOLDER/path/to/TTA-notes/mcp_server.py"],
      "env": {},
      "description": "TTA-notes Knowledge Base — exposes search_kb and get_high_priority_todos"
    }
  }
}
```

### 3B. Add `tta-notes-kb` to `.vscode/settings.json`

Add alongside the existing `hypertool` and `tta-dev` entries. Also remove `LOGSEQ_API_TOKEN` from `hypertool` env:

```json
"tta-notes-kb": {
    "command": "python",
    "args": ["/PLACEHOLDER/path/to/TTA-notes/mcp_server.py"],
    "env": {},
    "description": "TTA-notes KB — search_kb, get_high_priority_todos",
    "disabled": false
}
```

> **PLACEHOLDER:** Replace `/PLACEHOLDER/path/to/TTA-notes/mcp_server.py` with the actual absolute path once `TTA-notes` MCP server exists.

---

## Phase 4: Update Tier 1 Root Instructions

### 4A. `AGENTS.md` Changes

**Remove:**
- Entire "TODO Management & Knowledge Base" section (lines 25–44) — all Logseq page links
- `LogseqStrategyIntegration` from the primitives table
- References to `#tta-docs` toolset mentioning Logseq in AGENTS.md
- Footer line: `**Logseq:** [[TTA.dev/Agents]]`

**Add** (after the MCP Tool Registry reference):

```markdown
### 🔍 Pre-Task: Search for Context First

**MANDATORY:** Before executing any significant task, query the TTA-notes KB:

```
Tool: tta-notes-kb → search_kb
Query: <topic you're about to work on>
```

Also check for outstanding work:
```
Tool: tta-notes-kb → get_high_priority_todos
```

### 📝 Post-Task: Document Your Work

**MANDATORY:** After completing any significant task, use the `create-atomic-note` skill:

1. Read `.claude/skills/create-atomic-note/SKILL.md`
2. Create a single-topic note in `docs/kb-exports/YYYY-MM-DD_<slug>.md`
3. Include required YAML frontmatter (type, priority, status, tags, source_agent, date)

The `TTA-notes` repo ingests these exports periodically.

### 📋 TODO Management

Record TODOs as atomic notes with `type: todo` and `tags: [dev-todo]` (or `learning-todo`, `ops-todo`, `template-todo`).
Save to `docs/kb-exports/`. These replace the old Logseq journal entries.
```

### 4B. `CLAUDE.md` Changes

**In the "TODO Management" section**, replace:
> All TODOs go in Logseq (`logseq/journals/YYYY_MM_DD.md`).

With:
> All TODOs go in `docs/kb-exports/` as atomic notes (type: todo). Use the `create-atomic-note` skill.

**Add to the "Key Reference Files" section:**
> - `.claude/skills/create-atomic-note/SKILL.md` — post-task documentation workflow

---

## Files Modified Summary

| Action | Target |
|--------|--------|
| DELETE | `scripts/sync_journals.py` |
| DELETE | `scripts/pre-commit-logseq.sh` |
| DELETE | `scripts/kb-pre-commit-hook.sh` |
| DELETE | `scripts/kb-validation-hook.sh` |
| DELETE | `scripts/setup-logseq-mcp.sh` |
| DELETE | `scripts/validate-logseq-mcp.py` |
| DELETE | `scripts/validate_kb_links.py` |
| DELETE | `scripts/generate_kb_pages.py` |
| DELETE | `platform/documentation/` (entire package) |
| DELETE | `platform/kb-automation/` (entire package) |
| DELETE | `logseq/` (entire directory, 28 files) |
| CREATE | `docs/kb-exports/.gitkeep` |
| CREATE | `.claude/skills/create-atomic-note/SKILL.md` |
| MODIFY | `.mcp.json` — add `tta-notes-kb`, remove Logseq env vars |
| MODIFY | `.vscode/settings.json` — add `tta-notes-kb` MCP entry, remove Logseq env vars |
| MODIFY | `AGENTS.md` — replace Logseq TODO section with MCP + Atomic Notes instructions |
| MODIFY | `CLAUDE.md` — update TODO Management section |
| MODIFY | Root `pyproject.toml` — remove deleted packages from workspace |
| DELETE | `.github/workflows/kb-validation.yml` — entire workflow (validates Logseq KB) |
| MODIFY | `.github/workflows/publish.yml` — remove `documentation` and `kb-automation` package map entries |
| MODIFY | `.github/workflows/release.yml` — remove same two package map entries |
| RUN | `uv sync` — regenerate lock file |

---

## Pre-Migration Checklist (manual, before I execute)

- [ ] Copy `logseq/` directory to `TTA-notes` repo (preserves all content)
- [ ] Confirm `TTA-notes/mcp_server.py` path so I can fill in the placeholder
- [ ] Confirm whether `hypertool` MCP server should be kept (it has non-Logseq tools)
- [ ] Confirm whether `platform/documentation/` and `platform/kb-automation/` have any active usage in CI or other workflows that needs to be unwired first

---

## Pre-Migration Checklist — Status

- [x] `logseq/` content copied to `TTA-notes` — confirmed
- [x] MCP server path: `/home/thein/repos/TTA-notes/mcp_server.py`
- [x] Keep `hypertool` in MCP config (strip Logseq env vars only)
- [x] CI unwiring identified — see Phase 1D above

---

**HALTING HERE. Awaiting your explicit approval before executing any changes.**
