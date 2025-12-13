# E2B Integration with TTA.dev Primitives

**Complete guide for using E2B Code Interpreter with TTA.dev workflow primitives.**

---

## Overview

E2B (Environment-as-a-Service) provides secure, sandboxed environments for executing code. The TTA.dev `CodeExecutionPrimitive` integrates E2B seamlessly into workflow compositions, enabling:

- ✅ **Safe Code Execution** - Sandboxed environments prevent harmful code
- ✅ **Validation Workflows** - Test generated code before deployment
- ✅ **Iterative Refinement** - Generate → Execute → Fix → Repeat patterns
- ✅ **Benchmarking** - Compare framework implementations objectively
- ✅ **AI Code Generation** - Validate LLM-generated code automatically

## Quick Start

### Installation

```bash
# Install E2B SDK
pip install e2b-code-interpreter

# Set API key
export E2B_API_KEY="your-api-key-here"
# or
export E2B_KEY="your-api-key-here"  # Alternative name
```

### Basic Usage

```python
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Initialize primitive
executor = CodeExecutionPrimitive()

# Execute code
context = WorkflowContext(correlation_id="demo")
result = await executor.execute({
    "code": "print('Hello from E2B!')",
    "timeout": 30
}, context)

print(result["success"])  # True
print(result["logs"])     # ['Hello from E2B!']
```

### Compose with Other Primitives

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive

# Create resilient validation workflow
validation_workflow = (
    code_generator >>
    RetryPrimitive(
        primitive=CodeExecutionPrimitive(),
        max_retries=3
    ) >>
    result_validator
)
```

## CodeExecutionPrimitive API

### Input Schema

```python
{
    "code": str,              # Required: Python code to execute
    "timeout": int = 30,      # Optional: Execution timeout in seconds
    "files": dict = None,     # Optional: Files to create in sandbox
    "install": list = None    # Optional: Packages to install
}
```

### Output Schema

```python
{
    "success": bool,          # True if execution completed without errors
    "logs": list[str],        # Stdout/stderr output lines
    "error": str | None,      # Error message if execution failed
    "results": dict,          # Structured results if code produces them
    "execution_time": float,  # Time taken in seconds
    "sandbox_id": str         # E2B sandbox identifier for debugging
}
```

### Configuration Options

```python
# Custom configuration
executor = CodeExecutionPrimitive(
    api_key="custom-key",           # Override environment variable
    template="python",              # E2B template (default: python)
    timeout=60,                     # Default timeout
    auto_install_packages=True,     # Auto-install imports
    working_directory="/tmp"        # Sandbox working directory
)
```

## Usage Patterns

### Pattern 1: Iterative Code Generation

**Use Case:** Generate code with LLM, test it, fix errors, repeat until working.

```python
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive

class IterativeCodeGenerator:
    """Generate working code through iteration."""

    def __init__(self):
        self.executor = CodeExecutionPrimitive()
        self.max_attempts = 5

    async def generate_working_code(self, requirement: str, context) -> dict:
        """Generate code that actually works."""
        previous_errors = []

        for attempt in range(1, self.max_attempts + 1):
            # Generate code (with error context if retrying)
            code = await self.generate_code(requirement, previous_errors)

            # Test in E2B sandbox
            result = await self.executor.execute({
                "code": code,
                "timeout": 30
            }, context)

            # Check if it works
            if result["success"]:
                return {
                    "code": code,
                    "attempt": attempt,
                    "output": result["logs"],
                    "working": True
                }

            # Capture error for next iteration
            previous_errors.append({
                "attempt": attempt,
                "code": code,
                "error": result["error"],
                "logs": result["logs"]
            })

        # All attempts failed
        raise Exception(f"Failed to generate working code after {self.max_attempts} attempts")

    async def generate_code(self, requirement: str, errors: list) -> str:
        """Generate code with LLM (implementation depends on your LLM setup)."""
        if not errors:
            prompt = f"Generate Python code for: {requirement}"
        else:
            last_error = errors[-1]
            prompt = f"""
            Generate Python code for: {requirement}

            Previous attempt failed with error: {last_error['error']}
            Previous code:
            {last_error['code']}

            Fix the error and provide working code.
            """

        # Replace with your LLM call
        return await your_llm_call(prompt)

# Usage
generator = IterativeCodeGenerator()
result = await generator.generate_working_code(
    "Create a function that calculates fibonacci numbers",
    context
)
print(f"Working code generated in {result['attempt']} attempts")
```

### Pattern 2: Code Validation Pipeline

**Use Case:** Validate generated code meets requirements before deployment.

```python
from tta_dev_primitives import SequentialPrimitive

class CodeValidationPipeline:
    """Multi-stage code validation."""

    def __init__(self):
        self.pipeline = (
            syntax_validator >>
            security_scanner >>
            CodeExecutionPrimitive() >>  # Functional validation
            performance_tester >>
            integration_tester
        )

    async def validate_code(self, code: str, context) -> dict:
        """Run complete validation pipeline."""
        return await self.pipeline.execute({"code": code}, context)

# Individual validators
async def syntax_validator(data: dict, context) -> dict:
    """Check syntax without execution."""
    try:
        compile(data["code"], "<string>", "exec")
        return {**data, "syntax_valid": True}
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {e}")

async def security_scanner(data: dict, context) -> dict:
    """Scan for dangerous patterns."""
    dangerous = ["eval", "exec", "import os", "__import__"]
    if any(pattern in data["code"] for pattern in dangerous):
        raise ValueError("Code contains potentially dangerous patterns")
    return data

async def performance_tester(data: dict, context) -> dict:
    """Check performance metrics."""
    if data.get("execution_time", 0) > 10:
        raise ValueError("Code execution too slow")
    return data
```

### Pattern 3: Benchmarking Framework Integration

**Use Case:** Compare different implementations objectively.

```python
from tta_dev_primitives.benchmarking import BenchmarkSuite
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive

class CodeBenchmark:
    """Benchmark different code implementations."""

    def __init__(self):
        self.executor = CodeExecutionPrimitive()
        self.suite = BenchmarkSuite()

    async def compare_implementations(self, implementations: dict, context) -> dict:
        """Compare multiple implementations of same functionality."""
        results = {}

        for name, code in implementations.items():
            # Execute each implementation
            result = await self.executor.execute({
                "code": code,
                "timeout": 60
            }, context)

            if result["success"]:
                results[name] = {
                    "execution_time": result["execution_time"],
                    "output": result["logs"],
                    "lines_of_code": len(code.splitlines()),
                    "success": True
                }
            else:
                results[name] = {
                    "error": result["error"],
                    "success": False
                }

        return results

# Usage
benchmark = CodeBenchmark()
results = await benchmark.compare_implementations({
    "tta_primitives": tta_implementation_code,
    "vanilla_python": vanilla_implementation_code,
    "langchain": langchain_implementation_code
}, context)
```

### Pattern 4: Testing Infrastructure

**Use Case:** Test TTA.dev primitives themselves using E2B.

```python
import pytest
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive
from tta_dev_primitives.testing import create_test_context

@pytest.mark.asyncio
async def test_primitive_with_e2b():
    """Test primitive using E2B execution."""
    executor = CodeExecutionPrimitive()
    context = create_test_context()

    # Test code that uses your primitive
    test_code = '''
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.testing import MockPrimitive

# Test sequential composition
mock1 = MockPrimitive(return_value={"step": 1})
mock2 = MockPrimitive(return_value={"step": 2})

workflow = mock1 >> mock2
result = await workflow.execute({"input": "test"}, context)

assert result["step"] == 2
print("✅ Sequential primitive test passed")
    '''

    result = await executor.execute({"code": test_code}, context)

    assert result["success"], f"Test failed: {result.get('error')}"
    assert "✅ Sequential primitive test passed" in result["logs"]
```

## Best Practices

### 1. Error Handling

```python
async def robust_execution(code: str, context) -> dict:
    """Execute code with comprehensive error handling."""
    executor = CodeExecutionPrimitive()

    try:
        result = await executor.execute({
            "code": code,
            "timeout": 30
        }, context)

        if not result["success"]:
            # Log structured error info
            logger.error(
                "Code execution failed",
                extra={
                    "sandbox_id": result.get("sandbox_id"),
                    "error": result.get("error"),
                    "execution_time": result.get("execution_time"),
                    "correlation_id": context.correlation_id
                }
            )

        return result

    except Exception as e:
        logger.exception("E2B execution exception", extra={
            "correlation_id": context.correlation_id
        })
        return {
            "success": False,
            "error": str(e),
            "logs": [],
            "execution_time": 0
        }
```

### 2. Timeout Management

```python
# Configure appropriate timeouts
short_tasks = CodeExecutionPrimitive(timeout=10)    # Quick validation
medium_tasks = CodeExecutionPrimitive(timeout=60)   # Data processing
long_tasks = CodeExecutionPrimitive(timeout=300)    # ML training

# Use timeout primitive for extra protection
from tta_dev_primitives.recovery import TimeoutPrimitive

protected_executor = TimeoutPrimitive(
    primitive=CodeExecutionPrimitive(),
    timeout_seconds=30,
    raise_on_timeout=True
)
```

### 3. Resource Management

```python
class ResourceManagedExecution:
    """Manage E2B sandbox resources efficiently."""

    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = CodeExecutionPrimitive()

    async def execute_with_limits(self, code: str, context) -> dict:
        """Execute with concurrency limits."""
        async with self.semaphore:
            return await self.executor.execute({"code": code}, context)
```

### 4. Caching for Performance

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache execution results
cached_executor = CachePrimitive(
    primitive=CodeExecutionPrimitive(),
    ttl_seconds=3600,  # 1 hour
    key_fn=lambda data, ctx: hashlib.md5(data["code"].encode()).hexdigest()
)

# Use in workflow
workflow = (
    code_generator >>
    cached_executor >>  # Won't re-execute same code
    result_processor
)
```

## Advanced Features

### File System Operations

```python
# Create files in sandbox
result = await executor.execute({
    "code": """
import json

# Read data file
with open('data.json', 'r') as f:
    data = json.load(f)

# Process data
result = {'count': len(data['items'])}

# Write result
with open('output.json', 'w') as f:
    json.dump(result, f)

print(f"Processed {result['count']} items")
    """,
    "files": {
        "data.json": json.dumps({"items": [1, 2, 3, 4, 5]})
    }
}, context)
```

### Package Installation

```python
# Install packages in sandbox
result = await executor.execute({
    "code": """
import pandas as pd
import numpy as np

# Create sample data
df = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100)
})

# Calculate correlation
correlation = df['x'].corr(df['y'])
print(f"Correlation: {correlation:.3f}")
    """,
    "install": ["pandas", "numpy"]
}, context)
```

### Environment Configuration

```python
# Custom environment setup
executor = CodeExecutionPrimitive(
    template="python",
    timeout=120,
    working_directory="/workspace",
    environment_vars={
        "PYTHONPATH": "/workspace/src",
        "DATA_PATH": "/workspace/data"
    }
)
```

## Testing Patterns

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive

@pytest.mark.asyncio
async def test_code_execution_success():
    """Test successful code execution."""
    with patch('e2b_code_interpreter.AsyncSandbox') as mock_sandbox_class:
        # Mock sandbox instance
        mock_sandbox = AsyncMock()
        mock_sandbox_class.create.return_value.__aenter__.return_value = mock_sandbox
        mock_sandbox.run_code.return_value.logs = ["Hello World"]
        mock_sandbox.run_code.return_value.error = None
        mock_sandbox.sandbox_id = "test-sandbox-123"

        # Test execution
        executor = CodeExecutionPrimitive()
        result = await executor.execute({
            "code": "print('Hello World')"
        }, context)

        assert result["success"] is True
        assert result["logs"] == ["Hello World"]
        assert "test-sandbox-123" in result["sandbox_id"]

@pytest.mark.asyncio
async def test_code_execution_error():
    """Test error handling."""
    with patch('e2b_code_interpreter.AsyncSandbox') as mock_sandbox_class:
        mock_sandbox = AsyncMock()
        mock_sandbox_class.create.return_value.__aenter__.return_value = mock_sandbox
        mock_sandbox.run_code.return_value.logs = []
        mock_sandbox.run_code.return_value.error = "NameError: name 'undefined_var' is not defined"

        executor = CodeExecutionPrimitive()
        result = await executor.execute({
            "code": "print(undefined_var)"
        }, context)

        assert result["success"] is False
        assert "NameError" in result["error"]
```

### Integration Testing

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_e2b_integration():
    """Test with real E2B API (requires E2B_API_KEY)."""
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        pytest.skip("E2B_API_KEY not set")

    executor = CodeExecutionPrimitive(api_key=api_key)
    context = create_test_context()

    result = await executor.execute({
        "code": """
import sys
print(f"Python version: {sys.version}")
print("✅ E2B integration working")
        """
    }, context)

    assert result["success"] is True
    assert "Python version:" in "\n".join(result["logs"])
    assert "✅ E2B integration working" in result["logs"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_integration():
    """Test E2B primitive in workflow."""
    from tta_dev_primitives import SequentialPrimitive
    from tta_dev_primitives.testing import MockPrimitive

    # Setup workflow
    code_generator = MockPrimitive(return_value={
        "code": "result = 2 + 2\nprint(f'Result: {result}')"
    })

    executor = CodeExecutionPrimitive()

    validator = MockPrimitive(return_value={"validated": True})

    workflow = code_generator >> executor >> validator

    # Execute workflow
    result = await workflow.execute({"task": "add numbers"}, context)

    assert result["validated"] is True
    assert code_generator.call_count == 1
    assert validator.call_count == 1
```

## Observability Integration

### Tracing

```python
from opentelemetry import trace
from tta_dev_primitives.observability import InstrumentedPrimitive

class TracedCodeExecution(InstrumentedPrimitive):
    """E2B execution with enhanced tracing."""

    def __init__(self):
        super().__init__()
        self.executor = CodeExecutionPrimitive()
        self.tracer = trace.get_tracer(__name__)

    async def _execute_impl(self, data: dict, context) -> dict:
        """Execute with detailed tracing."""
        with self.tracer.start_as_current_span("e2b_code_execution") as span:
            # Add span attributes
            span.set_attribute("code_length", len(data["code"]))
            span.set_attribute("timeout", data.get("timeout", 30))
            span.set_attribute("has_files", bool(data.get("files")))

            # Execute code
            result = await self.executor.execute(data, context)

            # Record results
            span.set_attribute("execution_success", result["success"])
            span.set_attribute("execution_time_ms", result["execution_time"] * 1000)
            span.set_attribute("output_lines", len(result["logs"]))

            if not result["success"]:
                span.record_exception(Exception(result["error"]))
                span.set_status(trace.Status(trace.StatusCode.ERROR, result["error"]))

            return result
```

### Metrics

```python
from prometheus_client import Counter, Histogram
from tta_dev_primitives.observability import PrimitiveMetrics

class MetricizedCodeExecution:
    """E2B execution with Prometheus metrics."""

    def __init__(self):
        self.executor = CodeExecutionPrimitive()

        # Define metrics
        self.execution_counter = Counter(
            'e2b_executions_total',
            'Total E2B code executions',
            ['status', 'has_error']
        )

        self.execution_duration = Histogram(
            'e2b_execution_duration_seconds',
            'E2B execution duration',
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
        )

    async def execute_with_metrics(self, data: dict, context) -> dict:
        """Execute with metric collection."""
        with self.execution_duration.time():
            result = await self.executor.execute(data, context)

        # Record metrics
        self.execution_counter.labels(
            status='success' if result["success"] else 'error',
            has_error=str(bool(result.get("error")))
        ).inc()

        return result
```

## Troubleshooting

### Common Issues

#### 1. API Key Not Found
```python
# Error: E2B API key not found
# Solution: Set environment variable
export E2B_API_KEY="your_api_key_here"

# Or pass explicitly
executor = CodeExecutionPrimitive(api_key="your_api_key_here")
```

#### 2. Timeout Errors
```python
# Error: Code execution timed out
# Solution: Increase timeout or optimize code
result = await executor.execute({
    "code": slow_code,
    "timeout": 120  # Increase timeout
}, context)
```

#### 3. Package Installation Failures
```python
# Error: Package installation failed
# Solution: Use install parameter or pre-install
result = await executor.execute({
    "code": "import pandas as pd",
    "install": ["pandas"]  # Auto-install
}, context)
```

#### 4. Memory Limitations
```python
# Error: Sandbox ran out of memory
# Solution: Optimize code or use streaming
code = """
# Instead of loading all data at once
# data = pd.read_csv('huge_file.csv')

# Use chunks
for chunk in pd.read_csv('huge_file.csv', chunksize=1000):
    process_chunk(chunk)
"""
```

### Debugging Tips

```python
async def debug_execution(code: str, context) -> dict:
    """Debug code execution issues."""
    executor = CodeExecutionPrimitive()

    # Add debug prints
    debug_code = f"""
import sys
import os
print(f"Python version: {{sys.version}}")
print(f"Working directory: {{os.getcwd()}}")
print(f"Python path: {{sys.path}}")
print("=" * 50)

{code}

print("=" * 50)
print("Debug info printed above")
    """

    result = await executor.execute({"code": debug_code}, context)

    print(f"Sandbox ID: {result.get('sandbox_id')}")
    print(f"Execution time: {result.get('execution_time')}s")
    print(f"Success: {result.get('success')}")

    if result.get("logs"):
        print("Logs:")
        for i, log in enumerate(result["logs"]):
            print(f"  {i+1}: {log}")

    if result.get("error"):
        print(f"Error: {result['error']}")

    return result
```

## Performance Optimization

### 1. Batch Operations

```python
async def batch_execute(code_list: list, context) -> list:
    """Execute multiple code snippets efficiently."""
    executor = CodeExecutionPrimitive()

    # Execute in parallel with limits
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

    async def execute_one(code):
        async with semaphore:
            return await executor.execute({"code": code}, context)

    results = await asyncio.gather(*[
        execute_one(code) for code in code_list
    ])

    return results
```

### 2. Code Optimization

```python
# ❌ Inefficient: Multiple API calls
for item in items:
    result = await executor.execute({
        "code": f"process_item({item})"
    }, context)

# ✅ Efficient: Single batch call
batch_code = f"""
items = {items}
results = []
for item in items:
    results.append(process_item(item))
print(f"Processed {{len(results)}} items")
"""
result = await executor.execute({"code": batch_code}, context)
```

### 3. Result Caching

```python
from tta_dev_primitives.performance import CachePrimitive
import hashlib

def code_cache_key(data: dict, context) -> str:
    """Generate cache key for code execution."""
    code_hash = hashlib.md5(data["code"].encode()).hexdigest()
    timeout = data.get("timeout", 30)
    return f"e2b:{code_hash}:{timeout}"

cached_executor = CachePrimitive(
    primitive=CodeExecutionPrimitive(),
    ttl_seconds=3600,  # Cache for 1 hour
    key_fn=code_cache_key
)
```

## Examples

### Complete Working Examples

See the `examples/` directory for complete implementations:

- [`examples/benchmark_demo.py`](../examples/benchmark_demo.py) - Framework comparison demo
- [`examples/e2b_iterative_refinement.py`](../examples/e2b_iterative_refinement.py) - Code generation workflow
- [`examples/e2b_validation_pipeline.py`](../examples/e2b_validation_pipeline.py) - Code validation workflow

### Running the Examples

```bash
# Set your E2B API key
export E2B_API_KEY="your_key_here"

# Run benchmark demonstration
python examples/benchmark_demo.py

# Run iterative code generation
python examples/e2b_iterative_refinement.py

# Run validation pipeline
python examples/e2b_validation_pipeline.py
```

## Next Steps

1. **Get E2B API Key**: Sign up at [e2b.dev](https://e2b.dev)
2. **Try Examples**: Run the provided examples to see E2B in action
3. **Build Workflows**: Compose `CodeExecutionPrimitive` with other primitives
4. **Add Observability**: Use tracing and metrics for production monitoring
5. **Contribute**: Share your E2B + TTA.dev patterns with the community

## Related Documentation

- [TTA.dev Primitives Catalog](../PRIMITIVES_CATALOG.md) - All available primitives
- [Benchmarking Framework Guide](./benchmarking_framework_guide.md) - Using the benchmarking suite
- [E2B Official Documentation](https://e2b.dev/docs) - E2B platform details
- [Integration Patterns](../docs/guides/integration_patterns.md) - General integration guidance

---

**Last Updated:** November 3, 2025
**E2B SDK Version:** Compatible with e2b-code-interpreter ^0.0.8
**TTA.dev Version:** 0.1.0+


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Guides/E2b_integration_guide]]
