---
description: 'TTA.dev conventions for custom agent files'
applyTo: '**/*.agent.md'
---

# TTA.dev Agent Conventions

Agents live in `.github/agents/` and follow [GitHub's agent spec](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents).
This instruction covers **TTA.dev-specific** rules only.

## Frontmatter

Required fields: `name`, `description`, `tools`.
Recommended: `model`, `handoffs` (for workflow transitions).

```yaml
---
name: my-agent
description: 'What this agent does — be specific for discovery'
tools: ['read', 'edit', 'search', 'context7', 'github', 'serena']
model: 'claude-sonnet-4-5'
---
```

## Tool Selection

Use least-privilege. Common TTA.dev MCP tools:

| Tool | When to include |
|------|----------------|
| `context7` | Needs library docs lookup |
| `github` | Needs GitHub API access |
| `serena` | Needs symbol-level code navigation |
| `gitmcp` | Needs git history analysis |
| `sequential-thinking` | Complex reasoning tasks |
| `grafana` | Observability/monitoring tasks |
| `playwright` | Browser/UI testing |

Built-in aliases: `read`, `edit`, `search`, `execute`, `agent`, `web`.

## Body Structure

Every agent body should follow this pattern:

1. **Role** — One-line identity (e.g., "You are a **Backend Engineer** for TTA.dev")
2. **Before You Begin** — Session setup steps (dashboard, context loading)
3. **Core Responsibilities** — What this agent does
4. **Constraints** — What it must NOT do
5. **Quality Standards** — TTA.dev-specific checks

## Composition Registry

Every agent must be registered in `.github/copilot-catalog.yml` with its
`skill_refs` and `workflow_refs`. After creating or modifying an agent:

```bash
uv run python scripts/validate-catalog.py
```

See `docs/agents/dev/composition-model.md` for the full model:
INSTRUCTIONS → SKILLS/WORKFLOWS → AGENTS.

## Naming

- Filename: `lowercase-with-hyphens.agent.md`
- Name field: `Title Case` or `lowercase-with-hyphens`
- One agent per specialty — don't duplicate roles

## Handoffs

Use handoffs for workflow transitions between agents:

```yaml
handoffs:
  - label: 'Start Implementation'
    agent: backend-engineer
    prompt: 'Implement the plan above following TTA.dev conventions.'
    send: false
```

Keep to 2-3 handoffs max. Target agents must exist in `.github/agents/`.

## Deep Reference

For detailed patterns (orchestration, variables, tool config, prompt structure),
use the `create-agent` skill or see [GitHub's agent docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents).
