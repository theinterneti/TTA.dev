# Documentation Guidelines

## Documentation Principles

1. **Show, Don't Tell**: Include working code examples
2. **Be Specific**: Reference actual files, classes, and functions
3. **Stay Current**: Update docs when code changes
4. **User-Focused**: Write for developers using the code

## README Structure

Every package README should have:

```markdown
# Package Name

Brief one-line description.

## Features

- Feature 1 with brief explanation
- Feature 2 with brief explanation

## Installation

\`\`\`bash
uv pip install -e packages/package-name
\`\`\`

## Quick Start

\`\`\`python
# Minimal working example
from package_name import Component

result = Component().do_thing()
\`\`\`

## Usage Examples

### Example 1: Common Use Case

\`\`\`python
# Complete, runnable example
\`\`\`

### Example 2: Advanced Pattern

\`\`\`python
# Complete, runnable example
\`\`\`

## API Reference

### Class: ComponentName

Description of component.

**Parameters:**
- `param1` (type): Description
- `param2` (type): Description

**Returns:** Return type and description

**Example:**
\`\`\`python
component = ComponentName(param1="value")
result = component.method()
\`\`\`

## Development

\`\`\`bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Format code
uv run ruff format .
\`\`\`

## License

License information
```

## Code Examples in Documentation

### Good Example
```markdown
### Using Sequential Workflows

The `SequentialPrimitive` executes operations in order, passing output from each step as input to the next:

\`\`\`python
from tta_dev_primitives import SequentialPrimitive, LambdaPrimitive, WorkflowContext

# Define steps
validate = LambdaPrimitive(lambda x, ctx: {"validated": True, **x})
process = LambdaPrimitive(lambda x, ctx: {"processed": True, **x})

# Compose workflow
workflow = validate >> process

# Execute
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute({"input": "data"}, context)

print(result)  # {"validated": True, "processed": True, "input": "data"}
\`\`\`

This pattern is useful for:
- Data transformation pipelines
- Multi-stage processing
- Validation → Processing → Storage flows
```

### Bad Example
```markdown
### Using Sequential Workflows

You can use SequentialPrimitive to run things in order.

\`\`\`python
workflow = Sequential([step1, step2])
result = workflow.execute(input)
\`\`\`
```

Why bad:
- No imports shown
- No context about what step1/step2 are
- Missing WorkflowContext
- No expected output
- No explanation of when to use

## Linking to Code

Reference actual files:

```markdown
For the implementation, see [`src/core/sequential.py`](src/core/sequential.py).

Example usage in [`examples/real_world_workflows.py`](examples/real_world_workflows.py).
```

## Documenting Primitives

When documenting a primitive:

```markdown
## CachePrimitive

Wraps a workflow primitive with LRU caching and TTL support.

### Parameters

- `primitive` (`WorkflowPrimitive[T, U]`): The primitive to wrap
- `cache_key_fn` (`Callable`): Function to generate cache key from input and context
- `ttl_seconds` (`float`, optional): Time-to-live for cached entries. Default: `3600.0`
- `max_size` (`int`, optional): Maximum cache entries. Default: `128`

### Returns

Cached result of type `U`, or fresh execution if cache miss.

### Example

\`\`\`python
from tta_dev_primitives import CachePrimitive, LambdaPrimitive, WorkflowContext

async def expensive_operation(data, ctx):
    # Simulate expensive computation
    await asyncio.sleep(2.0)
    return {"result": data["query"]}

# Wrap with cache
cached = CachePrimitive(
    LambdaPrimitive(expensive_operation),
    cache_key_fn=lambda d, c: d.get("query", ""),
    ttl_seconds=3600.0  # 1 hour
)

context = WorkflowContext()

# First call - cache miss (2 seconds)
result1 = await cached.execute({"query": "test"}, context)

# Second call - cache hit (instant)
result2 = await cached.execute({"query": "test"}, context)

# Check cache stats
stats = cached.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")  # 50.00%
\`\`\`

### Use Cases

- Caching LLM responses for repeated queries
- Storing expensive computation results
- Reducing API calls to external services
- Improving response time for frequent requests
```

## Changelog Format

Use [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature X with brief description

### Changed
- Changed behavior Y with brief description

### Fixed
- Bug fix Z with brief description

## [0.2.0] - 2025-10-28

### Added
- `ParallelPrimitive` for concurrent execution
- `MockPrimitive` for testing workflows

### Changed
- Renamed package from `tta-workflow-primitives` to `tta-dev-primitives`

### Fixed
- Cache TTL not expiring correctly

## [0.1.0] - 2025-10-20

Initial release with core primitives.
```

## Architecture Documentation

Use diagrams and clear structure:

```markdown
## Architecture

### Workflow Primitive Hierarchy

\`\`\`
WorkflowPrimitive[T, U]
├── SequentialPrimitive
├── ParallelPrimitive
├── ConditionalPrimitive
├── RouterPrimitive
└── Decorated Primitives
    ├── CachePrimitive
    ├── RetryPrimitive
    ├── TimeoutPrimitive
    └── FallbackPrimitive
\`\`\`

### Composition Patterns

**Sequential (>>)**: Output of each step becomes input to next
\`\`\`python
workflow = step1 >> step2 >> step3
\`\`\`

**Parallel (|)**: All branches receive same input
\`\`\`python
workflow = branch1 | branch2 | branch3
\`\`\`

**Mixed**: Combine patterns
\`\`\`python
workflow = input_processor >> (fast_path | slow_path) >> aggregator
\`\`\`
```

## Common Mistakes to Avoid

❌ **Vague instructions**
```markdown
Use the primitive to do things.
```

✅ **Specific with examples**
```markdown
Use `RetryPrimitive` to automatically retry failed operations with exponential backoff:

\`\`\`python
retry_workflow = RetryPrimitive(
    api_call_primitive,
    max_attempts=3,
    backoff_factor=2.0
)
\`\`\`
```

❌ **Outdated examples**
```python
# Using old package name
from tta_workflow_primitives import ...  # Wrong!
```

✅ **Current examples**
```python
# Using current package name
from tta_dev_primitives import ...  # Correct!
```

❌ **No context**
```python
result = workflow.execute(data)  # Incomplete!
```

✅ **Complete context**
```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(workflow_id="demo", session_id="123")
result = await workflow.execute(data, context)  # Complete!
```

## Quality Checklist

- [ ] All code examples are complete and runnable
- [ ] Imports are shown
- [ ] WorkflowContext is included where needed
- [ ] Expected output is shown
- [ ] Use cases are explained
- [ ] Links to actual files work
- [ ] Examples use current package names
- [ ] No lorem ipsum or placeholder text
- [ ] Formatting is consistent
- [ ] Technical terms are explained


---
**Logseq:** [[TTA.dev/Platform/Primitives/.cursor/Rules/Documentation.instructions]]
