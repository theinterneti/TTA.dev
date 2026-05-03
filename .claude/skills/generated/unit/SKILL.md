---
name: unit
description: "Skill for the Unit area of TTA.dev. 1397 symbols across 140 files."
---

# Unit

1397 symbols | 140 files | Cohesion: 73%

## When to Use

- Working with code in `tests/`
- Understanding how test_executes_then_when_condition_true, test_else_not_called_when_true, test_then_called_with_input_and_context work
- Modifying unit-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/unit/test_model_discovery.py` | _discovery, _openai_compat_response, _make_httpx_mock, _error_httpx_mock, test_returns_mem_cache_when_fresh (+50) |
| `tests/unit/test_primitives_package_managers.py` | _mock_proc, test_success_path, test_all_extras_flag, test_no_dev_flag, test_working_dir_forwarded (+45) |
| `tests/unit/test_benchmark_fetcher.py` | _fetcher, _write_cache, _entry, test_empty_when_cache_file_absent, test_returns_typed_entries_from_valid_cache (+43) |
| `tests/unit/test_development_cycle.py` | _ctx, _graph, _dc, test_no_files_returns_empty_report, test_no_files_does_not_call_graph (+40) |
| `tests/unit/test_model_registry.py` | _ctx, _fresh_registry, _make_entry, test_last_seen_zero_never_stale, test_recent_entry_not_stale (+36) |
| `tests/unit/test_multi_model_workflow.py` | _ctx, _clf, _wf, _req, test_returns_response (+31) |
| `tests/unit/test_free_model_tracker.py` | _or_response, _raw_entry, _make_http_mock, test_returns_only_free_text_models, test_filters_non_text_modality (+31) |
| `tests/unit/test_ollama_primitive.py` | _ctx, _make_response, _primitive, test_basic_chat_returns_content, test_execute_think_flag_forwarded (+29) |
| `tests/unit/test_lifecycle_validation.py` | _ctx, _check, test_execute_passing_returns_passed_result, test_execute_failing_returns_failed_result, test_execute_passing_fix_command_is_none (+28) |
| `tests/unit/test_primitives_core_conditional.py` | _ctx, _prim, test_executes_then_when_condition_true, test_else_not_called_when_true, test_then_called_with_input_and_context (+27) |

## Entry Points

Start here when exploring this area:

- **`test_executes_then_when_condition_true`** (Function) — `tests/unit/test_primitives_core_conditional.py:80`
- **`test_else_not_called_when_true`** (Function) — `tests/unit/test_primitives_core_conditional.py:88`
- **`test_then_called_with_input_and_context`** (Function) — `tests/unit/test_primitives_core_conditional.py:96`
- **`test_condition_receives_input_and_context`** (Function) — `tests/unit/test_primitives_core_conditional.py:104`
- **`test_executes_else_when_condition_false`** (Function) — `tests/unit/test_primitives_core_conditional.py:124`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_executes_then_when_condition_true` | Function | `tests/unit/test_primitives_core_conditional.py` | 80 |
| `test_else_not_called_when_true` | Function | `tests/unit/test_primitives_core_conditional.py` | 88 |
| `test_then_called_with_input_and_context` | Function | `tests/unit/test_primitives_core_conditional.py` | 96 |
| `test_condition_receives_input_and_context` | Function | `tests/unit/test_primitives_core_conditional.py` | 104 |
| `test_executes_else_when_condition_false` | Function | `tests/unit/test_primitives_core_conditional.py` | 124 |
| `test_then_not_called_when_false` | Function | `tests/unit/test_primitives_core_conditional.py` | 132 |
| `test_passthrough_when_false_and_no_else` | Function | `tests/unit/test_primitives_core_conditional.py` | 140 |
| `test_passthrough_preserves_complex_input` | Function | `tests/unit/test_primitives_core_conditional.py` | 147 |
| `test_branches_on_input_value` | Function | `tests/unit/test_primitives_core_conditional.py` | 161 |
| `test_branches_on_context_value` | Function | `tests/unit/test_primitives_core_conditional.py` | 175 |
| `test_condition_exception_propagates` | Function | `tests/unit/test_primitives_core_conditional.py` | 196 |
| `test_then_exception_propagates` | Function | `tests/unit/test_primitives_core_conditional.py` | 205 |
| `test_else_exception_propagates` | Function | `tests/unit/test_primitives_core_conditional.py` | 214 |
| `test_executes_without_tracing` | Function | `tests/unit/test_primitives_core_conditional.py` | 231 |
| `test_metrics_recorded_on_success` | Function | `tests/unit/test_primitives_core_conditional.py` | 246 |
| `test_metrics_recorded_on_failure` | Function | `tests/unit/test_primitives_core_conditional.py` | 258 |
| `test_executes_matching_case` | Function | `tests/unit/test_primitives_core_conditional.py` | 307 |
| `test_non_selected_cases_not_called` | Function | `tests/unit/test_primitives_core_conditional.py` | 317 |
| `test_matching_case_called_with_input_and_context` | Function | `tests/unit/test_primitives_core_conditional.py` | 326 |
| `test_selector_receives_input_and_context` | Function | `tests/unit/test_primitives_core_conditional.py` | 334 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Parse_tool_calls` | cross_community | 6 |
| `Handle_model_command → Rank_models_for_task` | cross_community | 6 |
| `Handle_model_command → _classify_entry` | cross_community | 6 |
| `Main → _composite_score` | cross_community | 5 |
| `Control_start_workflow → To_dict` | cross_community | 4 |
| `Control_claim_task → To_dict` | cross_community | 4 |
| `Control_mark_workflow_step_running → To_dict` | cross_community | 4 |
| `Control_record_workflow_step_result → To_dict` | cross_community | 4 |
| `Control_record_workflow_gate_outcome → To_dict` | cross_community | 4 |
| `Control_mark_workflow_step_failed → To_dict` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Agents | 50 calls |
| Cli | 23 calls |
| Llm | 15 calls |
| Tools | 14 calls |
| Workflows | 13 calls |
| Control_plane | 11 calls |
| Safety | 10 calls |
| Integration | 9 calls |

## How to Explore

1. `gitnexus_context({name: "test_executes_then_when_condition_true"})` — see callers and callees
2. `gitnexus_query({query: "unit"})` — find related execution flows
3. Read key files listed above for implementation details
