---
name: testing
description: "Skill for the Testing area of TTA.dev. 21 symbols across 4 files."
---

# Testing

21 symbols | 4 files | Cohesion: 76%

## When to Use

- Working with code in `tests/`
- Understanding how test_mock_llm_receives_llm_request, execute, assert_called work
- Modifying testing-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/primitives/testing/test_mocks.py` | test_tracks_call_count, test_assert_called_passes_after_call, test_assert_called_with_passes, test_assert_called_with_context, test_assert_called_with_wrong_input_fails (+7) |
| `ttadev/primitives/testing/mocks.py` | execute, assert_called, assert_called_with, assert_called_once, execute (+1) |
| `tests/unit/test_example_auto_pr_reviewer.py` | _make_subprocess_result, test_mock_llm_receives_llm_request |
| `tests/observability/test_span_pipeline.py` | test_cache_miss_executes_inner_primitive |

## Entry Points

Start here when exploring this area:

- **`test_mock_llm_receives_llm_request`** (Function) — `tests/unit/test_example_auto_pr_reviewer.py:403`
- **`execute`** (Function) — `ttadev/primitives/testing/mocks.py:56`
- **`assert_called`** (Function) — `ttadev/primitives/testing/mocks.py:85`
- **`assert_called_with`** (Function) — `ttadev/primitives/testing/mocks.py:93`
- **`test_tracks_call_count`** (Function) — `tests/primitives/testing/test_mocks.py:27`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_mock_llm_receives_llm_request` | Function | `tests/unit/test_example_auto_pr_reviewer.py` | 403 |
| `execute` | Function | `ttadev/primitives/testing/mocks.py` | 56 |
| `assert_called` | Function | `ttadev/primitives/testing/mocks.py` | 85 |
| `assert_called_with` | Function | `ttadev/primitives/testing/mocks.py` | 93 |
| `test_tracks_call_count` | Function | `tests/primitives/testing/test_mocks.py` | 27 |
| `test_assert_called_passes_after_call` | Function | `tests/primitives/testing/test_mocks.py` | 72 |
| `test_assert_called_with_passes` | Function | `tests/primitives/testing/test_mocks.py` | 97 |
| `test_assert_called_with_context` | Function | `tests/primitives/testing/test_mocks.py` | 103 |
| `test_assert_called_with_wrong_input_fails` | Function | `tests/primitives/testing/test_mocks.py` | 109 |
| `test_reset_clears_tracking` | Function | `tests/primitives/testing/test_mocks.py` | 116 |
| `test_cache_miss_executes_inner_primitive` | Function | `tests/observability/test_span_pipeline.py` | 348 |
| `assert_called_once` | Function | `ttadev/primitives/testing/mocks.py` | 89 |
| `test_assert_called_once_passes` | Function | `tests/primitives/testing/test_mocks.py` | 83 |
| `test_assert_called_once_fails_on_multiple` | Function | `tests/primitives/testing/test_mocks.py` | 89 |
| `execute` | Function | `ttadev/primitives/testing/mocks.py` | 182 |
| `test_assert_primitive_called_passes` | Function | `tests/primitives/testing/test_mocks.py` | 140 |
| `test_reset_mocks_resets_tracked_mocks` | Function | `tests/primitives/testing/test_mocks.py` | 169 |
| `assert_primitive_called` | Function | `ttadev/primitives/testing/mocks.py` | 198 |
| `test_assert_primitive_called_with_times` | Function | `tests/primitives/testing/test_mocks.py` | 147 |
| `test_assert_primitive_called_wrong_times_fails` | Function | `tests/primitives/testing/test_mocks.py` | 155 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Observability | 1 calls |
| Performance | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_mock_llm_receives_llm_request"})` — see callers and callees
2. `gitnexus_query({query: "testing"})` — find related execution flows
3. Read key files listed above for implementation details
