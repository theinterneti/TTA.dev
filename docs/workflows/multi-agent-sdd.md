# Multi-Agent SDD Workflow via L0 Control Plane

This document is the **authoritative runbook** for running a Spec-Driven Development (SDD) cycle
through the TTA.dev L0 control plane. Every command is copy-pasteable. Run them in order.

---

## Overview

The workflow has **four steps**, each owned by a specialised agent:

| Step | Agent | Gate |
|------|-------|------|
| 0 | architect | APPROVAL (human) |
| 1 | backend-engineer | APPROVAL (human) |
| 2 | testing-specialist | APPROVAL (human) |
| 3 | devops-engineer | APPROVAL (human) |

---

## Prerequisites

```bash
uv sync --all-extras          # install deps
uv run tta control --help     # verify CLI works
```

---

## Step 1 — Start the workflow

```bash
uv run tta control workflow start \
  --name "sdd-example" \
  --goal "Add CachePrimitive metrics integration" \
  --agents "architect,backend-engineer,testing-specialist,devops-engineer"
```

**Expected output** (IDs will differ):

```
Workflow started.
  task_id:  task_<hex>
  run_id:   run_<hex>
  agents:   architect → backend-engineer → testing-specialist → devops-engineer
  lease:    expires <timestamp>
```

Save `task_id` for every subsequent command:

```bash
TASK_ID=task_<hex>   # replace with your actual ID
```

### Alternatively — attach to an existing task

If you already created a task with `tta control task create`, pass `--task-id` to
skip creating a duplicate:

```bash
uv run tta control workflow start \
  --name "sdd-example" \
  --goal "Add CachePrimitive metrics integration" \
  --agents "architect,backend-engineer,testing-specialist,devops-engineer" \
  --task-id $EXISTING_TASK_ID
```

---

## Step 2 — Inspect the workflow

```bash
uv run tta control workflow status --task-id $TASK_ID
uv run tta control workflow explain --task-id $TASK_ID
```

`explain` returns `"No active step"` until you activate step 0. That is expected.

---

## Step 3 — Architect phase (step 0)

### 3a. Activate the step

```bash
uv run tta control workflow step start $TASK_ID 0
```

Now `explain` shows the active step.

### 3b. Agent does its work

The architect agent reads the goal, produces a spec, and marks the step done:

```bash
uv run tta control workflow step done $TASK_ID 0 \
  --result "spec written at docs/specs/cache-metrics.md" \
  --confidence 0.95
```

### 3c. Human reviews and approves the gate

```bash
# List pending gates
uv run tta control task show --task-id $TASK_ID

# Approve the gate (gate ID printed in `task show`)
GATE_ID=gate_<hex>
uv run tta control workflow step gate $TASK_ID 0 \
  --gate-id $GATE_ID \
  --decision continue \
  --summary "Spec looks good, proceed"
```

---

## Step 4 — Backend-engineer phase (step 1)

```bash
uv run tta control workflow step start $TASK_ID 1
# ... agent implements ...
uv run tta control workflow step done $TASK_ID 1 \
  --result "CachePrimitive metrics wired up" \
  --confidence 0.9
uv run tta control workflow step gate $TASK_ID 1 \
  --gate-id $GATE_ID_STEP1 \
  --decision continue \
  --summary "Implementation approved"
```

---

## Step 5 — Testing-specialist phase (step 2)

```bash
uv run tta control workflow step start $TASK_ID 2
# ... agent writes / runs tests ...
uv run tta control workflow step done $TASK_ID 2 \
  --result "100% coverage, all tests pass" \
  --confidence 0.99
uv run tta control workflow step gate $TASK_ID 2 \
  --gate-id $GATE_ID_STEP2 \
  --decision continue \
  --summary "Tests pass"
```

---

## Step 6 — DevOps phase (step 3)

```bash
uv run tta control workflow step start $TASK_ID 3
# ... agent prepares CI/CD, docs, release notes ...
uv run tta control workflow step done $TASK_ID 3 \
  --result "CI green, changelog updated" \
  --confidence 0.97
uv run tta control workflow step gate $TASK_ID 3 \
  --gate-id $GATE_ID_STEP3 \
  --decision continue \
  --summary "Ready to merge"
```

---

## Step 7 — Complete the workflow

When all gates are approved and all steps are done:

```bash
uv run tta control task decide-gate \
  --task-id $TASK_ID \
  --gate-id <final-gate-id> \
  --decision approved \
  --summary "Workflow complete"
```

---

## Abort at any step

To fail a step and halt the workflow:

```bash
uv run tta control workflow step fail $TASK_ID <step_index> \
  --error "Spec review blocked — needs clarification from product"
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `"No active step"` from explain | Step not started yet | Run `workflow step start $TASK_ID <index>` |
| Gate not found | Wrong gate ID | Run `task show` to list gate IDs |
| Lease expired | >5 min since `workflow start` | Re-run `task claim` on the task to refresh lease |
| `"Workflow already attached"` | `--task-id` used on task that already has workflow | Use a fresh task or omit `--task-id` |

---

## Related

- `ttadev/control_plane/service.py` — `start_tracked_workflow`, `attach_workflow_to_task`
- `ttadev/cli/control.py` — all `tta control` subcommands
- `tests/integration/test_sdd_workflow.py` — automated end-to-end test for this workflow
- `AGENTS.md` — L0 continuation directives
