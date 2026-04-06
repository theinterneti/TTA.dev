# TTA.dev — Claude Code (Main Agent)

Claude Code is the **primary agent** for this repository. Other agents defer to Claude Code's decisions on architecture and standards. The owner is the sole developer.

## SDD Mandate

**No implementation code before a signed-off spec.** Follow the [sdd-workflow](.claude/skills/sdd-workflow/SKILL.md) skill for the 4-phase process (`/specify` → `/plan` → `/tasks` → `/implement`). Full constitution: [docs/agent-guides/sdd-constitution.md](docs/agent-guides/sdd-constitution.md).

## Session Start Protocol

**Every session begins with `/session-start`** (or the session-start skill steps manually).

1. `mcp__hindsight__recall` — query `adam-global` for durable directives/preferences, then query the current derived `project-*` or `workspace-*` bank for repository-specific mental models and context
2. `mcp__codegraphcontext__get_repository_stats` — confirm graph is current
3. Acknowledge what was loaded before any task work begins

**Every significant task ends with `mcp__hindsight__retain`** to the right bank:
- retain cross-project preferences and reusable workflow patterns in `adam-global`
- retain repository-specific decisions, commands, patterns, and failures in the current derived `project-*` or `workspace-*` bank

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
| [llm-provider-strategy](docs/agent-guides/llm-provider-strategy.md) | Live Hindsight runtime defaults, Groq preference, and fallback provider guidance |

## Non-Negotiable Standards (Quick Reference)

- **Package manager:** `uv` always (never `pip`/`poetry`)
- **Python:** 3.12+ with `str | None` (not `Optional[str]`)
- **Linting:** Ruff — line length 88, strict mode (`uv run ruff check . --fix`)
- **Type checking:** Pyright basic mode (`uvx pyright ttadev/`)
- **Testing:** pytest AAA pattern, 100% coverage for new code — use `make watch` during development, `make test` for the full run
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Primitives:** Always use for workflows (never manual retry/timeout loops)
- **State:** Pass via `WorkflowContext` (never globals)
- **LLM providers:** Groq `openai/gpt-oss-20b` for the live Hindsight runtime by default; keep Gemini 3.1 Flash Lite Preview and local Ollama as fallbacks — see [llm-provider-strategy](docs/agent-guides/llm-provider-strategy.md)
- **Orient before edit:** Run CGC (`find_code` + `analyze_code_relationships`) on any non-trivial target before touching it — **enforced by hook** (`.claude/settings.json`)
- **Retain after task:** Store cross-project signal in `adam-global` and repo-specific signal in the current derived `project-*` or `workspace-*` Hindsight bank
- **TTA cross-repo edits:** `~/Repos/TTA` is owned by the local TTA agent — never edit it directly. Clone to `/tmp/TTA-copilot`, commit + push, then `rm -rf /tmp/TTA-copilot`.

### Tool Selection: Symbol Lookup

Prefer semantic tools over raw file reads for symbol-level work:

| Goal | Use | Instead of |
|------|-----|------------|
| Find where a function/class is defined | `mcp__plugin_serena_serena__find_symbol` | `Grep` + `Read` |
| Find all callers of a function | `mcp__plugin_serena_serena__find_referencing_symbols` | `Grep` pattern search |
| Scan all symbols in a file | `mcp__plugin_serena_serena__get_symbols_overview` | `Read` whole file |
| Replace a function body precisely | `mcp__plugin_serena_serena__replace_symbol_body` | `Edit` with large context |
| Understand cross-file dependencies | `mcp__codegraphcontext__analyze_code_relationships` | Reading multiple files |
| Search for a symbol across the repo | `mcp__codegraphcontext__find_code` | `Grep` |

**When to use Serena vs CGC:**
- Use **Serena** for precise, symbol-level edits (you know the function, you want to read/replace it)
- Use **CGC** for orientation (you need to understand relationships and impact before touching anything)

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
- `ttadev/primitives/mcp_server/server.py`

If a task is about coordinating coding agents, task ownership, approvals, leases,
or developer work orchestration, **continue from that L0 surface** rather than
building a second orchestration system somewhere else.

### Immediate L0 Priorities

1. use the current L0 surface to prove one documented, repeatable multi-agent workflow
2. deepen approval/policy/review workflows only where that workflow needs richer coordination
3. strengthen ownership and telemetry attribution so active workflow steps can be explained clearly
4. connect additional agent-facing surfaces to the existing L0 state instead of creating parallel coordination systems

When implementing these, keep the design additive, local-first, and compatible
with the existing `.tta` session/project model.
