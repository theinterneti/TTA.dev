# Communication Style

# Communication Style

## When Asked Questions

- Provide clear, actionable answers
- Include code examples using the primitives
- Reference existing examples in `packages/tta-dev-primitives/examples/`
- Point to relevant documentation in package READMEs
- Show before/after when suggesting improvements

## When Making Suggestions

- Always consider testability (can this be tested with `MockPrimitive`?)
- Consider performance (can this benefit from `ParallelPrimitive`?)
- Consider reliability (should this have retry/timeout/fallback?)
- Think about observability (is context being passed correctly?)
- Explain the "why" behind architectural recommendations

## When Refactoring

- Look for opportunities to use primitives
- Identify manual async patterns that could be `Sequential` or `Parallel`
- Find places where retry/timeout/cache would improve reliability
- Ensure `WorkflowContext` is used for state passing
- Show concrete before/after examples

## Response Format

### For Code Changes
- Never print code blocks with "TODO" or placeholder comments
- Use edit tools instead of showing full file dumps
- Reference specific line numbers when discussing existing code
- Show minimal diffs for clarity

### For Explanations
- Use markdown formatting (bold for emphasis, code blocks for examples)
- Break complex topics into numbered steps
- Include links to relevant documentation
- Use tables for comparison when helpful

### For Errors
- Identify the root cause first
- Explain why the error occurs
- Provide specific fix (not "fix the error")
- Show how to prevent similar errors in future

## Anti-Pattern Recognition

When you see these patterns, call them out and suggest refactoring:
- ❌ Manual async orchestration without primitives
- ❌ Try/except with retry logic → use `RetryPrimitive`
- ❌ asyncio.wait_for() for timeouts → use `TimeoutPrimitive`
- ❌ Manual caching dictionaries → use `CachePrimitive`
- ❌ Global variables for state → use `WorkflowContext`
- ❌ Using `pip` → use `uv`
- ❌ Old type hints (`Optional[T]`) → use `T | None`

## Tone & Style

- **Professional but friendly**: Explain concepts clearly without being condescending
- **Concise**: Respect the user's time - get to the point quickly
- **Specific**: Use actual file names, line numbers, class names
- **Helpful**: Anticipate follow-up questions and address them proactively
- **Honest**: If you don't know something, say so and suggest alternatives


# Priority Order

# Priority Order

## Decision-Making Framework

When making decisions, prioritize in this order:

1. **Correctness**: Code must work and be tested
   - Every public API has tests
   - Edge cases are handled
   - Error messages are helpful

2. **Type Safety**: Full type annotations required
   - Use Python 3.11+ style (`str | None`, not `Optional[str]`)
   - Generic types for primitives: `WorkflowPrimitive[InputType, OutputType]`
   - Pydantic v2 models for data structures

3. **Composability**: Use primitives for reusable patterns
   - Compose with `>>` (Sequential) and `|` (Parallel)
   - Extend `WorkflowPrimitive` for new components
   - Keep primitives focused and single-purpose

4. **Testability**: Easy to test with mocks
   - Use `MockPrimitive` from `testing/` module
   - Async tests with `@pytest.mark.asyncio`
   - Test success, failure, and edge cases

5. **Performance**: Parallel where appropriate
   - Use `ParallelPrimitive` for independent operations
   - Add `CachePrimitive` to avoid redundant work
   - Profile before optimizing

6. **Reliability**: Retry, timeout, fallback where needed
   - `RetryPrimitive` for transient failures
   - `TimeoutPrimitive` to prevent hangs
   - `FallbackPrimitive` for graceful degradation

7. **Observability**: Context passing for tracing
   - Always accept `WorkflowContext` parameter
   - Use `context.metadata` for correlation IDs
   - Use `context.state` for passing data between steps

## Development Workflow Priorities

### Before Writing Code
1. Check if existing primitives solve the problem
2. Review examples in `packages/tta-dev-primitives/examples/`
3. Read relevant path-specific instructions
4. Plan composition strategy (Sequential? Parallel? Both?)

### While Writing Code
1. Write type annotations first
2. Write docstring with example
3. Implement logic
4. Add tests
5. Run quality checks (`ruff format`, `ruff check`, `pyright`)

### Before Committing
1. Run tests: `uv run pytest -v`
2. Check coverage: `uv run pytest --cov=packages`
3. Format code: `uv run ruff format .`
4. Lint code: `uv run ruff check . --fix`
5. Type check: `uvx pyright packages/`

## Code Review Priorities

When reviewing code (or suggestions), check in this order:

1. **Does it work?** - Tests pass, logic is correct
2. **Is it typed?** - Full annotations, no `Any` without reason
3. **Is it tested?** - Coverage for new code, edge cases handled
4. **Does it use primitives?** - Composition over manual orchestration
5. **Is it documented?** - Docstrings with examples
6. **Is it maintainable?** - Clear naming, no magic numbers
7. **Is it performant?** - Parallel where possible, cached if repeated

## Package Management

**Always use `uv`, never `pip` directly:**
- Install dependencies: `uv sync --all-extras`
- Run commands: `uv run <command>`
- Run tests: `uv run pytest -v`
- Install package locally: `uv pip install -e packages/tta-dev-primitives`

## When in Doubt

1. Check existing examples: `packages/tta-dev-primitives/examples/`
2. Read package README: `packages/tta-dev-primitives/README.md`
3. Look at test patterns: `packages/tta-dev-primitives/tests/`
4. Ask the user for clarification


# Anti-Patterns to Avoid

# Anti-Patterns to Avoid

## Code Anti-Patterns

### Using pip Instead of uv
❌ **BAD**:
```bash
pip install -e packages/tta-dev-primitives
python -m pytest
```

✅ **GOOD**:
```bash
uv sync --all-extras
uv run pytest -v
```

### Creating Primitives Without Type Hints
❌ **BAD**:
```python
class MyPrimitive(WorkflowPrimitive):
    async def execute(self, input_data, context):
        return process(input_data)
```

✅ **GOOD**:
```python
class MyPrimitive(WorkflowPrimitive[dict, str]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> str:
        return process(input_data)
```

### Skipping Tests
❌ **BAD**:
```python
# TODO: Add tests later
class NewFeature(WorkflowPrimitive[dict, dict]):
    ...
```

✅ **GOOD**:
```python
class NewFeature(WorkflowPrimitive[dict, dict]):
    """Feature with comprehensive tests."""
    ...

# In tests/test_new_feature.py
@pytest.mark.asyncio
async def test_new_feature():
    mock = MockPrimitive("feature", return_value={"status": "ok"})
    ...
```

### Using Global State Instead of WorkflowContext
❌ **BAD**:
```python
GLOBAL_COUNTER = 0
USER_SESSIONS = {}

async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    global GLOBAL_COUNTER
    GLOBAL_COUNTER += 1
    return {"count": GLOBAL_COUNTER}
```

✅ **GOOD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    count = context.state.get("counter", 0) + 1
    context.state["counter"] = count
    return {"count": count}
```

### Using Optional[T] Instead of T | None
❌ **BAD**:
```python
from typing import Optional, Dict, List

def process(data: Optional[Dict[str, List[str]]]) -> Optional[str]:
    ...
```

✅ **GOOD**:
```python
def process(data: dict[str, list[str]] | None) -> str | None:
    ...
```

### Manual Async Orchestration
❌ **BAD**:
```python
async def process_all():
    result1 = await step1()
    result2 = await step2(result1)
    result3 = await step3(result2)
    return result3
```

✅ **GOOD**:
```python
from tta_dev_primitives import SequentialPrimitive

workflow = step1 >> step2 >> step3
result = await workflow.execute(input_data, context)
```

### Manual Retry Logic
❌ **BAD**:
```python
async def call_api():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await api_call()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

✅ **GOOD**:
```python
from tta_dev_primitives import RetryPrimitive, LambdaPrimitive

api_primitive = LambdaPrimitive(api_call)
retry_api = RetryPrimitive(api_primitive, max_retries=3, backoff_factor=2.0)
result = await retry_api.execute(input_data, context)
```

### Manual Timeout Handling
❌ **BAD**:
```python
async def slow_operation():
    try:
        return await asyncio.wait_for(operation(), timeout=5.0)
    except asyncio.TimeoutError:
        return {"error": "timeout"}
```

✅ **GOOD**:
```python
from tta_dev_primitives import TimeoutPrimitive, LambdaPrimitive

op_primitive = LambdaPrimitive(operation)
timeout_op = TimeoutPrimitive(op_primitive, timeout=5.0)
result = await timeout_op.execute(input_data, context)
```

### Manual Caching
❌ **BAD**:
```python
CACHE = {}

async def get_data(key: str):
    if key in CACHE:
        return CACHE[key]
    result = await expensive_operation(key)
    CACHE[key] = result
    return result
```

✅ **GOOD**:
```python
from tta_dev_primitives import CachePrimitive, LambdaPrimitive

op_primitive = LambdaPrimitive(expensive_operation)
cached_op = CachePrimitive(op_primitive, ttl=3600)
result = await cached_op.execute(key, context)
```

## Workflow Anti-Patterns

### Not Using Parallel for Independent Operations
❌ **BAD**:
```python
result1 = await operation1()
result2 = await operation2()  # Could run in parallel!
result3 = await operation3()  # Could run in parallel!
return [result1, result2, result3]
```

✅ **GOOD**:
```python
workflow = op1 | op2 | op3  # All run in parallel
results = await workflow.execute(input_data, context)
```

### Not Passing Context Through Workflows
❌ **BAD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    # Losing context!
    result = await some_operation(input_data)
    return result
```

✅ **GOOD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    # Pass context through
    result = await child_primitive.execute(input_data, context)
    return result
```

## Documentation Anti-Patterns

### Missing Docstrings
❌ **BAD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    return process(input_data)
```

✅ **GOOD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input with validation.
    
    Args:
        input_data: Data to process
        context: Workflow context
        
    Returns:
        Processed result
        
    Example:
        ```python
        result = await processor.execute({"key": "value"}, context)
        ```
    """
    return process(input_data)
```

### Docstrings Without Examples
❌ **BAD**:
```python
"""Process data and return result."""
```

✅ **GOOD**:
```python
"""
Process data and return result.

Example:
    ```python
    processor = DataProcessor()
    context = WorkflowContext(workflow_id="demo")
    result = await processor.execute({"query": "test"}, context)
    ```
"""
```

## Testing Anti-Patterns

### Not Using MockPrimitive
❌ **BAD**:
```python
@pytest.mark.asyncio
async def test_workflow():
    # Using real implementations in tests
    workflow = RealStep1() >> RealStep2()
    result = await workflow.execute(data, context)
    assert result == expected
```

✅ **GOOD**:
```python
@pytest.mark.asyncio
async def test_workflow():
    # Using mocks for fast, isolated tests
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2
    result = await workflow.execute(data, context)
    assert mock1.call_count == 1
    assert result == "result2"
```

### Not Testing Failures
❌ **BAD**:
```python
@pytest.mark.asyncio
async def test_success():
    # Only testing happy path
    result = await primitive.execute(valid_data, context)
    assert result == expected
```

✅ **GOOD**:
```python
@pytest.mark.asyncio
async def test_success():
    result = await primitive.execute(valid_data, context)
    assert result == expected

@pytest.mark.asyncio
async def test_invalid_input():
    with pytest.raises(ValidationError, match="Missing required field"):
        await primitive.execute(invalid_data, context)

@pytest.mark.asyncio
async def test_timeout():
    slow_mock = MockPrimitive("slow", side_effect=asyncio.TimeoutError())
    with pytest.raises(asyncio.TimeoutError):
        await slow_mock.execute(data, context)
```

## Development Workflow Anti-Patterns

### Modifying Code Without Running Quality Checks
❌ **BAD**:
```bash
# Make changes, commit directly
git add .
git commit -m "fix stuff"
```

✅ **GOOD**:
```bash
# Make changes, run quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v
git add .
git commit -m "fix: specific description of fix"
```

### Committing Without Tests
❌ **BAD**:
```bash
# Add new feature
git add packages/tta-dev-primitives/src/core/new_feature.py
git commit -m "feat: add new feature"
```

✅ **GOOD**:
```bash
# Add new feature with tests
git add packages/tta-dev-primitives/src/core/new_feature.py
git add packages/tta-dev-primitives/tests/test_new_feature.py
uv run pytest -v
git commit -m "feat: add new feature with tests"
```

## Remember

**This is a production library** - avoid these patterns to maintain:
- ✅ Type safety
- ✅ Test coverage
- ✅ Composability
- ✅ Reliability
- ✅ Maintainability

---

# Quick Reference

## Key Documentation

- **Examples README**: [`examples/README.md`](examples/README.md) - All example workflows
- **Phase 3 Complete**: [`../../PHASE3_EXAMPLES_COMPLETE.md`](../../PHASE3_EXAMPLES_COMPLETE.md) - InstrumentedPrimitive pattern guide
- **Package README**: [`README.md`](README.md) - API documentation
- **Main AGENTS.md**: [`../../AGENTS.md`](../../AGENTS.md) - Repository-wide agent instructions
- **Primitives Catalog**: [`../../PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md) - Complete primitive reference

## Working Examples

All Phase 3 examples now use the **InstrumentedPrimitive pattern**:

1. **RAG Workflow** (`examples/rag_workflow.py`) - Basic retrieval-augmented generation
2. **Agentic RAG** (`examples/agentic_rag_workflow.py`) - Production RAG with grading
3. **Cost Tracking** (`examples/cost_tracking_workflow.py`) - Token/cost tracking
4. **Streaming** (`examples/streaming_workflow.py`) - Token-by-token streaming
5. **Multi-Agent** (`examples/multi_agent_workflow.py`) - Agent coordination

See [`PHASE3_EXAMPLES_COMPLETE.md`](../../PHASE3_EXAMPLES_COMPLETE.md) for implementation details.
