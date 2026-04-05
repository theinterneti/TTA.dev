# TTA.dev — Agent Instructions

> Universal entry point. All AI coding agents read this first.
> OpenCode users: this is your primary instruction file.

## What is TTA.dev?

A Python library of composable workflow primitives, observability tooling, and multi-agent
coordination infrastructure. The sole developer uses Claude Code, GitHub Copilot, and OpenCode.

## Commands

```bash
uv sync --all-extras    # Install (uv only — never pip or poetry)
make watch              # TDD loop (fast, fail-fast, use during development)
make test               # Full run with coverage (use before committing)
uv run ruff format . && uv run ruff check . --fix   # Format + lint
uvx pyright ttadev/     # Type check
.github/copilot-hooks/post-generation.sh            # Full quality gate
```

## Rules (non-negotiable)

- `uv` only — never `pip` or `poetry`
- Python 3.12+, `str | None` not `Optional[str]`, `dict[str, Any]` not `Dict`
- Always use primitives for retry/timeout/circuit-breaker — never write manual loops
- Pass state via `WorkflowContext` — no globals
- 100% test coverage on new code; AAA pattern; `MockPrimitive` for mocking
- Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)
- Never edit `~/Repos/TTA` directly — clone to `/tmp/TTA-copilot`, push, then delete

## Routing: When working on…

| Topic | Read before touching code |
|-------|--------------------------|
| Primitives / architecture | `docs/agents/dev/architecture.md` |
| Retry / timeout / circuit breaker | `docs/agents/dev/reliability.md` |
| OTel / Langfuse tracing | `docs/agents/dev/observability.md` |
| Tests / coverage / MockPrimitive | `docs/agents/dev/testing.md` |
| L0 task coordination / leases | `docs/agents/dev/l0-coordination.md` |
| Agent roles / roster | `docs/agents/runtime/l0-roster.md` |

## Skills (on-demand HOW-TO workflows)

`build-test-verify` · `core-conventions` · `git-commit` · `create-pull-request`
`self-review-checklist` · `sdd-workflow` · `session-start`

Skills live in `.github/skills/`. Before creating a new skill, search `github/awesome-copilot` first.

## L0 Directive

Agent coordination, task ownership, and leases live in `ttadev/control_plane/` and
`ttadev/cli/control.py`. Extend there — do not build parallel systems.

## Maintenance

See `docs/agents/MAINTENANCE.md` — budget enforcement, how to update this tree,
and cross-repo sync rules with the TTA repository.
