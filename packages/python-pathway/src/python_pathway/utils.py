"""Utility functions for Python code analysis."""

from __future__ import annotations

import ast


def load_source(file_path: str) -> str:
    """Read source code from a file.

    Args:
        file_path: Path to the Python source file.

    Returns:
        The source code as a string.
    """
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def parse_source(source: str) -> ast.Module:
    """Parse Python source code into an AST.

    Args:
        source: Python source code as a string.

    Returns:
        The parsed AST module.

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    return ast.parse(source)


def get_decorator_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> list[str]:
    """Extract decorator names from a function or class node.

    Args:
        node: An AST function or class node.

    Returns:
        A list of decorator name strings.
    """
    names: list[str] = []
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            names.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            names.append(f"{ast.unparse(decorator)}")
        elif isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(ast.unparse(func))
    return names


def get_annotation_string(annotation: ast.expr | None) -> str | None:
    """Convert an AST annotation to a string representation.

    Args:
        annotation: An AST expression node representing a type annotation,
            or None if no annotation is present.

    Returns:
        A string representation of the annotation, or None.
    """
    if annotation is None:
        return None
    return ast.unparse(annotation)


def calculate_complexity(tree: ast.Module) -> float:
    """Calculate a basic complexity score for an AST module.

    Score = 1 (base) + number of branches + number of loops
    + number of functions + number of classes.

    Args:
        tree: The parsed AST module.

    Returns:
        A floating-point complexity score (rounded to 2 decimal places).
    """
    score = 1.0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.ExceptHandler, ast.With, ast.Assert)):
            score += 1.0
        elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            score += 1.0
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score += 0.5
        elif isinstance(node, ast.ClassDef):
            score += 0.5
    return round(score, 2)
