# Whiteboard - Workflow Composition Patterns

**Visual guide to composing workflows with TTA.dev primitives**

---

## Purpose

Interactive whiteboard demonstrating:
- Sequential composition (`>>`)
- Parallel composition (`|`)
- Mixed composition patterns
- Real-world examples

---

## Pattern 1: Sequential Composition

### Visual Representation

```
Input → [Step 1] → [Step 2] → [Step 3] → Output
```

### Operator: `>>`

### Code Example

```python
workflow = step1 >> step2 >> step3
```

### Use Cases
- Processing pipeline
- Multi-stage transformations
- Ordered operations

### Related: [[TTA Primitives/SequentialPrimitive]]

---

## Pattern 2: Parallel Composition

### Visual Representation

```
        ┌─→ [Branch 1] ─┐
Input ──┼─→ [Branch 2] ─┼─→ Aggregate → Output
        └─→ [Branch 3] ─┘
```

### Operator: `|`

### Code Example

```python
workflow = branch1 | branch2 | branch3
```

### Use Cases
- Concurrent API calls
- Multi-model LLM queries
- Parallel data processing

### Related: [[TTA Primitives/ParallelPrimitive]]

---

## Pattern 3: Mixed Composition

### Visual Representation

```
Input → [Processor] → ┌─→ [Fast LLM] ─┐
                      ├─→ [Slow LLM] ─┤ → [Aggregator] → Output
                      └─→ [Cache]    ─┘
```

### Code Example

```python
workflow = (
    input_processor >>
    (fast_llm | slow_llm | cached_llm) >>
    aggregator
)
```

### Use Cases
- Multi-model orchestration
- Redundancy and fallback
- Cost optimization

---

## Pattern 4: Router-Based Composition

### Visual Representation

```
           ┌─→ Simple? → [Fast LLM]
Input → [Router] ─┼─→ Medium? → [Balanced LLM]
           └─→ Complex? → [Quality LLM]
```

### Code Example

```python
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "balanced": claude_sonnet,
        "quality": gpt4
    }
)
workflow = input_processor >> router >> output_formatter
```

### Related: [[TTA Primitives/RouterPrimitive]]

---

## Pattern 5: Recovery Stack

### Visual Representation

```
Input → [Timeout] → [Retry] → [Fallback] → [Cache] → Output
         └─────────── Recovery Layers ──────────┘
```

### Code Example

```python
from tta_dev_primitives.recovery import (
    TimeoutPrimitive,
    RetryPrimitive,
    FallbackPrimitive
)
from tta_dev_primitives.performance import CachePrimitive

workflow = (
    TimeoutPrimitive(api_call, timeout=30) >>
    RetryPrimitive(api_call, max_retries=3) >>
    FallbackPrimitive(
        primary=expensive_api,
        fallback=cheap_api
    ) >>
    CachePrimitive(ttl=3600)
)
```

---

## Whiteboard Elements

### For Each Pattern

1. **Input node** (circle)
2. **Process nodes** (rectangles)
3. **Output node** (circle)
4. **Arrows** showing data flow
5. **Annotations** with operator symbols
6. **Code snippets** (sticky notes)

### Color Coding

- **Blue:** Sequential steps
- **Green:** Parallel branches
- **Yellow:** Decision points
- **Red:** Error handling
- **Purple:** Caching/optimization

---

## Real-World Example: RAG Workflow

### Visual Layout

```
Query Input
    ↓
[Router: Simple/Complex]
    ↓
┌─────────────┴─────────────┐
│                           │
[Cache Check]        [Full Processing]
    ↓                       ↓
 Hit? ────┐      [Vector Retrieval]
    ↓     │                ↓
    ↓     │         [Document Grading]
    ↓     │                ↓
    ↓     └──────→ [LLM Generation]
    ↓                      ↓
    └──────────────────────┤
                           ↓
                   [Validation]
                           ↓
                       Response
```

### Code

```python
rag_workflow = (
    RouterPrimitive(routes={"simple": fast, "complex": full}) >>
    CachePrimitive(ttl=3600) >>
    (vector_retrieval >> document_grader >> llm_generator) >>
    validator
)
```

### Related: [[examples/rag_workflow.py]]

---

## Instructions for Whiteboard

1. Create whiteboard in Logseq
2. Add pattern sections vertically
3. Use consistent shape/color scheme
4. Link to primitive documentation
5. Add real code examples as sticky notes
6. Export as PNG for documentation

---

## Related Pages

- [[TTA Primitives]]
- [[TTA.dev/Architecture]]
- [[PRIMITIVES CATALOG]]
- [[Whiteboard - TTA.dev Architecture Overview]]

---

**Created:** [[2025-10-31]]
**Status:** In Progress
**Examples:** See packages/tta-dev-primitives/examples/
