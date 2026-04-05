# Task Protocol Reference

## Overview

The L0 task protocol defines how coding agents claim work, execute it with leases,
and return results with governance gates. All state is JSON-backed via `ttadev/control_plane/`.

## Key concepts

| Concept | Description |
|---|---|
| **Task** | A unit of work with a goal, assigned agent(s), and policy gates |
| **Run** | A single attempt to execute a task by one agent |
| **Lease** | A time-bounded claim on a task — expires if agent crashes |
| **Gate** | A policy evaluation checkpoint between workflow steps |

## Full task lifecycle

```
create_task(name, goal, agents, policy_gates)
  → task enters PENDING state

claim_task(agent_id)
  → task enters RUNNING state, agent holds a lease
  → lease TTL starts (default: 300 s)

mark_step_running(run_id, step_id)
  → signals step has started (for observability)

record_step_result(run_id, step_id, result, status)
  → records outcome: SUCCESS | FAILURE | SKIPPED

record_gate_outcome(run_id, gate_id, outcome, confidence)
  → policy evaluation: APPROVED | REJECTED | ESCALATED
  → ESCALATED → task enters WAITING_APPROVAL state

release_run(run_id, status)
  → lease released, run marked COMPLETED or FAILED

complete_task(task_id)
  → task enters COMPLETED state
```

## State machine

```
PENDING
  │ claim_task()
  ▼
RUNNING ──────────── gate ESCALATED ──▶ WAITING_APPROVAL
  │                                           │
  │ release_run(COMPLETED)         human approval
  ▼                                           │
COMPLETED                         release_run(COMPLETED)
                                              ▼
RUNNING → release_run(FAILED) → FAILED
```

## Lease TTL

If an agent crashes without releasing its lease, the task returns to PENDING
after the lease TTL. Another agent can then claim it. Default TTL: 300 s.

Agents must call `release_run()` even on failure to avoid TTL expiry delays.

## Policy gates

Gates are defined at workflow creation time:

```bash
tta control workflow start \
  --policy-gate "id=quality,label=Quality gate,policy=auto:confidence>=0.8"
```

Gate `policy` values:
- `auto:confidence>=N` — auto-approve if confidence ≥ N
- `human` — always escalate to human
- `auto` — auto-approve always (use for low-risk steps)

## CLI interface

```bash
# Create and start a workflow
tta control workflow start \
  --name "my-feature" \
  --goal "implement feature X" \
  --agents "developer,qa"

# Task management
tta control task list
tta control task show <task-id>

# Run management
tta control run list --task <task-id>
tta control run show <run-id>
```

## MCP tool interface

For coding agents accessing L0 via MCP:

```python
# Claim the next available task
result = await mcp.call("control_claim_task", {"agent_id": "my-agent-1"})

# Signal step started
await mcp.call("control_mark_workflow_step_running", {
    "run_id": run_id,
    "step_id": "implementation",
})

# Record step result
await mcp.call("control_record_workflow_step_result", {
    "run_id": run_id,
    "step_id": "implementation",
    "result": {"files_changed": ["src/feature.py"]},
    "status": "SUCCESS",
})

# Evaluate policy gate
await mcp.call("control_record_workflow_gate_outcome", {
    "run_id": run_id,
    "gate_id": "quality",
    "outcome": "APPROVED",
    "confidence": 0.92,
})

# Release run
await mcp.call("control_mark_workflow_step_failed", {
    "run_id": run_id,
    "step_id": "implementation",
    "error": "Compilation failed: ...",
})
```

## State storage location

All state is stored in `.tta/control_plane/` (created on first use):

```
.tta/control_plane/
  tasks/<task-id>.json
  runs/<run-id>.json
  leases/<run-id>.json
```

State files are human-readable JSON — inspect with `cat` for debugging.
Do not edit manually — use the CLI or MCP tools.

## Cross-repo note

See `docs/agents/dev/l0-coordination.md` for the boundary between
TTA.dev's L0 developer control plane and TTA's player-session orchestration.
