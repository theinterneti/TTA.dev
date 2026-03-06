# TTA.dev Documentation

Index and navigation guide for TTA.dev documentation.

## Directory Structure

```text
docs/
├── guides/           # How-to guides (setup, integration, troubleshooting)
├── reference/        # API reference, specs, MCP protocol docs
├── architecture/     # System design and architecture decision records
├── examples/         # Working code examples
└── _archive/         # Historical reports and planning docs
```

## guides/

How-to guides for development, integration, and operations.

| Subdirectory | Contents |
|-------------|----------|
| [agents/](guides/agents/) | Agent-specific guidance and memory architecture |
| [ci-cd/](guides/ci-cd/) | CI/CD workflow guides |
| [development/](guides/development/) | Coding standards, dev environment setup |
| [integration/](guides/integration/) | External system integration guides |
| [integrations/](guides/integrations/) | Cline, E2B, and tool integration guides |
| [observability/](guides/observability/) | Tracing, metrics, and monitoring setup |
| [quickstart/](guides/quickstart/) | Quick start guides for observability |
| [runbooks/](guides/runbooks/) | Operational runbooks |
| [troubleshooting/](guides/troubleshooting/) | Debugging and troubleshooting guides |

Also includes standalone guides at the `guides/` root (e.g., secrets management,
migration, LLM selection, production deployment).

## reference/

API reference, protocol documentation, and specifications.

| Subdirectory | Contents |
|-------------|----------|
| [mcp/](reference/mcp/) | Model Context Protocol usage, integration, and Hypertool docs |
| [mcp-references/](reference/mcp-references/) | MCP server reference (GitHub, Grafana, filesystem, etc.) |
| [models/](reference/models/) | Model selection strategy and evaluation |
| [specs/](reference/specs/) | Formal SDD specifications ([index](reference/specs/README.md)) |

## architecture/

System design documents and architecture decision records.

Key files:
- [Overview.md](architecture/Overview.md) — System architecture overview
- [PRIMITIVE_PATTERNS.md](architecture/PRIMITIVE_PATTERNS.md) — Primitive composition patterns
- [DECISION_RECORDS.md](architecture/DECISION_RECORDS.md) — Architecture decision records

## examples/

Working code examples demonstrating TTA.dev primitives and patterns.

- [README.md](examples/README.md) — Example index
- [primitive-composition.md](examples/primitive-composition.md) — Sequential, parallel, retry, fallback, timeout, cache, routing examples
- [custom_tool.md](examples/custom_tool.md) — Custom tool example

## _archive/

Historical content preserved for reference. AI agents should generally ignore
this directory unless researching project history.

Contains: daily-logs, sessions, status-reports, planning, knowledge-base,
research, strategy, refactor, and completed milestone reports.

## Quick Reference

| Task | Start With |
|------|------------|
| **New to TTA.dev** | [GETTING_STARTED.md](../GETTING_STARTED.md) |
| **Core Primitives** | [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) |
| **Primitive Specs** | [reference/specs/README.md](reference/specs/README.md) |
| **System Design** | [architecture/Overview.md](architecture/Overview.md) |
| **MCP Integration** | [reference/mcp/README.md](reference/mcp/README.md) |
| **How-to Guides** | [guides/README.md](guides/README.md) |
| **Agent Guidance** | [AGENTS.md](../AGENTS.md) |
