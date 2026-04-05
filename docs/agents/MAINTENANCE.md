# Agent Instruction System — Maintenance Guide

## Architecture

This directory is the single source of truth for all developer-facing agent
instructions in TTA.dev. Root files (CLAUDE.md, AGENTS.md, .github/copilot-instructions.md)
are **routing layers** with a 100-line hard budget. Knowledge lives here, not in root files.

### Directory structure

| Directory | Purpose | Loading |
|---|---|---|
| `dev/` | Developer guidance, loaded on demand via routing table | Agent reads when working on that topic |
| `runtime/` | Reference for developers touching L0 runtime agents | On demand |

`dev/observability.md` and `dev/reliability.md` are also auto-imported by `CLAUDE.md`
via `@`-imports — they serve double duty as always-loaded content for Claude Code.

### Four-tier agent taxonomy

| Tier | Who | Instructions |
|---|---|---|
| 1 — Developer agents | Claude Code, Copilot, OpenCode, Cline, Cursor | Root files + this tree |
| 2 — Domain expert personas | Chatmodes in `.tta/chatmodes/` | Chatmode files (not in this tree) |
| 3 — Runtime product agents | — (TTA.dev has no Tier 3) | — |
| 4 — Runtime dev agents | L0 agents in `ttadev/agents/` | `runtime/` reference docs |

---

## How to extend the system

### Adding developer-facing guidance

1. Create or extend a file in `docs/agents/dev/`
2. Add ONE row to each root file's routing table:
   `| Working on <topic> | docs/agents/dev/<topic>.md |`
3. Run `python scripts/check_agent_docs.py` — root files must stay under 100 lines

### Adding always-loaded guidance (CLAUDE.md @-imports)

1. Create a file in `docs/agents/dev/`
2. Add `@docs/agents/dev/<file>.md` to `CLAUDE.md`
3. Add a routing row in other agents' root files (Copilot/OpenCode cannot @-import)

### Adding runtime agent reference docs

1. Create a file in `docs/agents/runtime/`
2. Add a routing row: `| Editing L0 agents | docs/agents/runtime/<file>.md |`

---

## Maintenance header

Paste this comment into every root file you edit:

```
<!--
  MAINTENANCE PROTOCOL — read before editing this file
  Budget: 100 lines hard limit.
  DO NOT add content directly here.
  Instead:
    1. Create or extend a file in docs/agents/dev/ (or runtime/)
    2. Add ONE routing row to the table below
    3. Run: python scripts/check_agent_docs.py
  This file is a routing layer, not a knowledge store.
-->
```

---

## Cross-repo sync obligations

Any **structural or protocol change** (not typo/formatting) to these files requires
opening a tracking issue in TTA. Typos and formatting fixes do not require issues.

| This file | TTA counterpart |
|---|---|
| `docs/agents/dev/l0-coordination.md` | `docs/agents/dev/l0-boundary.md` |
| `AGENTS.md` (roster section) | `AGENTS.md` (roster section) |
| `docs/agents/dev/observability.md` | `docs/agents/_core/tools.md` (Hindsight section) |

---

## Budget enforcement

`python scripts/check_agent_docs.py` checks these root files against the 100-line budget:
`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`

If a file exceeds 100 lines, move the excess content into `docs/agents/dev/` or `docs/agents/runtime/`
and replace it with a routing row.
