#!/usr/bin/env python3
"""
ACE Benchmark Suite Demo

Demonstrates comprehensive benchmark validation for self-learning code generation.

Shows:
- Running standardized benchmark tasks
- Measuring learning effectiveness
- Comparing performance across difficulty levels
- Tracking improvement over time

Run with: python examples/ace_benchmark_demo.py
"""

import asyncio
import logging
from pathlib import Path

from tta_dev_primitives.ace import BenchmarkSuite, SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_benchmark_suite():
    """Run the complete benchmark suite."""

    print("🎯 ACE Benchmark Suite Demo")
    print("=" * 70)
    print("Validating self-learning code generation across multiple tasks\n")

    # Initialize learner
    learner = SelfLearningCodePrimitive(playbook_file=Path("benchmark_playbook.json"))

    # Initialize benchmark suite
    suite = BenchmarkSuite()

    print(f"📋 Benchmark Suite: {len(suite.tasks)} tasks")
    print("   • Easy: 3 tasks")
    print("   • Medium: 3 tasks")
    print("   • Hard: 2 tasks")
    print()

    # Create context
    context = WorkflowContext(correlation_id="benchmark-suite-demo")

    # Run all benchmarks
    print("🚀 Running benchmarks...\n")
    results = await suite.run_all_benchmarks(learner, context)

    # Print summary
    suite.print_summary(results)

    # Export results
    output_file = Path("benchmark_results.json")
    suite.export_results(results, output_file)

    return results, learner


async def demonstrate_learning_progression():
    """Show how performance improves with repeated benchmark runs."""

    print("\n" + "=" * 70)
    print("📈 Learning Progression Demo")
    print("=" * 70)
    print("Running benchmarks multiple times to show learning improvement\n")

    learner = SelfLearningCodePrimitive(playbook_file=Path("progression_playbook.json"))
    suite = BenchmarkSuite()
    context = WorkflowContext(correlation_id="progression-demo")

    # Run benchmarks 3 times
    all_runs = []
    for run in range(1, 4):
        print(f"\n{'=' * 70}")
        print(f"🔄 Run {run}/3")
        print(f"{'=' * 70}")
        print(f"Current playbook size: {learner.playbook_size} strategies")
        print(f"Current success rate: {learner.success_rate:.1%}\n")

        results = await suite.run_all_benchmarks(learner, context)
        all_runs.append(results)

        # Quick summary
        successful = sum(1 for r in results if r.success)
        print(f"\n✅ Run {run} complete: {successful}/{len(results)} tasks successful")

    # Compare runs
    print("\n" + "=" * 70)
    print("📊 Learning Progression Analysis")
    print("=" * 70)

    for i, results in enumerate(all_runs, 1):
        successful = sum(1 for r in results if r.success)
        total_strategies = sum(r.strategies_learned for r in results)
        avg_time = sum(r.execution_time for r in results) / len(results)

        print(f"\nRun {i}:")
        print(f"  Success rate: {successful}/{len(results)} ({successful / len(results):.1%})")
        print(f"  Strategies learned: {total_strategies}")
        print(f"  Avg execution time: {avg_time:.2f}s")

    # Show improvement
    if len(all_runs) >= 2:
        first_success = sum(1 for r in all_runs[0] if r.success)
        last_success = sum(1 for r in all_runs[-1] if r.success)
        improvement = last_success - first_success

        print(f"\n💡 Improvement: {improvement:+d} tasks ({improvement / len(results):+.1%})")

    return all_runs


async def main():
    """Run the complete benchmark demo."""

    print("🚀 ACE Benchmark Validation System\n")

    try:
        # Run single benchmark suite
        results, learner = await run_benchmark_suite()

        print(f"\n📚 Final playbook size: {learner.playbook_size} strategies")
        print(f"🎯 Final success rate: {learner.success_rate:.1%}")

        # Demonstrate learning progression
        await demonstrate_learning_progression()

        print("\n✨ Demo Complete!")
        print("\nKey Insights:")
        print("• Benchmarks provide standardized validation")
        print("• Learning improves performance over time")
        print("• Strategies accumulate and transfer across tasks")
        print("• Metrics enable data-driven optimization")

        print("\nNext Steps:")
        print("• Review benchmark_results.json for detailed analysis")
        print("• Run benchmarks periodically to track progress")
        print("• Add custom benchmarks for your use cases")
        print("• Compare different learning configurations")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("Make sure E2B_API_KEY is set in your environment")


if __name__ == "__main__":
    asyncio.run(main())
