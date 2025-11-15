"""Metrics tracking for ACE learning primitives.

Provides comprehensive metrics collection, analysis, and visualization for
self-learning code generation primitives.

Features:
- Learning curve tracking (success rate over time)
- Strategy effectiveness analysis
- Cost/benefit calculations
- Improvement measurement
- Exportable metrics for visualization
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LearningMetrics:
    """Metrics for a single learning session."""

    timestamp: float
    task_type: str
    execution_success: bool
    strategies_used: int
    strategies_learned: int
    iteration_count: int
    execution_time: float
    playbook_size: int
    success_rate: float
    improvement_score: float
    error_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across multiple sessions."""

    total_executions: int = 0
    successful_executions: int = 0
    total_strategies_learned: int = 0
    total_execution_time: float = 0.0
    average_iterations: float = 0.0
    success_rate: float = 0.0
    improvement_rate: float = 0.0
    task_type_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)
    learning_curve: list[tuple[float, float]] = field(default_factory=list)


class MetricsTracker:
    """Track and analyze ACE learning metrics.

    Example:
        ```python
        tracker = MetricsTracker(metrics_file=Path("ace_metrics.json"))

        # Record a learning session
        tracker.record_session(LearningMetrics(
            timestamp=time.time(),
            task_type="test_generation",
            execution_success=True,
            strategies_used=3,
            strategies_learned=1,
            iteration_count=2,
            execution_time=1.5,
            playbook_size=10,
            success_rate=0.8,
            improvement_score=0.15
        ))

        # Get aggregated metrics
        metrics = tracker.get_aggregated_metrics()
        print(f"Overall success rate: {metrics.success_rate:.1%}")

        # Export for visualization
        tracker.export_for_visualization("metrics_viz.json")
        ```
    """

    def __init__(self, metrics_file: Path | None = None) -> None:
        """Initialize metrics tracker.

        Args:
            metrics_file: Optional file to persist metrics
        """
        self.metrics_file = metrics_file or Path("ace_learning_metrics.json")
        self.sessions: list[LearningMetrics] = []

        # Load existing metrics if available
        if self.metrics_file.exists():
            self._load_metrics()

    def record_session(self, metrics: LearningMetrics) -> None:
        """Record a learning session.

        Args:
            metrics: Metrics from the learning session
        """
        self.sessions.append(metrics)
        self._save_metrics()

    def get_aggregated_metrics(self) -> AggregatedMetrics:
        """Calculate aggregated metrics across all sessions.

        Returns:
            Aggregated metrics with breakdowns and trends
        """
        if not self.sessions:
            return AggregatedMetrics()

        total_executions = len(self.sessions)
        successful_executions = sum(1 for s in self.sessions if s.execution_success)
        total_strategies_learned = sum(s.strategies_learned for s in self.sessions)
        total_execution_time = sum(s.execution_time for s in self.sessions)
        average_iterations = sum(s.iteration_count for s in self.sessions) / total_executions

        # Calculate learning curve (timestamp, success_rate)
        learning_curve = [(s.timestamp, s.success_rate) for s in self.sessions]

        # Calculate improvement rate (change in success rate over time)
        if len(self.sessions) >= 2:
            first_half = self.sessions[: len(self.sessions) // 2]
            second_half = self.sessions[len(self.sessions) // 2 :]
            first_success_rate = sum(1 for s in first_half if s.execution_success) / len(first_half)
            second_success_rate = sum(1 for s in second_half if s.execution_success) / len(
                second_half
            )
            improvement_rate = second_success_rate - first_success_rate
        else:
            improvement_rate = 0.0

        # Task type breakdown
        task_type_breakdown: dict[str, dict[str, Any]] = {}
        for session in self.sessions:
            if session.task_type not in task_type_breakdown:
                task_type_breakdown[session.task_type] = {
                    "count": 0,
                    "successes": 0,
                    "strategies_learned": 0,
                    "avg_iterations": 0.0,
                }

            breakdown = task_type_breakdown[session.task_type]
            breakdown["count"] += 1
            if session.execution_success:
                breakdown["successes"] += 1
            breakdown["strategies_learned"] += session.strategies_learned

        # Calculate averages for task types
        for task_type, breakdown in task_type_breakdown.items():
            task_sessions = [s for s in self.sessions if s.task_type == task_type]
            breakdown["avg_iterations"] = sum(s.iteration_count for s in task_sessions) / len(
                task_sessions
            )
            breakdown["success_rate"] = breakdown["successes"] / breakdown["count"]

        return AggregatedMetrics(
            total_executions=total_executions,
            successful_executions=successful_executions,
            total_strategies_learned=total_strategies_learned,
            total_execution_time=total_execution_time,
            average_iterations=average_iterations,
            success_rate=successful_executions / total_executions,
            improvement_rate=improvement_rate,
            task_type_breakdown=task_type_breakdown,
            learning_curve=learning_curve,
        )

    def export_for_visualization(self, output_file: Path) -> None:
        """Export metrics in format suitable for visualization.

        Creates a JSON file with:
        - Learning curve data (for plotting)
        - Task type breakdowns (for charts)
        - Summary statistics

        Args:
            output_file: Path to export JSON file
        """
        metrics = self.get_aggregated_metrics()

        export_data = {
            "summary": {
                "total_executions": metrics.total_executions,
                "successful_executions": metrics.successful_executions,
                "success_rate": metrics.success_rate,
                "improvement_rate": metrics.improvement_rate,
                "total_strategies_learned": metrics.total_strategies_learned,
                "average_iterations": metrics.average_iterations,
                "total_execution_time": metrics.total_execution_time,
            },
            "learning_curve": [
                {"timestamp": ts, "success_rate": sr} for ts, sr in metrics.learning_curve
            ],
            "task_type_breakdown": metrics.task_type_breakdown,
            "sessions": [
                {
                    "timestamp": s.timestamp,
                    "task_type": s.task_type,
                    "execution_success": s.execution_success,
                    "strategies_used": s.strategies_used,
                    "strategies_learned": s.strategies_learned,
                    "iteration_count": s.iteration_count,
                    "execution_time": s.execution_time,
                    "playbook_size": s.playbook_size,
                    "success_rate": s.success_rate,
                    "improvement_score": s.improvement_score,
                    "error_type": s.error_type,
                }
                for s in self.sessions
            ],
        }

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

    def print_summary(self) -> None:
        """Print a human-readable summary of metrics."""
        metrics = self.get_aggregated_metrics()

        print("\n" + "=" * 60)
        print("📊 ACE Learning Metrics Summary")
        print("=" * 60)
        print("\n📈 Overall Performance:")
        print(f"  Total executions: {metrics.total_executions}")
        print(f"  Successful: {metrics.successful_executions}")
        print(f"  Success rate: {metrics.success_rate:.1%}")
        print(f"  Improvement rate: {metrics.improvement_rate:+.1%}")
        print("\n🧠 Learning Progress:")
        print(f"  Total strategies learned: {metrics.total_strategies_learned}")
        print(f"  Average iterations per task: {metrics.average_iterations:.1f}")
        print(f"  Total execution time: {metrics.total_execution_time:.1f}s")

        if metrics.task_type_breakdown:
            print("\n📋 Task Type Breakdown:")
            for task_type, breakdown in metrics.task_type_breakdown.items():
                print(f"\n  {task_type}:")
                print(f"    Executions: {breakdown['count']}")
                print(f"    Success rate: {breakdown['success_rate']:.1%}")
                print(f"    Strategies learned: {breakdown['strategies_learned']}")
                print(f"    Avg iterations: {breakdown['avg_iterations']:.1f}")

        print("\n" + "=" * 60)

    def _save_metrics(self) -> None:
        """Save metrics to file."""
        data = [
            {
                "timestamp": s.timestamp,
                "task_type": s.task_type,
                "execution_success": s.execution_success,
                "strategies_used": s.strategies_used,
                "strategies_learned": s.strategies_learned,
                "iteration_count": s.iteration_count,
                "execution_time": s.execution_time,
                "playbook_size": s.playbook_size,
                "success_rate": s.success_rate,
                "improvement_score": s.improvement_score,
                "error_type": s.error_type,
                "metadata": s.metadata,
            }
            for s in self.sessions
        ]

        with open(self.metrics_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load_metrics(self) -> None:
        """Load metrics from file."""
        with open(self.metrics_file) as f:
            data = json.load(f)

        self.sessions = [
            LearningMetrics(
                timestamp=s["timestamp"],
                task_type=s["task_type"],
                execution_success=s["execution_success"],
                strategies_used=s["strategies_used"],
                strategies_learned=s["strategies_learned"],
                iteration_count=s["iteration_count"],
                execution_time=s["execution_time"],
                playbook_size=s["playbook_size"],
                success_rate=s["success_rate"],
                improvement_score=s["improvement_score"],
                error_type=s.get("error_type"),
                metadata=s.get("metadata", {}),
            )
            for s in data
        ]
