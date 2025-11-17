# Getting Started

type:: [[Guide]]
category:: [[Getting Started]]
difficulty:: [[Beginner]]
estimated-time:: 15 minutes
target-audience:: [[Developers]], [[AI Engineers]]

---

## Welcome to TTA.dev

- id:: getting-started-welcome
  TTA.dev is a production-ready AI development toolkit that makes building reliable AI workflows simple through composable primitives.

  **What you'll learn:** How to install TTA.dev, create your first workflow, and understand the core concepts.

---

## Prerequisites

{{embed ((prerequisites-full))}}

---

## Installation

{{embed ((uv-installation))}}

{{embed ((project-setup))}}

---

## Core Concepts

### What Are Agentic Primitives?

- id:: what-are-primitives
  **Agentic Primitives** are reusable building blocks for AI workflows. Instead of writing complex async orchestration code, you compose primitives using simple operators.

  **Think of them as:** LEGO blocks for AI workflows - each primitive does one thing well, and they snap together to create complex systems.

### The Two Composition Operators

- id:: composition-operators

**Sequential (`>>`):** Execute one after another

```python
workflow = step1 >> step2 >> step3
# Output of step1 → Input of step2 → Output of step2 → Input of step3
```

**Parallel (`|`):** Execute concurrently

```python
workflow = branch1 | branch2 | branch3
# All branches receive same input, execute in parallel
```

---

## Your First Workflow

### Example: Simple Sequential Workflow

{{embed ((sequential-basic-example))}}

### What Just Happened?

1. **Created primitives** using `LambdaPrimitive` to wrap functions
2. **Composed workflow** using `>>` operator (sequential execution)
3. **Executed workflow** with `WorkflowContext` for observability
4. **Got result** after data flowed through all three steps

---

## Your Second Workflow: Parallel Execution

### Example: Multi-LLM Comparison

{{embed ((parallel-llm-comparison))}}

### Key Differences

- Used `|` operator instead of `>>` for **parallel execution**
- All LLMs receive the **same input** (prompt)
- Results collected in **list**: `[gpt4_result, claude_result, llama_result]`
- **Execution time:** `max(llm_times)`, not `sum(llm_times)` 🚀

---

## Understanding WorkflowContext

- id:: understanding-workflow-context
  **WorkflowContext** is how you pass shared state and metadata through workflows. It's immutable and carries:

  - **correlation_id:** For tracing requests across services
  - **data:** Arbitrary metadata (user_id, session_id, etc.)
  - **parent_span:** For distributed tracing (OpenTelemetry)

### Creating a Context

```python
context = WorkflowContext(
    correlation_id="req-12345",
    data={
        "user_id": "user-789",
        "session_id": "sess-456",
        "request_type": "analysis"
    }
)
```

### Why WorkflowContext?

✅ **Observability:** Trace requests across primitives
✅ **No globals:** Pass state explicitly, not via global variables
✅ **Immutable:** Cannot be accidentally modified
✅ **Composable:** Works with all primitives automatically

---

## Common Patterns

### Pattern 1: Input Validation → Processing → Output

```python
{{embed ((standard-imports))}}

workflow = (
    input_validator >>      # Validate schema
    data_enricher >>        # Add metadata
    main_processor >>       # Core logic
    output_formatter        # Format response
)

result = await workflow.execute(input_data, context)
```

### Pattern 2: Parallel Processing → Aggregation

```python
workflow = (
    input_processor >>
    (model1 | model2 | model3) >>  # Parallel LLM calls
    result_aggregator              # Combine results
)
```

### Pattern 3: Dynamic Routing

```python
from tta_dev_primitives import RouterPrimitive

def choose_route(data, context):
    if data["complexity"] == "high":
        return "complex_path"
    else:
        return "simple_path"

router = RouterPrimitive(
    routes={
        "simple_path": fast_workflow,
        "complex_path": thorough_workflow
    },
    routing_fn=choose_route,
    default_route="simple_path"
)

workflow = input_processor >> router >> output_formatter
```

---

## Next Steps

### Learn More Primitives

- [[TTA.dev/Primitives/SequentialPrimitive]] - Sequential execution (you just used this!)
- [[TTA.dev/Primitives/ParallelPrimitive]] - Concurrent execution (you just used this!)
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing
- [[TTA.dev/Primitives/RetryPrimitive]] - Automatic retries
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/CachePrimitive]] - Result caching

### Explore Guides

- [[TTA.dev/Guides/Building Agentic Workflows]] - Build complete workflows
- [[TTA.dev/Guides/Error Handling Patterns]] - Handle failures gracefully
- [[TTA.dev/Guides/Observability Setup]] - Add tracing and metrics
- [[TTA.dev/Guides/Cost Optimization]] - Reduce LLM costs

### Try Examples

- [[TTA.dev/Examples/LLM Router]] - Smart LLM selection
- [[TTA.dev/Examples/Data Pipeline]] - ETL workflow
- [[TTA.dev/Examples/API Workflow]] - Resilient API calls
- [[TTA.dev/Examples/Real-World Workflows]] - Production examples

---

## Common Questions

### Q: Why not just use asyncio.gather()?

**A:** Primitives give you:
- ✅ Automatic observability (tracing, metrics, logs)
- ✅ Type safety with generics
- ✅ Error handling patterns built-in
- ✅ Context propagation automatically
- ✅ Composability and reusability
- ✅ Testing primitives like `MockPrimitive`

### Q: Can I use regular async functions?

**A:** Yes! Wrap them with `LambdaPrimitive`:

```python
async def my_function(data, context):
    # Your async code here
    return result

primitive = LambdaPrimitive(my_function)
workflow = step1 >> primitive >> step3
```

### Q: How do I handle errors?

**A:** Use recovery primitives:

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

# Automatic retry with backoff
reliable = RetryPrimitive(unreliable_step, max_retries=3)

# Fallback to alternative
resilient = FallbackPrimitive(
    primary=expensive_llm,
    fallbacks=[cheap_llm, cached_response]
)
```

### Q: How do I test workflows?

**A:** Use `MockPrimitive`:

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow():
    mock_llm = MockPrimitive(return_value="mocked response")
    workflow = step1 >> mock_llm >> step3

    result = await workflow.execute(input_data, context)
    assert mock_llm.call_count == 1
```

---

## Troubleshooting

### Import Errors

```bash
# Make sure dependencies are synced
uv sync --all-extras

# Verify you're in the virtual environment
which python  # Should point to .venv/bin/python
```

### Type Errors

```bash
# TTA.dev requires Python 3.11+ for modern type hints
python --version  # Should be 3.11 or higher

# Run type checker
uvx pyright packages/
```

### Execution Errors

```python
# Always pass WorkflowContext
context = WorkflowContext(correlation_id="unique-id")
result = await workflow.execute(input_data, context)

# Not:
result = await workflow.execute(input_data)  # ❌ Missing context
```

---

## What You've Learned

- ✅ Installed TTA.dev using `uv`
- ✅ Created sequential workflows with `>>`
- ✅ Created parallel workflows with `|`
- ✅ Used `WorkflowContext` for state management
- ✅ Understood the primitive composition model
- ✅ Saw real-world patterns (routing, error handling)

---

## Keep Learning

- **Documentation:** [[TTA.dev]] - Main hub
- **All Primitives:** [[TTA.dev/Primitives]] - Complete catalog
- **Examples:** [[TTA.dev/Examples]] - Working code
- **Architecture:** [[TTA.dev/Architecture]] - Design decisions

---

## Need Help?

- **GitHub Issues:** <https://github.com/theinterneti/TTA.dev/issues>
- **Discussions:** <https://github.com/theinterneti/TTA.dev/discussions>
- **Documentation:** [[TTA.dev/Guides]]

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 15 minutes
**Difficulty:** [[Beginner]]

- [[Project Hub]]