---
category: mental-models
date: 2026-03-20
component: agents
severity: high
tags: [mental-model, agents, AgentSpec, AgentPrimitive, AgentRegistry]
---
# Mental Model: Agent System (Phase 2)

All files: `ttadev/agents/`

## Core types

**AgentSpec** (frozen dataclass, `spec.py`): `name`, `role`, `system_prompt`,
`capabilities`, `tools: list[AgentTool]`, `quality_gates: list[QualityGate]`,
`handoff_triggers: list[HandoffTrigger]`

**AgentTool**: `name`, `description`, `rule: ToolRule` (ALWAYS/WHEN_INSTRUCTED/NEVER)
**QualityGate**: `name`, `check: Callable[[AgentResult], bool]`, `error_message`
**HandoffTrigger**: `condition: Callable[[AgentTask], bool]`, `target_agent: str`

**AgentTask** (`task.py`): `instruction`, `context: dict`, `constraints`, `agent_hint: str | None`
**AgentResult** (`task.py`): `agent_name`, `response`, `artifacts`, `suggestions`,
`spawned_agents`, `quality_gates_passed: bool`, `confidence: float` (0.0–1.0)
**Artifact**: `name`, `content`, `artifact_type` ("code"/"test"/"diff"/"report")

## AgentPrimitive (base.py)

Extends `InstrumentedPrimitive[AgentTask, AgentResult]`.
Flow: check handoff triggers → build tool handlers → run ToolCallLoop → check quality gates.
Composable: `agent_a >> agent_b` or `agent_a | agent_b`.

## AgentRegistry (registry.py)

- Global in-memory registry
- `override_registry()` context manager — REQUIRED for test isolation
- `get_registry()` — returns contextvar override or global
- `registry.get(name)` — returns agent CLASS, not instance (caller instantiates)

## ChatPrimitive protocol (protocol.py)

`chat(messages: list[dict], system: str | None, ctx: WorkflowContext) -> str`
Implemented by all LLM integration primitives.

## Built-in agents

developer, qa, devops, security, git, github, performance — each in own file.
AgentRouterPrimitive (router.py) — routes AgentTask to correct agent.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
