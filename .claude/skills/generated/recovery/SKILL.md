---
name: recovery
description: "Skill for the Recovery area of TTA.dev. 48 symbols across 6 files."
---

# Recovery

48 symbols | 6 files | Cohesion: 79%

## When to Use

- Working with code in `tests/`
- Understanding how execute, test_primary_succeeds_returns_primary_result_with_tracer, test_fallback_invoked_when_primary_fails_with_tracer work
- Modifying recovery-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/primitives/recovery/test_retry_primitive.py` | _make_primitive, test_succeeds_on_first_attempt, test_passes_context_to_wrapped_primitive, test_raises_after_max_retries_exceeded, test_zero_retries_fails_immediately (+9) |
| `tests/primitives/recovery/test_fallback_primitive.py` | _make_ctx, _ok, _fail, test_primary_succeeds_returns_primary_result_with_tracer, test_fallback_invoked_when_primary_fails_with_tracer (+8) |
| `tests/primitives/recovery/test_circuit_breaker_primitive.py` | test_success_resets_failure_count, test_circuit_breaker_opens_after_failure_threshold, test_circuit_open_blocks_without_calling_wrapped_primitive, test_circuit_breaker_error_carries_failure_count, test_circuit_breaker_transitions_to_half_open_after_recovery_timeout (+7) |
| `ttadev/primitives/recovery/circuit_breaker_primitive.py` | execute, _should_attempt_reset, call, _should_attempt_reset, classify_error (+2) |
| `ttadev/primitives/recovery/fallback.py` | execute |
| `ttadev/demo_working_tta.py` | main |

## Entry Points

Start here when exploring this area:

- **`execute`** (Function) — `ttadev/primitives/recovery/fallback.py:64`
- **`test_primary_succeeds_returns_primary_result_with_tracer`** (Function) — `tests/primitives/recovery/test_fallback_primitive.py:67`
- **`test_fallback_invoked_when_primary_fails_with_tracer`** (Function) — `tests/primitives/recovery/test_fallback_primitive.py:79`
- **`test_raises_primary_error_when_both_fail_with_tracer`** (Function) — `tests/primitives/recovery/test_fallback_primitive.py:91`
- **`test_fallback_not_called_when_primary_succeeds_with_tracer`** (Function) — `tests/primitives/recovery/test_fallback_primitive.py:102`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `execute` | Function | `ttadev/primitives/recovery/fallback.py` | 64 |
| `test_primary_succeeds_returns_primary_result_with_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 67 |
| `test_fallback_invoked_when_primary_fails_with_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 79 |
| `test_raises_primary_error_when_both_fail_with_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 91 |
| `test_fallback_not_called_when_primary_succeeds_with_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 102 |
| `test_primary_succeeds_returns_primary_result_without_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 125 |
| `test_fallback_invoked_when_primary_fails_without_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 138 |
| `test_raises_primary_error_when_both_fail_without_tracer` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 151 |
| `test_checkpoints_recorded_on_primary_success` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 170 |
| `test_checkpoints_recorded_on_fallback_path` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 186 |
| `test_checkpoints_recorded_on_both_fail` | Function | `tests/primitives/recovery/test_fallback_primitive.py` | 201 |
| `main` | Function | `ttadev/demo_working_tta.py` | 31 |
| `execute` | Function | `ttadev/primitives/recovery/circuit_breaker_primitive.py` | 158 |
| `test_success_resets_failure_count` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 147 |
| `test_circuit_breaker_opens_after_failure_threshold` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 181 |
| `test_circuit_open_blocks_without_calling_wrapped_primitive` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 203 |
| `test_circuit_breaker_error_carries_failure_count` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 232 |
| `test_circuit_breaker_transitions_to_half_open_after_recovery_timeout` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 262 |
| `test_circuit_in_half_open_closes_after_success_threshold` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 294 |
| `test_circuit_half_open_failure_reopens_circuit` | Function | `tests/primitives/recovery/test_circuit_breaker_primitive.py` | 327 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Init → _should_attempt_reset` | cross_community | 5 |
| `Init → _on_success` | cross_community | 5 |
| `Init → _on_failure` | cross_community | 5 |
| `Wrapper → Classify_error` | intra_community | 3 |
| `Main → _should_attempt_reset` | cross_community | 3 |
| `Main → _on_success` | cross_community | 3 |
| `Main → _on_failure` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 18 calls |

## How to Explore

1. `gitnexus_context({name: "execute"})` — see callers and callees
2. `gitnexus_query({query: "recovery"})` — find related execution flows
3. Read key files listed above for implementation details
