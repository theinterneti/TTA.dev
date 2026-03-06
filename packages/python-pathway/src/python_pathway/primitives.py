"""Workflow primitives for Python code analysis."""

from __future__ import annotations

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.package_managers.uv import UvTreeInput, UvTreePrimitive

from .analyzer import PythonAnalyzer
from .detector import PatternDetector
from .models import AnalysisResult, PatternMatch


class CodeAnalysisPrimitive(WorkflowPrimitive[str, AnalysisResult]):
    """Analyze a Python source file and return structured results.

    Wraps PythonAnalyzer and PatternDetector as a composable workflow primitive.

    Example:
        ```python
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute("src/my_module.py", context)
        print(result.classes)
        ```
    """

    def __init__(self, include_patterns: bool = True) -> None:
        """Initialize the primitive.

        Args:
            include_patterns: Whether to run pattern detection in addition to analysis.
        """
        self._analyzer = PythonAnalyzer()
        self._detector = PatternDetector()
        self._include_patterns = include_patterns

    async def execute(self, input_data: str, context: WorkflowContext) -> AnalysisResult:
        """Execute code analysis on a Python file.

        Args:
            input_data: Path to the Python source file.
            context: Workflow context.

        Returns:
            An AnalysisResult with structural information and detected patterns.
        """
        result = self._analyzer.analyze_file(input_data)
        if self._include_patterns:
            patterns = self._detector.detect_patterns(input_data)
            result = result.model_copy(update={"patterns": patterns})
        return result


class PatternDetectionPrimitive(WorkflowPrimitive[str, list[PatternMatch]]):
    """Detect patterns and anti-patterns in a Python source file.

    Example:
        ```python
        primitive = PatternDetectionPrimitive()
        patterns = await primitive.execute("src/my_module.py", context)
        ```
    """

    def __init__(self) -> None:
        """Initialize the pattern detection primitive."""
        self._detector = PatternDetector()

    async def execute(
        self,
        input_data: str,
        context: WorkflowContext,
    ) -> list[PatternMatch]:
        """Execute pattern detection on a Python file.

        Args:
            input_data: Path to the Python source file.
            context: Workflow context.

        Returns:
            A list of detected patterns and anti-patterns.
        """
        return self._detector.detect_patterns(input_data)


class DependencyAnalysisPrimitive(WorkflowPrimitive[str, dict[str, object]]):
    """Analyze Python project dependencies using uv tree.

    Composes with UvTreePrimitive to retrieve the dependency tree
    and returns a structured dict with the raw output.

    Example:
        ```python
        primitive = DependencyAnalysisPrimitive()
        result = await primitive.execute("/path/to/project", context)
        print(result["dependency_tree"])
        ```
    """

    def __init__(self) -> None:
        """Initialize the dependency analysis primitive."""

    async def execute(
        self,
        input_data: str,
        context: WorkflowContext,
    ) -> dict[str, object]:
        """Execute dependency analysis for a Python project.

        Args:
            input_data: Path to the project directory.
            context: Workflow context.

        Returns:
            A dict with keys:

            - ``dependency_tree``: raw ``uv tree`` output (str)
            - ``success``: whether the command succeeded (bool)
            - ``project_path``: the analysed project path (str)
        """
        uv_tree = UvTreePrimitive(working_dir=input_data)
        output = await uv_tree.execute(UvTreeInput(), context)
        return {
            "dependency_tree": output.stdout,
            "success": output.success,
            "project_path": input_data,
        }
