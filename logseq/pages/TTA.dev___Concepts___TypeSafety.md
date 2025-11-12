# TTA.dev/Concepts/TypeSafety

type:: [C] CoreConcept
status:: stable
tags:: #concept, #type-safety, #generics
context-level:: 1-Strategic
summary:: Type safety through Python generics ensures workflow correctness at design time, preventing runtime type errors
implemented-by:: [[TTA.dev/Primitives/Core/WorkflowPrimitive]]
related-concepts:: [[TTA.dev/Concepts/Composition]], [[TTA.dev/Concepts/Observability]]
documentation:: docs/development/CodingStandards.md
examples:: packages/tta-dev-primitives/examples/type_safety.py
created-date:: [[2025-11-11]]
last-updated:: [[2025-11-11]]

---

## Overview

**Type Safety** in TTA.dev is achieved through Python's generic type system, ensuring that workflows are correct by construction. Every primitive declares its input and output types using `WorkflowPrimitive[TInput, TOutput]`, enabling the type checker to catch incompatibilities before runtime.

This design principle makes TTA.dev workflows as reliable as compiled code, while maintaining Python's developer-friendly syntax.

---

## Why This Matters

### Business Value

- **Fewer Production Bugs** - Catch type errors during development
- **Faster Debugging** - Type hints guide developers to correct usage
- **Better Documentation** - Types serve as inline documentation
- **Easier Refactoring** - Type checker validates changes across codebase

### Technical Value

- **Compile-Time Validation** - Pyright/mypy catch errors pre-runtime
- **IDE Autocomplete** - Better editor support with type hints
- **Self-Documenting Code** - Types clarify intent without comments
- **Refactoring Safety** - Change types with confidence

---

## Core Principles

1. **Generic Primitives** - `WorkflowPrimitive[T, U]` declares input/output types
2. **Type Inference** - Composition operators propagate types automatically
3. **No `Any` Escape Hatches** - All public APIs are fully typed
4. **Pydantic Models** - Structured data uses validated schemas
5. **100% Type Coverage** - All code passes strict type checking

---

## Implementation

Type safety is implemented through:

- [[TTA.dev/Primitives/Core/WorkflowPrimitive]] - Generic base class `WorkflowPrimitive[T, U]`
- [[TTA.dev/Data/WorkflowContext]] - Fully typed execution context
- Python type hints - All functions/methods have complete annotations

---

## Generic Type System

### Base Primitive

```python
from typing import Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")

class WorkflowPrimitive(Generic[T, U], ABC):
    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        pass
```

### Concrete Implementations

```python
class StringToDict(WorkflowPrimitive[str, dict]):
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {"text": input_data, "length": len(input_data)}

class DictToInt(WorkflowPrimitive[dict, int]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> int:
        return input_data.get("length", 0)
```

### Type-Safe Composition

```python
# ✅ Valid - types align (str → dict → int)
workflow: WorkflowPrimitive[str, int] = StringToDict() >> DictToInt()

# ❌ Type error - int ≠ dict
# workflow = DictToInt() >> StringToDict()  # Pyright catches this!
```

---

## Type Checking Tools

### Pyright (Recommended)

```bash
# Run type checker
uvx pyright packages/

# Expected: 0 errors
```

### Mypy (Alternative)

```bash
# Run mypy
uv run mypy packages/ --strict
```

---

## Type Patterns

### Pattern 1: Homogeneous Workflows

All steps have same type:

```python
class TextTransformer(WorkflowPrimitive[str, str]):
    pass

workflow: WorkflowPrimitive[str, str] = (
    TextTransformer() >>
    TextTransformer() >>
    TextTransformer()
)
```

### Pattern 2: Heterogeneous Workflows

Types transform through pipeline:

```python
workflow: WorkflowPrimitive[str, int] = (
    ParseJSON() >>           # str → dict
    ExtractCount() >>        # dict → list
    ComputeLength()          # list → int
)
```

### Pattern 3: Union Types

Multiple possible types:

```python
class FlexiblePrimitive(WorkflowPrimitive[str | dict, dict]):
    async def execute(
        self,
        input_data: str | dict,
        context: WorkflowContext
    ) -> dict:
        if isinstance(input_data, str):
            return {"text": input_data}
        return input_data
```

---

## Pydantic Integration

Structured data uses [[TTA.dev/Data/WorkflowContext]] and other Pydantic models:

```python
from pydantic import BaseModel

class Request(BaseModel):
    prompt: str
    max_tokens: int

class Response(BaseModel):
    text: str
    tokens_used: int

class LLMPrimitive(WorkflowPrimitive[Request, Response]):
    async def execute(
        self,
        input_data: Request,
        context: WorkflowContext
    ) -> Response:
        # input_data is validated by Pydantic
        # Return value must match Response schema
        return Response(text="...", tokens_used=100)
```

---

## Common Type Errors

### Error: Type Mismatch

```python
# ❌ Error
workflow = StringToDict() >> StringToDict()
# Error: Expected dict input, got str output from previous step

# ✅ Fix - ensure types align
workflow = StringToDict() >> DictToInt()
```

### Error: Missing Type Annotation

```python
# ❌ Error
class BadPrimitive(WorkflowPrimitive):  # Missing type parameters!
    pass

# ✅ Fix - add generic types
class GoodPrimitive(WorkflowPrimitive[str, dict]):
    pass
```

### Error: Using `Any`

```python
# ❌ Discouraged
from typing import Any

class LoosePrimitive(WorkflowPrimitive[Any, Any]):  # Defeats type safety!
    pass

# ✅ Better - be specific
class StrictPrimitive(WorkflowPrimitive[str, dict]):
    pass
```

---

## Type Safety in Practice

### Example: Production Workflow

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

# All types explicitly declared
class ValidateInput(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Validates and cleans input data."""
    pass

class CallLLM(WorkflowPrimitive[dict[str, Any], str]):
    """Calls LLM and returns text response."""
    pass

class FormatOutput(WorkflowPrimitive[str, dict[str, str]]):
    """Formats LLM response as structured output."""
    pass

# Type-safe composition - compiler validates this!
workflow: WorkflowPrimitive[dict[str, Any], dict[str, str]] = (
    ValidateInput() >>
    CachePrimitive(RetryPrimitive(CallLLM())) >>
    FormatOutput()
)
```

---

## Benefits Over Duck Typing

| Approach | Type Safety | Runtime Errors | IDE Support | Refactoring |
|----------|-------------|----------------|-------------|-------------|
| Duck Typing | ❌ None | 😱 Many | 🤷 Limited | 💣 Dangerous |
| Type Hints | ✅ Strong | 😊 Rare | 🎯 Excellent | 🛡️ Safe |

---

## Related Concepts

- [[TTA.dev/Concepts/Composition]] - How types flow through composition
- [[TTA.dev/Concepts/Observability]] - Typed context propagation
- [[TTA.dev/Primitives/Core/WorkflowPrimitive]] - Generic base class

---

## Examples

**Example Files:**
- `packages/tta-dev-primitives/examples/type_safety_examples.py` - Type safety patterns
- `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py` - Generic base class

---

## Further Reading

- Python typing documentation: https://docs.python.org/3/library/typing.html
- Pyright: https://github.com/microsoft/pyright
- `docs/development/CodingStandards.md` - TTA.dev coding standards

---

## Tags

#concept #type-safety #generics #python #static-analysis
