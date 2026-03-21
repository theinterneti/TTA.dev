---
category: mental-models
date: 2026-03-20
component: integrations
severity: high
tags: [mental-model, e2b, hindsight, cgc, llm-providers]
---
# Mental Model: Integrations Layer

## E2B (Code Execution)

SDK: `e2b-code-interpreter==2.5.0` (core dep in pyproject.toml).
Key: `E2B_API_KEY` in `.env` (also reads `E2B_KEY`).
Primitive: `ttadev/primitives/integrations/e2b_primitive.py` → `CodeExecutionPrimitive`.
Alias: `E2BPrimitive = CodeExecutionPrimitive`.

Free tier: 20 concurrent Firecracker microVMs, 8 vCPU each, 1-hour sessions.
Auto-rotates sessions at 55 minutes. 150ms startup.
Runtime: Python 3.13.12. Confirmed working 2026-03-19.

Usage:
```python
async with CodeExecutionPrimitive() as executor:
    result = await executor.execute({"code": "print(42)"}, ctx)
    # result["output"] == "42\n", result["success"] == True
```

## Hindsight (Cross-session Memory)

Docker: API port 8888, dashboard port 9999. Volume: ~/.local/share/hindsight.
Model: HINDSIGHT_LLM_MODEL env var (currently google/gemma-3n-e4b-it:free).
MCP: configured in ~/.claude.json as HTTP transport at http://localhost:8888/mcp.

Known issue: if container exits uncleanly, delete
~/.local/share/hindsight/instances/hindsight/data/postmaster.pid before restarting.

PersistentMemory in ttadev/workflows/memory.py wraps Hindsight with graceful degradation.
Bank for this project: `tta-dev`.

## CodeGraphContext (CGC)

Version: 0.3.1 globally at ~/.local/bin/cgc.
Graph: 3 repos, 1278 files, 13098 functions, 2319 classes (as of 2026-03-17).
MCP: configured in ~/.claude.json as stdio transport.

Key MCP tools: find_code, analyze_code_relationships, calculate_cyclomatic_complexity,
find_dead_code, execute_cypher_query, get_repository_stats.

No TTA.dev primitive yet — Phase 2 will add CodeGraphPrimitive.

## LLM provider selection

`get_llm_client()` in `ttadev/workflows/llm_provider.py` (also `ttadev/integrations/`):
1. LLM_FORCE_PROVIDER=ollama → Ollama
2. OPENROUTER_API_KEY set → OpenRouter (model from HINDSIGHT_LLM_MODEL)
3. Else → Ollama (qwen2.5:7b, http://localhost:11434/v1)

---
**Created:** 2026-03-20
**Verified:** [x] Yes
