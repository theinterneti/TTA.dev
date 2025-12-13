# Agentic Primitives

type:: [[Guide]]
category:: [[Core Concepts]]
difficulty:: [[Beginner]]
estimated-time:: 25 minutes
target-audience:: [[Developers]], [[AI Engineers]], [[Architects]]

---

## Overview

- id:: agentic-primitives-overview
  **Agentic Primitives** are the core building blocks of TTA.dev. They are composable, reusable workflow components that enable you to build reliable AI systems through composition rather than complex orchestration code. Think of them as LEGO blocks for AI workflows - small, focused pieces that snap together to create powerful systems.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should understand:**
- Basic async/await in Python
- Function composition concepts
- Why reliability matters in AI systems

---

## What Are Agentic Primitives?

### The Problem They Solve

Traditional AI workflow code looks like this:

```python
# ❌ Complex orchestration code
async def process_user_request(user_input: str):
    # Try primary LLM
    try:
        result = await call_gpt4(user_input)
    except RateLimitError:
        # Wait and retry
        await asyncio.sleep(5)
        try:
            result = await call_gpt4(user_input)
        except Exception:
            # Fallback to cheaper model
            try:
                result = await call_gpt4_mini(user_input)
            except Exception:
                # Use cache
                result = get_cached_response(user_input)

    # Process result
    return format_output(result)
```

**Problems:**
- Hard to test (nested try/except)
- Hard to reuse (specific to this flow)
- Hard to observe (no built-in tracing)
- Hard to modify (change retry logic = rewrite function)

### The Primitive Solution

```python
# ✅ Composable primitives
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Build workflow from primitives
gpt4_with_retry = RetryPrimitive(gpt4, max_retries=2)
gpt4_with_fallback = FallbackPrimitive(
    primary=gpt4_with_retry,
    fallbacks=[gpt4_mini, cached_response]
)

workflow = input_processor >> gpt4_with_fallback >> output_formatter

# Execute
result = await workflow.execute(user_input, context)
```

**Benefits:**
- ✅ Easy to test (each primitive tests independently)
- ✅ Easy to reuse (primitives work in any workflow)
- ✅ Easy to observe (built-in tracing and logging)
- ✅ Easy to modify (swap primitives, no code rewrite)

---

## Core Principles

### 1. Single Responsibility

- id:: agentic-primitives-single-responsibility

Each primitive does **one thing well**:

- **SequentialPrimitive** - Run steps in order
- **ParallelPrimitive** - Run steps concurrently
- **RetryPrimitive** - Retry on failure
- **CachePrimitive** - Cache results

**Not** "SequentialRetryWithCaching" - that's composition!

### 2. Composition Over Inheritance

- id:: agentic-primitives-composition

Build complex behavior by **combining** simple primitives:

```python
# Don't create: ComplexLLMWithRetryAndFallbackAndCache

# Do compose:
workflow = (
    CachePrimitive(                    # Layer 1: Cache
        RetryPrimitive(                # Layer 2: Retry
            FallbackPrimitive(         # Layer 3: Fallback
                primary=expensive_llm,
                fallbacks=[cheap_llm]
            ),
            max_retries=3
        ),
        ttl_seconds=3600
    )
)
```

### 3. Immutability

- id:: agentic-primitives-immutability

Primitives **don't modify** input, they **return new** output:

```python
# ✅ Good: Returns new object
class UpperCasePrimitive(WorkflowPrimitive[str, str]):
    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        return input_data.upper()  # Returns new string

# ❌ Bad: Modifies input
class BadPrimitive(WorkflowPrimitive[dict, dict]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        input_data["modified"] = True  # Mutates input!
        return input_data
```

### 4. Context Propagation

- id:: agentic-primitives-context-propagation

All primitives receive and pass along `WorkflowContext`:

```python
context = WorkflowContext(
    workflow_id="user-signup",
    correlation_id="req-12345",
    metadata={"user_id": "user-789"}
)

# Context flows through entire workflow
result = await workflow.execute(input_data, context)

# Check timing
elapsed = context.elapsed_ms()
```

---

## The Primitive Hierarchy

### Base Class: WorkflowPrimitive

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MyPrimitive(WorkflowPrimitive[InputType, OutputType]):
    async def execute(self, input_data: InputType, context: WorkflowContext) -> OutputType:
        # Your logic here
        return output_data
```

**All primitives extend** `WorkflowPrimitive[T, U]`

### Categories

**Core Primitives** (workflow structure)
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base class
- [[TTA.dev/Primitives/SequentialPrimitive]] - Sequential execution
- [[TTA.dev/Primitives/ParallelPrimitive]] - Parallel execution
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Branching
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing

**Recovery Primitives** (error handling)
- [[TTA.dev/Primitives/RetryPrimitive]] - Automatic retry
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

**Performance Primitives** (optimization)
- [[TTA.dev/Primitives/CachePrimitive]] - Result caching

**Testing Primitives** (verification)
- [[TTA.dev/Primitives/MockPrimitive]] - Testing mocks

---

## Composition Operators

### Sequential: `>>` (Shift Right)

- id:: agentic-primitives-sequential-operator

Execute primitives **in order**, output of one becomes input to next:

```python
workflow = step1 >> step2 >> step3

# Equivalent to:
result1 = await step1.execute(input_data, context)
result2 = await step2.execute(result1, context)
result3 = await step3.execute(result2, context)
```

**Use when:** Steps depend on each other's output

### Parallel: `|` (Pipe)

- id:: agentic-primitives-parallel-operator

Execute primitives **concurrently**, all receive same input:

```python
workflow = branch1 | branch2 | branch3

# Equivalent to:
results = await asyncio.gather(
    branch1.execute(input_data, context),
    branch2.execute(input_data, context),
    branch3.execute(input_data, context)
)
```

**Use when:** Steps are independent, can run in parallel

### Mixed Composition

- id:: agentic-primitives-mixed-composition

Combine both operators for complex workflows:

```python
workflow = (
    input_validator >>                    # Step 1: Validate
    (fast_llm | slow_llm | cached_llm) >> # Step 2: Parallel LLMs
    aggregator >>                         # Step 3: Combine results
    output_formatter                      # Step 4: Format
)
```

---

## Real-World Examples

### Example 1: Content Generation Pipeline

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Step 1: Safety check
safety_checker = LambdaPrimitive(lambda text, ctx: {
    "text": text,
    "is_safe": content_safety_check(text)
})

# Step 2: LLM generation (with retry and cache)
llm_call = LambdaPrimitive(lambda data, ctx: generate_content(data["text"]))
cached_llm = CachePrimitive(llm_call, ttl_seconds=3600)
retry_llm = RetryPrimitive(cached_llm, max_retries=3)

# Step 3: Post-processing
formatter = LambdaPrimitive(lambda data, ctx: format_for_ui(data))

# Compose workflow
content_pipeline = safety_checker >> retry_llm >> formatter

# Execute
result = await content_pipeline.execute("Write about AI safety", context)
```

### Example 2: Multi-LLM Comparison

```python
from tta_dev_primitives import ParallelPrimitive

# Query 3 different LLMs in parallel
gpt4 = LambdaPrimitive(lambda prompt, ctx: call_openai(prompt, "gpt-4"))
claude = LambdaPrimitive(lambda prompt, ctx: call_anthropic(prompt, "claude-3"))
llama = LambdaPrimitive(lambda prompt, ctx: call_local_llm(prompt))

# Run all in parallel
compare_llms = gpt4 | claude | llama

# Get all responses
results = await compare_llms.execute("Explain quantum computing", context)
# results = [gpt4_response, claude_response, llama_response]
```

### Example 3: Cost-Optimized LLM Router

```python
from tta_dev_primitives import RouterPrimitive

def select_llm(input_data: str, context: WorkflowContext) -> str:
    # Simple queries → cheap model
    if len(input_data) < 100:
        return "gpt-4-mini"
    # Complex queries → powerful model
    return "gpt-4"

llm_router = RouterPrimitive(
    routes={
        "gpt-4-mini": cheap_llm,   # $0.0001/request
        "gpt-4": expensive_llm,    # $0.03/request
    },
    route_selector=select_llm
)

# Automatically routes to appropriate LLM
result = await llm_router.execute(user_query, context)
```

---

## Building Your Own Primitive

### Step 1: Extend WorkflowPrimitive

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class SentimentAnalyzer(WorkflowPrimitive[str, dict]):
    """Analyze sentiment of text."""

    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        # Record start
        context.checkpoint("sentiment_analysis.start")

        # Your logic
        sentiment = analyze_sentiment(input_data)

        # Record completion
        context.checkpoint("sentiment_analysis.complete")

        return {
            "text": input_data,
            "sentiment": sentiment,
            "confidence": 0.95
        }
```

### Step 2: Use in Workflow

```python
# Compose with other primitives
workflow = (
    input_cleaner >>
    SentimentAnalyzer() >>
    result_formatter
)

result = await workflow.execute("I love this product!", context)
```

### Step 3: Test

```python
@pytest.mark.asyncio
async def test_sentiment_analyzer():
    analyzer = SentimentAnalyzer()
    context = WorkflowContext()

    result = await analyzer.execute("Great product!", context)

    assert result["sentiment"] == "positive"
    assert result["confidence"] > 0.9
```

---

## Best Practices

### Keep Primitives Focused

✅ **Good:** `ParseJSONPrimitive` - Does one thing
❌ **Bad:** `ParseJSONValidateAndTransformPrimitive` - Does too much (compose instead)

### Use Type Hints

```python
# ✅ Good: Clear input/output types
class ParseIntPrimitive(WorkflowPrimitive[str, int]):
    async def execute(self, input_data: str, context: WorkflowContext) -> int:
        return int(input_data)

# ❌ Bad: No type hints
class ParseIntPrimitive(WorkflowPrimitive):
    async def execute(self, input_data, context):
        return int(input_data)
```

### Add Checkpoints

```python
async def execute(self, input_data: str, context: WorkflowContext) -> dict:
    context.checkpoint("operation.start")

    # Do work
    result = process_data(input_data)

    context.checkpoint("operation.complete")
    return result
```

### Handle Errors Gracefully

```python
async def execute(self, input_data: str, context: WorkflowContext) -> dict:
    try:
        return await risky_operation(input_data)
    except ValueError as e:
        logger.error("validation_error", error=str(e))
        raise  # Re-raise for caller to handle
    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        raise
```

---

## Why "Agentic"?

The term **"Agentic"** refers to the ability of AI systems to:

1. **Make autonomous decisions** (ConditionalPrimitive, RouterPrimitive)
2. **Recover from failures** (RetryPrimitive, FallbackPrimitive)
3. **Adapt behavior** (RouterPrimitive based on context)
4. **Coordinate actions** (SequentialPrimitive, ParallelPrimitive)

Primitives enable building **agent-like systems** that don't need constant human intervention.

---

## Primitives vs Traditional Code

| Aspect | Traditional Code | Agentic Primitives |
|--------|------------------|-------------------|
| **Reusability** | Copy/paste functions | Import and compose |
| **Testing** | Mock entire workflow | Test each primitive |
| **Observability** | Manual logging | Built-in tracing |
| **Error Handling** | Nested try/except | Recovery primitives |
| **Composition** | Function calls | Operators (`>>`, `|`) |
| **Readability** | Imperative code | Declarative workflow |

---

## Common Patterns

### The Reliability Stack

```python
# Layer 1: Cache (avoid work)
# Layer 2: Retry (handle transient failures)
# Layer 3: Fallback (degrade gracefully)

reliable_operation = (
    CachePrimitive(
        RetryPrimitive(
            FallbackPrimitive(
                primary=expensive_service,
                fallbacks=[cheap_service, cached_data]
            ),
            max_retries=3
        ),
        ttl_seconds=3600
    )
)
```

### The Validation Pipeline

```python
# Validate → Process → Transform → Output
workflow = (
    input_validator >>
    data_processor >>
    result_transformer >>
    output_formatter
)
```

### The Parallel Fan-Out

```python
# One input → Multiple processors → Aggregate
workflow = (
    input_processor >>
    (processor1 | processor2 | processor3) >>
    result_aggregator
)
```

---

## Next Steps

- **Learn composition:** [[TTA.dev/Guides/Workflow Composition]]
- **Handle errors:** [[TTA.dev/Guides/Error Handling Patterns]]
- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Browse catalog:** [[PRIMITIVES CATALOG]]

---

## Related Content

### All Primitives

{{query (page-property type [[Primitive]])}}

### Essential Guides

- [[TTA.dev/Guides/Getting Started]] - Setup and first workflow
- [[TTA.dev/Guides/Workflow Composition]] - Advanced composition patterns
- [[TTA.dev/Guides/Error Handling Patterns]] - Building resilient workflows

---

## Key Takeaways

1. **Primitives are building blocks** - Small, focused, composable
2. **Composition beats complexity** - Combine simple pieces for power
3. **Operators make it intuitive** - `>>` for sequential, `|` for parallel
4. **Context flows through** - WorkflowContext carries state
5. **Built-in observability** - Tracing and logging automatic
6. **Easy to test** - Each primitive tests independently

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 25 minutes
**Difficulty:** [[Beginner]]

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___guides___agentic primitives]]
