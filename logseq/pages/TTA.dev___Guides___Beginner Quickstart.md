# Beginner Quickstart

type:: [[Guide]]
category:: [[Getting Started]]
difficulty:: [[Beginner]]
estimated-time:: 15 minutes
target-audience:: [[Beginners]], [[New Users]]

---

## Overview

- id:: beginner-quickstart-overview
  **Get started with TTA.dev in 15 minutes.** This guide takes you from zero to your first working AI workflow with no prior knowledge required. You'll learn the absolute essentials and build something real.

---

## What You'll Build

By the end of this guide, you'll have:
- ✅ A working AI workflow with 3 primitives
- ✅ Error handling with automatic retries
- ✅ Cost optimization with caching
- ✅ Full observability and logging

**Your first workflow:**
```
Input → Process → LLM (with retry) → Format → Output
           ↓
        Cache (save 50% cost)
```

---

## Step 1: Installation (2 minutes)

### Prerequisites
- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`

### Install TTA.dev

**Using uv (recommended):**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init my-ai-project
cd my-ai-project

# Add TTA.dev
uv add tta-dev-primitives
```

**Using pip:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install TTA.dev
pip install tta-dev-primitives
```

### Verify Installation

```bash
python -c "from tta_dev_primitives import WorkflowPrimitive; print('✅ TTA.dev installed!')"
```

---

## Step 2: Your First Primitive (3 minutes)

Create a file called `hello_workflow.py`:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
import asyncio

class HelloWorld(WorkflowPrimitive[str, str]):
    """Your first primitive - says hello!"""

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        return f"Hello, {input_data}!"

# Run it
async def main():
    primitive = HelloWorld()
    context = WorkflowContext()
    result = await primitive.execute("World", context)
    print(result)  # Output: Hello, World!

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**
```bash
python hello_workflow.py
# Output: Hello, World!
```

🎉 **You just created your first primitive!**

---

## Step 3: Chain Primitives Together (3 minutes)

Now let's create a workflow with multiple steps:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
import asyncio

class InputProcessor(WorkflowPrimitive[str, dict]):
    """Step 1: Process the input."""
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {
            "original": input_data,
            "uppercase": input_data.upper(),
            "length": len(input_data)
        }

class Formatter(WorkflowPrimitive[dict, str]):
    """Step 2: Format the output."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> str:
        return f"Processed '{input_data['original']}' ({input_data['length']} chars)"

# Chain them together with >>
async def main():
    # Create workflow: Input → Process → Format
    workflow = InputProcessor() >> Formatter()

    # Run it
    context = WorkflowContext()
    result = await workflow.execute("hello world", context)
    print(result)
    # Output: Processed 'hello world' (11 chars)

if __name__ == "__main__":
    asyncio.run(main())
```

**The magic:** The `>>` operator chains primitives together!
- Output of `InputProcessor` → Input of `Formatter`
- Type-safe (Python will catch mismatches)
- Readable and composable

---

## Step 4: Add Error Handling (3 minutes)

Let's add automatic retries for reliability:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive
import asyncio
import random

class UnreliableAPI(WorkflowPrimitive[str, str]):
    """Simulates an API that fails sometimes."""
    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        if random.random() < 0.5:  # 50% chance of failure
            raise Exception("API temporarily unavailable")
        return f"API processed: {input_data}"

async def main():
    # Wrap with RetryPrimitive
    unreliable = UnreliableAPI()
    reliable = RetryPrimitive(
        primitive=unreliable,
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Now it retries automatically!
    context = WorkflowContext()
    try:
        result = await reliable.execute("test data", context)
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Failed after 3 retries: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

**What happens:**
1. First attempt fails? → Wait 1 second, retry
2. Second attempt fails? → Wait 2 seconds, retry
3. Third attempt fails? → Wait 4 seconds, retry
4. Still failing? → Raise exception

---

## Step 5: Add Caching (2 minutes)

Save money by caching expensive operations:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
import asyncio
import time

class ExpensiveLLM(WorkflowPrimitive[str, str]):
    """Simulates an expensive LLM call."""
    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        print(f"💰 Expensive LLM call (costs $0.01)")
        await asyncio.sleep(1)  # Simulate slow API
        return f"LLM response for: {input_data}"

async def main():
    # Wrap with CachePrimitive
    expensive_llm = ExpensiveLLM()
    cached_llm = CachePrimitive(
        primitive=expensive_llm,
        ttl_seconds=60,  # Cache for 1 minute
        max_size=100
    )

    context = WorkflowContext()

    # First call - cache miss
    print("First call:")
    start = time.time()
    result1 = await cached_llm.execute("What is Python?", context)
    print(f"⏱️  Took {time.time() - start:.1f}s")
    print(f"📄 {result1}\n")

    # Second call - cache hit!
    print("Second call (same input):")
    start = time.time()
    result2 = await cached_llm.execute("What is Python?", context)
    print(f"⏱️  Took {time.time() - start:.1f}s (instant!)")
    print(f"📄 {result2}")
    print("✅ Saved $0.01 (50% cost reduction)")

if __name__ == "__main__":
    asyncio.run(main())
```

**Output:**
```
First call:
💰 Expensive LLM call (costs $0.01)
⏱️  Took 1.0s
📄 LLM response for: What is Python?

Second call (same input):
⏱️  Took 0.0s (instant!)
📄 LLM response for: What is Python?
✅ Saved $0.01 (50% cost reduction)
```

---

## Step 6: Complete Real-World Example (2 minutes)

Let's combine everything into a production-ready workflow:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive
import asyncio

# Step 1: Input Processor
class InputProcessor(WorkflowPrimitive[str, dict]):
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {"query": input_data, "timestamp": context.start_time}

# Step 2: LLM (with retry and cache)
class GPT4(WorkflowPrimitive[dict, dict]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Simulate LLM call
        return {"response": f"AI answer to: {input_data['query']}"}

# Step 3: Fallback (cheap alternative)
class GPT3(WorkflowPrimitive[dict, dict]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        return {"response": f"Quick answer to: {input_data['query']}", "fallback": True}

# Step 4: Formatter
class OutputFormatter(WorkflowPrimitive[dict, str]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> str:
        fallback_note = " (fallback)" if input_data.get("fallback") else ""
        return f"✨ {input_data['response']}{fallback_note}"

# Build production workflow
async def main():
    # Layer 1: Cache expensive LLM
    gpt4 = GPT4()
    cached_gpt4 = CachePrimitive(gpt4, ttl_seconds=3600)

    # Layer 2: Retry on failure
    retry_gpt4 = RetryPrimitive(cached_gpt4, max_retries=3)

    # Layer 3: Fallback to cheaper model
    gpt3 = GPT3()
    resilient_llm = FallbackPrimitive(
        primary=retry_gpt4,
        fallbacks=[gpt3]
    )

    # Complete workflow
    workflow = (
        InputProcessor() >>
        resilient_llm >>
        OutputFormatter()
    )

    # Run it!
    context = WorkflowContext(workflow_id="my-first-workflow")
    result = await workflow.execute("What is AI?", context)
    print(result)
    print(f"\n⏱️  Total time: {context.elapsed_ms():.0f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

**This workflow has:**
- ✅ Caching (50%+ cost reduction)
- ✅ Retries (handles transient failures)
- ✅ Fallback (graceful degradation)
- ✅ Observability (timing, context tracking)
- ✅ Type safety (catches errors at dev time)

---

## Quick Reference Card

### Core Patterns

**Sequential (A → B → C):**
```python
workflow = step1 >> step2 >> step3
```

**Parallel (A, B, C at same time):**
```python
workflow = step1 | step2 | step3
```

**Retry (automatic retries):**
```python
from tta_dev_primitives.recovery import RetryPrimitive
workflow = RetryPrimitive(step, max_retries=3)
```

**Fallback (graceful degradation):**
```python
from tta_dev_primitives.recovery import FallbackPrimitive
workflow = FallbackPrimitive(primary=expensive, fallbacks=[cheap])
```

**Cache (save money):**
```python
from tta_dev_primitives.performance import CachePrimitive
workflow = CachePrimitive(expensive, ttl_seconds=3600)
```

### Essential Imports

```python
# Core
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

# Recovery
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# Performance
from tta_dev_primitives.performance import CachePrimitive

# Testing
from tta_dev_primitives.testing import MockPrimitive
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Forgetting async/await

```python
# WRONG
result = primitive.execute(data, context)  # Missing await!

# RIGHT
result = await primitive.execute(data, context)
```

### ❌ Mistake 2: Not using WorkflowContext

```python
# WRONG
result = await primitive.execute(data, None)  # No context!

# RIGHT
context = WorkflowContext()
result = await primitive.execute(data, context)
```

### ❌ Mistake 3: Ignoring types

```python
# WRONG - Types don't match
class Step1(WorkflowPrimitive[str, dict]):
    ...

class Step2(WorkflowPrimitive[str, str]):  # Expects str, not dict!
    ...

workflow = Step1() >> Step2()  # Type error!

# RIGHT - Types match
class Step2(WorkflowPrimitive[dict, str]):  # Accepts dict
    ...
```

---

## What's Next?

### Learn More

**Core Concepts:**
- [[TTA.dev/Guides/Agentic Primitives]] - Deep dive into primitives
- [[TTA.dev/Guides/Workflow Composition]] - Advanced patterns

**Practical Guides:**
- [[TTA.dev/Guides/Error Handling Patterns]] - Robust error handling
- [[TTA.dev/Guides/Cost Optimization]] - Save 30-80% on costs
- [[TTA.dev/Guides/Observability]] - Monitor your workflows

**All Primitives:**
- [[TTA.dev/Primitives/SequentialPrimitive]] - Chain operations
- [[TTA.dev/Primitives/ParallelPrimitive]] - Concurrent execution
- [[TTA.dev/Primitives/RetryPrimitive]] - Automatic retries
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/CachePrimitive]] - Cost optimization
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing
- [[TTA.dev/Primitives/ConditionalPrimitive]] - If/else logic
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breakers
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

### Join the Community

- 🌐 **GitHub:** https://github.com/theinterneti/TTA.dev
- 📚 **Docs:** Full documentation in this Logseq graph
- 💬 **Issues:** Report bugs or request features

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'tta_dev_primitives'"

**Solution:** Install the package
```bash
uv add tta-dev-primitives
# or
pip install tta-dev-primitives
```

### Issue: "SyntaxError: invalid syntax" on async/await

**Solution:** You need Python 3.11+
```bash
python --version  # Should be 3.11 or higher
```

### Issue: Types don't match when chaining

**Solution:** Check that output type of A matches input type of B
```python
# A outputs dict, B expects dict
class A(WorkflowPrimitive[str, dict]): ...
class B(WorkflowPrimitive[dict, str]): ...
workflow = A() >> B()  # ✅ Works!
```

---

## Summary

**In 15 minutes you learned:**
1. ✅ How to install TTA.dev
2. ✅ How to create primitives
3. ✅ How to chain them with `>>`
4. ✅ How to add error handling (retry)
5. ✅ How to optimize costs (cache)
6. ✅ How to build production workflows

**Key concept:** Compose small, focused primitives into powerful workflows using `>>` and `|` operators.

**Next step:** Read [[TTA.dev/Guides/Agentic Primitives]] for deeper understanding!

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 15 minutes
**Difficulty:** [[Beginner]]
