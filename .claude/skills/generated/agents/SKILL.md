---
name: agents
description: "Skill for the Agents area of TTA.dev. 77 symbols across 26 files."
---

# Agents

77 symbols | 26 files | Cohesion: 71%

## When to Use

- Working with code in `tests/`
- Understanding how register, override_registry, test_edit_reruns_step_with_new_instruction work
- Modifying agents-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/agents/test_spawn_agent_model_injection.py` | _make_spec, _make_model_aware_agent, _make_legacy_agent, test_spawn_agent_context_default_model_no_type_error, test_spawned_agent_has_non_none_model (+5) |
| `tests/agents/test_registry.py` | test_override_is_visible_inside_context, test_register_and_get, test_register_overwrites, test_global_restored_after_context, test_override_restored_on_exception (+4) |
| `tests/agents/test_tool_call_loop.py` | _make_anthropic_response, _make_google_response, test_parse_anthropic_tool_calls, test_parse_anthropic_multiple_tool_calls, test_parse_google_tool_calls (+3) |
| `tests/agents/test_router.py` | _make_registry, _make_router, test_agent_hint_bypasses_scoring, test_keyword_routing_no_llm_call, test_ambiguous_task_calls_orchestrator (+2) |
| `ttadev/agents/registry.py` | register, override_registry, get, get_registry, all |
| `ttadev/cli/agent.py` | handle_agent_command, _cmd_list, _cmd_show, _cmd_run, _run_agent |
| `tests/agents/test_spawn_agent.py` | _make_agent_class, test_spawn_agent_returns_result, test_spawn_agent_unknown_name_raises, test_spawn_agent_without_workflow_context |
| `tests/unit/test_spawn_agent_no_model.py` | _make_model_aware_agent, test_spawn_agent_no_model_arg_with_context_default_succeeds, test_mock_primitive_tracker_was_invoked |
| `tests/agents/test_agent_primitive.py` | test_subclass_auto_registers, _make_spec, __init__ |
| `ttadev/agents/router.py` | _get_model, _get_orchestrator, _execute_impl |

## Entry Points

Start here when exploring this area:

- **`register`** (Function) — `ttadev/agents/registry.py:24`
- **`override_registry`** (Function) — `ttadev/agents/registry.py:61`
- **`test_edit_reruns_step_with_new_instruction`** (Function) — `tests/workflows/test_orchestrator.py:167`
- **`test_memory_attached_to_context`** (Function) — `tests/workflows/test_orchestrator.py:219`
- **`test_spawn_agent_no_model_arg_with_context_default_succeeds`** (Function) — `tests/unit/test_spawn_agent_no_model.py:76`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `register` | Function | `ttadev/agents/registry.py` | 24 |
| `override_registry` | Function | `ttadev/agents/registry.py` | 61 |
| `test_edit_reruns_step_with_new_instruction` | Function | `tests/workflows/test_orchestrator.py` | 167 |
| `test_memory_attached_to_context` | Function | `tests/workflows/test_orchestrator.py` | 219 |
| `test_spawn_agent_no_model_arg_with_context_default_succeeds` | Function | `tests/unit/test_spawn_agent_no_model.py` | 76 |
| `test_mock_primitive_tracker_was_invoked` | Function | `tests/unit/test_spawn_agent_no_model.py` | 103 |
| `test_feature_dev_with_l0_tracking` | Function | `tests/integration/test_multi_agent_proof.py` | 29 |
| `test_feature_dev_failed_step_recorded` | Function | `tests/integration/test_multi_agent_proof.py` | 87 |
| `test_spawn_agent_context_default_model_no_type_error` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 95 |
| `test_spawned_agent_has_non_none_model` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 120 |
| `test_spawn_agent_explicit_model_kwarg` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 142 |
| `test_explicit_model_takes_precedence_over_context_default` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 161 |
| `test_legacy_agent_still_works_no_model_param` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 187 |
| `test_spawn_agent_unknown_name_still_raises_key_error` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 208 |
| `test_spawn_agent_no_model_no_default_raises_value_error_not_type_error` | Function | `tests/agents/test_spawn_agent_model_injection.py` | 218 |
| `test_spawn_agent_returns_result` | Function | `tests/agents/test_spawn_agent.py` | 47 |
| `test_spawn_agent_unknown_name_raises` | Function | `tests/agents/test_spawn_agent.py` | 61 |
| `test_spawn_agent_without_workflow_context` | Function | `tests/agents/test_spawn_agent.py` | 70 |
| `test_override_is_visible_inside_context` | Function | `tests/agents/test_registry.py` | 48 |
| `test_subclass_auto_registers` | Function | `tests/agents/test_agent_primitive.py` | 111 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 3 calls |
| Llm | 2 calls |

## How to Explore

1. `gitnexus_context({name: "register"})` — see callers and callees
2. `gitnexus_query({query: "agents"})` — find related execution flows
3. Read key files listed above for implementation details
