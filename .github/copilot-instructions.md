# TTA.dev Copilot Instructions

A Python library of workflow primitives and multi-agent coordination. Sole developer —
build fast, scale when needed.

## Quality Gate (mandatory after every code change)

```bash
.github/copilot-hooks/post-generation.sh
```

Thresholds: Ruff all-pass · Pyright ≤2 errors · Pytest all non-integration tests pass · Coverage ≥ 80%

## Commands

```bash
uv sync --all-extras                                # Install (uv only — never pip)
make watch                                          # TDD loop
make test                                           # Full run with coverage
uv run ruff format . && uv run ruff check . --fix   # Format + lint
uvx pyright ttadev/                                 # Type check
```

## Standards

- Python 3.12+, `str | None` not `Optional[str]`, `dict[str, Any]` not `Dict`
- Line length 100 (Ruff enforced); docstrings Google style
- Always use primitives for retry/timeout/circuit-breaker — never write manual loops
- Pass state via `WorkflowContext` — no globals
- 100% coverage on new code; AAA test pattern with `MockPrimitive`
- Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)

## Routing: When working on…

| Topic | Read before touching code |
|-------|--------------------------|
| Primitives / architecture | `docs/agents/dev/architecture.md` |
| Retry / timeout / circuit breaker | `docs/agents/dev/reliability.md` |
| OTel / Langfuse tracing | `docs/agents/dev/observability.md` |
| Tests / coverage | `docs/agents/dev/testing.md` |
| L0 task coordination | `docs/agents/dev/l0-coordination.md` |

## Skills (use these for complex tasks)

| Skill | When |
|-------|------|
| `build-test-verify` | Before any commit or PR |
| `core-conventions` | Writing or reviewing Python |
| `git-commit` | Making commits |
| `create-pull-request` | Opening PRs |
| `self-review-checklist` | Pre-merge |
| `sdd-workflow` | New features |

Before creating a new skill, search `github/awesome-copilot` skills directory first.

## L0 Directive

Agent coordination and task leases live in `ttadev/control_plane/`. Extend there — no parallel systems.
