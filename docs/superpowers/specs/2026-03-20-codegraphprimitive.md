# CodeGraphPrimitive — Functional Specification

**Date:** 2026-03-20
**Status:** Approved
**Phase:** 2a of DevelopmentCycle Integration Design
**Parent spec:** docs/superpowers/specs/2026-03-20-development-cycle-integration-design.md

---

## What is this?

`CodeGraphPrimitive` is a typed, instrumented primitive that wraps the CodeGraphContext (CGC) MCP server.
It answers the question "what does this code touch, and what touches it?" — the Orient step in the
DevelopmentCycle loop. It accepts a `CodeGraphQuery` (target + list of operations to run) and returns
an `ImpactReport` summarising callers, dependencies, related tests, complexity, and risk level.

---

## User Journeys

### Journey 1 — Developer orients before editing a function

The developer (or Claude Code running the session-start skill) is about to modify
`RetryPrimitive._execute_impl`. They call `CodeGraphPrimitive` with:

```python
query = CodeGraphQuery(
    target="RetryPrimitive._execute_impl",
    operations=[CGCOp.get_relationships, CGCOp.find_tests, CGCOp.get_complexity],
)
report = await graph.execute(query, context)
# report.risk == "medium"
# report.callers == ["WorkflowOrchestrator._run_step", ...]
# report.related_tests == ["tests/test_retry_primitive.py", ...]
# report.summary == "RetryPrimitive._execute_impl is called by 3 internal callers..."
```

They read `report.summary` and `report.related_tests` to understand impact before touching the file.

### Journey 2 — QA agent validates test coverage before marking a PR ready

The QA agent queries CGC for all tests related to a changed module:

```python
query = CodeGraphQuery(target="CachePrimitive", operations=[CGCOp.find_tests])
report = await graph.execute(query, context)
# report.related_tests used to build the E2B validation run
```

### Journey 3 — DevelopmentCycle orchestrates Orient step automatically

`DevelopmentCycle` calls `CodeGraphPrimitive` internally as step 1 of the loop.
The returned `ImpactReport` is attached to context and consumed by the Write and Validate steps.
The developer sees only the final result; CGC is invisible infrastructure.

### Journey 4 — CGC is unavailable (server down or not configured)

The primitive degrades gracefully:
- Logs a warning with the error
- Returns an empty `ImpactReport` with `risk="low"`, empty lists, and
  `summary="CGC unavailable — orient step skipped"`
- Does NOT raise — the calling workflow continues unblocked

### Journey 5 — Power user runs a raw Cypher query

```python
query = CodeGraphQuery(
    target="",
    operations=[CGCOp.raw_cypher],
    cypher="MATCH (f:Function)-[:CALLS]->(g:Function {name: 'cleanup'}) RETURN f.name LIMIT 10",
)
report = await graph.execute(query, context)
# report.summary contains the raw Cypher result as formatted text
```

---

## The Five Operations (`CGCOp` enum)

| Name | CGC MCP tool | Returns |
|---|---|---|
| `find_code` | `mcp__codegraphcontext__find_code` | Locations of the target in the graph |
| `get_relationships` | `mcp__codegraphcontext__analyze_code_relationships` | Callers, callees, importers |
| `get_complexity` | `mcp__codegraphcontext__calculate_cyclomatic_complexity` | Numeric complexity score |
| `find_tests` | `mcp__codegraphcontext__find_code` with `test` heuristic | Related test file paths |
| `raw_cypher` | `mcp__codegraphcontext__execute_cypher_query` | Raw graph query result |

The `CodeGraphPrimitive.execute()` call runs all requested operations, collects their results,
derives a risk level, and synthesises a plain-English `summary` string.

---

## Input / Output Contract

```python
class CodeGraphQuery(TypedDict, total=False):
    target: str                # Required for all ops except raw_cypher. Function/class/file name.
    operations: list[CGCOp]    # Required. Which operations to run.
    depth: int                 # Optional (default 2). Graph traversal depth for relationships.
    cypher: str                # Required only for CGCOp.raw_cypher.

class ImpactReport(TypedDict):
    target: str
    callers: list[str]         # Direct callers of target
    dependencies: list[str]    # Modules/functions target imports or calls
    related_tests: list[str]   # Test file paths that exercise target
    complexity: float          # Cyclomatic complexity score (0.0 if not requested)
    risk: Literal["low", "medium", "high"]
    summary: str               # Human/LLM-readable paragraph
    cgc_available: bool        # False if CGC was unreachable
```

**Risk derivation rule:**
- `complexity >= 10` → `"high"`
- `complexity >= 5` OR `len(callers) >= 5` → `"medium"`
- Otherwise → `"low"`
- CGC unavailable → `"low"` (unknown = not blocked)

---

## Success Criteria

1. `CodeGraphPrimitive` extends `InstrumentedPrimitive[CodeGraphQuery, ImpactReport]`
2. Every `execute()` call emits an OTel span named `cgc.orient` with attributes: `target`, `operations`, `risk`, `cgc_available`
3. All 5 `CGCOp` values work end-to-end against the live CGC MCP server
4. When CGC is unreachable, the primitive returns a valid (empty) `ImpactReport` without raising
5. `related_tests` correctly uses a `test` path heuristic (filters `find_code` results to paths containing `/test` or starting with `test_`)
6. `summary` is a non-empty plain-English string for all successful queries
7. 100% test coverage using `MockPrimitive` or direct CGC MCP mocking — no live CGC calls in unit tests
8. `CodeGraphPrimitive` is exported from `ttadev/primitives/__init__.py` alongside other primitives
9. `CGCOp` enum and `ImpactReport` TypedDict are exported from `ttadev/primitives/__init__.py`

---

## Out of Scope

- **LLM-generated summaries** — `summary` is assembled from structured data, not an LLM call
- **Caching CGC results** — `CachePrimitive` can be composed externally if needed; not baked in
- **Writing to the code graph** — read-only; `mcp__codegraphcontext__add_code_to_graph` not wrapped
- **Repo management** (watch/unwatch/delete) — out of scope
- **Multi-repo aggregation** — single target at a time; fan-out is the caller's responsibility
- **`DevelopmentCycle` integration** — Phase 3; this spec covers the primitive only

---

## Edge Cases

| Case | Expected behaviour |
|---|---|
| `operations=[]` | Return empty `ImpactReport` immediately, `risk="low"` |
| `target=""` and no `raw_cypher` | Raise `ValueError("target is required for non-cypher operations")` |
| CGC returns no results for `find_code` | Empty lists, `complexity=0.0`, `risk="low"` |
| `raw_cypher` with no `cypher` field | Raise `ValueError("cypher query string is required for CGCOp.raw_cypher")` |
| CGC timeout | Treat as unavailable — return graceful empty report, log warning |
| `depth` > 5 | Clamp to 5, log warning (avoids graph explosions) |

---

## File Layout (for `/plan` phase)

| Path | Purpose |
|---|---|
| `ttadev/primitives/code_graph/__init__.py` | Package exports |
| `ttadev/primitives/code_graph/primitive.py` | `CodeGraphPrimitive` implementation |
| `ttadev/primitives/code_graph/types.py` | `CodeGraphQuery`, `ImpactReport`, `CGCOp` |
| `tests/primitives/code_graph/test_primitive.py` | Unit tests (all CGC calls mocked) |

---

## Open Questions

None — design decisions resolved in parent spec (2026-03-20).
