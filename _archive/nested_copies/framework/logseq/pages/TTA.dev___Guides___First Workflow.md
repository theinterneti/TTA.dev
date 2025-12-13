# First Workflow Guide

**Build your first complete TTA.dev workflow from scratch**

type:: Guide
audience:: new-users
difficulty:: beginner
estimated-time:: 20 minutes
status:: Complete
related:: [[TTA Primitives]], [[TTA.dev/Guides/Beginner Quickstart]], [[TTA.dev/Guides/Workflow Composition]]
prerequisites:: [[TTA.dev/Guides/Beginner Quickstart]]

---

## 🎯 What You'll Build

A production-ready LLM workflow with:
- ✅ Input validation
- ✅ Caching (cost optimization)
- ✅ Retry logic (reliability)
- ✅ Timeout protection (stability)
- ✅ Fallback handling (availability)
- ✅ Full observability

### Final Result

```python
workflow = (
    ValidateInputPrimitive() >>
    CachePrimitive(ttl_seconds=3600) >>
    TimeoutPrimitive(timeout_seconds=30) >>
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(
        primary=GPT4Primitive(),
        fallback=GPT35Primitive()
    ) >>
    FormatOutputPrimitive()
)
```

---

## 📋 Prerequisites

Before starting:
- ✅ Completed [[TTA.dev/Guides/Beginner Quickstart]]
- ✅ Python 3.11+ installed
- ✅ `tta-dev-primitives` package installed
- ✅ Basic understanding of async/await

---

## 🏗️ Step-by-Step Build

### Step 1: Set Up Project

Create a new directory and file:

```bash
mkdir my-first-workflow
cd my-first-workflow
touch workflow.py
```

### Step 2: Define Custom Primitives

We'll create simple primitives for our workflow:

```python
import asyncio
from typing import Dict, Any
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class ValidateInputPrimitive(WorkflowPrimitive[Dict[str, Any], Dict[str, Any]]):
    """Validates that input has required fields."""

    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        # Check required fields
        if "prompt" not in input_data:
            raise ValueError("Missing required field: prompt")

        if not isinstance(input_data["prompt"], str):
            raise TypeError("Prompt must be a string")

        # Add metadata
        return {
            **input_data,
            "validated_at": context.correlation_id,
            "status": "validated"
        }

class ProcessLLMPrimitive(WorkflowPrimitive[Dict[str, Any], Dict[str, Any]]):
    """Simulates an LLM call (replace with real API call)."""

    def __init__(self, model_name: str = "gpt-4"):
        super().__init__()
        self.model_name = model_name

    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        # Simulate API call
        prompt = input_data["prompt"]

        # In production: call OpenAI, Anthropic, etc.
        response = f"[{self.model_name}] Response to: {prompt}"

        return {
            "prompt": prompt,
            "response": response,
            "model": self.model_name,
            "context_id": context.correlation_id
        }

class FormatOutputPrimitive(WorkflowPrimitive[Dict[str, Any], str]):
    """Formats the output for display."""

    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: WorkflowContext
    ) -> str:
        return f"""
=== LLM Response ===
Model: {input_data.get('model', 'unknown')}
Prompt: {input_data.get('prompt', 'N/A')}
Response: {input_data.get('response', 'N/A')}
Context ID: {input_data.get('context_id', 'N/A')}
====================
        """.strip()
```

### Step 3: Build Basic Workflow

Start simple with just the core primitives:

```python
async def basic_workflow():
    """Basic workflow without error handling."""

    # Create workflow
    workflow = (
        ValidateInputPrimitive() >>
        ProcessLLMPrimitive(model_name="gpt-4") >>
        FormatOutputPrimitive()
    )

    # Execute
    context = WorkflowContext(correlation_id="basic-001")
    input_data = {"prompt": "What is TTA.dev?"}

    result = await workflow.execute(input_data, context)
    print("Basic Workflow Result:")
    print(result)
    print()

# Run it
asyncio.run(basic_workflow())
```

**Output:**
```
Basic Workflow Result:
=== LLM Response ===
Model: gpt-4
Prompt: What is TTA.dev?
Response: [gpt-4] Response to: What is TTA.dev?
Context ID: basic-001
====================
```

---

### Step 4: Add Caching (Cost Optimization)

Add caching to avoid redundant LLM calls:

```python
from tta_dev_primitives.performance import CachePrimitive

async def cached_workflow():
    """Workflow with caching for cost optimization."""

    # Create workflow with cache
    workflow = (
        ValidateInputPrimitive() >>
        CachePrimitive(
            primitive=ProcessLLMPrimitive(model_name="gpt-4"),
            ttl_seconds=3600,  # Cache for 1 hour
            max_size=1000      # Max 1000 entries
        ) >>
        FormatOutputPrimitive()
    )

    context = WorkflowContext(correlation_id="cached-001")
    input_data = {"prompt": "What is TTA.dev?"}

    # First call - cache miss
    print("First call (cache miss):")
    result1 = await workflow.execute(input_data, context)
    print(result1)
    print()

    # Second call - cache hit!
    print("Second call (cache hit - much faster!):")
    result2 = await workflow.execute(input_data, context)
    print(result2)
    print()

asyncio.run(cached_workflow())
```

**Benefits:**
- 🚀 **40-60% cost reduction** (typical)
- ⚡ **100x faster** on cache hits
- 💾 **Automatic LRU eviction**

---

### Step 5: Add Retry Logic (Reliability)

Handle transient failures automatically:

```python
from tta_dev_primitives.recovery import RetryPrimitive

async def reliable_workflow():
    """Workflow with automatic retry on failures."""

    workflow = (
        ValidateInputPrimitive() >>
        CachePrimitive(
            primitive=RetryPrimitive(
                primitive=ProcessLLMPrimitive(model_name="gpt-4"),
                max_retries=3,
                backoff_strategy="exponential",
                initial_delay=1.0,
                jitter=True  # Prevents thundering herd
            ),
            ttl_seconds=3600
        ) >>
        FormatOutputPrimitive()
    )

    context = WorkflowContext(correlation_id="reliable-001")
    input_data = {"prompt": "What is TTA.dev?"}

    result = await workflow.execute(input_data, context)
    print("Reliable Workflow Result:")
    print(result)

asyncio.run(reliable_workflow())
```

**Retry Strategy:**
- Attempt 1: Immediate
- Attempt 2: ~1 second delay
- Attempt 3: ~2 second delay
- Attempt 4: ~4 second delay

---

### Step 6: Add Timeout Protection (Stability)

Prevent hanging requests:

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

async def stable_workflow():
    """Workflow with timeout protection."""

    workflow = (
        ValidateInputPrimitive() >>
        CachePrimitive(
            primitive=TimeoutPrimitive(
                primitive=RetryPrimitive(
                    primitive=ProcessLLMPrimitive(model_name="gpt-4"),
                    max_retries=3,
                    backoff_strategy="exponential"
                ),
                timeout_seconds=30.0,  # Max 30 seconds
                raise_on_timeout=True
            ),
            ttl_seconds=3600
        ) >>
        FormatOutputPrimitive()
    )

    context = WorkflowContext(correlation_id="stable-001")
    input_data = {"prompt": "What is TTA.dev?"}

    try:
        result = await workflow.execute(input_data, context)
        print("Stable Workflow Result:")
        print(result)
    except TimeoutError:
        print("Request timed out after 30 seconds")

asyncio.run(stable_workflow())
```

---

### Step 7: Add Fallback (High Availability)

Use cheaper model if primary fails:

```python
from tta_dev_primitives.recovery import FallbackPrimitive

async def production_workflow():
    """Production-ready workflow with all safeguards."""

    workflow = (
        ValidateInputPrimitive() >>
        CachePrimitive(
            primitive=TimeoutPrimitive(
                primitive=RetryPrimitive(
                    primitive=FallbackPrimitive(
                        primary=ProcessLLMPrimitive(model_name="gpt-4"),
                        fallbacks=[
                            ProcessLLMPrimitive(model_name="gpt-3.5-turbo"),
                            ProcessLLMPrimitive(model_name="local-llama")
                        ]
                    ),
                    max_retries=3,
                    backoff_strategy="exponential"
                ),
                timeout_seconds=30.0
            ),
            ttl_seconds=3600
        ) >>
        FormatOutputPrimitive()
    )

    context = WorkflowContext(correlation_id="production-001")
    input_data = {"prompt": "What is TTA.dev?"}

    result = await workflow.execute(input_data, context)
    print("Production Workflow Result:")
    print(result)

asyncio.run(production_workflow())
```

**Fallback Chain:**
1. Try GPT-4 (best quality)
2. Fallback to GPT-3.5 (faster, cheaper)
3. Fallback to local model (always available)

---

## 🎓 Complete Example

Here's the final, production-ready workflow:

```python
import asyncio
from typing import Dict, Any
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# [Include all primitives from steps above]

async def main():
    """Production-ready LLM workflow."""

    # Build workflow with all patterns
    workflow = (
        ValidateInputPrimitive() >>
        CachePrimitive(
            primitive=TimeoutPrimitive(
                primitive=RetryPrimitive(
                    primitive=FallbackPrimitive(
                        primary=ProcessLLMPrimitive(model_name="gpt-4"),
                        fallbacks=[
                            ProcessLLMPrimitive(model_name="gpt-3.5-turbo")
                        ]
                    ),
                    max_retries=3,
                    backoff_strategy="exponential",
                    initial_delay=1.0
                ),
                timeout_seconds=30.0
            ),
            ttl_seconds=3600,
            max_size=1000
        ) >>
        FormatOutputPrimitive()
    )

    # Execute workflow
    context = WorkflowContext(correlation_id="production-001")

    test_cases = [
        {"prompt": "What is TTA.dev?"},
        {"prompt": "How do primitives work?"},
        {"prompt": "What is TTA.dev?"},  # Cache hit!
    ]

    for i, input_data in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"Test Case {i}: {input_data['prompt']}")
        print('='*50)

        try:
            result = await workflow.execute(input_data, context)
            print(result)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Workflow Benefits

| Feature | Benefit | Impact |
|---------|---------|--------|
| **Caching** | Avoid redundant API calls | 40-60% cost reduction |
| **Retry** | Handle transient failures | 99.9% reliability |
| **Timeout** | Prevent hanging | <30s worst-case latency |
| **Fallback** | Graceful degradation | 99.99% availability |
| **Validation** | Catch errors early | Better UX |
| **Observability** | Track execution | Easy debugging |

---

## 🔍 Understanding the Flow

```
Input → Validate → Cache Check
                       ├─ Hit → Return Cached
                       └─ Miss → Timeout(
                                   Retry(
                                     Fallback(
                                       GPT-4
                                       ↓ (on failure)
                                       GPT-3.5
                                     )
                                   )
                                 )
                                 → Format → Output
```

---

## 🎯 Next Steps

### Enhance Your Workflow

1. **Add Routing**
   - Use [[TTA Primitives/RouterPrimitive]] for dynamic model selection
   - Route based on complexity, cost, speed

2. **Add Parallel Processing**
   - Use [[TTA Primitives/ParallelPrimitive]] for concurrent operations
   - Process multiple prompts at once

3. **Add Metrics**
   - See [[TTA.dev/Guides/Observability]] for metrics setup
   - Track cost, latency, cache hit rate

### Learn More Patterns

- [[TTA.dev/Guides/Workflow Composition]] - Advanced composition
- [[TTA.dev/Guides/Error Handling Patterns]] - More error patterns
- [[TTA.dev/Guides/Cost Optimization]] - Optimize costs
- [[TTA Primitives]] - Complete primitive catalog

### Explore Examples

- `packages/tta-dev-primitives/examples/rag_workflow.py`
- `packages/tta-dev-primitives/examples/agentic_rag_workflow.py`
- `packages/tta-dev-primitives/examples/cost_tracking_workflow.py`

---

## 🆘 Troubleshooting

### Issue: "Cache not working"

```python
# Make sure cache key is deterministic
cache = CachePrimitive(
    primitive=my_primitive,
    key_fn=lambda data, ctx: data["prompt"]  # ← Use stable key
)
```

### Issue: "Retry exhausted"

```python
# Increase retries or add fallback
workflow = RetryPrimitive(
    primitive=my_primitive,
    max_retries=5,  # ← Increase attempts
    backoff_strategy="exponential"
)
```

### Issue: "Timeout too aggressive"

```python
# Increase timeout for slow operations
workflow = TimeoutPrimitive(
    primitive=my_primitive,
    timeout_seconds=60.0  # ← Increase timeout
)
```

---

## ✅ Checklist

Before moving to production:

- [ ] Input validation added
- [ ] Caching configured with appropriate TTL
- [ ] Retry logic with exponential backoff
- [ ] Timeout protection configured
- [ ] Fallback chain defined
- [ ] Observability context set up
- [ ] Error handling tested
- [ ] Unit tests written
- [ ] Integration tests passing
- [ ] Documentation updated

---

**Last Updated:** October 31, 2025
**Difficulty:** Beginner
**Estimated Time:** 20 minutes
**Prerequisites:** Beginner Quickstart

**Next Guide:** [[TTA.dev/Guides/Workflow Composition]]

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___guides___first workflow]]
