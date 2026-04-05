# TTA.dev — Claude Code

Claude Code is the primary agent. Owner is the sole developer. Other agents defer to Claude Code.

@docs/agents/dev/architecture.md
@docs/agents/dev/reliability.md

## SDD Mandate

No code before a signed-off spec. Use `sdd-workflow` skill: `/specify` → `/plan` → `/tasks` → `/implement`.

## Session Start

1. `mcp__hindsight__recall` — query `adam-global`, then the current `project-*`/`workspace-*` bank
2. `mcp__codegraphcontext__get_repository_stats` — confirm code graph is current
3. Acknowledge loaded context before any task work begins
4. Retain to `adam-global` (cross-project patterns) or repo bank after significant tasks

## Standards

- **Package manager:** `uv` — never `pip` or `poetry`
- **Python:** 3.12+, `str | None` not `Optional[str]`, `dict[str, Any]` not `Dict`
- **Linting:** `uv run ruff check . --fix` (line length 100)
- **Types:** `uvx pyright ttadev/`
- **Tests:** `make watch` (TDD loop), `make test` (CI); 100% coverage on new code
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Primitives:** Always use for retry/timeout/workflow — never write manual loops
- **State:** Pass via `WorkflowContext` — no globals
- **TTA cross-repo:** Never edit `~/Repos/TTA` directly. Clone to `/tmp/TTA-copilot`, push, delete.

## Skills (on-demand HOW-TO)

| Skill | When to invoke |
|-------|---------------|
| `session-start` | Start of every session |
| `build-test-verify` | Before any commit or PR |
| `core-conventions` | Writing or reviewing Python code |
| `git-commit` | Making commits |
| `create-pull-request` | Opening PRs |
| `self-review-checklist` | Pre-merge validation |
| `sdd-workflow` | Any new feature or implementation |

Before creating a new skill, search `github/awesome-copilot` skills first.

## Reference Docs (load when working in that area)

| Topic | Read |
|-------|------|
| Primitives / architecture | `docs/agents/dev/architecture.md` |
| Retry / timeout / circuit breaker | `docs/agents/dev/reliability.md` |
| OTel / Langfuse tracing | `docs/agents/dev/observability.md` |
| Tests / coverage / MockPrimitive | `docs/agents/dev/testing.md` |
| L0 task coordination | `docs/agents/dev/l0-coordination.md` |
| Agent roles / roster | `docs/agents/runtime/l0-roster.md` |

## Tool Selection

| Goal | Use | Not |
|------|-----|-----|
| Find symbol definition | `mcp__plugin_serena__find_symbol` | grep |
| Find all callers | `mcp__plugin_serena__find_referencing_symbols` | grep |
| Scan file symbols | `mcp__plugin_serena__get_symbols_overview` | read full file |
| Cross-file dependencies | `mcp__codegraphcontext__analyze_code_relationships` | read files |
| Search repo-wide | `mcp__codegraphcontext__find_code` | grep |

Use **Serena** for precise symbol-level edits. Use **CGC** for orientation before touching anything.

## Multi-Agent Context

| Agent | Primary file |
|-------|-------------|
| Claude Code | `CLAUDE.md` (this file) |
| GitHub Copilot | `.github/copilot-instructions.md` |
| OpenCode / universal | `AGENTS.md` |

## L0 Directive

Agent coordination, task ownership, and leases → `ttadev/control_plane/` + `ttadev/cli/control.py`.
Extend there. Do not build parallel systems. See `docs/agents/dev/l0-coordination.md`.
