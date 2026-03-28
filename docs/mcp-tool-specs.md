# MCP Control-Plane Tool Specifications

**Server:** `ttadev/primitives/mcp_server/server.py`
**Version:** M3.0
**Total tools:** 24

All tools are exposed over the Model Context Protocol. Read-only tools are safe
to call at any time. Mutating tools change persistent state in `.tta/control/`.
Idempotent tools are safe to retry.

All list tools support pagination via `limit` (default 50) and `offset`
(default 0) parameters. List responses include `total_count`, `has_more`, and
`next_offset` fields alongside the items array.

All tools accept an optional `data_dir` parameter (default: `".tta"`) to
redirect state to a non-default directory.

On error, any tool returns:
```json
{"error": "<message>", "error_type": "<ExceptionClassName>"}
```

---

## control_create_task

**Type:** Mutating
**Description:** Create a new task in the control plane with optional gates and resource locks.

**Input schema:**
```json
{
  "type": "object",
  "required": ["title"],
  "properties": {
    "title": {"type": "string", "description": "Short imperative title"},
    "description": {"type": "string", "default": ""},
    "project_name": {"type": "string"},
    "requested_role": {"type": "string"},
    "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"},
    "gates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "gate_type", "label"],
        "properties": {
          "id": {"type": "string"},
          "gate_type": {"type": "string", "enum": ["approval", "policy", "review"]},
          "label": {"type": "string"},
          "required": {"type": "boolean", "default": true},
          "policy_name": {"type": "string"}
        }
      }
    },
    "workspace_locks": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Workspace names to acquire locks on at claim time"
    },
    "file_locks": {
      "type": "array",
      "items": {"type": "string"},
      "description": "File paths to acquire locks on at claim time"
    },
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the newly created task.

---

## control_list_tasks

**Type:** Read-only
**Description:** List tasks in the control plane, optionally filtered by status or project.

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
    "project_name": {"type": "string"},
    "limit": {"type": "integer", "default": 50, "minimum": 1},
    "offset": {"type": "integer", "default": 0, "minimum": 0},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"tasks": [TaskRecord, ...], "total_count": int, "has_more": bool, "next_offset": int | null}`

---

## control_get_task

**Type:** Read-only
**Description:** Fetch a single task by ID.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id"],
  "properties": {
    "task_id": {"type": "string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}`

---

## control_claim_task

**Type:** Mutating
**Description:** Claim a pending task, create an active run, and issue a lease; optionally stamp OTel trace context.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id"],
  "properties": {
    "task_id": {"type": "string"},
    "agent_role": {"type": "string"},
    "lease_ttl_seconds": {"type": "number", "default": 300},
    "trace_id": {"type": "string", "description": "OTel trace ID hex string for attribution"},
    "span_id": {"type": "string", "description": "OTel span ID hex string for attribution"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord, "run": RunRecord, "lease": LeaseRecord}` — the claim result.

---

## control_decide_gate

**Type:** Mutating
**Description:** Record a gate decision (approved / rejected / changes_requested) for a task gate.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "gate_id", "status"],
  "properties": {
    "task_id": {"type": "string"},
    "gate_id": {"type": "string"},
    "status": {"type": "string", "enum": ["approved", "rejected", "changes_requested"]},
    "decided_by": {"type": "string"},
    "decision_role": {"type": "string"},
    "summary": {"type": "string", "default": ""},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the updated task.

---

## control_reopen_gate

**Type:** Mutating
**Description:** Reopen a gate that is currently in `changes_requested` state.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "gate_id"],
  "properties": {
    "task_id": {"type": "string"},
    "gate_id": {"type": "string"},
    "reopened_by": {"type": "string"},
    "summary": {"type": "string", "default": ""},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the updated task.

---

## control_list_locks

**Type:** Read-only
**Description:** List active coordination locks, optionally filtered by scope type.

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "scope_type": {"type": "string", "enum": ["workspace", "file"]},
    "limit": {"type": "integer", "default": 50, "minimum": 1},
    "offset": {"type": "integer", "default": 0, "minimum": 0},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"locks": [LockRecord, ...], "total_count": int, "has_more": bool, "next_offset": int | null}`

---

## control_acquire_workspace_lock

**Type:** Mutating
**Description:** Acquire an exclusive workspace-scoped lock for an active run.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "run_id", "workspace_name"],
  "properties": {
    "task_id": {"type": "string"},
    "run_id": {"type": "string"},
    "workspace_name": {"type": "string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"lock": LockRecord}`

---

## control_acquire_file_lock

**Type:** Mutating
**Description:** Acquire an exclusive file-scoped lock for an active run.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "run_id", "file_path"],
  "properties": {
    "task_id": {"type": "string"},
    "run_id": {"type": "string"},
    "file_path": {"type": "string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"lock": LockRecord}`

---

## control_release_lock

**Type:** Idempotent
**Description:** Release a coordination lock by ID; safe to call more than once.

**Input schema:**
```json
{
  "type": "object",
  "required": ["lock_id"],
  "properties": {
    "lock_id": {"type": "string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"released_lock_id": "<lock_id>"}`

---

## control_list_runs

**Type:** Read-only
**Description:** List runs, optionally filtered by status.

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["active", "completed", "released", "expired"]},
    "limit": {"type": "integer", "default": 50, "minimum": 1},
    "offset": {"type": "integer", "default": 0, "minimum": 0},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"runs": [RunRecord, ...], "total_count": int, "has_more": bool, "next_offset": int | null}`

---

## control_get_run

**Type:** Read-only
**Description:** Fetch a single run and its current lease by run ID.

**Input schema:**
```json
{
  "type": "object",
  "required": ["run_id"],
  "properties": {
    "run_id": {"type": "string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"run": RunRecord, "lease": LeaseRecord | null}`

---

## control_heartbeat_run

**Type:** Idempotent
**Description:** Renew the lease for an active run; safe to call repeatedly.

**Input schema:**
```json
{
  "type": "object",
  "required": ["run_id"],
  "properties": {
    "run_id": {"type": "string"},
    "lease_ttl_seconds": {"type": "number", "default": 300},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"lease": LeaseRecord}`

---

## control_complete_run

**Type:** Mutating
**Description:** Mark an active run as completed and auto-finalize the parent task if all steps are done.

**Input schema:**
```json
{
  "type": "object",
  "required": ["run_id"],
  "properties": {
    "run_id": {"type": "string"},
    "summary": {"type": "string", "default": ""},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"run": RunRecord}` — the updated run.

---

## control_release_run

**Type:** Mutating
**Description:** Release an active run back to pending (e.g., on agent failure) with an optional reason.

**Input schema:**
```json
{
  "type": "object",
  "required": ["run_id"],
  "properties": {
    "run_id": {"type": "string"},
    "reason": {"type": "string", "default": ""},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"run": RunRecord}` — the updated run.

---

## control_list_ownership

**Type:** Read-only
**Description:** List active ownership records (task + run + lease + session/project context) across all projects and sessions.

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "limit": {"type": "integer", "default": 50, "minimum": 1},
    "offset": {"type": "integer", "default": 0, "minimum": 0},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"active": [OwnershipRecord, ...], "total_count": int, "has_more": bool, "next_offset": int | null}`

---

## control_list_project_ownership

**Type:** Read-only
**Description:** List active ownership records scoped to a single project.

**Input schema:**
```json
{
  "type": "object",
  "required": ["project_id"],
  "properties": {
    "project_id": {"type": "string"},
    "limit": {"type": "integer", "default": 50, "minimum": 1},
    "offset": {"type": "integer", "default": 0, "minimum": 0},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"project_id": str, "active": [OwnershipRecord, ...], "total_count": int, "has_more": bool, "next_offset": int | null}`

---

## control_list_session_ownership

**Type:** Read-only
**Description:** List active ownership records scoped to a single session.

**Input schema:**
```json
{
  "type": "object",
  "required": ["session_id"],
  "properties": {
    "session_id": {"type": "string"},
    "limit": {"type": "integer", "default": 50, "minimum": 1},
    "offset": {"type": "integer", "default": 0, "minimum": 0},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"session_id": str, "active": [OwnershipRecord, ...], "total_count": int, "has_more": bool, "next_offset": int | null}`

---

## control_start_workflow

**Type:** Mutating
**Description:** Create and immediately claim a tracked multi-agent workflow task, registering one approval gate per step agent.

**Input schema:**
```json
{
  "type": "object",
  "required": ["workflow_name", "workflow_goal", "step_agents"],
  "properties": {
    "workflow_name": {"type": "string"},
    "workflow_goal": {"type": "string"},
    "step_agents": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1,
      "description": "Ordered list of agent names — one entry per workflow step"
    },
    "project_name": {"type": "string"},
    "policy_gates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "label", "policy"],
        "properties": {
          "id": {"type": "string"},
          "label": {"type": "string"},
          "policy": {"type": "string", "description": "Policy expression, e.g. \"auto:confidence>=0.85\""}
        }
      },
      "description": "Optional extra POLICY gates appended after step gates"
    },
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord, "run": RunRecord, "lease": LeaseRecord}` — the claim result.

---

## control_mark_workflow_step_running

**Type:** Idempotent
**Description:** Transition a tracked workflow step to RUNNING; safe to call again on retry (trace context is replaced).

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "step_index"],
  "properties": {
    "task_id": {"type": "string"},
    "step_index": {"type": "integer", "minimum": 0},
    "trace_id": {"type": "string", "description": "OTel trace ID hex string"},
    "span_id": {"type": "string", "description": "OTel span ID hex string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the updated task.

---

## control_record_workflow_step_result

**Type:** Mutating
**Description:** Record the result and confidence score for a completed workflow step; automatically evaluates any pending POLICY gates.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "step_index", "result_summary", "confidence"],
  "properties": {
    "task_id": {"type": "string"},
    "step_index": {"type": "integer", "minimum": 0},
    "result_summary": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the updated task.

---

## control_record_workflow_gate_outcome

**Type:** Mutating
**Description:** Record an approval-gate decision for a tracked workflow step, advancing or halting the workflow.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "step_index", "decision"],
  "properties": {
    "task_id": {"type": "string"},
    "step_index": {"type": "integer", "minimum": 0},
    "decision": {
      "type": "string",
      "enum": ["continue", "skip", "edit", "quit", "escalate_to_human"]
    },
    "summary": {"type": "string", "default": ""},
    "policy_name": {
      "type": "string",
      "description": "Set when the decision was made automatically by a policy rule"
    },
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the updated task.

---

## control_mark_workflow_step_failed

**Type:** Mutating
**Description:** Mark a tracked workflow step as FAILED with an error summary.

**Input schema:**
```json
{
  "type": "object",
  "required": ["task_id", "step_index", "error_summary"],
  "properties": {
    "task_id": {"type": "string"},
    "step_index": {"type": "integer", "minimum": 0},
    "error_summary": {"type": "string"},
    "data_dir": {"type": "string", "default": ".tta"}
  }
}
```

**Output:** `{"task": TaskRecord}` — the updated task.

---

## Response Object Shapes

### TaskRecord
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "status": "pending | in_progress | completed",
  "priority": "low | normal | high",
  "project_name": "string | null",
  "requested_role": "string | null",
  "gates": [
    {
      "id": "string",
      "gate_type": "approval | policy | review",
      "label": "string",
      "status": "pending | approved | rejected | changes_requested",
      "required": "boolean",
      "policy_name": "string | null",
      "decided_by": "string | null",
      "decision_role": "string | null",
      "summary": "string | null",
      "history": []
    }
  ],
  "workflow_steps": [
    {
      "step_index": "integer",
      "agent": "string",
      "status": "pending | running | completed | skipped | quit | failed",
      "result_summary": "string | null",
      "confidence": "number | null",
      "gate_decision": "continue | skip | edit | quit | escalate_to_human | null",
      "trace_id": "string | null",
      "span_id": "string | null"
    }
  ],
  "created_at": "ISO-8601 string",
  "updated_at": "ISO-8601 string"
}
```

### RunRecord
```json
{
  "id": "string",
  "task_id": "string",
  "status": "active | completed | released | expired",
  "agent_role": "string | null",
  "summary": "string | null",
  "trace_id": "string | null",
  "span_id": "string | null",
  "started_at": "ISO-8601 string",
  "ended_at": "ISO-8601 string | null"
}
```

### LeaseRecord
```json
{
  "id": "string",
  "run_id": "string",
  "expires_at": "ISO-8601 string",
  "ttl_seconds": "number"
}
```

### LockRecord
```json
{
  "id": "string",
  "task_id": "string",
  "run_id": "string",
  "scope_type": "workspace | file",
  "scope_name": "string",
  "acquired_at": "ISO-8601 string"
}
```

### OwnershipRecord
```json
{
  "task": "TaskRecord",
  "run": "RunRecord",
  "lease": "LeaseRecord | null",
  "session": "object | null",
  "project": "object | null",
  "telemetry": "object | null"
}
```
