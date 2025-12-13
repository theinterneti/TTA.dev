# Universal AI Assistant Instructions

This directory contains **tool-agnostic instruction sources** that can be transformed into assistant-specific configuration files.

## Philosophy

**One Source of Truth** → **Multiple Tool Configurations**

Instead of maintaining separate instruction files for GitHub Copilot, Cline, Augment, Cursor, etc., we maintain a single universal format and generate tool-specific files on demand.

## Structure

```
.universal-instructions/
├── core/                        # Core instruction modules (combined → repository-wide)
│   ├── project-overview.md      # What this project is
│   ├── architecture.md          # How it's structured
│   ├── development-workflow.md  # How to develop
│   └── quality-standards.md     # Quality requirements
├── path-specific/               # Path-specific rules (one per file type)
│   ├── package-source.instructions.md   # For packages/**/src/**/*.py
│   ├── tests.instructions.md            # For **/tests/**/*.py
│   ├── scripts.instructions.md          # For scripts/**/*.py
│   └── documentation.instructions.md    # For **/*.md
├── agent-behavior/              # AI agent behavioral guidelines (combined → agent file)
│   ├── communication.md         # How to communicate
│   ├── priorities.md            # Decision-making priorities
│   └── anti-patterns.md         # What to avoid
└── mappings/                    # Tool-specific output configurations
    ├── copilot.yaml             # GitHub Copilot config
    ├── cline.yaml               # Cline config
    ├── cursor.yaml              # Cursor config
    └── augment.yaml             # Augment config
```

## Usage

### Generate All Tool Configurations

```bash
uv run python scripts/generate_assistant_configs.py --tool all
```

### Generate Specific Tool Configuration

```bash
# GitHub Copilot
uv run python scripts/generate_assistant_configs.py --tool copilot

# Cline
uv run python scripts/generate_assistant_configs.py --tool cline

# Cursor
uv run python scripts/generate_assistant_configs.py --tool cursor

# Augment
uv run python scripts/generate_assistant_configs.py --tool augment
```

## How It Works

The generator uses **tta-dev-primitives** for orchestration:

1. **Reads universal sources** from `core/`, `path-specific/`, `agent-behavior/` using `ParallelPrimitive` (faster than sequential)
2. **Reads tool mapping** from `mappings/<tool>.yaml` using `ReadYAMLPrimitive`
3. **Generates tool-specific files** using composition of primitives:
   - Repository-wide instructions: `ReadFilePrimitive` (parallel) → `CombineCorePrimitive` → `WriteFilePrimitive`
   - Agent behavior: `ReadFilePrimitive` (parallel) → `CombineAgentBehaviorPrimitive` → `WriteFilePrimitive`
   - Path-specific: `ReadFilePrimitive` → `AddFrontmatterPrimitive` → `WriteFilePrimitive` (all in parallel)

**Key primitive usage:**
- **Parallel I/O**: All file reads happen concurrently for speed
- **Sequential composition**: Read → Process → Write (using `>>` operator)
- **WorkflowContext**: Tracing and correlation IDs throughout generation

### Example: Copilot Generation

For Copilot (`mappings/copilot.yaml`):
```yaml
name: copilot
output_dir: .github
repository_wide_file: copilot-instructions.md
agent_instructions_file: ../AGENTS.md
path_specific_dir: instructions
path_specific_extension: .instructions.md
frontmatter_format: yaml
```

Generates:
- `.github/copilot-instructions.md` (combined `core/*.md`)
- `AGENTS.md` (combined `agent-behavior/*.md`)
- `.github/instructions/*.instructions.md` (from `path-specific/*.instructions.md` with YAML frontmatter)

## Adding a New Tool

1. Create mapping file: `.universal-instructions/mappings/TOOLNAME.yaml`
   ```yaml
name: toolname
   output_dir: path/to/output
   repository_wide_file: instructions.md
   agent_instructions_file: ../AGENT.md
   path_specific_dir: rules
   path_specific_extension: .md
   frontmatter_format: yaml  # or 'none'
```
2. Add to choices in `scripts/generate_assistant_configs.py` argparser
3. Run generator: `uv run python scripts/generate_assistant_configs.py --tool toolname`

## AI Assistant Self-Configuration

AI assistants can self-configure by running the generator. Example prompts:

### For Copilot
```
Please generate your configuration by running:
uv run python scripts/generate_assistant_configs.py --tool copilot
```

### For All Tools
```
Please regenerate all AI assistant configurations:
uv run python scripts/generate_assistant_configs.py --tool all
```

## Benefits

✅ **Single Source of Truth** - Update once, deploy everywhere
✅ **Consistency** - All tools get same knowledge
✅ **Easy Updates** - Change universal source, regenerate all
✅ **Tool-Agnostic** - Easy to add new AI assistants
✅ **Version Controlled** - Universal sources tracked in git
✅ **Primitive-Powered** - Generation uses workflow primitives
✅ **Type-Safe** - Full Pydantic models and type annotations
✅ **Self-Configuring** - AI assistants can generate their own config
✅ **Parallel Processing** - Fast generation using concurrent I/O

## Technical Implementation

The generator script (`scripts/generate_assistant_configs.py`) uses `tta-dev-primitives` to demonstrate proper usage:

### Primitives Used
- **`WorkflowPrimitive[T, U]`**: Base class for all processors
- **Parallel composition (via `|` operator)**: Concurrent file reads
- **`ReadFilePrimitive`**: Custom primitive for file I/O
- **`WriteFilePrimitive`**: Custom primitive for writing files
- **`ReadYAMLPrimitive`**: Custom primitive for YAML parsing
- **`CombineCorePrimitive`**: Custom primitive for combining core docs
- **`AddFrontmatterPrimitive`**: Custom primitive for adding YAML frontmatter
- **`WorkflowContext`**: Context passing for tracing and correlation

### Composition Pattern
```python
# Parallel read → Sequential processing → Write
workflow = (file1 | file2 | file3) >> combiner >> writer
```

### Type Safety
All primitives are fully typed:
```python
class ReadFilePrimitive(WorkflowPrimitive[Path, str]):
    async def execute(self, input_data: Path, context: WorkflowContext) -> str:
        ...
```

This is a **working example** of how to use primitives for real-world orchestration tasks.
e(self, input_data: dict, context: WorkflowContext) -> dict:
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
# Quality Standards

## Type Hints (Strictly Enforced)

- Use Pydantic v2 models for all data structures
- Full type annotations required
- Generic types for primitives: `class MyPrimitive(WorkflowPrimitive[InputType, OutputType])`
- **Python 3.11+ style**: Use `str | None`, NOT `Optional[str]`

## Docstrings (Google Style)

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

## Naming Conventions

- **Classes**: `PascalCase` (e.g., `SequentialPrimitive`, `WorkflowContext`)
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`
- **Primitives**: Always suffix with `Primitive`

## Error Handling

- Use specific exceptions, not generic `Exception`
- Always include context in error messages
- Use structured logging with correlation IDs from `WorkflowContext`

Example:
```python
if not input_data.get("required_field"):
    raise ValidationError(
        f"Missing required_field in {self.__class__.__name__} "
        f"for workflow_id={context.workflow_id}"
    )
```

## Import Organization

```python
# Standard library
import asyncio
from typing import Any

# Third-party
from pydantic import BaseModel, Field

# Local package - absolute imports
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
```

## Anti-Patterns to Avoid

❌ Using `pip` instead of `uv`
❌ Creating primitives without type hints
❌ Skipping tests ("will add later")
❌ Global state instead of `WorkflowContext`
❌ Modifying code without running quality checks
❌ Using `Optional[T]` instead of `T | None`
# Package Source Code Guidelines

## Core Principles

1. **Use TTA Dev Primitives**: Always compose workflows using primitives
2. **Type Safety First**: Full type annotations required
3. **Test Coverage**: Every public API must have tests
4. **Documentation**: Google-style docstrings with examples

## Type Annotations

```python
# ✅ GOOD: Python 3.11+ style
def process(data: dict[str, Any]) -> str | None:
    ...

class MyPrimitive(WorkflowPrimitive[dict, str]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> str:
        ...

# ❌ BAD: Old style
from typing import Optional, Dict, Any

def process(data: Dict[str, Any]) -> Optional[str]:  # Don't use this
    ...
```

## Workflow Primitives

All workflows must extend `WorkflowPrimitive[T, U]` and implement `execute()`:

```python
from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext

class MyWorkflow(WorkflowPrimitive[InputType, OutputType]):
    async def execute(self, input_data: InputType, context: WorkflowContext) -> OutputType:
        """
        Brief description.

        Args:
            input_data: Description
            context: Workflow context for tracing

        Returns:
            Description

        Example:
```python
            workflow = MyWorkflow()
            context = WorkflowContext(workflow_id="demo")
            result = await workflow.execute(input_data, context)
            ```
"""
        # Implementation
        pass
```

## Composition Patterns

Use operators for composition:

```python
# Sequential
workflow = step1 >> step2 >> step3

# Parallel
workflow = branch1 | branch2 | branch3

# Mixed
workflow = input_step >> (parallel1 | parallel2) >> aggregator
```

## Context Management

**Never use global state**. Pass data through `WorkflowContext`:

```python
# ✅ GOOD: Use context
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    user_id = context.metadata.get("user_id")
    context.state["processed_count"] = context.state.get("processed_count", 0) + 1
    return result

# ❌ BAD: Global state
GLOBAL_COUNTER = 0  # Don't do this

async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    global GLOBAL_COUNTER  # Don't do this
    GLOBAL_COUNTER += 1
    ...
```

## Error Handling

Use specific exceptions with context:

```python
# ✅ GOOD
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    if not input_data.get("required_field"):
        raise ValidationError(
            f"Missing required_field in {self.__class__.__name__} "
            f"for workflow_id={context.workflow_id}"
        )

# ❌ BAD
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    if not input_data.get("required_field"):
        raise Exception("Missing field")  # Too generic, no context
```

## Naming Conventions

- Classes: `PascalCase` ending in `Primitive` for workflow components
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

## Documentation Requirements

Every public class and method needs Google-style docstrings:

```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input data with validation and transformation.

    This method validates the input structure, applies transformations,
    and returns the processed result.

    Args:
        input_data: Raw input containing 'query' and optional 'params'
        context: Workflow context with session tracking info

    Returns:
        Processed data with 'result' and 'metadata' keys

    Raises:
        ValidationError: If required fields are missing
        TimeoutError: If processing exceeds configured timeout

    Example:
```python
        processor = DataProcessor(timeout=5.0)
        context = WorkflowContext(workflow_id="process-123")
        result = await processor.execute(
            {"query": "test", "params": {}},
            context
        )
        ```
"""
    ...
```

## Import Organization

```python
# Standard library
import asyncio
from typing import Any

# Third-party
from pydantic import BaseModel, Field

# Local package - absolute imports
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive
```

## Pydantic Models

Use Pydantic v2 for all data structures:

```python
from pydantic import BaseModel, Field

class InputData(BaseModel):
    """Input structure for processing."""

    query: str = Field(..., description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Quality Checklist

Before committing, ensure:
- [ ] Full type annotations
- [ ] Google-style docstrings with examples
- [ ] Tests using `MockPrimitive`
- [ ] No global state
- [ ] Specific exceptions with context
- [ ] Uses primitives for composition
- [ ] Formatted with `uv run ruff format`
- [ ] Linted with `uv run ruff check --fix`
- [ ] Type-checked with `uvx pyright`
ntext) -> dict:
    """
    Process input data with validation and transformation.

    This method validates the input structure, applies transformations,
    and returns the processed result.

    Args:
        input_data: Raw input containing 'query' and optional 'params'
        context: Workflow context with session tracking info

    Returns:
        Processed data with 'result' and 'metadata' keys

    Raises:
        ValidationError: If required fields are missing
        TimeoutError: If processing exceeds configured timeout

    Example:
        ```python
        processor = DataProcessor(timeout=5.0)
        context = WorkflowContext(workflow_id="process-123")
        result = await processor.execute(
            {"query": "test", "params": {}},
            context
        )
        ```
    """
    ...
```

## Import Organization

```python
# Standard library
import asyncio
from typing import Any

# Third-party
from pydantic import BaseModel, Field

# Local package - absolute imports
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive
```

## Pydantic Models

Use Pydantic v2 for all data structures:

```python
from pydantic import BaseModel, Field

class InputData(BaseModel):
    """Input structure for processing."""

    query: str = Field(..., description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Quality Checklist

Before committing, ensure:
- [ ] Full type annotations
- [ ] Google-style docstrings with examples
- [ ] Tests using `MockPrimitive`
- [ ] No global state
- [ ] Specific exceptions with context
- [ ] Uses primitives for composition
- [ ] Formatted with `uv run ruff format`
- [ ] Linted with `uv run ruff check --fix`
- [ ] Type-checked with `uvx pyright`


---
**Logseq:** [[TTA.dev/Platform/Primitives/.cursor/Rules/Package-source.instructions]]
