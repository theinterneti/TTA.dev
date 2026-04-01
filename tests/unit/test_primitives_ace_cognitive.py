"""Tests for ACE cognitive manager and benchmark suite.

Covers:
- MockACEPlaybook: strategy management, file persistence, success/failure recording
- SelfLearningCodePrimitive: instantiation, properties, execute() learning paths
- BenchmarkTask / BenchmarkResult / DifficultyLevel dataclasses
- BenchmarkSuite: task creation, pattern matching, criteria validation,
  benchmark execution (success, failure, exception), summary output, JSON export

All E2B / external API calls are fully mocked.
Tests follow AAA (Arrange / Act / Assert) pattern throughout.

Note: BenchmarkRunner does not exist in benchmarks.py (prompt description was
inaccurate) — all benchmark coverage is through BenchmarkSuite instead.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.ace.benchmarks import (
    BenchmarkResult,
    BenchmarkSuite,
    BenchmarkTask,
    DifficultyLevel,
)
from ttadev.primitives.ace.cognitive_manager import (
    ACEInput,
    MockACEPlaybook,
    SelfLearningCodePrimitive,
)
from ttadev.primitives.core.base import WorkflowContext

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_code_output(
    success: bool = True,
    output: str = "result output",
    error: str | None = None,
    execution_time: float = 0.05,
) -> dict[str, Any]:
    """Build a mock CodeOutput dict matching the TypedDict shape."""
    return {
        "success": success,
        "output": output,
        "error": error,
        "execution_time": execution_time,
        "logs": [],
        "sandbox_id": "mock-sandbox-id",
    }


@pytest.fixture
def ctx() -> WorkflowContext:
    """Minimal WorkflowContext for test isolation."""
    return WorkflowContext(workflow_id="test-ace")


@pytest.fixture
def primitive(tmp_path: Path):
    """SelfLearningCodePrimitive with E2B executor fully mocked.

    Yields (primitive_instance, mock_executor) so individual tests can
    configure mock_exec.execute return_value / side_effect per scenario.
    """
    with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive") as MockExecCls:  # noqa: N806
        mock_exec = MagicMock()
        mock_exec.execute = AsyncMock(return_value=_make_code_output())
        MockExecCls.return_value = mock_exec
        p = SelfLearningCodePrimitive(playbook_file=tmp_path / "playbook.json")
        yield p, mock_exec


# ============================================================
# TestMockACEPlaybook
# ============================================================


class TestMockACEPlaybook:
    """Unit tests for MockACEPlaybook — pure Python, no mocking needed."""

    # --- construction ---

    def test_init_creates_empty_strategies(self) -> None:
        """Arrange/Act: fresh playbook. Assert: no strategies, size==0."""
        pb = MockACEPlaybook()
        assert pb.strategies == []
        assert pb.size() == 0

    # --- add_strategy ---

    def test_add_strategy_increases_size(self) -> None:
        # Arrange
        pb = MockACEPlaybook()
        # Act
        pb.add_strategy("use memoization", "recursion")
        # Assert
        assert pb.size() == 1

    def test_add_strategy_stores_correct_composite_key(self) -> None:
        pb = MockACEPlaybook()
        pb.add_strategy("validate inputs", "error_handling")
        keys = [s["key"] for s in pb.strategies]
        assert "error_handling:validate inputs" in keys

    def test_add_strategy_stores_strategy_context_and_counters(self) -> None:
        pb = MockACEPlaybook()
        pb.add_strategy("sqrt optimisation", "prime_checking")
        strat = pb.strategies[0]
        assert strat["strategy"] == "sqrt optimisation"
        assert strat["context"] == "prime_checking"
        assert strat["successes"] == 0
        assert strat["failures"] == 0

    def test_add_duplicate_strategy_is_ignored(self) -> None:
        """Same context:strategy key must not be added twice."""
        pb = MockACEPlaybook()
        pb.add_strategy("memoize", "recursion")
        pb.add_strategy("memoize", "recursion")
        assert pb.size() == 1

    def test_same_strategy_in_different_contexts_both_stored(self) -> None:
        pb = MockACEPlaybook()
        pb.add_strategy("memoize", "recursion")
        pb.add_strategy("memoize", "caching")
        assert pb.size() == 2

    # --- get_relevant_strategies ---

    def test_get_relevant_by_context_substring_match(self) -> None:
        # Arrange
        pb = MockACEPlaybook()
        pb.add_strategy("use sqrt limit", "prime_checking")
        # Act
        results = pb.get_relevant_strategies("prime_checking optimisation for loops")
        # Assert
        assert "use sqrt limit" in results

    def test_get_relevant_by_high_success_count(self) -> None:
        """Strategy with successes > failures appears regardless of context text."""
        pb = MockACEPlaybook()
        pb.add_strategy("fast path", "general_context")
        pb.record_success("fast path")
        pb.record_success("fast path")  # 2 successes > 0 failures
        results = pb.get_relevant_strategies("completely unrelated task text")
        assert "fast path" in results

    def test_get_relevant_no_match_returns_empty_list(self) -> None:
        pb = MockACEPlaybook()
        pb.add_strategy("niche strategy", "very_specific_context")
        # failures == successes == 0; context won't match
        results = pb.get_relevant_strategies("totally different domain task")
        assert results == []

    # --- record_success / record_failure ---

    def test_record_success_increments_counter(self) -> None:
        # Arrange
        pb = MockACEPlaybook()
        pb.add_strategy("try-except wrapping", "error")
        # Act
        pb.record_success("try-except wrapping")
        pb.record_success("try-except wrapping")
        # Assert
        strat = next(s for s in pb.strategies if s["strategy"] == "try-except wrapping")
        assert strat["successes"] == 2

    def test_record_failure_increments_counter(self) -> None:
        pb = MockACEPlaybook()
        pb.add_strategy("bad approach", "debug")
        pb.record_failure("bad approach")
        strat = next(s for s in pb.strategies if s["strategy"] == "bad approach")
        assert strat["failures"] == 1

    def test_record_success_for_unknown_strategy_does_not_raise(self) -> None:
        pb = MockACEPlaybook()
        pb.record_success("ghost strategy")  # should silently no-op

    def test_record_failure_for_unknown_strategy_does_not_raise(self) -> None:
        pb = MockACEPlaybook()
        pb.record_failure("ghost strategy")  # should silently no-op

    # --- file persistence ---

    def test_save_to_file_writes_valid_json(self, tmp_path: Path) -> None:
        # Arrange
        pb = MockACEPlaybook()
        pb.add_strategy("memoize", "recursion")
        filepath = tmp_path / "test_playbook.json"
        # Act
        pb.save_to_file(filepath)
        # Assert
        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert len(data) == 1
        assert data[0]["strategy"] == "memoize"
        assert data[0]["context"] == "recursion"

    def test_load_from_file_restores_strategies(self, tmp_path: Path) -> None:
        # Arrange: save first playbook
        pb1 = MockACEPlaybook()
        pb1.add_strategy("iterative approach", "performance")
        pb1.record_success("iterative approach")
        filepath = tmp_path / "load_test.json"
        pb1.save_to_file(filepath)
        # Act: load into fresh playbook
        pb2 = MockACEPlaybook()
        pb2.load_from_file(filepath)
        # Assert
        assert pb2.size() == 1
        assert pb2.strategies[0]["strategy"] == "iterative approach"
        assert pb2.strategies[0]["successes"] == 1

    def test_roundtrip_preserves_all_strategies(self, tmp_path: Path) -> None:
        # Arrange
        pb = MockACEPlaybook()
        for i in range(5):
            pb.add_strategy(f"strategy_{i}", f"context_{i}")
        filepath = tmp_path / "roundtrip.json"
        # Act
        pb.save_to_file(filepath)
        pb2 = MockACEPlaybook()
        pb2.load_from_file(filepath)
        # Assert
        assert pb2.size() == 5


# ============================================================
# TestSelfLearningCodePrimitive — construction & properties
# ============================================================


class TestSelfLearningCodePrimitiveInit:
    def test_instantiation_succeeds_with_mocked_executor(self, tmp_path: Path) -> None:
        """Arrange: patch E2B; Act: construct; Assert: no exception, valid object."""
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        assert p is not None
        assert isinstance(p, SelfLearningCodePrimitive)

    def test_initial_execution_counters_are_zero(self, tmp_path: Path) -> None:
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        assert p.total_executions == 0
        assert p.successful_executions == 0

    def test_success_rate_zero_before_any_execution(self, tmp_path: Path) -> None:
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        assert p.success_rate == 0.0

    def test_playbook_size_zero_on_fresh_init(self, tmp_path: Path) -> None:
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        assert p.playbook_size == 0

    def test_improvement_score_zero_without_baseline(self, tmp_path: Path) -> None:
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        assert p.improvement_score == 0.0

    def test_loads_existing_playbook_file_on_init(self, tmp_path: Path) -> None:
        """If playbook_file exists at init time, strategies are loaded from it."""
        filepath = tmp_path / "existing.json"
        data = [
            {
                "key": "ctx:strat",
                "strategy": "strat",
                "context": "ctx",
                "successes": 1,
                "failures": 0,
            }
        ]
        filepath.write_text(json.dumps(data))
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=filepath)
        assert p.playbook_size == 1

    def test_improvement_score_capped_at_one(self, tmp_path: Path) -> None:
        """improvement_score must never exceed 1.0 even with extreme input."""
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        p.baseline_success_rate = 0.1
        p.total_executions = 10
        p.successful_executions = 10  # 100% success
        assert p.improvement_score <= 1.0
        assert p.improvement_score == pytest.approx(1.0)

    def test_improvement_score_zero_when_below_baseline(self, tmp_path: Path) -> None:
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        p.baseline_success_rate = 0.8
        p.total_executions = 10
        p.successful_executions = 5  # 50% < 80% baseline
        assert p.improvement_score == 0.0

    def test_success_rate_manual_calculation(self, tmp_path: Path) -> None:
        with patch("ttadev.primitives.ace.cognitive_manager.CodeExecutionPrimitive"):
            p = SelfLearningCodePrimitive(playbook_file=tmp_path / "pb.json")
        p.total_executions = 4
        p.successful_executions = 3
        assert p.success_rate == pytest.approx(0.75)


# ============================================================
# TestSelfLearningCodePrimitive — execute() happy path
# ============================================================


class TestSelfLearningCodePrimitiveExecuteSuccess:
    async def test_returns_valid_ace_output_keys(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """Happy path: first attempt succeeds — verify all expected output keys."""
        # Arrange
        p, _ = primitive
        # Act
        result = await p.execute(ACEInput(task="calculate fibonacci"), ctx)
        # Assert
        assert result["execution_success"] is True
        assert "code_generated" in result
        assert "strategies_learned" in result
        assert "playbook_size" in result
        assert "improvement_score" in result
        assert "learning_summary" in result
        assert "result" in result

    async def test_total_executions_increments_after_execute(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p, _ = primitive
        assert p.total_executions == 0
        # Act
        await p.execute(ACEInput(task="fibonacci"), ctx)
        # Assert
        assert p.total_executions == 1

    async def test_successful_executions_increments_on_success(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True)
        await p.execute(ACEInput(task="fibonacci"), ctx)
        assert p.successful_executions == 1

    async def test_success_rate_is_one_after_single_success(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True)
        await p.execute(ACEInput(task="fibonacci"), ctx)
        assert p.success_rate == 1.0

    async def test_fibonacci_task_generates_fibonacci_code(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, _ = primitive
        result = await p.execute(ACEInput(task="calculate fibonacci numbers"), ctx)
        assert result["code_generated"] is not None
        assert "fibonacci" in result["code_generated"].lower()

    async def test_prime_task_generates_prime_code(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, _ = primitive
        result = await p.execute(ACEInput(task="generate prime numbers"), ctx)
        assert result["code_generated"] is not None
        assert "prime" in result["code_generated"].lower()

    async def test_language_parameter_accepted_without_error(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True)
        result = await p.execute(ACEInput(task="generic task", language="javascript"), ctx)
        assert result["execution_success"] is True

    async def test_max_iterations_one_calls_executor_exactly_once(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """max_iterations=1 on success → exactly one executor call."""
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True)
        await p.execute(ACEInput(task="generic task", max_iterations=1), ctx)
        assert mock_exec.execute.call_count == 1

    async def test_playbook_size_in_output_matches_property(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, _ = primitive
        result = await p.execute(ACEInput(task="fibonacci"), ctx)
        assert result["playbook_size"] == p.playbook_size

    async def test_learning_summary_contains_succeeded_on_success(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True)
        result = await p.execute(ACEInput(task="fibonacci"), ctx)
        assert "succeeded" in result["learning_summary"]

    async def test_output_result_contains_executor_output(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True, output="55")
        result = await p.execute(ACEInput(task="fibonacci"), ctx)
        assert result["result"] == "55"


# ============================================================
# TestSelfLearningCodePrimitive — execute() failure paths
# ============================================================


class TestSelfLearningCodePrimitiveExecuteFailure:
    async def test_successful_executions_not_incremented_on_failure(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=False, error="SyntaxError: unexpected indent"
        )
        # Act
        await p.execute(ACEInput(task="generic task", max_iterations=1), ctx)
        # Assert
        assert p.successful_executions == 0

    async def test_execution_success_false_when_all_iterations_fail(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=False, error="NameError: bad")
        result = await p.execute(ACEInput(task="task", max_iterations=1), ctx)
        assert result["execution_success"] is False

    async def test_learning_summary_contains_failed_on_failure(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=False, error="SyntaxError: oops")
        result = await p.execute(ACEInput(task="generic", max_iterations=1), ctx)
        assert "failed" in result["learning_summary"]

    async def test_retry_loop_calls_executor_multiple_times(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """Executor fails twice then succeeds — verifies full retry loop fires."""
        p, mock_exec = primitive
        mock_exec.execute.side_effect = [
            _make_code_output(success=False, error="NameError: x not defined"),
            _make_code_output(success=False, error="NameError: x not defined"),
            _make_code_output(success=True, output="42"),
        ]
        result = await p.execute(ACEInput(task="generic task", max_iterations=3), ctx)
        assert mock_exec.execute.call_count == 3
        assert result["execution_success"] is True

    async def test_exception_in_executor_handled_gracefully(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """RuntimeError from executor is caught; execution_success=False returned."""
        p, mock_exec = primitive
        mock_exec.execute.side_effect = RuntimeError("Sandbox crashed hard")
        result = await p.execute(ACEInput(task="generic task", max_iterations=1), ctx)
        assert result["execution_success"] is False

    async def test_success_rate_half_after_one_fail_one_success(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        # First: fail (max_iterations=1 prevents retries)
        mock_exec.execute.return_value = _make_code_output(success=False, error="NameError: x")
        await p.execute(ACEInput(task="task one", max_iterations=1), ctx)
        # Second: succeed
        mock_exec.execute.return_value = _make_code_output(success=True)
        await p.execute(ACEInput(task="fibonacci", max_iterations=1), ctx)
        assert p.success_rate == pytest.approx(0.5)


# ============================================================
# TestSelfLearningCodePrimitive — learning behaviour
# ============================================================


class TestSelfLearningCodePrimitiveLearning:
    async def test_recursion_error_adds_two_strategies(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """RecursionError → _learn_from_failure adds exactly 2 strategies."""
        # Arrange
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=False,
            error="RecursionError: maximum recursion depth exceeded",
        )
        # Act
        result = await p.execute(ACEInput(task="generic recursion task", max_iterations=1), ctx)
        # Assert
        assert result["strategies_learned"] >= 2
        assert p.playbook_size >= 2

    async def test_name_error_adds_at_least_one_strategy(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=False, error="NameError: name 'x' is not defined"
        )
        result = await p.execute(ACEInput(task="generic task", max_iterations=1), ctx)
        assert result["strategies_learned"] >= 1

    async def test_syntax_error_adds_at_least_one_strategy(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=False, error="SyntaxError: invalid syntax at line 3"
        )
        result = await p.execute(ACEInput(task="generic task", max_iterations=1), ctx)
        assert result["strategies_learned"] >= 1

    async def test_fast_execution_learns_performance_strategy(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """execution_time < 0.1s on success triggers 'current approach is performant'."""
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=True, output="done", execution_time=0.01
        )
        result = await p.execute(ACEInput(task="generic fast task"), ctx)
        assert result["execution_success"] is True
        assert result["strategies_learned"] >= 1

    async def test_prime_task_with_sqrt_learns_strategy(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """Prime code path generates int(n**0.5) → sqrt strategy learned."""
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(success=True, execution_time=0.01)
        result = await p.execute(ACEInput(task="generate prime numbers"), ctx)
        assert result["execution_success"] is True
        assert result["strategies_learned"] >= 1  # sqrt + performance strategies

    async def test_playbook_grows_across_multiple_executions(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """Playbook accumulates strategies and never shrinks."""
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=False, error="RecursionError: stack overflow"
        )
        await p.execute(ACEInput(task="task A", max_iterations=1), ctx)
        size_after_first = p.playbook_size
        mock_exec.execute.return_value = _make_code_output(
            success=False, error="NameError: z is not defined"
        )
        await p.execute(ACEInput(task="task B", max_iterations=1), ctx)
        assert p.playbook_size >= size_after_first

    async def test_identical_error_twice_no_duplicate_strategy(
        self, primitive: tuple, ctx: WorkflowContext
    ) -> None:
        """Same error type on two calls → strategy not duplicated in playbook."""
        p, mock_exec = primitive
        mock_exec.execute.return_value = _make_code_output(
            success=False, error="SyntaxError: bad syntax"
        )
        await p.execute(ACEInput(task="task A", max_iterations=1), ctx)
        size_after_first = p.playbook_size
        await p.execute(ACEInput(task="task B", max_iterations=1), ctx)
        assert p.playbook_size == size_after_first  # strategy already existed, not re-added


# ============================================================
# TestBenchmarkDataclasses
# ============================================================


class TestDifficultyLevel:
    def test_easy_value(self) -> None:
        assert DifficultyLevel.EASY.value == "easy"

    def test_medium_value(self) -> None:
        assert DifficultyLevel.MEDIUM.value == "medium"

    def test_hard_value(self) -> None:
        assert DifficultyLevel.HARD.value == "hard"

    def test_all_three_levels_exist(self) -> None:
        levels = {d.value for d in DifficultyLevel}
        assert levels == {"easy", "medium", "hard"}


class TestBenchmarkTask:
    def test_instantiation_with_required_fields(self) -> None:
        # Arrange / Act
        task = BenchmarkTask(
            id="test_id",
            name="Test Task",
            description="A test description",
            task="Do something useful",
            language="python",
            difficulty=DifficultyLevel.EASY,
            expected_patterns=["def", "return"],
            validation_criteria={"has_function": True},
        )
        # Assert
        assert task.id == "test_id"
        assert task.name == "Test Task"
        assert task.difficulty == DifficultyLevel.EASY
        assert task.language == "python"

    def test_default_max_iterations_is_three(self) -> None:
        task = BenchmarkTask(
            id="t",
            name="T",
            description="d",
            task="do",
            language="python",
            difficulty=DifficultyLevel.MEDIUM,
            expected_patterns=[],
            validation_criteria={},
        )
        assert task.max_iterations == 3

    def test_default_timeout_seconds_is_thirty(self) -> None:
        task = BenchmarkTask(
            id="t",
            name="T",
            description="d",
            task="do",
            language="python",
            difficulty=DifficultyLevel.HARD,
            expected_patterns=[],
            validation_criteria={},
        )
        assert task.timeout_seconds == 30

    def test_custom_max_iterations_stored(self) -> None:
        task = BenchmarkTask(
            id="t",
            name="T",
            description="d",
            task="do",
            language="python",
            difficulty=DifficultyLevel.MEDIUM,
            expected_patterns=[],
            validation_criteria={},
            max_iterations=7,
        )
        assert task.max_iterations == 7


class TestBenchmarkResult:
    def test_instantiation_with_all_fields(self) -> None:
        result = BenchmarkResult(
            task_id="easy_fib",
            task_name="Fibonacci",
            success=True,
            iterations_used=1,
            execution_time=0.5,
            strategies_learned=2,
            code_generated="def fib(): pass",
            error_message=None,
            patterns_found=["def", "return"],
            validation_passed=True,
        )
        assert result.task_id == "easy_fib"
        assert result.success is True
        assert result.error_message is None

    def test_metadata_defaults_to_empty_dict(self) -> None:
        result = BenchmarkResult(
            task_id="x",
            task_name="X",
            success=False,
            iterations_used=3,
            execution_time=1.0,
            strategies_learned=0,
            code_generated=None,
            error_message="timeout",
            patterns_found=[],
            validation_passed=False,
        )
        assert result.metadata == {}

    def test_metadata_custom_value_stored(self) -> None:
        result = BenchmarkResult(
            task_id="x",
            task_name="X",
            success=True,
            iterations_used=1,
            execution_time=0.1,
            strategies_learned=0,
            code_generated=None,
            error_message=None,
            patterns_found=[],
            validation_passed=True,
            metadata={"difficulty": "easy", "language": "python"},
        )
        assert result.metadata["difficulty"] == "easy"


# ============================================================
# TestBenchmarkSuite — initialization
# ============================================================


class TestBenchmarkSuiteInit:
    def test_instantiation_succeeds(self) -> None:
        suite = BenchmarkSuite()
        assert suite is not None

    def test_has_exactly_eight_predefined_tasks(self) -> None:
        suite = BenchmarkSuite()
        assert len(suite.tasks) == 8

    def test_all_task_ids_are_unique(self) -> None:
        suite = BenchmarkSuite()
        ids = [t.id for t in suite.tasks]
        assert len(ids) == len(set(ids))

    def test_has_at_least_one_easy_task(self) -> None:
        suite = BenchmarkSuite()
        easy = [t for t in suite.tasks if t.difficulty == DifficultyLevel.EASY]
        assert len(easy) >= 1

    def test_has_at_least_one_medium_task(self) -> None:
        suite = BenchmarkSuite()
        medium = [t for t in suite.tasks if t.difficulty == DifficultyLevel.MEDIUM]
        assert len(medium) >= 1

    def test_has_at_least_one_hard_task(self) -> None:
        suite = BenchmarkSuite()
        hard = [t for t in suite.tasks if t.difficulty == DifficultyLevel.HARD]
        assert len(hard) >= 1

    def test_all_tasks_have_nonempty_expected_patterns(self) -> None:
        suite = BenchmarkSuite()
        for task in suite.tasks:
            assert len(task.expected_patterns) > 0, f"{task.id} has empty expected_patterns"

    def test_all_tasks_have_nonempty_validation_criteria(self) -> None:
        suite = BenchmarkSuite()
        for task in suite.tasks:
            assert len(task.validation_criteria) > 0, f"{task.id} has empty validation_criteria"

    def test_all_tasks_use_python_language(self) -> None:
        suite = BenchmarkSuite()
        for task in suite.tasks:
            assert task.language == "python"

    def test_fibonacci_task_present(self) -> None:
        suite = BenchmarkSuite()
        ids = [t.id for t in suite.tasks]
        assert "easy_fibonacci" in ids

    def test_hard_lru_cache_task_present(self) -> None:
        suite = BenchmarkSuite()
        ids = [t.id for t in suite.tasks]
        assert "hard_lru_cache" in ids


# ============================================================
# TestBenchmarkSuite — _check_patterns
# ============================================================


class TestBenchmarkSuiteCheckPatterns:
    def setup_method(self) -> None:
        self.suite = BenchmarkSuite()

    def test_all_patterns_found_returns_full_list(self) -> None:
        # Arrange
        code = "def fibonacci(n): return n"
        patterns = ["def", "fibonacci", "return"]
        # Act
        found = self.suite._check_patterns(code, patterns)
        # Assert
        assert set(found) == set(patterns)

    def test_partial_match_returns_only_matching_subset(self) -> None:
        code = "def foo(): pass"
        patterns = ["def", "fibonacci", "return"]
        found = self.suite._check_patterns(code, patterns)
        assert "def" in found
        assert "fibonacci" not in found
        assert "return" not in found

    def test_no_match_returns_empty_list(self) -> None:
        code = "x = 1 + 2"
        found = self.suite._check_patterns(code, ["def", "class", "return"])
        assert found == []

    def test_matching_is_case_insensitive(self) -> None:
        code = "DEF FIBONACCI(): RETURN N"
        patterns = ["def", "fibonacci", "return"]
        found = self.suite._check_patterns(code, patterns)
        assert len(found) == 3

    def test_empty_patterns_list_returns_empty(self) -> None:
        found = self.suite._check_patterns("def foo(): pass", [])
        assert found == []

    def test_empty_code_returns_empty(self) -> None:
        found = self.suite._check_patterns("", ["def", "class"])
        assert found == []


# ============================================================
# TestBenchmarkSuite — _validate_criteria
# ============================================================


class TestBenchmarkSuiteValidateCriteria:
    def setup_method(self) -> None:
        self.suite = BenchmarkSuite()

    def test_has_function_passes_with_def(self) -> None:
        assert (
            self.suite._validate_criteria("def my_func(x): return x", {"has_function": True})
            is True
        )

    def test_has_function_fails_without_def(self) -> None:
        assert self.suite._validate_criteria("x = 1 + 2", {"has_function": True}) is False

    def test_has_class_passes_with_class_keyword(self) -> None:
        assert self.suite._validate_criteria("class MyClass: pass", {"has_class": True}) is True

    def test_has_class_fails_without_class_keyword(self) -> None:
        assert self.suite._validate_criteria("def func(): pass", {"has_class": True}) is False

    def test_has_return_passes(self) -> None:
        assert self.suite._validate_criteria("def f(): return 1", {"has_return": True}) is True

    def test_has_return_fails_when_absent(self) -> None:
        assert self.suite._validate_criteria("def f(): print('hi')", {"has_return": True}) is False

    def test_has_loop_passes_with_for(self) -> None:
        assert (
            self.suite._validate_criteria("for i in range(10): print(i)", {"has_loop": True})
            is True
        )

    def test_has_loop_passes_with_while(self) -> None:
        assert self.suite._validate_criteria("while True: break", {"has_loop": True}) is True

    def test_has_loop_fails_without_loop(self) -> None:
        assert self.suite._validate_criteria("def f(): return 1", {"has_loop": True}) is False

    def test_empty_code_always_fails(self) -> None:
        assert self.suite._validate_criteria("", {"has_function": True}) is False

    def test_multiple_criteria_all_passing(self) -> None:
        code = "def func(): return 1"
        assert (
            self.suite._validate_criteria(code, {"has_function": True, "has_return": True}) is True
        )

    def test_multiple_criteria_one_failing(self) -> None:
        code = "def func(): print(1)"  # has function but NOT return
        assert (
            self.suite._validate_criteria(code, {"has_function": True, "has_return": True}) is False
        )

    def test_unknown_criterion_key_does_not_fail_validation(self) -> None:
        """Unhandled criterion keys (has_recursion etc.) must not block pass."""
        code = "def func(): return 1"
        assert (
            self.suite._validate_criteria(code, {"has_function": True, "has_recursion": True})
            is True
        )

    def test_empty_criteria_dict_passes_vacuously(self) -> None:
        assert self.suite._validate_criteria("def f(): pass", {}) is True


# ============================================================
# TestBenchmarkSuite — run_benchmark / run_all_benchmarks
# ============================================================


class TestBenchmarkSuiteRunBenchmark:
    def _mock_learner(
        self,
        code: str = "def fibonacci(n): return n",
        success: bool = True,
        strategies: int = 1,
    ) -> MagicMock:
        """Build a mock learner returning a predictable ACEOutput."""
        mock_learner = MagicMock()
        mock_learner.execute = AsyncMock(
            return_value={
                "execution_success": success,
                "code_generated": code,
                "strategies_learned": strategies if success else 0,
                "playbook_size": strategies,
                "improvement_score": 0.1 if success else 0.0,
                "learning_summary": "Execution succeeded" if success else "Execution failed",
                "result": "output" if success else "",
            }
        )
        return mock_learner

    async def test_returns_benchmark_result_instance(self, ctx: WorkflowContext) -> None:
        # Arrange
        suite = BenchmarkSuite()
        task = suite.tasks[0]  # easy_fibonacci
        # Act
        result = await suite.run_benchmark(task, self._mock_learner(), ctx)
        # Assert
        assert isinstance(result, BenchmarkResult)
        assert result.task_id == task.id
        assert result.task_name == task.name

    async def test_execution_time_is_non_negative(self, ctx: WorkflowContext) -> None:
        suite = BenchmarkSuite()
        result = await suite.run_benchmark(suite.tasks[0], self._mock_learner(), ctx)
        assert result.execution_time >= 0

    async def test_validation_failure_when_code_missing_criteria(
        self, ctx: WorkflowContext
    ) -> None:
        """Execution success=True but code fails validation → overall success=False."""
        suite = BenchmarkSuite()
        task = suite.tasks[0]  # easy_fibonacci: needs "def", "return"
        learner = self._mock_learner(code="x = 1 + 2", success=True)
        result = await suite.run_benchmark(task, learner, ctx)
        assert result.validation_passed is False
        assert result.success is False

    async def test_exception_from_learner_captured_in_error_message(
        self, ctx: WorkflowContext
    ) -> None:
        """If learner.execute raises, error_message is set and success=False."""
        suite = BenchmarkSuite()
        mock_learner = MagicMock()
        mock_learner.execute = AsyncMock(side_effect=RuntimeError("sandbox exploded"))
        result = await suite.run_benchmark(suite.tasks[0], mock_learner, ctx)
        assert result.success is False
        assert result.error_message is not None
        assert "sandbox exploded" in result.error_message

    async def test_patterns_found_populated_correctly(self, ctx: WorkflowContext) -> None:
        suite = BenchmarkSuite()
        task = suite.tasks[0]  # expected_patterns: ["def", "fibonacci", "return"]
        learner = self._mock_learner(code="def fibonacci(n): return n")
        result = await suite.run_benchmark(task, learner, ctx)
        assert len(result.patterns_found) > 0
        assert "def" in result.patterns_found

    async def test_metadata_includes_difficulty(self, ctx: WorkflowContext) -> None:
        suite = BenchmarkSuite()
        task = suite.tasks[0]
        result = await suite.run_benchmark(task, self._mock_learner(), ctx)
        assert "difficulty" in result.metadata
        assert result.metadata["difficulty"] == task.difficulty.value

    async def test_run_all_benchmarks_returns_one_result_per_task(
        self, ctx: WorkflowContext
    ) -> None:
        # Arrange
        suite = BenchmarkSuite()
        # Act
        results = await suite.run_all_benchmarks(self._mock_learner(), ctx)
        # Assert
        assert len(results) == len(suite.tasks)
        assert all(isinstance(r, BenchmarkResult) for r in results)

    async def test_run_all_benchmarks_works_without_context_arg(self) -> None:
        """run_all_benchmarks must auto-create WorkflowContext when none passed."""
        suite = BenchmarkSuite()
        mock_learner = MagicMock()
        mock_learner.execute = AsyncMock(
            return_value={
                "execution_success": True,
                "code_generated": "def func(): return 1",
                "strategies_learned": 0,
                "playbook_size": 0,
                "improvement_score": 0.0,
                "learning_summary": "ok",
                "result": "",
            }
        )
        results = await suite.run_all_benchmarks(mock_learner)  # no ctx arg
        assert len(results) == len(suite.tasks)


# ============================================================
# TestBenchmarkSuite — print_summary
# ============================================================


class TestBenchmarkSuitePrintSummary:
    def _make_result(
        self,
        task_id: str = "t1",
        name: str = "Test",
        success: bool = True,
        difficulty: str = "easy",
        error: str | None = None,
    ) -> BenchmarkResult:
        return BenchmarkResult(
            task_id=task_id,
            task_name=name,
            success=success,
            iterations_used=1,
            execution_time=0.1,
            strategies_learned=0,
            code_generated=None,
            error_message=error,
            patterns_found=[],
            validation_passed=success,
            metadata={"difficulty": difficulty, "language": "python"},
        )

    def test_print_summary_does_not_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        suite = BenchmarkSuite()
        suite.print_summary([self._make_result()])
        out = capsys.readouterr().out
        assert "Benchmark" in out

    def test_print_summary_includes_failed_task_name(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        suite = BenchmarkSuite()
        suite.print_summary([self._make_result(name="Failing Task", success=False, error="boom")])
        out = capsys.readouterr().out
        assert "Failing Task" in out

    def test_print_summary_shows_difficulty_in_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        suite = BenchmarkSuite()
        results = [
            self._make_result("e1", difficulty="easy"),
            self._make_result("m1", difficulty="medium", success=False),
        ]
        suite.print_summary(results)
        out = capsys.readouterr().out
        assert "easy" in out.lower() or "medium" in out.lower()


# ============================================================
# TestBenchmarkSuite — export_results
# ============================================================


class TestBenchmarkSuiteExportResults:
    def _make_result(self, task_id: str = "r1", success: bool = True) -> BenchmarkResult:
        return BenchmarkResult(
            task_id=task_id,
            task_name="Task Name",
            success=success,
            iterations_used=2,
            execution_time=0.5,
            strategies_learned=1,
            code_generated="def f(): pass",
            error_message=None,
            patterns_found=["def"],
            validation_passed=success,
            metadata={"difficulty": "easy", "language": "python"},
        )

    def test_export_creates_file_on_disk(self, tmp_path: Path) -> None:
        suite = BenchmarkSuite()
        output_file = tmp_path / "results.json"
        suite.export_results([self._make_result()], output_file)
        assert output_file.exists()

    def test_export_json_has_summary_and_results_keys(self, tmp_path: Path) -> None:
        suite = BenchmarkSuite()
        output_file = tmp_path / "results.json"
        suite.export_results([self._make_result()], output_file)
        data = json.loads(output_file.read_text())
        assert "summary" in data
        assert "results" in data

    def test_export_summary_counts_correct(self, tmp_path: Path) -> None:
        suite = BenchmarkSuite()
        results = [
            self._make_result("r1", success=True),
            self._make_result("r2", success=False),
            self._make_result("r3", success=True),
        ]
        output_file = tmp_path / "results.json"
        suite.export_results(results, output_file)
        data = json.loads(output_file.read_text())
        assert data["summary"]["total_tasks"] == 3
        assert data["summary"]["successful"] == 2

    def test_export_results_list_contains_correct_task_id(self, tmp_path: Path) -> None:
        suite = BenchmarkSuite()
        output_file = tmp_path / "results.json"
        suite.export_results([self._make_result("unique_id_42")], output_file)
        data = json.loads(output_file.read_text())
        assert data["results"][0]["task_id"] == "unique_id_42"

    def test_export_total_strategies_learned_summed(self, tmp_path: Path) -> None:
        suite = BenchmarkSuite()
        results = [self._make_result() for _ in range(4)]  # each strategies_learned=1
        output_file = tmp_path / "results.json"
        suite.export_results(results, output_file)
        data = json.loads(output_file.read_text())
        assert data["summary"]["total_strategies_learned"] == 4

    def test_export_empty_results_list_does_not_crash(self, tmp_path: Path) -> None:
        """Exporting an empty list must produce valid JSON without ZeroDivisionError."""
        suite = BenchmarkSuite()
        output_file = tmp_path / "empty.json"
        suite.export_results([], output_file)
        data = json.loads(output_file.read_text())
        assert data["summary"]["total_tasks"] == 0
        assert data["results"] == []
