"""CodeGraphPrimitive types — CGCOp enum, CodeGraphQuery, ImpactReport."""

from __future__ import annotations

import enum
from typing import Literal, TypedDict


class CGCOp(enum.Enum):
    """Operations that CodeGraphPrimitive can execute against the code graph."""

    find_code = "find_code"
    get_relationships = "get_relationships"
    get_complexity = "get_complexity"
    find_tests = "find_tests"
    raw_cypher = "raw_cypher"


class CodeGraphQuery(TypedDict, total=False):
    """Input for CodeGraphPrimitive.

    All fields are optional at the TypedDict level, but:
    - ``operations`` is always required at runtime.
    - ``target`` is required for all ops except ``raw_cypher``.
    - ``cypher`` is required for ``CGCOp.raw_cypher``.
    """

    target: str  # function/class name (substring match)
    operations: list[CGCOp]  # required
    depth: int  # default 2, clamped to 5
    cypher: str  # required for CGCOp.raw_cypher
    repo_path: str | None  # optional: filter results to this repo path


class ImpactReport(TypedDict):
    """Output from CodeGraphPrimitive."""

    target: str
    callers: list[str]  # "FuncName (path:line)"
    dependencies: list[str]  # functions called by target
    related_tests: list[str]  # file paths containing "/test" or "test_"
    complexity: float  # cyclomatic complexity; 0.0 if not queried
    risk: Literal["low", "medium", "high"]
    summary: str  # human/LLM-readable paragraph
    cgc_available: bool  # False when FalkorDB was unreachable
