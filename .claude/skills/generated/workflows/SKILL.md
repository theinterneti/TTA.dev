---
name: workflows
description: "Skill for the Workflows area of TTA.dev. 56 symbols across 10 files."
---

# Workflows

56 symbols | 10 files | Cohesion: 58%

## When to Use

- Working with code in `tests/`
- Understanding how user_message, test_no_provider_error_returns_exit_1, test_openai_auth_error_shows_friendly_message work
- Modifying workflows-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/workflows/test_orchestrator.py` | _three_step_registry, test_aggregates_artifacts, test_skip_marks_step_skipped, test_no_confirm_never_calls_prompt_user, test_no_confirm_completes_all_steps_without_tty (+7) |
| `ttadev/workflows/memory.py` | _warn_once, reflect, async_reflect, retain, async_retain (+6) |
| `tests/workflows/test_gate.py` | _step_result, test_auto_approve_returns_continue, test_auto_approve_no_io, test_non_tty_auto_approves, test_e_with_instruction_returns_edit (+4) |
| `ttadev/workflows/llm_provider.py` | user_message, _is_provider_error, get_default_ollama_model, _config_from_spec, get_llm_provider_chain (+1) |
| `tests/workflows/test_llm_provider.py` | _make_fake_args, test_no_provider_error_returns_exit_1, test_openai_auth_error_shows_friendly_message, test_httpx_connect_error_shows_friendly_message, test_unrelated_error_is_reraised |
| `tests/unit/test_workflow_memory.py` | test_reflect_no_raise, test_warned_true_after_call, test_warning_message_logged, test_recall_returns_empty_list, test_recall_no_raise |
| `ttadev/workflows/development_cycle.py` | _build_system_prompt, _reframe_instruction, _run_chain_pass, _write |
| `tests/unit/test_development_cycle.py` | test_retry_on_low_quality, test_raises_when_all_providers_error |
| `ttadev/cli/workflow.py` | _cmd_run |
| `ttadev/workflows/quality_gate.py` | quality_gate_passed |

## Entry Points

Start here when exploring this area:

- **`user_message`** (Function) — `ttadev/workflows/llm_provider.py:74`
- **`test_no_provider_error_returns_exit_1`** (Function) — `tests/workflows/test_llm_provider.py:343`
- **`test_openai_auth_error_shows_friendly_message`** (Function) — `tests/workflows/test_llm_provider.py:364`
- **`test_httpx_connect_error_shows_friendly_message`** (Function) — `tests/workflows/test_llm_provider.py:394`
- **`test_unrelated_error_is_reraised`** (Function) — `tests/workflows/test_llm_provider.py:420`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `user_message` | Function | `ttadev/workflows/llm_provider.py` | 74 |
| `test_no_provider_error_returns_exit_1` | Function | `tests/workflows/test_llm_provider.py` | 343 |
| `test_openai_auth_error_shows_friendly_message` | Function | `tests/workflows/test_llm_provider.py` | 364 |
| `test_httpx_connect_error_shows_friendly_message` | Function | `tests/workflows/test_llm_provider.py` | 394 |
| `test_unrelated_error_is_reraised` | Function | `tests/workflows/test_llm_provider.py` | 420 |
| `quality_gate_passed` | Function | `ttadev/workflows/quality_gate.py` | 99 |
| `test_retry_on_low_quality` | Function | `tests/unit/test_development_cycle.py` | 276 |
| `test_raises_when_all_providers_error` | Function | `tests/unit/test_development_cycle.py` | 299 |
| `test_aggregates_artifacts` | Function | `tests/workflows/test_orchestrator.py` | 103 |
| `test_skip_marks_step_skipped` | Function | `tests/workflows/test_orchestrator.py` | 125 |
| `test_no_confirm_never_calls_prompt_user` | Function | `tests/workflows/test_orchestrator.py` | 267 |
| `test_no_confirm_completes_all_steps_without_tty` | Function | `tests/workflows/test_orchestrator.py` | 307 |
| `test_tracked_quit_records_quit_state` | Function | `tests/workflows/test_orchestrator.py` | 362 |
| `test_completes_all_steps` | Function | `tests/workflows/test_orchestrator.py` | 91 |
| `test_total_confidence_is_mean` | Function | `tests/workflows/test_orchestrator.py` | 113 |
| `test_quit_stops_workflow` | Function | `tests/workflows/test_orchestrator.py` | 148 |
| `test_no_confirm_prints_auto_approved_messages` | Function | `tests/workflows/test_orchestrator.py` | 293 |
| `test_tracked_run_creates_l0_task_and_run` | Function | `tests/workflows/test_orchestrator.py` | 337 |
| `test_auto_approve_returns_continue` | Function | `tests/workflows/test_gate.py` | 24 |
| `test_auto_approve_no_io` | Function | `tests/workflows/test_gate.py` | 31 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Async_retain → _warn_once` | cross_community | 3 |
| `Async_recall → _warn_once` | cross_community | 3 |
| `Async_reflect → _warn_once` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 22 calls |
| Agents | 11 calls |
| Cli | 3 calls |

## How to Explore

1. `gitnexus_context({name: "user_message"})` — see callers and callees
2. `gitnexus_query({query: "workflows"})` — find related execution flows
3. Read key files listed above for implementation details
