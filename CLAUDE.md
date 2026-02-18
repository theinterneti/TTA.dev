# TTA.dev — Claude Code (Main Agent)

This is the root CLAUDE.md for the TTA.dev monorepo. Claude Code is the **primary/main agent** for this repository. Other agents (Cline, GitHub Copilot, Augment CLI, Gemini) are secondary and should be deferred to Claude Code's decisions on architecture and standards.

The owner is the **sole developer**. All code is original work.

---

## What is TTA.dev?

A production-ready **AI development toolkit** — a Python monorepo providing composable workflow primitives, observability, multi-agent coordination, and integrations for building reliable AI applications.

## Repo Layout

```
TTA.dev/
├── platform/              # Core packages (7 packages)
│   ├── primitives/        # tta-dev-primitives v1.3.0 — core workflows
│   ├── observability/     # tta-observability-integration v1.0.0
│   ├── agent-context/     # universal-agent-context v1.0.0
│   ├── agent-coordination/# tta-agent-coordination (active dev)
│   ├── integrations/      # tta-dev-integrations v0.1.0
│   ├── documentation/     # tta-documentation-primitives
│   └── kb-automation/     # tta-kb-automation
├── apps/                  # observability-ui, n8n, streamlit-mvp
├── templates/             # Vibe coding templates
├── docs/                  # Architecture, guides, agent docs
├── tests/                 # Integration tests
├── scripts/               # Automation and validation scripts
├── data/ace_playbooks/    # ACE agent playbooks
├── logseq/                # Knowledge base + TODO management
├── .hindsight/            # Cross-agent persistent memory
├── .cline/                # Cline agent config
├── .augment/              # Augment CLI agent config
└── .github/               # CI/CD + Copilot instructions
```

## Non-Negotiable Standards

- **Package manager:** `uv` always. Never `pip` or `poetry`.
- **Python:** 3.11+ — use `str | None` not `Optional[str]`, `dict[str, Any]` not `Dict`
- **Formatter:** Ruff at 100-char line length (`uv run ruff format .`)
- **Linter:** Ruff (`uv run ruff check . --fix`)
- **Type checker:** Pyright basic mode (`uvx pyright platform/`)
- **Tests:** pytest + pytest-asyncio; `@pytest.mark.asyncio` on async tests; 100% coverage for new code
- **Commits:** Conventional Commits — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **No global state:** pass data through `WorkflowContext`

## Core Pattern: Primitive Composition

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> process_data

result = await workflow.execute(input_data, WorkflowContext(workflow_id="demo"))
```

**Anti-patterns** — never write these manually:
- `try/except` retry loops → use `RetryPrimitive`
- `asyncio.wait_for()` → use `TimeoutPrimitive`
- Manual cache dicts → use `CachePrimitive`

## Quality Gate (run before every commit)

```bash
uv run ruff format .
uv run ruff check . --fix
uvx pyright platform/
uv run pytest -v
```

## TODO Management

All TODOs go in Logseq (`logseq/journals/YYYY_MM_DD.md`).
Tags: `#dev-todo`, `#learning-todo`, `#template-todo`, `#ops-todo`

## Multi-Agent Context

| Agent | Role | Config |
|-------|------|--------|
| **Claude Code** | **Main agent — primary decision maker** | `CLAUDE.md` (this file) |
| Cline | Secondary — fast iteration | `.cline/instructions.md`, `.clinerules` |
| GitHub Copilot | Autocomplete + toolsets | `.github/copilot-instructions.md` |
| Augment CLI | Context management | `.augment/` |
| Gemini | Sub-agent tasks | `platform/agent-context/GEMINI.md` |

Cross-agent memory lives in `.hindsight/`. Claude Code's own persistent memory is at `~/.claude/projects/-home-thein-repos-TTA-dev/memory/`.

## Key Reference Files

- `AGENTS.md` — universal agent guidance (all agents read this)
- `PRIMITIVES_CATALOG.md` — full API reference
- `GETTING_STARTED.md` — quick start
- `docs/architecture/Overview.md` — system architecture
- `.cline/instructions.md` — Cline-specific instructions
- `MCP_TOOL_REGISTRY.md` — available MCP tools
