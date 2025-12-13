# Examples

**Tag page for code examples, tutorials, and working demonstrations**

---

## Overview

**Examples** in TTA.dev demonstrate:
- 💻 Working code patterns
- 📚 Real-world use cases
- 🎓 Learning scenarios
- 🔧 Integration examples
- 🚀 Production patterns

**Goal:** Provide runnable, understandable examples for all TTA.dev features.

**See:** [[TTA.dev/Examples]], [[Learning TTA Primitives]]

---

## Pages Tagged with #Examples

{{query (page-tags [[Examples]])}}

---

## Example Categories

### 1. Basic Examples

**Foundation patterns:**

**Sequential Workflow:**
```python
from tta_dev_primitives import WorkflowContext

async def basic_sequential():
    """Simple sequential workflow."""
    workflow = step1 >> step2 >> step3

    context = WorkflowContext(correlation_id="demo")
    result = await workflow.execute(input_data, context)
    return result
```

**Parallel Execution:**
```python
async def basic_parallel():
    """Concurrent execution."""
    workflow = branch1 | branch2 | branch3

    results = await workflow.execute(input_data, context)
    return results  # [result1, result2, result3]
```

**See:** `packages/tta-dev-primitives/examples/basic_workflow.py`

---

### 2. Recovery Examples

**Error handling patterns:**

**Retry Pattern:**
```python
from tta_dev_primitives.recovery import RetryPrimitive

async def retry_example():
    """Retry with exponential backoff."""
    retry = RetryPrimitive(
        max_retries=3,
        backoff_strategy="exponential",
        initial_delay=1.0,
        jitter=True
    )

    workflow = retry >> api_call
    result = await workflow.execute(data, context)
    return result
```

**Fallback Pattern:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive

async def fallback_example():
    """Graceful degradation."""
    fallback = FallbackPrimitive(
        primary=openai_gpt4,
        fallbacks=[anthropic_claude, google_gemini]
    )

    result = await fallback.execute(prompt, context)
    return result
```

**See:** `packages/tta-dev-primitives/examples/error_handling_patterns.py`

---

### 3. Performance Examples

**Optimization patterns:**

**Caching:**
```python
from tta_dev_primitives.performance import CachePrimitive

async def cache_example():
    """LRU cache with TTL."""
    cache = CachePrimitive(
        ttl_seconds=3600,  # 1 hour
        max_size=1000
    )

    workflow = cache >> expensive_llm_call
    result = await workflow.execute(prompt, context)
    return result
```

**Memory:**
```python
from tta_dev_primitives.performance import MemoryPrimitive

async def memory_example():
    """Conversational memory."""
    memory = MemoryPrimitive(max_size=100)

    # Store conversation
    await memory.add("user_msg_1", {"role": "user", "content": "Hello"})

    # Search history
    history = await memory.search(keywords=["hello"])
    return history
```

**See:** `packages/tta-dev-primitives/examples/performance_patterns.py`

---

### 4. Real-World Examples

**Production-ready patterns:**

**RAG Workflow:**
```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

async def rag_workflow(query: str):
    """Production RAG pipeline."""
    # Cache embeddings
    cached_embeddings = CachePrimitive(
        ttl_seconds=3600,
        max_size=10000
    )

    # Retry retrieval
    retry_retrieval = RetryPrimitive(
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Fallback LLM
    fallback_llm = FallbackPrimitive(
        primary=gpt4,
        fallbacks=[claude, gemini]
    )

    # Compose workflow
    workflow = (
        cached_embeddings >>
        retry_retrieval >>
        fallback_llm
    )

    context = WorkflowContext(correlation_id=f"rag-{query}")
    result = await workflow.execute({"query": query}, context)
    return result
```

**See:** `packages/tta-dev-primitives/examples/rag_workflow.py`

---

**Cost Tracking:**
```python
from tta_dev_primitives.observability import BudgetPrimitive

async def cost_tracking_example():
    """Track and enforce budget."""
    budget = BudgetPrimitive(
        daily_limit_usd=100.0,
        alert_threshold=0.8
    )

    workflow = budget >> expensive_operation
    result = await workflow.execute(data, context)

    # Check usage
    usage = budget.get_usage()
    print(f"Spent: ${usage['spent']:.2f} / ${usage['limit']:.2f}")
    return result
```

**See:** `packages/tta-dev-primitives/examples/cost_tracking_workflow.py`

---

**Multi-Agent:**
```python
from tta_dev_primitives.orchestration import DelegationPrimitive

async def multi_agent_example():
    """Orchestrator + executors."""
    workflow = DelegationPrimitive(
        orchestrator=claude_sonnet,  # Plan
        executor=gemini_flash         # Execute
    )

    result = await workflow.execute(complex_task, context)
    return result
```

**See:** `packages/tta-dev-primitives/examples/multi_agent_workflow.py`

---

### 5. Integration Examples

**External service integration:**

**Supabase Integration:**
```python
from tta_dev_primitives import WorkflowPrimitive

class SupabasePrimitive(WorkflowPrimitive):
    """Custom Supabase primitive."""

    def __init__(self, supabase_client):
        super().__init__()
        self.client = supabase_client

    async def _execute(self, data, context):
        """Query Supabase."""
        result = await self.client.table('data').select('*').execute()
        return result.data
```

**GitHub Integration:**
```python
async def github_integration_example():
    """Integrate with GitHub API."""
    workflow = (
        fetch_github_issues >>
        classify_issues >>
        route_to_agent
    )

    result = await workflow.execute({"repo": "owner/repo"}, context)
    return result
```

**See:** `packages/tta-dev-primitives/examples/integration_examples.py`

---

### 6. Observability Examples

**Tracing and metrics:**

**OpenTelemetry:**
```python
from opentelemetry import trace
from observability_integration import initialize_observability

async def observability_example():
    """Full observability setup."""
    # Initialize
    initialize_observability(
        service_name="my-app",
        enable_prometheus=True
    )

    # Create workflow with tracing
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("my_workflow") as span:
        span.set_attribute("input_size", len(data))

        workflow = step1 >> step2 >> step3
        result = await workflow.execute(data, context)

        span.set_attribute("output_size", len(result))
        return result
```

**See:** `packages/tta-dev-primitives/examples/observability.py`

---

## Example TODOs

### Example Creation TODOs

**Examples to create:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "examples"))}}

---

## Example Structure

### Good Example Pattern

```python
"""
Example: [Descriptive Name]

Demonstrates:
- Feature 1
- Feature 2
- Feature 3

Prerequisites:
- Package installed
- Environment setup
- Any API keys

Usage:
    python example.py
"""

import asyncio
from tta_dev_primitives import WorkflowContext

async def main():
    """Main example function."""
    # Setup
    context = WorkflowContext(correlation_id="example")

    # Example workflow
    workflow = step1 >> step2 >> step3

    # Execute
    result = await workflow.execute(input_data, context)

    # Display results
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    # Run example
    result = asyncio.run(main())
    print(f"✅ Example completed: {result}")
```

---

## Example Locations

### Package Examples

```
packages/tta-dev-primitives/
└── examples/
    ├── basic_workflow.py          # Foundation
    ├── composition.py              # Operators
    ├── error_handling_patterns.py  # Recovery
    ├── performance_patterns.py     # Optimization
    ├── rag_workflow.py            # Production RAG
    ├── agentic_rag_workflow.py    # Enhanced RAG
    ├── cost_tracking_workflow.py  # Budget tracking
    ├── streaming_workflow.py      # Streaming
    ├── multi_agent_workflow.py    # Orchestration
    └── memory_workflow.py         # Conversational memory
```

**See:** [[tta-dev-primitives]]

---

### Documentation Examples

```
docs/
└── examples/
    ├── getting_started.md         # Quick start
    ├── integration_patterns.md    # Integrations
    ├── production_patterns.md     # Production
    └── advanced_patterns.md       # Advanced
```

---

### Tutorial Examples

**Logseq tutorials:**
- [[Tutorial - Building Your First Workflow]]
- [[Tutorial - Adding Error Handling]]
- [[Tutorial - Performance Optimization]]
- [[Tutorial - Production Deployment]]

---

## Running Examples

### Local Execution

```bash
# Run specific example
uv run python packages/tta-dev-primitives/examples/rag_workflow.py

# Run all examples
for file in packages/tta-dev-primitives/examples/*.py; do
    echo "Running $file"
    uv run python "$file"
done

# Run with observability
docker-compose -f docker-compose.test.yml up -d
uv run python packages/tta-dev-primitives/examples/observability.py
```

---

### Testing Examples

```bash
# Test examples as doctests
uv run pytest packages/tta-dev-primitives/examples/ --doctest-modules

# Run example tests
uv run pytest packages/tta-dev-primitives/tests/examples/

# Validate examples run
./scripts/validate_examples.sh
```

---

## Best Practices

### ✅ DO

**Complete and Runnable:**
```python
# ✅ Good: Complete example
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive

async def complete_example():
    """Working retry example."""
    retry = RetryPrimitive(max_retries=3)
    workflow = retry >> api_call

    context = WorkflowContext(correlation_id="demo")
    result = await workflow.execute({"url": "..."}, context)
    return result

# Can copy-paste and run immediately
```

**Clear Purpose:**
```python
"""
Example: Exponential Backoff Retry

Demonstrates:
- RetryPrimitive usage
- Exponential backoff strategy
- Jitter for thundering herd
- Error handling

When to use:
- Transient failures
- Rate-limited APIs
- Network instability
"""
```

**Expected Output:**
```python
async def example_with_output():
    """Example with expected results."""
    result = await workflow.execute(data, context)

    print(f"Expected: {{'status': 'success', 'data': [...]}}")
    print(f"Actual:   {result}")

    assert result['status'] == 'success'
    return result
```

---

### ❌ DON'T

**Don't Use Incomplete Examples:**
```python
# ❌ Bad: Won't run
workflow = thing >> other_thing

# ✅ Good: Complete imports and setup
from tta_dev_primitives import WorkflowPrimitive
workflow = step1 >> step2
```

**Don't Use Unrealistic Data:**
```python
# ❌ Bad: Fake data
result = await workflow.execute({"data": "..."}, context)

# ✅ Good: Realistic data
result = await workflow.execute({
    "prompt": "Explain quantum computing",
    "max_tokens": 500,
    "temperature": 0.7
}, context)
```

**Don't Skip Error Handling:**
```python
# ❌ Bad: No error handling
result = await api_call()

# ✅ Good: Show error patterns
try:
    result = await api_call()
except APIError as e:
    logger.error(f"API failed: {e}")
    result = fallback_response
```

---

## Example Patterns

### Tutorial Pattern

**Step-by-step learning:**

```python
"""
Tutorial: Building a Resilient LLM Pipeline

Step 1: Basic LLM Call
Step 2: Add Retry
Step 3: Add Fallback
Step 4: Add Caching
Step 5: Add Observability
"""

# Step 1: Basic LLM Call
async def step1_basic():
    """Simple LLM call."""
    result = await llm_call(prompt)
    return result

# Step 2: Add Retry
async def step2_retry():
    """Add retry for reliability."""
    retry = RetryPrimitive(max_retries=3)
    workflow = retry >> llm_call
    result = await workflow.execute(prompt, context)
    return result

# ... Steps 3-5 continue building
```

---

### Comparison Pattern

**Show alternatives:**

```python
"""
Comparison: Sequential vs Parallel Execution

Demonstrates performance difference between sequential
and parallel execution for independent operations.
"""

# Sequential (slow)
async def sequential_example():
    """Execute in sequence: 3 seconds."""
    result1 = await op1()  # 1s
    result2 = await op2()  # 1s
    result3 = await op3()  # 1s
    return [result1, result2, result3]

# Parallel (fast)
async def parallel_example():
    """Execute concurrently: 1 second."""
    workflow = op1 | op2 | op3
    results = await workflow.execute(data, context)
    return results  # All complete in ~1s

# Benchmark
print(f"Sequential: {sequential_time}s")
print(f"Parallel: {parallel_time}s")
print(f"Speedup: {sequential_time / parallel_time}x")
```

---

### Real-World Pattern

**Production-ready:**

```python
"""
Real-World: Production LLM Service

Full production deployment example including:
- Multi-model routing
- Cost optimization
- Error handling
- Observability
- Rate limiting
"""

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive
from observability_integration import initialize_observability

async def production_llm_service():
    """Complete production service."""
    # Initialize observability
    initialize_observability(service_name="llm-service")

    # Layer 1: Cache
    cache = CachePrimitive(ttl_seconds=3600, max_size=10000)

    # Layer 2: Router
    router = RouterPrimitive(
        routes={"fast": gpt4_mini, "quality": gpt4},
        router_fn=select_model
    )

    # Layer 3: Retry
    retry = RetryPrimitive(max_retries=3)

    # Layer 4: Fallback
    fallback = FallbackPrimitive(
        primary=router,
        fallbacks=[claude, gemini]
    )

    # Compose
    workflow = cache >> retry >> fallback

    # Execute
    context = WorkflowContext(correlation_id="prod-123")
    result = await workflow.execute(prompt, context)
    return result
```

**See:** `packages/tta-dev-primitives/examples/real_world_workflows.py`

---

## Related Concepts

- [[TTA.dev/Examples]] - Example index
- [[Learning TTA Primitives]] - Learning resources
- [[Documentation]] - Documentation
- [[Tutorial]] - Tutorials
- [[tta-dev-primitives]] - Core package

---

## Documentation

- [[GETTING_STARTED]] - Quick start
- [[PRIMITIVES_CATALOG]] - Primitive reference
- [[TTA.dev/Integration Guide]] - Integration guide
- [[TTA.dev/Best Practices]] - Best practices

---

**Tags:** #examples #tutorials #learning #code #patterns #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Examples]]
