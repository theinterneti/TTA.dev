---
name: control-plane
description: "Skill for the Control_plane area of TTA.dev. 82 symbols across 16 files."
---

# Control_plane

82 symbols | 16 files | Cohesion: 80%

## When to Use

- Working with code in `ttadev/`
- Understanding how put_run, list_leases, get_lease_for_task work
- Modifying control_plane-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ttadev/control_plane/store.py` | _read_map, _write_map, _lock_for, put_run, list_leases (+10) |
| `ttadev/control_plane/workflow_service.py` | _emit_control_plane_span, _now_iso, _make_workflow_gate_id, _get_workflow_step, _build_workflow_gate_decision_record (+6) |
| `ttadev/control_plane/task_service.py` | _now, _now_iso, _current_agent_id, _find_gate, _ensure_gate_decider_allowed (+6) |
| `ttadev/control_plane/lease_service.py` | _now, _now_iso, _validate_lock_owner, _acquire_lock, _expire_lease (+6) |
| `ttadev/control_plane/run_service.py` | _now, _now_iso, get_run, get_lease_for_run, list_active_ownership (+5) |
| `ttadev/control_plane/models.py` | to_dict, from_dict, from_dict, from_dict, from_dict (+4) |
| `ttadev/control_plane/service.py` | heartbeat_run, list_runs, _parse_policy_decision |
| `tests/unit/test_l0_store.py` | test_lease_roundtrip_and_delete, test_task_roundtrip |
| `tests/unit/test_control_plane_trace_attribution.py` | test_run_record_round_trips_trace_fields, test_workflow_step_round_trips_trace_fields |
| `ttadev/primitives/mcp_server/tools/control_plane.py` | control_heartbeat_run, control_list_runs |

## Entry Points

Start here when exploring this area:

- **`put_run`** (Function) — `ttadev/control_plane/store.py:71`
- **`list_leases`** (Function) — `ttadev/control_plane/store.py:77`
- **`get_lease_for_task`** (Function) — `ttadev/control_plane/store.py:81`
- **`put_lease`** (Function) — `ttadev/control_plane/store.py:92`
- **`delete_lease`** (Function) — `ttadev/control_plane/store.py:98`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `put_run` | Function | `ttadev/control_plane/store.py` | 71 |
| `list_leases` | Function | `ttadev/control_plane/store.py` | 77 |
| `get_lease_for_task` | Function | `ttadev/control_plane/store.py` | 81 |
| `put_lease` | Function | `ttadev/control_plane/store.py` | 92 |
| `delete_lease` | Function | `ttadev/control_plane/store.py` | 98 |
| `put_lock` | Function | `ttadev/control_plane/store.py` | 123 |
| `delete_lock` | Function | `ttadev/control_plane/store.py` | 129 |
| `to_dict` | Function | `ttadev/control_plane/models.py` | 481 |
| `from_dict` | Function | `ttadev/control_plane/models.py` | 539 |
| `test_lease_roundtrip_and_delete` | Function | `tests/unit/test_l0_store.py` | 50 |
| `get_run` | Function | `ttadev/control_plane/run_service.py` | 160 |
| `get_lease_for_run` | Function | `ttadev/control_plane/run_service.py` | 167 |
| `list_active_ownership` | Function | `ttadev/control_plane/run_service.py` | 171 |
| `claim_task` | Function | `ttadev/control_plane/run_service.py` | 213 |
| `heartbeat_run` | Function | `ttadev/control_plane/run_service.py` | 316 |
| `complete_run` | Function | `ttadev/control_plane/run_service.py` | 340 |
| `release_run` | Function | `ttadev/control_plane/run_service.py` | 382 |
| `finalize_tracked_workflow` | Function | `ttadev/control_plane/run_service.py` | 412 |
| `get_integration` | Function | `ttadev/observability/apm/langfuse/tta_apm_langfuse/__init__.py` | 11 |
| `start_tracked_workflow` | Function | `ttadev/control_plane/workflow_service.py` | 138 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Get_integration` | cross_community | 5 |
| `Main → Get_integration` | cross_community | 5 |
| `Main → Get_integration` | cross_community | 4 |
| `Acquire_workspace_lock → Release_locks_for_run` | intra_community | 4 |
| `Acquire_file_lock → Release_locks_for_run` | intra_community | 4 |
| `Finalize_tracked_workflow → _now` | intra_community | 4 |
| `Control_claim_task → To_dict` | cross_community | 3 |
| `Control_get_run → To_dict` | cross_community | 3 |
| `Control_get_run → To_dict` | cross_community | 3 |
| `Decide_gate → _get_active_session` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 7 calls |
| Unit | 6 calls |
| Observability | 1 calls |

## How to Explore

1. `gitnexus_context({name: "put_run"})` — see callers and callees
2. `gitnexus_query({query: "control_plane"})` — find related execution flows
3. Read key files listed above for implementation details
