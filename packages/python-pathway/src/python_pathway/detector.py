"""Pattern detection for Python code analysis."""

from __future__ import annotations

import ast

from .models import PatternMatch
from .utils import load_source, parse_source


class PatternDetector:
    """Detect common patterns and anti-patterns in Python source files.

    Detects:
    - Patterns: singleton, factory, decorator_pattern, context_manager, async_patterns
    - Anti-patterns: mutable_default_argument, bare_except, missing_type_hints, star_import

    Example:
        ```python
        detector = PatternDetector()
        patterns = detector.detect_patterns("path/to/file.py")
        for pattern in patterns:
            print(f"{pattern.name}: line {pattern.line_number}")
        ```
    """

    def detect_patterns(self, file_path: str) -> list[PatternMatch]:
        """Detect patterns in a Python source file.

        Args:
            file_path: Path to the Python source file.

        Returns:
            A list of PatternMatch objects for each detected pattern.
        """
        source = load_source(file_path)
        return self.detect_from_source(source)

    def detect_from_source(self, source: str) -> list[PatternMatch]:
        """Detect patterns in Python source code.

        Args:
            source: Python source code as a string.

        Returns:
            A list of PatternMatch objects.
        """
        tree = parse_source(source)
        patterns: list[PatternMatch] = []
        patterns.extend(self._detect_singleton(tree))
        patterns.extend(self._detect_factory(tree))
        patterns.extend(self._detect_decorator_pattern(tree))
        patterns.extend(self._detect_context_manager(tree))
        patterns.extend(self._detect_async_patterns(tree))
        patterns.extend(self._detect_mutable_default_args(tree))
        patterns.extend(self._detect_bare_except(tree))
        patterns.extend(self._detect_missing_type_hints(tree))
        patterns.extend(self._detect_star_imports(tree))
        return patterns

    # -------------------------------------------------------------------------
    # Pattern detectors
    # -------------------------------------------------------------------------

    def _detect_singleton(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect singleton pattern: class with _instance class attribute and __new__ method.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each detected singleton class.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            has_new = any(
                isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "__new__"
                for n in ast.walk(node)
            )
            has_instance_attr = any(
                isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id.startswith("_instance") for t in n.targets)
                for n in ast.walk(node)
            )
            if has_new and has_instance_attr:
                results.append(
                    PatternMatch(
                        name="singleton",
                        category="pattern",
                        description=f"Singleton pattern detected in class '{node.name}'",
                        line_number=node.lineno,
                        severity="info",
                    )
                )
        return results

    def _detect_factory(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect factory pattern: functions/methods named create_* or *_factory.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each detected factory function.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name.lower()
                if name.startswith("create_") or name.endswith("_factory") or name == "create":
                    results.append(
                        PatternMatch(
                            name="factory",
                            category="pattern",
                            description=f"Factory pattern detected in function '{node.name}'",
                            line_number=node.lineno,
                            severity="info",
                        )
                    )
        return results

    def _detect_decorator_pattern(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect decorator pattern: functions that return inner wrapper functions.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each detected decorator function.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Heuristic: function contains a nested function and returns it
            inner_funcs = [
                n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            has_return_of_inner = any(
                isinstance(n, ast.Return)
                and isinstance(n.value, ast.Name)
                and any(n.value.id == f.name for f in inner_funcs)
                for n in ast.walk(node)
            )
            if inner_funcs and has_return_of_inner:
                results.append(
                    PatternMatch(
                        name="decorator_pattern",
                        category="pattern",
                        description=f"Decorator pattern detected in function '{node.name}'",
                        line_number=node.lineno,
                        severity="info",
                    )
                )
        return results

    def _detect_context_manager(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect context manager pattern: classes with __enter__ and __exit__ methods.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each detected context manager class.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            method_names = {
                n.name
                for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if "__enter__" in method_names and "__exit__" in method_names:
                results.append(
                    PatternMatch(
                        name="context_manager",
                        category="pattern",
                        description=f"Context manager pattern in class '{node.name}'",
                        line_number=node.lineno,
                        severity="info",
                    )
                )
        return results

    def _detect_async_patterns(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect async/await patterns: async functions at module level.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each top-level async function.
        """
        results: list[PatternMatch] = []
        for node in tree.body:
            if isinstance(node, ast.AsyncFunctionDef):
                results.append(
                    PatternMatch(
                        name="async_pattern",
                        category="pattern",
                        description=f"Async pattern in function '{node.name}'",
                        line_number=node.lineno,
                        severity="info",
                    )
                )
        return results

    # -------------------------------------------------------------------------
    # Anti-pattern detectors
    # -------------------------------------------------------------------------

    def _detect_mutable_default_args(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect mutable default arguments (list, dict, set literals as defaults).

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each function with mutable defaults.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for default in node.args.defaults + node.args.kw_defaults:
                if default is None:
                    continue
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    results.append(
                        PatternMatch(
                            name="mutable_default_argument",
                            category="anti_pattern",
                            description=(f"Mutable default argument in function '{node.name}'"),
                            line_number=node.lineno,
                            severity="warning",
                        )
                    )
                    break
        return results

    def _detect_bare_except(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect bare except clauses (except: without exception type).

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each bare except clause.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                results.append(
                    PatternMatch(
                        name="bare_except",
                        category="anti_pattern",
                        description="Bare except clause detected",
                        line_number=node.lineno,
                        severity="warning",
                    )
                )
        return results

    def _detect_missing_type_hints(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect public functions missing type hints on parameters or return type.

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each public function missing type hints.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            missing = node.returns is None or any(
                arg.annotation is None for arg in node.args.args if arg.arg != "self"
            )
            if missing:
                results.append(
                    PatternMatch(
                        name="missing_type_hints",
                        category="anti_pattern",
                        description=f"Missing type hints in public function '{node.name}'",
                        line_number=node.lineno,
                        severity="warning",
                    )
                )
        return results

    def _detect_star_imports(self, tree: ast.Module) -> list[PatternMatch]:
        """Detect star imports (from module import *).

        Args:
            tree: The parsed AST module.

        Returns:
            A list of PatternMatch objects for each star import.
        """
        results: list[PatternMatch] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        results.append(
                            PatternMatch(
                                name="star_import",
                                category="anti_pattern",
                                description=f"Star import from '{node.module}'",
                                line_number=node.lineno,
                                severity="warning",
                            )
                        )
        return results
