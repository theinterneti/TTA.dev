---
name: tools
description: "Skill for the Tools area of TTA.dev. 32 symbols across 7 files."
---

# Tools

32 symbols | 7 files | Cohesion: 46%

## When to Use

- Working with code in `ttadev/`
- Understanding how control_start_workflow, control_mark_workflow_step_running, control_record_workflow_step_result work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ttadev/primitives/mcp_server/tools/control_plane.py` | control_release_lock, control_create_task, control_list_tasks, control_get_task, control_claim_task (+9) |
| `ttadev/primitives/mcp_server/tools/_helpers.py` | _create_control_plane_service, _emit_mcp_span, _serialize_task, _control_plane_error_payload, _paginate (+3) |
| `ttadev/primitives/mcp_server/tools/workflow.py` | control_start_workflow, control_mark_workflow_step_running, control_record_workflow_step_result, control_record_workflow_gate_outcome, control_mark_workflow_step_failed |
| `ttadev/control_plane/service.py` | list_active_ownership, acquire_workspace_lock |
| `ttadev/control_plane/models.py` | to_dict |
| `ttadev/primitives/mcp_server/tools/primitives.py` | tta_bootstrap |
| `ttadev/primitives/mcp_server/tools/observability.py` | _get_providers_status |

## Entry Points

Start here when exploring this area:

- **`control_start_workflow`** (Function) — `ttadev/primitives/mcp_server/tools/workflow.py:22`
- **`control_mark_workflow_step_running`** (Function) — `ttadev/primitives/mcp_server/tools/workflow.py:81`
- **`control_record_workflow_step_result`** (Function) — `ttadev/primitives/mcp_server/tools/workflow.py:126`
- **`control_record_workflow_gate_outcome`** (Function) — `ttadev/primitives/mcp_server/tools/workflow.py:175`
- **`control_mark_workflow_step_failed`** (Function) — `ttadev/primitives/mcp_server/tools/workflow.py:221`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `control_start_workflow` | Function | `ttadev/primitives/mcp_server/tools/workflow.py` | 22 |
| `control_mark_workflow_step_running` | Function | `ttadev/primitives/mcp_server/tools/workflow.py` | 81 |
| `control_record_workflow_step_result` | Function | `ttadev/primitives/mcp_server/tools/workflow.py` | 126 |
| `control_record_workflow_gate_outcome` | Function | `ttadev/primitives/mcp_server/tools/workflow.py` | 175 |
| `control_mark_workflow_step_failed` | Function | `ttadev/primitives/mcp_server/tools/workflow.py` | 221 |
| `control_release_lock` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 278 |
| `control_create_task` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 31 |
| `control_list_tasks` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 67 |
| `control_get_task` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 92 |
| `control_claim_task` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 108 |
| `control_decide_gate` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 147 |
| `control_reopen_gate` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 181 |
| `list_active_ownership` | Function | `ttadev/control_plane/service.py` | 181 |
| `control_list_ownership` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 398 |
| `control_list_project_ownership` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 418 |
| `control_list_session_ownership` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 445 |
| `acquire_workspace_lock` | Function | `ttadev/control_plane/service.py` | 213 |
| `to_dict` | Function | `ttadev/control_plane/models.py` | 563 |
| `control_acquire_workspace_lock` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 232 |
| `control_acquire_file_lock` | Function | `ttadev/primitives/mcp_server/tools/control_plane.py` | 255 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Control_list_project_ownership → Get` | cross_community | 5 |
| `Control_start_workflow → To_dict` | cross_community | 4 |
| `Control_claim_task → To_dict` | cross_community | 4 |
| `Control_mark_workflow_step_running → To_dict` | cross_community | 4 |
| `Control_record_workflow_step_result → To_dict` | cross_community | 4 |
| `Control_record_workflow_gate_outcome → To_dict` | cross_community | 4 |
| `Control_mark_workflow_step_failed → To_dict` | cross_community | 4 |
| `Control_list_tasks → To_dict` | cross_community | 4 |
| `Control_create_task → To_dict` | cross_community | 4 |
| `Control_get_task → To_dict` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 15 calls |
| Control_plane | 3 calls |
| Observability | 2 calls |

## How to Explore

1. `gitnexus_context({name: "control_start_workflow"})` — see callers and callees
2. `gitnexus_query({query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
