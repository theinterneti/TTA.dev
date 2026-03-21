---
category: codebase-insights
date: 2026-03-19
component: agents
severity: high
tags: [agents, phase2, AgentSpec, AgentPrimitive, AgentRegistry, role-based]
related_memories: []
---
# Agent System — Phase 2 (Fully Implemented)

All files in `ttadev/agents/`.

## Core Data Types

| Type | File | Description |
|---|---|---|
| `AgentSpec` | spec.py | Frozen dataclass: name, role, system_prompt, capabilities, tools, quality_gates, handoff_triggers |
| `AgentTool` | spec.py | name, description, rule (ALWAYS/WHEN_INSTRUCTED/NEVER) |
| `QualityGate` | spec.py | name, check: Callable[[AgentResult], bool], error_message |
| `HandoffTrigger` | spec.py | condition: Callable[[AgentTask], bool], target_agent, reason |
| `AgentTask` | task.py | instruction, context: dict, constraints, agent_hint: str|None |
| `AgentResult` | task.py | agent_name, response, artifacts, suggestions, spawned_agents, quality_gates_passed, confidence: float |
| `Artifact` | task.py | name, content, artifact_type ("code"/"test"/"diff"/"report") |

## AgentPrimitive (base.py)

Extends `InstrumentedPrimitive[AgentTask, AgentResult]`. Checks handoff triggers → builds tool handlers → runs ToolCallLoop → checks quality gates. Composable with `>>` and `|`.

## AgentRegistry (registry.py)

- Global in-memory registry
- `override_registry()` context manager for test isolation
- `get_registry()` returns contextvar override or global
- `registry.get(name)` returns agent CLASS (not instance — caller instantiates)

## Built-in Agents

developer, qa, devops, security, git, github, performance — each in own file.

## AgentRouterPrimitive (router.py)

Routes `AgentTask` to correct specialist based on `agent_hint` or task content analysis.

## Protocol (protocol.py)

`ChatPrimitive` protocol — `chat(messages, system, ctx) -> str` — implemented by all LLM integration primitives.

---

**Created:** 2026-03-19
**Last Updated:** 2026-03-19
**Verified:** [x] Yes
