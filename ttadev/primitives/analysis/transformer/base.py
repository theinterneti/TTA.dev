"""Data classes for AST-based code transformation."""

import ast
from dataclasses import dataclass
from typing import Any


@dataclass
class TransformResult:
    """Result of a code transformation."""

    original_code: str
    transformed_code: str
    changes_made: list[dict[str, Any]]
    imports_added: list[str]
    success: bool
    error: str | None = None


@dataclass
class FunctionInfo:
    """Information about a function to transform."""

    name: str
    is_async: bool
    args: list[str]
    body: list[ast.stmt]
    decorators: list[ast.expr]
    returns: ast.expr | None
    lineno: int
    col_offset: int


# =============================================================================
# AST Node Transformers - Actually rewrite function bodies
# =============================================================================
