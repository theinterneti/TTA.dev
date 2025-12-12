type:: reference
status:: active
created:: 2025-12-04

# TTA.dev Architecture

**System architecture overview for the TTA.dev multi-agent development platform.**

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TTA.dev Platform                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Augment   │  │    Cline    │  │   Copilot   │   Agents     │
│  │  Worktree   │  │  Worktree   │  │  Worktree   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Main Worktree                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │  │
│  │  │ pages/  │  │journals/│  │platform/│  │  docs/  │       │  │
│  │  │   KB    │  │ Shared  │  │Packages │  │  Docs   │       │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    TTA-notes (Shared Brain)                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Platform Packages

Located in `platform/`:

| Package | Purpose |
|---------|---------|
| **primitives** | Core workflow building blocks (30+ primitives) |
| **agent-context** | Context engineering for agents |
| **agent-coordination** | Multi-agent coordination protocols |
| **kb-automation** | Knowledge base automation |
| **observability** | OpenTelemetry integration |
| **integrations** | External service integrations |
| **documentation** | Auto-documentation generation |
| **shared** | Common utilities |

---

## Primitives Architecture

The core abstraction is the `WorkflowPrimitive`:

```python
class WorkflowPrimitive[I, O](ABC):
    """Base class for all workflow primitives."""

    @abstractmethod
    async def execute(self, input: I, context: Context) -> O:
        """Execute the primitive."""
        ...
```

**Categories:**
- **Core**: Composition (Sequential, Parallel, Conditional, Router)
- **Recovery**: Resilience (Retry, Fallback, Timeout, CircuitBreaker)
- **Adaptive**: Self-tuning (AdaptiveRetry, AdaptiveCache, etc.)
- **Performance**: Optimization (Cache, Memory)
- **Observability**: Monitoring (Instrumented, Observable)

See: [[TTA.dev/Primitives]] for full index.

---

## Knowledge Architecture

```
┌────────────────┐     sync     ┌────────────────┐
│    TTA.dev     │─────────────►│   TTA-notes    │
│    pages/      │              │    pages/      │
└───────┬────────┘              └────────────────┘
        │ links
        ▼
┌────────────────┐     sync     ┌────────────────┐
│    TTA.dev     │─────────────►│   TTA-notes    │
│   journals/    │              │   journals/    │
└───────┬────────┘              └────────────────┘
        ▲ consolidate
        │
┌───────┴────────┐
│ logseq/journals│  (per-worktree, gitignored)
│  agent notes   │
└────────────────┘
```

---

## Multi-Agent Coordination

### Worktree Isolation

Each agent has its own worktree with isolated:
- Working directory
- Git index
- Local journals (`logseq/journals/`)

### Shared Resources

All agents share:
- `pages/` (Canonical KB)
- `journals/` (Consolidated thinking)
- `platform/` (Code packages)

### Sync Mechanisms

| Script | Purpose |
|--------|---------|
| `scripts/sync_journals.py` | Consolidate worktree journals |
| `scripts/generate_kb_pages.py` | Generate KB from code |

---

## Documentation Index

Detailed docs in `docs/`:

| Category | Content |
|----------|---------|
| `architecture/` | System design, primitives patterns |
| `guides/` | How-to guides, tutorials |
| `integration/` | Integration documentation |
| `runbooks/` | Operational procedures |
| `quickstart/` | Getting started guides |

---

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Agent Workflow]] - How agents work
- [[TTA.dev/KB Structure]] - Knowledge organization
- `docs/architecture/MONOREPO_STRUCTURE.md` - Full structure details

---

**Tags:** #architecture #reference #system-design
