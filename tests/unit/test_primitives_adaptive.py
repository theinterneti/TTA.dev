"""Tests for adaptive/self-improving primitives."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from ttadev.primitives.adaptive import (
    AdaptiveCachePrimitive,
    AdaptiveFallbackPrimitive,
    AdaptiveMetrics,
    AdaptiveRetryPrimitive,
    AdaptiveTimeoutPrimitive,
    LearningMode,
    LearningStrategy,
    StrategyMetrics,
    get_adaptive_metrics,
    reset_adaptive_metrics,
)
from ttadev.primitives.adaptive.exceptions import (
    AdaptiveError,
    CircuitBreakerError,
    ContextExtractionError,
    LearningError,
    PerformanceRegressionError,
    StrategyAdaptationError,
    StrategyNotFoundError,
    StrategyValidationError,
    ValidationWindowError,
)
from ttadev.primitives.adaptive.retry import RetryStrategyParams
from ttadev.primitives.adaptive.timeout import TimeoutError as AdaptiveTimeoutError
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**metadata: Any) -> WorkflowContext:
    """Return a WorkflowContext with given metadata for test isolation."""
    return WorkflowContext(workflow_id="test", metadata=metadata)


def _make_retry(
    target: MockPrimitive | None = None,
    learning_mode: LearningMode = LearningMode.OBSERVE,
    max_retries: int = 1,
) -> AdaptiveRetryPrimitive:
    """Build an AdaptiveRetryPrimitive with zero-delay baseline for fast tests."""
    target = target or MockPrimitive("target", return_value={"ok": True})
    primitive = AdaptiveRetryPrimitive(
        target_primitive=target,
        learning_mode=learning_mode,
    )
    # Zero out delays so retry tests complete instantly
    params = primitive.strategies["baseline_exponential"].parameters
    params["initial_delay"] = 0.0
    params["max_delay"] = 0.0
    params["max_retries"] = max_retries
    return primitive


# ===========================================================================
# TestStrategyMetrics
# ===========================================================================


@pytest.mark.unit
class TestStrategyMetrics:
    """Unit tests for the StrategyMetrics dataclass."""

    def test_default_values(self):
        """StrategyMetrics initialises with all-zero counts and empty context set."""
        # Arrange / Act
        m = StrategyMetrics()

        # Assert
        assert m.success_count == 0
        assert m.failure_count == 0
        assert m.total_latency == 0.0
        assert m.total_executions == 0
        assert m.contexts_seen == set()

    def test_success_rate_zero_executions_returns_zero(self):
        """success_rate returns 0.0 when no executions have been recorded."""
        m = StrategyMetrics()
        assert m.success_rate == 0.0

    def test_failure_rate_zero_executions_returns_one(self):
        """failure_rate is 1.0 (1 - success_rate) when no executions recorded."""
        m = StrategyMetrics()
        assert m.failure_rate == 1.0

    def test_update_success_increments_success_count(self):
        """update(success=True) increments success_count and total_latency."""
        # Arrange
        m = StrategyMetrics()

        # Act
        m.update(success=True, latency=0.5, context_key="ctx_a")

        # Assert
        assert m.success_count == 1
        assert m.total_executions == 1
        assert m.total_latency == pytest.approx(0.5)
        assert m.failure_count == 0

    def test_update_failure_increments_failure_count_not_latency(self):
        """update(success=False) increments failure_count but NOT total_latency."""
        m = StrategyMetrics()
        m.update(success=False, latency=0.1, context_key="ctx_b")

        assert m.failure_count == 1
        assert m.success_count == 0
        assert m.total_executions == 1
        assert m.total_latency == 0.0

    def test_success_rate_calculated_correctly(self):
        """success_rate equals successes / total_executions."""
        m = StrategyMetrics()
        m.update(True, 0.1, "k")
        m.update(True, 0.2, "k")
        m.update(False, 0.0, "k")

        assert m.success_rate == pytest.approx(2 / 3)

    def test_avg_latency_no_successes_returns_infinity(self):
        """avg_latency returns inf when no successful executions exist."""
        m = StrategyMetrics()
        m.update(False, 0.0, "k")

        assert m.avg_latency == float("inf")

    def test_avg_latency_calculated_correctly(self):
        """avg_latency equals total_latency / success_count."""
        m = StrategyMetrics()
        m.update(True, 1.0, "k")
        m.update(True, 3.0, "k")

        assert m.avg_latency == pytest.approx(2.0)

    def test_failure_rate_is_complement_of_success_rate(self):
        """failure_rate + success_rate == 1.0 for any metrics state."""
        m = StrategyMetrics()
        m.update(True, 0.1, "k")
        m.update(False, 0.0, "k")

        assert m.success_rate + m.failure_rate == pytest.approx(1.0)

    def test_contexts_tracked_as_unique_set(self):
        """Unique context keys are recorded in contexts_seen; duplicates ignored."""
        m = StrategyMetrics()
        m.update(True, 0.1, "ctx_a")
        m.update(True, 0.1, "ctx_b")
        m.update(True, 0.1, "ctx_a")  # duplicate

        assert m.contexts_seen == {"ctx_a", "ctx_b"}

    def test_is_better_than_requires_minimum_sample_size(self):
        """is_better_than returns False when either strategy has < 10 executions."""
        # Arrange – only 9 runs
        good = StrategyMetrics()
        base = StrategyMetrics()
        for _ in range(9):
            good.update(True, 0.1, "k")
            base.update(False, 0.0, "k")

        # Act / Assert
        assert good.is_better_than(base) is False

    def test_is_better_than_returns_true_for_significant_improvement(self):
        """is_better_than is True when success_rate improvement >= significance_threshold."""
        # Arrange – base 50% vs candidate 100% at same latency
        base = StrategyMetrics()
        candidate = StrategyMetrics()
        for _ in range(20):
            base.update(True, 0.5, "k")
            base.update(False, 0.0, "k")
            candidate.update(True, 0.5, "k")

        assert candidate.is_better_than(base) is True

    def test_is_better_than_false_when_latency_too_much_worse(self):
        """is_better_than is False when candidate latency > 110% of baseline."""
        base = StrategyMetrics()
        candidate = StrategyMetrics()
        for _ in range(15):
            base.update(True, 1.0, "k")
            candidate.update(True, 6.0, "k")  # 6× slower

        assert candidate.is_better_than(base) is False

    def test_multiple_updates_accumulate(self):
        """Multiple update calls accumulate counts correctly."""
        m = StrategyMetrics()
        for i in range(5):
            m.update(True, float(i), "k")
        for _ in range(3):
            m.update(False, 0.0, "k")

        assert m.total_executions == 8
        assert m.success_count == 5
        assert m.failure_count == 3


# ===========================================================================
# TestLearningStrategy
# ===========================================================================


@pytest.mark.unit
class TestLearningStrategy:
    """Unit tests for the LearningStrategy dataclass."""

    def _strategy(self, pattern: str = "prod") -> LearningStrategy:
        return LearningStrategy(
            name="test_strategy",
            description="A test strategy",
            parameters={"max_retries": 3},
            context_pattern=pattern,
        )

    def test_construction_stores_all_fields(self):
        """LearningStrategy stores name, description, parameters, and context_pattern."""
        s = self._strategy()

        assert s.name == "test_strategy"
        assert s.description == "A test strategy"
        assert s.parameters == {"max_retries": 3}
        assert s.context_pattern == "prod"

    def test_default_validation_state_is_false(self):
        """New strategy is not validated and has zero validation attempts."""
        s = self._strategy()
        assert s.is_validated is False
        assert s.validation_attempts == 0
        assert s.validation_successes == 0

    def test_matches_context_true_when_pattern_in_key(self):
        """matches_context returns True when context_pattern is in the lowercased key."""
        s = self._strategy(pattern="prod")
        assert s.matches_context("env:production|priority:high") is True

    def test_matches_context_false_when_pattern_absent(self):
        """matches_context returns False when pattern does not appear in the key."""
        s = self._strategy(pattern="staging")
        assert s.matches_context("env:production|priority:high") is False

    def test_matches_context_is_case_insensitive(self):
        """matches_context compares against the lowercased version of context_key."""
        s = self._strategy(pattern="production")
        assert s.matches_context("env:PRODUCTION|priority:high") is True

    def test_empty_pattern_matches_everything(self):
        """Empty context_pattern is a substring of any string, so it always matches."""
        s = self._strategy(pattern="")
        assert s.matches_context("anything:goes:here") is True

    def test_record_usage_success_updates_metrics(self):
        """record_usage(success=True) delegates correctly to StrategyMetrics."""
        s = self._strategy()
        s.record_usage(success=True, latency=0.3, context_key="ctx_a")

        assert s.metrics.success_count == 1
        assert s.metrics.total_executions == 1

    def test_record_usage_failure_updates_failure_count(self):
        """record_usage(success=False) increments failure_count in metrics."""
        s = self._strategy()
        s.record_usage(success=False, latency=0.0, context_key="ctx_a")

        assert s.metrics.failure_count == 1

    def test_record_validation_below_threshold_not_validated(self):
        """Strategy is NOT validated until at least 5 validation attempts are made."""
        s = self._strategy()
        for _ in range(4):
            s.record_validation(True)

        assert s.is_validated is False
        assert s.validation_attempts == 4

    def test_record_validation_five_passing_marks_validated(self):
        """Five 100%-successful validations set is_validated=True."""
        s = self._strategy()
        for _ in range(5):
            s.record_validation(True)

        assert s.is_validated is True

    def test_record_validation_all_failing_stays_false(self):
        """If all 5 validations fail (0% success), is_validated stays False."""
        s = self._strategy()
        for _ in range(5):
            s.record_validation(False)

        assert s.is_validated is False

    def test_record_validation_eighty_percent_validates(self):
        """4 of 5 validations (80%) sets is_validated=True (meets 80% threshold)."""
        s = self._strategy()
        for _ in range(4):
            s.record_validation(True)
        s.record_validation(False)

        assert s.is_validated is True


# ===========================================================================
# TestLearningMode
# ===========================================================================


@pytest.mark.unit
class TestLearningMode:
    """Tests for the LearningMode enum."""

    def test_four_modes_exist(self):
        """All four expected learning modes are defined."""
        modes = {m.value for m in LearningMode}
        assert modes == {"disabled", "observe", "validate", "active"}

    def test_disabled_value(self):
        """LearningMode.DISABLED has value 'disabled'."""
        assert LearningMode.DISABLED.value == "disabled"

    def test_observe_value(self):
        """LearningMode.OBSERVE has value 'observe'."""
        assert LearningMode.OBSERVE.value == "observe"

    def test_validate_value(self):
        """LearningMode.VALIDATE has value 'validate'."""
        assert LearningMode.VALIDATE.value == "validate"

    def test_active_value(self):
        """LearningMode.ACTIVE has value 'active'."""
        assert LearningMode.ACTIVE.value == "active"

    def test_modes_are_distinct(self):
        """All four LearningMode members are different from one another."""
        modes = list(LearningMode)
        assert len(set(modes)) == 4


# ===========================================================================
# TestExceptions
# ===========================================================================


@pytest.mark.unit
class TestExceptions:
    """Tests for the custom exception hierarchy in adaptive.exceptions."""

    def test_adaptive_error_is_exception(self):
        """AdaptiveError subclasses Exception."""
        assert issubclass(AdaptiveError, Exception)

    def test_learning_error_inherits_adaptive(self):
        """LearningError is an AdaptiveError."""
        assert issubclass(LearningError, AdaptiveError)

    def test_strategy_validation_inherits_learning(self):
        """StrategyValidationError is a LearningError."""
        assert issubclass(StrategyValidationError, LearningError)

    def test_strategy_adaptation_inherits_learning(self):
        """StrategyAdaptationError is a LearningError."""
        assert issubclass(StrategyAdaptationError, LearningError)

    def test_context_extraction_inherits_adaptive(self):
        """ContextExtractionError is an AdaptiveError."""
        assert issubclass(ContextExtractionError, AdaptiveError)

    def test_validation_window_inherits_learning(self):
        """ValidationWindowError is a LearningError."""
        assert issubclass(ValidationWindowError, LearningError)

    def test_performance_regression_inherits_strategy_validation(self):
        """PerformanceRegressionError is a StrategyValidationError."""
        assert issubclass(PerformanceRegressionError, StrategyValidationError)

    def test_circuit_breaker_inherits_adaptive(self):
        """CircuitBreakerError is an AdaptiveError."""
        assert issubclass(CircuitBreakerError, AdaptiveError)

    def test_strategy_not_found_inherits_adaptive(self):
        """StrategyNotFoundError is an AdaptiveError."""
        assert issubclass(StrategyNotFoundError, AdaptiveError)

    def test_circuit_breaker_basic_message(self):
        """CircuitBreakerError stores and includes the message text."""
        err = CircuitBreakerError("CB triggered")
        assert "CB triggered" in str(err)

    def test_circuit_breaker_with_failure_rate(self):
        """CircuitBreakerError embeds failure_rate as a percentage in its message."""
        err = CircuitBreakerError("CB triggered", failure_rate=0.75)
        assert err.failure_rate == pytest.approx(0.75)
        assert "75.0%" in str(err)

    def test_circuit_breaker_with_cooldown(self):
        """CircuitBreakerError embeds cooldown_seconds in its message."""
        err = CircuitBreakerError("CB triggered", cooldown_seconds=60.0)
        assert err.cooldown_seconds == pytest.approx(60.0)
        assert "60.0" in str(err)

    def test_circuit_breaker_default_message_not_empty(self):
        """CircuitBreakerError() without args has a non-empty default message."""
        err = CircuitBreakerError()
        assert str(err) != ""

    def test_strategy_not_found_carries_name(self):
        """StrategyNotFoundError stores the missing strategy name."""
        err = StrategyNotFoundError("my_strategy")
        assert err.strategy_name == "my_strategy"
        assert "my_strategy" in str(err)
        assert err.available_strategies is None

    def test_strategy_not_found_lists_alternatives(self):
        """StrategyNotFoundError lists available strategy names in its message."""
        err = StrategyNotFoundError("x", available_strategies=["alpha", "beta"])
        assert "alpha" in str(err)
        assert "beta" in str(err)
        assert err.available_strategies == ["alpha", "beta"]

    def test_performance_regression_stores_all_attributes(self):
        """PerformanceRegressionError stores and formats all regression details."""
        err = PerformanceRegressionError(
            strategy_name="new_v2",
            metric_name="success_rate",
            strategy_value=0.70,
            baseline_value=0.90,
        )
        assert err.strategy_name == "new_v2"
        assert err.metric_name == "success_rate"
        assert err.strategy_value == pytest.approx(0.70)
        assert err.baseline_value == pytest.approx(0.90)
        assert "new_v2" in str(err)
        assert "success_rate" in str(err)

    def test_all_exceptions_catchable_as_adaptive_error(self):
        """Every custom exception can be caught with a single 'except AdaptiveError'."""
        exceptions: list[AdaptiveError] = [
            LearningError("le"),
            StrategyValidationError("sv"),
            StrategyAdaptationError("sa"),
            CircuitBreakerError(),
            ContextExtractionError("ce"),
            ValidationWindowError("vw"),
            StrategyNotFoundError("x"),
        ]
        for exc in exceptions:
            with pytest.raises(AdaptiveError):
                raise exc


# ===========================================================================
# TestAdaptiveMetrics
# ===========================================================================


@pytest.mark.unit
class TestAdaptiveMetrics:
    """Tests for AdaptiveMetrics — graceful no-OTel degradation."""

    def setup_method(self):
        """Reset the module-level singleton before each test."""
        reset_adaptive_metrics()

    def test_instantiation_succeeds(self):
        """AdaptiveMetrics can be created without errors regardless of OTel."""
        m = AdaptiveMetrics()
        assert m is not None

    def test_enabled_property_is_bool(self):
        """'enabled' property is always a bool (True iff OTel is available)."""
        m = AdaptiveMetrics()
        assert isinstance(m.enabled, bool)

    def test_record_strategy_created_no_crash(self):
        """record_strategy_created silently succeeds even without OTel."""
        AdaptiveMetrics().record_strategy_created("Retry", "prod_v1", "production")

    def test_record_strategy_adopted_no_crash(self):
        """record_strategy_adopted silently succeeds even without OTel."""
        AdaptiveMetrics().record_strategy_adopted("Retry", "prod_v1")

    def test_record_strategy_rejected_no_crash(self):
        """record_strategy_rejected silently succeeds even without OTel."""
        AdaptiveMetrics().record_strategy_rejected("Retry", "prod_v1", "perf_regression")

    def test_record_learning_rate_no_crash(self):
        """record_learning_rate silently succeeds even without OTel."""
        AdaptiveMetrics().record_learning_rate("Retry", 5.0)

    def test_record_validation_success_no_crash(self):
        """record_validation_success silently succeeds even without OTel."""
        AdaptiveMetrics().record_validation_success("Retry", "prod_v1", 1.5)

    def test_record_validation_failure_no_crash(self):
        """record_validation_failure silently succeeds even without OTel."""
        AdaptiveMetrics().record_validation_failure("Retry", "prod_v1", "low_success", 0.5)

    def test_record_strategy_execution_no_crash(self):
        """record_strategy_execution silently succeeds even without OTel."""
        AdaptiveMetrics().record_strategy_execution(
            "Retry", "prod_v1", success_rate=0.95, latency_ms=250.0
        )

    def test_record_strategy_execution_custom_metrics_no_crash(self):
        """record_strategy_execution with custom_metrics silently succeeds."""
        AdaptiveMetrics().record_strategy_execution(
            "Retry", "prod_v1", custom_metrics={"p99_ms": 500.0}
        )

    def test_record_performance_improvement_no_crash(self):
        """record_performance_improvement silently succeeds even without OTel."""
        AdaptiveMetrics().record_performance_improvement("Retry", "success_rate", 12.5)

    def test_record_circuit_breaker_trip_no_crash(self):
        """record_circuit_breaker_trip silently succeeds even without OTel."""
        AdaptiveMetrics().record_circuit_breaker_trip("Retry", "high_failure_rate")

    def test_record_circuit_breaker_reset_no_crash(self):
        """record_circuit_breaker_reset silently succeeds even without OTel."""
        AdaptiveMetrics().record_circuit_breaker_reset("Retry")

    def test_record_fallback_activation_no_crash(self):
        """record_fallback_activation silently succeeds even without OTel."""
        AdaptiveMetrics().record_fallback_activation("Retry", "circuit_breaker")

    def test_record_context_switch_no_crash(self):
        """record_context_switch silently succeeds even without OTel."""
        AdaptiveMetrics().record_context_switch("Retry", "production", "staging")

    def test_record_context_drift_no_crash(self):
        """record_context_drift silently succeeds even without OTel."""
        AdaptiveMetrics().record_context_drift("Retry", "production")

    def test_update_active_strategies_no_crash(self):
        """update_active_strategies silently succeeds even without OTel."""
        m = AdaptiveMetrics()
        m.update_active_strategies("Retry", +1)
        m.update_active_strategies("Retry", -1)

    def test_get_adaptive_metrics_returns_singleton(self):
        """get_adaptive_metrics returns the same instance on repeated calls."""
        m1 = get_adaptive_metrics()
        m2 = get_adaptive_metrics()
        assert m1 is m2

    def test_reset_adaptive_metrics_clears_singleton(self):
        """After reset_adaptive_metrics(), get_adaptive_metrics() returns a new object."""
        m1 = get_adaptive_metrics()
        reset_adaptive_metrics()
        m2 = get_adaptive_metrics()
        assert m1 is not m2


# ===========================================================================
# TestRetryStrategyParams
# ===========================================================================


@pytest.mark.unit
class TestRetryStrategyParams:
    """Tests for RetryStrategyParams serialisation and defaults."""

    def test_default_values_are_conservative(self):
        """Default RetryStrategyParams has sensible conservative defaults."""
        p = RetryStrategyParams()
        assert p.max_retries == 3
        assert p.initial_delay == pytest.approx(1.0)
        assert p.backoff_factor == pytest.approx(2.0)
        assert p.max_delay == pytest.approx(60.0)
        assert p.jitter is True
        assert p.jitter_factor == pytest.approx(0.1)

    def test_to_dict_contains_all_fields(self):
        """to_dict serialises every field of the dataclass."""
        p = RetryStrategyParams(max_retries=5, initial_delay=0.5)
        d = p.to_dict()

        assert d["max_retries"] == 5
        assert d["initial_delay"] == pytest.approx(0.5)
        assert "backoff_factor" in d
        assert "max_delay" in d
        assert "jitter" in d
        assert "jitter_factor" in d

    def test_from_dict_round_trip_preserves_values(self):
        """from_dict(to_dict(p)) recreates an identical RetryStrategyParams."""
        original = RetryStrategyParams(max_retries=7, initial_delay=2.0, jitter=False)
        restored = RetryStrategyParams.from_dict(original.to_dict())

        assert restored.max_retries == 7
        assert restored.initial_delay == pytest.approx(2.0)
        assert restored.jitter is False

    def test_from_dict_custom_all_fields(self):
        """from_dict accepts a fully-specified parameter dict."""
        d = {
            "max_retries": 10,
            "initial_delay": 0.25,
            "backoff_factor": 1.5,
            "max_delay": 30.0,
            "jitter": False,
            "jitter_factor": 0.05,
        }
        p = RetryStrategyParams.from_dict(d)
        assert p.max_retries == 10
        assert p.backoff_factor == pytest.approx(1.5)
        assert p.jitter is False


# ===========================================================================
# TestAdaptiveRetryPrimitive
# ===========================================================================


@pytest.mark.unit
class TestAdaptiveRetryPrimitive:
    """Tests for AdaptiveRetryPrimitive — retry with adaptive strategy learning."""

    def test_construction_stores_target(self):
        """target_primitive is accessible after construction."""
        target = MockPrimitive("t", return_value={"x": 1})
        retry = AdaptiveRetryPrimitive(target_primitive=target)
        assert retry.target_primitive is target

    def test_baseline_strategy_created_on_init(self):
        """Constructor registers the baseline_exponential strategy."""
        retry = _make_retry()
        assert "baseline_exponential" in retry.strategies
        assert retry.baseline_strategy is not None

    def test_baseline_strategy_name(self):
        """Baseline strategy name is 'baseline_exponential'."""
        retry = _make_retry()
        assert retry.baseline_strategy.name == "baseline_exponential"

    def test_default_learning_mode_is_validate(self):
        """Default learning_mode is VALIDATE without explicit argument."""
        target = MockPrimitive("t", return_value={})
        retry = AdaptiveRetryPrimitive(target_primitive=target)
        assert retry.learning_mode == LearningMode.VALIDATE

    def test_custom_learning_mode_stored(self):
        """Explicitly passing learning_mode=ACTIVE is stored correctly."""
        target = MockPrimitive("t", return_value={})
        retry = AdaptiveRetryPrimitive(target_primitive=target, learning_mode=LearningMode.ACTIVE)
        assert retry.learning_mode == LearningMode.ACTIVE

    def test_get_default_strategy_returns_learning_strategy(self):
        """_get_default_strategy returns a LearningStrategy with retry parameters."""
        retry = _make_retry()
        s = retry._get_default_strategy()
        assert isinstance(s, LearningStrategy)
        assert "max_retries" in s.parameters

    async def test_execute_target_success_first_attempt(self):
        """When target succeeds immediately, result has success=True and attempts=1."""
        # Arrange
        target = MockPrimitive("t", return_value={"data": "ok"})
        retry = _make_retry(target=target)
        ctx = _ctx(environment="test")

        # Act
        result = await retry.execute({"input": "x"}, ctx)

        # Assert
        assert result["success"] is True
        assert result["attempts"] == 1
        assert result["result"] == {"data": "ok"}
        target.assert_called_once()

    async def test_execute_includes_strategy_used(self):
        """Result dict includes the name of the strategy that was applied."""
        target = MockPrimitive("t", return_value={})
        retry = _make_retry(target=target)

        result = await retry.execute({}, _ctx())

        assert result["strategy_used"] == "baseline_exponential"

    async def test_execute_all_retries_exhausted_returns_failure_dict(self):
        """When target always raises, result has success=False (no exception raised)."""
        # Arrange
        target = MockPrimitive("t", raise_error=ValueError("boom"))
        retry = _make_retry(target=target, max_retries=2)
        ctx = _ctx()

        # Act
        result = await retry.execute({"input": "x"}, ctx)

        # Assert
        assert result["success"] is False
        assert result["result"] is None
        assert result["attempts"] == 3  # max_retries=2 → 3 total attempts

    async def test_execute_failure_includes_error_type(self):
        """Failure result dict includes 'error' and 'error_type' fields."""
        target = MockPrimitive("t", raise_error=RuntimeError("kaboom"))
        retry = _make_retry(target=target, max_retries=0)

        result = await retry.execute({}, _ctx())

        assert "error" in result
        assert result["error_type"] == "RuntimeError"

    async def test_execute_updates_strategy_success_count(self):
        """Strategy success_count is incremented after a successful execute."""
        target = MockPrimitive("t", return_value={"ok": True})
        retry = _make_retry(target=target)

        await retry.execute({}, _ctx())

        assert retry.strategies["baseline_exponential"].metrics.success_count == 1

    async def test_execute_captures_error_in_result_on_failure(self):
        """When all retries are exhausted, result has success=False and error populated."""
        target = MockPrimitive("t", raise_error=RuntimeError("fail"))
        retry = _make_retry(target=target, max_retries=0)

        result = await retry.execute({}, _ctx())

        assert result["success"] is False
        assert "fail" in result["error"]
        assert result["error_type"] == "RuntimeError"
        # Strategy still records the execution completed (not an unhandled raise)
        assert retry.strategies["baseline_exponential"].metrics.total_executions >= 1

    async def test_execute_flaky_target_recovers_on_retry(self):
        """A target that fails once then succeeds returns success with attempts=2."""
        call_count = 0

        def flaky(input_data: Any, _ctx: WorkflowContext) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("transient")
            return {"recovered": True}

        target = MockPrimitive("flaky", side_effect=flaky)
        retry = _make_retry(target=target, max_retries=3)

        result = await retry.execute({"q": 1}, _ctx())

        assert result["success"] is True
        assert result["attempts"] == 2
        assert result["result"] == {"recovered": True}

    def test_get_learning_summary_required_keys(self):
        """get_learning_summary returns a dict with all expected top-level keys."""
        retry = _make_retry()
        summary = retry.get_learning_summary()

        required = {
            "learning_mode",
            "total_strategies",
            "circuit_breaker_active",
            "total_adaptations",
            "successful_adaptations",
            "context_drift_detections",
            "strategies",
        }
        assert required.issubset(summary.keys())

    def test_select_strategy_disabled_always_returns_baseline(self):
        """In DISABLED mode, _select_strategy always uses the baseline strategy."""
        target = MockPrimitive("t", return_value={})
        retry = AdaptiveRetryPrimitive(target_primitive=target, learning_mode=LearningMode.DISABLED)
        strategy = retry._select_strategy("any:context:key")
        assert strategy.name == "baseline_exponential"

    def test_select_strategy_no_match_falls_back_to_baseline(self):
        """When no registered strategy matches the context key, baseline is returned."""
        retry = _make_retry()
        retry.strategies["niche"] = LearningStrategy(
            name="niche",
            description="very specific",
            parameters={},
            context_pattern="xyzabc_never_matches",
        )
        strategy = retry._select_strategy("env:production|priority:high")
        assert strategy.name == "baseline_exponential"

    def test_circuit_breaker_initially_inactive(self):
        """circuit_breaker_active is False on a freshly created primitive."""
        retry = _make_retry()
        assert retry.circuit_breaker_active is False

    def test_activate_circuit_breaker_sets_flag(self):
        """_activate_circuit_breaker sets circuit_breaker_active=True."""
        retry = _make_retry()
        retry._activate_circuit_breaker(duration_seconds=300.0)
        assert retry.circuit_breaker_active is True

    def test_circuit_breaker_deactivates_after_expiry(self):
        """Circuit breaker auto-deactivates once its duration has elapsed."""
        retry = _make_retry()
        retry._activate_circuit_breaker(duration_seconds=0.001)
        time.sleep(0.02)  # let it expire
        retry._select_strategy("any_ctx")  # triggers expiry check
        assert retry.circuit_breaker_active is False

    async def test_context_extractor_embeds_environment_and_priority(self):
        """_context_extractor produces a key containing environment and priority."""
        retry = _make_retry()
        ctx = _ctx(environment="prod", priority="high")
        key = retry._context_extractor({"q": 1}, ctx)
        assert "prod" in key
        assert "high" in key

    async def test_consider_reducing_retries_creates_strategy(self):
        """_consider_reducing_retries adds a low_retry strategy when called directly."""
        target = MockPrimitive("t", return_value={})
        retry = AdaptiveRetryPrimitive(target_primitive=target, learning_mode=LearningMode.ACTIVE)
        strategy = retry.strategies["baseline_exponential"]
        context_key = "env:prod|priority:normal|time_sensitive:False|errors:general"

        initial_count = len(retry.strategies)
        await retry._consider_reducing_retries(context_key, strategy, _ctx())

        assert len(retry.strategies) == initial_count + 1
        assert retry.total_adaptations == 1

    async def test_consider_error_specific_strategy_for_timeout_error(self):
        """_consider_error_specific_strategy creates a TimeoutError-specific strategy."""
        target = MockPrimitive("t", return_value={})
        retry = AdaptiveRetryPrimitive(target_primitive=target, learning_mode=LearningMode.ACTIVE)
        initial_count = len(retry.strategies)
        await retry._consider_error_specific_strategy("env:prod", "TimeoutError", False, 3, _ctx())

        new = [s for name, s in retry.strategies.items() if "timeouterror" in name]
        assert len(new) == 1
        assert new[0].parameters["max_retries"] == 2
        assert len(retry.strategies) == initial_count + 1

    async def test_max_strategies_limit_prevents_new_creation(self):
        """No strategies are created once max_strategies is already reached."""
        target = MockPrimitive("t", return_value={})
        retry = AdaptiveRetryPrimitive(
            target_primitive=target,
            learning_mode=LearningMode.ACTIVE,
            max_strategies=1,  # baseline fills the limit
        )
        strategy = retry.strategies["baseline_exponential"]
        initial_count = len(retry.strategies)

        await retry._consider_reducing_retries("ctx_key", strategy, _ctx())

        assert len(retry.strategies) == initial_count  # unchanged


# ===========================================================================
# TestAdaptiveCachePrimitive
# ===========================================================================


@pytest.mark.unit
class TestAdaptiveCachePrimitive:
    """Tests for AdaptiveCachePrimitive — TTL-adaptive caching."""

    def _make_cache(
        self,
        target: MockPrimitive | None = None,
        mode: LearningMode = LearningMode.OBSERVE,
        ttl_seconds: float = 3600.0,
    ) -> AdaptiveCachePrimitive:
        """Build an AdaptiveCachePrimitive with a str-based key function."""
        target = target or MockPrimitive("target", return_value={"cached": True})
        cache = AdaptiveCachePrimitive(
            target_primitive=target,
            cache_key_fn=lambda data, ctx: str(data),
            learning_mode=mode,
        )
        cache.strategies["baseline_conservative"].parameters["ttl_seconds"] = ttl_seconds
        return cache

    def test_construction_registers_baseline_strategy(self):
        """Constructor registers baseline_conservative strategy."""
        cache = self._make_cache()
        assert "baseline_conservative" in cache.strategies
        assert cache.baseline_strategy is not None

    def test_get_default_strategy_has_required_parameters(self):
        """Default strategy has ttl_seconds, max_cache_size, and min_hit_rate."""
        cache = self._make_cache()
        s = cache._get_default_strategy()
        assert "ttl_seconds" in s.parameters
        assert "max_cache_size" in s.parameters
        assert "min_hit_rate" in s.parameters

    async def test_cache_miss_invokes_target(self):
        """First access is a cache miss and target primitive is executed."""
        target = MockPrimitive("t", return_value={"value": 99})
        cache = self._make_cache(target=target)

        result = await cache.execute({"q": "hello"}, _ctx())

        assert result == {"value": 99}
        target.assert_called_once()

    async def test_cache_hit_skips_target(self):
        """Second access with same input returns cached result without calling target."""
        target = MockPrimitive("t", return_value={"value": 99})
        cache = self._make_cache(target=target)
        data = {"q": "hello"}

        await cache.execute(data, _ctx())  # miss
        result = await cache.execute(data, _ctx())  # hit

        assert result == {"value": 99}
        assert target.call_count == 1

    async def test_cache_miss_after_ttl_expiry(self):
        """After TTL expires the entry is treated as a miss and target is re-invoked."""
        target = MockPrimitive("t", return_value={"v": 1})
        cache = self._make_cache(target=target, ttl_seconds=60.0)
        data = {"q": "expiry"}

        # Prime the cache
        await cache.execute(data, _ctx())

        # Backdate the entry to simulate expiry
        key = str(data)
        value, _, ck = cache._cache[key]
        cache._cache[key] = (value, time.time() - 7200, ck)  # 2 hours old

        await cache.execute(data, _ctx())

        assert target.call_count == 2

    async def test_clear_cache_removes_all_entries(self):
        """clear_cache empties the internal _cache dict entirely."""
        target = MockPrimitive("t", return_value={"x": 1})
        cache = self._make_cache(target=target)

        await cache.execute({"a": 1}, _ctx())
        await cache.execute({"b": 2}, _ctx())
        assert len(cache._cache) == 2

        cache.clear_cache()

        assert len(cache._cache) == 0

    async def test_evict_expired_removes_stale_only(self):
        """evict_expired removes entries older than TTL and returns their count."""
        target = MockPrimitive("t", return_value={"x": 1})
        cache = self._make_cache(target=target, ttl_seconds=60.0)

        await cache.execute({"k": "fresh"}, _ctx())
        await cache.execute({"k": "stale"}, _ctx())

        stale_key = str({"k": "stale"})
        v, _, ck = cache._cache[stale_key]
        cache._cache[stale_key] = (v, time.time() - 7200, ck)

        evicted = cache.evict_expired()

        assert evicted == 1
        assert stale_key not in cache._cache
        assert str({"k": "fresh"}) in cache._cache

    async def test_get_cache_stats_empty_state(self):
        """get_cache_stats on a fresh cache returns all-zero counts."""
        cache = self._make_cache()
        stats = cache.get_cache_stats()

        assert stats["total_size"] == 0
        assert stats["total_requests"] == 0
        assert stats["overall_hit_rate"] == 0.0

    async def test_get_cache_stats_tracks_hits_and_misses(self):
        """get_cache_stats correctly reports hits, misses, and overall_hit_rate."""
        target = MockPrimitive("t", return_value={"r": 1})
        cache = self._make_cache(target=target)
        data = {"q": "same"}

        await cache.execute(data, _ctx())  # miss
        await cache.execute(data, _ctx())  # hit
        await cache.execute(data, _ctx())  # hit

        stats = cache.get_cache_stats()
        assert stats["total_hits"] == 2
        assert stats["total_misses"] == 1
        assert stats["overall_hit_rate"] == pytest.approx(2 / 3)

    async def test_max_cache_size_triggers_eviction(self):
        """When cache reaches max_cache_size, the oldest entry is evicted."""
        target = MockPrimitive("t", return_value={"x": 1})
        cache = self._make_cache(target=target)
        cache.strategies["baseline_conservative"].parameters["max_cache_size"] = 2

        await cache.execute({"k": 1}, _ctx())
        await cache.execute({"k": 2}, _ctx())
        await cache.execute({"k": 3}, _ctx())  # triggers eviction

        assert len(cache._cache) <= 2

    def test_get_hit_rate_unknown_context_returns_zero(self):
        """_get_hit_rate returns 0.0 for context keys that have never been seen."""
        cache = self._make_cache()
        assert cache._get_hit_rate("nonexistent_ctx") == 0.0

    async def test_different_inputs_produce_independent_cache_entries(self):
        """Each unique input value creates its own cache entry."""
        target = MockPrimitive("t", return_value={"v": 1})
        cache = self._make_cache(target=target)

        await cache.execute({"q": "A"}, _ctx())
        await cache.execute({"q": "B"}, _ctx())

        assert target.call_count == 2
        assert len(cache._cache) == 2

    async def test_context_metrics_initialised_on_first_access(self):
        """_context_metrics is populated after the first execute call."""
        target = MockPrimitive("t", return_value={})
        cache = self._make_cache(target=target)

        assert len(cache._context_metrics) == 0
        await cache.execute({"x": 1}, _ctx(environment="test"))
        assert len(cache._context_metrics) >= 1


# ===========================================================================
# TestAdaptiveTimeoutPrimitive
# ===========================================================================


@pytest.mark.unit
class TestAdaptiveTimeoutPrimitive:
    """Tests for AdaptiveTimeoutPrimitive — latency-learning timeout wrapper."""

    def _make_timeout(
        self,
        target: MockPrimitive | None = None,
        timeout_ms: float = 5000.0,
        mode: LearningMode = LearningMode.OBSERVE,
    ) -> AdaptiveTimeoutPrimitive:
        target = target or MockPrimitive("t", return_value={"ok": True})
        return AdaptiveTimeoutPrimitive(
            target_primitive=target,  # type: ignore[arg-type]
            baseline_timeout_ms=timeout_ms,
            learning_mode=mode,
        )

    def test_construction_registers_baseline_strategy(self):
        """Constructor registers 'baseline_conservative' strategy."""
        p = self._make_timeout()
        assert "baseline_conservative" in p.strategies
        assert p.baseline_strategy is not None

    def test_default_strategy_contains_timeout_ms(self):
        """Default strategy parameters include timeout_ms matching the constructor arg."""
        p = self._make_timeout(timeout_ms=1000.0)
        s = p._get_default_strategy()
        assert s.parameters["timeout_ms"] == pytest.approx(1000.0)

    def test_default_strategy_contains_percentile_and_buffer(self):
        """Default strategy has percentile_target and buffer_factor parameters."""
        p = self._make_timeout()
        s = p._get_default_strategy()
        assert "percentile_target" in s.parameters
        assert "buffer_factor" in s.parameters

    def test_timeout_stats_initial_all_zeros(self):
        """get_timeout_stats returns all-zero counts on a fresh primitive."""
        p = self._make_timeout()
        stats = p.get_timeout_stats()

        assert stats["total_executions"] == 0
        assert stats["timeout_count"] == 0
        assert stats["success_count"] == 0
        assert stats["timeout_rate"] == 0.0

    async def test_execute_within_timeout_returns_result(self):
        """When target completes before timeout, its result is returned."""
        target = MockPrimitive("t", return_value={"fast": True})
        p = self._make_timeout(target=target)

        result = await p.execute({"x": 1}, _ctx())

        assert result == {"fast": True}

    async def test_execute_increments_success_count(self):
        """Successful execution increments _success_count."""
        target = MockPrimitive("t", return_value="ok")
        p = self._make_timeout(target=target)

        await p.execute({}, _ctx())

        assert p._success_count == 1

    async def test_execute_records_latency_sample(self):
        """Each successful execution appends a latency value to _latency_samples."""
        target = MockPrimitive("t", return_value="x")
        p = self._make_timeout(target=target)

        await p.execute({}, _ctx())

        assert len(p._latency_samples) == 1
        assert p._latency_samples[0] >= 0.0

    async def test_execute_exceeds_timeout_raises_adaptive_timeout_error(self):
        """AdaptiveTimeoutError is raised when target execution exceeds the timeout."""

        async def slow(_data: Any, _ctx: WorkflowContext) -> Any:
            await asyncio.sleep(5)
            return "too slow"

        target = MockPrimitive("slow", side_effect=slow)
        p = self._make_timeout(target=target, timeout_ms=50.0)

        with pytest.raises(AdaptiveTimeoutError):
            await p.execute({}, _ctx())

    async def test_timeout_increments_timeout_count(self):
        """Each timeout occurrence increments _timeout_count by 1."""

        async def slow(_data: Any, _ctx: WorkflowContext) -> Any:
            await asyncio.sleep(5)
            return "late"

        target = MockPrimitive("slow", side_effect=slow)
        p = self._make_timeout(target=target, timeout_ms=50.0)

        with pytest.raises(AdaptiveTimeoutError):
            await p.execute({}, _ctx())

        assert p._timeout_count == 1

    async def test_context_latencies_tracked_by_environment_key(self):
        """Per-context latencies are stored under the environment metadata key."""
        target = MockPrimitive("t", return_value="ok")
        p = self._make_timeout(target=target)

        await p.execute({}, _ctx(environment="staging"))

        assert "staging" in p._context_latencies
        assert len(p._context_latencies["staging"]) == 1

    async def test_get_timeout_stats_reflects_one_success(self):
        """get_timeout_stats accurately reflects one successful execution."""
        target = MockPrimitive("t", return_value="ok")
        p = self._make_timeout(target=target)

        await p.execute({}, _ctx())
        stats = p.get_timeout_stats()

        assert stats["total_executions"] == 1
        assert stats["success_count"] == 1
        assert stats["timeout_count"] == 0
        assert stats["timeout_rate"] == 0.0

    async def test_current_timeout_ms_matches_baseline(self):
        """get_timeout_stats.current_timeout_ms reflects the baseline strategy value."""
        p = self._make_timeout(timeout_ms=3000.0)
        stats = p.get_timeout_stats()
        assert stats["current_timeout_ms"] == pytest.approx(3000.0)

    async def test_multiple_executions_accumulate_latencies(self):
        """Latency samples accumulate correctly across multiple execute calls."""
        target = MockPrimitive("t", return_value="ok")
        p = self._make_timeout(target=target)

        for _ in range(3):
            await p.execute({}, _ctx())

        assert len(p._latency_samples) == 3
        assert p._success_count == 3

    async def test_latency_percentiles_populated_after_executions(self):
        """get_timeout_stats includes non-negative p50/p95/p99 after some executions."""
        target = MockPrimitive("t", return_value="ok")
        p = self._make_timeout(target=target)

        for _ in range(5):
            await p.execute({}, _ctx())

        stats = p.get_timeout_stats()
        latencies = stats["latencies"]
        assert latencies["p50_ms"] >= 0.0
        assert latencies["p95_ms"] >= 0.0
        assert latencies["p99_ms"] >= 0.0


# ===========================================================================
# TestAdaptiveFallbackPrimitive
# ===========================================================================


@pytest.mark.unit
class TestAdaptiveFallbackPrimitive:
    """Tests for AdaptiveFallbackPrimitive — strategy-learning multi-provider fallback."""

    def _make_fallback(
        self,
        primary_result: Any = None,
        primary_error: Exception | None = None,
        fallback_results: dict[str, Any] | None = None,
        mode: LearningMode | str = LearningMode.OBSERVE,
        order: list[str] | None = None,
    ) -> tuple[AdaptiveFallbackPrimitive, dict[str, MockPrimitive]]:
        """Build a configured AdaptiveFallbackPrimitive for testing."""
        if primary_error:
            primary = MockPrimitive("primary", raise_error=primary_error)
        else:
            primary = MockPrimitive("primary", return_value=primary_result or {"primary": True})

        fallback_results = fallback_results or {
            "fb_a": {"src": "fb_a"},
            "fb_b": {"src": "fb_b"},
        }
        fallback_mocks = {
            name: MockPrimitive(name, return_value=val) for name, val in fallback_results.items()
        }

        primitive = AdaptiveFallbackPrimitive(
            primary=primary,
            fallbacks=fallback_mocks,
            learning_mode=mode,
            baseline_fallback_order=order,
        )
        return primitive, {"primary": primary, **fallback_mocks}

    def test_construction_registers_baseline_strategy(self):
        """Constructor adds 'baseline' to the strategies dict."""
        p, _ = self._make_fallback()
        assert "baseline" in p.strategies
        assert p.baseline_strategy is not None

    def test_default_fallback_order_is_alphabetical(self):
        """Without a custom order, fallbacks are sorted alphabetically."""
        p, _ = self._make_fallback()
        assert p._baseline_fallback_order == ["fb_a", "fb_b"]

    def test_custom_fallback_order_respected(self):
        """Explicit baseline_fallback_order overrides alphabetical default."""
        p, _ = self._make_fallback(order=["fb_b", "fb_a"])
        assert p._baseline_fallback_order == ["fb_b", "fb_a"]

    def test_string_learning_mode_coerced_to_enum(self):
        """Learning mode can be passed as a string and is converted to LearningMode."""
        primary = MockPrimitive("p", return_value={})
        p = AdaptiveFallbackPrimitive(
            primary=primary,
            fallbacks={"fb": MockPrimitive("fb", return_value={})},
            learning_mode="ACTIVE",
        )
        assert p.learning_mode == LearningMode.ACTIVE

    def test_get_default_strategy_has_fallback_order(self):
        """_get_default_strategy includes 'fallback_order' in parameters."""
        p, _ = self._make_fallback()
        s = p._get_default_strategy()
        assert "fallback_order" in s.parameters
        assert isinstance(s.parameters["fallback_order"], list)

    async def test_primary_success_returns_result_directly(self):
        """When primary succeeds, its result is returned and fallbacks are not called."""
        p, mocks = self._make_fallback(primary_result={"answer": 42})

        result = await p.execute({"q": 1}, _ctx())

        assert result == {"answer": 42}
        mocks["primary"].assert_called_once()
        assert mocks["fb_a"].call_count == 0
        assert mocks["fb_b"].call_count == 0

    async def test_primary_failure_first_fallback_returns_its_result(self):
        """When primary fails, the first-ordered fallback handles the request."""
        p, _ = self._make_fallback(primary_error=RuntimeError("primary down"))

        result = await p.execute({}, _ctx())

        assert result == {"src": "fb_a"}

    async def test_first_fallback_failure_escalates_to_second(self):
        """If first fallback also fails, the second fallback is tried."""
        primary = MockPrimitive("p", raise_error=RuntimeError("fail"))
        fb_a = MockPrimitive("fb_a", raise_error=ValueError("fb_a fail"))
        fb_b = MockPrimitive("fb_b", return_value={"src": "fb_b"})

        p = AdaptiveFallbackPrimitive(
            primary=primary,
            fallbacks={"fb_a": fb_a, "fb_b": fb_b},
            baseline_fallback_order=["fb_a", "fb_b"],
        )

        result = await p.execute({}, _ctx())

        assert result == {"src": "fb_b"}
        assert fb_a.call_count == 1
        assert fb_b.call_count == 1

    async def test_all_options_fail_raises_last_exception(self):
        """When primary and all fallbacks raise, the last exception propagates."""
        primary = MockPrimitive("p", raise_error=RuntimeError("primary"))
        fb_a = MockPrimitive("fb_a", raise_error=ValueError("fb_a"))
        fb_b = MockPrimitive("fb_b", raise_error=ConnectionError("fb_b"))

        p = AdaptiveFallbackPrimitive(
            primary=primary,
            fallbacks={"fb_a": fb_a, "fb_b": fb_b},
            baseline_fallback_order=["fb_a", "fb_b"],
        )

        with pytest.raises((RuntimeError, ConnectionError)):
            await p.execute({}, _ctx())

    async def test_primary_attempts_incremented_per_call(self):
        """_primary_attempts increments once for each execute call."""
        p, _ = self._make_fallback()

        await p.execute({}, _ctx())
        await p.execute({}, _ctx())

        assert p._primary_attempts == 2

    async def test_primary_failures_tracked_on_error(self):
        """_primary_failures increments when primary raises an exception."""
        p, _ = self._make_fallback(primary_error=RuntimeError("down"))

        await p.execute({}, _ctx())

        assert p._primary_failures == 1

    async def test_fallback_successes_tracked_per_fallback(self):
        """_fallback_successes[name] increments when that fallback succeeds."""
        primary = MockPrimitive("p", raise_error=RuntimeError("fail"))
        fb_a = MockPrimitive("fb_a", return_value={"ok": True})
        p = AdaptiveFallbackPrimitive(primary=primary, fallbacks={"fb_a": fb_a})

        await p.execute({}, _ctx())

        assert p._fallback_successes["fb_a"] == 1

    async def test_get_fallback_stats_initial_state(self):
        """get_fallback_stats returns all-zero values on a fresh primitive."""
        p, _ = self._make_fallback()
        stats = p.get_fallback_stats()

        assert stats["primary_attempts"] == 0
        assert stats["primary_failures"] == 0
        assert stats["primary_failure_rate"] == 0.0
        assert "fb_a" in stats["fallbacks"]
        assert "fb_b" in stats["fallbacks"]

    async def test_get_fallback_stats_after_primary_success(self):
        """Stats after successful primary call show 1 attempt and 0 failures."""
        p, _ = self._make_fallback(primary_result={"r": 1})

        await p.execute({}, _ctx())
        stats = p.get_fallback_stats()

        assert stats["primary_attempts"] == 1
        assert stats["primary_failures"] == 0
        assert stats["primary_failure_rate"] == 0.0

    def test_get_fallback_stats_includes_best_fallback_order(self):
        """get_fallback_stats includes a 'best_fallback_order' list."""
        p, _ = self._make_fallback()
        stats = p.get_fallback_stats()
        assert "best_fallback_order" in stats
        assert isinstance(stats["best_fallback_order"], list)

    async def test_unknown_fallback_name_in_order_skipped_gracefully(self):
        """A fallback name in the strategy order that doesn't exist is silently skipped."""
        primary = MockPrimitive("p", raise_error=RuntimeError("fail"))
        fb_a = MockPrimitive("fb_a", return_value={"ok": True})

        p = AdaptiveFallbackPrimitive(
            primary=primary,
            fallbacks={"fb_a": fb_a},
            baseline_fallback_order=["unknown_fb", "fb_a"],
        )

        result = await p.execute({}, _ctx())

        assert result == {"ok": True}

    async def test_context_stats_tracked_per_environment(self):
        """Context-level stats are populated for each unique environment."""
        p, _ = self._make_fallback(primary_result={"r": 1})

        await p.execute({}, _ctx(environment="prod"))
        await p.execute({}, _ctx(environment="staging"))

        assert "prod" in p._context_stats
        assert "staging" in p._context_stats

    async def test_fallback_latencies_recorded_on_usage(self):
        """_fallback_latencies records timing data when a fallback is invoked."""
        primary = MockPrimitive("p", raise_error=RuntimeError("fail"))
        fb_a = MockPrimitive("fb_a", return_value={"ok": True})
        p = AdaptiveFallbackPrimitive(primary=primary, fallbacks={"fb_a": fb_a})

        await p.execute({}, _ctx())

        assert len(p._fallback_latencies["fb_a"]) == 1
        assert p._fallback_latencies["fb_a"][0] >= 0.0

    async def test_fallback_stats_success_rate_after_one_use(self):
        """Per-fallback success_rate is 1.0 after one successful fallback execution."""
        primary = MockPrimitive("p", raise_error=RuntimeError("fail"))
        fb_a = MockPrimitive("fb_a", return_value={"ok": True})
        p = AdaptiveFallbackPrimitive(primary=primary, fallbacks={"fb_a": fb_a})

        await p.execute({}, _ctx())
        stats = p.get_fallback_stats()

        assert stats["fallbacks"]["fb_a"]["attempts"] == 1
        assert stats["fallbacks"]["fb_a"]["successes"] == 1
        assert stats["fallbacks"]["fb_a"]["success_rate"] == pytest.approx(1.0)
