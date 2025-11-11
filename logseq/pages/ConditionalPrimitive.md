# ConditionalPrimitive

**Branch execution based on runtime conditions.**

## Overview

ConditionalPrimitive enables conditional branching in workflows, executing different primitives based on runtime evaluation.

**Import:**
```python
from tta_dev_primitives import ConditionalPrimitive
```

## Usage

### Basic Conditional

```python
from tta_dev_primitives import ConditionalPrimitive, WorkflowContext

workflow = ConditionalPrimitive(
    condition=lambda data, ctx: data["priority"] == "high",
    then_primitive=fast_track_handler,
    else_primitive=normal_handler
)

result = await workflow.execute(request_data, context)
```

### Complex Conditions

```python
def check_complexity(data: dict, context: WorkflowContext) -> bool:
    """Route based on input complexity."""
    text = data.get("text", "")

    # Complex if long or contains code
    is_long = len(text) > 1000
    has_code = "```" in text or "def " in text

    return is_long or has_code

workflow = ConditionalPrimitive(
    condition=check_complexity,
    then_primitive=powerful_llm,
    else_primitive=fast_llm
)
```

### With Context

```python
def user_has_premium(data: dict, context: WorkflowContext) -> bool:
    """Check user tier from context."""
    return context.metadata.get("user_tier") == "premium"

workflow = ConditionalPrimitive(
    condition=user_has_premium,
    then_primitive=premium_features,
    else_primitive=basic_features
)
```

## Patterns

### Multi-Way Branching

```python
# Chain conditionals for multiple paths
workflow = ConditionalPrimitive(
    condition=lambda d, c: d["type"] == "A",
    then_primitive=handle_type_a,
    else_primitive=ConditionalPrimitive(
        condition=lambda d, c: d["type"] == "B",
        then_primitive=handle_type_b,
        else_primitive=handle_default
    )
)
```

**Note:** For many branches, use [[RouterPrimitive]] instead.

### Validation Branching

```python
from pydantic import BaseModel, ValidationError

def is_valid(data: dict, context: WorkflowContext) -> bool:
    try:
        InputModel(**data)
        return True
    except ValidationError:
        return False

workflow = ConditionalPrimitive(
    condition=is_valid,
    then_primitive=process_valid_input,
    else_primitive=return_error_response
)
```

### Feature Flags

```python
def feature_enabled(data: dict, context: WorkflowContext) -> bool:
    """Check if feature flag is enabled."""
    feature_flags = context.metadata.get("feature_flags", {})
    return feature_flags.get("new_algorithm", False)

workflow = ConditionalPrimitive(
    condition=feature_enabled,
    then_primitive=new_algorithm,
    else_primitive=legacy_algorithm
)
```

## Examples

### Size-Based Routing

```python
# Route to different models based on input size
size_router = ConditionalPrimitive(
    condition=lambda d, c: len(d.get("text", "")) < 500,
    then_primitive=fast_small_model,
    else_primitive=powerful_large_model
)

workflow = cache >> size_router >> format_output
```

### A/B Testing

```python
import random

def in_test_group(data: dict, context: WorkflowContext) -> bool:
    """50/50 A/B split based on user_id."""
    user_id = data.get("user_id", "")
    return hash(user_id) % 2 == 0

ab_test = ConditionalPrimitive(
    condition=in_test_group,
    then_primitive=variant_a,
    else_primitive=variant_b
)
```

### Rate Limit Handling

```python
from datetime import datetime, timedelta

def within_rate_limit(data: dict, context: WorkflowContext) -> bool:
    """Check if user is within rate limit."""
    user_id = data["user_id"]
    last_request = context.metadata.get(f"last_request_{user_id}")

    if not last_request:
        return True

    elapsed = datetime.now() - last_request
    return elapsed > timedelta(seconds=1)

workflow = ConditionalPrimitive(
    condition=within_rate_limit,
    then_primitive=process_request >> update_timestamp,
    else_primitive=return_rate_limit_error
)
```

## Comparison with RouterPrimitive

| Feature | ConditionalPrimitive | RouterPrimitive |
|---------|---------------------|-----------------|
| **Branches** | 2 (then/else) | Many |
| **Selection** | Boolean condition | Router function returns key |
| **Use case** | Simple if/else | Complex routing logic |
| **Syntax** | More explicit | More flexible |

### When to Use Conditional

- ✅ Binary decision (yes/no, true/false)
- ✅ Simple condition logic
- ✅ Only 2 paths needed

### When to Use Router

- ✅ Multiple destinations (3+)
- ✅ Dynamic route selection
- ✅ Route based on multiple factors

## Type Safety

```python
from tta_dev_primitives import ConditionalPrimitive, WorkflowPrimitive

# Both branches must have compatible types
then_primitive: WorkflowPrimitive[Input, Output]
else_primitive: WorkflowPrimitive[Input, Output]

conditional = ConditionalPrimitive(
    condition=check_condition,
    then_primitive=then_primitive,
    else_primitive=else_primitive
)

# Output type is Output (from both branches)
result: Output = await conditional.execute(input_data, context)
```

## Observability

### Automatic Metrics

- `conditional_evaluation_total` - Times condition evaluated
- `conditional_then_branch_total` - Times then branch taken
- `conditional_else_branch_total` - Times else branch taken

### Automatic Spans

- `conditional.evaluate` - Condition evaluation
- `conditional.then` - Then branch execution
- `conditional.else` - Else branch execution

### Logging

```python
# Automatic structured logs
logger.info(
    "conditional_branch_taken",
    condition_result=True,
    branch="then",
    primitive="fast_track_handler"
)
```

## Related Primitives

### Composition
- [[SequentialPrimitive]] - Sequential execution
- [[ParallelPrimitive]] - Parallel execution
- [[RouterPrimitive]] - Multi-way routing (better for 3+ branches)

### Recovery
- [[FallbackPrimitive]] - Automatic fallback on failure
- [[RetryPrimitive]] - Retry logic
- [[TimeoutPrimitive]] - Timeout protection

## Implementation

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py`

**Tests:** `packages/tta-dev-primitives/tests/test_conditional.py`

## Related Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Primitives]] - All primitives
- [[TTA.dev/Examples]] - Working examples
- [[RouterPrimitive]] - Alternative for multi-way branching

## Tags

primitive:: core
type:: control-flow
pattern:: branching

- [[Project Hub]]