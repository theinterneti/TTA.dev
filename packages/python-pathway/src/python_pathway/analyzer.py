"""AST-based Python code analyzer."""

from __future__ import annotations

import ast

from .models import AnalysisResult, ClassInfo, FunctionInfo, ImportInfo
from .utils import (
    calculate_complexity,
    get_annotation_string,
    get_decorator_names,
    load_source,
    parse_source,
)


class PythonAnalyzer:
    """Analyze Python source files using the AST module.

    Extracts structural information about classes, functions, and imports.

    Example:
        ```python
        analyzer = PythonAnalyzer()
        result = analyzer.analyze_file("path/to/file.py")
        print(result.classes)
        ```
    """

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a Python source file.

        Args:
            file_path: Path to the Python source file.

        Returns:
            An AnalysisResult with all extracted information.

        Raises:
            FileNotFoundError: If the file does not exist.
            SyntaxError: If the file cannot be parsed.
        """
        source = load_source(file_path)
        return self.analyze_source(source, file_path=file_path)

    def analyze_source(self, source: str, file_path: str = "<string>") -> AnalysisResult:
        """Analyze Python source code from a string.

        Args:
            source: Python source code as a string.
            file_path: Optional path to associate with the result.

        Returns:
            An AnalysisResult with all extracted information.
        """
        tree = parse_source(source)
        total_lines = len(source.splitlines())
        complexity = calculate_complexity(tree)

        classes = self._extract_classes(tree)
        functions = self._extract_top_level_functions(tree)
        imports = self._extract_imports(tree)

        return AnalysisResult(
            file_path=file_path,
            classes=classes,
            functions=functions,
            imports=imports,
            total_lines=total_lines,
            complexity_score=complexity,
        )

    def _extract_classes(self, tree: ast.Module) -> list[ClassInfo]:
        """Extract class definitions from an AST module.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of ClassInfo objects for each class defined in the module.
        """
        classes: list[ClassInfo] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                methods = [
                    n.name
                    for n in ast.walk(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                decorators = get_decorator_names(node)
                is_abstract = any(b in {"ABC", "abc.ABC"} for b in bases) or "abstractmethod" in [
                    d
                    for m in ast.walk(node)
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                    for d in get_decorator_names(m)
                ]
                classes.append(
                    ClassInfo(
                        name=node.name,
                        bases=bases,
                        methods=methods,
                        decorators=decorators,
                        line_number=node.lineno,
                        is_abstract=is_abstract,
                    )
                )
        return classes

    def _extract_top_level_functions(self, tree: ast.Module) -> list[FunctionInfo]:
        """Extract top-level function definitions from an AST module.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of FunctionInfo objects for each top-level function.
        """
        functions: list[FunctionInfo] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._build_function_info(node))
        return functions

    def _build_function_info(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionInfo:
        """Build a FunctionInfo from a function AST node.

        Args:
            node: An AST function definition node.

        Returns:
            A FunctionInfo with all extracted information.
        """
        params = [arg.arg for arg in node.args.args]
        return_type = get_annotation_string(node.returns)
        decorators = get_decorator_names(node)
        has_type_hints = (
            any(arg.annotation is not None for arg in node.args.args) or node.returns is not None
        )
        return FunctionInfo(
            name=node.name,
            parameters=params,
            return_type=return_type,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            line_number=node.lineno,
            has_type_hints=has_type_hints,
        )

    def _extract_imports(self, tree: ast.Module) -> list[ImportInfo]:
        """Extract import statements from an AST module.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of ImportInfo objects for each import statement.
        """
        imports: list[ImportInfo] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            alias=alias.asname,
                            is_from_import=False,
                            line_number=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append(
                    ImportInfo(
                        module=module,
                        names=names,
                        is_from_import=True,
                        line_number=node.lineno,
                    )
                )
        return imports
