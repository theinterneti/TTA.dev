---
name: safety
description: "Skill for the Safety area of TTA.dev. 24 symbols across 2 files."
---

# Safety

24 symbols | 2 files | Cohesion: 92%

## When to Use

- Working with code in `tests/`
- Understanding how execute, test_none_severity_returns_input_unchanged, test_low_without_handler_returns_input_unchanged work
- Modifying safety-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/primitives/safety/test_safety_gate_primitive.py` | _ctx, _scorer, test_none_severity_returns_input_unchanged, test_low_without_handler_returns_input_unchanged, test_high_without_handler_returns_input_unchanged (+18) |
| `ttadev/primitives/safety/safety_gate_primitive.py` | execute |

## Entry Points

Start here when exploring this area:

- **`execute`** (Function) — `ttadev/primitives/safety/safety_gate_primitive.py:229`
- **`test_none_severity_returns_input_unchanged`** (Function) — `tests/primitives/safety/test_safety_gate_primitive.py:66`
- **`test_low_without_handler_returns_input_unchanged`** (Function) — `tests/primitives/safety/test_safety_gate_primitive.py:72`
- **`test_high_without_handler_returns_input_unchanged`** (Function) — `tests/primitives/safety/test_safety_gate_primitive.py:78`
- **`test_critical_without_block_returns_input_when_no_handler`** (Function) — `tests/primitives/safety/test_safety_gate_primitive.py:84`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `execute` | Function | `ttadev/primitives/safety/safety_gate_primitive.py` | 229 |
| `test_none_severity_returns_input_unchanged` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 66 |
| `test_low_without_handler_returns_input_unchanged` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 72 |
| `test_high_without_handler_returns_input_unchanged` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 78 |
| `test_critical_without_block_returns_input_when_no_handler` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 84 |
| `test_low_handler_called_with_correct_input` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 100 |
| `test_medium_handler_receives_original_input` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 111 |
| `test_only_matching_handler_is_called` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 127 |
| `test_unregistered_severity_skips_all_handlers` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 143 |
| `test_critical_with_block_raises_escalated_error` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 161 |
| `test_critical_handler_called_before_raise` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 174 |
| `test_critical_no_block_returns_handler_result` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 187 |
| `test_lower_severities_never_raise` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 199 |
| `test_service_record_called_on_critical` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 238 |
| `test_service_failure_does_not_suppress_escalation` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 256 |
| `test_no_service_call_on_non_critical` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 271 |
| `test_no_service_does_not_raise_on_critical` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 283 |
| `test_scorer_exception_propagates` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 301 |
| `test_handler_exception_propagates` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 307 |
| `test_pipeline_passes_through_on_safe_input` | Function | `tests/primitives/safety/test_safety_gate_primitive.py` | 327 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 2 calls |

## How to Explore

1. `gitnexus_context({name: "execute"})` — see callers and callees
2. `gitnexus_query({query: "safety"})` — find related execution flows
3. Read key files listed above for implementation details
