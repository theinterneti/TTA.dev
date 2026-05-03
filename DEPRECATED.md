# Deprecated Primitives

> These modules are scheduled for archival as part of the TTA.dev Slim Down.
> Each has an OSS replacement that does the job better.
> See the [40-hour plan](plan.md) for the full migration strategy.

## Status Key

- 🔴 **Archive** — Moving to `_archive/` at repo root. No direct replacement needed in TTA.dev.
- 🟡 **Shim** — Temporarily kept with thin wrapper delegating to OSS. Will be removed after TTA app migrates.
- 🟢 **Keep** — Genuinely unique code with no OSS equivalent.

## Modules Being Archived (🔴)

| Module | LOC | OSS Replacement | Notes |
|--------|-----|-----------------|-------|
| `primitives/adaptive/` | 3,024 | None (research code) | Self-learning retry — over-engineering |
| `primitives/ace/` | 1,658 | E2B SDK directly | E2B has its own SDK |
| `primitives/analysis/` | 5,257 | `ast` stdlib + Ruff | Meta-tool analyzing primitives being deleted |
| `primitives/apm/` | 556 | Langfuse | `litellm.callbacks = ["langfuse_otel"]` |
| `primitives/benchmarking/` | 966 | pytest-benchmark | Standard tool |
| `primitives/code_graph/` | 465 | CGC MCP server | Already running |
| `primitives/collaboration/` | 460 | OpenHands SDK | Multi-agent via OpenHands |
| `primitives/config/` | 947 | Pydantic Settings | Already using Pydantic |
| `primitives/coordination/` | 645 | Redis directly | Thin wrapper adds no value |
| `primitives/extensions/` | 96 | None (dead code) | Plugin system for code being removed |
| `primitives/lifecycle/` | 2,109 | GitHub Actions + pre-commit | Stage gates belong in CI/CD |
| `primitives/memory/` | 492 | Hindsight MCP server | Already using Hindsight |
| `primitives/orchestration/` | 960 | PydanticAI / LangGraph | TTA already depends on LangGraph |
| `primitives/package_managers/` | 873 | `uv` / `pip` directly | |
| `primitives/performance/` | 686 | cProfile / py-spy | Standard profiling tools |
| `primitives/persistence/` | 67 | JSON stdlib / SQLAlchemy | |
| `primitives/research/` | 663 | None (not library code) | Research notebooks don't belong in a library |
| `primitives/speckit/` | 3,199 | Skills/prompts | SDD workflow as SKILL.md, not Python |
| `primitives/streaming/` | 215 | LiteLLM streaming | Built into LiteLLM |

**Subtotal: ~22,338 LOC being archived**

## Modules with Temporary Shims (🟡)

| Module | LOC | OSS Replacement | Shim Strategy |
|--------|-----|-----------------|---------------|
| `primitives/llm/` | 13,145 | LiteLLM Router | Keep `LLMRequest`/`LLMResponse` types. Delete routing, model catalog, cost tracking. New: `ttadev/llm.py` (~100 LOC) |
| `primitives/recovery/` | 1,776 | LiteLLM (LLM retry) + Tenacity (general retry) | `RetryPrimitive` → `tenacity.retry`. `CircuitBreakerPrimitive` → LiteLLM `allowed_fails`. `TimeoutPrimitive` → `asyncio.timeout` |
| `primitives/observability/` | 1,688 | Langfuse + OpenTelemetry SDK | Keep minimal tracing hooks that agents need. Delete custom wrappers |
| `primitives/integrations/` | 2,954 | Direct SDKs (E2B, HuggingFace, OpenRouter) | Keep `openhands_primitive.py` (529 LOC) — genuinely useful |
| `primitives/safety/` | 459 | Guardrails AI / NeMo Guardrails | Evaluate before archiving |

**Subtotal: ~20,022 LOC → shim to ~2,000 LOC → eventually ~500 LOC**

## Modules Being Kept (🟢)

| Module | LOC | Why |
|--------|-----|-----|
| `primitives/core/base.py` | ~200 | `WorkflowContext` + `>>` operator — used everywhere |
| `primitives/integrations/openhands_primitive.py` | 529 | Production-ready OpenHands wrapper, 28 tests, OTel |
| `primitives/mcp_server/` | 2,782 | MCP tools = the agent interface to TTA.dev |
| `primitives/testing/` | 227 | `MockPrimitive` — useful test helper |
| `control_plane/` | ~800 | L0 coordination — unique, needed for multi-agent |

**Subtotal: ~4,538 LOC kept**

## Migration Timeline

1. **Phase 2**: Create `ttadev/llm.py` wrapper + compatibility shims
2. **Phase 3A**: Rewrite `primitives/__init__.py` exports
3. **Phase 3B**: Archive 🔴 modules + matching tests
4. **Phase 3C**: Clean 🟢 modules, verify tests
5. **Phase 4**: Update TTA app to use new APIs
6. **Post-migration**: Remove 🟡 shims once TTA app is fully migrated

## Adding New Code

Before writing ANY new Python code in TTA.dev, check:
1. Does LiteLLM already do this? → Use LiteLLM
2. Does Langfuse already do this? → Use Langfuse
3. Does OpenHands already do this? → Use OpenHands
4. Does Tenacity already do this? → Use Tenacity
5. Is this a standard library feature? → Use stdlib
6. Only then: write custom code
