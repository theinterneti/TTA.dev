"""Workflow integration example for CodeAnalysisPrimitive.

This example shows how to use CodeAnalysisPrimitive and
PatternDetectionPrimitive within a TTA.dev workflow context.

Usage:
    uv run python examples/workflow_integration.py [path/to/file.py]
"""

from __future__ import annotations

import asyncio
import sys

from tta_dev_primitives import WorkflowContext

from python_pathway import CodeAnalysisPrimitive, PatternDetectionPrimitive


async def run_analysis_workflow(file_path: str) -> None:
    """Run a complete code analysis workflow on a Python file.

    Args:
        file_path: Path to the Python file to analyze.
    """
    context = WorkflowContext(workflow_id="code-analysis-demo")

    print(f"Starting workflow: {context.workflow_id}")
    print(f"Analyzing: {file_path}\n")

    # -------------------------------------------------------------------------
    # Step 1: Full code analysis (structure + patterns)
    # -------------------------------------------------------------------------
    analysis_primitive = CodeAnalysisPrimitive(include_patterns=True)
    result = await analysis_primitive.execute(file_path, context)

    print("=== Structural Analysis ===")
    print(f"Lines:      {result.total_lines}")
    print(f"Complexity: {result.complexity_score}")
    print(f"Classes:    {len(result.classes)}")
    print(f"Functions:  {len(result.functions)}")
    print(f"Imports:    {len(result.imports)}")

    # -------------------------------------------------------------------------
    # Step 2: Dedicated pattern detection (same primitive, different focus)
    # -------------------------------------------------------------------------
    pattern_primitive = PatternDetectionPrimitive()
    patterns = await pattern_primitive.execute(file_path, context)

    design_patterns = [p for p in patterns if p.category == "pattern"]
    anti_patterns = [p for p in patterns if p.category == "anti_pattern"]

    print("\n=== Pattern Report ===")
    print(f"Design patterns:  {len(design_patterns)}")
    print(f"Anti-patterns:    {len(anti_patterns)}")

    if design_patterns:
        print("\nDetected design patterns:")
        for p in design_patterns:
            print(f"  ✓ {p.name} — {p.description} (line {p.line_number})")

    if anti_patterns:
        print("\nDetected anti-patterns:")
        for p in anti_patterns:
            print(f"  ⚠ [{p.severity}] {p.name} — {p.description} (line {p.line_number})")
    else:
        print("\n✓ No anti-patterns found.")

    print("\nWorkflow completed successfully.")


def main() -> None:
    """Entry point."""
    file_path = sys.argv[1] if len(sys.argv) > 1 else __file__
    asyncio.run(run_analysis_workflow(file_path))


if __name__ == "__main__":
    main()
