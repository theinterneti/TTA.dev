# Learning TTA Primitives

**Flashcard collection for mastering TTA.dev workflow primitives**

This page demonstrates Logseq's flashcard and cloze features applied to learning TTA.dev primitives.

---

## 🎯 Core Concepts

### What is a WorkflowPrimitive? #card

A WorkflowPrimitive is the **base class** for all TTA.dev workflow components.

Key characteristics:
- Type-safe: `WorkflowPrimitive[TInput, TOutput]`
- Composable: Use `>>` (sequential) and `|` (parallel) operators
- Observable: Automatic span creation and metrics
- Async: All operations are `async def`

Reference: [[TTA Primitives]]

---

### Base Class Pattern #card

The correct pattern for extending primitives is:

```python
from tta_dev_primitives.observability import InstrumentedPrimitive

class MyPrimitive({{cloze InstrumentedPrimitive}}[dict, dict]):
    def __init__(self):
        {{cloze super().__init__(name="my_primitive")}}

    async def {{cloze _execute_impl}}(self, input_data, context):
        # Implementation
        return result
```

Key points:
- Extend {{cloze InstrumentedPrimitive}}, not WorkflowPrimitive directly
- Call {{cloze super().__init__(name="...")}} in constructor
- Implement {{cloze _execute_impl}} method
- Parameter order: {{cloze (input_data, context)}}

---

## 🔗 Composition Operators

### Sequential Composition #card

**Operator:** `>>`

**Purpose:** {{cloze Execute primitives in sequence, passing output to next input}}

**Example:**
```python
workflow = step1 >> step2 >> step3
```

**Execution flow:**
```
input → step1 → result1 → step2 → result2 → step3 → output
```

---

### Parallel Composition #card

**Operator:** `|`

**Purpose:** {{cloze Execute primitives concurrently, collecting results in a list}}

**Example:**
```python
workflow = branch1 | branch2 | branch3
```

**Execution flow:**
```
             ┌─→ branch1 ─┐
input ───────┼─→ branch2 ─┼───→ [result1, result2, result3]
             └─→ branch3 ─┘
```

---

### Mixed Composition #card

You can combine operators for complex workflows:

```python
workflow = (
    {{cloze input_processor}} >>
    ({{cloze fast_path | slow_path | cached_path}}) >>
    {{cloze aggregator}}
)
```

This pattern:
1. Processes input sequentially
2. Executes three branches in parallel
3. Aggregates results sequentially

---

## 🔄 Recovery Primitives

### RetryPrimitive Parameters #card

```python
from tta_dev_primitives.recovery import RetryPrimitive

retry = RetryPrimitive(
    primitive={{cloze wrapped_primitive}},
    max_retries={{cloze 3}},
    backoff_strategy={{cloze "exponential"}},
    initial_delay={{cloze 1.0}},
    jitter={{cloze True}}
)
```

**Backoff strategies:**
- {{cloze "exponential"}} - 1s, 2s, 4s, 8s...
- {{cloze "linear"}} - 1s, 2s, 3s, 4s...
- {{cloze "constant"}} - 1s, 1s, 1s, 1s...

---

### FallbackPrimitive Usage #card

**Purpose:** {{cloze Graceful degradation by trying multiple alternatives}}

```python
from tta_dev_primitives.recovery import FallbackPrimitive

workflow = FallbackPrimitive(
    primary={{cloze expensive_api}},
    fallbacks={{cloze [cheap_api, cached_response, default_value]}}
)
```

**Execution:** Tries {{cloze primary}} first, then each {{cloze fallback}} in order until one succeeds.

---

### TimeoutPrimitive Configuration #card

**Purpose:** {{cloze Prevent operations from hanging indefinitely (circuit breaker pattern)}}

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

protected = TimeoutPrimitive(
    primitive={{cloze slow_operation}},
    timeout_seconds={{cloze 30.0}},
    raise_on_timeout={{cloze True}}
)
```

**What happens on timeout?**
- If `raise_on_timeout=True`: {{cloze Raises TimeoutError}}
- If `raise_on_timeout=False`: {{cloze Returns None or default value}}

---

## ⚡ Performance Primitives

### CachePrimitive Parameters #card

```python
from tta_dev_primitives.performance import CachePrimitive

cache = CachePrimitive(
    primitive={{cloze expensive_operation}},
    ttl_seconds={{cloze 3600}},  # 1 hour
    max_size={{cloze 1000}},
    key_fn={{cloze lambda data, ctx: hash(data)}}}
)
```

**Benefits:**
- Cost reduction: {{cloze 30-40%}} typical
- Latency reduction: {{cloze 100x}} on cache hit
- Eviction policy: {{cloze LRU}} (Least Recently Used)

---

### When to Use CachePrimitive #card

**✅ Use when:**
- Operations are {{cloze expensive}} (LLM calls, API requests)
- {{cloze Repeated inputs}} are common
- Results are {{cloze deterministic}} (same input → same output)

**❌ Don't use when:**
- Results {{cloze change frequently}}
- Each input is {{cloze unique}}
- {{cloze Memory constraints}} are tight

---

## 🎯 Routing Primitives

### RouterPrimitive Structure #card

```python
from tta_dev_primitives.core import RouterPrimitive

router = RouterPrimitive(
    routes={{cloze {"fast": llm1, "quality": llm2}}},
    router_fn={{cloze select_route_function}},
    default={{cloze "fast"}}
)
```

**Router function signature:**
```python
def select_route(
    {{cloze input_data}}: dict,
    {{cloze context}}: [[TTA.dev/Data/WorkflowContext]]
) -> {{cloze str}}:
    # Return route key
    return "fast" if simple else "quality"
```

---

### Tier-Based Routing #card

**Three standard tiers:**

1. **{{cloze fast}}** tier:
   - Use: {{cloze Cheaper, faster models (GPT-4-mini)}}
   - When: {{cloze Simple queries, high volume}}

2. **{{cloze balanced}}** tier:
   - Use: {{cloze Mid-tier models}}
   - When: {{cloze General purpose tasks}}

3. **{{cloze quality}}** tier:
   - Use: {{cloze Best models (GPT-4, Claude Opus)}}
   - When: {{cloze Complex tasks, critical accuracy}}

**Cost impact:** Tier selection can save {{cloze 30-40%}} on LLM costs.

---

## 📊 Observability

### [[TTA.dev/Data/WorkflowContext]] Purpose #card

**[[TTA.dev/Data/WorkflowContext]]** carries {{cloze state and metadata}} through the workflow.

Key attributes:
- `{{cloze correlation_id}}` - Unique request identifier
- `{{cloze trace_id}}` - Distributed tracing ID
- `{{cloze metadata}}` - User-supplied metadata dictionary
- `{{cloze span_context}}` - OpenTelemetry span context

**Creation:**
```python
context = WorkflowContext( # This is a code example, will address later if needed
    correlation_id={{cloze "req-123"}},
    metadata={{cloze {"user_id": "user-789"}}}
)
```

---

### Automatic Observability Features #card

All primitives automatically provide:

1. **{{cloze OpenTelemetry spans}}** - Distributed tracing
2. **{{cloze Prometheus metrics}}** - Execution time, success rate
3. **{{cloze Structured logging}}** - JSON-formatted logs with context
4. **{{cloze Context propagation}}** - Correlation IDs across primitives

No manual instrumentation needed! Just extend {{cloze InstrumentedPrimitive}}.

---

## 🧪 Testing

### MockPrimitive Usage #card

```python
from tta_dev_primitives.testing import MockPrimitive

# Create mock
mock_llm = MockPrimitive(
    return_value={{cloze {"output": "test response"}}}}
)

# Use in workflow
workflow = step1 >> {{cloze mock_llm}} >> step3

# Assert
result = await workflow.execute(data, context)
assert {{cloze mock_llm.call_count}} == 1
```

**Why use MockPrimitive?**
- Avoid {{cloze expensive API calls}} in tests
- Control {{cloze test data}} precisely
- Test {{cloze error handling}} with mock failures

---

## 📝 Common Patterns

### Production LLM Pattern #card

Layer your primitives for production reliability:

```python
production_llm = (
    {{cloze CachePrimitive}}(ttl=3600) >>           # Layer 1: Cache
    {{cloze TimeoutPrimitive}}(timeout=30) >>       # Layer 2: Timeout
    {{cloze RetryPrimitive}}(max_retries=3) >>      # Layer 3: Retry
    {{cloze FallbackPrimitive}}(                    # Layer 4: Fallback
        primary=gpt4,
        fallbacks=[gpt4_mini, claude]
    )
)
```

**Benefits:**
- {{cloze 40-60%}} cost reduction (cache)
- {{cloze 99.9%}} availability (fallback)
- {{cloze <30s}} worst-case latency (timeout)

---

### RAG Workflow Pattern #card

```python
rag_workflow = (
    query_processor >>
    {{cloze CachePrimitive}}(vector_retrieval) >>
    {{cloze FallbackPrimitive}}(
        primary=vector_db,
        fallbacks=[web_search, default_docs]
    ) >>
    document_grader >>
    answer_generator >>
    hallucination_checker
)
```

Key components:
- {{cloze Cache}} vector lookups
- {{cloze Fallback}} to web search
- {{cloze Grade}} document relevance
- {{cloze Validate}} for hallucinations

---

## 🎓 Study Tips

### Review Schedule

- **Day 1:** Create flashcards while learning
- **Day 2:** Review all cards (first repetition)
- **Day 4:** Review cards rated "Again" or "Hard"
- **Day 7:** Review all cards (second repetition)
- **Day 14:** Review all cards (third repetition)
- **Day 30:** Review all cards (fourth repetition)

### Effective Flashcard Creation

1. **One concept per card** - Don't overload
2. **Use examples** - Code snippets help memory
3. **Add context** - Link to related pages
4. **Update regularly** - Refine as understanding grows

### Using Cloze vs Q&A

- **Cloze:** {{cloze Facts, syntax, definitions, parameters}}
- **Q&A:** {{cloze Concepts, patterns, decisions, comparisons}}

---

## 🔗 Related Pages

- [[TTA Primitives]] - Full primitives catalog
- [[TTA.dev (Meta-Project)]] - Project dashboard
- [[AI Research]] - Research notes and patterns
- [[Architecture Decisions]] - ADR log

---

## 📊 Progress Tracking

### Cards Created
{{query (and (property card) [[Learning TTA Primitives]])}}

### Cards Due Today
{{query (and (property card) (due today))}}

### Mastery Level

- [ ] Beginner - Understanding basic concepts
- [ ] Intermediate - Can compose simple workflows
- [ ] Advanced - Building complex production patterns
- [ ] Expert - Contributing new primitives

---

**Last Updated:** October 31, 2025
**Card Count:** 22 flashcards + cloze deletions
**Estimated Study Time:** 30-45 minutes for initial review
