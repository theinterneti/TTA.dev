# TTA.dev Agent Instructions

Universal entry point for all AI agents working in this repository.

Boundary Rules: Write all project documentation, status updates, and notes exclusively to docs/kb-exports/. Never create or modify .md files in the project root or source directories unless explicitly asked to

## What is TTA.dev?

A Python monorepo providing composable workflow primitives, observability, and multi-agent coordination for building reliable AI applications.

## Repo Layout

```
platform/           # Core packages
├── primitives/     # tta-dev-primitives — core workflows
├── observability/  # tta-observability-integration
├── agent-context/  # universal-agent-context
├── agent-coordination/
├── integrations/
├── documentation/
└── kb-automation/
apps/               # User-facing applications
templates/          # Vibe coding starter templates
docs/               # Architecture, guides, agent docs
tests/              # Integration tests
scripts/            # Automation and validation
```

## Agent Skills (Tier 2)

Load these dynamically based on your current task:

| Skill | When to Use |
|-------|-------------|
| [build-test-verify](.claude/skills/build-test-verify/SKILL.md) | Building, testing, linting, verifying code |
| [git-commit](.claude/skills/git-commit/SKILL.md) | Making git commits |
| [create-pull-request](.claude/skills/create-pull-request/SKILL.md) | Creating or updating PRs |
| [core-conventions](.claude/skills/core-conventions/SKILL.md) | Writing or reviewing Python code |
| [self-review-checklist](.claude/skills/self-review-checklist/SKILL.md) | Pre-merge self-review |
| [sdd-workflow](.claude/skills/sdd-workflow/SKILL.md) | Building new features (SDD process) |

## Agent Guides (Tier 3)

Deep reference — load only when a skill's instructions are insufficient:

| Guide | Content |
|-------|---------|
| [testing-architecture](docs/agent-guides/testing-architecture.md) | Full testing standards, markers, CI pipeline, MockPrimitive API |
| [primitives-patterns](docs/agent-guides/primitives-patterns.md) | Composition operators, all primitives, recovery & performance patterns |
| [python-standards](docs/agent-guides/python-standards.md) | Type hints, naming, imports, docstrings, error handling |
| [sdd-constitution](docs/agent-guides/sdd-constitution.md) | Complete SDD Constitution §1-§4 |
| [observability-guide](docs/agent-guides/observability-guide.md) | OpenTelemetry tracing, metrics, context propagation |
| [todo-management](docs/agent-guides/todo-management.md) | Logseq TODOs, tags, properties, validation |

## Key References

- [Getting Started](GETTING_STARTED.md) — Setup and first workflow
- [Primitives Catalog](PRIMITIVES_CATALOG.md) — Complete API reference
- [MCP Tool Registry](MCP_TOOL_REGISTRY.md) — Available MCP tools
- [Hindsight Memory](docs/guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md) — Cross-agent persistent memory

## Agent-Specific Config

| Agent | Config |
|-------|--------|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) (primary agent) |
| GitHub Copilot | [`.github/copilot-instructions.md`](.github/copilot-instructions.md) |
| Copilot path-based rules | [`.github/instructions/`](.github/instructions/) |
