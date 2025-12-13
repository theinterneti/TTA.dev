# E2B Integration for TTA.dev

Secure Python code execution in cloud-based sandboxes, seamlessly integrated with TTA.dev primitives.

## 📚 Documentation Index

### Getting Started
- **Quick Start** - ⬇️ Below (basic usage)
- **[E2B Quick Wins](../../E2B_QUICK_WINS_SUMMARY.md)** - 5-minute impact overview
- **[Phase 1 Complete](../../E2B_PHASE1_COMPLETE.md)** - Implementation summary

### Core Pattern (CRITICAL!)
- **[Iterative Refinement Pattern](../../E2B_ITERATIVE_REFINEMENT_PATTERN.md)** - The most important E2B pattern
- **[Iterative Refinement Complete](../../E2B_ITERATIVE_REFINEMENT_COMPLETE.md)** - Implementation summary
- **Example:** `examples/e2b_iterative_code_refinement.py`

### Advanced Features (NEW!)
- **[Advanced Features Expansion](../../E2B_ADVANCED_FEATURES_EXPANSION.md)** - Templates & Webhooks guide
- **[Advanced Quick Start](../../E2B_ADVANCED_QUICK_START.md)** - Step-by-step setup
- **[Expansion Complete](../../E2B_EXPANSION_COMPLETE.md)** - Implementation summary
- **Example:** `examples/e2b_advanced_iterative_refinement.py`

### Integration Opportunities
- **[Integration Opportunities](../../E2B_INTEGRATION_OPPORTUNITIES.md)** - 6 ways to use E2B

### Production Ready
- **ML Template:** `examples/e2b.Dockerfile.ml-template`
- **Webhook Server:** `examples/e2b_webhook_monitoring_server.py`
- **Production Examples:** `examples/e2b_*.py`

---

## Quick Start

```bash
# Install
cd packages/tta-dev-primitives
uv add e2b-code-interpreter

# Set API key
export E2B_API_KEY=your_key_here

# Run
python examples/e2b_code_execution_workflow.py
```

## Basic Usage

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives import WorkflowContext

# Create primitive
executor = CodeExecutionPrimitive()

# Execute code
context = WorkflowContext(trace_id="demo-001")
result = await executor.execute(
    {"code": "print(21 + 21)"},
    context
)

# Results
print(result["logs"])  # ['[stdout] 42']
print(result["success"])  # True
print(result["execution_time"])  # 0.123
```

## Integration Patterns

### 1. Code Generation + Validation

AI generates code → E2B validates it works → Provide feedback

```python
workflow = (
    CodeGeneratorPrimitive() >>
    RetryPrimitive(
        CodeExecutionPrimitive(),
        strategy=RetryStrategy(max_retries=2)
    ) >>
    CodeValidatorPrimitive()
)
```

**Use Cases:**
- AI coding assistants
- Test generation workflows
- Documentation code snippets

### 🔄 Iterative Code Refinement (RECOMMENDED!)

**The most important E2B pattern:** Generate → Execute → Fix → Repeat

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

class IterativeCodeGenerator:
    """Keep generating code until it works!"""

    def __init__(self):
        self.executor = CodeExecutionPrimitive()

    async def generate_working_code(self, requirement, context, max_attempts=3):
        """Generate code iteratively until it executes successfully."""
        previous_errors = None

        for attempt in range(1, max_attempts + 1):
            # Generate code (learning from previous errors)
            code = await llm.generate(requirement, previous_errors)

            # Execute in E2B
            result = await self.executor.execute(
                {"code": code, "timeout": 30},
                context
            )

            # Success? Return it!
            if result["success"]:
                return {"code": code, "output": result["logs"]}

            # Failed? Feed error back to LLM
            previous_errors = result["error"]

        raise Exception("Failed after max attempts")
```

**Why this is critical:**
- AI-generated code fails ~30-50% of the time on first attempt
- Syntax errors, import errors, logic bugs are common
- E2B catches these BEFORE they reach production
- FREE tier makes validation cost $0
- Typically takes 1-3 iterations to get working code

**Full example:** `examples/e2b_iterative_code_refinement.py`

**Use Cases:**

### 2. Multi-Agent Collaboration

One agent writes code → Another agent executes and analyzes

```python
workflow = AgentCoderPrimitive() >> AgentExecutorPrimitive()
```

**Use Cases:**
- Pair programming agents
- Code review automation
- Collaborative development

### 3. Data Processing Pipeline

Fetch data → Generate processing code → Execute in isolation

```python
pipeline = DataFetcherPrimitive() >> DataProcessorPrimitive()
```

**Use Cases:**
- ETL workflows
- Data transformation
- Complex calculations

### 4. Agent Tooling

Provide agents with computational capabilities

```python
class ToolCallingAgent(InstrumentedPrimitive):
    def __init__(self):
        self.code_executor = CodeExecutionPrimitive()

    async def _execute_impl(self, input_data, context):
        if needs_computation(input_data["query"]):
            return await self.code_executor.execute(...)
```

**Use Cases:**
- Math/scientific computations
- Data analysis
- Algorithm testing

## Features

✅ **Secure Isolation** - Cloud sandboxes (E2B infrastructure)
✅ **Session Management** - Auto-rotation before 1-hour limit
✅ **Context Manager** - `async with` support
✅ **Observability** - Full OpenTelemetry integration
✅ **Error Handling** - Comprehensive error capture
✅ **Environment Variables** - Custom env var support
✅ **Timeout Control** - Per-execution timeouts
✅ **FREE Tier** - $0/month for 20 concurrent sandboxes

## API Reference

### CodeExecutionPrimitive

```python
class CodeExecutionPrimitive(InstrumentedPrimitive[CodeInput, CodeOutput]):
    def __init__(
        self,
        default_timeout: int = 30,
        session_max_age: int = 3300  # 55 minutes
    )
```

**Input (CodeInput):**
```python
{
    "code": str,                    # Required: Python code to execute
    "timeout": int,                 # Optional: Timeout in seconds (default: 30)
    "env_vars": dict[str, str],     # Optional: Environment variables
}
```

**Output (CodeOutput):**
```python
{
    "output": str,                  # Output text (if any)
    "error": str | None,            # Error message (if failed)
    "execution_time": float,        # Execution duration in seconds
    "success": bool,                # True if executed successfully
    "logs": list[str],              # stdout/stderr logs
    "sandbox_id": str,              # E2B sandbox identifier
}
```

### Context Manager

```python
async with CodeExecutionPrimitive() as executor:
    result1 = await executor.execute({"code": "x = 1"}, context)
    result2 = await executor.execute({"code": "print(x + 1)"}, context)
    # Sandbox automatically cleaned up
```

## Cost & Limits

### FREE Hobby Tier

- **Cost:** $0/month
- **Concurrent sandboxes:** 20
- **Session duration:** 1 hour max
- **Resources per sandbox:**
  - 8 vCPUs
  - 8GB RAM
  - 10GB disk

**Perfect for:**
- Development
- Testing
- Small-scale production
- Personal projects

### Pro Tier (Pay-as-you-go)

- **24-hour sessions**
- **Higher concurrency**
- **Priority support**

## Examples

### Fibonacci Calculation

```python
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""

result = await executor.execute({"code": code}, context)
# Output: ['[stdout] Fibonacci(10) = 55']
```

### Data Processing

```python
code = """
import json

data = {"users": [{"id": 1, "name": "Alice"}]}
processed = json.dumps(data, indent=2)
print(processed)
"""

result = await executor.execute({"code": code}, context)
# success: True, logs contain formatted JSON
```

### With Environment Variables

```python
result = await executor.execute(
    {
        "code": "import os; print(os.environ['API_KEY'])",
        "env_vars": {"API_KEY": "secret123"}
    },
    context
)
```

## Testing

### Integration Tests

```bash
# Requires E2B_API_KEY
E2B_API_KEY=your_key uv run pytest \
    packages/tta-dev-primitives/tests/integrations/test_e2b_integration.py -v
```

**Test Coverage:**
- Basic code execution
- Fibonacci calculation
- Context manager usage
- Library imports (json, math)
- Error handling

### Unit Tests

```bash
# Uses mocks
uv run pytest \
    packages/tta-dev-primitives/tests/integrations/test_e2b_primitive.py -v
```

## Architecture

### E2B API (SDK 2.3.0)

```python
from e2b_code_interpreter import AsyncSandbox

# Create sandbox
sandbox = await AsyncSandbox.create(timeout=3600)

# Execute code
execution = await sandbox.run_code(code)

# Get results
output = execution.text  # Can be None
logs = execution.logs.stdout  # List of strings
errors = execution.error  # Error info if any

# Cleanup
await sandbox.kill()
```

### TTA.dev Integration

CodeExecutionPrimitive extends `InstrumentedPrimitive` for:
- Automatic OpenTelemetry tracing
- Prometheus metrics
- Structured logging
- Context propagation

### Session Management

- **Default rotation:** 55 minutes (before 1-hour limit)
- **Automatic cleanup:** Old sandbox killed, new created
- **Seamless to caller:** Transparent rotation

## Troubleshooting

### API Key Not Set

```bash
export E2B_API_KEY=your_key_here
```

Get your key from: https://e2b.dev/

### Negative Execution Time

Fixed in v1.0. Timer now starts immediately before `run_code()`.

### Import Errors

Make sure SDK is installed:
```bash
cd packages/tta-dev-primitives
uv add e2b-code-interpreter
```

### Sandbox Timeout

Increase timeout:
```python
executor = CodeExecutionPrimitive(default_timeout=120)
```

## Documentation

- **Phase 1 Summary:** `E2B_PHASE1_COMPLETE.md`
- **Research:** `docs/integrations/E2B_INTEGRATION_RESEARCH.md`
- **Integration Tests:** `tests/integrations/test_e2b_integration.py`
- **Examples:** `examples/e2b_code_execution_workflow.py`

## Links

- **E2B Documentation:** https://e2b.dev/docs
- **GitHub:** https://github.com/e2b-dev/code-interpreter
- **API Reference:** https://e2b.dev/docs/api-reference
- **TTA.dev:** https://github.com/theinterneti/TTA.dev

---

**Last Updated:** November 6, 2025
**Status:** Production-Ready ✅
**Cost:** $0/month (FREE tier)


---
**Logseq:** [[TTA.dev/Platform/Primitives/Docs/Integrations/E2b_readme]]
