---
name: tests
description: "Skill for the Tests area of TTA.dev. 177 symbols across 22 files."
---

# Tests

177 symbols | 22 files | Cohesion: 75%

## When to Use

- Working with code in `tests/`
- Understanding how test_openai_provider_with_tools_populates_tool_calls, test_openai_provider_without_tools_has_none_tool_calls, test_openai_provider_finish_reason_stop work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_eval_harness.py` | _task, _llm_resp, _ctx, test_execute_calls_all_models_and_populates_results, test_failed_model_sets_error_field_not_raises (+29) |
| `tests/test_ollama_primitives.py` | _ctx, test_health_check_healthy, test_health_check_unhealthy, test_list_models, test_running_models (+19) |
| `tests/test_model_monitor.py` | _ctx, _monitor, test_record_success_tracks_stats, test_record_failure_tracks_stats, test_success_rate_computed (+17) |
| `tests/test_tool_calling.py` | _make_ctx, _make_request, _make_openai_mock_response, test_openai_provider_with_tools_populates_tool_calls, test_openai_provider_without_tools_has_none_tool_calls (+12) |
| `tests/test_model_benchmarks.py` | _ctx, _registry, _entry, test_min_humaneval_score_excludes_low_scoring_models, test_min_humaneval_score_excludes_models_with_no_data (+8) |
| `tests/test_auth_session.py` | test_verify_session_returns_payload_for_valid_token, test_verify_session_preserves_user_id, test_verify_session_preserves_scopes, test_verify_session_returns_none_for_expired_token, test_verify_session_returns_none_for_wrong_secret (+1) |
| `tests/unit/test_auth_session.py` | test_encode_decode_roundtrip, test_valid_token_returns_payload, test_wrong_secret_rejected, test_tampered_payload_rejected, test_expired_token_rejected (+1) |
| `tests/test_auth_api_key.py` | test_store_and_get_round_trip, test_revoke_sets_revoked_flag_to_true, test_store_overwrites_existing_record_with_same_key_id, test_scopes_are_stored_correctly, test_is_valid_returns_true_for_valid_key (+1) |
| `ttadev/integrations/auth/session.py` | _b64url_encode, _b64url_decode, _sign, create_session, verify_session |
| `tests/unit/test_ollama_primitive.py` | test_health_returns_true_on_200, test_health_returns_false_on_non_200, test_health_returns_false_on_connection_error, test_unknown_action_raises_value_error, test_execute_propagates_client_error |

## Entry Points

Start here when exploring this area:

- **`test_openai_provider_with_tools_populates_tool_calls`** (Function) — `tests/test_tool_calling.py:223`
- **`test_openai_provider_without_tools_has_none_tool_calls`** (Function) — `tests/test_tool_calling.py:249`
- **`test_openai_provider_finish_reason_stop`** (Function) — `tests/test_tool_calling.py:269`
- **`test_openai_provider_multiple_tool_calls_in_single_response`** (Function) — `tests/test_tool_calling.py:286`
- **`test_groq_provider_with_tools_populates_tool_calls`** (Function) — `tests/test_tool_calling.py:317`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_openai_provider_with_tools_populates_tool_calls` | Function | `tests/test_tool_calling.py` | 223 |
| `test_openai_provider_without_tools_has_none_tool_calls` | Function | `tests/test_tool_calling.py` | 249 |
| `test_openai_provider_finish_reason_stop` | Function | `tests/test_tool_calling.py` | 269 |
| `test_openai_provider_multiple_tool_calls_in_single_response` | Function | `tests/test_tool_calling.py` | 286 |
| `test_groq_provider_with_tools_populates_tool_calls` | Function | `tests/test_tool_calling.py` | 317 |
| `test_anthropic_provider_with_tools_populates_tool_calls` | Function | `tests/test_tool_calling.py` | 382 |
| `test_anthropic_provider_without_tools_has_none_tool_calls` | Function | `tests/test_tool_calling.py` | 410 |
| `test_anthropic_provider_multiple_tool_calls` | Function | `tests/test_tool_calling.py` | 437 |
| `test_anthropic_provider_mixed_text_and_tool_calls` | Function | `tests/test_tool_calling.py` | 465 |
| `test_ollama_provider_with_tools_populates_tool_calls` | Function | `tests/test_tool_calling.py` | 493 |
| `test_ollama_provider_without_tools_has_none_tool_calls` | Function | `tests/test_tool_calling.py` | 534 |
| `test_ollama_provider_finish_reason_is_stop_for_text_response` | Function | `tests/test_tool_calling.py` | 561 |
| `test_ollama_payload_includes_tools_when_set` | Function | `tests/test_tool_calling.py` | 585 |
| `test_execute_calls_all_models_and_populates_results` | Function | `tests/test_eval_harness.py` | 303 |
| `test_failed_model_sets_error_field_not_raises` | Function | `tests/test_eval_harness.py` | 321 |
| `test_keyword_score_two_of_three` | Function | `tests/test_eval_harness.py` | 348 |
| `test_run_id_is_unique_per_execute_call` | Function | `tests/test_eval_harness.py` | 364 |
| `test_completed_at_is_set_after_execute` | Function | `tests/test_eval_harness.py` | 377 |
| `test_timeout_model_gets_error_result_not_exception` | Function | `tests/test_eval_harness.py` | 391 |
| `test_unknown_provider_gives_error_result` | Function | `tests/test_eval_harness.py` | 412 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 54 calls |
| Llm | 17 calls |
| Observability | 2 calls |
| Performance | 2 calls |
| Scripts | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_openai_provider_with_tools_populates_tool_calls"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
