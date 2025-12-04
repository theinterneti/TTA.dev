# DelegationPrimitive

type:: [[Primitive]]
category:: [[Orchestration]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 90
complexity:: [[High]]
python-class:: `DelegationPrimitive`
import-path:: `from tta_dev_primitives.orchestration import DelegationPrimitive`
related-primitives:: [[TTA.dev/Primitives/RouterPrimitive]], [[TTA.dev/Primitives/WorkflowPrimitive]]

---

## Overview

- id:: delegation-primitive-overview
  Delegates tasks from an orchestrator model to executor models, enabling the orchestrator-executor pattern for cost optimization and intelligent task distribution.

  **Think of it as:** A smart dispatcher that routes complex tasks to the most appropriate AI model based on the task requirements.

---

## Use Cases

- id:: delegation-primitive-use-cases
  - **Cost optimization:** Route simple tasks to cheaper/free models
  - **Multi-model orchestration:** Leverage strengths of different LLMs
  - **Task distribution:** Spread workload across multiple models
  - **Quality tiers:** Use premium models only when needed
  - **Fallback routing:** Route to alternative models on failure

---

## Key Benefits

- id:: delegation-primitive-benefits
  - ✅ **Cost reduction** - Route to free flagship models when possible
  - ✅ **Intelligent delegation** - Orchestrator chooses best executor
  - ✅ **Multi-model workflows** - Combine capabilities of different LLMs
  - ✅ **Observability** - Track delegations, costs, and usage
  - ✅ **Type-safe** - Strong typing with Pydantic models
  - ✅ **Extensible** - Easy to add new executor models

---

## API Reference

- id:: delegation-primitive-api

### DelegationRequest

```python
class DelegationRequest(BaseModel):
    task_description: str  # Description of the task to delegate
    executor_model: str    # Model to execute the task
    messages: list[dict[str, str]]  # Messages to send to executor
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = {}
```

### DelegationResponse

```python
class DelegationResponse(BaseModel):
    content: str           # Generated response from executor
    executor_model: str    # Model that executed the task
    usage: dict[str, int]  # Token usage statistics
    cost: float            # Estimated cost in USD
    metadata: dict[str, Any] = {}
```

### Constructor

```python
DelegationPrimitive(
    orchestrator: WorkflowPrimitive,  # Model that decides delegation
    executors: dict[str, WorkflowPrimitive]  # Available executor models
)
```

---

## Examples

### Basic Delegation

- id:: delegation-basic-example

```python
from tta_dev_primitives.orchestration import DelegationPrimitive
from tta_dev_primitives import WorkflowContext

# Create delegation primitive
delegation = DelegationPrimitive(
    orchestrator=claude_sonnet,
    executors={
        "gemini-pro": gemini_primitive,
        "deepseek-r1": deepseek_primitive,
        "llama-3.3-70b": llama_primitive,
    }
)

# Create delegation request
request = DelegationRequest(
    task_description="Summarize this document",
    executor_model="gemini-pro",
    messages=[{"role": "user", "content": "Summarize: ..."}],
)

# Execute delegation
context = WorkflowContext(correlation_id="delegation-001")
response = await delegation.execute(request, context)

print(f"Result: {response.content}")
print(f"Cost: ${response.cost:.4f}")
```

### Orchestrator-Executor Pattern

- id:: delegation-orchestrator-pattern

```python
# Pattern: High-quality orchestrator + Free executors
orchestrator = ClaudeSonnet45()  # Premium: Analyzes and plans

executors = {
    "coding": DeepSeekR1(),      # Free: Code generation
    "summarization": GeminiPro(), # Free: Text summarization
    "reasoning": Llama33_70B(),   # Free: Complex reasoning
}

delegation = DelegationPrimitive(
    orchestrator=orchestrator,
    executors=executors
)

# Orchestrator decides which executor to use
async def process_task(task: str, context: WorkflowContext):
    # 1. Orchestrator analyzes task
    analysis = await orchestrator.execute(
        {"task": task, "action": "analyze"},
        context
    )

    # 2. Delegate to appropriate executor
    request = DelegationRequest(
        task_description=task,
        executor_model=analysis["recommended_model"],
        messages=[{"role": "user", "content": task}],
    )

    return await delegation.execute(request, context)
```

### Cost-Optimized Workflow

- id:: delegation-cost-example

```python
from tta_dev_primitives.orchestration import DelegationPrimitive

# Route to free models by default
delegation = DelegationPrimitive(
    orchestrator=budget_aware_orchestrator,
    executors={
        "free-tier": gemini_flash_free,    # $0/request
        "standard": gemini_pro,             # ~$0.001/request
        "premium": claude_opus,             # ~$0.015/request
    }
)

# Orchestrator picks cheapest capable model
# Simple tasks → free-tier
# Medium tasks → standard
# Complex tasks → premium (only when necessary)
```

---

## Orchestrator-Executor Pattern

- id:: delegation-pattern-detail

```
┌─────────────────────────────────────────────────────┐
│                   User Request                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              Orchestrator Model                      │
│           (Claude Sonnet 4.5)                       │
│                                                      │
│  1. Analyze task complexity                         │
│  2. Select appropriate executor                      │
│  3. Create detailed instructions                     │
└─────────────────┬───────────────────────────────────┘
                  │
         ┌────────┼────────┐
         │        │        │
         ▼        ▼        ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│ Executor 1 │ │ Executor 2 │ │ Executor 3 │
│ Gemini Pro │ │ DeepSeek R1│ │ Llama 70B  │
│   (free)   │ │   (free)   │ │   (free)   │
└────────────┘ └────────────┘ └────────────┘
```

---

## Best Practices

- id:: delegation-best-practices

✅ **Use free models for simple tasks** - Cost savings of 90%+
✅ **Let orchestrator decide** - Don't hardcode executor selection
✅ **Track costs per delegation** - Use response.cost for monitoring
✅ **Set appropriate timeouts** - Combine with TimeoutPrimitive
✅ **Add fallback executors** - Handle model unavailability

❌ **Don't over-delegate** - Some tasks are faster inline
❌ **Don't ignore context limits** - Check model token limits
❌ **Don't skip validation** - Verify executor results

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/RouterPrimitive]] - Route based on task classification
- [[TTA.dev/Primitives/FallbackPrimitive]] - Fallback to alternative executors
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Timeout long-running delegations
- [[TTA.dev/Primitives/CachePrimitive]] - Cache delegation results

### Related Primitives

- [[TTA.dev/Primitives/TaskClassifierPrimitive]] - Classify tasks for routing
- [[TTA.dev/Primitives/MultiModelWorkflow]] - Orchestrate multiple models

---

## Metadata

**Source Code:** [delegation_primitive.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py)
**Tests:** [test_delegation_primitive.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/orchestration/test_delegation_primitive.py)

**Created:** [[2025-12-03]]
**Last Updated:** [[2025-12-03]]
**Status:** [[Stable]] - Production Ready
