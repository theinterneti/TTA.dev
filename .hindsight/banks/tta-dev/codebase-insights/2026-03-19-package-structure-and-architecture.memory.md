---
category: codebase-insights
date: 2026-03-19
component: architecture
severity: high
tags: [package-structure, architecture, stale-docs, modules]
related_memories: []
---
# TTA.dev Package Structure and Architecture

Single Python package `ttadev` v0.1.0. Old `packages/` layout in AGENTS.md is outdated — everything is in `ttadev/`.

## Module Map

| Module | Purpose | Status |
|---|---|---|
| `ttadev/primitives/` | Core workflow primitives (v1.3.1) | Stable |
| `ttadev/agents/` | Role-based agent system | Phase 2, done |
| `ttadev/workflows/` | Guided workflow orchestrator | Phase 3, done |
| `ttadev/integrations/` | LLM provider selection | Stable |
| `ttadev/cli/` | `tta` CLI (run/project/session/agent/workflow) | Stable |
| `ttadev/skills/` | Skills sub-package (`tta_skill_primitives`) | Stable |
| `ttadev/observability/` | OpenTelemetry integration | Stable |
| `ttadev/ui/` | UI components | Stable |

## Key Entry Points

- `tta` CLI → `ttadev.cli:main`
- `ttadev/__init__.py` exports only `initialize_observability()` (explicit opt-in)
- `ttadev/primitives/__init__.py` auto-calls `setup_tracing()` on import

## Stale Documentation (Do Not Follow)

- `AGENTS.md` — references `platform/` directory (does not exist)
- `PRIMITIVES_CATALOG.md` — imports reference old `tta_dev_primitives` package name
- `docs/agent-guides/llm-provider-strategy.md` — lists nemotron as default (nemotron is broken, see llm-provider-strategy memory)

---

**Created:** 2026-03-19
**Last Updated:** 2026-03-19
**Verified:** [x] Yes
