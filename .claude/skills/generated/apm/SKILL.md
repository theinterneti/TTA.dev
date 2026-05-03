---
name: apm
description: "Skill for the Apm area of TTA.dev. 21 symbols across 6 files."
---

# Apm

21 symbols | 6 files | Cohesion: 40%

## When to Use

- Working with code in `tests/`
- Understanding how get, test_execute_propagates_exception_when_apm_disabled, test_execute_error_increments_error_counter work
- Modifying apm-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/primitives/apm/test_apm_instrumented.py` | get, test_execute_propagates_exception_when_apm_disabled, test_execute_error_increments_error_counter, test_init_metrics_creates_counter_and_histogram, make_context (+11) |
| `tests/unit/test_primitives_apm.py` | test_is_apm_enabled_false_when_not_initialized |
| `ttadev/primitives/apm/setup.py` | is_apm_enabled |
| `ttadev/primitives/apm/decorators.py` | async_wrapper |
| `ttadev/primitives/core/base.py` | WorkflowPrimitive |
| `ttadev/primitives/apm/instrumented.py` | APMWorkflowPrimitive |

## Entry Points

Start here when exploring this area:

- **`get`** (Function) — `tests/primitives/apm/test_apm_instrumented.py:22`
- **`test_execute_propagates_exception_when_apm_disabled`** (Function) — `tests/primitives/apm/test_apm_instrumented.py:61`
- **`test_execute_error_increments_error_counter`** (Function) — `tests/primitives/apm/test_apm_instrumented.py:195`
- **`test_init_metrics_creates_counter_and_histogram`** (Function) — `tests/primitives/apm/test_apm_instrumented.py:229`
- **`make_context`** (Function) — `tests/primitives/apm/test_apm_instrumented.py:41`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `WorkflowPrimitive` | Class | `ttadev/primitives/core/base.py` | 443 |
| `APMWorkflowPrimitive` | Class | `ttadev/primitives/apm/instrumented.py` | 12 |
| `get` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 22 |
| `test_execute_propagates_exception_when_apm_disabled` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 61 |
| `test_execute_error_increments_error_counter` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 195 |
| `test_init_metrics_creates_counter_and_histogram` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 229 |
| `make_context` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 41 |
| `test_execute_returns_impl_result_when_apm_disabled` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 54 |
| `test_execute_falls_through_when_no_tracer` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 93 |
| `test_execute_success_records_histogram` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 163 |
| `test_execute_success_records_span_attributes` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 129 |
| `test_execute_error_records_error_attributes` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 178 |
| `test_context_attributes_added_to_span` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 269 |
| `test_execute_success_increments_counter` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 145 |
| `test_execute_error_records_histogram_on_failure` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 214 |
| `test_span_created_with_correct_name` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 252 |
| `test_is_apm_enabled_false_when_not_initialized` | Function | `tests/unit/test_primitives_apm.py` | 68 |
| `is_apm_enabled` | Function | `ttadev/primitives/apm/setup.py` | 161 |
| `async_wrapper` | Function | `ttadev/primitives/apm/decorators.py` | 28 |
| `_make_tracer_mock` | Function | `tests/primitives/apm/test_apm_instrumented.py` | 112 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 3 calls |

## How to Explore

1. `gitnexus_context({name: "get"})` — see callers and callees
2. `gitnexus_query({query: "apm"})` — find related execution flows
3. Read key files listed above for implementation details
