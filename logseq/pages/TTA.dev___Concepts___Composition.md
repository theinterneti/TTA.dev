# TTA.dev/Concepts/Composition

**Combining primitives to create complex workflows**

---

## Overview

Composition is the fundamental concept in TTA.dev that enables building complex AI workflows from simple, reusable primitives. Instead of writing monolithic functions, you compose small building blocks using intuitive operators.

**Core Principle:** Complex workflows emerge from simple primitives
**Key Operators:** `>>` (sequential), `|` (parallel)
**Foundation:** [[WorkflowPrimitive]]

---

## Why Composition?

### Benefits

1. **Reusability** - Write once, use everywhere
2. **Testability** - Test individual primitives in isolation
3. **Maintainability** - Clear, declarative workflow structure
4. **Observability** - Automatic tracing for each primitive
5. **Type Safety** - Compile-time guarantees for data flow

### Comparison

```python
# ❌ Monolithic approach (hard to test, maintain, observe)
async def process_document(doc: str) -> dict:
    # Extract text
    text = await extract_text(doc)

    # Generate embeddings
    embeddings = await generate_embeddings(text)

    # Store in vector DB
    result = await store_embeddings(embeddings)

    return result

# ✅ Compositional approach (testable, observable, reusable)
from tta_dev_primitives import SequentialPrimitive

workflow = (
    extract_text_primitive >>
    generate_embeddings_primitive >>
    store_embeddings_primitive
)

result = await workflow.execute({"document": doc}, context)
```

---

## Sequential Composition

### The `>>` Operator

Sequential composition chains primitives where each step's output becomes the next step's input:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

# Define primitives
async def step1(data: dict, context: WorkflowContext) -> dict:
    return {"result": data["input"].upper()}

async def step2(data: dict, context: WorkflowContext) -> dict:
    return {"result": f"Processed: {data['result']}"}

async def step3(data: dict, context: WorkflowContext) -> dict:
    return {"result": f"Final: {data['result']}"}

# Compose sequentially
workflow = step1 >> step2 >> step3

# Execute
context = WorkflowContext(workflow_id="sequential-demo")
result = await workflow.execute({"input": "hello"}, context)

# Result: {"result": "Final: Processed: HELLO"}
```

**Data Flow:**
```
input → step1 → result1 → step2 → result2 → step3 → output
```

### Explicit Sequential Primitive

```python
from tta_dev_primitives import SequentialPrimitive

# Equivalent to using >> operator
workflow = SequentialPrimitive([
    step1,
    step2,
    step3
])
```

---

## Parallel Composition

### The `|` Operator

Parallel composition executes primitives concurrently with the same input:

```python
from tta_dev_primitives import WorkflowContext

# Define parallel branches
async def fast_path(data: dict, context: WorkflowContext) -> dict:
    return {"branch": "fast", "result": "Quick result"}

async def quality_path(data: dict, context: WorkflowContext) -> dict:
    await asyncio.sleep(0.1)  # Simulate slower, higher quality
    return {"branch": "quality", "result": "Detailed result"}

async def cached_path(data: dict, context: WorkflowContext) -> dict:
    return {"branch": "cached", "result": "Cached result"}

# Compose in parallel
workflow = fast_path | quality_path | cached_path

# Execute
context = WorkflowContext(workflow_id="parallel-demo")
results = await workflow.execute({"input": "test"}, context)

# Results: [
#   {"branch": "fast", "result": "Quick result"},
#   {"branch": "quality", "result": "Detailed result"},
#   {"branch": "cached", "result": "Cached result"}
# ]
```

**Data Flow:**
```
           ┌─→ fast_path ─→ result1
input ─────┼─→ quality_path → result2
           └─→ cached_path ─→ result3
```

### Explicit Parallel Primitive

```python
from tta_dev_primitives import ParallelPrimitive

# Equivalent to using | operator
workflow = ParallelPrimitive([
    fast_path,
    quality_path,
    cached_path
])
```

---

## Mixed Composition

### Sequential + Parallel

Combine both patterns for sophisticated workflows:

```python
from tta_dev_primitives import WorkflowContext

# Input processing (sequential)
async def validate_input(data: dict, context: WorkflowContext) -> dict:
    return {"validated": True, "data": data}

# Parallel processing branches
async def analyze_sentiment(data: dict, context: WorkflowContext) -> dict:
    return {"sentiment": "positive"}

async def extract_entities(data: dict, context: WorkflowContext) -> dict:
    return {"entities": ["TTA.dev", "Python"]}

async def classify_topic(data: dict, context: WorkflowContext) -> dict:
    return {"topic": "AI Development"}

# Result aggregation (sequential)
async def aggregate_results(data: dict, context: WorkflowContext) -> dict:
    return {
        "summary": "Analysis complete",
        "results": data
    }

# Compose: sequential → parallel → sequential
workflow = (
    validate_input >>
    (analyze_sentiment | extract_entities | classify_topic) >>
    aggregate_results
)

# Execute
result = await workflow.execute({"text": "TTA.dev is great!"}, context)
```

**Data Flow:**
```
input → validate_input → validated_data
                               │
                     ┌─────────┼─────────┐
                     ↓         ↓         ↓
            analyze_sentiment  extract  classify
                     │         entities  topic
                     └─────────┼─────────┘
                               ↓
                        aggregate_results
                               ↓
                            output
```

---

## Nested Composition

### Composing Composed Workflows

```python
# Build sub-workflows
preprocessing = (
    load_document >>
    extract_text >>
    clean_text
)

analysis = (
    tokenize >>
    (analyze_sentiment | extract_entities | classify_topic) >>
    aggregate_analysis
)

postprocessing = (
    format_results >>
    add_metadata >>
    save_output
)

# Compose sub-workflows into main workflow
main_workflow = (
    preprocessing >>
    analysis >>
    postprocessing
)

# Clean, hierarchical structure
result = await main_workflow.execute({"document": doc}, context)
```

---

## Conditional Composition

### Dynamic Routing

```python
from tta_dev_primitives import ConditionalPrimitive

# Define branches
async def simple_processing(data: dict, context: WorkflowContext) -> dict:
    return {"processed": "simple", "data": data}

async def complex_processing(data: dict, context: WorkflowContext) -> dict:
    return {"processed": "complex", "data": data}

# Conditional composition
def is_complex(data: dict, context: WorkflowContext) -> bool:
    return len(data.get("text", "")) > 1000

conditional_step = ConditionalPrimitive(
    condition=is_complex,
    then_primitive=complex_processing,
    else_primitive=simple_processing
)

# Use in workflow
workflow = (
    validate_input >>
    conditional_step >>
    format_output
)
```

### Router-Based Composition

```python
from tta_dev_primitives.core import RouterPrimitive

# Define routes
routes = {
    "fast": gpt4_mini_primitive,
    "balanced": gpt4_primitive,
    "quality": claude_sonnet_primitive
}

def select_route(data: dict, context: WorkflowContext) -> str:
    priority = data.get("priority", "balanced")
    return priority

router = RouterPrimitive(
    routes=routes,
    router_fn=select_route,
    default="balanced"
)

# Use in workflow
workflow = (
    preprocess >>
    router >>  # Dynamic routing based on priority
    postprocess
)
```

---

## Composition with Recovery

### Adding Resilience

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# Unreliable operation with recovery
reliable_operation = (
    TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=external_api_call,
            max_retries=3,
            backoff_strategy="exponential"
        ),
        timeout_seconds=10.0
    )
)

# Use in larger workflow
workflow = (
    prepare_request >>
    reliable_operation >>
    process_response
)
```

### Fallback Chains

```python
# Primary → Backup → Cache
resilient_llm = FallbackPrimitive(
    primary=openai_gpt4,
    fallbacks=[
        anthropic_claude,
        google_gemini,
        cached_responses
    ]
)

workflow = (
    format_prompt >>
    resilient_llm >>
    parse_response
)
```

---

## Composition with Caching

### Performance Optimization

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive operations
cached_embedding = CachePrimitive(
    primitive=generate_embeddings,
    ttl_seconds=3600,
    max_size=1000
)

cached_llm = CachePrimitive(
    primitive=llm_generation,
    ttl_seconds=1800,
    max_size=500
)

# Compose with caching
workflow = (
    extract_text >>
    cached_embedding >>  # Cache embeddings
    query_vector_db >>
    cached_llm >>        # Cache LLM responses
    format_output
)
```

---

## Type-Safe Composition

### Generic Type Parameters

```python
from tta_dev_primitives import WorkflowPrimitive
from typing import TypeVar

TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')

class TypedPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Type-safe primitive."""

    async def _execute_impl(
        self,
        data: TInput,
        context: WorkflowContext
    ) -> TOutput:
        # Implementation
        pass

# Type checker verifies composition
step1: WorkflowPrimitive[str, dict] = ...
step2: WorkflowPrimitive[dict, list] = ...
step3: WorkflowPrimitive[list, str] = ...

# Type-safe composition
workflow = step1 >> step2 >> step3  # Type: WorkflowPrimitive[str, str]
```

---

## Best Practices

### 1. Keep Primitives Small

```python
# ✅ Good: Small, focused primitives
extract_text = TextExtractionPrimitive()
clean_text = TextCleaningPrimitive()
tokenize = TokenizationPrimitive()

workflow = extract_text >> clean_text >> tokenize

# ❌ Bad: Large, monolithic primitive
everything = DoEverythingPrimitive()
```

### 2. Name Workflows Descriptively

```python
# ✅ Good: Clear intent
rag_retrieval_workflow = (
    embed_query >>
    search_vector_db >>
    rerank_results
)

# ❌ Bad: Generic name
workflow1 = step1 >> step2 >> step3
```

### 3. Use Parentheses for Clarity

```python
# ✅ Good: Clear grouping
workflow = (
    preprocess >>
    (fast_llm | quality_llm | cached_llm) >>
    postprocess
)

# ❌ Confusing: Ambiguous precedence
workflow = preprocess >> fast_llm | quality_llm | cached_llm >> postprocess
```

### 4. Extract Common Patterns

```python
# ✅ Good: Reusable sub-workflows
def create_resilient_llm(llm_primitive):
    return TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=llm_primitive,
            max_retries=3
        ),
        timeout_seconds=30.0
    )

# Use pattern
gpt4_resilient = create_resilient_llm(gpt4_primitive)
claude_resilient = create_resilient_llm(claude_primitive)
```

---

## Anti-Patterns

### ❌ Don't Break Composition

```python
# Bad: Mixing composition with manual async
workflow = step1 >> step2

async def bad_workflow(data, context):
    result1 = await workflow.execute(data, context)
    # Manual async breaks composition
    result2 = await some_other_operation(result1)
    return result2

# Good: Keep everything composed
workflow = step1 >> step2 >> step3
```

### ❌ Don't Ignore Context

```python
# Bad: Not passing context
async def bad_primitive(data: dict, context: WorkflowContext) -> dict:
    # Ignores context, loses tracing
    return await some_operation(data)

# Good: Use context
async def good_primitive(data: dict, context: WorkflowContext) -> dict:
    logger.info("Processing", correlation_id=context.correlation_id)
    return await some_operation(data, context)
```

---

## Related Concepts

- [[TTA.dev/Concepts/Observability]] - Automatic tracing in composition
- [[TTA.dev/Concepts/Context Propagation]] - How context flows through composition
- [[TTA.dev/Concepts/Recovery]] - Error handling in composition

---

## Related Patterns

- [[TTA.dev/Patterns/Sequential Workflow]] - Sequential composition patterns
- [[TTA.dev/Patterns/Parallel Execution]] - Parallel composition patterns
- [[TTA.dev/Patterns/Caching]] - Caching in composed workflows

---

## Related Primitives

- [[WorkflowPrimitive]] - Base for all primitives
- [[SequentialPrimitive]] - Sequential composition
- [[ParallelPrimitive]] - Parallel composition
- [[ConditionalPrimitive]] - Conditional branching
- [[RouterPrimitive]] - Dynamic routing

---

## Related Examples

- [[TTA.dev/Examples/RAG Workflow]] - Composition in RAG
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Agent composition
- [[TTA.dev/Examples/Basic Workflow]] - Simple composition

---

**Category:** Core Concept
**Complexity:** Medium
**Status:** Production-ready

- [[Project Hub]]