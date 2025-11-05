# Whiteboard - Primitive Composition Patterns

type:: Whiteboard
category:: [[Architecture]]
status:: Template
created:: [[2025-10-31]]

---

## Purpose

Visual guide to composing TTA.dev workflow primitives using operators.

---

## Composition Patterns

### 1. Sequential Composition (`>>`)

**Visual Flow:**

```
INPUT → [Step 1] → result1 → [Step 2] → result2 → [Step 3] → OUTPUT
```

**Code:**
```python
workflow = step1 >> step2 >> step3
```

**Use When:**
- Each step depends on the previous result
- Data transforms through stages
- Linear pipeline processing

---

### 2. Parallel Composition (`|`)

**Visual Flow:**

```
                ┌─→ [Branch 1] ─┐
                │                │
INPUT ──────────┼─→ [Branch 2] ─┼────→ [result1, result2, result3]
                │                │
                └─→ [Branch 3] ─┘
```

**Code:**
```python
workflow = branch1 | branch2 | branch3
```

**Use When:**
- Independent operations on same input
- Concurrent execution for speed
- Collecting multiple perspectives

---

### 3. Mixed Composition

**Visual Flow:**

```
INPUT → [Validate] → valid_data ──┬─→ [Fast Path]   ─┐
                                   │                  │
                                   ├─→ [Slow Path]   ─┼─→ [Aggregate] → OUTPUT
                                   │                  │
                                   └─→ [Cached Path] ─┘
```

**Code:**
```python
workflow = (
    validate >>
    (fast_path | slow_path | cached_path) >>
    aggregate
)
```

**Use When:**
- Combining sequential and parallel patterns
- Complex multi-stage workflows
- Need for validation + parallel processing

---

## Recovery Composition

### Retry Pattern

**Visual Flow:**

```
INPUT → [Attempt 1] ──fail──→ [Wait] → [Attempt 2] ──fail──→ [Wait] → [Attempt 3]
                ↓                          ↓                              ↓
              success                    success                        success/fail
                ↓                          ↓                              ↓
              OUTPUT                     OUTPUT                      OUTPUT/ERROR
```

**Code:**
```python
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)
```

---

### Fallback Pattern

**Visual Flow:**

```
INPUT → [Primary] ──success──→ OUTPUT
           ↓
          fail
           ↓
        [Fallback 1] ──success──→ OUTPUT
           ↓
          fail
           ↓
        [Fallback 2] ──success──→ OUTPUT
```

**Code:**
```python
workflow = FallbackPrimitive(
    primary=gpt4,
    fallbacks=[gpt35, llama]
)
```

---

## Production Pattern

**Complete Workflow with All Safeguards:**

**Visual Flow:**

```
INPUT
  ↓
[Validate] ──invalid──→ ERROR
  ↓ valid
[Cache Check] ──hit──→ OUTPUT
  ↓ miss
[Timeout(30s)]
  ↓
[Retry(3x)]
  ↓
[Fallback: GPT-4 → GPT-3.5]
  ↓
[Format]
  ↓
OUTPUT
```

**Code:**
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

## Design Elements

**When creating actual whiteboard in Logseq:**

1. **Use Shapes:**
   - Rectangles for primitives
   - Diamonds for decision points
   - Arrows for data flow
   - Circles for inputs/outputs

2. **Color Coding:**
   - Blue: Core primitives
   - Green: Recovery patterns
   - Yellow: Performance optimizations
   - Red: Error paths

3. **Labels:**
   - Add clear labels on arrows (success, fail, timeout)
   - Show data transformations
   - Indicate timing (delays, timeouts)

4. **Connections:**
   - Link to actual primitive pages
   - Reference code examples
   - Show related patterns

---

## Related

- [[TTA.dev/Architecture]]
- [[TTA Primitives]]
- [[TTA.dev/Guides/Workflow Composition]]
- [[TTA.dev/Guides/First Workflow]]

---

**To Create Actual Whiteboard:**
1. Open Logseq
2. Right-click this page → "Open in whiteboard"
3. Use drawing tools to create visual diagrams
4. Embed code blocks and page references
5. Export as PNG for documentation

---

**Last Updated:** [[2025-10-31]]
**Status:** Template Ready
**Next:** Create interactive whiteboard in Logseq UI
