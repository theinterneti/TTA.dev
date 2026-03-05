# Primitives Patterns

Deep reference for TTA.dev primitive composition, operators, and workflow patterns.

## Core Concept

TTA.dev provides composable workflow primitives. Always use them instead of manual async orchestration.

## Composition Operators

- `>>` — Sequential execution (previous output → next input)
- `|` — Parallel execution (same input to all branches)

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Sequential
workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> process_data

# Parallel
workflow = fast_path | slow_path | cached_path

# Combined
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator
)

# Execute
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

**Type adaptation:** Use `LambdaPrimitive` to adapt types between sequential steps.

## Available Primitives

| Category | Primitives |
|----------|-----------|
| **Core** | `SequentialPrimitive`, `ParallelPrimitive`, `RouterPrimitive` |
| **Recovery** | `RetryPrimitive`, `FallbackPrimitive`, `TimeoutPrimitive`, `CompensationPrimitive` |
| **Performance** | `CachePrimitive`, `MemoryPrimitive` |
| **Skills** | `Skill`, `SkillDescriptor`, `SkillRegistry` |
| **Collaboration** | `GitCollaborationPrimitive` |
| **Adaptive** | `AdaptiveRetryPrimitive`, `LogseqStrategyIntegration` |
| **Testing** | `MockPrimitive` |

**Extension modules** (non-core): Accessible via `tta_dev_primitives.extensions`:

```python
from tta_dev_primitives.extensions import list_extensions, adaptive
```

## Recovery Patterns

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive,
    CompensationPrimitive,
)

# Retry with exponential backoff
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
)

# Fallback chain
workflow = FallbackPrimitive(
    primary=fast_service,
    fallback=slow_service,
)

# Timeout protection
workflow = TimeoutPrimitive(
    primitive=long_running_task,
    timeout_seconds=30.0,
)
```

## Performance Patterns

```python
from tta_dev_primitives.performance import CachePrimitive

# LRU cache with TTL
cached = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000,
)
```

## Agent Skills (SKILL.md)

Skills are self-describing agent capabilities that extend `WorkflowPrimitive` and compose with `>>` and `|`:

```python
from tta_skill_primitives import Skill, SkillDescriptor, SkillRegistry

class CodeReviewSkill(Skill[str, dict]):
    descriptor = SkillDescriptor(
        name="code-review",
        description="Analyse code for quality and security issues.",
    )

    async def execute(self, input_data, context):
        return {"issues": [], "score": 100}

# Register for discovery
registry = SkillRegistry()
registry.register(CodeReviewSkill())
skill = registry.get("code-review")
```

## Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| Manual async orchestration | `SequentialPrimitive` or `>>` |
| `try/except` with retry loops | `RetryPrimitive` |
| `asyncio.wait_for()` | `TimeoutPrimitive` |
| Manual caching dicts | `CachePrimitive` |
| Global variables for state | `WorkflowContext` |
| Modifying core primitives | Extend via composition |

## State Management

Always pass state via `WorkflowContext`:

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"},
)
result = await workflow.execute(input_data, context)
```

## Key Files

- **Core primitives:** `platform/primitives/src/tta_dev_primitives/`
- **Observability:** `platform/observability/src/observability_integration/`
- **Agent context:** `platform/agent-context/src/universal_agent_context/`
- **Examples:** `platform/primitives/examples/`
- **Full API reference:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
