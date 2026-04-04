# `.agents/` — OpenHands Agent Skills

This directory contains **skill files** consumed by [OpenHands](https://github.com/All-Hands-AI/OpenHands)
during automated PR reviews and agentic workflows on this repository.

## Directory Layout

```
.agents/
├── README.md          ← this file
└── skills/
    └── code-review.md ← TTA.dev code-review guidelines (triggered by /codereview)
```

## What Skills Are

An OpenHands *skill* is a Markdown file with YAML frontmatter that tells the agent:

- **When to activate** (the `triggers` list — slash commands or event names)
- **What rules to apply** (the body of the Markdown file)

Skills are loaded automatically when OpenHands is attached to this repository.
They provide project-specific context that the agent uses *instead of* generic
heuristics, which means reviewers get consistent, accurate feedback every time.

## Adding a New Skill

1. Create `skills/<slug>.md` with valid frontmatter:
   ```yaml
   ---
   name: <slug>
   description: One-line description for the agent registry
   triggers:
     - /<command>
   ---
   ```
2. Write the body in plain Markdown — use numbered lists and code fences liberally.
3. Open a PR; the skill takes effect once merged to `main`.

## Current Skills

| Skill | Trigger | Purpose |
|---|---|---|
| `code-review` | `/codereview` | TTA.dev-specific PR review standards |

## Ownership

Skills are maintained by the backend engineering team.
Questions → open a GitHub issue with the `tooling` label.
