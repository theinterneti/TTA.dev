# Composition Model

TTA.dev uses a four-layer composition model connecting atomic standards to
full agent capabilities. The canonical registry is
`.github/copilot-catalog.yml`.

## Layers

```
INSTRUCTIONS (atomic standards, auto-applied by glob)
    ↓ referenced by (instruction_refs)
SKILLS (capabilities) + WORKFLOWS (multi-step processes)
    ↓ composed into (skill_refs + workflow_refs)
AGENTS (orchestrators with tools + MCP access)
```

### Instructions

Atomic coding standards in `.github/instructions/`. Applied automatically by
`applyTo` glob — agents don't reference these directly. IDs are derived from
filenames: `python.instructions.md` → `python`.

### Skills & Workflows

On-demand capabilities in `.github/skills/`. The catalog distinguishes:

- **`kind: capability`** — Reusable task (e.g., `build-test-verify`, `core-conventions`)
- **`kind: workflow`** — Multi-step process (e.g., `sdd-workflow`, `feature-development`)

Each skill declares `instruction_refs` — the instructions it depends on.

### Agents

Role-based specialists in `.github/agents/`. Each declares:

- `skill_refs` — capabilities it uses
- `workflow_refs` — processes it follows
- `tools` — kept in `.agent.md` frontmatter (official Copilot field)

## Canonical Stack

All integrations route through these four systems:

| System | Role | Implementation |
|--------|------|----------------|
| **LiteLLM** | All LLM calls | `LiteLLMPrimitive` in `ttadev/primitives/llm/` |
| **Langfuse** | LLM observability | Auto-wired via `LANGFUSE_*` env vars |
| **Hindsight** | Cross-session memory | MCP server at `http://localhost:8888/mcp/` |
| **OpenHands** | Agent execution | `OpenHandsPrimitive` in `ttadev/primitives/integrations/` |

## Registry

The single source of truth is `.github/copilot-catalog.yml`. It contains:

- `stack` — canonical technology choices
- `instructions` — all instruction files with their glob patterns
- `skills` — all skills/workflows with `kind` and `instruction_refs`
- `agents` — all agents with `skill_refs` and `workflow_refs`

### Validation

```bash
uv run python scripts/validate-catalog.py
```

Checks:
- All referenced paths exist on disk
- All `instruction_refs`, `skill_refs`, `workflow_refs` resolve to valid entries
- No orphaned files (files on disk not in registry)
- No circular references

### Adding a new skill

1. Create `.github/skills/<name>/SKILL.md` with standard frontmatter
2. Add entry to `.github/copilot-catalog.yml` under `skills:`
3. Add skill to relevant agents' `skill_refs`
4. Add ONE row to the AGENTS.md skills table
5. Run `uv run python scripts/validate-catalog.py`

### Adding a new agent

1. Create `.github/agents/<name>.agent.md` with standard frontmatter
2. Add entry to `.github/copilot-catalog.yml` under `agents:`
3. Add ONE row to the AGENTS.md agents table
4. Run `uv run python scripts/validate-catalog.py`
