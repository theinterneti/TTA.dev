#!/usr/bin/env python3
"""
ACE Metrics Tracking Demo

Demonstrates comprehensive metrics collection and analysis for self-learning
code generation primitives.

Shows:
- Learning curve tracking
- Task type performance analysis
- Strategy effectiveness measurement
- Exportable metrics for visualization

Run with: python examples/ace_metrics_demo.py
"""

import asyncio
import logging
import time
from pathlib import Path

from tta_dev_primitives.ace import (
    LearningMetrics,
    MetricsTracker,
    SelfLearningCodePrimitive,
)
from tta_dev_primitives.core.base import WorkflowContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_learning_sessions_with_metrics():
    """Run multiple learning sessions and track metrics."""

    print("📊 ACE Metrics Tracking Demo")
    print("=" * 60)

    # Initialize metrics tracker
    tracker = MetricsTracker(metrics_file=Path("ace_metrics_demo.json"))

    # Initialize learner
    learner = SelfLearningCodePrimitive(playbook_file=Path("metrics_demo_playbook.json"))

    context = WorkflowContext(correlation_id="metrics-demo")

    # Simulate different task types
    task_scenarios = [
        ("fibonacci_generation", "Create a function to calculate fibonacci numbers"),
        ("prime_checking", "Create a function to check if a number is prime"),
        ("fibonacci_generation", "Create a function to calculate fibonacci with memoization"),
        ("test_generation", "Generate pytest test for fibonacci function"),
        ("prime_checking", "Create a function to find all primes up to N"),
        ("test_generation", "Generate pytest test for prime checking"),
        ("data_processing", "Create a function to process CSV data"),
        ("fibonacci_generation", "Create optimized fibonacci function"),
    ]

    print(f"\nRunning {len(task_scenarios)} learning sessions...\n")

    for i, (task_type, task_description) in enumerate(task_scenarios, 1):
        print(f"Session {i}/{len(task_scenarios)}: {task_type}")

        start_time = time.time()

        try:
            result = await learner.execute(
                {"task": task_description, "language": "python", "max_iterations": 3}, context
            )

            execution_time = time.time() - start_time

            # Record metrics
            metrics = LearningMetrics(
                timestamp=time.time(),
                task_type=task_type,
                execution_success=result["execution_success"],
                strategies_used=len(learner.playbook.strategies),
                strategies_learned=result["strategies_learned"],
                iteration_count=3,  # max_iterations
                execution_time=execution_time,
                playbook_size=result["playbook_size"],
                success_rate=learner.success_rate,
                improvement_score=result["improvement_score"],
                error_type=None if result["execution_success"] else "execution_error",
                metadata={"task_description": task_description},
            )

            tracker.record_session(metrics)

            status = "✅" if result["execution_success"] else "❌"
            print(f"  {status} Success: {result['execution_success']}")
            print(f"  📚 Strategies learned: {result['strategies_learned']}")
            print(f"  ⏱️  Execution time: {execution_time:.2f}s")
            print()

        except Exception as e:
            logger.error(f"Session {i} failed: {e}")
            print(f"  ❌ Failed: {e}\n")

    # Display metrics summary
    tracker.print_summary()

    # Export for visualization
    viz_file = Path("ace_metrics_visualization.json")
    tracker.export_for_visualization(viz_file)
    print(f"\n📁 Metrics exported to: {viz_file}")
    print("   Use this file for visualization in dashboards/notebooks")

    return tracker


async def demonstrate_metrics_analysis():
    """Show how to analyze metrics programmatically."""

    print("\n" + "=" * 60)
    print("🔍 Metrics Analysis Demo")
    print("=" * 60)

    # Load existing metrics
    tracker = MetricsTracker(metrics_file=Path("ace_metrics_demo.json"))

    if not tracker.sessions:
        print("\nNo metrics found. Run learning sessions first.")
        return

    metrics = tracker.get_aggregated_metrics()

    print("\n📈 Learning Curve Analysis:")
    print(f"  Total sessions: {metrics.total_executions}")
    print(f"  Overall success rate: {metrics.success_rate:.1%}")
    print(f"  Improvement rate: {metrics.improvement_rate:+.1%}")

    print("\n🎯 Task Type Performance:")
    for task_type, breakdown in metrics.task_type_breakdown.items():
        print(f"\n  {task_type}:")
        print(f"    Sessions: {breakdown['count']}")
        print(f"    Success rate: {breakdown['success_rate']:.1%}")
        print(f"    Strategies learned: {breakdown['strategies_learned']}")
        print(f"    Avg iterations: {breakdown['avg_iterations']:.1f}")

    print("\n💡 Insights:")
    # Find best performing task type
    best_task = max(metrics.task_type_breakdown.items(), key=lambda x: x[1]["success_rate"])
    print(f"  Best performing task: {best_task[0]} ({best_task[1]['success_rate']:.1%})")

    # Find most learning-intensive task
    most_learning = max(
        metrics.task_type_breakdown.items(), key=lambda x: x[1]["strategies_learned"]
    )
    print(
        f"  Most learning: {most_learning[0]} ({most_learning[1]['strategies_learned']} strategies)"
    )


async def main():
    """Run the complete metrics demo."""

    print("🚀 ACE Metrics Tracking System Demo\n")

    try:
        # Run learning sessions with metrics
        await run_learning_sessions_with_metrics()

        # Analyze metrics
        await demonstrate_metrics_analysis()

        print("\n✨ Demo Complete!")
        print("\nNext steps:")
        print("• Review ace_metrics_visualization.json for detailed data")
        print("• Use metrics to identify improvement opportunities")
        print("• Track learning progress over time")
        print("• Compare different task types and strategies")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
