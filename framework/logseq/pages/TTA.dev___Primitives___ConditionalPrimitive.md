# ConditionalPrimitive

type:: [[Primitive]]
category:: [[Core]]
status:: [[Stable]]
version:: 0.1.0
package:: [[tta-dev-primitives]]
test-coverage:: 100%
complexity:: [[Medium]]
import-path:: from tta_dev_primitives import ConditionalPrimitive

---

## Overview

- id:: conditional-primitive-overview
  **ConditionalPrimitive** enables if/else branching in workflows. Execute different primitives based on a condition function, allowing dynamic workflow control and decision-making. This is the key primitive for building adaptive AI workflows that respond to content, safety checks, or business rules.

---

## Use Cases

- **Content Safety Filtering** - Route safe vs unsafe content to different processors
- **Feature Flags** - Enable/disable workflow branches based on configuration
- **A/B Testing** - Route traffic to different implementations
- **Quality Checks** - Use fast path for simple requests, complex path for harder ones
- **Cost Optimization** - Choose expensive vs cheap LLM based on complexity
- **Error Routing** - Route errors to fallback vs retry logic

---

## Key Benefits

- **Dynamic Control Flow** - Adapt workflow behavior at runtime
- **Type Safety** - Condition function receives input data and context
- **Optional Else Branch** - Pass through input if no else specified
- **Full Observability** - Logs condition evaluation and branch selection
- **Composability** - Combine with other primitives using >> and |

---

## API Reference

### Constructor

```python
def __init__(
    self,
    condition: Callable[[Any, WorkflowContext], bool],
    then_primitive: WorkflowPrimitive,
    else_primitive: WorkflowPrimitive | None = None
)
```

**Parameters:**
- `condition` (Callable) - Function `(input, context) -> bool` to determine branch
- `then_primitive` (WorkflowPrimitive) - Execute if condition returns True
- `else_primitive` (WorkflowPrimitive | None) - Execute if condition returns False (optional)

**Returns:** ConditionalPrimitive instance

### Execute Method

```python
async def execute(self, input_data: Any, context: WorkflowContext) -> Any
```

**Parameters:**
- `input_data` (Any) - Input data passed to condition and selected branch
- `context` (WorkflowContext) - Workflow context with state and tracing

**Returns:** Output from selected branch, or input_data if no else branch and condition is False

**Raises:** Exception if selected primitive fails

---

## Examples

### Example 1: Content Safety Check

- id:: conditional-safety-example

```python
from tta_dev_primitives import ConditionalPrimitive, LambdaPrimitive, WorkflowContext

# Safety check function
def is_safe(input_data: dict, context: WorkflowContext) -> bool:
    return input_data.get("safety_level") != "blocked"

# Different processors for safe vs unsafe content
safe_processor = LambdaPrimitive(lambda data, ctx: {"result": f"Processing: {data['text']}"})
unsafe_processor = LambdaPrimitive(lambda data, ctx: {"result": "Content blocked", "reason": "unsafe"})

# Conditional workflow
workflow = ConditionalPrimitive(
    condition=is_safe,
    then_primitive=safe_processor,
    else_primitive=unsafe_processor
)

# Test with safe content
context = WorkflowContext()
safe_result = await workflow.execute(
    {"text": "Hello world", "safety_level": "safe"},
    context
)
# Output: {"result": "Processing: Hello world"}

# Test with unsafe content
unsafe_result = await workflow.execute(
    {"text": "Harmful content", "safety_level": "blocked"},
    context
)
# Output: {"result": "Content blocked", "reason": "unsafe"}
```

### Example 2: LLM Selection Based on Complexity

- id:: conditional-llm-selection

```python
# Complexity analyzer
def is_complex(input_data: str, context: WorkflowContext) -> bool:
    # Simple heuristic: long or has technical terms
    return len(input_data) > 500 or any(word in input_data.lower() for word in ["algorithm", "quantum", "neuroscience"])

# Different LLMs
simple_llm = LambdaPrimitive(lambda text, ctx: call_gpt4_mini(text))  # Fast & cheap
complex_llm = LambdaPrimitive(lambda text, ctx: call_gpt4(text))      # Powerful & expensive

# Route based on complexity
workflow = ConditionalPrimitive(
    condition=is_complex,
    then_primitive=complex_llm,  # Use powerful model for complex queries
    else_primitive=simple_llm    # Use cheap model for simple queries
)

# Simple query → GPT-4 Mini ($0.0001/request)
result1 = await workflow.execute("What's the weather?", context)

# Complex query → GPT-4 ($0.03/request)
result2 = await workflow.execute(
    "Explain the implications of quantum entanglement for distributed computing architectures over 500 words",
    context
)
```

### Example 3: Feature Flag Control

- id:: conditional-feature-flag

```python
# Check feature flag from context
def feature_enabled(input_data: Any, context: WorkflowContext) -> bool:
    return context.metadata.get("feature_new_algorithm", False)

# New vs old implementation
new_algorithm = LambdaPrimitive(lambda data, ctx: process_with_new_algorithm(data))
old_algorithm = LambdaPrimitive(lambda data, ctx: process_with_old_algorithm(data))

workflow = ConditionalPrimitive(
    condition=feature_enabled,
    then_primitive=new_algorithm,
    else_primitive=old_algorithm
)

# Enable feature for specific users
context_new = WorkflowContext(metadata={"feature_new_algorithm": True})
result_new = await workflow.execute(data, context_new)

# Default users get old algorithm
context_default = WorkflowContext()
result_old = await workflow.execute(data, context_default)
```

### Example 4: Optional Else (Pass-Through)

- id:: conditional-optional-else

```python
# Validator that only processes if data needs validation
def needs_validation(input_data: dict, context: WorkflowContext) -> bool:
    return input_data.get("source") == "untrusted"

# Validator (only for untrusted sources)
validator = LambdaPrimitive(lambda data, ctx: validate_and_sanitize(data))

# No else branch - passes through if condition is False
workflow = ConditionalPrimitive(
    condition=needs_validation,
    then_primitive=validator
    # else_primitive=None (default)
)

# Untrusted source → validate
untrusted_data = {"source": "untrusted", "content": "user input"}
validated = await workflow.execute(untrusted_data, context)

# Trusted source → pass through unchanged
trusted_data = {"source": "internal", "content": "system data"}
passed_through = await workflow.execute(trusted_data, context)
# Output: same as input (no validation needed)
```

### Example 5: Composition with Sequential

- id:: conditional-composition-sequential

```python
from tta_dev_primitives import SequentialPrimitive

# Complete workflow with pre-processing, conditional routing, post-processing
input_processor = LambdaPrimitive(lambda data, ctx: {"processed": data.strip().lower()})
quality_check = LambdaPrimitive(lambda data, ctx: {"quality": len(data["processed"]) > 10})

def high_quality(data: dict, context: WorkflowContext) -> bool:
    return data.get("quality", False)

premium_handler = LambdaPrimitive(lambda data, ctx: {"tier": "premium", **data})
standard_handler = LambdaPrimitive(lambda data, ctx: {"tier": "standard", **data})

output_formatter = LambdaPrimitive(lambda data, ctx: f"[{data['tier'].upper()}] {data['processed']}")

# Full workflow: preprocess → check quality → conditional routing → format
workflow = (
    input_processor >>
    quality_check >>
    ConditionalPrimitive(
        condition=high_quality,
        then_primitive=premium_handler,
        else_primitive=standard_handler
    ) >>
    output_formatter
)

result = await workflow.execute("  High quality user input here  ", context)
# Output: "[PREMIUM] high quality user input here"
```

---

## Composition Patterns

### Sequential After Conditional

- id:: conditional-pattern-sequential

```python
# Conditional routing → common post-processing
workflow = (
    ConditionalPrimitive(condition, branch_a, branch_b) >>
    common_post_processor >>
    output_formatter
)
```

### Parallel Conditionals

- id:: conditional-pattern-parallel

```python
# Multiple independent conditional checks
workflow = (
    ConditionalPrimitive(safety_check, safe_path, blocked_path) |
    ConditionalPrimitive(quality_check, premium_path, standard_path) |
    ConditionalPrimitive(language_check, english_path, translate_path)
)
```

### Nested Conditionals

- id:: conditional-pattern-nested

```python
# Decision tree
primary_condition = ConditionalPrimitive(
    condition=is_authenticated,
    then_primitive=ConditionalPrimitive(
        condition=has_premium,
        then_primitive=premium_flow,
        else_primitive=free_flow
    ),
    else_primitive=anonymous_flow
)
```

---

## Best Practices

### Condition Functions

✅ **Keep conditions pure** - No side effects, just return bool
✅ **Use context metadata** - Store feature flags and config
✅ **Handle edge cases** - What if input is None or missing fields?
✅ **Document decisions** - Comment why branches exist
✅ **Test both branches** - Unit tests for True and False paths

### Branch Selection

✅ **Make branches obvious** - Clear naming (safe_path vs unsafe_path)
✅ **Similar output types** - Both branches should return compatible data
✅ **Log branch taken** - Add context.checkpoint() for debugging
✅ **Monitor branch usage** - Track which branch gets used most

### Don'ts

❌ Don't put complex logic in condition function (extract to separate function)
❌ Don't modify input_data in condition (read-only access)
❌ Don't ignore context parameter (use it for configuration)
❌ Don't create deep nesting (refactor to router or multiple conditionals)
❌ Don't forget else branch if pass-through isn't desired

---

## Observability

### Metrics Tracked

The primitive automatically tracks:
- **Branch Selection** - Which branch (then/else) was chosen
- **Condition Evaluation Time** - How long condition took
- **Branch Execution Time** - Duration of selected primitive
- **Success/Failure Rates** - Per-branch error rates

### Logging

```python
# Automatic logs
logger.info("conditional_workflow_start", has_else_branch=True)
logger.info("conditional_condition_evaluated", condition_result=True)
logger.info("conditional_then_branch_start")
logger.info("conditional_branch_complete", branch="then", duration_ms=45.2)
```

### Checkpoints

```python
# Automatic checkpoints
context.checkpoint("conditional.start")
context.checkpoint("conditional.condition_eval.start")
context.checkpoint("conditional.condition_eval.complete")
context.checkpoint("conditional.then_branch.start")
context.checkpoint("conditional.then_branch.complete")
```

---

## Testing

### Testing Both Branches

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_conditional_both_branches():
    then_mock = MockPrimitive(return_value="then result")
    else_mock = MockPrimitive(return_value="else result")

    # Test condition True
    conditional_true = ConditionalPrimitive(
        condition=lambda data, ctx: True,
        then_primitive=then_mock,
        else_primitive=else_mock
    )

    context = WorkflowContext()
    result = await conditional_true.execute("input", context)

    assert result == "then result"
    assert then_mock.call_count == 1
    assert else_mock.call_count == 0

    # Reset mocks
    then_mock.reset()
    else_mock.reset()

    # Test condition False
    conditional_false = ConditionalPrimitive(
        condition=lambda data, ctx: False,
        then_primitive=then_mock,
        else_primitive=else_mock
    )

    result = await conditional_false.execute("input", context)

    assert result == "else result"
    assert then_mock.call_count == 0
    assert else_mock.call_count == 1
```

---

## Real-World Example: Content Moderation Pipeline

```python
# Content moderation with conditional routing
def is_safe_content(input_data: dict, context: WorkflowContext) -> bool:
    safety_score = input_data.get("safety_score", 1.0)
    return safety_score >= 0.8

def needs_human_review(input_data: dict, context: WorkflowContext) -> bool:
    safety_score = input_data.get("safety_score", 1.0)
    return 0.5 <= safety_score < 0.8

# Safety check
safety_check = LambdaPrimitive(lambda data, ctx: {
    **data,
    "safety_score": analyze_safety(data["text"])
})

# Different paths
auto_approve = LambdaPrimitive(lambda data, ctx: {**data, "status": "approved"})
human_review = LambdaPrimitive(lambda data, ctx: {**data, "status": "pending_review"})
auto_reject = LambdaPrimitive(lambda data, ctx: {**data, "status": "rejected"})

# Nested conditional routing
review_check = ConditionalPrimitive(
    condition=needs_human_review,
    then_primitive=human_review,
    else_primitive=auto_reject
)

moderation_pipeline = (
    safety_check >>
    ConditionalPrimitive(
        condition=is_safe_content,
        then_primitive=auto_approve,
        else_primitive=review_check
    )
)

# Safe content → auto approved
result1 = await moderation_pipeline.execute({"text": "Hello world!"}, context)
# Output: {"text": "Hello world!", "safety_score": 0.95, "status": "approved"}

# Borderline content → human review
result2 = await moderation_pipeline.execute({"text": "Questionable content..."}, context)
# Output: {"text": "Questionable content...", "safety_score": 0.6, "status": "pending_review"}

# Unsafe content → auto rejected
result3 = await moderation_pipeline.execute({"text": "Clearly harmful content"}, context)
# Output: {"text": "Clearly harmful content", "safety_score": 0.2, "status": "rejected"}
```

---

## Related Content

### Core Primitives

{{query (and (page-property type [[Primitive]]) (page-property category [[Core]]))}}

### Related Patterns

- [[TTA.dev/Primitives/RouterPrimitive]] - Multi-way routing (conditional is binary routing)
- [[TTA.dev/Primitives/SequentialPrimitive]] - Use after conditional for common processing
- [[TTA.dev/Guides/Workflow Composition]] - Composing conditional with other primitives

---

## References

- **GitHub Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py`](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py)
- **Tests:** [`packages/tta-dev-primitives/tests/test_conditional.py`](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/test_conditional.py)

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Category:** [[Core]]
**Complexity:** [[Medium]]
