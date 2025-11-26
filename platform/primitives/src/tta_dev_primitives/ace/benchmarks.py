"""Benchmark suite for ACE learning validation.

Provides comprehensive benchmarks to validate learning effectiveness across
different code generation scenarios.

Features:
- Standardized test tasks
- Difficulty levels (easy, medium, hard)
- Multiple programming languages
- Success criteria validation
- Performance measurement
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.base import WorkflowContext
from .cognitive_manager import ACEInput, SelfLearningCodePrimitive


class DifficultyLevel(Enum):
    """Benchmark difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class BenchmarkTask:
    """A single benchmark task."""

    id: str
    name: str
    description: str
    task: str
    language: str
    difficulty: DifficultyLevel
    expected_patterns: list[str]  # Patterns that should appear in solution
    validation_criteria: dict[str, Any]  # Criteria for success
    max_iterations: int = 3
    timeout_seconds: int = 30


@dataclass
class BenchmarkResult:
    """Result from running a benchmark task."""

    task_id: str
    task_name: str
    success: bool
    iterations_used: int
    execution_time: float
    strategies_learned: int
    code_generated: str | None
    error_message: str | None
    patterns_found: list[str]
    validation_passed: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class BenchmarkSuite:
    """Comprehensive benchmark suite for ACE learning validation.

    Example:
        ```python
        suite = BenchmarkSuite()

        # Run all benchmarks
        results = await suite.run_all_benchmarks(learner)

        # Analyze results
        suite.print_summary(results)

        # Export for analysis
        suite.export_results(results, Path("benchmark_results.json"))
        ```
    """

    def __init__(self) -> None:
        """Initialize benchmark suite with predefined tasks."""
        self.tasks = self._create_benchmark_tasks()

    def _create_benchmark_tasks(self) -> list[BenchmarkTask]:
        """Create comprehensive set of benchmark tasks."""

        return [
            # ===== EASY TASKS =====
            BenchmarkTask(
                id="easy_fibonacci",
                name="Fibonacci Sequence",
                description="Generate fibonacci numbers",
                task="Create a function to calculate the nth fibonacci number",
                language="python",
                difficulty=DifficultyLevel.EASY,
                expected_patterns=["def", "fibonacci", "return"],
                validation_criteria={"has_function": True, "has_return": True},
            ),
            BenchmarkTask(
                id="easy_factorial",
                name="Factorial Calculation",
                description="Calculate factorial of a number",
                task="Create a function to calculate factorial of n",
                language="python",
                difficulty=DifficultyLevel.EASY,
                expected_patterns=["def", "factorial", "return"],
                validation_criteria={"has_function": True, "has_return": True},
            ),
            BenchmarkTask(
                id="easy_palindrome",
                name="Palindrome Check",
                description="Check if string is palindrome",
                task="Create a function to check if a string is a palindrome",
                language="python",
                difficulty=DifficultyLevel.EASY,
                expected_patterns=["def", "palindrome", "return"],
                validation_criteria={"has_function": True, "has_return": True},
            ),
            # ===== MEDIUM TASKS =====
            BenchmarkTask(
                id="medium_prime_sieve",
                name="Sieve of Eratosthenes",
                description="Generate primes using sieve algorithm",
                task="Create a function to find all prime numbers up to n using Sieve of Eratosthenes",
                language="python",
                difficulty=DifficultyLevel.MEDIUM,
                expected_patterns=["def", "prime", "sieve", "return"],
                validation_criteria={
                    "has_function": True,
                    "has_loop": True,
                    "has_return": True,
                },
            ),
            BenchmarkTask(
                id="medium_binary_search",
                name="Binary Search",
                description="Implement binary search algorithm",
                task="Create a function to perform binary search on a sorted array",
                language="python",
                difficulty=DifficultyLevel.MEDIUM,
                expected_patterns=["def", "binary", "search", "return"],
                validation_criteria={
                    "has_function": True,
                    "has_loop_or_recursion": True,
                    "has_return": True,
                },
            ),
            BenchmarkTask(
                id="medium_merge_sort",
                name="Merge Sort",
                description="Implement merge sort algorithm",
                task="Create a function to sort an array using merge sort",
                language="python",
                difficulty=DifficultyLevel.MEDIUM,
                expected_patterns=["def", "merge", "sort", "return"],
                validation_criteria={
                    "has_function": True,
                    "has_recursion": True,
                    "has_return": True,
                },
            ),
            # ===== HARD TASKS =====
            BenchmarkTask(
                id="hard_lru_cache",
                name="LRU Cache Implementation",
                description="Implement LRU cache with O(1) operations",
                task="Create a class implementing an LRU cache with get and put operations in O(1) time",
                language="python",
                difficulty=DifficultyLevel.HARD,
                expected_patterns=["class", "LRU", "get", "put", "dict"],
                validation_criteria={
                    "has_class": True,
                    "has_methods": True,
                    "has_data_structures": True,
                },
            ),
            BenchmarkTask(
                id="hard_graph_traversal",
                name="Graph DFS/BFS",
                description="Implement graph traversal algorithms",
                task="Create functions for depth-first and breadth-first graph traversal",
                language="python",
                difficulty=DifficultyLevel.HARD,
                expected_patterns=["def", "dfs", "bfs", "graph", "visited"],
                validation_criteria={
                    "has_function": True,
                    "has_recursion_or_queue": True,
                    "has_visited_tracking": True,
                },
            ),
        ]

    async def run_benchmark(
        self,
        task: BenchmarkTask,
        learner: SelfLearningCodePrimitive,
        context: WorkflowContext,
    ) -> BenchmarkResult:
        """Run a single benchmark task.

        Args:
            task: Benchmark task to run
            learner: Self-learning primitive to test
            context: Workflow context

        Returns:
            Benchmark result with metrics
        """
        start_time = time.time()

        try:
            # Execute task
            result = await learner.execute(
                ACEInput(
                    task=task.task,
                    language=task.language,
                    max_iterations=task.max_iterations,
                    context=task.description,
                ),
                context,
            )

            execution_time = time.time() - start_time

            # Validate result
            patterns_found = self._check_patterns(
                result.get("code_generated", ""), task.expected_patterns
            )
            validation_passed = self._validate_criteria(
                result.get("code_generated", ""), task.validation_criteria
            )

            return BenchmarkResult(
                task_id=task.id,
                task_name=task.name,
                success=result["execution_success"] and validation_passed,
                iterations_used=task.max_iterations,
                execution_time=execution_time,
                strategies_learned=result["strategies_learned"],
                code_generated=result.get("code_generated"),
                error_message=None,
                patterns_found=patterns_found,
                validation_passed=validation_passed,
                metadata={
                    "difficulty": task.difficulty.value,
                    "language": task.language,
                    "playbook_size": result["playbook_size"],
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return BenchmarkResult(
                task_id=task.id,
                task_name=task.name,
                success=False,
                iterations_used=0,
                execution_time=execution_time,
                strategies_learned=0,
                code_generated=None,
                error_message=str(e),
                patterns_found=[],
                validation_passed=False,
                metadata={
                    "difficulty": task.difficulty.value,
                    "language": task.language,
                },
            )

    async def run_all_benchmarks(
        self, learner: SelfLearningCodePrimitive, context: WorkflowContext | None = None
    ) -> list[BenchmarkResult]:
        """Run all benchmark tasks.

        Args:
            learner: Self-learning primitive to test
            context: Optional workflow context

        Returns:
            List of benchmark results
        """
        if context is None:
            context = WorkflowContext(correlation_id="benchmark-suite")

        results = []
        for task in self.tasks:
            print(f"\n🎯 Running: {task.name} ({task.difficulty.value})")
            result = await self.run_benchmark(task, learner, context)
            results.append(result)
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.task_name}: {result.execution_time:.2f}s")

        return results

    def _check_patterns(self, code: str, patterns: list[str]) -> list[str]:
        """Check which expected patterns are present in code."""
        return [p for p in patterns if p.lower() in code.lower()]

    def _validate_criteria(self, code: str, criteria: dict[str, Any]) -> bool:
        """Validate code against criteria."""
        if not code:
            return False

        code_lower = code.lower()

        for criterion, expected in criteria.items():
            if criterion == "has_function" and expected:
                if "def " not in code_lower:
                    return False
            elif criterion == "has_class" and expected:
                if "class " not in code_lower:
                    return False
            elif criterion == "has_return" and expected:
                if "return" not in code_lower:
                    return False
            elif criterion == "has_loop" and expected:
                if "for " not in code_lower and "while " not in code_lower:
                    return False

        return True

    def print_summary(self, results: list[BenchmarkResult]) -> None:
        """Print benchmark summary."""
        print("\n" + "=" * 70)
        print("📊 Benchmark Suite Results")
        print("=" * 70)

        # Overall stats
        total = len(results)
        successful = sum(1 for r in results if r.success)
        total_time = sum(r.execution_time for r in results)
        total_strategies = sum(r.strategies_learned for r in results)

        print("\n📈 Overall Performance:")
        print(f"  Total tasks: {total}")
        print(f"  Successful: {successful} ({successful / total:.1%})")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Strategies learned: {total_strategies}")

        # By difficulty
        print("\n🎯 Performance by Difficulty:")
        for difficulty in DifficultyLevel:
            diff_results = [r for r in results if r.metadata.get("difficulty") == difficulty.value]
            if diff_results:
                diff_success = sum(1 for r in diff_results if r.success)
                print(
                    f"  {difficulty.value.capitalize()}: {diff_success}/{len(diff_results)} "
                    f"({diff_success / len(diff_results):.1%})"
                )

        # Failed tasks
        failed = [r for r in results if not r.success]
        if failed:
            print(f"\n❌ Failed Tasks ({len(failed)}):")
            for result in failed:
                print(f"  • {result.task_name}")
                if result.error_message:
                    print(f"    Error: {result.error_message[:100]}")

        print("\n" + "=" * 70)

    def export_results(self, results: list[BenchmarkResult], output_file: Path) -> None:
        """Export benchmark results to JSON."""
        import json

        data = {
            "summary": {
                "total_tasks": len(results),
                "successful": sum(1 for r in results if r.success),
                "total_time": sum(r.execution_time for r in results),
                "total_strategies_learned": sum(r.strategies_learned for r in results),
            },
            "results": [
                {
                    "task_id": r.task_id,
                    "task_name": r.task_name,
                    "success": r.success,
                    "iterations_used": r.iterations_used,
                    "execution_time": r.execution_time,
                    "strategies_learned": r.strategies_learned,
                    "patterns_found": r.patterns_found,
                    "validation_passed": r.validation_passed,
                    "metadata": r.metadata,
                }
                for r in results
            ],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n📁 Results exported to: {output_file}")
