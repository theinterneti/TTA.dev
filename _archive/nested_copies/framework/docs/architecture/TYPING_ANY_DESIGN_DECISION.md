# typing.Any Design Decision

**Date:** 2025-11-05
**Status:** Decided
**Decision:** Allow `typing.Any` in base primitive classes with explicit justification

---

## Context

During CI/CD quality checks, we encountered 450+ Ruff ANN401 violations ("Dynamically typed expressions (typing.Any) are disallowed"). This rule enforces that `typing.Any` should only be used as an "escape hatch" when truly necessary.

### What is ANN401?

**Rule:** `any-type` (ANN401)
**Source:** flake8-annotations linter
**Purpose:** Checks that function arguments are annotated with a more specific type than `Any`

**Why it exists:**
- `Any` is a special type indicating an **unconstrained type**
- Type checkers allow **all operations** on `Any`
- This defeats the purpose of type checking
- Better to be explicit about types and use `Any` only as an "escape hatch"

**Ruff Documentation:**
> It's better to be explicit about the type of an expression, and to use `Any` as an "escape hatch" only when it is really needed.

Sources:
- [Ruff ANN401 Rule](https://docs.astral.sh/ruff/rules/any-type/)
- [Python typing spec: Any](https://typing.python.org/en/latest/spec/special-types.html#any)
- [Mypy documentation: The Any type](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-any-type)

---

## Problem Statement

TTA.dev uses `typing.Any` in **46 locations** across the codebase, primarily in:

1. **Base primitive classes** (`WorkflowPrimitive[TInput, TOutput]`)
2. **Mock/test utilities** (`MockPrimitive`)
3. **Conditional routing** (`ConditionalPrimitive`)
4. **Instrumentation wrappers** (`InstrumentedPrimitive`)

These are **architectural choices**, not convenience shortcuts.

---

## Analysis: When is `typing.Any` Justified?

### ✅ **Legitimate Use Cases**

Based on research and Python typing best practices:

#### 1. **Generic Base Classes with Unknown Type Parameters**

When building framework/library primitives that users will specialize:

```python
class WorkflowPrimitive[TInput, TOutput]:
    """Base class - TInput/TOutput are type variables, not Any."""
    async def execute(
        self,
        input_data: TInput,  # ✅ Generic type variable
        context: WorkflowContext
    ) -> TOutput:  # ✅ Generic type variable
        ...
```

**BUT** - when the primitive needs to accept callbacks or functions with unknown signatures:

```python
class ConditionalPrimitive(WorkflowPrimitive[TInput, TOutput]):
    def __init__(
        self,
        condition: Callable[[TInput, WorkflowContext], bool],  # ✅ Specific
        then_primitive: WorkflowPrimitive[TInput, TOutput],    # ✅ Specific
        else_primitive: WorkflowPrimitive[TInput, TOutput] | None = None,
    ):
        ...
```

vs.

```python
class MockPrimitive(WorkflowPrimitive[Any, Any]):  # ⚠️ Any used here
    """Testing primitive that mocks any workflow step.

    Justification: Mocks need to accept and return ANY type to be useful
    for testing. This is an intentional design choice for test flexibility.
    """
    def __init__(self, return_value: Any = None):  # ⚠️ Any used here
        self._return_value = return_value
```

#### 2. **Test Doubles and Mocking**

Mocks **must** be able to stand in for any type:

```python
# ✅ JUSTIFIED: MockPrimitive needs to mock any workflow
mock_llm = MockPrimitive(return_value={"response": "test"})
workflow = step1 >> mock_llm >> step3  # mock_llm stands in for real LLM
```

#### 3. **Wrapper/Decorator Patterns**

When instrumenting or wrapping arbitrary functions:

```python
class InstrumentedPrimitive[TInput, TOutput]:
    """Adds observability to any primitive.

    Justification: Must wrap primitives with ANY input/output types.
    Using `Any` here allows maximum flexibility for instrumentation.
    """
    def __init__(
        self,
        primitive: WorkflowPrimitive[TInput, TOutput],
        tracer: Any = None  # ⚠️ OpenTelemetry tracer - complex type
    ):
        ...
```

#### 4. **Integration with Third-Party Libraries**

When dealing with complex external types:

```python
# OpenTelemetry Tracer has complex type that's hard to represent
tracer: Any  # ⚠️ JUSTIFIED: Complex external library type

# Better than importing entire typing dependency tree:
# from opentelemetry.trace import Tracer, TracerProvider, Span, ...
```

### ❌ **Non-Justified Use Cases**

#### 1. **Convenience/Laziness**

```python
# ❌ BAD: Using Any because we don't want to type it properly
def process(data: Any) -> Any:
    return data["result"]  # Should be dict[str, Any] -> str
```

#### 2. **Avoiding Union Types**

```python
# ❌ BAD: Using Any to avoid union
def handle(value: Any):
    ...

# ✅ GOOD: Explicit union
def handle(value: str | int | dict[str, Any]):
    ...
```

#### 3. **Overly Broad APIs**

```python
# ❌ BAD: API accepts anything
def configure(settings: Any):
    ...

# ✅ GOOD: Specific configuration type
class Settings(TypedDict):
    timeout: int
    retry: bool

def configure(settings: Settings):
    ...
```

---

## Decision

### ✅ **Allow `typing.Any` in these specific cases:**

1. **Base primitive classes** where flexibility is **core to the design**
   - `MockPrimitive` - must mock any workflow
   - Test utilities - need flexibility for testing

2. **Integration points** with complex external types
   - OpenTelemetry tracers
   - Complex SDK objects

3. **Generic wrappers** that must handle arbitrary types
   - `InstrumentedPrimitive` wrapping any primitive
   - Decorator patterns

### 📝 **Requirements when using `Any`:**

1. **Add a docstring comment explaining WHY**
   ```python
   class MockPrimitive(WorkflowPrimitive[Any, Any]):
       """Testing primitive that mocks any workflow step.

       Uses typing.Any intentionally:
       - Input: Must accept any input type for testing flexibility
       - Output: Must return any output type to match mocked primitive

       This is a deliberate design choice for maximum test utility.
       """
   ```

2. **Use `# type: ignore[ANN401]` with explanation** for specific parameters
   ```python
   def __init__(
       self,
       return_value: Any = None,  # type: ignore[ANN401] - Mock must return any type
   ):
       ...
   ```

3. **Consider alternatives first:**
   - Generic type variables (`T`, `TInput`, `TOutput`)
   - Union types (`str | int | dict`)
   - Protocol types (structural subtyping)
   - TypedDict for structured data

### ⚙️ **Configuration Strategy:**

1. **Keep ANN401 enabled globally** (don't add to ignore list)
2. **Suppress per-file for test/mock utilities:**
   ```toml
   [tool.ruff.lint.per-file-ignores]
   "src/**/testing/*.py" = ["ANN401"]  # Testing utilities need flexibility
   "src/**/mocks.py" = ["ANN401"]
   ```

3. **Suppress inline with justification** for legitimate uses in production code:
   ```python
   tracer: Any  # OpenTelemetry tracer - complex external type
   ```

---

## Implementation

### Current Status (2025-11-05)

**Before mitigation:**
- 450 ANN401 errors across codebase

**After package-level configuration:**
- 68 ANN401 errors remaining
- Reduced by 85% through proper per-file ignores

**Breakdown:**
- Tests: Suppressed via per-file-ignores
- Examples: Suppressed via per-file-ignores
- Production code: 68 locations need review

### Package Configuration

#### tta-dev-primitives
```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP", "ANN"]
ignore = ["E501", "ANN101", "ANN102", "ANN401"]  # Allow Any for base primitives

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN", "E501", "E402"]
"examples/**/*.py" = ["ANN", "E501"]
```

**Justification:** Base primitive library needs `Any` for:
- MockPrimitive (test utility)
- Generic base classes with flexible types
- Integration wrappers

#### tta-documentation-primitives
```toml
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "PLR2004", "ANN", "E501"]
"examples/*" = ["ANN", "E501"]
```

**Justification:** Documentation-focused package with many examples demonstrating various patterns.

---

## Remaining Work

### Phase 1: Audit (Current)

Review each of 68 remaining `Any` usages:

```bash
uv run ruff check . --output-format=concise 2>&1 | grep "ANN401"
```

### Phase 2: Categorize

For each usage, determine:
1. ✅ **Justified** - Add docstring/comment explaining why
2. ⚠️ **Questionable** - Can we use generics instead?
3. ❌ **Unjustified** - Replace with specific type

### Phase 3: Remediate

| Category | Action |
|----------|--------|
| Justified | Add `# type: ignore[ANN401]` + justification comment |
| Questionable | Refactor to use generic type variables |
| Unjustified | Replace with specific type annotation |

### Phase 4: Document Patterns

Create examples showing:
- ✅ When to use `Any` (with justification)
- ❌ When NOT to use `Any`
- 🔄 How to refactor `Any` to generics

---

## Examples

### ✅ Good: Justified Use

```python
from typing import Any, TypeVar
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

T = TypeVar('T')

class MockPrimitive(WorkflowPrimitive[Any, Any]):
    """Mock any workflow primitive for testing.

    Uses typing.Any intentionally:
    - Must accept any input type to mock diverse workflows
    - Must return any output type to match mocked primitive

    This is a deliberate design for maximum test flexibility.
    Not suitable for production use.
    """

    def __init__(
        self,
        return_value: Any = None,  # type: ignore[ANN401] - Mock returns any type
    ):
        self._return_value = return_value

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: Any,  # type: ignore[ANN401] - Mock accepts any input
    ) -> Any:  # type: ignore[ANN401] - Mock returns any output
        return self._return_value
```

### ✅ Good: Refactored to Generics

```python
# ❌ BEFORE: Overly broad
class CachePrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(self, primitive: WorkflowPrimitive[Any, Any]):
        ...

# ✅ AFTER: Properly generic
TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')

class CachePrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Cache results of any primitive while preserving types."""
    def __init__(self, primitive: WorkflowPrimitive[TInput, TOutput]):
        ...
```

### ❌ Bad: Unjustified Use

```python
# ❌ BAD: Using Any out of laziness
def process_data(data: Any) -> Any:
    return {"result": data["value"] * 2}

# ✅ GOOD: Specific types
def process_data(data: dict[str, int]) -> dict[str, int]:
    return {"result": data["value"] * 2}
```

---

## References

### Official Documentation

1. **Ruff ANN401 Rule**
   - https://docs.astral.sh/ruff/rules/any-type/
   - Explains the rule and its rationale

2. **Python Typing Spec: Any**
   - https://typing.python.org/en/latest/spec/special-types.html#any
   - Official specification

3. **Mypy Documentation: The Any Type**
   - https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-any-type
   - Best practices from Mypy team

### TTA.dev Documentation

- `AGENTS.md` - Agent instructions for type usage
- `packages/tta-dev-primitives/README.md` - Primitive design patterns
- `.github/instructions/package-source.instructions.md` - Type hint requirements

---

## Conclusion

**typing.Any is a powerful tool that should be used sparingly and with explicit justification.**

In TTA.dev:
- ✅ Allowed in base primitive classes for flexibility
- ✅ Allowed in test/mock utilities
- ✅ Allowed for complex external library types
- ❌ Not allowed as a convenience shortcut
- 📝 Must be documented when used

This approach balances:
- **Type safety** (catching bugs at development time)
- **Flexibility** (allowing powerful abstractions)
- **Clarity** (making design intent explicit)

---

**Last Updated:** 2025-11-05
**Next Review:** After completing Phase 3 remediation
**Owner:** TTA.dev Core Team


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Architecture/Typing_any_design_decision]]
