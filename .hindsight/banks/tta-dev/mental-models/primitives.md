---
category: mental-models
date: 2026-03-20
component: primitives
severity: high
tags: [mental-model, primitives, WorkflowPrimitive, WorkflowContext, composition]
---
# Mental Model: Primitives System

Package: `ttadev/primitives/` — version 1.3.1 (separate from package v0.1.0).
Auto-calls `setup_tracing()` on import.

## Core types

**WorkflowPrimitive[T, U]** (`ttadev/primitives/core/base.py`)
- Abstract. `execute(input_data: T, context: WorkflowContext) -> U`
- `>>` → SequentialPrimitive (chain). `|` → ParallelPrimitive (fan-out/gather).

**WorkflowContext** (Pydantic model, same file)
- W3C trace: `trace_id`, `span_id`, `baggage`
- Identity: `agent_id`, `agent_role`, `session_id`
- `spawn_agent(role)`, `create_child_context()`, `from_project(name, workflow_id)`, `checkpoint(label)`
- `memory` — attached at runtime by WorkflowOrchestrator

**InstrumentedPrimitive** (`ttadev/primitives/observability/instrumented_primitive.py`)
- Extends WorkflowPrimitive. Override `_execute_impl` not `execute`.
- Wraps with OTel spans automatically. All agents + orchestrator extend this.

## All exported primitives

LambdaPrimitive, SequentialPrimitive, ParallelPrimitive, ConditionalPrimitive,
RouterPrimitive, RetryPrimitive, FallbackPrimitive, TimeoutPrimitive,
CompensationPrimitive, CachePrimitive, MockPrimitive, GitCollaborationPrimitive.

## Integration primitives (`ttadev/primitives/integrations/`)

anthropic, openai, openrouter, groq, google-ai-studio, ollama, together-ai,
huggingface, e2b, supabase, sqlite. All implement `ChatPrimitive` protocol.
All optional deps — graceful degradation in `__init__.py` with try/except.

## Recovery primitives (`ttadev/primitives/recovery/`)

retry, timeout, fallback, circuit_breaker (two files), compensation.

## Import path

All internal imports use `from ttadev.primitives.X` — never `from primitives.X` (old, broken).

---
**Created:** 2026-03-20
**Verified:** [x] Yes
