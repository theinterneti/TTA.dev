# Plan: Phase 2 — Role-Based Agent System

**Phase:** SDD Phase 2 (Technical Plan)
**Status:** Draft — awaiting sign-off
**Spec:** [phase2-agent-system.md](phase2-agent-system.md)
**Date:** 2026-03-19

---

## Affected Packages

| Package | Change |
|---------|--------|
| `ttadev` | Primary — all new agent code lives here |
| `ttadev.primitives.core` | `WorkflowContext` gains `spawn_agent()` |
| `ttadev.primitives.integrations` | LLM primitives adopt `ChatPrimitive` protocol |
| `ttadev.cli` | New `agent` subcommand group |

**No new external dependencies.** The `anthropic` SDK is already in `pyproject.toml`.

---

## Pre-existing State (Important)

`ttadev/agents/` exists as a directory but has no `__init__.py` — it is not currently a Python package. It contains two **orphaned sub-packages** with their own `pyproject.toml` files:

- `ttadev/agents/context/` — `universal-agent-context` (v1.0.0): has `AgentCoordinationPrimitive`, `AgentHandoffPrimitive`, `AgentMemoryPrimitive`
- `ttadev/agents/coordination/` — `tta-agent-coordination` (v1.0.0): appears empty at the module level

Neither is installed in the venv. Both import from `primitives.core.base` (stale path). **These are tech debt.** This plan does not integrate them. A follow-up task will evaluate them for removal or proper integration.

---

## New Modules

### `ttadev/agents/` — make it a package

```
ttadev/agents/
├── __init__.py          # package + public exports
├── protocol.py          # ChatPrimitive protocol (structural typing)
├── spec.py              # AgentSpec, AgentTool, ToolRule, QualityGate, HandoffTrigger
├── task.py              # AgentTask, AgentResult, Artifact
├── base.py              # AgentPrimitive (wraps ChatPrimitive with AgentSpec)
├── tool_call_loop.py    # ToolCallLoop primitive
├── registry.py          # AgentRegistry, global instance, contextvars override
├── router.py            # AgentRouterPrimitive
├── developer.py         # DeveloperAgent (first concrete spec)
├── context/             # (existing orphaned sub-package — untouched)
└── coordination/        # (existing orphaned sub-package — untouched)
```

### `ttadev/cli/agent.py` — CLI subcommand

---

## Module Design

### `protocol.py` — `ChatPrimitive`

A `typing.Protocol` that any model must satisfy to be used inside `AgentPrimitive`:

```python
class ChatMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatPrimitive(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str: ...
```

Existing LLM primitives (`AnthropicPrimitive`, `GoogleAIStudioPrimitive`, etc.) will gain a `chat()` adapter method that translates to their native request/response types. This is non-breaking — `execute()` is unchanged.

---

### `spec.py` — `AgentSpec` and supporting types

```python
class ToolRule(str, Enum):
    ALWAYS = "always"
    WHEN_INSTRUCTED = "when_instructed"
    NEVER = "never"

@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    rule: ToolRule

@dataclass(frozen=True)
class QualityGate:
    name: str
    check: Callable[[AgentResult], bool]
    error_message: str

@dataclass(frozen=True)
class HandoffTrigger:
    condition: Callable[[AgentTask], bool]
    target_agent: str        # registry name
    reason: str

@dataclass(frozen=True)
class AgentSpec:
    name: str
    role: str
    system_prompt: str
    capabilities: list[str]
    tools: list[AgentTool]
    quality_gates: list[QualityGate]
    handoff_triggers: list[HandoffTrigger]
```

---

### `task.py` — `AgentTask` and `AgentResult`

```python
@dataclass
class Artifact:
    name: str
    content: str
    artifact_type: str           # "code", "test", "diff", "report"

@dataclass
class AgentTask:
    instruction: str
    context: dict[str, Any]
    constraints: list[str]
    agent_hint: str | None = None

@dataclass
class AgentResult:
    agent_name: str
    response: str
    artifacts: list[Artifact]
    suggestions: list[str]
    spawned_agents: list[str]
    quality_gates_passed: bool
    confidence: float            # 0.0–1.0
```

---

### `base.py` — `AgentPrimitive`

Extends `InstrumentedPrimitive` (for automatic observability tracing):

```python
class AgentPrimitive(InstrumentedPrimitive[AgentTask, AgentResult]):
    def __init__(self, spec: AgentSpec, model: ChatPrimitive): ...

    async def _execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
        # 1. Build messages from spec.system_prompt + task
        # 2. Check handoff_triggers — spawn sub-agents via ctx.spawn_agent()
        # 3. Run ToolCallLoop with tools matching ALWAYS + WHEN_INSTRUCTED rules
        # 4. Parse response into AgentResult
        # 5. Run quality_gates — raise if any fail
        # 6. Return result
```

`AgentPrimitive` self-registers in `AgentRegistry` on first instantiation.

---

### `tool_call_loop.py` — `ToolCallLoop`

A minimal primitive that handles the LLM function-calling conversation loop:

```python
class ToolCallLoop(InstrumentedPrimitive[ToolCallRequest, str]):
    """Runs the model → tool call → result → model loop until completion.

    Inputs: initial messages, tool definitions, model (ChatPrimitive)
    Output: final text response after all tool calls are resolved
    Max iterations: configurable (default 10) to prevent infinite loops
    """
```

This is intentionally generic — it works with any `ChatPrimitive` and any tool set, not just agents. Future non-agent uses are expected.

---

### `registry.py` — `AgentRegistry`

```python
_registry_var: ContextVar[AgentRegistry | None] = ContextVar("agent_registry", default=None)

class AgentRegistry:
    def register(self, agent_class: type[AgentPrimitive]) -> None: ...
    def get(self, name: str) -> type[AgentPrimitive]: ...
    def all(self) -> list[type[AgentPrimitive]]: ...

# Global instance — populated by imports
_global_registry = AgentRegistry()

def get_registry() -> AgentRegistry:
    """Returns contextvar override if set, otherwise global registry."""
    return _registry_var.get() or _global_registry

# Test helper
@contextmanager
def override_registry(registry: AgentRegistry):
    token = _registry_var.set(registry)
    try:
        yield registry
    finally:
        _registry_var.reset(token)
```

---

### `router.py` — `AgentRouterPrimitive`

```python
class AgentRouterPrimitive(InstrumentedPrimitive[AgentTask, AgentResult]):
    def __init__(self, orchestrator: ChatPrimitive, registry: AgentRegistry | None = None):
        # registry defaults to get_registry() at call time (not init time)
        ...

    async def _execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
        # 1. If task.agent_hint is set and valid, use it directly
        # 2. Score agents by capability keyword match (fast, no LLM call)
        # 3. If top score margin > 0.7, dispatch without LLM
        # 4. Otherwise: ask orchestrator model to pick, passing agent names + capabilities
        # 5. Execute selected agent; return its AgentResult
```

---

### `developer.py` — `DeveloperAgent`

```python
DEVELOPER_SPEC = AgentSpec(
    name="developer",
    role="Senior Python Developer",
    system_prompt="""...""",   # Full system prompt: TTA.dev conventions,
                               # Python standards, ruff/pyright/pytest rules
    capabilities=[
        "code implementation",
        "code review",
        "debugging",
        "refactoring",
        "test writing",
    ],
    tools=[
        AgentTool("ruff", "Python linter", ToolRule.ALWAYS),
        AgentTool("pyright", "Type checker", ToolRule.ALWAYS),
        AgentTool("pytest", "Test runner", ToolRule.ALWAYS),
        AgentTool("git", "Version control", ToolRule.WHEN_INSTRUCTED),
    ],
    quality_gates=[
        QualityGate("ruff_passes", check_ruff, "Ruff lint failed on produced code"),
        QualityGate("pyright_passes", check_pyright, "Pyright type check failed"),
    ],
    handoff_triggers=[
        HandoffTrigger(is_security_task, "security", "Security review needed"),
        HandoffTrigger(is_devops_task, "devops", "Infrastructure/deployment task"),
        HandoffTrigger(is_pr_task, "github", "PR workflow task"),
    ],
)

class DeveloperAgent(AgentPrimitive):
    def __init__(self, model: ChatPrimitive):
        super().__init__(spec=DEVELOPER_SPEC, model=model)
```

---

## Changes to Existing Files

### `ttadev/primitives/core/base.py` — `WorkflowContext.spawn_agent()`

```python
async def spawn_agent(
    self,
    agent_name: str,
    task: "AgentTask",
) -> "AgentResult":
    """Spawn a sub-agent as a child span of the current workflow."""
    from ttadev.agents.registry import get_registry
    from ttadev.agents.task import AgentTask

    registry = get_registry()
    agent_class = registry.get(agent_name)
    child_ctx = self._make_child_span(agent_name)
    return await agent_class().execute(task, child_ctx)
```

Import is deferred (inside the method) to avoid a circular import between `core` and `agents`.

### `ttadev/cli/__init__.py` — wire `agent` subcommand

Add `agent` sub-parser group:
- `tta agent list`
- `tta agent show <name>`
- `tta agent run <name> <instruction>`
- `tta agent run --route <instruction>`

### LLM primitives — add `chat()` adapter

`AnthropicPrimitive`, `GoogleAIStudioPrimitive`, `GroqPrimitive`, `OpenAIPrimitive`, `OpenRouterPrimitive` each gain:

```python
async def chat(
    self,
    messages: list[ChatMessage],
    system: str | None,
    ctx: WorkflowContext,
) -> str:
    request = AnthropicRequest(messages=messages, system=system)
    response = await self.execute(request, ctx)
    return response.content
```

This is purely additive — no existing behaviour changes.

---

## Observability Strategy

- Every `AgentPrimitive._execute()` produces a span named `agent.<name>` (via `InstrumentedPrimitive`)
- `spawn_agent()` produces a child span — visible in the dashboard as nested sub-agent calls
- `ToolCallLoop` iterations produce sub-spans: `tool_call.<tool_name>`
- `AgentRouterPrimitive` adds a span attribute `router.selected_agent` showing which agent was chosen

---

## Test Plan

```
tests/
└── agents/
    ├── test_spec.py            # AgentSpec construction, frozen, valid
    ├── test_task.py            # AgentTask/AgentResult serialisation
    ├── test_registry.py        # register, get, all; contextvar override isolation
    ├── test_agent_primitive.py # execute with mock ChatPrimitive; quality gate enforcement
    ├── test_tool_call_loop.py  # loop terminates; max iterations guard; tool result injection
    ├── test_router.py          # keyword routing; LLM fallback; agent_hint short-circuit
    ├── test_developer.py       # DeveloperAgent spec correctness; handoff triggers
    └── test_spawn_agent.py     # WorkflowContext.spawn_agent() creates child span
```

All tests use mock `ChatPrimitive` — no live API calls. One integration test (`tests/integration/test_agent_e2e.py`) is marked `@pytest.mark.external` and skipped in CI.

---

## Tech Debt Created

- `ttadev/agents/context/` and `ttadev/agents/coordination/` remain orphaned sub-packages. Follow-up task: evaluate for removal or proper integration once the new agent system is stable.

---

## Build Order (dependency-sorted)

1. `protocol.py` — no deps on new code
2. `spec.py` — no deps on new code
3. `task.py` — no deps on new code
4. `registry.py` — depends on `base.py` type (forward ref only)
5. `base.py` (`AgentPrimitive`) — depends on spec, task, registry, protocol
6. `tool_call_loop.py` — depends on protocol
7. `developer.py` — depends on base, spec
8. `router.py` — depends on base, registry, task
9. `WorkflowContext.spawn_agent()` — depends on registry, task (deferred import)
10. LLM primitive `chat()` adapters — depends on protocol
11. `ttadev/cli/agent.py` — depends on registry, task, router
12. `ttadev/agents/__init__.py` — re-exports everything
