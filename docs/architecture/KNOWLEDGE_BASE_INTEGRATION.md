# Knowledge Base Integration Architecture

This document is retained as a historical pointer, but its original Logseq-centric design is
superseded.

## Current Direction

TTA.dev no longer treats Logseq as the active knowledge base architecture for agent workflows.

The current split is:

- **Hindsight** for cross-session agent memory and retrieval
- **CodeGraphContext** for code structure, symbol relationships, and repository context
- **`KnowledgeBasePrimitive`** as a backend-neutral abstraction that degrades safely when no
  knowledge backend is available

## What Changed

The earlier version of this document described a design based on:

- Logseq pages and journals as the primary knowledge store
- `mcp-logseq` as the active integration layer
- `KnowledgeBasePrimitive(logseq_available=...)` as the public API shape

That is no longer the current architecture.

The active runtime surface now uses backend-neutral terminology:

- `KnowledgeBasePrimitive(backend_available=...)`
- `KBResult.source` values of `backend` or `fallback`

## Canonical References

Use these documents instead of the original Logseq design:

- [`docs/guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md`](../guides/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md)
- [`docs/specs/phase3-guided-workflow-system.md`](../specs/phase3-guided-workflow-system.md)
- [`docs/specs/phase3-technical-plan.md`](../specs/phase3-technical-plan.md)

## Migration Guidance

If you find older docs or examples that still refer to Logseq knowledge-base integration:

- treat them as historical, not authoritative
- prefer Hindsight for persistent agent memory
- prefer CodeGraphContext for repository/code understanding
- update examples to use backend-neutral `KnowledgeBasePrimitive` terminology

## Status

- Original Logseq knowledge-base integration design: retired
- Hindsight + CodeGraphContext direction: active
- Backend-neutral knowledge-base abstraction: active
