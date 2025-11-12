# TTA.dev/Integrations/CodeExecution/E2BPrimitive

type:: [I] Integration
status:: stable
integration-type:: code-execution
tags:: #integration, #code-execution, #sandbox, #e2b
context-level:: 2-Operational
external-service:: E2B (e2b.dev)
wraps-primitive:: [[TTA.dev/Primitives/Core/WorkflowPrimitive]]
requires-config:: [[TTA.dev/Data/WorkflowContext]]
api-endpoint:: https://api.e2b.dev
dependencies:: e2b, e2b-code-interpreter
import-path:: from tta_dev_primitives.integrations import CodeExecutionPrimitive
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/integrations/e2b_primitive.py
created-date:: [[2025-11-11]]
last-updated:: [[2025-11-11]]

---

## Overview

**E2BPrimitive** (CodeExecutionPrimitive) provides safe, sandboxed Python code execution using E2B's cloud infrastructure. It enables AI-generated code validation, test execution, and iterative refinement workflows without local security risks.

**Integration Type:** code-execution
**External Service:** E2B (e2b.dev)
**Status:** stable

**Key Features:**
- ✅ Sandboxed execution - Isolated from local environment
- ✅ FREE tier available - No credit card required
- ✅ Fast spin-up - ~2-3 second cold start
- ✅ Full Python support - Standard library + pip packages
- ✅ Observable - Full OpenTelemetry integration

---

## Prerequisites

### E2B Account Setup

1. **Sign up:** Visit https://e2b.dev and create free account
2. **Get API key:** Navigate to Settings → API Keys
3. **Copy key:** Save for environment variable

### Environment Variables

```bash
# Required
export E2B_API_KEY="your-api-key-here"

# Optional
export E2B_TIMEOUT="30"  # Execution timeout in seconds
```

### Python Dependencies

```bash
# Install TTA.dev with E2B integration
uv add tta-dev-primitives e2b e2b-code-interpreter

# Or separately
uv add e2b e2b-code-interpreter
```

---

## Installation

### Via UV (Recommended)

```bash
uv add tta-dev-primitives e2b e2b-code-interpreter
```

### Via Pip

```bash
pip install tta-dev-primitives e2b e2b-code-interpreter
```

---

## Configuration

### Basic Configuration

```python
import os
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# API key from environment
api_key = os.getenv("E2B_API_KEY")

# Create primitive
code_executor = CodeExecutionPrimitive(
    api_key=api_key,
    timeout=30
)
```

### Advanced Configuration

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

code_executor = CodeExecutionPrimitive(
    api_key=os.getenv("E2B_API_KEY"),
    timeout=60,
    template="base",  # E2B template to use
    enable_pip_install=True,  # Allow pip installs
    max_output_size=10_000  # Limit output size
)
```

---

## Usage

### Basic Execution

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives import WorkflowContext
import os

# Initialize
executor = CodeExecutionPrimitive(api_key=os.getenv("E2B_API_KEY"))

# Execute code
code = """
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)

print(factorial(5))
"""

context = WorkflowContext(correlation_id="exec-123")
result = await executor.execute({"code": code}, context)

print(result["success"])  # True
print(result["logs"])     # "120\n"
```

### With Error Handling

```python
# Execute code with syntax error
bad_code = "print('missing quote)"

result = await executor.execute({"code": bad_code}, context)

print(result["success"])  # False
print(result["error"])    # "SyntaxError: EOL while scanning string literal"
```

### Install Packages

```python
code = """
# Install package
import os
os.system('pip install requests')

import requests
response = requests.get('https://api.github.com')
print(response.status_code)
"""

result = await executor.execute(
    {"code": code, "timeout": 60},
    context
)
```

---

## API Reference

### Constructor

```python
CodeExecutionPrimitive(
    api_key: str,
    timeout: int = 30,
    template: str = "base",
    enable_pip_install: bool = True,
    max_output_size: int = 10_000
)
```

**Parameters:**
- `api_key` - E2B API key (get from https://e2b.dev)
- `timeout` - Execution timeout in seconds (default: 30)
- `template` - E2B sandbox template (default: "base")
- `enable_pip_install` - Allow pip package installation (default: True)
- `max_output_size` - Max output characters (default: 10,000)

### Methods

#### `execute(input_data: dict, context: WorkflowContext) -> dict`

Executes Python code in E2B sandbox.

**Input Schema:**
```python
{
    "code": str,           # Python code to execute (required)
    "timeout": int | None  # Override default timeout (optional)
}
```

**Output Schema:**
```python
{
    "success": bool,       # Execution succeeded
    "logs": str,           # Captured stdout/stderr
    "error": str | None,   # Error message if failed
    "execution_time_ms": float  # Execution duration
}
```

**Raises:**
- `ValueError` - Invalid input (missing code)
- `TimeoutError` - Execution exceeded timeout
- `E2BError` - E2B service error

---

## Composition Patterns

### Pattern 1: Iterative Code Refinement

**Use Case:** Generate code with LLM, execute, fix errors, repeat

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives.recovery import RetryPrimitive

class IterativeCodeGenerator:
    def __init__(self):
        self.executor = CodeExecutionPrimitive(api_key=os.getenv("E2B_API_KEY"))
        self.max_attempts = 3

    async def generate_working_code(self, requirement: str, context):
        """Keep generating until code executes successfully."""
        previous_errors = []

        for attempt in range(1, self.max_attempts + 1):
            # Step 1: Generate code (LLM)
            code = await llm_generate_code(requirement, previous_errors)

            # Step 2: Execute in E2B sandbox
            result = await self.executor.execute({"code": code}, context)

            # Step 3: Check if it works
            if result["success"]:
                return {"code": code, "output": result["logs"]}

            # Step 4: Feed error back to LLM for next iteration
            previous_errors.append({
                "attempt": attempt,
                "code": code,
                "error": result["error"]
            })

        raise Exception("Failed to generate working code")
```

### Pattern 2: Test Validation Workflow

```python
# Workflow: Generate code → Execute tests → Validate
workflow = (
    generate_code_with_llm >>
    CodeExecutionPrimitive(api_key=api_key) >>
    validate_test_results >>
    format_response
)
```

### Pattern 3: With Caching

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache execution results to avoid re-running identical code
cached_executor = CachePrimitive(
    CodeExecutionPrimitive(api_key=api_key),
    ttl_seconds=3600,
    key_fn=lambda data, ctx: data["code"]  # Cache by code content
)
```

---

## Examples

### Example 1: Validate Generated Code

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives import WorkflowContext
import os

async def validate_code(generated_code: str) -> bool:
    """Validate LLM-generated code by executing it."""

    executor = CodeExecutionPrimitive(api_key=os.getenv("E2B_API_KEY"))
    context = WorkflowContext()

    result = await executor.execute({"code": generated_code}, context)

    return result["success"]

# Usage
code = 'print("Hello, World!")'
is_valid = await validate_code(code)  # True
```

### Example 2: Run Tests

```python
test_code = """
def add(a, b):
    return a + b

# Tests
assert add(1, 2) == 3
assert add(-1, 1) == 0
assert add(0, 0) == 0

print("All tests passed!")
"""

result = await executor.execute({"code": test_code}, context)
print(result["logs"])  # "All tests passed!"
```

**See:** `packages/tta-dev-primitives/examples/e2b_iterative_code_refinement.py`

---

## Authentication

### API Key

```python
import os

# From environment variable (recommended)
api_key = os.getenv("E2B_API_KEY")

# Or hardcoded (NOT recommended in production)
api_key = "e2b_xxxxxxxxxxxxx"

executor = CodeExecutionPrimitive(api_key=api_key)
```

### Free Tier Limits

E2B offers a **FREE tier** with:
- ✅ 100 hours of compute per month
- ✅ No credit card required
- ✅ Full feature access

**When to upgrade:**
- Need more than 100 hours/month
- Require dedicated compute resources
- Want higher rate limits

---

## Error Handling

### Common Errors

**`ValueError`** - Missing or invalid input
```python
# ❌ Missing code
result = await executor.execute({}, context)

# ✅ Fix - provide code
result = await executor.execute({"code": "print('hi')"}, context)
```

**`TimeoutError`** - Execution exceeded timeout
```python
# ❌ Infinite loop
code = "while True: pass"

# ✅ Fix - increase timeout or fix code
result = await executor.execute(
    {"code": code, "timeout": 60},
    context
)
```

**`E2BError`** - E2B service error
```python
# Usually indicates API key issue or service outage
# Check API key is valid and E2B status page
```

### Retry Strategy

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry transient E2B failures
resilient_executor = RetryPrimitive(
    CodeExecutionPrimitive(api_key=api_key),
    max_retries=3,
    backoff_strategy="exponential"
)
```

---

## Observability

### Spans Created

- `code_execution.execute` - Full execution span
- `code_execution.sandbox_init` - Sandbox initialization
- `code_execution.code_run` - Code execution phase

### Metrics Emitted

- `code_execution_requests_total` - Total executions
- `code_execution_success_total` - Successful executions
- `code_execution_error_total` - Failed executions
- `code_execution_duration_seconds` - Execution latency

### Logs

Structured logs include:
```json
{
  "primitive": "CodeExecutionPrimitive",
  "correlation_id": "exec-123",
  "success": true,
  "execution_time_ms": 2345.67,
  "code_length": 156
}
```

---

## Performance

**Typical Latency:**
- Cold start: ~2-3 seconds
- Warm execution: ~100-500ms

**Throughput:**
- Depends on sandbox availability
- ~10-20 concurrent executions typical

**Resource Usage:**
- CPU: Low (delegated to E2B)
- Memory: Low (only stores code/results)
- Network: Moderate (API calls to E2B)

### Optimization Tips

1. **Reuse sandboxes** - E2B supports session reuse (future feature)
2. **Cache results** - Use [[TTA.dev/Primitives/Performance/CachePrimitive]] for identical code
3. **Batch operations** - Execute multiple code blocks in single session
4. **Set appropriate timeouts** - Avoid waiting for infinite loops

---

## Testing

### Unit Tests

```python
from unittest.mock import AsyncMock
import pytest

@pytest.mark.asyncio
async def test_code_execution_success():
    executor = CodeExecutionPrimitive(api_key="test-key")

    # Mock E2B client
    executor._client = AsyncMock(return_value={
        "success": True,
        "logs": "42\n",
        "error": None
    })

    result = await executor.execute(
        {"code": "print(42)"},
        WorkflowContext()
    )

    assert result["success"] is True
    assert "42" in result["logs"]
```

### Integration Tests

Requires E2B API key:

```bash
export E2B_API_KEY="your-key"
RUN_INTEGRATION=true pytest tests/integration/test_e2b_primitive.py
```

---

## Troubleshooting

### Issue: "Invalid API Key" Error

**Symptom:** `E2BError: Invalid API key`
**Solution:**
1. Check API key is correct
2. Verify environment variable is set
3. Generate new key from https://e2b.dev/settings

### Issue: Timeout Errors

**Symptom:** Code execution times out
**Solution:**
1. Increase timeout parameter
2. Check for infinite loops in code
3. Optimize code complexity

### Issue: Package Installation Fails

**Symptom:** `pip install` doesn't work
**Solution:**
1. Ensure `enable_pip_install=True`
2. Check package name spelling
3. Increase timeout for package installation

---

## Related Integrations

- [[TTA.dev/Integrations/MCP/MCPCodeExecution]] - MCP-based code execution
- [[TTA.dev/Integrations/LLM/AnthropicPrimitive]] - For generating code to execute

---

## Related Primitives

Works well with:

- [[TTA.dev/Primitives/Recovery/RetryPrimitive]] - Retry failed executions
- [[TTA.dev/Primitives/Performance/CachePrimitive]] - Cache execution results
- [[TTA.dev/Primitives/Core/SequentialPrimitive]] - Chain with code generation

---

## Source Code

**Location:** `packages/tta-dev-primitives/src/tta_dev_primitives/integrations/e2b_primitive.py`
**Tests:** `packages/tta-dev-primitives/tests/integrations/test_e2b_primitive.py`

---

## External Resources

- [E2B Official Documentation](https://e2b.dev/docs)
- [E2B Python SDK](https://github.com/e2b-dev/e2b)
- [E2B Pricing](https://e2b.dev/pricing)
- [E2B Templates](https://e2b.dev/docs/templates)

---

## Tags

#integration #code-execution #sandbox #e2b #safety #validation
