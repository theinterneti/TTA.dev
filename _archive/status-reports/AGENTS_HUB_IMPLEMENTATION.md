# TTA.dev AI Coding Agent Instructions

## Project Overview

TTA.dev is a **production-ready AI development toolkit** providing battle-tested workflow primitives for building reliable AI applications. This is a **monorepo with one core package** under `packages/`:

- **tta-dev-primitives**: Production-ready development primitives providing composable workflow patterns (Router, Cache, Timeout, Retry, Sequential, Parallel), recovery strategies (Fallback, Compensation), performance utilities, and observability tools

**Philosophy**: Only proven code with comprehensive testing, real production usage, and comprehensive documentation enters this repository.

## Architecture & Core Patterns

### Workflow Primitive Composition

The foundation is `WorkflowPrimitive[T, U]` - all workflows implement `async execute(input_data: T, context: WorkflowContext) -> U`. Compose using operators:

```python
# Sequential (>>): Output of each becomes input to next
workflow = step1 >> step2 >> step3

# Parallel (|): All receive same input, returns list of outputs
workflow = branch1 | branch2 | branch3

# Mixed composition
workflow = input_processor >> (fast_path | slow_path) >> aggregator
```

**Key insight**: Every primitive receives `WorkflowContext` containing `workflow_id`, `session_id`, `player_id`, `metadata`, and `state` - use this for tracing and state passing, NOT global variables.

### Package Structure Convention

Both packages follow identical structure:
```
packages/<package-name>/
├── src/<package_name>/
│   ├── core/          # Base abstractions (base.py, sequential.py, parallel.py, etc.)
│   ├── recovery/      # Retry, fallback, timeout, compensation
│   ├── performance/   # Cache, optimization
│   ├── observability/ # Logging, metrics, tracing
│   ├── apm/          # Agent Package Manager integration (optional)
│   └── testing/       # Test utilities (MockPrimitive, fixtures)
├── tests/             # Mirror src/ structure
├── pyproject.toml     # Uses hatchling, pytest, ruff, mypy
└── README.md
```

## Development Workflows

### Package Management: uv (NOT pip)

**Always use `uv` commands, never pip directly**:
```bash
cd packages/tta-dev-primitives
uv sync --all-extras              # Install dependencies
uv run pytest -v                  # Run tests
uv run ruff format .              # Format
uv run ruff check . --fix         # Lint
uvx pyright .                     # Type check
```

### Testing Requirements (CRITICAL)

**Comprehensive test coverage is required** (currently 52% overall: Core 88%, Performance 100%, Recovery 67%). Test structure:
- Use `pytest-asyncio` with `@pytest.mark.asyncio` for async tests
- Use `MockPrimitive` from `testing/` for workflow testing
- Test files mirror source structure: `src/core/cache.py` → `tests/test_cache.py`
- Coverage command: `uv run pytest --cov=packages --cov-report=html`

Example test pattern:
```python
from tta_workflow_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_sequential_workflow():
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert mock1.call_count == 1
    assert result == "result2"
```

### Quality Gates

Before any commit/PR, run:
```bash
# Use VS Code tasks (Cmd/Ctrl+Shift+P → "Task: Run Task")
# OR manually:
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v
```

**Package validation script**: `./scripts/validate-package.sh <package-name>` runs all checks.

## Code Style & Conventions

### Type Hints (Strictly Enforced)

- Use Pydantic v2 models for all data structures
- Full type annotations required (`[tool.ruff.lint] select = ["ANN"]`)
- Generic types for primitives: `class MyPrimitive(WorkflowPrimitive[InputType, OutputType])`
- Python 3.11+ features encouraged (use `str | None`, not `Optional[str]`)

### Docstrings (Google Style)

```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input with intelligent caching.

    Args:
        input_data: Request data with 'query' key
        context: Workflow context with session info

    Returns:
        Processed result with 'response' key

    Raises:
        ValueError: If input_data missing required keys

    Example:
```python
        cache = CachePrimitive(ttl=3600)
        result = await cache.execute({"query": "..."}, context)
        ```
"""
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `SequentialPrimitive`, `WorkflowContext`)
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`
- **Primitives**: Always suffix with `Primitive` (e.g., `CachePrimitive`, `RouterPrimitive`)

### Error Handling

- Use specific exceptions, not generic `Exception`
- Always include context in error messages: `f"Failed to execute {self.__class__.__name__}: {error}"`
- Structured logging with correlation IDs from `WorkflowContext`

## Project-Specific Knowledge

### APM (Agent Package Manager) Integration

Optional OpenTelemetry integration via `apm/` directories:
- `apm.yml` files define package metadata for MCP compatibility
- Tracing via `@trace_workflow` decorator
- Install with `[tracing]` or `[apm]` extras
- Gracefully degrades if dependencies missing (see `__init__.py` ImportError handling)

### Package Structure

**NOTE**: The repository previously had two packages (`tta-workflow-primitives` and `dev-primitives`) which were **consolidated into `tta-dev-primitives`** on 2025-10-28. All workflow primitives are now in the single `tta-dev-primitives` package.

### Legacy Code (DO NOT USE)

The `archive/legacy-tta-game/` directory contains old game code. It's kept for historical reference but is NOT part of the current project. Focus on `packages/` only.

### Documentation Strategy

- Package READMEs are the primary documentation
- Architecture docs in `docs/architecture/`
- Development guides in `docs/development/`
- MCP-specific docs in `docs/mcp/`
- Update READMEs when adding features (include code examples)

## Common Tasks

### Adding a New Primitive

1. Create in appropriate subpackage: `src/<package>/core/my_primitive.py`
2. Extend `WorkflowPrimitive[T, U]` with typed generics
3. Implement `async execute(input_data: T, context: WorkflowContext) -> U`
4. Add comprehensive docstring with example
5. Export in `__init__.py`
6. Create `tests/test_my_primitive.py` with 100% coverage
7. Update package README with usage example

### Running Tests

```bash
# All tests
cd packages/tta-dev-primitives && uv run pytest -v

# With coverage
cd packages/tta-dev-primitives && uv run pytest --cov=src --cov-report=html

# Specific test module
cd packages/tta-dev-primitives && uv run pytest tests/test_cache.py -v

# Use VS Code task: "🧪 Run All Tests"
```

### Creating a PR

1. Run quality checks: `uv run pytest -v && uv run ruff format . && uvx pyright packages/`
2. Update `CHANGELOG.md` (if exists)
3. Follow PR template in `.github/PULL_REQUEST_TEMPLATE.md`
4. Ensure 100% test coverage for new code
5. Use Conventional Commits format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## Debugging Tips

- Use `WorkflowContext.metadata` for debugging state across primitives
- Enable structured logging: `from tta_workflow_primitives.observability import setup_logging; setup_logging("DEBUG")`
- Check test output for primitive call counts: `assert mock.call_count == expected`
- For async issues, ensure `@pytest.mark.asyncio` decorator present

## Anti-Patterns to Avoid

❌ Using `pip` instead of `uv`
❌ Creating primitives without type hints
❌ Skipping tests ("will add later")
❌ Global state instead of `WorkflowContext`
❌ Modifying code without running quality checks
❌ Using `Optional[T]` instead of `T | None` (this is Python 3.11+)

## Quick Reference

**Run quality checks**: `cd packages/tta-dev-primitives && uv run pytest -v && uv run ruff check . && uvx pyright .`
**Install package locally**: `uv pip install -e packages/tta-dev-primitives`
**View tasks**: VS Code → Cmd/Ctrl+Shift+P → "Task: Run Task"

**Remember**: This is a production library - every line must be tested, typed, and documented.

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

## Configuration Management

All agent configurations are generated from the universal instruction system located in `.universal-instructions/`.

**To regenerate all tool-specific configurations:**
```bash
./scripts/generate-configs.sh
```

This ensures consistency across all AI coding assistants.

## Source of Truth

The `.universal-instructions/` directory contains:
- `core/` - Project overview, architecture, development workflow, quality standards
- `path-specific/` - Instructions for different file types (packages, tests, scripts, docs)
- `agent-behavior/` - Communication, priorities, anti-patterns (source for this AGENTS.md)
- `mappings/` - Tool-specific configuration mappings

**All changes should be made to `.universal-instructions/` and regenerated**, not edited directly in tool-specific files or this AGENTS.md.


---
**Logseq:** [[TTA.dev/_archive/Status-reports/Agents_hub_implementation]]
