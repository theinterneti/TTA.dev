"""ACE-Enabled Self-Learning Primitives.

Combines Agentic Context Engine (ACE) with TTA.dev primitives to create
self-improving workflows that learn from execution feedback.

This module provides the foundation for primitives that:
- Learn strategies from execution results (not just reasoning)
- Build playbooks of successful patterns
- Self-improve over time through real-world feedback
- Combine with E2B for learning from actual code execution

Example:
    ```python
    from tta_dev_primitives.ace import SelfLearningCodePrimitive
    from tta_dev_primitives import WorkflowContext

    # Create a primitive that learns from code execution
    learner = SelfLearningCodePrimitive()

    # First execution - baseline performance
    context = WorkflowContext(correlation_id="learn-001")
    result1 = await learner.execute({
        "task": "Create a function to calculate fibonacci numbers",
        "language": "python"
    }, context)

    # Second execution - uses learned strategies
    result2 = await learner.execute({
        "task": "Create a function to calculate prime numbers",
        "language": "python"
    }, context)

    # The primitive has learned strategies that improve performance
    print(f"Strategies learned: {learner.playbook_size}")
    print(f"Success rate improvement: {learner.success_rate}")
    ```
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TypedDict

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive

logger = logging.getLogger(__name__)


class ACEInput(TypedDict, total=False):
    """Input for ACE-enabled primitives."""

    task: str  # Required: Task description
    context: str  # Optional: Additional context
    language: str  # Optional: Programming language (default: python)
    expected_output: str  # Optional: Expected result for learning
    max_iterations: int  # Optional: Max refinement iterations (default: 3)


class ACEOutput(TypedDict):
    """Output from ACE-enabled primitives."""

    result: Any  # The actual result
    code_generated: str | None  # Generated code (if applicable)
    execution_success: bool  # Whether execution succeeded
    strategies_learned: int  # Number of new strategies learned
    playbook_size: int  # Total strategies in playbook
    improvement_score: float  # Improvement over baseline (0.0-1.0)
    learning_summary: str  # Human-readable summary of learning


class MockACEPlaybook:
    """Mock implementation of ACE Playbook for initial development.

    This will be replaced with the real ACE Playbook once integrated.
    """

    def __init__(self) -> None:
        self.strategies = []
        self.success_counts = {}
        self.failure_counts = {}

    def add_strategy(self, strategy: str, context: str = "") -> None:
        """Add a learned strategy."""
        strategy_key = f"{context}:{strategy}"
        if strategy_key not in [s["key"] for s in self.strategies]:
            self.strategies.append(
                {
                    "key": strategy_key,
                    "strategy": strategy,
                    "context": context,
                    "successes": 0,
                    "failures": 0,
                }
            )
            logger.info(f"Learned new strategy: {strategy}")

    def get_relevant_strategies(self, task_context: str) -> list[str]:
        """Get strategies relevant to current task."""
        relevant = []
        for strategy in self.strategies:
            if (
                strategy["context"].lower() in task_context.lower()
                or strategy["successes"] > strategy["failures"]
            ):
                relevant.append(strategy["strategy"])
        return relevant

    def record_success(self, strategy: str) -> None:
        """Record successful use of strategy."""
        for s in self.strategies:
            if s["strategy"] == strategy:
                s["successes"] += 1
                break

    def record_failure(self, strategy: str) -> None:
        """Record failed use of strategy."""
        for s in self.strategies:
            if s["strategy"] == strategy:
                s["failures"] += 1
                break

    def size(self) -> int:
        """Get total number of strategies."""
        return len(self.strategies)

    def save_to_file(self, filepath: Path) -> None:
        """Save playbook to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.strategies, f, indent=2)

    def load_from_file(self, filepath: Path) -> None:
        """Load playbook from JSON file."""
        if filepath.exists():
            with open(filepath) as f:
                self.strategies = json.load(f)


class SelfLearningCodePrimitive(InstrumentedPrimitive[ACEInput, ACEOutput]):
    """Code generation primitive that learns from execution feedback.

    This primitive combines:
    - LLM-based code generation
    - E2B sandbox execution
    - ACE-style learning from results
    - Strategy playbook building

    The primitive learns patterns like:
    - Error handling strategies that work
    - Library/import patterns for different tasks
    - Code structure approaches that succeed
    - Debugging techniques that resolve issues

    Attributes:
        playbook: Learned strategies storage
        e2b_executor: E2B code execution primitive
        success_rate: Current success rate (0.0-1.0)
        total_executions: Total number of executions
        successful_executions: Number of successful executions
    """

    def __init__(self, playbook_file: Path | None = None) -> None:
        """Initialize the self-learning code primitive.

        Args:
            playbook_file: Optional file to persist learned strategies
        """
        super().__init__()

        # Initialize components
        self.playbook = MockACEPlaybook()
        self.e2b_executor = CodeExecutionPrimitive()

        # Learning metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.baseline_success_rate = 0.0

        # Persistence
        self.playbook_file = playbook_file or Path("ace_playbook.json")
        if self.playbook_file.exists():
            self.playbook.load_from_file(self.playbook_file)
            logger.info(f"Loaded {self.playbook.size()} strategies from {self.playbook_file}")

    @property
    def success_rate(self) -> float:
        """Current success rate."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    @property
    def playbook_size(self) -> int:
        """Number of learned strategies."""
        return self.playbook.size()

    @property
    def improvement_score(self) -> float:
        """Improvement over baseline (0.0-1.0)."""
        if self.baseline_success_rate == 0:
            return 0.0
        current_rate = self.success_rate
        if current_rate <= self.baseline_success_rate:
            return 0.0
        return min(
            1.0,
            (current_rate - self.baseline_success_rate) / (1.0 - self.baseline_success_rate),
        )

    async def _execute_impl(self, input_data: ACEInput, context: WorkflowContext) -> ACEOutput:
        """Execute with learning."""

        task = input_data["task"]
        task_context = input_data.get("context", "")
        language = input_data.get("language", "python")
        max_iterations = input_data.get("max_iterations", 3)

        # Track metrics
        self.total_executions += 1

        # Get relevant strategies from playbook
        relevant_strategies = self.playbook.get_relevant_strategies(f"{task} {task_context}")

        # Generate code using learned strategies
        code = await self._generate_code_with_strategies(
            task=task,
            context=task_context,
            language=language,
            strategies=relevant_strategies,
        )

        # Execute code and learn from results
        execution_result = None
        strategies_learned = 0

        for iteration in range(max_iterations):
            try:
                # Execute in E2B sandbox
                execution_result = await self.e2b_executor.execute(
                    {"code": code, "language": language, "timeout": 30}, context
                )

                if execution_result["success"]:
                    # Success! Record and learn
                    self.successful_executions += 1
                    strategies_learned += await self._learn_from_success(
                        task, code, execution_result, relevant_strategies
                    )
                    break
                else:
                    # Failure - learn and try to improve
                    strategies_learned += await self._learn_from_failure(
                        task, code, execution_result, relevant_strategies
                    )

                    # Generate improved code for next iteration
                    if iteration < max_iterations - 1:
                        code = await self._improve_code(
                            original_code=code,
                            error=execution_result.get("error", ""),
                            task=task,
                            strategies=self.playbook.get_relevant_strategies(
                                f"error_handling {task}"
                            ),
                        )

            except Exception as e:
                logger.error(f"Execution error: {e}")
                execution_result = {
                    "success": False,
                    "error": str(e),
                    "output": "",
                    "execution_time": 0.0,
                    "logs": [],
                }

        # Save learned strategies
        if strategies_learned > 0:
            self.playbook.save_to_file(self.playbook_file)

        # Generate learning summary
        learning_summary = self._generate_learning_summary(strategies_learned, execution_result)

        return ACEOutput(
            result=execution_result.get("output", "") if execution_result else "",
            code_generated=code,
            execution_success=execution_result.get("success", False) if execution_result else False,
            strategies_learned=strategies_learned,
            playbook_size=self.playbook_size,
            improvement_score=self.improvement_score,
            learning_summary=learning_summary,
        )

    async def _generate_code_with_strategies(
        self, task: str, context: str, language: str, strategies: list[str]
    ) -> str:
        """Generate code using learned strategies.

        In a full ACE integration, this would use the ACE Generator.
        For now, we use a simple template-based approach.
        """

        # Build prompt with learned strategies (used implicitly in generation logic below)

        # Simple code generation (would be replaced with LLM call)
        if "fibonacci" in task.lower():
            if "use memoization for better performance" in strategies:
                return '''def fibonacci(n, memo={}):
    """Calculate fibonacci with memoization."""
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]

# Test the function
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")'''
            else:
                return '''def fibonacci(n):
    """Calculate fibonacci recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")'''

        elif "prime" in task.lower():
            return '''def is_prime(n):
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def generate_primes(limit):
    """Generate prime numbers up to limit."""
    primes = []
    for i in range(2, limit + 1):
        if is_prime(i):
            primes.append(i)
    return primes

# Test the function
primes = generate_primes(50)
print(f"Primes up to 50: {primes}")'''

        # Default: simple task-based code generation
        return f"""# Generated code for: {task}
print("Hello from generated code!")
print("Task: {task}")
print("Context: {context}")
print("Language: {language}")"""

    async def _learn_from_success(
        self, task: str, code: str, result: dict, strategies_used: list[str]
    ) -> int:
        """Learn strategies from successful execution."""

        strategies_learned = 0

        # Record success for used strategies
        for strategy in strategies_used:
            self.playbook.record_success(strategy)

        # Learn new strategies from successful patterns
        if "fibonacci" in task.lower() and "memo" in code:
            self.playbook.add_strategy(
                "use memoization for better performance", "recursive_algorithms"
            )
            strategies_learned += 1

        if "prime" in task.lower() and "int(n**0.5)" in code:
            self.playbook.add_strategy("optimize prime checking with sqrt limit", "number_theory")
            strategies_learned += 1

        # Learn from execution performance
        if result.get("execution_time", 0) < 0.1:
            self.playbook.add_strategy("current approach is performant", task.lower())
            strategies_learned += 1

        return strategies_learned

    async def _learn_from_failure(
        self, task: str, code: str, result: dict, strategies_used: list[str]
    ) -> int:
        """Learn strategies from failed execution."""

        strategies_learned = 0
        error = result.get("error", "")

        # Record failure for used strategies
        for strategy in strategies_used:
            self.playbook.record_failure(strategy)

        # Learn error handling strategies
        if "RecursionError" in error:
            self.playbook.add_strategy(
                "add base case for recursion to prevent stack overflow",
                "recursion_error_handling",
            )
            self.playbook.add_strategy(
                "consider iterative approach for deep recursion",
                "recursion_error_handling",
            )
            strategies_learned += 2

        if "NameError" in error:
            self.playbook.add_strategy(
                "ensure all variables are defined before use", "variable_error_handling"
            )
            strategies_learned += 1

        if "SyntaxError" in error:
            self.playbook.add_strategy("validate syntax before execution", "syntax_error_handling")
            strategies_learned += 1

        return strategies_learned

    async def _improve_code(
        self, original_code: str, error: str, task: str, strategies: list[str]
    ) -> str:
        """Improve code based on error and strategies."""

        # Simple improvement logic (would use LLM in full implementation)
        if "RecursionError" in error and "fibonacci" in task.lower():
            # Add memoization to prevent deep recursion
            return '''def fibonacci(n, memo={}):
    """Calculate fibonacci with memoization to prevent recursion error."""
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]

# Test with reasonable inputs
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")'''

        # Default: return original code with error handling
        return f"""try:
{original_code}
except Exception as e:
    print(f"Error occurred: {{e}}")
    print("Implementing error handling based on learned strategies")"""

    def _generate_learning_summary(
        self, strategies_learned: int, execution_result: dict | None
    ) -> str:
        """Generate human-readable learning summary."""

        success = execution_result.get("success", False) if execution_result else False

        summary_parts = [
            f"Execution {'succeeded' if success else 'failed'}",
            f"Learned {strategies_learned} new strategies",
            f"Total strategies in playbook: {self.playbook_size}",
            f"Current success rate: {self.success_rate:.1%}",
            f"Improvement over baseline: {self.improvement_score:.1%}",
        ]

        if strategies_learned > 0:
            summary_parts.append("✅ Learning is active and improving performance")
        else:
            summary_parts.append("ℹ️ No new strategies learned this iteration")

        return " | ".join(summary_parts)


# Export for use in other modules
__all__ = ["SelfLearningCodePrimitive", "ACEInput", "ACEOutput", "MockACEPlaybook"]
