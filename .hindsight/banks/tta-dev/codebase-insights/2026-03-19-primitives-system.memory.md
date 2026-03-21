---
category: codebase-insights
date: 2026-03-19
component: primitives
severity: high
tags: [primitives, WorkflowPrimitive, WorkflowContext, InstrumentedPrimitive, composition]
related_memories: []
---
# Primitives System

`ttadev/primitives/` — version 1.3.1 (tracked separately from package v0.1.0).

## WorkflowPrimitive[T, U]

Abstract base in `ttadev/primitives/core/base.py`.

- `execute(input_data: T, context: WorkflowContext) -> U` — abstract
- `>>` → `SequentialPrimitive` (chain output to next input)
- `|` → `ParallelPrimitive` (fan-out, gather results)

## WorkflowContext (Pydantic model)

- W3C trace context: `trace_id`, `span_id`, `baggage`
- Agent identity: `agent_id`, `agent_role`, `session_id`
- `spawn_agent(role)` — child context with new span
- `create_child_context()` — lightweight child
- `from_project(project_name)` — factory
- `checkpoint(label)` — OTel span event
- `memory` — attached by WorkflowOrchestrator at runtime

## InstrumentedPrimitive

`ttadev/primitives/observability/instrumented_primitive.py`

Extends WorkflowPrimitive. Wraps `_execute_impl` with OTel spans. All agents and WorkflowOrchestrator extend this.

## Full Primitive Export List

WorkflowPrimitive, WorkflowContext, LambdaPrimitive, SequentialPrimitive, ParallelPrimitive, ConditionalPrimitive, RouterPrimitive, RetryPrimitive, FallbackPrimitive, TimeoutPrimitive, CompensationPrimitive, CachePrimitive, MockPrimitive, GitCollaborationPrimitive, persistence primitives.

## Integration Primitives (`ttadev/primitives/integrations/`)

anthropic, openai, openrouter, groq, google-ai-studio, ollama, together-ai, huggingface, e2b, supabase, sqlite.

Each implements the `ChatPrimitive` protocol: `chat(messages, system, ctx) -> str`.

**Warning:** anthropic_primitive.py and openrouter_primitive.py import from `primitives.core.base` (not `ttadev.primitives.core.base`) — may be a stale import path to fix.

## Recovery Primitives (`ttadev/primitives/recovery/`)

retry, timeout, fallback, circuit_breaker (two files), compensation.

---

**Created:** 2026-03-19
**Last Updated:** 2026-03-19
**Verified:** [x] Yes
