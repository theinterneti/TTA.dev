"""Python Pathway - Python code analysis utilities for TTA.dev.

Provides AST-based analysis, pattern detection, and workflow primitives
for integrating code analysis into TTA.dev workflows.

Example:
    ```python
    from python_pathway import PythonAnalyzer, PatternDetector
    from python_pathway import CodeAnalysisPrimitive

    analyzer = PythonAnalyzer()
    result = analyzer.analyze_file("path/to/file.py")
    print(result.classes)
    ```
"""

from __future__ import annotations

from .analyzer import PythonAnalyzer
from .detector import PatternDetector
from .models import (
    AnalysisResult,
    ClassInfo,
    FunctionInfo,
    ImportInfo,
    PatternMatch,
)
from .primitives import (
    CodeAnalysisPrimitive,
    DependencyAnalysisPrimitive,
    PatternDetectionPrimitive,
)

__all__ = [
    "PythonAnalyzer",
    "PatternDetector",
    "AnalysisResult",
    "ClassInfo",
    "FunctionInfo",
    "ImportInfo",
    "PatternMatch",
    "CodeAnalysisPrimitive",
    "DependencyAnalysisPrimitive",
    "PatternDetectionPrimitive",
]
