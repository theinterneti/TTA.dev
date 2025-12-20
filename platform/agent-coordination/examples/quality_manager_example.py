"""
Simple Quality Manager Example

Demonstrates how to use QualityManager with the actual API.

This example shows quality operations:
- coverage_analysis: Analyze test coverage
- quality_gate: Enforce quality standards
- generate_report: Create quality reports

Requirements:
- pytest installed
- tta-agent-coordination package installed
"""

import asyncio

from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.managers import (
    QualityManager,
    QualityManagerConfig,
    QualityOperation,
)


async def example_coverage_analysis():
    """Example: Analyze test coverage."""
    print("\n" + "=" * 80)
    print("Example 1: Coverage Analysis")
    print("=" * 80 + "\n")

    # Configure manager
    config = QualityManagerConfig(
        pytest_executable="python",  # "python" or "uv"
        default_test_strategy="coverage",
        min_coverage_percent=80.0,
        coverage_output_format="html",
        generate_reports=True,
    )

    manager = QualityManager(config)

    try:
        # Create operation
        operation = QualityOperation(
            operation="coverage_analysis",
            test_path="tests/",
            test_strategy="coverage",
            output_format="html",
        )

        # Execute
        context = WorkflowContext(correlation_id="coverage-example")
        result = await manager.execute(operation, context)

        # Print results
        print(f"Success: {result.success}")
        print(f"Operation: {result.operation}")

        if result.coverage_data:
            print("\nCoverage Data:")
            print(f"  Total: {result.coverage_data.get('total_coverage', 'N/A')}%")

        if result.report_path:
            print(f"\nReport: {result.report_path}")

    finally:
        manager.close()  # Note: close() is NOT async


async def example_quality_gate():
    """Example: Enforce quality gates."""
    print("\n" + "=" * 80)
    print("Example 2: Quality Gate Enforcement")
    print("=" * 80 + "\n")

    config = QualityManagerConfig(
        pytest_executable="python",
        min_coverage_percent=80.0,
        max_failures=0,
        generate_reports=True,
    )

    manager = QualityManager(config)

    try:
        # Quality gate operation
        operation = QualityOperation(
            operation="quality_gate",
            test_path="tests/",
            coverage_threshold=85.0,  # Override minimum
            max_failures=0,  # No failures allowed
        )

        context = WorkflowContext(correlation_id="quality-gate-example")
        result = await manager.execute(operation, context)

        print(f"Quality Gate Passed: {result.quality_gate_passed}")
        print(f"Overall Success: {result.success}")

        if result.quality_issues:
            print("\nQuality Issues:")
            for issue in result.quality_issues:
                print(f"  - {issue}")

        if result.test_results:
            print("\nTest Results:")
            print(f"  Total: {result.test_results.get('total', 'N/A')}")
            print(f"  Passed: {result.test_results.get('passed', 'N/A')}")
            print(f"  Failed: {result.test_results.get('failed', 'N/A')}")

    finally:
        manager.close()


async def example_generate_report():
    """Example: Generate quality report."""
    print("\n" + "=" * 80)
    print("Example 3: Generate Quality Report")
    print("=" * 80 + "\n")

    config = QualityManagerConfig(
        pytest_executable="python",
        coverage_output_format="json",
        generate_reports=True,
    )

    manager = QualityManager(config)

    try:
        operation = QualityOperation(
            operation="generate_report",
            test_path="tests/",
            output_format="json",
            include_trends=False,  # Don't include historical data
        )

        context = WorkflowContext(correlation_id="report-example")
        result = await manager.execute(operation, context)

        print(f"Report Generated: {result.success}")
        if result.report_path:
            print(f"Report Location: {result.report_path}")

    finally:
        manager.close()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  Quality Manager Examples")
    print("  Real API Demonstration")
    print("=" * 80)

    print("\n⚠️  Note: These examples use the ACTUAL QualityManager API")
    print("   Ensure pytest is installed and tests exist\n")

    # Run examples
    await example_coverage_analysis()
    await example_quality_gate()
    await example_generate_report()

    print("\n" + "=" * 80)
    print("  Examples Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
