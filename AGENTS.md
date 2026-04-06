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

Skills live in `.github/skills/`. Invoke by name when relevant.

| Skill | Purpose |
|-------|---------|
| `session-start` | Orient at session start — load context, warm up |
| `build-test-verify` | Build, test, lint, type-check, verify quality |
| `core-conventions` | Python code conventions (uv, types, primitives, state) |
| `git-commit` | Conventional Commits format and pre-commit checks |
| `create-pull-request` | PR title, description, review checklist |
| `self-review-checklist` | Pre-merge quality audit |
| `sdd-workflow` | Spec-Driven Development 4-phase workflow |
| `ttadev-primitives` | Compose workflows with `>>` operator and primitives |
| `ttadev-llm` | Call LLMs via LiteLLMPrimitive / UniversalLLMPrimitive |
| `feature-development` | Full-stack feature workflow (API → UI → tests) |
| `package-release` | PyPI release workflow with validation |
| `incident-response` | Emergency production response |
| `create-atomic-note` | Save a KB note to `docs/kb-exports/` |

Before creating a new skill, search `github/awesome-copilot` first.

## Agent-Specific Guides (`docs/agent-guides/`)

Deep-dive references for specific topics:

| Guide | Content |
|-------|---------|
| `testing-architecture.md` | Testing standards, CI pipeline |
| `primitives-patterns.md` | Composition, all primitives |
| `python-standards.md` | Types, naming, imports |
| `sdd-constitution.md` | Full SDD §1-§4 |
| `observability-guide.md` | OpenTelemetry integration |
| `todo-management.md` | Repository TODO format |
| `secrets-guide.md` | API keys, `.env`, 1Password CLI |
| `llm-provider-strategy.md` | Provider routing and fallback |
| `l0-workflow-runbook.md` | L0 control plane walkthrough |

## Custom Agents (`.github/agents/`)

Copilot Chat agents with specialized roles:

| Agent | Specialty |
|-------|-----------|
| `architect` | System design, patterns, trade-offs |
| `backend-engineer` | Python primitives and workflows |
| `frontend-engineer` | React/TypeScript UI |
| `testing-specialist` | QA, test automation, validation |
| `code-reviewer` | Post-implementation quality audit |
| `project-planner` | SDD specs and task breakdowns |
| `devops-engineer` | Infrastructure, CI/CD, deployment |
| `data-scientist` | Data analysis, ML workflows |
| `observability-expert` | Monitoring, tracing, metrics |

## Copilot Instructions (`.github/instructions/`)

Auto-applied by file pattern — agents don't need to reference these directly:

| File | Applies to |
|------|-----------|
| `python.instructions.md` | `ttadev/**/*.py` |
| `testing.instructions.md` | `**/tests/**/*.py` |
| `scripts.instructions.md` | `scripts/**/*.py` |
| `documentation.instructions.md` | `**/*.md` |
| `agents.instructions.md` | `**/*.agent.md` |
| `agent-skills.instructions.md` | `**/.github/skills/**/SKILL.md` |
| `instructions.instructions.md` | `**/*.instructions.md` |
| `agent-safety.instructions.md` | `**` (all files) |
| `context-engineering.instructions.md` | `**` (all files) |
| `ai-prompt-engineering-safety-best-practices.instructions.md` | `**` (all files) |
| `github-actions-ci-cd-best-practices.instructions.md` | `.github/workflows/*.yml` |

## L0 Directive

Agent coordination, task ownership, and leases live in `ttadev/control_plane/` and
`ttadev/cli/control.py`. Extend there — do not build parallel systems.

## Maintenance

See `docs/agents/MAINTENANCE.md` — budget enforcement, how to update this tree,
and cross-repo sync rules with the TTA repository.
