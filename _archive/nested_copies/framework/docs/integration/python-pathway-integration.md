# Python Pathway Integration

**Category:** Code Analysis & Utilities
**Status:** Experimental
**Version:** 0.1.0
**Last Updated:** 2024-03-19

---

## Overview

The Python Pathway integration provides utilities for Python code analysis, path management, and workspace navigation. It offers tools for analyzing Python project structures, dependency graphs, and code quality metrics.

### Key Features

- **Path Management** - Workspace-aware path resolution
- **Dependency Analysis** - Import graph generation
- **Code Quality** - Static analysis and metrics
- **Project Structure** - Automatic structure detection
- **Module Discovery** - Find and analyze Python modules

### Use Cases

1. **Code Navigation** - Find modules and dependencies
2. **Dependency Tracking** - Analyze import relationships
3. **Quality Analysis** - Code metrics and quality scores
4. **Project Scaffolding** - Generate project structures
5. **Module Management** - Discover and organize modules

---

## Architecture

### System Components

```text
┌────────────────────────────────────────────────────────┐
│                 Python Pathway                          │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │Path Manager  │  │  Analyzer    │  │  Discovery  │  │
│  │              │  │              │  │             │  │
│  │- Resolution  │  │- Imports     │  │- Modules    │  │
│  │- Validation  │  │- Metrics     │  │- Packages   │  │
│  │- Normalization│ │- Complexity  │  │- Structure  │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│         │                 │                  │         │
│         └─────────────────┴──────────────────┘         │
│                           │                            │
│                  ┌────────┴────────┐                   │
│                  │  Workspace API  │                   │
│                  │                 │                   │
│                  │ - Navigation    │                   │
│                  │ - Analysis      │                   │
│                  │ - Reporting     │                   │
│                  └─────────────────┘                   │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Python Project │
                  │   Workspace     │
                  └─────────────────┘
```

### Data Flow

```text
Analysis Request:
  Path/Module → Resolver → AST Parser → Analyzer → Report

Discovery Flow:
  Workspace Root → Scanner → Module Finder → Structure Builder → Results

Dependency Flow:
  Module → Import Extractor → Graph Builder → Dependency Report
```

---

## Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Package Installation

```bash
# Add Python Pathway
uv add python-pathway

# Or install from workspace
cd /home/thein/repos/TTA.dev
uv sync --all-extras
```

### Verify Installation

```python
from python_pathway import PathManager, ModuleAnalyzer

# Check version
print(PathManager.__version__)
```

---

## Configuration

### Basic Configuration

```python
from python_pathway import PathwayConfig

config = PathwayConfig(
    # Workspace root
    root_path="/home/thein/repos/TTA.dev",

    # Python paths
    python_paths=[
        "packages/tta-dev-primitives/src",
        "packages/tta-observability-integration/src",
    ],

    # Exclusions
    exclude_patterns=[
        "**/__pycache__",
        "**/.pytest_cache",
        "**/node_modules",
        "**/.venv",
    ],

    # Analysis options
    analyze_imports=True,
    analyze_complexity=True,
    analyze_types=False,  # Requires type stubs
)
```

### Environment Configuration

```bash
# .env file
PATHWAY_ROOT=/home/thein/repos/TTA.dev
PATHWAY_PYTHON_PATHS=packages/*/src
PATHWAY_EXCLUDE=**/__pycache__,**/.venv
```

---

## Usage Examples

### Path Management

#### Basic Path Operations

```python
from python_pathway import PathManager

# Initialize
pm = PathManager(root="/home/thein/repos/TTA.dev")

# Resolve paths
abs_path = pm.resolve("packages/tta-dev-primitives/src")
print(f"Absolute: {abs_path}")

# Relative paths
rel_path = pm.relative_to(
    "/home/thein/repos/TTA.dev/packages/tta-dev-primitives/src/base.py",
    "/home/thein/repos/TTA.dev"
)
print(f"Relative: {rel_path}")

# Validate paths
if pm.exists("packages/tta-dev-primitives"):
    print("Path exists")

# Find files
python_files = pm.find_files(
    pattern="**/*.py",
    exclude_patterns=["**/tests/**", "**/__pycache__/**"]
)
print(f"Found {len(python_files)} Python files")
```

#### Workspace Navigation

```python
from python_pathway import WorkspaceNavigator

# Initialize
navigator = WorkspaceNavigator(root="/home/thein/repos/TTA.dev")

# Find packages
packages = navigator.find_packages()
for package in packages:
    print(f"Package: {package.name} at {package.path}")

# Find module
module = navigator.find_module("tta_dev_primitives.core.base")
print(f"Module path: {module.file_path}")

# Get package structure
structure = navigator.get_package_structure("tta-dev-primitives")
print(f"Package structure:")
for module in structure.modules:
    print(f"  - {module.name}")
```

### Module Analysis

#### Analyze Imports

```python
from python_pathway import ModuleAnalyzer

analyzer = ModuleAnalyzer()

# Analyze module imports
result = analyzer.analyze_imports("packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py")

print(f"Module: {result.module_name}")
print(f"Imports:")
for imp in result.imports:
    print(f"  - {imp.module} {'(from ' + imp.from_module + ')' if imp.from_module else ''}")

print(f"\nDependencies:")
for dep in result.dependencies:
    print(f"  - {dep}")
```

#### Analyze Code Complexity

```python
from python_pathway import ComplexityAnalyzer

analyzer = ComplexityAnalyzer()

# Analyze file complexity
result = analyzer.analyze_file("packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py")

print(f"File: {result.file_path}")
print(f"Lines of code: {result.loc}")
print(f"Functions: {result.function_count}")
print(f"Classes: {result.class_count}")
print(f"Average complexity: {result.avg_complexity}")

# Function-level complexity
for func in result.functions:
    print(f"\nFunction: {func.name}")
    print(f"  Lines: {func.loc}")
    print(f"  Complexity: {func.complexity}")
    print(f"  Parameters: {func.parameter_count}")
```

#### Analyze Module Structure

```python
from python_pathway import StructureAnalyzer

analyzer = StructureAnalyzer()

# Analyze package structure
result = analyzer.analyze_package("packages/tta-dev-primitives")

print(f"Package: {result.name}")
print(f"Version: {result.version}")
print(f"Modules: {len(result.modules)}")
print(f"Total LOC: {result.total_loc}")

# Module breakdown
for module in result.modules:
    print(f"\n{module.name}:")
    print(f"  Classes: {len(module.classes)}")
    print(f"  Functions: {len(module.functions)}")
    print(f"  LOC: {module.loc}")
```

### Dependency Analysis

#### Build Dependency Graph

```python
from python_pathway import DependencyAnalyzer

analyzer = DependencyAnalyzer()

# Analyze package dependencies
graph = analyzer.analyze_package("packages/tta-dev-primitives")

print(f"Total modules: {len(graph.nodes)}")
print(f"Dependencies: {len(graph.edges)}")

# Find circular dependencies
circular = graph.find_circular_dependencies()
if circular:
    print(f"\n⚠️  Circular dependencies found:")
    for cycle in circular:
        print(f"  - {' → '.join(cycle)}")

# Find most imported modules
top_imported = graph.get_most_imported(limit=5)
print(f"\nMost imported modules:")
for module, count in top_imported:
    print(f"  - {module}: {count} imports")

# Get module dependencies
module_deps = graph.get_dependencies("tta_dev_primitives.core.base")
print(f"\nDependencies of base module:")
for dep in module_deps:
    print(f"  - {dep}")
```

#### Export Dependency Graph

```python
from python_pathway import DependencyAnalyzer

analyzer = DependencyAnalyzer()
graph = analyzer.analyze_package("packages/tta-dev-primitives")

# Export as DOT (Graphviz)
graph.export_dot("deps.dot")

# Export as JSON
graph.export_json("deps.json")

# Export as Mermaid
mermaid = graph.export_mermaid()
print(mermaid)

# Render with Graphviz
graph.render("deps.png", format="png")
```

### Code Quality Analysis

#### Quality Metrics

```python
from python_pathway import QualityAnalyzer

analyzer = QualityAnalyzer()

# Analyze code quality
result = analyzer.analyze_package("packages/tta-dev-primitives")

print(f"Package: {result.name}")
print(f"Quality Score: {result.score}/100")
print(f"\nMetrics:")
print(f"  Maintainability: {result.maintainability}/100")
print(f"  Testability: {result.testability}/100")
print(f"  Documentation: {result.documentation}/100")
print(f"  Type Coverage: {result.type_coverage}%")

# Issues by severity
print(f"\nIssues:")
print(f"  Errors: {result.error_count}")
print(f"  Warnings: {result.warning_count}")
print(f"  Info: {result.info_count}")

# Top issues
for issue in result.top_issues[:5]:
    print(f"\n{issue.severity}: {issue.message}")
    print(f"  File: {issue.file}")
    print(f"  Line: {issue.line}")
```

#### Generate Quality Report

```python
from python_pathway import QualityAnalyzer

analyzer = QualityAnalyzer()
result = analyzer.analyze_package("packages/tta-dev-primitives")

# Generate HTML report
report = analyzer.generate_report(
    result,
    format="html",
    output="quality-report.html"
)

print(f"Report generated: {report.path}")

# Generate markdown report
report = analyzer.generate_report(
    result,
    format="markdown",
    output="quality-report.md"
)
```

---

## Integration Patterns

### Pattern 1: Pre-commit Quality Check

```python
from python_pathway import QualityAnalyzer, PathManager
import sys

def check_quality():
    pm = PathManager(root=".")
    analyzer = QualityAnalyzer()

    # Get changed files
    changed_files = pm.get_changed_files()

    # Analyze quality
    issues = []
    for file_path in changed_files:
        if file_path.endswith(".py"):
            result = analyzer.analyze_file(file_path)
            issues.extend(result.errors)

    if issues:
        print(f"❌ {len(issues)} quality issues found:")
        for issue in issues[:10]:
            print(f"  - {issue.file}:{issue.line}: {issue.message}")
        sys.exit(1)
    else:
        print("✅ Quality check passed")
        sys.exit(0)

if __name__ == "__main__":
    check_quality()
```

### Pattern 2: Dependency Validation

```python
from python_pathway import DependencyAnalyzer

def validate_dependencies():
    analyzer = DependencyAnalyzer()

    # Analyze all packages
    packages = [
        "packages/tta-dev-primitives",
        "packages/tta-observability-integration",
        "packages/universal-agent-context",
    ]

    all_valid = True

    for package_path in packages:
        graph = analyzer.analyze_package(package_path)

        # Check for circular dependencies
        circular = graph.find_circular_dependencies()
        if circular:
            print(f"❌ Circular dependencies in {package_path}:")
            for cycle in circular:
                print(f"  - {' → '.join(cycle)}")
            all_valid = False

        # Check for external dependencies
        external = graph.get_external_dependencies()
        print(f"\n{package_path} external dependencies:")
        for dep in external:
            print(f"  - {dep}")

    if all_valid:
        print("\n✅ All dependencies valid")
    else:
        print("\n❌ Dependency issues found")
        sys.exit(1)

if __name__ == "__main__":
    validate_dependencies()
```

### Pattern 3: Documentation Generator

```python
from python_pathway import StructureAnalyzer, ModuleAnalyzer
from pathlib import Path

def generate_docs():
    struct_analyzer = StructureAnalyzer()
    mod_analyzer = ModuleAnalyzer()

    # Analyze package
    package = struct_analyzer.analyze_package("packages/tta-dev-primitives")

    # Generate documentation
    docs_dir = Path("docs/api")
    docs_dir.mkdir(exist_ok=True)

    # Package overview
    with open(docs_dir / "overview.md", "w") as f:
        f.write(f"# {package.name}\n\n")
        f.write(f"Version: {package.version}\n")
        f.write(f"Modules: {len(package.modules)}\n\n")

        f.write("## Modules\n\n")
        for module in package.modules:
            f.write(f"- [{module.name}]({module.name}.md)\n")

    # Module documentation
    for module in package.modules:
        analysis = mod_analyzer.analyze_module(module.file_path)

        with open(docs_dir / f"{module.name}.md", "w") as f:
            f.write(f"# {module.name}\n\n")

            # Classes
            f.write("## Classes\n\n")
            for cls in analysis.classes:
                f.write(f"### {cls.name}\n\n")
                if cls.docstring:
                    f.write(f"{cls.docstring}\n\n")

                # Methods
                if cls.methods:
                    f.write("#### Methods\n\n")
                    for method in cls.methods:
                        f.write(f"- `{method.name}`: {method.docstring or 'No description'}\n")
                f.write("\n")

            # Functions
            f.write("## Functions\n\n")
            for func in analysis.functions:
                f.write(f"### {func.name}\n\n")
                if func.docstring:
                    f.write(f"{func.docstring}\n\n")
                f.write(f"Parameters: {', '.join(func.parameters)}\n\n")

    print(f"✅ Documentation generated in {docs_dir}")

if __name__ == "__main__":
    generate_docs()
```

---

## Best Practices

### Path Management Best Practices

1. **Use Absolute Paths**

   ```python
   # ✅ Good - explicit
   pm = PathManager(root="/home/thein/repos/TTA.dev")
   path = pm.resolve("packages/tta-dev-primitives/src")

   # ❌ Bad - ambiguous
   path = "packages/tta-dev-primitives/src"
   ```

2. **Validate Paths**

   ```python
   # Always validate before operations
   if pm.exists(path):
       result = analyzer.analyze(path)
   else:
       print(f"Path not found: {path}")
   ```

3. **Use Path Objects**

   ```python
   from pathlib import Path

   # Preferred
   path = Path("/home/thein/repos/TTA.dev")
   file_path = path / "packages" / "tta-dev-primitives" / "src"
   ```

### Analysis Best Practices

1. **Cache Analysis Results**

   ```python
   # Avoid re-analyzing unchanged files
   analyzer = ModuleAnalyzer(cache_dir=".cache/analysis")
   result = analyzer.analyze(path)  # Cached if file unchanged
   ```

2. **Handle Errors Gracefully**

   ```python
   try:
       result = analyzer.analyze(path)
   except SyntaxError as e:
       print(f"Syntax error in {path}: {e}")
   except Exception as e:
       print(f"Analysis failed for {path}: {e}")
   ```

3. **Use Filters**

   ```python
   # Exclude test files from metrics
   analyzer = QualityAnalyzer(
       exclude_patterns=[
           "**/tests/**",
           "**/*_test.py",
           "**/test_*.py",
       ]
   )
   ```

### Performance Optimization

1. **Parallel Analysis**

   ```python
   from python_pathway import ModuleAnalyzer
   import asyncio

   async def analyze_files(file_paths):
       analyzer = ModuleAnalyzer()
       tasks = [analyzer.analyze_async(path) for path in file_paths]
       return await asyncio.gather(*tasks)

   # Analyze files in parallel
   results = asyncio.run(analyze_files(python_files))
   ```

2. **Incremental Analysis**

   ```python
   # Only analyze changed files
   pm = PathManager(root=".")
   changed = pm.get_changed_files()

   analyzer = ModuleAnalyzer()
   for file_path in changed:
       if file_path.endswith(".py"):
           result = analyzer.analyze(file_path)
   ```

3. **Limit Recursion**

   ```python
   # Limit depth for large projects
   navigator = WorkspaceNavigator(
       root=".",
       max_depth=3  # Only 3 levels deep
   )
   ```

---

## Troubleshooting

### Issue: Module Not Found

**Symptoms:**

```text
ModuleNotFoundError: No module named 'tta_dev_primitives'
```

**Solution:**

```python
# Add package paths to Python path
from python_pathway import PathManager

pm = PathManager(root="/home/thein/repos/TTA.dev")
pm.add_python_paths([
    "packages/tta-dev-primitives/src",
    "packages/tta-observability-integration/src",
])

# Or use environment variable
import os
os.environ["PYTHONPATH"] = ":".join([
    "/home/thein/repos/TTA.dev/packages/tta-dev-primitives/src",
    "/home/thein/repos/TTA.dev/packages/tta-observability-integration/src",
])
```

### Issue: Import Analysis Fails

**Symptoms:**

```text
Failed to analyze imports: SyntaxError
```

**Solution:**

```python
# Check Python version compatibility
analyzer = ModuleAnalyzer(python_version="3.11")

# Or skip files with syntax errors
analyzer = ModuleAnalyzer(skip_errors=True)
result = analyzer.analyze_package(
    "packages/tta-dev-primitives",
    on_error="warn"  # "skip" or "raise"
)
```

### Issue: Slow Analysis

**Symptoms:**

```text
Analysis takes too long on large projects
```

**Solution:**

```python
# Use caching
analyzer = ModuleAnalyzer(
    cache_dir=".cache/analysis",
    cache_ttl=3600  # 1 hour
)

# Exclude unnecessary files
analyzer = ModuleAnalyzer(
    exclude_patterns=[
        "**/__pycache__/**",
        "**/tests/**",
        "**/.venv/**",
        "**/node_modules/**",
    ]
)

# Limit analysis scope
result = analyzer.analyze_package(
    "packages/tta-dev-primitives",
    analyze_complexity=False,  # Skip complexity analysis
    analyze_types=False,  # Skip type analysis
)
```

---

## API Reference

### Core Classes

#### PathManager

```python
class PathManager:
    def __init__(
        self,
        root: str | Path,
        python_paths: list[str] | None = None,
    ): ...

    def resolve(self, path: str | Path) -> Path: ...
    def relative_to(self, path: str | Path, base: str | Path) -> Path: ...
    def exists(self, path: str | Path) -> bool: ...
    def find_files(
        self,
        pattern: str,
        exclude_patterns: list[str] | None = None
    ) -> list[Path]: ...
```

#### ModuleAnalyzer

```python
class ModuleAnalyzer:
    def __init__(
        self,
        python_version: str = "3.11",
        cache_dir: str | Path | None = None,
    ): ...

    def analyze_imports(self, file_path: str | Path) -> ImportAnalysis: ...
    def analyze_module(self, file_path: str | Path) -> ModuleAnalysis: ...
    async def analyze_async(self, file_path: str | Path) -> ModuleAnalysis: ...
```

#### DependencyAnalyzer

```python
class DependencyAnalyzer:
    def __init__(
        self,
        exclude_external: bool = False,
    ): ...

    def analyze_package(self, package_path: str | Path) -> DependencyGraph: ...
    def analyze_workspace(self, root: str | Path) -> DependencyGraph: ...

class DependencyGraph:
    @property
    def nodes(self) -> list[str]: ...

    @property
    def edges(self) -> list[tuple[str, str]]: ...

    def find_circular_dependencies(self) -> list[list[str]]: ...
    def get_most_imported(self, limit: int = 10) -> list[tuple[str, int]]: ...
    def export_dot(self, output: str | Path) -> None: ...
    def export_json(self, output: str | Path) -> None: ...
```

#### QualityAnalyzer

```python
class QualityAnalyzer:
    def __init__(
        self,
        exclude_patterns: list[str] | None = None,
    ): ...

    def analyze_file(self, file_path: str | Path) -> QualityResult: ...
    def analyze_package(self, package_path: str | Path) -> QualityResult: ...
    def generate_report(
        self,
        result: QualityResult,
        format: str = "html",  # "html", "markdown", "json"
        output: str | Path | None = None
    ) -> Report: ...
```

### Data Classes

```python
@dataclass
class ImportAnalysis:
    module_name: str
    file_path: Path
    imports: list[Import]
    dependencies: list[str]

@dataclass
class ModuleAnalysis:
    name: str
    file_path: Path
    loc: int
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
    imports: list[Import]

@dataclass
class QualityResult:
    name: str
    score: int  # 0-100
    maintainability: int
    testability: int
    documentation: int
    type_coverage: float
    error_count: int
    warning_count: int
    info_count: int
    top_issues: list[Issue]
```

---

## Related Documentation

- **Package README:** [`packages/python-pathway/README.md`](../../packages/python-pathway/README.md)
- **Code Quality Guide:** [`docs/guides/code-quality-guide.md`](../guides/code-quality-guide.md)
- **Testing Guide:** [`docs/guides/testing-guide.md`](../guides/testing-guide.md)

---

**Last Updated:** 2024-03-19
**Status:** Experimental
**Maintainer:** TTA.dev Team


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Integration/Python-pathway-integration]]
