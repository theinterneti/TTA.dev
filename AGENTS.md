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

# Running with 1Password secret injection:
op run --env-file=.env -- uv run python -m ttadev.observability
# First copy .env.template to .env and fill in your keys
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
| Composition model / catalog | `docs/agents/dev/composition-model.md` |

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

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **TTA.dev** (36271 symbols, 58586 relationships, 246 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/TTA.dev/context` | Codebase overview, check index freshness |
| `gitnexus://repo/TTA.dev/clusters` | All functional areas |
| `gitnexus://repo/TTA.dev/processes` | All execution flows |
| `gitnexus://repo/TTA.dev/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
| Work in the Unit area (1397 symbols) | `.claude/skills/generated/unit/SKILL.md` |
| Work in the Scripts area (187 symbols) | `.claude/skills/generated/scripts/SKILL.md` |
| Work in the Tests area (177 symbols) | `.claude/skills/generated/tests/SKILL.md` |
| Work in the Llm area (156 symbols) | `.claude/skills/generated/llm/SKILL.md` |
| Work in the Adaptive area (151 symbols) | `.claude/skills/generated/adaptive/SKILL.md` |
| Work in the Cli area (108 symbols) | `.claude/skills/generated/cli/SKILL.md` |
| Work in the Observability area (91 symbols) | `.claude/skills/generated/observability/SKILL.md` |
| Work in the Control_plane area (82 symbols) | `.claude/skills/generated/control-plane/SKILL.md` |
| Work in the Agents area (77 symbols) | `.claude/skills/generated/agents/SKILL.md` |
| Work in the Integration area (65 symbols) | `.claude/skills/generated/integration/SKILL.md` |
| Work in the Integrations area (60 symbols) | `.claude/skills/generated/integrations/SKILL.md` |
| Work in the Workflows area (56 symbols) | `.claude/skills/generated/workflows/SKILL.md` |
| Work in the Memory area (55 symbols) | `.claude/skills/generated/memory/SKILL.md` |
| Work in the Recovery area (48 symbols) | `.claude/skills/generated/recovery/SKILL.md` |
| Work in the Js area (48 symbols) | `.claude/skills/generated/js/SKILL.md` |
| Work in the Tools area (32 symbols) | `.claude/skills/generated/tools/SKILL.md` |
| Work in the Safety area (24 symbols) | `.claude/skills/generated/safety/SKILL.md` |
| Work in the Testing area (21 symbols) | `.claude/skills/generated/testing/SKILL.md` |
| Work in the Config area (21 symbols) | `.claude/skills/generated/config/SKILL.md` |
| Work in the Apm area (21 symbols) | `.claude/skills/generated/apm/SKILL.md` |

<!-- gitnexus:end -->
