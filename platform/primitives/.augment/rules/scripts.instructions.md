# Scripts Guidelines

## Core Principle

**ALL scripts should use `tta-dev-primitives` for orchestration, workflow management, and reliability patterns.**

## Why Use Primitives in Scripts?

Scripts benefit from primitives because they provide:
- **Parallel execution** - Faster completion
- **Automatic retry** - Handle transient failures
- **Timeout protection** - Prevent hangs
- **Caching** - Avoid redundant work
- **Testability** - Easy to test with mocks

## Before Writing a Script

Ask yourself:
1. Does this orchestrate multiple steps? → Use `SequentialPrimitive`
2. Can steps run concurrently? → Use `ParallelPrimitive`
3. Could operations fail transiently? → Add `RetryPrimitive`
4. Could operations hang? → Add `TimeoutPrimitive`
5. Should results be cached? → Add `CachePrimitive`
6. Is there a fallback strategy? → Use `FallbackPrimitive`

## Pattern: Model Evaluation Script

```python
#!/usr/bin/env python3
"""Evaluate multiple models in parallel with retry and timeout."""

import asyncio
from tta_dev_primitives import (
    ParallelPrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    CachePrimitive,
    LambdaPrimitive,
    WorkflowContext,
)

async def test_model(model_data: dict, ctx: WorkflowContext) -> dict:
    """Test a single model."""
    model_name = model_data["model_name"]
    # Actual testing logic here
    return {"model": model_name, "score": 0.85}

def build_workflow(models: list[str]):
    """Build parallel evaluation workflow with resilience."""
    # Wrap each model test with timeout + retry
    model_tests = []
    for model_name in models:
        inject_name = LambdaPrimitive(
            lambda d, c, name=model_name: {**d, "model_name": name}
        )
        test = TimeoutPrimitive(
            RetryPrimitive(
                LambdaPrimitive(test_model),
                max_attempts=3,
                backoff_factor=2.0
            ),
            timeout_seconds=30.0
        )
        model_tests.append(inject_name >> test)

    # Run all in parallel, cache for 1 hour
    return CachePrimitive(
        ParallelPrimitive(model_tests),
        cache_key_fn=lambda d, c: "model-eval",
        ttl_seconds=3600.0
    )

async def main():
    models = ["phi-4", "qwen-0.5b", "qwen-1.5b"]
    workflow = build_workflow(models)
    context = WorkflowContext(workflow_id="model-eval")

    results = await workflow.execute({}, context)

    for result in results:
        print(f"{result['model']}: {result['score']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Pattern: MCP Server Management

```python
#!/usr/bin/env python3
"""Start and monitor MCP servers with retry and parallel startup."""

import asyncio
from tta_dev_primitives import (
    ParallelPrimitive,
    RetryPrimitive,
    SequentialPrimitive,
    TimeoutPrimitive,
    LambdaPrimitive,
    WorkflowContext,
)

async def start_server(server_data: dict, ctx: WorkflowContext) -> dict:
    """Start a single MCP server."""
    name = server_data["name"]
    # Start server logic
    return {"server": name, "status": "running"}

async def health_check(server_data: dict, ctx: WorkflowContext) -> dict:
    """Check server health."""
    # Health check logic
    return {**server_data, "healthy": True}

def build_startup_workflow(servers: list[str]):
    """Build server startup workflow with health checks."""
    # Create startup primitive for each server
    server_starts = []
    for server_name in servers:
        inject_name = LambdaPrimitive(
            lambda d, c, name=server_name: {"name": name}
        )
        start = RetryPrimitive(
            TimeoutPrimitive(
                LambdaPrimitive(start_server),
                timeout_seconds=30.0
            ),
            max_attempts=3,
            backoff_factor=2.0
        )
        health = TimeoutPrimitive(
            LambdaPrimitive(health_check),
            timeout_seconds=10.0
        )
        server_starts.append(inject_name >> start >> health)

    # Start all servers in parallel, then validate
    return SequentialPrimitive([
        ParallelPrimitive(server_starts),
        LambdaPrimitive(lambda d, c: {"all_servers": d, "status": "ready"})
    ])

async def main():
    servers = ["basic", "agent_tool", "knowledge_resource"]
    workflow = build_startup_workflow(servers)
    context = WorkflowContext(workflow_id="mcp-startup")

    result = await workflow.execute({}, context)
    print(f"All servers started: {result['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Pattern: Validation Script

```python
#!/usr/bin/env python3
"""Run package validation checks in parallel."""

import asyncio
from tta_dev_primitives import (
    ParallelPrimitive,
    SequentialPrimitive,
    LambdaPrimitive,
    WorkflowContext,
)

async def run_formatter(data: dict, ctx: WorkflowContext) -> dict:
    """Run code formatter."""
    # subprocess call to ruff format
    return {"check": "format", "passed": True}

async def run_linter(data: dict, ctx: WorkflowContext) -> dict:
    """Run linter."""
    # subprocess call to ruff check
    return {"check": "lint", "passed": True}

async def run_type_check(data: dict, ctx: WorkflowContext) -> dict:
    """Run type checker."""
    # subprocess call to pyright
    return {"check": "types", "passed": True}

async def run_tests(data: dict, ctx: WorkflowContext) -> dict:
    """Run test suite."""
    # subprocess call to pytest
    return {"check": "tests", "passed": True}

def build_validation_workflow(package: str):
    """Build validation workflow with parallel checks."""
    inject_package = LambdaPrimitive(lambda d, c: {"package": package})

    # Run format, lint, types in parallel
    parallel_checks = ParallelPrimitive([
        LambdaPrimitive(run_formatter),
        LambdaPrimitive(run_linter),
        LambdaPrimitive(run_type_check),
    ])

    # Then run tests (depends on code quality)
    tests = LambdaPrimitive(run_tests)

    # Aggregate results
    aggregate = LambdaPrimitive(
        lambda d, c: {
            "package": package,
            "checks": d,
            "all_passed": all(r["passed"] for r in d if isinstance(r, dict))
        }
    )

    return inject_package >> parallel_checks >> tests >> aggregate

async def main():
    workflow = build_validation_workflow("tta-dev-primitives")
    context = WorkflowContext(workflow_id="validation")

    result = await workflow.execute({}, context)

    print(f"Package: {result['package']}")
    print(f"All checks passed: {result['all_passed']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Script Structure

```python
#!/usr/bin/env python3
"""
Script description.

Usage:
    python script.py [args]
"""

import asyncio
import argparse
from tta_dev_primitives import (
    # Import needed primitives
    WorkflowContext,
)

# Define async primitive functions
async def step_function(data: dict, ctx: WorkflowContext) -> dict:
    """Do something."""
    return result

# Build workflow composition
def build_workflow() -> WorkflowPrimitive:
    """Compose workflow from primitives."""
    return workflow

# Main entry point
async def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Script description")
    # Add arguments
    args = parser.parse_args()

    workflow = build_workflow()
    context = WorkflowContext(workflow_id="script-name")

    result = await workflow.execute(input_data, context)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing Scripts

Scripts should be testable using `MockPrimitive`:

```python
# test_my_script.py
import pytest
from tta_dev_primitives.testing import MockPrimitive
from scripts.my_script import build_workflow

@pytest.mark.asyncio
async def test_script_workflow():
    """Test script workflow logic."""
    # Mock external operations
    # Test workflow composition
    # Verify behavior
    pass
```

## Common Patterns

### Pattern: Concurrent Operations
**Use**: `ParallelPrimitive([op1, op2, op3])`

### Pattern: Sequential Pipeline
**Use**: `op1 >> op2 >> op3`

### Pattern: Retry on Failure
**Use**: `RetryPrimitive(operation, max_attempts=3)`

### Pattern: Timeout Protection
**Use**: `TimeoutPrimitive(operation, timeout_seconds=30.0)`

### Pattern: Result Caching
**Use**: `CachePrimitive(operation, cache_key_fn=..., ttl_seconds=3600)`

### Pattern: Fallback Strategy
**Use**: `FallbackPrimitive(primary=expensive_op, fallback=cheap_op)`

## Anti-Patterns

❌ **Manual async orchestration**
```python
# Bad
results = []
for item in items:
    result = await process(item)
    results.append(result)
```

✅ **Use ParallelPrimitive**
```python
# Good
workflow = ParallelPrimitive([
    LambdaPrimitive(lambda d, c, item=item: process(item))
    for item in items
])
results = await workflow.execute({}, context)
```

❌ **Manual retry logic**
```python
# Bad
for attempt in range(3):
    try:
        result = await operation()
        break
    except Exception:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)
```

✅ **Use RetryPrimitive**
```python
# Good
retry_op = RetryPrimitive(
    LambdaPrimitive(operation),
    max_attempts=3,
    backoff_factor=2.0
)
result = await retry_op.execute({}, context)
```

## Quality Checklist

- [ ] Uses primitives for orchestration
- [ ] Has async main() entry point
- [ ] Defines workflow composition function
- [ ] Uses WorkflowContext for execution
- [ ] Includes retry for transient failures
- [ ] Includes timeout for long operations
- [ ] Uses parallel execution where possible
- [ ] Has docstring explaining usage
- [ ] Can be tested with MockPrimitive
- [ ] Formatted with `uv run ruff format`


---
**Logseq:** [[TTA.dev/Platform/Primitives/.augment/Rules/Scripts.instructions]]
