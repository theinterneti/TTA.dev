"""Basic usage example for PythonAnalyzer.

This example shows how to analyze a Python source file using PythonAnalyzer
directly without any workflow context.

Usage:
    uv run python examples/basic_analysis.py
"""

from __future__ import annotations

import sys

from python_pathway import PatternDetector, PythonAnalyzer


def main() -> None:
    """Run a basic analysis on a given file (or this script itself)."""
    file_path = sys.argv[1] if len(sys.argv) > 1 else __file__

    print(f"Analyzing: {file_path}\n")

    # -------------------------------------------------------------------------
    # Structural analysis
    # -------------------------------------------------------------------------
    analyzer = PythonAnalyzer()
    result = analyzer.analyze_file(file_path)

    print(f"Total lines:      {result.total_lines}")
    print(f"Complexity score: {result.complexity_score}")

    if result.classes:
        print(f"\nClasses ({len(result.classes)}):")
        for cls in result.classes:
            abstract = " [abstract]" if cls.is_abstract else ""
            bases = f"({', '.join(cls.bases)})" if cls.bases else ""
            print(f"  line {cls.line_number:3d}  {cls.name}{bases}{abstract}")
            if cls.methods:
                for m in cls.methods:
                    print(f"               - {m}()")

    if result.functions:
        print(f"\nTop-level functions ({len(result.functions)}):")
        for func in result.functions:
            async_marker = "async " if func.is_async else ""
            hints = " [typed]" if func.has_type_hints else ""
            print(f"  line {func.line_number:3d}  {async_marker}{func.name}(){hints}")

    if result.imports:
        print(f"\nImports ({len(result.imports)}):")
        for imp in result.imports:
            if imp.is_from_import:
                names = ", ".join(imp.names)
                print(f"  line {imp.line_number:3d}  from {imp.module} import {names}")
            else:
                alias = f" as {imp.alias}" if imp.alias else ""
                print(f"  line {imp.line_number:3d}  import {imp.module}{alias}")

    # -------------------------------------------------------------------------
    # Pattern detection
    # -------------------------------------------------------------------------
    detector = PatternDetector()
    patterns = detector.detect_patterns(file_path)

    if patterns:
        print(f"\nDetected patterns/anti-patterns ({len(patterns)}):")
        for p in sorted(patterns, key=lambda x: x.line_number):
            icon = "✓" if p.category == "pattern" else "⚠"
            print(f"  {icon} [{p.severity:7s}] line {p.line_number:3d}  {p.description}")
    else:
        print("\nNo patterns detected.")


if __name__ == "__main__":
    main()
