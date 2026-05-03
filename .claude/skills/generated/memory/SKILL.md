---
name: memory
description: "Skill for the Memory area of TTA.dev. 55 symbols across 7 files."
---

# Memory

55 symbols | 7 files | Cohesion: 57%

## When to Use

- Working with code in `tests/`
- Understanding how test_recall_empty_store, test_recall_matches_retained, test_recall_empty_query_raises work
- Modifying memory-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/primitives/memory/test_agent_memory.py` | test_recall_returns_memory_results, test_recall_raises_on_empty_query, test_retain_success, test_retain_raises_on_empty_content, test_retain_sync_passes_async_false (+12) |
| `tests/unit/test_agent_memory.py` | test_recall_empty_store, test_recall_matches_retained, test_recall_empty_query_raises, test_retain_success, test_retain_empty_raises (+6) |
| `tests/primitives/memory/test_client.py` | _make_response, test_recall_returns_memory_results, test_recall_passes_budget_and_types, test_recall_omits_types_when_none, test_recall_returns_empty_list_on_empty_results (+6) |
| `ttadev/primitives/memory/agent_memory.py` | recall, retain, is_available, get_directives, get_mental_model |
| `ttadev/primitives/memory/client.py` | recall, _bank_url, get_mental_model, retain, get_directives |
| `tests/primitives/memory/test_in_memory_backend.py` | test_store_and_retrieve_fact, test_namespace_isolation_via_separate_backends, test_build_context_prefix_combines_directives_and_recall |
| `ttadev/primitives/mcp_server/tools/observability.py` | memory_recall, memory_retain, memory_build_context |

## Entry Points

Start here when exploring this area:

- **`test_recall_empty_store`** (Function) — `tests/unit/test_agent_memory.py:24`
- **`test_recall_matches_retained`** (Function) — `tests/unit/test_agent_memory.py:30`
- **`test_recall_empty_query_raises`** (Function) — `tests/unit/test_agent_memory.py:37`
- **`recall`** (Function) — `ttadev/primitives/memory/agent_memory.py:53`
- **`test_store_and_retrieve_fact`** (Function) — `tests/primitives/memory/test_in_memory_backend.py:185`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_recall_empty_store` | Function | `tests/unit/test_agent_memory.py` | 24 |
| `test_recall_matches_retained` | Function | `tests/unit/test_agent_memory.py` | 30 |
| `test_recall_empty_query_raises` | Function | `tests/unit/test_agent_memory.py` | 37 |
| `recall` | Function | `ttadev/primitives/memory/agent_memory.py` | 53 |
| `test_store_and_retrieve_fact` | Function | `tests/primitives/memory/test_in_memory_backend.py` | 185 |
| `test_namespace_isolation_via_separate_backends` | Function | `tests/primitives/memory/test_in_memory_backend.py` | 255 |
| `test_recall_returns_memory_results` | Function | `tests/primitives/memory/test_agent_memory.py` | 40 |
| `test_recall_raises_on_empty_query` | Function | `tests/primitives/memory/test_agent_memory.py` | 55 |
| `test_retain_success` | Function | `tests/unit/test_agent_memory.py` | 53 |
| `test_retain_empty_raises` | Function | `tests/unit/test_agent_memory.py` | 59 |
| `test_retain_async_flag` | Function | `tests/unit/test_agent_memory.py` | 65 |
| `retain` | Function | `ttadev/primitives/memory/agent_memory.py` | 76 |
| `test_build_context_prefix_combines_directives_and_recall` | Function | `tests/primitives/memory/test_in_memory_backend.py` | 235 |
| `test_retain_success` | Function | `tests/primitives/memory/test_agent_memory.py` | 75 |
| `test_retain_raises_on_empty_content` | Function | `tests/primitives/memory/test_agent_memory.py` | 85 |
| `test_retain_sync_passes_async_false` | Function | `tests/primitives/memory/test_agent_memory.py` | 94 |
| `test_is_available_with_in_memory_backend` | Function | `tests/unit/test_agent_memory.py` | 17 |
| `is_available` | Function | `ttadev/primitives/memory/agent_memory.py` | 49 |
| `test_is_available_delegates_to_client` | Function | `tests/primitives/memory/test_agent_memory.py` | 192 |
| `test_is_available_false_when_client_unavailable` | Function | `tests/primitives/memory/test_agent_memory.py` | 199 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Memory_build_context → Get_directives` | cross_community | 3 |
| `Memory_build_context → Recall` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Unit | 17 calls |

## How to Explore

1. `gitnexus_context({name: "test_recall_empty_store"})` — see callers and callees
2. `gitnexus_query({query: "memory"})` — find related execution flows
3. Read key files listed above for implementation details
