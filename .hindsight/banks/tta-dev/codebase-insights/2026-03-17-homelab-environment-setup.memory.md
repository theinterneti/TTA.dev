---
category: codebase-insights
date: 2026-03-17
component: environment
severity: medium
tags: [homelab, setup, falkordb, cgc, python, uv, git]
related_memories: []
---
# Homelab Environment Setup (TTA.dev)

Fresh clone on homelab machine as of 2026-03-17. All runtimes present, no Docker.

## Context

**When:** 2026-03-17
**Where:** Homelab machine (`/home/adam/Repos/TTA.dev`)
**Who:** adam (theinterneti <theinternetisbig@gmail.com>)
**What:** Fresh clone, full environment bootstrap

## Environment State

### Runtimes
- Python 3.12.3
- uv 0.10.11
- Node.js 18.19.1

### Setup Completed
- `.venv` created via `uv sync --all-extras`
- `cgc` installed globally via `uv tool install codegraphcontext` (v0.3.1)
- FalkorDB Lite configured at `~/.codegraphcontext/` — zero-config, no daemon
- CGC index complete: 414 files, 3495 functions, 679 classes
- `.cgcignore` added to exclude noise directories

### Notable Constraints
- **No Docker** on this machine
- Use FalkorDB Lite (in-process) — NOT containerized FalkorDB
- `.env` not yet created — needs to be made from `.env.example` with API keys

### Git Identity
`theinterneti <theinternetisbig@gmail.com>`

## Lesson Learned

Always use FalkorDB Lite for this environment. `cgc watch` can be enabled for live graph updates.

### Do

- Use FalkorDB Lite (in-process, no daemon) for all graph operations
- Use `uv` for all package management (never pip/poetry)

### Don't

- Don't suggest Docker-based FalkorDB — no Docker installed
- Don't assume `.env` exists — user must create it from `.env.example`

## Applicability

**When to Apply:**
- Any suggestion involving FalkorDB, graph indexing, or environment setup on this machine

---

**Created:** 2026-03-17
**Last Updated:** 2026-03-19
**Verified:** [x] Yes
