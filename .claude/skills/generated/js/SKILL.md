---
name: js
description: "Skill for the Js area of TTA.dev. 48 symbols across 10 files."
---

# Js

48 symbols | 10 files | Cohesion: 73%

## When to Use

- Working with code in `ttadev/`
- Understanding how json, renderRows, add work
- Modifying js-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ttadev/observability/dashboard/js/app.js` | _switchTab, _activateLiveTab, _activateCostTab, render, _activateFleetTab (+16) |
| `ttadev/observability/dashboard/js/session-detail.js` | init, _loadSession, _render, renderRows, _renderEmpty (+3) |
| `ttadev/observability/dashboard/js/session-tree.js` | _render, _makeProjectGroup, init, _load, _prependSession (+3) |
| `ttadev/observability/dashboard/js/cgc-graph.js` | init, _loadGraph, _renderGraph |
| `ttadev/observability/dashboard/js/workflow-dag.js` | _renderDag, _renderGraph |
| `ttadev/ui/static/js/code-graph.js` | loadGraph, renderGraph |
| `tests/unit/test_models_cmd.py` | json |
| `ttadev/primitives/persistence/repository.py` | add |
| `ttadev/ui/static/graph.js` | searchGraph |
| `ttadev/skills/src/tta_skill_primitives/registry.py` | has |

## Entry Points

Start here when exploring this area:

- **`json`** (Function) — `tests/unit/test_models_cmd.py:123`
- **`renderRows`** (Function) — `ttadev/observability/dashboard/js/session-detail.js:97`
- **`add`** (Function) — `ttadev/primitives/persistence/repository.py:12`
- **`has`** (Function) — `ttadev/skills/src/tta_skill_primitives/registry.py:99`
- **`_renderDag`** (Method) — `ttadev/observability/dashboard/js/workflow-dag.js:67`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `json` | Function | `tests/unit/test_models_cmd.py` | 123 |
| `renderRows` | Function | `ttadev/observability/dashboard/js/session-detail.js` | 97 |
| `add` | Function | `ttadev/primitives/persistence/repository.py` | 12 |
| `has` | Function | `ttadev/skills/src/tta_skill_primitives/registry.py` | 99 |
| `_renderDag` | Method | `ttadev/observability/dashboard/js/workflow-dag.js` | 67 |
| `_renderGraph` | Method | `ttadev/observability/dashboard/js/workflow-dag.js` | 95 |
| `init` | Method | `ttadev/observability/dashboard/js/cgc-graph.js` | 17 |
| `_loadGraph` | Method | `ttadev/observability/dashboard/js/cgc-graph.js` | 60 |
| `_renderGraph` | Method | `ttadev/observability/dashboard/js/cgc-graph.js` | 101 |
| `init` | Method | `ttadev/observability/dashboard/js/session-detail.js` | 18 |
| `_loadSession` | Method | `ttadev/observability/dashboard/js/session-detail.js` | 35 |
| `_render` | Method | `ttadev/observability/dashboard/js/session-detail.js` | 70 |
| `_renderEmpty` | Method | `ttadev/observability/dashboard/js/session-detail.js` | 118 |
| `_buildMetrics` | Method | `ttadev/observability/dashboard/js/session-detail.js` | 136 |
| `_render` | Method | `ttadev/observability/dashboard/js/session-tree.js` | 34 |
| `_makeProjectGroup` | Method | `ttadev/observability/dashboard/js/session-tree.js` | 70 |
| `init` | Method | `ttadev/observability/dashboard/js/session-tree.js` | 14 |
| `_load` | Method | `ttadev/observability/dashboard/js/session-tree.js` | 20 |
| `_prependSession` | Method | `ttadev/observability/dashboard/js/session-tree.js` | 142 |
| `_makeAllItem` | Method | `ttadev/observability/dashboard/js/session-tree.js` | 99 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Init → Add` | cross_community | 6 |
| `Init → _escapeHtml` | cross_community | 5 |
| `Init → Add` | cross_community | 5 |
| `Init → _should_attempt_reset` | cross_community | 5 |
| `Init → _on_success` | cross_community | 5 |
| `Init → _on_failure` | cross_community | 5 |
| `Init → Has` | cross_community | 4 |
| `Init → Set` | cross_community | 4 |
| `Init → _relativeTime` | cross_community | 4 |
| `Init → _duration` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Recovery | 3 calls |
| Unit | 1 calls |

## How to Explore

1. `gitnexus_context({name: "json"})` — see callers and callees
2. `gitnexus_query({query: "js"})` — find related execution flows
3. Read key files listed above for implementation details
