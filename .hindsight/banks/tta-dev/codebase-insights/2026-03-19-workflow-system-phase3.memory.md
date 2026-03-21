---
category: codebase-insights
date: 2026-03-19
component: workflows
severity: high
tags: [workflows, phase3, WorkflowOrchestrator, ApprovalGate, WorkflowMemory, PersistentMemory]
related_memories: []
---
# Workflow System — Phase 3 (Fully Implemented)

All files in `ttadev/workflows/`.

## WorkflowDefinition (definition.py) — immutable frozen dataclass

- `name`, `description`, `steps: list[WorkflowStep]`
- `auto_approve: bool` — skip human approval gates
- `memory_config: MemoryConfig(flush_to_persistent, bank_id)`
- `WorkflowStep`: `agent: str`, `gate: bool = True`, `input_transform: Callable | None`
- `WorkflowResult`: `workflow_name`, `goal`, `steps`, `artifacts`, `memory_snapshot`, `completed`, `total_confidence`

## WorkflowOrchestrator (orchestrator.py)

Extends `InstrumentedPrimitive[WorkflowGoal, WorkflowResult]` — fully composable with `>>` and `|`.

Input: `WorkflowGoal(goal: str, context: dict)`

Execution loop:
1. Attach `WorkflowMemory` to `context.memory`
2. For each step: build task (with input_transform or default) → get agent from registry → execute → gate check
3. Gate decisions: CONTINUE / SKIP (skip next step too) / EDIT (re-run same step with new instruction) / QUIT
4. Accumulate artifacts and memory
5. Flush to PersistentMemory if `memory_config.flush_to_persistent`

`total_confidence` = avg confidence of non-skipped steps.

## ApprovalGate (gate.py)

Human-in-the-loop checkpoint. `auto_approve=True` bypasses all prompts.
Non-TTY stdin auto-approves with log warning.
Shows step index, confidence %, quality gate status, 500-char response preview.

## Memory (memory.py)

**WorkflowMemory** (Tier 1 — in-context):
- `set(key, value)`, `get(key)`, `append(key, value)`, `snapshot() -> dict`
- Lives on `WorkflowContext.memory`, cleared after run unless flushed

**PersistentMemory** (Tier 2 — Hindsight-backed):
- Graceful degradation: warns once and no-ops if Hindsight unavailable
- Uses `hindsight_client.Hindsight` if installed, else `_HttpHindsightShim` (raw HTTP)
- `retain(bank_id, content)`, `recall(bank_id, query)`, `reflect(bank_id, query)`

## Prebuilt Workflow (prebuilt.py)

`feature_dev_workflow`: developer → qa → security → git → github
All steps gated, memory flushed to persistent after completion.

---

**Created:** 2026-03-19
**Last Updated:** 2026-03-19
**Verified:** [x] Yes
