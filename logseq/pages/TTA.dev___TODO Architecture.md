type:: [[Architecture]]
description:: Complete system design for TTA.dev TODO management

# TODO Architecture

Complete reference for the TTA.dev TODO management system architecture.

## Overview

TTA.dev uses Logseq as the primary TODO management system. All tasks are tracked in journal entries with structured tags and properties.

## Tag Convention

| Tag | Purpose | Example |
|-----|---------|---------|
| `#dev-todo` | Development work (building TTA.dev) | Implement new primitive |
| `#learning-todo` | User education (tutorials, exercises) | Write getting started guide |
| `#template-todo` | Reusable patterns for agents/users | Create workflow template |
| `#ops-todo` | Infrastructure and deployment | Set up CI/CD pipeline |

## TODO Format

```markdown
- TODO Task description #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives]]
```

## Priority Levels

- `[#A]` - High priority: blocking or urgent
- `[#B]` - Medium priority: important but not urgent
- `[#C]` - Low priority: nice to have

## Properties

| Property | Values | Description |
|----------|--------|-------------|
| `type::` | implementation, bug, docs, refactor | Task type |
| `priority::` | high, medium, low | Task urgency |
| `package::` | tta-dev-primitives, etc. | Affected package |
| `related::` | wiki link to page | Related KB pages |

## Workflow

1. Add TODOs to today's journal: `logseq/journals/YYYY_MM_DD.md`
2. Tag with appropriate `#tag`
3. Set priority if needed
4. Track status: `TODO` → `DOING` → `DONE`

## Dashboard Pages

- [[TODO Management System]] - Active task dashboard with live queries
- [[TODO Templates]] - Copy-paste patterns for common task types

## Related Pages
- [[TTA.dev]] - Project overview
- [[TTA.dev/TODOs]] - Legacy TODO dashboard
