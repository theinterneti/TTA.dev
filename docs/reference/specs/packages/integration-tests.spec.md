# Cross-Package Integration Test Specification

- **Version:** 1.0.0
- **Status:** Approved
- **Package:** infrastructure
- **Source:** `tests/integration/`

## 1. Purpose

This specification defines the formal test contracts for cross-package integration tests
in TTA.dev. Integration tests validate that packages work correctly together — ensuring
composed workflows, shared context propagation, and observability chains function end-to-end.

## 2. Test Categories

### 2.1 Primitives + Observability Integration

**Source:** `tests/integration/test_observability_primitives.py`

These tests MUST verify:

| Requirement | Description |
|-------------|-------------|
| Span creation | `InstrumentedPrimitive` MUST create a span named `primitive.{name}` on every execution |
| Metrics recording | `record_execution()` MUST record duration, success/failure count, and error type |
| Context propagation | `WorkflowContext` trace fields (`trace_id`, `span_id`, `parent_span_id`) MUST propagate through `>>` and `\|` composition |
| Failure tracking | Failed primitives MUST record exception details on the span and increment `failed_executions` counter |
| Overhead bounds | Instrumentation overhead MUST NOT exceed 10% of primitive execution time for operations > 1ms |
| Error preservation | `ObservablePrimitive` wrapper MUST re-raise the original exception unchanged |

### 2.2 Multi-Agent Coordination Integration

**Source:** `tests/integration/test_agent_coordination_integration.py`

These tests MUST verify:

| Requirement | Description |
|-------------|-------------|
| Handoff context | `AgentHandoffPrimitive` MUST preserve `WorkflowContext` metadata across agent transitions |
| Memory sharing | `AgentMemoryPrimitive` MUST allow agents to store and retrieve data within the same workflow |
| Parallel coordination | `AgentCoordinationPrimitive` with `"aggregate"` strategy MUST execute agents concurrently and collect all results |
| Consensus strategy | `AgentCoordinationPrimitive` with `"consensus"` strategy MUST aggregate votes from all agents |
| First strategy | `AgentCoordinationPrimitive` with `"first"` strategy MUST return as soon as one agent completes |
| Failure isolation | Coordination MUST handle individual agent failures gracefully when `require_all_success=False` |
| Timeout enforcement | Coordination `timeout_seconds` MUST cancel agents that exceed the deadline |
| Memory scope isolation | Memory scopes (`"workflow"`, `"session"`, `"global"`) MUST isolate data appropriately |

### 2.3 Workflow Composition Integration

**Source:** `tests/integration/test_workflow_data_pipeline.py`, `tests/integration/test_workflow_code_review.py`

These tests MUST verify:

| Requirement | Description |
|-------------|-------------|
| Sequential composition | `A >> B >> C` MUST pass output of A to B, output of B to C |
| Parallel composition | `A \| B \| C` MUST execute concurrently with the same input and return `[result_a, result_b, result_c]` |
| Mixed composition | `(A >> B) \| (C >> D)` MUST execute two sequential chains in parallel |
| Context propagation | `WorkflowContext.state` modifications MUST be visible to subsequent steps in sequential chains |
| Checkpoint tracking | Each primitive MUST record `{name}.start` and `{name}.end` checkpoints |
| Error propagation | Exceptions MUST propagate immediately in sequential chains; first exception wins in parallel |
| Performance | Parallel execution MUST be faster than sequential for I/O-bound operations |

### 2.4 LLM Routing Integration

**Source:** `tests/integration/test_workflow_llm_routing.py`

These tests MUST verify:

| Requirement | Description |
|-------------|-------------|
| Router dispatch | `RouterPrimitive` MUST dispatch to the correct primitive based on `router_fn` output |
| Fallback chain | `FallbackPrimitive` MUST try primary, then fallback on failure |
| Retry resilience | `RetryPrimitive` MUST retry transient failures with backoff |
| Cache effectiveness | `CachePrimitive` MUST return cached results on cache hits |
| Composed resilience | `CachePrimitive >> TimeoutPrimitive >> RetryPrimitive >> RouterPrimitive` MUST work as a composed workflow |

### 2.5 Primitive Adoption Compliance

**Source:** `tests/integration/test_agent_primitive_adoption.py`

These tests MUST verify:

| Requirement | Description |
|-------------|-------------|
| Import compliance | All example files MUST import from `tta_dev_primitives` |
| Anti-pattern detection | Example files MUST NOT use `asyncio.gather()` or `asyncio.create_task()` directly |
| Context usage | All workflow examples MUST use `WorkflowContext` for execution |
| Base class compliance | Core primitives MUST extend `WorkflowPrimitive` |

## 3. Test Environment Requirements

- All integration tests MUST run without external services (no databases, no APIs, no Docker).
- Tests MUST use `MockPrimitive` or `LambdaPrimitive` for simulating external dependencies.
- Tests MUST complete within 60 seconds per test (default `@pytest.mark.timeout(60)`).
- Tests requiring external resources MUST be marked with `@pytest.mark.integration`.

## 4. Cross-Package Contract Verification

Each integration test file MUST verify at least one cross-package boundary:

| Test File | Packages Verified |
|-----------|-------------------|
| `test_observability_primitives.py` | `tta-dev-primitives` ↔ `tta-observability-integration` |
| `test_agent_coordination_integration.py` | `universal-agent-context` ↔ `tta-dev-primitives` |
| `test_workflow_data_pipeline.py` | `tta-dev-primitives` (core ↔ recovery ↔ performance) |
| `test_workflow_code_review.py` | `tta-dev-primitives` (core ↔ observability) |
| `test_workflow_llm_routing.py` | `tta-dev-primitives` (core ↔ recovery ↔ routing) |

## 5. Cross-References

- [WorkflowPrimitive Spec](../primitives/workflow-primitive.spec.md) — Base class contracts
- [Span Schema](../observability/span-schema.spec.md) — Observability contracts verified by tests
- [Metrics Catalog](../observability/metrics-catalog.spec.md) — Metrics contracts verified by tests
- [Context Propagation](../observability/context-propagation.spec.md) — Propagation contracts verified by tests
