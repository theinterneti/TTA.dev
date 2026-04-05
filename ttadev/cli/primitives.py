"""CLI subcommands for discovering and inspecting TTA.dev primitives.

Provides:
    tta primitives list          — grouped table of all built-in primitives
    tta primitives info <name>   — module path, docstring, and usage example
"""

from __future__ import annotations

import argparse
import inspect
import sys
import textwrap
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Primitive catalogue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PrimitiveEntry:
    """Metadata for a single primitive shown in the catalogue."""

    name: str
    module: str
    one_liner: str
    category: str


# Canonical category ordering shown to users.
_CATEGORY_ORDER = [
    "Composition",
    "Reliability",
    "Caching",
    "Safety",
    "LLM",
    "Streaming",
    "Code Graph",
    "Collaboration",
    "Memory",
    "Testing",
]

# fmt: off
_CATALOGUE: list[_PrimitiveEntry] = [
    # Composition
    _PrimitiveEntry("SequentialPrimitive",    "ttadev.primitives.core.sequential",       "Chain primitives in order",                  "Composition"),
    _PrimitiveEntry("ParallelPrimitive",      "ttadev.primitives.core.parallel",         "Run primitives concurrently",                "Composition"),
    _PrimitiveEntry("ConditionalPrimitive",   "ttadev.primitives.core.conditional",      "Branch on a predicate",                      "Composition"),
    _PrimitiveEntry("RouterPrimitive",        "ttadev.primitives.core.routing",          "Route to one of N primitives",               "Composition"),
    # Reliability
    _PrimitiveEntry("RetryPrimitive",         "ttadev.primitives.recovery.retry",        "Retry on transient failures",                "Reliability"),
    _PrimitiveEntry("TimeoutPrimitive",       "ttadev.primitives.recovery.timeout",      "Cancel after N seconds",                     "Reliability"),
    _PrimitiveEntry("FallbackPrimitive",      "ttadev.primitives.recovery.fallback",     "Fall back to a secondary primitive",         "Reliability"),
    _PrimitiveEntry("CompensationPrimitive",  "ttadev.primitives.recovery.compensation", "Roll back side-effects on failure",          "Reliability"),
    # Caching
    _PrimitiveEntry("CachePrimitive",         "ttadev.primitives.performance.cache",     "Memoize outputs by key",                     "Caching"),
    # Safety
    _PrimitiveEntry("SafetyGatePrimitive",    "ttadev.primitives.safety",                "Enforce content-safety rules",               "Safety"),
    # LLM
    _PrimitiveEntry("UniversalLLMPrimitive",  "ttadev.primitives.llm",                   "Provider-agnostic LLM calls",                "LLM"),
    # Streaming
    _PrimitiveEntry("StreamingPrimitive",     "ttadev.primitives.streaming",             "Stream tokens as they arrive",               "Streaming"),
    # Code Graph
    _PrimitiveEntry("CodeGraphPrimitive",     "ttadev.primitives.code_graph",            "Query the CGC code knowledge graph",         "Code Graph"),
    # Collaboration
    _PrimitiveEntry("GitCollaborationPrimitive", "ttadev.primitives.collaboration",      "Coordinate multi-agent git workflows",        "Collaboration"),
    # Memory
    _PrimitiveEntry("AgentMemory",            "ttadev.primitives.memory",                "Persist and retrieve agent memories",        "Memory"),
    # Testing
    _PrimitiveEntry("MockPrimitive",          "ttadev.primitives.testing.mocks",         "Return static or dynamic test values",       "Testing"),
]
# fmt: on

_BY_NAME: dict[str, _PrimitiveEntry] = {e.name: e for e in _CATALOGUE}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_class(entry: _PrimitiveEntry) -> type | None:
    """Return the class for *entry* from ``ttadev.primitives``, or None.

    All built-in primitives are re-exported from the top-level package, so
    we can resolve them with a single ``getattr`` — no dynamic module path
    needed, and no untrusted input is ever passed to an import call.
    """
    try:
        import ttadev.primitives as _prims  # noqa: PLC0415

        return getattr(_prims, entry.name, None)  # type: ignore[return-value]
    except Exception:  # noqa: BLE001
        return None


def _first_paragraph(doc: str) -> str:
    """Return the first non-empty paragraph of a docstring."""
    doc = inspect.cleandoc(doc)
    paragraphs = doc.split("\n\n")
    return paragraphs[0].strip()


def _extract_example(doc: str) -> str | None:
    """Return the text between the first ```python / ``` fence, or None."""
    cleaned = inspect.cleandoc(doc)
    in_block = False
    lines: list[str] = []
    for line in cleaned.splitlines():
        if line.strip().startswith("```python"):
            in_block = True
            continue
        if in_block:
            if line.strip() == "```":
                break
            lines.append(line)
    return "\n".join(lines) if lines else None


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


def list_primitives(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Implement ``tta primitives list``.

    Prints a grouped table of all built-in primitives and exits.
    """
    # Group entries by category while preserving canonical order.
    groups: dict[str, list[_PrimitiveEntry]] = {cat: [] for cat in _CATEGORY_ORDER}
    for entry in _CATALOGUE:
        groups.setdefault(entry.category, []).append(entry)

    print("Available primitives (ttadev.primitives)\n")
    for category in _CATEGORY_ORDER:
        entries = groups.get(category, [])
        if not entries:
            continue
        print(f"  {category}")
        name_width = max(len(e.name) for e in entries) + 2
        for e in entries:
            print(f"    {e.name:<{name_width}}{e.one_liner}")
        print()

    print("Run `tta primitives info <name>` for usage examples.")
    return 0


def info_primitive(args: argparse.Namespace) -> int:
    """Implement ``tta primitives info <name>``.

    Shows module path, description, and usage example for the named primitive.
    """
    name: str = args.primitive_name
    entry = _BY_NAME.get(name)
    if entry is None:
        # Fuzzy suggestion: case-insensitive match.
        name_lower = name.lower()
        suggestions = [n for n in _BY_NAME if n.lower() == name_lower]
        if not suggestions:
            suggestions = [n for n in _BY_NAME if name_lower in n.lower()]
        msg = f"error: unknown primitive '{name}'"
        if suggestions:
            msg += f"\nDid you mean: {', '.join(suggestions)}"
        else:
            msg += "\nRun `tta primitives list` to see all available primitives."
        print(msg, file=sys.stderr)
        return 1

    cls = _get_class(entry)

    print(f"\n{entry.name}")
    print(f"  Module   : {entry.module}")
    print(f"  Category : {entry.category}")

    doc = (cls.__doc__ if cls and cls.__doc__ else None) or entry.one_liner
    description = _first_paragraph(doc)
    # Wrap description at 72 chars, indented 4 spaces.
    wrapped = textwrap.fill(description, width=72, initial_indent="  ", subsequent_indent="  ")
    print(f"\n  Description:\n{wrapped}")

    if cls and cls.__doc__:
        example = _extract_example(cls.__doc__)
        if example:
            print("\n  Example:")
            for line in example.splitlines():
                print(f"    {line}")

    print()
    return 0


# ---------------------------------------------------------------------------
# Argparse registration (matches the pattern used by control.py, models.py …)
# ---------------------------------------------------------------------------


def register_primitives_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the ``primitives`` subparser tree to *sub*."""
    prim_p = sub.add_parser(
        "primitives",
        help="Discover and inspect built-in TTA.dev primitives",
    )
    prim_sub = prim_p.add_subparsers(dest="primitives_command")

    # primitives list
    prim_sub.add_parser("list", help="Show all available primitives grouped by category")

    # primitives info <name>
    info_p = prim_sub.add_parser("info", help="Show details for a specific primitive")
    info_p.add_argument("primitive_name", metavar="NAME", help="Primitive class name")


def handle_primitives_command(args: argparse.Namespace) -> int:
    """Dispatch ``primitives`` sub-commands and return an exit code."""
    if args.primitives_command == "list":
        return list_primitives(args)
    if args.primitives_command == "info":
        return info_primitive(args)
    # No subcommand — print help.
    import ttadev.cli as _cli_mod  # avoid circular at module level

    _cli_mod._build_parser().parse_args(["primitives", "--help"])
    return 0
