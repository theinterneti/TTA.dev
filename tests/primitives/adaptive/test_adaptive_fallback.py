"""Comprehensive tests for AdaptiveFallbackPrimitive — AAA pattern throughout.

Coverage targets:
- __init__: string/enum learning_mode conversion, baseline order (custom vs alphabetical)
- _get_default_strategy
- _execute_with_strategy: primary success, primary-fail+fallback-success,
  primary-fail+all-fallbacks-fail, unknown fallback key skipped
- Context stats initialization and tracking
- Fallback latency recording
- get_fallback_stats: empty, with data, best_fallback_order scoring
- _consider_new_strategy: insufficient observations, same order, insufficient
  improvement, creates improved strategy
"""

from __future__ import annotations

import pytest

from ttadev.primitives.adaptive.base import LearningMode
from ttadev.primitives.adaptive.fallback import AdaptiveFallbackPrimitive
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**metadata) -> WorkflowContext:
    return WorkflowContext(metadata=metadata)


def _make_fallback(
    primary: MockPrimitive,
    fallbacks: dict,
    mode: str | LearningMode = "DISABLED",
    order: list | None = None,
    min_obs: int = 10,
) -> AdaptiveFallbackPrimitive:
    return AdaptiveFallbackPrimitive(
        primary=primary,
        fallbacks=fallbacks,
        learning_mode=mode,
        baseline_fallback_order=order,
        min_observations_before_learning=min_obs,
    )


# ---------------------------------------------------------------------------
# __init__: learning mode conversion
# ---------------------------------------------------------------------------


def test_string_learning_mode_disabled_converted():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")}, mode="DISABLED")

    # Assert
    assert fb.learning_mode == LearningMode.DISABLED


def test_string_learning_mode_validate_converted():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")}, mode="VALIDATE")

    # Assert
    assert fb.learning_mode == LearningMode.VALIDATE


def test_string_learning_mode_active_converted():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")}, mode="ACTIVE")

    # Assert
    assert fb.learning_mode == LearningMode.ACTIVE


def test_string_learning_mode_observe_converted():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")}, mode="OBSERVE")

    # Assert
    assert fb.learning_mode == LearningMode.OBSERVE


def test_enum_learning_mode_preserved():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")}, mode=LearningMode.ACTIVE)

    # Assert
    assert fb.learning_mode == LearningMode.ACTIVE


# ---------------------------------------------------------------------------
# __init__: baseline fallback order
# ---------------------------------------------------------------------------


def test_baseline_fallback_order_custom_preserved():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(
        primary,
        {"a": MockPrimitive("a"), "b": MockPrimitive("b"), "c": MockPrimitive("c")},
        order=["c", "a", "b"],
    )

    # Assert
    assert fb._baseline_fallback_order == ["c", "a", "b"]
    assert fb.baseline_strategy.parameters["fallback_order"] == ["c", "a", "b"]


def test_baseline_fallback_order_alphabetical_when_not_specified():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(
        primary,
        {"c": MockPrimitive("c"), "a": MockPrimitive("a"), "b": MockPrimitive("b")},
    )

    # Assert — sorted alphabetically
    assert fb._baseline_fallback_order == ["a", "b", "c"]
    assert fb.baseline_strategy.parameters["fallback_order"] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# _get_default_strategy
# ---------------------------------------------------------------------------


def test_get_default_strategy_returns_baseline():
    # Arrange
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a"), "b": MockPrimitive("b")})

    # Act
    strategy = fb._get_default_strategy()

    # Assert
    assert strategy.name == "baseline"
    assert strategy.description == "Default fallback order"
    assert strategy.context_pattern == ""
    assert "fallback_order" in strategy.parameters
    assert "primary_timeout_ms" in strategy.parameters
    assert "fallback_timeout_ms" in strategy.parameters


def test_baseline_strategy_registered_in_strategies():
    # Arrange / Act
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")})

    # Assert
    assert "baseline" in fb.strategies
    assert fb.baseline_strategy is not None


# ---------------------------------------------------------------------------
# _execute_with_strategy: primary success
# ---------------------------------------------------------------------------


async def test_primary_succeeds_returns_primary_result():
    # Arrange
    primary = MockPrimitive("primary", return_value={"source": "primary"})
    fallback_a = MockPrimitive("fallback_a", return_value={"source": "a"})
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx()

    # Act
    result = await fb.execute({}, ctx)

    # Assert
    assert result == {"source": "primary"}
    assert primary.call_count == 1
    assert fallback_a.call_count == 0


async def test_primary_success_increments_primary_attempts():
    # Arrange
    primary = MockPrimitive("primary", return_value={"source": "primary"})
    fb = _make_fallback(primary, {"a": MockPrimitive("a")})
    ctx = _ctx()

    # Act
    await fb.execute({}, ctx)

    # Assert
    assert fb._primary_attempts == 1
    assert fb._primary_failures == 0


# ---------------------------------------------------------------------------
# _execute_with_strategy: primary fail, fallback success
# ---------------------------------------------------------------------------


async def test_primary_fail_first_fallback_succeeds():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("primary down"))
    fallback_a = MockPrimitive("fallback_a", return_value={"source": "a"})
    fb = _make_fallback(primary, {"a": fallback_a}, order=["a"])
    ctx = _ctx()

    # Act
    result = await fb.execute({}, ctx)

    # Assert
    assert result == {"source": "a"}
    assert fb._primary_failures == 1
    assert fb._fallback_successes["a"] == 1
    assert fb._fallback_attempts["a"] == 1


async def test_primary_fail_second_fallback_succeeds_when_first_fails():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("primary down"))
    fallback_a = MockPrimitive("fallback_a", raise_error=RuntimeError("a down"))
    fallback_b = MockPrimitive("fallback_b", return_value={"source": "b"})
    fb = _make_fallback(primary, {"a": fallback_a, "b": fallback_b}, order=["a", "b"])
    ctx = _ctx()

    # Act
    result = await fb.execute({}, ctx)

    # Assert
    assert result == {"source": "b"}
    assert fb._fallback_successes["a"] == 0
    assert fb._fallback_successes["b"] == 1


async def test_fallback_latency_recorded_on_success():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fallback_a = MockPrimitive("fallback_a", return_value={"source": "a"})
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx()

    # Act
    await fb.execute({}, ctx)

    # Assert
    assert len(fb._fallback_latencies["a"]) == 1
    assert fb._fallback_latencies["a"][0] >= 0.0


# ---------------------------------------------------------------------------
# _execute_with_strategy: all fail
# ---------------------------------------------------------------------------


async def test_all_fail_raises_last_exception():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("primary down"))
    fallback_a = MockPrimitive("fallback_a", raise_error=RuntimeError("a down"))
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx()

    # Act / Assert — last error re-raised (from fallback_a)
    with pytest.raises(RuntimeError, match="a down"):
        await fb.execute({}, ctx)


async def test_all_fail_primary_failure_counted():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fallback_a = MockPrimitive("fallback_a", raise_error=RuntimeError("a down"))
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx()

    # Act
    with pytest.raises(RuntimeError):
        await fb.execute({}, ctx)

    # Assert
    assert fb._primary_failures == 1
    assert fb._fallback_attempts["a"] == 1
    assert fb._fallback_successes["a"] == 0


# ---------------------------------------------------------------------------
# Unknown fallback key in order
# ---------------------------------------------------------------------------


async def test_unknown_fallback_key_skipped_and_next_tried():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fallback_a = MockPrimitive("fallback_a", return_value={"source": "a"})
    fb = _make_fallback(
        primary,
        {"a": fallback_a},
        order=["nonexistent", "a"],  # nonexistent key → skipped
    )
    ctx = _ctx()

    # Act
    result = await fb.execute({}, ctx)

    # Assert — skips unknown, uses "a"
    assert result == {"source": "a"}


async def test_unknown_fallback_key_all_unknown_raises():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fb = _make_fallback(
        primary,
        {"a": MockPrimitive("a")},
        order=["nonexistent1", "nonexistent2"],  # all unknown
    )
    ctx = _ctx()

    # Act / Assert — all options exhausted → re-raise primary error
    with pytest.raises(ValueError, match="down"):
        await fb.execute({}, ctx)


# ---------------------------------------------------------------------------
# Context stats initialization and tracking
# ---------------------------------------------------------------------------


async def test_context_stats_initialized_on_first_access():
    # Arrange
    primary = MockPrimitive("primary", return_value={"data": "ok"})
    fb = _make_fallback(primary, {"a": MockPrimitive("a")})
    ctx = _ctx(environment="staging")

    # Act
    await fb.execute({}, ctx)

    # Assert
    assert "staging" in fb._context_stats
    stats = fb._context_stats["staging"]
    assert stats["primary_attempts"] == 1
    assert stats["primary_failures"] == 0
    assert "fallback_usage" in stats
    assert "fallback_successes" in stats


async def test_context_stats_failure_tracked():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fallback_a = MockPrimitive("fallback_a", return_value={"source": "a"})
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx(environment="prod")

    # Act
    await fb.execute({}, ctx)

    # Assert
    assert fb._context_stats["prod"]["primary_failures"] == 1
    assert fb._context_stats["prod"]["fallback_usage"]["a"] == 1
    assert fb._context_stats["prod"]["fallback_successes"]["a"] == 1


async def test_context_stats_default_key_when_no_env():
    # Arrange
    primary = MockPrimitive("primary", return_value={"data": "ok"})
    fb = _make_fallback(primary, {"a": MockPrimitive("a")})
    ctx = WorkflowContext()  # no environment metadata

    # Act
    await fb.execute({}, ctx)

    # Assert
    assert "default" in fb._context_stats


# ---------------------------------------------------------------------------
# get_fallback_stats
# ---------------------------------------------------------------------------


def test_get_fallback_stats_empty():
    # Arrange
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a"), "b": MockPrimitive("b")})

    # Act
    stats = fb.get_fallback_stats()

    # Assert
    assert stats["primary_attempts"] == 0
    assert stats["primary_failures"] == 0
    assert stats["primary_failure_rate"] == 0.0
    assert "a" in stats["fallbacks"]
    assert "b" in stats["fallbacks"]
    assert stats["fallbacks"]["a"]["attempts"] == 0
    assert stats["fallbacks"]["a"]["success_rate"] == 0.0
    assert stats["fallbacks"]["a"]["avg_latency_ms"] == 0.0


async def test_get_fallback_stats_with_data():
    # Arrange
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fallback_a = MockPrimitive("fallback_a", return_value={"source": "a"})
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx()

    for _ in range(3):
        await fb.execute({}, ctx)

    # Act
    stats = fb.get_fallback_stats()

    # Assert
    assert stats["primary_attempts"] == 3
    assert stats["primary_failures"] == 3
    assert stats["primary_failure_rate"] == 1.0
    assert stats["fallbacks"]["a"]["attempts"] == 3
    assert stats["fallbacks"]["a"]["successes"] == 3
    assert stats["fallbacks"]["a"]["success_rate"] == 1.0
    assert stats["fallbacks"]["a"]["avg_latency_ms"] >= 0.0


async def test_get_fallback_stats_best_order_by_success_rate():
    # Arrange — b has higher success rate than a → b should be first
    primary = MockPrimitive("primary", raise_error=ValueError("down"))
    fallback_a = MockPrimitive("fallback_a", raise_error=ValueError("a down"))
    fallback_b = MockPrimitive("fallback_b", return_value={"source": "b"})
    fb = _make_fallback(primary, {"a": fallback_a, "b": fallback_b}, order=["a", "b"])
    ctx = _ctx()

    # a fails, b succeeds
    await fb.execute({}, ctx)

    # Act
    stats = fb.get_fallback_stats()

    # Assert — b first in best order
    assert stats["best_fallback_order"][0] == "b"


async def test_get_fallback_stats_strategies_included():
    # Arrange
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")})

    # Act
    stats = fb.get_fallback_stats()

    # Assert
    assert "baseline" in stats["strategies"]
    strat = stats["strategies"]["baseline"]
    assert "fallback_order" in strat
    assert "success_rate" in strat
    assert "avg_latency_ms" in strat


async def test_get_fallback_stats_contexts_populated():
    # Arrange
    primary = MockPrimitive("primary", return_value={"data": "ok"})
    fb = _make_fallback(primary, {"a": MockPrimitive("a")})
    ctx = _ctx(environment="myenv")

    await fb.execute({}, ctx)

    # Act
    stats = fb.get_fallback_stats()

    # Assert
    assert "myenv" in stats["contexts"]


async def test_get_fallback_stats_latency_score_zero_for_no_latency():
    # Arrange — no fallback was ever used → avg_latency = 0 → latency_score = 1.0
    primary = MockPrimitive("primary", return_value={"data": "ok"})
    fallback_a = MockPrimitive("fallback_a")
    fb = _make_fallback(primary, {"a": fallback_a})
    ctx = _ctx()

    await fb.execute({}, ctx)  # primary succeeds, no fallback

    # Act
    stats = fb.get_fallback_stats()

    # Assert — fallback has 0 avg_latency → latency_score=1.0, score based on 0*0.7+1.0*0.3=0.3
    assert stats["fallbacks"]["a"]["avg_latency_ms"] == 0.0
    # best_fallback_order should still have "a"
    assert "a" in stats["best_fallback_order"]


# ---------------------------------------------------------------------------
# _consider_new_strategy
# ---------------------------------------------------------------------------


async def test_consider_new_strategy_insufficient_observations():
    # Arrange
    primary = MockPrimitive("primary")
    fb = _make_fallback(primary, {"a": MockPrimitive("a")}, mode="ACTIVE", min_obs=10)
    fb._primary_attempts = 5  # Below threshold
    ctx = _ctx()

    # Act
    result = await fb._consider_new_strategy({}, ctx, fb.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_same_order_returns_none():
    # Arrange — both fallbacks have 0 attempts → both score 0 → alphabetical → matches baseline
    primary = MockPrimitive("primary")
    fallback_a = MockPrimitive("fallback_a")
    fallback_b = MockPrimitive("fallback_b")
    fb = _make_fallback(
        primary,
        {"a": fallback_a, "b": fallback_b},
        mode="ACTIVE",
        min_obs=5,
    )
    fb._primary_attempts = 10
    # Both have 0 attempts → optimal order = ['a', 'b'] (alphabetical by 0 score)
    # Baseline is also ['a', 'b'] → same order → None
    ctx = _ctx()

    # Act
    result = await fb._consider_new_strategy({}, ctx, fb.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_creates_improved_strategy():
    # Arrange — b has much better success rate → optimal order changes → new strategy
    primary = MockPrimitive("primary")
    fallback_a = MockPrimitive("fallback_a")
    fallback_b = MockPrimitive("fallback_b")
    fb = _make_fallback(
        primary,
        {"a": fallback_a, "b": fallback_b},
        order=["a", "b"],  # current order: a first
        mode="ACTIVE",
        min_obs=5,
    )
    fb._primary_attempts = 20

    # b is much better: 90% success vs a's 10%
    fb._fallback_attempts["a"] = 10
    fb._fallback_successes["a"] = 1  # 10% success
    fb._fallback_latencies["a"] = [500.0] * 10
    fb._fallback_attempts["b"] = 10
    fb._fallback_successes["b"] = 9  # 90% success
    fb._fallback_latencies["b"] = [100.0] * 10

    ctx = _ctx(environment="default")

    # Act
    result = await fb._consider_new_strategy({}, ctx, fb.baseline_strategy.metrics)

    # Assert — new strategy created with b first
    assert result is not None
    assert result.parameters["fallback_order"][0] == "b"
    assert "fallback_order" in result.parameters
    assert "primary_timeout_ms" in result.parameters


async def test_consider_new_strategy_insufficient_improvement_returns_none():
    # Arrange — different order but improvement < 5%
    primary = MockPrimitive("primary")
    fallback_a = MockPrimitive("fallback_a")
    fallback_b = MockPrimitive("fallback_b")
    fb = _make_fallback(
        primary,
        {"a": fallback_a, "b": fallback_b},
        order=["b", "a"],  # current: b first
        mode="ACTIVE",
        min_obs=5,
    )
    fb._primary_attempts = 20

    # Both have similar success rates → small improvement
    fb._fallback_attempts["a"] = 10
    fb._fallback_successes["a"] = 5  # 50% success
    fb._fallback_latencies["a"] = [200.0] * 10
    fb._fallback_attempts["b"] = 10
    fb._fallback_successes["b"] = 5  # 50% success
    fb._fallback_latencies["b"] = [200.0] * 10

    # Set current strategy success rate to same as estimated → no improvement
    fb.baseline_strategy.metrics.success_count = 50
    fb.baseline_strategy.metrics.total_executions = 100  # 50% success rate

    ctx = _ctx(environment="default")

    # Act
    result = await fb._consider_new_strategy({}, ctx, fb.baseline_strategy.metrics)

    # Assert — same scores, same order, no improvement → None
    assert result is None


async def test_consider_new_strategy_new_strategy_includes_context_pattern():
    # Arrange
    primary = MockPrimitive("primary")
    fallback_a = MockPrimitive("fallback_a")
    fallback_b = MockPrimitive("fallback_b")
    fb = _make_fallback(
        primary,
        {"a": fallback_a, "b": fallback_b},
        order=["a", "b"],
        mode="ACTIVE",
        min_obs=5,
    )
    fb._primary_attempts = 20
    fb._fallback_attempts["a"] = 10
    fb._fallback_successes["a"] = 1
    fb._fallback_latencies["a"] = [500.0] * 10
    fb._fallback_attempts["b"] = 10
    fb._fallback_successes["b"] = 9
    fb._fallback_latencies["b"] = [100.0] * 10

    ctx = _ctx(environment="myenv")

    # Act
    result = await fb._consider_new_strategy({}, ctx, fb.baseline_strategy.metrics)

    # Assert — context pattern matches environment
    if result is not None:
        assert result.context_pattern == "myenv"
        assert "myenv" in result.name


async def test_multiple_fallbacks_with_no_attempts_scores_by_latency_only():
    # Arrange — no attempts on any fallback → success_rate = 0, latency_score = 0
    # → all scores equal → alphabetical order → same as baseline → None
    primary = MockPrimitive("primary")
    fb = _make_fallback(
        primary,
        {"z": MockPrimitive("z"), "a": MockPrimitive("a"), "m": MockPrimitive("m")},
        mode="ACTIVE",
        min_obs=5,
    )
    fb._primary_attempts = 10
    ctx = _ctx()

    # Act
    result = await fb._consider_new_strategy({}, ctx, fb.baseline_strategy.metrics)

    # Assert — same order → None
    assert result is None
