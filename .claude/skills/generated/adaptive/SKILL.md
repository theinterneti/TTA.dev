---
name: adaptive
description: "Skill for the Adaptive area of TTA.dev. 151 symbols across 10 files."
---

# Adaptive

151 symbols | 10 files | Cohesion: 81%

## When to Use

- Working with code in `tests/`
- Understanding how get_fallback_stats, test_get_default_strategy_returns_baseline, test_primary_succeeds_returns_primary_result work
- Modifying adaptive-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/primitives/adaptive/test_adaptive_retry.py` | _ctx, test_execute_retry_success_on_first_attempt, test_execute_retry_succeeds_after_failures, test_execute_retry_exhaustion_returns_failure_dict, test_execute_retry_no_sleep_after_last_attempt (+32) |
| `tests/primitives/adaptive/test_adaptive_cache.py` | _ctx, _make_cache, test_cache_default_strategy_params, test_cache_miss_calls_target_primitive, test_cache_hit_returns_cached_value_without_calling_target (+26) |
| `tests/primitives/adaptive/test_adaptive_fallback.py` | _ctx, _make_fallback, test_get_default_strategy_returns_baseline, test_primary_succeeds_returns_primary_result, test_primary_success_increments_primary_attempts (+21) |
| `tests/primitives/adaptive/test_adaptive_timeout.py` | _ctx, _make_timeout, test_execute_success_records_latency, test_execute_success_tracks_context_latency, test_execute_multiple_successes_accumulate (+18) |
| `ttadev/primitives/adaptive/retry.py` | _execute_retry_with_tracing, _consider_error_specific_strategy, _context_extractor, _consider_reducing_retries, _consider_faster_backoff (+7) |
| `ttadev/primitives/adaptive/cache.py` | _get_default_strategy, _consider_new_strategy, get_cache_stats, evict_expired, _get_hit_rate (+2) |
| `ttadev/primitives/adaptive/base.py` | _execute_impl, _select_strategy, _execute_with_strategy, _get_default_strategy, _learn_from_execution (+2) |
| `ttadev/primitives/adaptive/fallback.py` | _get_default_strategy, _consider_new_strategy, get_fallback_stats |
| `ttadev/primitives/adaptive/exceptions.py` | AdaptiveError, LearningError, StrategyValidationError |
| `ttadev/primitives/adaptive/timeout.py` | _consider_new_strategy, get_timeout_stats |

## Entry Points

Start here when exploring this area:

- **`get_fallback_stats`** (Function) — `ttadev/primitives/adaptive/fallback.py:395`
- **`test_get_default_strategy_returns_baseline`** (Function) — `tests/primitives/adaptive/test_adaptive_fallback.py:135`
- **`test_primary_succeeds_returns_primary_result`** (Function) — `tests/primitives/adaptive/test_adaptive_fallback.py:167`
- **`test_primary_success_increments_primary_attempts`** (Function) — `tests/primitives/adaptive/test_adaptive_fallback.py:183`
- **`test_primary_fail_first_fallback_succeeds`** (Function) — `tests/primitives/adaptive/test_adaptive_fallback.py:202`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `AdaptiveError` | Class | `ttadev/primitives/adaptive/exceptions.py` | 35 |
| `LearningError` | Class | `ttadev/primitives/adaptive/exceptions.py` | 45 |
| `StrategyValidationError` | Class | `ttadev/primitives/adaptive/exceptions.py` | 61 |
| `get_fallback_stats` | Function | `ttadev/primitives/adaptive/fallback.py` | 395 |
| `test_get_default_strategy_returns_baseline` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 135 |
| `test_primary_succeeds_returns_primary_result` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 167 |
| `test_primary_success_increments_primary_attempts` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 183 |
| `test_primary_fail_first_fallback_succeeds` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 202 |
| `test_primary_fail_second_fallback_succeeds_when_first_fails` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 219 |
| `test_fallback_latency_recorded_on_success` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 236 |
| `test_all_fail_raises_last_exception` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 256 |
| `test_all_fail_primary_failure_counted` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 268 |
| `test_unknown_fallback_key_skipped_and_next_tried` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 290 |
| `test_unknown_fallback_key_all_unknown_raises` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 308 |
| `test_context_stats_initialized_on_first_access` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 328 |
| `test_context_stats_failure_tracked` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 346 |
| `test_get_fallback_stats_empty` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 380 |
| `test_get_fallback_stats_with_data` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 399 |
| `test_get_fallback_stats_best_order_by_success_rate` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 422 |
| `test_get_fallback_stats_strategies_included` | Function | `tests/primitives/adaptive/test_adaptive_fallback.py` | 440 |

## How to Explore

1. `gitnexus_context({name: "get_fallback_stats"})` — see callers and callees
2. `gitnexus_query({query: "adaptive"})` — find related execution flows
3. Read key files listed above for implementation details
