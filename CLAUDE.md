# TTA.dev — Claude Code (Main Agent)

Claude Code is the **primary agent** for this repository. Other agents defer to Claude Code's decisions on architecture and standards. The owner is the sole developer.

## SDD Mandate

**No implementation code before a signed-off spec.** Follow the [sdd-workflow](.claude/skills/sdd-workflow/SKILL.md) skill for the 4-phase process (`/specify` → `/plan` → `/tasks` → `/implement`). Full constitution: [docs/agent-guides/sdd-constitution.md](docs/agent-guides/sdd-constitution.md).

## Session Start Protocol

**Every session begins with `/session-start`** (or the session-start skill steps manually).

1. `mcp__hindsight__recall` — query `tta-dev` bank for directives + mental models
2. `mcp__codegraphcontext__get_repository_stats` — confirm graph is current
3. Acknowledge what was loaded before any task work begins

**Every significant task ends with `mcp__hindsight__retain`** to the `tta-dev` bank:
decisions made, patterns used, failures encountered.

## Repo Layout

```
ttadev/             # Main package
├── primitives/     # Core workflow primitives (retry, cache, timeout, etc.)
├── agents/         # Role-based agent system (specs, registry, router)
├── observability/  # OpenTelemetry integration
├── integrations/   # LLM integrations (Anthropic, OpenAI, Groq, etc.)
├── cli/            # `tta` CLI subcommands
├── skills/         # Agent skills
└── ui/             # UI components
docs/               # Architecture, guides, agent docs
tests/              # Test suite
```

## Agent Skills (Tier 2)

| Skill | When to Use |
|-------|-------------|
| [session-start](.claude/skills/session-start/SKILL.md) | Start of every session — load directives, mental models, CGC orientation |
| [build-test-verify](.claude/skills/build-test-verify/SKILL.md) | Build, test, lint, verify |
| [git-commit](.claude/skills/git-commit/SKILL.md) | Making commits |
| [create-pull-request](.claude/skills/create-pull-request/SKILL.md) | Creating PRs |
| [core-conventions](.claude/skills/core-conventions/SKILL.md) | Writing/reviewing Python code |
| [self-review-checklist](.claude/skills/self-review-checklist/SKILL.md) | Pre-merge review |
| [sdd-workflow](.claude/skills/sdd-workflow/SKILL.md) | New feature development |

## Agent Guides (Tier 3)

| Guide | Content |
|-------|---------|
| [testing-architecture](docs/agent-guides/testing-architecture.md) | Testing standards, CI pipeline |
| [primitives-patterns](docs/agent-guides/primitives-patterns.md) | Composition, all primitives |
| [python-standards](docs/agent-guides/python-standards.md) | Types, naming, imports |
| [sdd-constitution](docs/agent-guides/sdd-constitution.md) | Full SDD §1-§4 |
| [observability-guide](docs/agent-guides/observability-guide.md) | OpenTelemetry integration |
| [todo-management](docs/agent-guides/todo-management.md) | Repository TODO format and session task tracking |
| [secrets-guide](docs/agent-guides/secrets-guide.md) | API keys, `.env`, 1Password CLI |
| [llm-provider-strategy](docs/agent-guides/llm-provider-strategy.md) | LLM provider hierarchy, OpenRouter + Ollama |

## Non-Negotiable Standards (Quick Reference)

- **Package manager:** `uv` always (never `pip`/`poetry`)
- **Python:** 3.11+ with `str | None` (not `Optional[str]`)
- **Linting:** Ruff — line length 88, strict mode (`uv run ruff check . --fix`)
- **Type checking:** Pyright basic mode (`uvx pyright ttadev/`)
- **Testing:** pytest AAA pattern, 100% coverage for new code
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Primitives:** Always use for workflows (never manual retry/timeout loops)
- **State:** Pass via `WorkflowContext` (never globals)
- **LLM providers:** OpenRouter free models first, Ollama fallback — see [llm-provider-strategy](docs/agent-guides/llm-provider-strategy.md)
- **Orient before edit:** Run CGC (`find_code` + `analyze_code_relationships`) on any non-trivial target before touching it
- **Retain after task:** Store decisions, patterns, failures to `tta-dev` Hindsight bank after each significant task

### ⛔ TODO Management — CI-Blocking Rule

All TODOs must strictly follow the [TODO Management System](docs/agent-guides/todo-management.md).
You **must** use the `#dev-todo` tag and include `type::`, `priority::`, and `package::` properties.
**Malformed TODOs will block CI.**

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <package-name>
```

Details: [core-conventions](.claude/skills/core-conventions/SKILL.md)

## Key References

- [AGENTS.md](AGENTS.md) — Universal agent guidance
- [PRIMITIVES_CATALOG.md](PRIMITIVES_CATALOG.md) — Full API reference
- [GETTING_STARTED.md](GETTING_STARTED.md) — Quick start
- [MCP_TOOL_REGISTRY.md](MCP_TOOL_REGISTRY.md) — Available MCP tools

## Multi-Agent Context

| Agent | Config |
|-------|--------|
| **Claude Code** | `CLAUDE.md` (this file) |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Copilot path rules | `.github/instructions/` |

Cross-agent memory: `.hindsight/` — see [Hindsight Memory](docs/guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md).

## L0 Continuation Directive

`TTA.dev` now contains the first implemented L0 developer control-plane slice:

- `ttadev/control_plane/`
- `ttadev/cli/control.py`

If a task is about coordinating coding agents, task ownership, approvals, leases,
or developer work orchestration, **continue from that L0 surface** rather than
building a second orchestration system somewhere else.

### Immediate L0 Priorities

1. expose current task/run/lease operations through MCP tools
2. add approval and policy state
3. add workspace/file-lock coordination
4. wire observability and agent telemetry into L0 ownership views

When implementing these, keep the design additive, local-first, and compatible
with the existing `.tta` session/project model.
