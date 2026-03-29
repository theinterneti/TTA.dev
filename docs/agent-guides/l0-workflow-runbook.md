# L0 Multi-Agent Workflow Runbook

A step-by-step guide to running a documented, repeatable multi-agent workflow
through the TTA.dev L0 control plane.  All steps work against the local `.tta`
state directory and require no external services.

---

## Overview

The L0 surface exposes workflow coordination through two interfaces:

| Interface | Who uses it | Purpose |
|-----------|------------|---------|
| `tta control workflow start` | Developer / orchestrator CLI | Start a workflow, inspect state |
| MCP tools (`control_*`) | Coding agents (Claude, Copilot, Cline) | Claim tasks, drive steps, record results |

A workflow proceeds through these phases:

```
start_workflow → claim_task → mark_step_running → record_step_result
             → (policy gate evaluates) → record_gate_outcome
             → release_run → next agent claims → ... → complete_run
```

---

## Prerequisites

```bash
# The .tta directory is created automatically on first use.
# All commands below use a local .tta directory in the project root.
```

---

## Step 1 — Start the workflow (CLI)

```bash
tta control workflow start \
  --name "feature-x" \
  --goal "implement and review feature X" \
  --agents "backend-engineer,reviewer" \
  --policy-gate "id=quality,label=Quality gate,policy=auto:confidence>=0.8"
```

Expected output:

```
Workflow started.
  task_id:  task_abc123
  run_id:   run_xyz456
  agents:   backend-engineer → reviewer
  lease:    expires 2026-03-27T20:05:00+00:00
```

What this creates:

- One top-level **task** with `workflow` tracking (2 steps)
- Two per-step **APPROVAL gates** (one per agent, `required=false`)
- One **POLICY gate** (`id=quality`, `required=true`, auto-evaluates on result)
- An initial **run** + **lease** for the starting agent

---

## Step 2 — Agent 1 marks step 0 running (MCP)

Agent 1 (`backend-engineer`) was auto-claimed during `start_workflow`.  It stamps
its OTel trace context and marks the step as in-progress:

```json
// Tool: control_mark_workflow_step_running
{
  "task_id": "task_abc123",
  "step_index": 0,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "data_dir": ".tta"
}
```

State after this call:

- `workflow.steps[0].status = RUNNING`
- `workflow.steps[0].trace_id = "4bf92f…"`  ← OTel attribution stored

---

## Step 3 — Agent 1 records its result (MCP)

After completing the work, agent 1 records a result summary and confidence score:

```json
// Tool: control_record_workflow_step_result
{
  "task_id": "task_abc123",
  "step_index": 0,
  "result_summary": "Implemented feature X with full test coverage.",
  "confidence": 0.9,
  "data_dir": ".tta"
}
```

**Policy gate auto-evaluation fires here.**  Because `confidence (0.9) ≥ 0.8`:

- `task.gates["quality"].status = APPROVED`
- `task.gates["quality"].decided_by = "policy:auto:confidence>=0.8"`

If confidence were below 0.8, the gate stays `PENDING` and requires a human
decision (see [Low-confidence path](#low-confidence-path) below).

---

## Step 4 — Agent 1 records gate outcome and releases (MCP)

Agent 1 signals that it is done and the workflow should continue:

```json
// Tool: control_record_workflow_gate_outcome
{
  "task_id": "task_abc123",
  "step_index": 0,
  "decision": "continue",
  "summary": "Policy gate approved; handing off to reviewer.",
  "data_dir": ".tta"
}
```

State after this call:

- `workflow.steps[0].gate_decision = CONTINUE`
- `workflow.steps[0].status = COMPLETED`

Then agent 1 releases its run (does NOT call `complete_run` — that would mark
the task finished before reviewer has worked):

```json
// Tool: control_release_run
{
  "run_id": "run_xyz456",
  "reason": "step 0 done, handing off to reviewer",
  "data_dir": ".tta"
}
```

---

## Step 5 — Agent 2 claims and drives step 1 (MCP)

Agent 2 (`reviewer`) claims the now-available task:

```json
// Tool: control_claim_task
{
  "task_id": "task_abc123",
  "trace_id": "99887766554433221100ffeeddccbbaa",
  "span_id": "8877665544332211",
  "data_dir": ".tta"
}
```

Then marks step 1 running, records result, and completes:

```json
// control_mark_workflow_step_running
{ "task_id": "task_abc123", "step_index": 1,
  "trace_id": "99887766…", "span_id": "88776655…", "data_dir": ".tta" }

// control_record_workflow_step_result
{ "task_id": "task_abc123", "step_index": 1,
  "result_summary": "Review passed. No issues found.", "confidence": 0.95,
  "data_dir": ".tta" }

// control_complete_run
{ "run_id": "run_def789", "summary": "review done", "data_dir": ".tta" }
```

`complete_run` marks the top-level task as `COMPLETED`.

---

## Step 6 — Inspect results (CLI)

```bash
tta control task show task_abc123
tta control run show run_xyz456
tta control run show run_def789
```

`task show` output includes:

```
Workflow: feature-x (2 steps) — RUNNING
  step 0  backend-engineer  COMPLETED  gate=continue  trace=4bf92f35…
  step 1  reviewer          COMPLETED  trace=99887766…
Gates:
  workflow-step-1-backend-engineer  APPROVAL  APPROVED
  workflow-step-2-reviewer          APPROVAL  PENDING
  quality                           POLICY    APPROVED  by policy:auto:confidence>=0.8
```

---

## Low-confidence path

If agent 1 records a low confidence score (`0.5`), the policy gate stays `PENDING`:

```json
// control_record_workflow_step_result with confidence=0.5
// → task.gates["quality"].status remains PENDING
```

A human (or orchestrator) must then decide:

```json
// Tool: control_record_workflow_gate_outcome
{
  "task_id": "task_abc123",
  "step_index": 0,
  "decision": "quit",
  "summary": "Confidence too low; stopping workflow for rework.",
  "data_dir": ".tta"
}
```

After this:

- `workflow.steps[0].gate_decision = QUIT`
- `workflow.steps[0].status = QUIT`
- `workflow.status = QUIT`
- Step 1 remains `PENDING` (never started)

---

## Escalation Path (ESCALATE_TO_HUMAN)

When an agent determines that a workflow step needs human review before
proceeding, it records `ESCALATE_TO_HUMAN` as the gate outcome:

```bash
# MCP tool call
control_record_workflow_gate_outcome(
    task_id="task_abc",
    step_index=0,
    decision="escalate_to_human",
    summary="Confidence 0.45 — below threshold for autonomous continuation",
)
```

This pauses the workflow (`status = ESCALATED`) without advancing to the next step.

The developer reviews the situation:
```bash
tta control workflow status <task_id>
tta control gate list <task_id>
```

To resume, approve the linked step gate:
```bash
tta control gate approve <task_id> <gate_id> --note "Reviewed — looks good"
```

The workflow returns to `RUNNING` and the agent can continue from where it paused.

**Known gap:** If a human rejects (rather than approves) the gate on an escalated
workflow, the workflow remains `ESCALATED`. There is no automated path to resolve
a rejected escalation — it requires manual intervention (direct store update or
task force-quit). This will be addressed in a future iteration.

---

## MCP ↔ CLI tool mapping

| Action | MCP Tool | CLI equivalent |
|--------|----------|----------------|
| Start workflow | `control_start_workflow` | `tta control workflow start` |
| Claim task | `control_claim_task` | _(no CLI claim — agents only)_ |
| Mark step running | `control_mark_workflow_step_running` | _(no CLI)_ |
| Record step result | `control_record_workflow_step_result` | _(no CLI)_ |
| Record gate outcome | `control_record_workflow_gate_outcome` | _(no CLI)_ |
| Mark step failed | `control_mark_workflow_step_failed` | _(no CLI)_ |
| Release run | `control_release_run` | _(no CLI)_ |
| Complete run | `control_complete_run` | _(no CLI)_ |
| Show task | `control_get_task` | `tta control task show <id>` |
| Show run | `control_get_run` | `tta control run show <id>` |
| List tasks | `control_list_tasks` | `tta control task list` |

---

## Known gaps (future work)

| Gap | Status | Impact |
|-----|--------|--------|
| Rejected escalation leaves workflow stuck in `ESCALATED` | Open (M4) | Workflow remains paused indefinitely; requires manual intervention (direct store update or force-quit) to recover |

**M3 Resolutions:**
- ✓ `ESCALATE_TO_HUMAN` gate outcome — now implemented
- ✓ Abandoned workflow detection — implemented via `expire_abandoned_workflows()`
- ✓ Orphaned step cleanup — implemented via `cleanup_orphaned_steps()`
- ✓ MCP tool specs — published at `docs/mcp-tool-specs.md`
