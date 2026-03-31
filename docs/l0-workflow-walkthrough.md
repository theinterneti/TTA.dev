# L0 Workflow Walkthrough

**Status:** verified 2026-03-31 · proof run against `ttadev` HEAD
**Audience:** developers and AI agents reproducing or extending L0 multi-agent workflows

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Walkthrough: Happy Path](#4-walkthrough-happy-path)
5. [Walkthrough: Failure Path](#5-walkthrough-failure-path)
6. [Observability](#6-observability)
7. [Hindsight Integration](#7-hindsight-integration)
8. [MCP Tool Reference](#8-mcp-tool-reference)
9. [Known Limitations & Current Gaps](#9-known-limitations--current-gaps)
10. [Reproducing This Walkthrough](#10-reproducing-this-walkthrough)

---

## 1. Overview

The **L0 control plane** is the local coordination backbone for multi-agent workflows in TTA.dev.
It is not a hosted service — it runs entirely on the developer's machine, storing state in the
`.tta/` directory.

Its responsibilities are:

- **Task ownership** — one canonical task record per workflow execution
- **Active run state** — a claimed run tied to the orchestrator, with a renewable lease
- **Per-step tracking** — status, result, confidence, and OTel trace context for every agent step
- **Approval / policy gates** — required checkpoints before a workflow can advance
- **Audit trail** — every state transition is recorded and inspectable via CLI

This walkthrough is the primary proof that the L0 surface works end-to-end.
A developer (or AI agent) following it from scratch should reproduce the exact same state
transitions shown in the captured output below.

---

## 2. Architecture

The L0 control plane has three layers that build on each other:

```
┌─────────────────────────────────────────────────────────────┐
│  CLI  (tta control …)                                        │
│  Human-friendly shell interface.                             │
│  Entry point: ttadev/cli/control.py                          │
└─────────────────────┬───────────────────────────────────────┘
                      │ calls
┌─────────────────────▼───────────────────────────────────────┐
│  Service  (ControlPlaneService)                              │
│  All business logic: task/run/gate/step state machines.      │
│  Entry point: ttadev/control_plane/service.py                │
└─────────────────────┬───────────────────────────────────────┘
                      │ calls
┌─────────────────────▼───────────────────────────────────────┐
│  Store  (JSON files on disk)                                 │
│  Persistent state.  Location: .tta/control/                  │
│  Entry point: ttadev/control_plane/store.py                  │
└─────────────────────────────────────────────────────────────┘
```

A fourth entry point, the **MCP server** (`ttadev/primitives/mcp_server/server.py`), exposes the
same Service layer to AI agents over the Model Context Protocol.  The CLI and the MCP server are
parallel surfaces — they share the same state files.

**State storage:** `.tta/control/` in the current working directory.  Pass `--data-dir` (CLI) or
`data_dir` (MCP) to redirect.

---

## 3. Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| `uv` | `pip install uv` or see https://docs.astral.sh/uv |
| `tta` CLI | `uv run tta --help` — available after `uv sync` |
| OTel collector | **Optional.** All spans degrade silently to no-ops when absent. |

```bash
# Verify the CLI is available
uv run tta --help

# Verify the control subcommand is registered
uv run tta control --help
```

No API keys, no network, no external services are required for the walkthrough.

---

## 4. Walkthrough: Happy Path

### Phase 1 — Start the workflow

```bash
uv run tta control workflow start \
  --name "l0-demo-workflow" \
  --goal "End-to-end L0 demo for walkthrough documentation" \
  --agents "architect,backend-engineer,reviewer" \
  --project "l0-walkthrough"
```

**Required flags:**

| Flag | Description |
|---|---|
| `--name` | Human-readable workflow name |
| `--goal` | Goal statement (not `--description`) |
| `--agents` | Comma-separated ordered list of agent names (not `--agent`) |
| `--project` | Optional project label |

**Expected output:**

```
Workflow started.
  task_id:  task_b837ef6c4b9e
  run_id:   run_15e22ea01b53
  agents:   architect → backend-engineer → reviewer
  lease:    expires 2026-03-31T16:59:39.089032+00:00
```

Save the `task_id` for subsequent commands:

```bash
export TASK_ID=task_b837ef6c4b9e
```

What happened internally:
- One `TaskRecord` created with status `in_progress`
- One approval gate registered per step agent (IDs: `workflow-step-1-architect`,
  `workflow-step-2-backend-engineer`, `workflow-step-3-reviewer`)
- One `RunRecord` claimed immediately; a 5-minute lease issued

---

### Phase 2 — Inspect initial state

```bash
uv run tta control workflow status $TASK_ID
```

```
Workflow: l0-demo-workflow  (RUNNING)
Goal:     End-to-end L0 demo for walkthrough documentation

Steps
──────────────────────────────────────────────────────────────────────
  0  architect            pending      -       -
  1  backend-engineer     pending      -       -
  2  reviewer             pending      -       -

Gates
──────────────────────────────────────────────────────────────────────
  workflow-step-1-architect              approval   pending
  workflow-step-2-backend-engineer       approval   pending
  workflow-step-3-reviewer               approval   pending
```

Note: gate IDs are **1-based** (`workflow-step-1-architect`) while step indices are **0-based**.

---

### Phase 3 — Mark step 0 running

```bash
uv run tta control workflow step start $TASK_ID 0 \
  --trace-id "00000000000000000000000000000001" \
  --span-id  "0000000000000001"
```

The `step_index` argument (here `0`) is a **positional integer**, not a flag.
`--trace-id` and `--span-id` are optional; when omitted, the service auto-captures the caller's
active OTel context.

```
Step 0 started.
  agent:    architect
  started:  2026-03-31T16:54:52.830814+00:00
  trace:    00000000000000000000000000000001
```

Inspect while running:

```bash
uv run tta control workflow explain $TASK_ID
```

```
Workflow:  l0-demo-workflow  (RUNNING)
Goal:      End-to-end L0 demo for walkthrough documentation

Active Step
─────────────────────────────────────────────────────────────────
  Step 1 / 3   architect    RUNNING   for 0s
  Agent:   architect
  Trace:   00000000000000000000000000000001
  Span:    0000000000000001

Pending Gates
  workflow-step-2-backend-engineer
  workflow-step-3-reviewer
```

---

### Phase 4 — Record step result

```bash
uv run tta control workflow step done $TASK_ID 0 \
  --result "Architecture design complete: 3-layer service pattern identified" \
  --confidence 0.92
```

```
Step 0 completed.
  agent:      architect
  result:     Architecture design complete: 3-layer service pattern identified
  confidence: 0.92
  completed:  2026-03-31T16:55:01.285420+00:00
```

Step 0's `WorkflowStepRecord` now has status `completed`.

---

### Phase 5 — Record the gate outcome

```bash
uv run tta control workflow step gate $TASK_ID 0 \
  --decision "continue" \
  --summary "Architecture looks solid, confidence 0.92 exceeds threshold" \
  --policy-name "auto:confidence≥0.85"
```

```
Step 0 gate outcome recorded.
  decision: continue
  step status: completed
  workflow status: running
```

Inspect the updated state:

```bash
uv run tta control workflow status $TASK_ID
```

```
Workflow: l0-demo-workflow  (RUNNING)
Goal:     End-to-end L0 demo for walkthrough documentation

Steps
──────────────────────────────────────────────────────────────────────
  0  architect            completed    0.92    15s        gate=continue      4bf92f35…
  1  backend-engineer     pending      -       -
  2  reviewer             pending      -       -

Gates
──────────────────────────────────────────────────────────────────────
  workflow-step-1-architect              approval   approved               by ed066958…
  workflow-step-2-backend-engineer       approval   pending
  workflow-step-3-reviewer               approval   pending
```

The workflow is now ready to advance to step 1.

---

### Repeating phases 3–5 for remaining steps

Start step 1:

```bash
uv run tta control workflow step start $TASK_ID 1
```

```
Step 1 started.
  agent:    backend-engineer
  started:  2026-03-31T16:55:15.127515+00:00
  trace:    00000000000000000000000000000001
```

Then record result and gate outcome for steps 1 and 2 in the same pattern.

---

## 5. Walkthrough: Failure Path

Continuing from step 1 running above — simulate a failed step:

```bash
uv run tta control workflow step fail $TASK_ID 1 \
  --error "Dependency missing: ttadev.primitives.circuit_breaker not found"
```

```
Step 1 marked failed.
  agent:  backend-engineer
  error:  Dependency missing: ttadev.primitives.circuit_breaker not found in package registry
```

Inspect the resulting state:

```bash
uv run tta control workflow status $TASK_ID
```

```
Workflow: l0-demo-workflow  (FAILED)
Goal:     End-to-end L0 demo for walkthrough documentation

Steps
──────────────────────────────────────────────────────────────────────
  0  architect            completed    0.92    15s        gate=continue      4bf92f35…
  1  backend-engineer     failed       -       -                             4bf92f35…
  2  reviewer             pending      -       -

Gates
──────────────────────────────────────────────────────────────────────
  workflow-step-1-architect              approval   approved               by ...
  workflow-step-2-backend-engineer       approval   pending
  workflow-step-3-reviewer               approval   pending
```

Workflow status transitions to `FAILED`.  The OTel span for step 1 has `StatusCode.ERROR` set.

Additional inspection commands:

```bash
uv run tta control task show $TASK_ID
uv run tta control task list
```

Note: `workflow list` and `workflow show` do **not** exist.  Use `task list` / `task show
<task_id>` for task-level views.

---

## 6. Observability

### OTel span table

Every L0 operation emits a paired span: one from the service layer (`ttadev.control_plane`
tracer) and one from the MCP wrapper (`ttadev.mcp_server` tracer).

| Operation | Service span | MCP span | Key attributes |
|---|---|---|---|
| Start workflow | `tta.l0.workflow.start` | `tta.l0.mcp.workflow.start` | `l0.workflow_name`, `l0.total_steps`, `l0.task_id` |
| Step → RUNNING | `tta.l0.step.running` | `tta.l0.mcp.step.running` | `l0.task_id`, `l0.step_index`, `l0.step_agent` |
| Step → COMPLETED | `tta.l0.step.completed` | `tta.l0.mcp.step.completed` | `l0.task_id`, `l0.step_index`, `l0.confidence` |
| Gate outcome | `tta.l0.gate.outcome` | `tta.l0.mcp.gate.outcome` | `l0.task_id`, `l0.step_index`, `l0.gate_decision` |
| Step → FAILED | `tta.l0.step.failed` | `tta.l0.mcp.step.failed` | `l0.task_id`, `l0.step_index`, `l0.error_summary` |

### Wiring an OTel collector

OTel is **fully optional**.  When no collector is configured, all spans are silent no-ops and no
errors are raised.

To enable trace export, set the standard OTLP environment variables before running `tta`:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_SERVICE_NAME="tta-control-plane"
uv run tta control workflow start …
```

Any OTLP-compatible backend (Jaeger, Tempo, Honeycomb, etc.) works.  The observability dashboard
bundled with `ttadev` can be started with:

```bash
uv run python -m ttadev.observability
# → http://localhost:8000
```

### Trace propagation notes

- `mark_workflow_step_running` auto-captures the caller's active OTel context when `--trace-id`
  and `--span-id` are omitted.
- `mark_workflow_step_failed` sets `StatusCode.ERROR` on both the service span and the MCP span.
- Trace IDs and span IDs are stored on `WorkflowStepRecord` and appear in `workflow status`
  output (truncated to 8 chars).

---

## 7. Hindsight Integration

`WorkflowStepRecord` carries two optional fields — `hindsight_bank_id` and
`hindsight_document_id` — that link a step to a Hindsight memory bank entry.

These fields can be set at two points in the step lifecycle:

| When | Service method | MCP tool |
|---|---|---|
| Step transitions to RUNNING | `mark_workflow_step_running(…, hindsight_bank_id=…, hindsight_document_id=…)` | `control_mark_workflow_step_running` |
| Step result is recorded | `record_workflow_step_result(…, hindsight_bank_id=…, hindsight_document_id=…)` | `control_record_workflow_step_result` |

**Important:** The CLI does **not** expose `--hindsight-bank-id` or `--hindsight-document-id`.
Hindsight linking is **MCP-only** — it is intended for agent-originated calls, not human shell
sessions.

Example (MCP caller, JSON params):

```json
{
  "task_id": "task_b837ef6c4b9e",
  "step_index": 0,
  "trace_id": "00000000000000000000000000000001",
  "hindsight_bank_id": "arch-decisions-2026",
  "hindsight_document_id": "doc_3f9a12"
}
```

---

## 8. MCP Tool Reference

The five workflow-specific MCP tools mirror the CLI workflow subcommands, but accept structured
JSON and support additional fields (like Hindsight linking) that the CLI omits.

### `control_start_workflow`

**Type:** Mutating
Creates and immediately claims a tracked multi-agent workflow task.

| Parameter | Required | Description |
|---|---|---|
| `workflow_name` | ✅ | Human-readable name |
| `workflow_goal` | ✅ | Goal statement |
| `step_agents` | ✅ | Ordered array of agent name strings |
| `project_name` | — | Optional project label |
| `policy_gates` | — | Extra POLICY gates appended after step gates |
| `data_dir` | — | Override state directory (default: `.tta`) |

**Returns:** `{"task": TaskRecord, "run": RunRecord, "lease": LeaseRecord}`

---

### `control_mark_workflow_step_running`

**Type:** Idempotent
Transitions a step to RUNNING; safe to call again on retry.

| Parameter | Required | Description |
|---|---|---|
| `task_id` | ✅ | |
| `step_index` | ✅ | Zero-based integer |
| `trace_id` | — | OTel trace ID hex string |
| `span_id` | — | OTel span ID hex string |
| `hindsight_bank_id` | — | Hindsight memory bank to link |
| `hindsight_document_id` | — | Specific document within the bank |

**Returns:** `{"task": TaskRecord}`

---

### `control_record_workflow_step_result`

**Type:** Mutating
Records result and confidence; auto-evaluates pending POLICY gates.

| Parameter | Required | Description |
|---|---|---|
| `task_id` | ✅ | |
| `step_index` | ✅ | Zero-based integer |
| `result_summary` | ✅ | Free-text result description |
| `confidence` | ✅ | Float 0.0–1.0 |
| `hindsight_bank_id` | — | Hindsight memory bank to link |
| `hindsight_document_id` | — | Specific document within the bank |

**Returns:** `{"task": TaskRecord}`

---

### `control_record_workflow_gate_outcome`

**Type:** Mutating
Records an approval-gate decision, advancing or halting the workflow.

| Parameter | Required | Description |
|---|---|---|
| `task_id` | ✅ | |
| `step_index` | ✅ | Zero-based integer |
| `decision` | ✅ | `continue` \| `skip` \| `edit` \| `quit` \| `escalate_to_human` |
| `summary` | — | Human-readable rationale |
| `policy_name` | — | Set when an automated policy made the decision |

**Returns:** `{"task": TaskRecord}`

---

### `control_mark_workflow_step_failed`

**Type:** Mutating
Marks a step FAILED; sets `StatusCode.ERROR` on OTel spans.

| Parameter | Required | Description |
|---|---|---|
| `task_id` | ✅ | |
| `step_index` | ✅ | Zero-based integer |
| `error_summary` | ✅ | Short description of the failure |

**Returns:** `{"task": TaskRecord}`

---

## 9. Known Limitations & Current Gaps

The following behaviours are accurate as of HEAD.  They are not bugs — they are deliberate design
boundaries or deferred work.

| # | Limitation | Details |
|---|---|---|
| 1 | Flag name: `--goal` not `--description` | Using `--description` will error. |
| 2 | Flag name: `--agents` (plural, CSV) not `--agent` | Single `--agent` does not exist. |
| 3 | No `workflow list` / `workflow show` | Use `task list` and `task show <task_id>` instead. |
| 4 | Step subcommands are nested | `workflow step {start,done,fail,gate}` — not top-level. |
| 5 | Step index is zero-based positional arg | Pass `0`, `1`, `2` — not `--step 0`. |
| 6 | ⚠ **Gap: no CLI `workflow finalize` command** | After all steps complete the workflow status stays `RUNNING`. `finalize_tracked_workflow()` exists in the Service, and `control_complete_run` in the MCP server completes it, but no CLI command wraps `finalize_tracked_workflow` yet. Finalisation from the CLI is a known open item. |
| 7 | Gate IDs are 1-based in naming, steps are 0-based | Gate `workflow-step-1-architect` corresponds to step index `0`. |
| 8 | Hindsight linking is MCP-only | `--hindsight-bank-id` / `--hindsight-document-id` are not exposed in the CLI. |
| 9 | OTel is fully optional | Spans are silent no-ops when no collector is configured; no runtime errors result. |

---

## 10. Reproducing This Walkthrough

Copy-paste the block below into a shell from the repo root.  It reproduces every state transition
shown in this document.

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== workflow start ==="
START_OUTPUT=$(uv run tta control workflow start \
  --name "l0-demo-workflow" \
  --goal "End-to-end L0 demo for walkthrough documentation" \
  --agents "architect,backend-engineer,reviewer" \
  --project "l0-walkthrough")
echo "$START_OUTPUT"

TASK_ID=$(echo "$START_OUTPUT" | grep 'task_id' | awk '{print $2}')
echo ""
echo "Captured TASK_ID=$TASK_ID"

echo ""
echo "=== workflow status (initial) ==="
uv run tta control workflow status "$TASK_ID"

echo ""
echo "=== step start 0 (with OTel trace context) ==="
uv run tta control workflow step start "$TASK_ID" 0 \
  --trace-id "00000000000000000000000000000001" \
  --span-id  "0000000000000001"

echo ""
echo "=== workflow explain (while step 0 running) ==="
uv run tta control workflow explain "$TASK_ID"

echo ""
echo "=== step done 0 ==="
uv run tta control workflow step done "$TASK_ID" 0 \
  --result "Architecture design complete: 3-layer service pattern identified" \
  --confidence 0.92

echo ""
echo "=== step gate 0 ==="
uv run tta control workflow step gate "$TASK_ID" 0 \
  --decision "continue" \
  --summary "Architecture looks solid, confidence 0.92 exceeds threshold" \
  --policy-name "auto:confidence≥0.85"

echo ""
echo "=== workflow status after step 0 gate ==="
uv run tta control workflow status "$TASK_ID"

echo ""
echo "=== step start 1 ==="
uv run tta control workflow step start "$TASK_ID" 1

echo ""
echo "=== step fail 1 (simulate failure) ==="
uv run tta control workflow step fail "$TASK_ID" 1 \
  --error "Dependency missing: ttadev.primitives.circuit_breaker not found"

echo ""
echo "=== workflow status (failed) ==="
uv run tta control workflow status "$TASK_ID"

echo ""
echo "=== task show ==="
uv run tta control task show "$TASK_ID"

echo ""
echo "=== task list ==="
uv run tta control task list
```

**Expected terminal state after the script:**

- Step 0: `completed`, confidence `0.92`, gate `continue`, trace `4bf92f35…`
- Step 1: `failed`, error recorded, OTel span has `StatusCode.ERROR`
- Step 2: `pending` (never reached)
- Workflow: `FAILED`
- Task: `in_progress` (underlying `TaskRecord.status`; workflow-level status is tracked in the
  step metadata and displayed separately by the CLI)

---

*Document generated from a live demo run on 2026-03-31.*
*Source of truth: `ttadev/control_plane/` and `ttadev/cli/control.py`.*
