# Tasks: Phase 2 — Role-Based Agent System

**Phase:** SDD Phase 3 (Task Breakdown)
**Status:** Ready for implementation
**Plan:** [phase2-agent-system-plan.md](phase2-agent-system-plan.md)
**Date:** 2026-03-19

---

## Checklist

### Group A — Data Types (no dependencies)

- [ ] **A1** — Create `ttadev/agents/protocol.py`
  - Define `ChatMessage` TypedDict (`role`, `content`)
  - Define `ChatPrimitive` Protocol with `async chat(messages, system, ctx) -> str`
  - **Acceptance:** `isinstance(mock, ChatPrimitive)` passes for a structurally compatible class; incompatible class fails at type-check time (pyright)

- [ ] **A2** — Create `ttadev/agents/spec.py`
  - `ToolRule` enum: `ALWAYS`, `WHEN_INSTRUCTED`, `NEVER`
  - `AgentTool` frozen dataclass: `name`, `description`, `rule`
  - `QualityGate` frozen dataclass: `name`, `check: Callable[[AgentResult], bool]`, `error_message`
  - `HandoffTrigger` frozen dataclass: `condition: Callable[[AgentTask], bool]`, `target_agent`, `reason`
  - `AgentSpec` frozen dataclass: all fields from spec doc
  - **Acceptance:** `AgentSpec(...)` is constructable; mutation raises `FrozenInstanceError`; all fields type-check clean

- [ ] **A3** — Create `ttadev/agents/task.py`
  - `Artifact` dataclass: `name`, `content`, `artifact_type`
  - `AgentTask` dataclass: `instruction`, `context`, `constraints`, `agent_hint=None`
  - `AgentResult` dataclass: `agent_name`, `response`, `artifacts`, `suggestions`, `spawned_agents`, `quality_gates_passed`, `confidence`
  - **Acceptance:** Round-trip serialisation via `dataclasses.asdict`; default values correct

---

### Group B — Registry (depends on A)

- [ ] **B1** — Create `ttadev/agents/registry.py`
  - `AgentRegistry` class: `register()`, `get()`, `all()`
  - `get()` raises `KeyError` with clear message if agent not found
  - Module-level `_global_registry` instance
  - `get_registry()` function: returns contextvar override if set, else global
  - `override_registry(registry)` context manager for test isolation
  - **Acceptance:** Two concurrent `override_registry` calls in separate async tasks don't bleed into each other (contextvar isolation test)

---

### Group C — Core Primitives (depends on A, B)

- [ ] **C1** — Create `ttadev/agents/tool_call_loop.py`
  - `ToolDefinition` dataclass: `name`, `description`, `parameters: dict`
  - `ToolCallRequest` dataclass: `messages`, `tools`, `model`
  - `ToolCallLoop(InstrumentedPrimitive[ToolCallRequest, str])`
  - Loop: chat → detect tool calls in response → execute registered handlers → append result → repeat
  - `max_iterations` guard (default 10); raises `ToolCallLoopError` if exceeded
  - **Acceptance:** Loop terminates after mock tool resolves in 1 iteration; raises on iteration limit; no tool calls → returns response directly

- [ ] **C2** — Create `ttadev/agents/base.py` — `AgentPrimitive`
  - `AgentPrimitive(InstrumentedPrimitive[AgentTask, AgentResult])`
  - `__init__(spec: AgentSpec, model: ChatPrimitive)`
  - `__init_subclass__` auto-registers subclass in `_global_registry`
  - `_execute()`: build prompt → check handoff triggers → run `ToolCallLoop` with ALWAYS tools → parse result → run quality gates
  - Quality gate failure raises `QualityGateError(gate_name, message)`
  - **Acceptance:** Mock model returning fixed string produces correct `AgentResult`; failing quality gate raises; handoff trigger calls `ctx.spawn_agent()`

---

### Group D — First Concrete Agent (depends on C)

- [ ] **D1** — Create `ttadev/agents/developer.py` — `DeveloperAgent`
  - `DEVELOPER_SPEC` constant with full system prompt (Python/TTA.dev standards, ruff/pyright/pytest)
  - Capabilities: `["code implementation", "code review", "debugging", "refactoring", "test writing"]`
  - Tools: ruff (ALWAYS), pyright (ALWAYS), pytest (ALWAYS), git (WHEN_INSTRUCTED)
  - Quality gates: ruff passes, pyright passes on any code in artifacts
  - Handoff triggers: security keywords → `"security"`, deploy/infra keywords → `"devops"`, PR/merge keywords → `"github"`
  - `class DeveloperAgent(AgentPrimitive)` — thin subclass, just sets spec
  - **Acceptance:** `DeveloperAgent` appears in `get_registry().all()` after import; handoff trigger fires on "check for SQL injection"; quality gates defined and callable

---

### Group E — Router (depends on B, C, D)

- [ ] **E1** — Create `ttadev/agents/router.py` — `AgentRouterPrimitive`
  - `AgentRouterPrimitive(InstrumentedPrimitive[AgentTask, AgentResult])`
  - `__init__(orchestrator: ChatPrimitive, registry: AgentRegistry | None = None)`
  - Registry resolved at call time via `get_registry()` (not init time)
  - Routing logic: agent_hint short-circuit → keyword score → LLM fallback
  - Span attribute `router.selected_agent` set on every execution
  - `GeneralistResult` fallback when no agent scores above 0.3
  - **Acceptance:** `agent_hint="developer"` bypasses scoring; known keyword routes correctly without LLM call; ambiguous task calls mock orchestrator exactly once

---

### Group F — WorkflowContext Extension (depends on A, B)

- [ ] **F1** — Extend `ttadev/primitives/core/base.py`
  - Add `async spawn_agent(self, agent_name: str, task: "AgentTask") -> "AgentResult"` to `WorkflowContext`
  - Deferred import of `registry` and `task` types (inside method body) to avoid circular import
  - Creates child context via `self._make_child_span(agent_name)` — or equivalent span-nesting mechanism
  - **Acceptance:** `spawn_agent()` on a `WorkflowContext` with a mock registry calls the correct agent; child span `parent_span_id` matches parent `span_id`; no import error at module load time

---

### Group G — LLM Adapter Methods (depends on A)

- [ ] **G1** — Add `chat()` to `AnthropicPrimitive`
  - `async chat(messages, system, ctx) -> str` — translates to `AnthropicRequest`, calls `execute()`, returns `response.content`
  - **Acceptance:** `isinstance(AnthropicPrimitive(), ChatPrimitive)` passes structural check; `chat()` returns a string

- [ ] **G2** — Add `chat()` to remaining LLM primitives
  - `GoogleAIStudioPrimitive`, `GroqPrimitive`, `OpenAIPrimitive`, `OpenRouterPrimitive`
  - Same pattern as G1
  - **Acceptance:** All 5 LLM primitives pass `isinstance(..., ChatPrimitive)` structural check; existing `execute()` tests still pass

---

### Group H — Package Init (depends on all above)

- [ ] **H1** — Create `ttadev/agents/__init__.py`
  - Re-export public surface: `AgentSpec`, `AgentTool`, `ToolRule`, `QualityGate`, `HandoffTrigger`, `AgentTask`, `AgentResult`, `Artifact`, `ChatPrimitive`, `AgentPrimitive`, `ToolCallLoop`, `AgentRegistry`, `get_registry`, `override_registry`, `AgentRouterPrimitive`, `DeveloperAgent`
  - **Acceptance:** `from ttadev.agents import DeveloperAgent, AgentRouterPrimitive` works; no circular import errors

---

### Group I — CLI (depends on H)

- [ ] **I1** — Create `ttadev/cli/agent.py`
  - `register_agent_subcommands(sub: _SubParsersAction) -> None`
  - `tta agent list` — prints table: name, role, capabilities
  - `tta agent show <name>` — prints spec: system prompt preview, tools with rules, quality gates, handoff triggers
  - `tta agent run <name> <instruction>` — instantiates agent with no model (requires `--model` flag or `ANTHROPIC_API_KEY`), executes, prints result
  - `tta agent run --route <instruction>` — uses `AgentRouterPrimitive`
  - `--json` flag for structured output on all subcommands
  - **Acceptance:** `tta agent list` exits 0 and shows `developer`; `tta agent show developer` prints system prompt; `tta agent run developer "hello" --dry-run` prints the prompt that would be sent without calling any API

- [ ] **I2** — Wire into `ttadev/cli/__init__.py`
  - Import `register_agent_subcommands` and call it inside `_build_parser()`
  - **Acceptance:** `tta --help` shows `agent` in the subcommand list; `tta agent --help` shows `list`, `show`, `run`

---

### Group J — Tests (depends on H)

- [ ] **J1** — `tests/agents/test_spec.py` — A2 acceptance tests
- [ ] **J2** — `tests/agents/test_task.py` — A3 acceptance tests
- [ ] **J3** — `tests/agents/test_registry.py` — B1 acceptance tests (including contextvar isolation)
- [ ] **J4** — `tests/agents/test_tool_call_loop.py` — C1 acceptance tests
- [ ] **J5** — `tests/agents/test_agent_primitive.py` — C2 acceptance tests
- [ ] **J6** — `tests/agents/test_developer.py` — D1 acceptance tests
- [ ] **J7** — `tests/agents/test_router.py` — E1 acceptance tests
- [ ] **J8** — `tests/agents/test_spawn_agent.py` — F1 acceptance tests
- [ ] **J9** — `tests/integration/test_agent_e2e.py` — end-to-end: `DeveloperAgent` on a real code review task; marked `@pytest.mark.external`, skipped in CI

---

## Dependency Graph

```
A1, A2, A3          (parallel — no deps)
      ↓
      B1             (needs A types)
      ↓
  C1, C2             (parallel — need A + B)
      ↓
      D1             (needs C2)
      ↓
      E1             (needs B + C + D)

A1, A2 → F1         (WorkflowContext — needs A for deferred import)
A1     → G1, G2     (LLM adapters — need protocol only)

All above → H1 → I1 → I2
All above → J1–J9   (tests written alongside each group)
```

---

## Definition of Done

- [ ] All J1–J8 tests pass with 100% coverage on new code
- [ ] `uv run ruff check .` passes
- [ ] `uvx pyright ttadev/` passes
- [ ] `tta agent list` shows `developer` in terminal
- [ ] `tta agent show developer` prints the full spec
- [ ] `from ttadev.agents import DeveloperAgent, AgentRouterPrimitive` works in a fresh Python session
- [ ] Existing test suite (314 tests) still passes
