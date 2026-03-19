# Spec: Phase 2 — Role-Based Agent System

**Phase:** SDD Phase 1 (Functional Specification)
**Status:** Draft — awaiting sign-off
**Date:** 2026-03-19
**Scope:** `AgentSpec`, `AgentPrimitive`, `AgentRouterPrimitive`, `DeveloperAgent`, `tta agent` CLI

---

## Problem Statement

TTA.dev's primitives are powerful for workflow composition, but they operate at the model level — you configure a model and call it. There is no concept of a *role*: a persistent identity that carries domain knowledge, a specific toolset, and rules for how to use them.

The result: every workflow that involves an LLM must re-specify the system prompt, tools, and behavioral rules from scratch. There is no way to say "use a code reviewer here" and have that mean something concrete and reusable.

**Goal:** An agent is a *suit of clothes* a model wears. Swap the clothes, get a different specialist. The underlying model is unchanged — the agent spec shapes its identity, knowledge, tools, and rules for that context.

---

## Core Concept

```
AgentSpec  =  system_prompt  +  tools  +  tool_rules  +  capabilities
AgentPrimitive  =  AgentSpec  +  any LLM primitive  →  WorkflowPrimitive
```

An `AgentPrimitive` is composable with `>>` and `|` just like any other primitive. An agent in a workflow can also spawn sub-agents mid-task via the `WorkflowContext`. An `AgentRouterPrimitive` inspects task context and routes automatically to the right agent.

---

## User Journeys

### Journey 1: Use an agent directly

```python
from ttadev.agents import DeveloperAgent
from ttadev.primitives.integrations import AnthropicPrimitive

agent = DeveloperAgent(model=AnthropicPrimitive())
result = await agent.execute(AgentTask(
    instruction="Review this function for edge cases",
    context={"code": "def divide(a, b): return a / b"},
))
# result.response — agent's review
# result.suggestions — structured recommendations
```

### Journey 2: Agent as a step in a composed workflow

```python
review_workflow = (
    TimeoutPrimitive(timeout_seconds=30)
    >> RetryPrimitive(max_attempts=2)
    >> DeveloperAgent(model=AnthropicPrimitive())
)
result = await review_workflow.execute(task, ctx)
```

### Journey 3: Agent spawns a sub-agent on the fly

An agent, mid-task, determines that part of the work needs a specialist:

```python
# Inside DeveloperAgent._execute():
if task_needs_security_review(task):
    security_result = await ctx.spawn_agent(
        agent_name="security",
        task=AgentTask(instruction="Check for injection vulnerabilities", ...),
    )
```

The sub-agent runs in a child `WorkflowContext` span and its result flows back to the parent agent.

### Journey 4: Adaptive routing via AgentRouterPrimitive

```python
from ttadev.agents import AgentRouterPrimitive, agent_registry

router = AgentRouterPrimitive(
    agents=agent_registry.all(),
    orchestrator=AnthropicPrimitive(),  # model that decides routing
)

# Router inspects the task, picks the right agent, executes it
result = await router.execute(AgentTask(
    instruction="Our test suite is flaky on CI",
    context={"repo": "TTA.dev"},
))
# Routes to QAAgent automatically
```

### Journey 5: CLI usage

```bash
# Run an agent task directly
tta agent run developer "Review the retry primitive for thread safety"

# List registered agents
tta agent list

# Show an agent's spec (system prompt, tools, capabilities)
tta agent show developer
```

---

## AgentSpec — the "suit of clothes"

An `AgentSpec` defines everything that makes a generalist model into a specialist:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique identifier (e.g. `"developer"`) |
| `role` | `str` | Human label (e.g. `"Senior Python Developer"`) |
| `system_prompt` | `str` | The full system prompt injected before every conversation |
| `capabilities` | `list[str]` | What this agent can do (used by router for matching) |
| `tools` | `list[AgentTool]` | MCP servers, skills, and shell commands available |
| `tool_rules` | `dict[str, ToolRule]` | Per-tool usage rules: `ALWAYS`, `WHEN_INSTRUCTED`, `NEVER` |
| `quality_gates` | `list[QualityGate]` | Checks that must pass before the agent returns a result |
| `handoff_triggers` | `list[HandoffTrigger]` | Conditions that cause the agent to spawn a sub-agent |

### Tool rules

```python
class ToolRule(Enum):
    ALWAYS = "always"           # agent uses this tool on every task
    WHEN_INSTRUCTED = "when_instructed"  # agent uses it only if asked
    NEVER = "never"             # agent must not use this tool
```

Example: a `DeveloperAgent` always runs the linter, uses the debugger only when instructed, and never touches deployment scripts.

---

## DeveloperAgent — the first concrete spec

**Role:** Senior Python developer. Writes, reviews, and debugs code to production standards.

**Capabilities:**
- Code implementation (new features, bug fixes)
- Code review (correctness, style, edge cases, security)
- Debugging (root cause analysis, fix suggestion)
- Refactoring (simplification, pattern alignment)
- Test writing (pytest, AAA pattern)

**Tools (always):** ruff, pyright, pytest
**Tools (when instructed):** git, file editor
**Tools (never):** deployment scripts, infrastructure commands

**Quality gates (must pass before returning):**
- Ruff lint passes on any code produced
- Pyright type-check passes on any code produced
- If tests were written, they pass

**Handoff triggers:**
- Security-related task → spawn `SecurityAgent`
- CI/CD task → spawn `DevOpsAgent`
- PR workflow task → spawn `GitHubAgent`

---

## AgentTask and AgentResult

```python
@dataclass
class AgentTask:
    instruction: str          # what the agent should do
    context: dict[str, Any]   # relevant code, files, error messages, etc.
    constraints: list[str]    # e.g. "don't change the public API"
    agent_hint: str | None    # caller's preferred agent (router may override)

@dataclass
class AgentResult:
    agent_name: str
    response: str             # agent's primary output
    artifacts: list[Artifact] # files created/modified, test results, etc.
    suggestions: list[str]    # structured recommendations
    spawned_agents: list[str] # names of any sub-agents used
    quality_gates_passed: bool
    confidence: float         # 0.0–1.0 self-assessed confidence
```

---

## AgentRouterPrimitive — adaptive routing

The router is itself an agent: it receives a task, uses a fast/cheap model to classify it, and dispatches to the best-fit registered agent.

**Routing logic:**
1. Extract intent keywords and domain signals from `AgentTask.instruction`
2. Score each registered agent by capability match
3. If score is unambiguous (>0.7 margin): dispatch directly
4. If ambiguous: ask the orchestrator model to choose, passing agent descriptions
5. Execute the selected agent; return its `AgentResult`
6. If the selected agent triggers a handoff, the router handles spawning the sub-agent

**Fallback:** if no agent matches with confidence >0.3, use a `GeneralistAgent` (bare model with no specialisation).

---

## Sub-agent Spawning via WorkflowContext

`WorkflowContext` gains a `spawn_agent()` method:

```python
async def spawn_agent(
    self,
    agent_name: str,
    task: AgentTask,
) -> AgentResult: ...
```

- Creates a child span in the observability trace
- Looks up `agent_name` in the `AgentRegistry`
- Executes the sub-agent with the same model configuration as the parent
- Returns the result; the parent agent decides how to incorporate it

This keeps sub-agent calls visible in the observability dashboard as nested spans.

---

## AgentRegistry

A simple module-level registry that agents self-register into on import:

```python
from ttadev.agents import agent_registry

agent_registry.register(DeveloperAgent)
all_agents = agent_registry.all()           # list[type[AgentPrimitive]]
agent = agent_registry.get("developer")    # type[AgentPrimitive]
```

---

## `tta agent` CLI

Extends the existing `tta` CLI with an `agent` subcommand group:

```
tta agent list                        # show all registered agents + capabilities
tta agent show <name>                 # print agent spec (system prompt, tools, rules)
tta agent run <name> <instruction>    # run an agent task, print result
tta agent run --route <instruction>   # let the router pick the agent
```

Output format: plain text by default, `--json` for structured output.

---

## Success Criteria

- [ ] `AgentSpec`, `AgentPrimitive`, `AgentTask`, `AgentResult` are importable from `ttadev.agents`
- [ ] `DeveloperAgent` passes its quality gates on a real code review task
- [ ] An `AgentPrimitive` composes with `>>` and `|` without modification to core primitives
- [ ] `WorkflowContext.spawn_agent()` produces a visible child span in the observability dashboard
- [ ] `AgentRouterPrimitive` correctly routes 4/5 test tasks to the right agent without explicit hints
- [ ] `tta agent run developer "..."` works end-to-end from the CLI
- [ ] 100% test coverage on new code; all existing tests still pass

---

## Out of Scope (Phase 2)

- The remaining 6 agent types (`QAAgent`, `DevOpsAgent`, `GitAgent`, `GitHubAgent`, `SecurityAgent`, `PerformanceAgent`) — they follow the same pattern once it's proven; they are Phase 2.2+
- Agent memory / learning from past interactions — Phase 3
- Agent consensus / voting (`AgentConsensus`) — Phase 3
- Human-in-the-loop approval gates — Phase 3
- Multi-tenant agent configuration — not planned

---

## Decisions

1. **Model coupling:** `AgentPrimitive` requires a `ChatPrimitive` protocol (accepts a `messages` list, returns a completion). This prevents accidentally wiring a `CachePrimitive` as a model. Existing LLM primitives (`AnthropicPrimitive`, `GoogleAIStudioPrimitive`, etc.) will implement the protocol.

2. **Tool invocation:** TTA.dev owns a minimal `ToolCallLoop` primitive that wraps any `ChatPrimitive` model and handles the function-calling conversation loop. This is more reusable than deferring to each model's native implementation, and keeps tool execution observable.

3. **AgentRegistry scope:** Global registry, auto-populated on import, with a `contextvars.ContextVar` override for test isolation. Workflows are optional — `DeveloperAgent(model=...).execute(task)` works with no `WorkflowContext`. `WorkflowContext.spawn_agent()` reads the global registry (respecting any contextvar override) but does not own it.
