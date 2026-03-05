# python-pathway

AST-based Python code analysis utilities for TTA.dev.

`python-pathway` provides structural analysis, pattern detection, and composable
workflow primitives for integrating Python code analysis into TTA.dev workflows.

## Features

- **Structural analysis** — extract classes, functions, and imports from any Python
  source file using the standard `ast` module (no external parser required)
- **Pattern detection** — automatically detect common design patterns (singleton,
  factory, decorator, context manager, async) and anti-patterns (mutable default
  arguments, bare except, missing type hints, star imports)
- **Workflow primitives** — drop-in `WorkflowPrimitive` implementations
  (`CodeAnalysisPrimitive`, `PatternDetectionPrimitive`,
  `DependencyAnalysisPrimitive`) composable with the `>>` operator
- **Pydantic v2 models** — fully typed, serialisable result models

## Installation

This package is part of the TTA.dev workspace. Install it alongside the
workspace from the repo root:

```bash
uv sync
```

## Quick Start

### Standalone usage

```python
from python_pathway import PythonAnalyzer, PatternDetector

analyzer = PythonAnalyzer()
result = analyzer.analyze_file("src/my_module.py")

print(result.total_lines)        # int
print(result.complexity_score)   # float
print(result.classes)            # list[ClassInfo]
print(result.functions)          # list[FunctionInfo]
print(result.imports)            # list[ImportInfo]

detector = PatternDetector()
patterns = detector.detect_patterns("src/my_module.py")
for p in patterns:
    print(f"[{p.severity}] {p.name}: {p.description}")
```

### Workflow integration

```python
import asyncio
from tta_dev_primitives import WorkflowContext
from python_pathway import CodeAnalysisPrimitive

async def main() -> None:
    ctx = WorkflowContext(workflow_id="analysis")
    primitive = CodeAnalysisPrimitive(include_patterns=True)
    result = await primitive.execute("src/my_module.py", ctx)
    print(result.patterns)

asyncio.run(main())
```

### Dependency analysis

```python
import asyncio
from tta_dev_primitives import WorkflowContext
from python_pathway import DependencyAnalysisPrimitive

async def main() -> None:
    ctx = WorkflowContext(workflow_id="deps")
    primitive = DependencyAnalysisPrimitive()
    result = await primitive.execute("/path/to/project", ctx)
    print(result["dependency_tree"])

asyncio.run(main())
```

## API Reference

### Models (`python_pathway.models`)

| Model | Description |
|---|---|
| `AnalysisResult` | Complete analysis result for a Python source file |
| `ClassInfo` | Class name, bases, methods, decorators, line number, `is_abstract` |
| `FunctionInfo` | Function name, parameters, return type, decorators, `is_async`, `has_type_hints` |
| `ImportInfo` | Module, imported names, alias, `is_from_import`, line number |
| `PatternMatch` | Pattern name, category (`pattern`/`anti_pattern`), description, severity |

### Analyzer (`python_pathway.analyzer`)

```python
class PythonAnalyzer:
    def analyze_file(self, file_path: str) -> AnalysisResult: ...
    def analyze_source(self, source: str, file_path: str = "<string>") -> AnalysisResult: ...
```

### Detector (`python_pathway.detector`)

```python
class PatternDetector:
    def detect_patterns(self, file_path: str) -> list[PatternMatch]: ...
    def detect_from_source(self, source: str) -> list[PatternMatch]: ...
```

**Detected patterns:**

| Name | Category | Severity |
|---|---|---|
| `singleton` | pattern | info |
| `factory` | pattern | info |
| `decorator_pattern` | pattern | info |
| `context_manager` | pattern | info |
| `async_pattern` | pattern | info |
| `mutable_default_argument` | anti_pattern | warning |
| `bare_except` | anti_pattern | warning |
| `missing_type_hints` | anti_pattern | warning |
| `star_import` | anti_pattern | warning |

### Primitives (`python_pathway.primitives`)

| Primitive | Input | Output |
|---|---|---|
| `CodeAnalysisPrimitive` | `str` (file path) | `AnalysisResult` |
| `PatternDetectionPrimitive` | `str` (file path) | `list[PatternMatch]` |
| `DependencyAnalysisPrimitive` | `str` (project dir) | `dict[str, object]` |

All primitives implement `WorkflowPrimitive[T, U]` and support the `>>` operator
for sequential composition.

## Development

### Running tests

```bash
# From repo root
uv run pytest packages/python-pathway/

# With coverage
uv run pytest packages/python-pathway/ --cov=python_pathway
```

### Linting

```bash
uv run ruff check packages/python-pathway/
uv run ruff format packages/python-pathway/
```

## License

MIT — see [LICENSE](LICENSE).
