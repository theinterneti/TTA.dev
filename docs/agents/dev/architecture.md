# TTA.dev Architecture Reference

## What TTA.dev is

A Python monorepo of **composable workflow primitives** for building reliable AI applications.
The primitives system is the core product; everything else (L0 agents, MCP server, CLI, observability)
is built on top of it.

## Package layout

```
ttadev/
  primitives/         # Core primitives (DO NOT add non-primitive logic here)
    core/             # WorkflowPrimitive base, WorkflowContext, LambdaPrimitive
    recovery/         # Retry, Timeout, CircuitBreaker, Fallback, Compensation
    coordination/     # Sequential, Parallel, Router
    performance/      # Cache, Memory, benchmarking
    integrations/     # LLM provider primitives (Groq, OpenAI, Ollama, etc.)
    llm/              # ModelRouterPrimitive, TaskProfile, chat adapters
    observability/    # OTel span/metric primitives (wraps ttadev.observability)
    mcp_server/       # 43-tool MCP server for coding agents (~2600 lines — target for split)
    testing/          # MockPrimitive, test utilities
  agents/             # L0 runtime dev agents (AgentSpec, AgentPrimitive, registry)
  observability/      # OpenTelemetry + local dashboard server
  control_plane/      # L0 task/run/lease state (JSON-backed)
  cli/                # `tta` CLI subcommands
  workflows/          # High-level workflow compositions
  integrations/       # External service integrations (auth, DB, Langfuse, OpenHands)
```

## Primitive composition

Two operators wire primitives into workflows:

| Operator | Meaning | When to use |
|---|---|---|
| `>>` | Sequential — output of left becomes input of right | Ordered pipeline steps |
| `\|` | Parallel — same input to all branches | Fan-out / race / aggregation |

```python
from ttadev.primitives.core.base import WorkflowContext, LambdaPrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive
from ttadev.primitives.recovery.timeout import TimeoutPrimitive

# Build the workflow graph — no I/O yet
workflow = TimeoutPrimitive(
    RetryPrimitive(LambdaPrimitive(call_api), max_retries=3),
    timeout_seconds=30.0,
)

# Execute — all I/O happens here
result = await workflow.execute(data, WorkflowContext(workflow_id="my-task"))
```

**Rule:** Build the graph first, execute second. Never mix construction and execution.

## WorkflowContext

The single shared object that flows through every primitive in a workflow run.

```python
@dataclass
class WorkflowContext:
    workflow_id: str        # Unique per execution
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_span: Any = None  # OTel span, if set
```

- **Never pass state via globals or module-level variables.** Use `WorkflowContext.metadata`.
- Primitives must not mutate context state owned by other primitives.

## LLM provider architecture

```
ModelRouterPrimitive
  └── selects best model via TaskProfile + benchmark data (aa_intelligence, aa_coding…)
       └── ModelRouterChatAdapter — wraps selected provider as ChatPrimitive
            └── concrete provider: GroqPrimitive | OpenAIPrimitive | OllamaPrimitive | …
```

Preferred pattern:
```python
from ttadev.agents import DeveloperAgent
from ttadev.primitives.llm import ModelRouterPrimitive

router = ModelRouterPrimitive(...)
agent = DeveloperAgent.with_router(router)   # DO NOT use DeveloperAgent(model=...)
```

See [llm-provider-strategy](../../../docs/agent-guides/llm-provider-strategy.md) for live provider defaults.

## L0 agent system

`ttadev/agents/` contains 7 specialist agents that operate on this repo itself:
`DeveloperAgent`, `DevOpsAgent`, `SecurityAgent`, `GitAgent`, `GitHubAgent`, `QAAgent`, `PerformanceAgent`.

Each agent is defined by an `AgentSpec` (role, system prompt, tools, handoff triggers, quality gates)
and executed by `AgentPrimitive` using the standard primitive protocol.

See [runtime/l0-roster.md](../runtime/l0-roster.md) for the full roster.
See [runtime/l0-agent-spec.md](../runtime/l0-agent-spec.md) for how to write/modify specs.

## Key anti-patterns

```python
# ❌ Manual retry loop
for attempt in range(3):
    try: result = await call()
    except: await asyncio.sleep(2 ** attempt)

# ✅ Use RetryPrimitive
result = await RetryPrimitive(LambdaPrimitive(call), max_retries=3).execute(data, ctx)

# ❌ Global state
_CURRENT_MODEL = "gpt-4"

# ✅ WorkflowContext
ctx.metadata["selected_model"] = "gpt-4"

# ❌ Hardcoded model name
agent = DeveloperAgent(model="gpt-4o")

# ✅ ModelRouter selects dynamically
agent = DeveloperAgent.with_router(router)
```

## Files known to exceed 500-line limit

| File | ~Lines | Action |
|---|---|---|
| `primitives/mcp_server/server.py` | ~2600 | Issue #352 |
| `workflows/service.py` | ~1661 | Issue #353 |
| `primitives/llm/transformer.py` | ~3177 | Issue #351 (highest priority) |

Do not add logic to these files until split issues are resolved.
