"""Pydantic models for Python code analysis results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImportInfo(BaseModel):
    """Information about an import statement."""

    module: str
    names: list[str] = Field(default_factory=list)
    alias: str | None = None
    is_from_import: bool = False
    line_number: int = 0


class ClassInfo(BaseModel):
    """Information about a class definition."""

    name: str
    bases: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    line_number: int = 0
    is_abstract: bool = False


class FunctionInfo(BaseModel):
    """Information about a function/method definition."""

    name: str
    parameters: list[str] = Field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = Field(default_factory=list)
    is_async: bool = False
    line_number: int = 0
    has_type_hints: bool = False


class PatternMatch(BaseModel):
    """A detected pattern or anti-pattern."""

    name: str
    category: str  # "pattern" or "anti_pattern"
    description: str
    line_number: int = 0
    severity: str = "info"  # "info", "warning", "error"


class AnalysisResult(BaseModel):
    """Complete analysis result for a Python source file."""

    file_path: str
    classes: list[ClassInfo] = Field(default_factory=list)
    functions: list[FunctionInfo] = Field(default_factory=list)
    imports: list[ImportInfo] = Field(default_factory=list)
    total_lines: int = 0
    complexity_score: float = 0.0
    patterns: list[PatternMatch] = Field(default_factory=list)
