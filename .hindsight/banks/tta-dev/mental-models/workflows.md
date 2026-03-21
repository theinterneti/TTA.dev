---
category: mental-models
date: 2026-03-20
component: workflows
severity: high
tags: [mental-model, workflows, WorkflowOrchestrator, ApprovalGate, memory]
---
# Mental Model: Workflow System (Phase 3)

All files: `ttadev/workflows/`

## WorkflowDefinition (definition.py) — immutable frozen dataclass

`name`, `description`, `steps: list[WorkflowStep]`, `auto_approve: bool`,
`memory_config: MemoryConfig(flush_to_persistent, bank_id)`

WorkflowStep: `agent: str`, `gate: bool = True`, `input_transform: Callable | None`
WorkflowResult: `workflow_name`, `goal`, `steps`, `artifacts`, `memory_snapshot`,
`completed`, `total_confidence`

## WorkflowOrchestrator (orchestrator.py)

Extends `InstrumentedPrimitive[WorkflowGoal, WorkflowResult]` — composable with >> and |.
Input: `WorkflowGoal(goal: str, context: dict)`

Execution loop:
1. Attach WorkflowMemory to context.memory
2. For each step: build task → get agent from registry → execute → gate check
3. Gate decisions: CONTINUE / SKIP (skips next step too) / EDIT (re-run same step) / QUIT
4. Flush to PersistentMemory if memory_config.flush_to_persistent
total_confidence = avg confidence of non-skipped steps

## ApprovalGate (gate.py)

Human-in-the-loop checkpoint. `auto_approve=True` skips all prompts.
Non-TTY stdin auto-approves with log warning.
Keys: Enter=continue, s=skip, e=edit (re-runs step), q=quit, ?=full output.

## Memory layers (memory.py)

**WorkflowMemory** (Tier 1): in-context key/value. `set/get/append/snapshot`.
Lives on `context.memory`, cleared after run unless flushed.

**PersistentMemory** (Tier 2): Hindsight-backed. Graceful degradation if unavailable.
Uses `hindsight_client.Hindsight` if installed, else `_HttpHindsightShim`.
Methods: `retain(bank_id, content)`, `recall(bank_id, query)`, `reflect(bank_id, query)`.

## Prebuilt (prebuilt.py)

`feature_dev_workflow`: developer→qa→security→git→github, all gated, memory flushed.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
