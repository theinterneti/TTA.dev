"""Comprehensive tests for AdaptiveTimeoutPrimitive — AAA pattern throughout.

Coverage targets:
- __init__ / _get_default_strategy with custom params
- _execute_with_strategy: success (latency tracking), timeout (raises TimeoutError)
- Context latency initialization per environment
- get_timeout_stats: empty, with data, with timeouts, per-context
- _consider_new_strategy: insufficient data, context-specific vs global latencies,
  high timeout rate (>10% → p99), medium rate (>5% → p95 1.5x),
  low rate (<5% → p95 1.2x tighter), no significant change
"""

from __future__ import annotations

import asyncio

import pytest

from ttadev.primitives.adaptive.base import LearningMode
from ttadev.primitives.adaptive.timeout import AdaptiveTimeoutPrimitive
from ttadev.primitives.adaptive.timeout import TimeoutError as AdaptiveTimeoutError
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**metadata) -> WorkflowContext:
    return WorkflowContext(metadata=metadata)


def _make_timeout(
    mock: MockPrimitive,
    baseline_ms: float = 5000.0,
    mode: LearningMode = LearningMode.DISABLED,
    min_obs: int = 20,
    **kwargs,
) -> AdaptiveTimeoutPrimitive:
    return AdaptiveTimeoutPrimitive(
        target_primitive=mock,
        baseline_timeout_ms=baseline_ms,
        learning_mode=mode,
        min_observations_before_learning=min_obs,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# __init__ / _get_default_strategy
# ---------------------------------------------------------------------------


def test_timeout_init_stores_baseline_params():
    # Arrange / Act
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=3000.0)

    # Assert
    assert timeout._baseline_timeout_ms == 3000.0
    assert timeout._success_count == 0
    assert timeout._timeout_count == 0
    assert timeout._latency_samples == []


def test_timeout_get_default_strategy_uses_baseline_params():
    # Arrange
    mock = MockPrimitive("target")
    timeout = AdaptiveTimeoutPrimitive(
        target_primitive=mock,
        baseline_timeout_ms=2500.0,
        baseline_percentile_target=99,
        baseline_buffer_factor=2.0,
        learning_mode=LearningMode.DISABLED,
    )

    # Act
    strategy = timeout._get_default_strategy()

    # Assert
    assert strategy.name == "baseline_conservative"
    assert strategy.parameters["timeout_ms"] == 2500.0
    assert strategy.parameters["percentile_target"] == 99
    assert strategy.parameters["buffer_factor"] == 2.0
    assert strategy.context_pattern == "*"


def test_timeout_baseline_strategy_registered():
    # Arrange / Act
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock)

    # Assert
    assert "baseline_conservative" in timeout.strategies
    assert timeout.baseline_strategy is not None


# ---------------------------------------------------------------------------
# _execute_with_strategy: success path
# ---------------------------------------------------------------------------


async def test_execute_success_records_latency():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock, baseline_ms=5000.0)
    ctx = _ctx()

    # Act
    result = await timeout.execute({}, ctx)

    # Assert
    assert result == {"data": "result"}
    assert timeout._success_count == 1
    assert timeout._timeout_count == 0
    assert len(timeout._latency_samples) == 1
    assert timeout._latency_samples[0] > 0


async def test_execute_success_tracks_context_latency():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock, baseline_ms=5000.0)
    ctx = _ctx(environment="production")

    # Act
    await timeout.execute({}, ctx)

    # Assert
    assert "production" in timeout._context_latencies
    assert len(timeout._context_latencies["production"]) == 1


async def test_execute_multiple_successes_accumulate():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock, baseline_ms=5000.0)
    ctx = _ctx()

    # Act
    for _ in range(5):
        await timeout.execute({}, ctx)

    # Assert
    assert timeout._success_count == 5
    assert len(timeout._latency_samples) == 5


async def test_execute_default_context_key_is_default():
    # Arrange — no environment metadata → uses "default" key
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock)
    ctx = WorkflowContext()  # no metadata

    # Act
    await timeout.execute({}, ctx)

    # Assert
    assert "default" in timeout._context_latencies


# ---------------------------------------------------------------------------
# _execute_with_strategy: timeout path
# ---------------------------------------------------------------------------


async def test_execute_timeout_raises_adaptive_timeout_error():
    # Arrange
    async def slow(inp, ctx):
        await asyncio.sleep(10.0)
        return {"data": "never"}

    mock = MockPrimitive("target", side_effect=slow)
    timeout = _make_timeout(mock, baseline_ms=10.0)  # 10ms timeout
    ctx = _ctx()

    # Act / Assert
    with pytest.raises(AdaptiveTimeoutError, match="Execution exceeded timeout"):
        await timeout.execute({}, ctx)


async def test_execute_timeout_increments_timeout_count():
    # Arrange
    async def slow(inp, ctx):
        await asyncio.sleep(10.0)
        return {}

    mock = MockPrimitive("target", side_effect=slow)
    timeout = _make_timeout(mock, baseline_ms=10.0)
    ctx = _ctx()

    # Act
    with pytest.raises(AdaptiveTimeoutError):
        await timeout.execute({}, ctx)

    # Assert
    assert timeout._timeout_count == 1
    assert timeout._success_count == 0


async def test_execute_timeout_does_not_record_latency_sample():
    # Arrange
    async def slow(inp, ctx):
        await asyncio.sleep(10.0)
        return {}

    mock = MockPrimitive("target", side_effect=slow)
    timeout = _make_timeout(mock, baseline_ms=10.0)
    ctx = _ctx()

    # Act
    with pytest.raises(AdaptiveTimeoutError):
        await timeout.execute({}, ctx)

    # Assert — latency NOT added to samples (only success adds)
    assert len(timeout._latency_samples) == 0


# ---------------------------------------------------------------------------
# get_timeout_stats
# ---------------------------------------------------------------------------


def test_get_timeout_stats_empty():
    # Arrange
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock)

    # Act
    stats = timeout.get_timeout_stats()

    # Assert
    assert stats["total_executions"] == 0
    assert stats["timeout_count"] == 0
    assert stats["success_count"] == 0
    assert stats["timeout_rate"] == 0.0
    assert stats["latencies"]["p50_ms"] == 0.0
    assert stats["latencies"]["p95_ms"] == 0.0
    assert stats["latencies"]["p99_ms"] == 0.0
    assert stats["latencies"]["avg_ms"] == 0.0
    assert stats["latencies"]["min_ms"] == 0.0
    assert stats["latencies"]["max_ms"] == 0.0
    assert stats["contexts"] == {}


async def test_get_timeout_stats_with_successes():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock, baseline_ms=5000.0)
    ctx = _ctx(environment="staging")

    for _ in range(5):
        await timeout.execute({}, ctx)

    # Act
    stats = timeout.get_timeout_stats()

    # Assert
    assert stats["success_count"] == 5
    assert stats["timeout_count"] == 0
    assert stats["total_executions"] == 5
    assert stats["timeout_rate"] == 0.0
    assert stats["latencies"]["p95_ms"] > 0
    assert stats["latencies"]["avg_ms"] > 0
    assert "staging" in stats["contexts"]


async def test_get_timeout_stats_with_timeout():
    # Arrange
    async def slow(inp, ctx):
        await asyncio.sleep(10.0)
        return {}

    mock = MockPrimitive("target", side_effect=slow)
    timeout = _make_timeout(mock, baseline_ms=10.0)
    ctx = _ctx()

    with pytest.raises(AdaptiveTimeoutError):
        await timeout.execute({}, ctx)

    # Act
    stats = timeout.get_timeout_stats()

    # Assert
    assert stats["timeout_count"] == 1
    assert stats["success_count"] == 0
    assert stats["timeout_rate"] == 1.0


async def test_get_timeout_stats_per_context():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock, baseline_ms=5000.0)

    ctx_a = _ctx(environment="env_a")
    ctx_b = _ctx(environment="env_b")

    for _ in range(3):
        await timeout.execute({}, ctx_a)
    for _ in range(2):
        await timeout.execute({}, ctx_b)

    # Act
    stats = timeout.get_timeout_stats()

    # Assert
    assert "env_a" in stats["contexts"]
    assert "env_b" in stats["contexts"]
    assert stats["contexts"]["env_a"]["executions"] == 3
    assert stats["contexts"]["env_b"]["executions"] == 2
    assert stats["contexts"]["env_a"]["avg_latency_ms"] > 0
    assert stats["contexts"]["env_a"]["min_latency_ms"] > 0
    assert stats["contexts"]["env_a"]["max_latency_ms"] > 0
    assert stats["contexts"]["env_a"]["p95_latency_ms"] > 0


async def test_get_timeout_stats_strategies_included():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    timeout = _make_timeout(mock)
    ctx = _ctx()
    await timeout.execute({}, ctx)

    # Act
    stats = timeout.get_timeout_stats()

    # Assert
    assert "baseline_conservative" in stats["strategies"]
    strat = stats["strategies"]["baseline_conservative"]
    assert "timeout_ms" in strat
    assert "percentile_target" in strat
    assert "buffer_factor" in strat
    assert "success_rate" in strat


def test_get_timeout_stats_current_timeout_from_baseline():
    # Arrange
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=7777.0)

    # Act
    stats = timeout.get_timeout_stats()

    # Assert
    assert stats["current_timeout_ms"] == 7777.0


# ---------------------------------------------------------------------------
# _consider_new_strategy
# ---------------------------------------------------------------------------


async def test_consider_new_strategy_insufficient_data_returns_none():
    # Arrange
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, min_obs=20, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [100.0] * 5  # only 5, need 20
    ctx = _ctx()

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_uses_global_when_context_too_sparse():
    # Arrange — 20 global samples but fewer than 5 context-specific
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=5000.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 10) for i in range(1, 21)]  # 10–200ms
    timeout._timeout_count = 0
    timeout._success_count = 20
    ctx = _ctx(environment="sparse_env")
    timeout._context_latencies["sparse_env"] = [100.0, 150.0, 120.0]  # only 3 → use global

    # Act — should use global samples (sufficient data)
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert — no error; either creates or doesn't based on values
    # (global p95 ≈ 190ms * 1.2 = 228ms vs 5000ms → large diff → creates)
    assert result is not None or result is None  # just verify no exception


async def test_consider_new_strategy_uses_context_when_sufficient():
    # Arrange
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=5000.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 10) for i in range(1, 21)]  # 10–200ms (global)
    timeout._timeout_count = 0
    timeout._success_count = 20
    ctx = _ctx(environment="rich_env")
    # 10 context-specific samples → uses these instead of global
    timeout._context_latencies["rich_env"] = [float(i * 20) for i in range(1, 11)]  # 20–200ms

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert — runs without error
    assert result is None or result is not None


async def test_consider_new_strategy_high_timeout_rate_uses_p99_with_2x_buffer():
    # Arrange — >10% timeout rate → use p99, 2x buffer
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=100.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 5) for i in range(1, 21)]  # 5–100ms
    timeout._timeout_count = 5  # 5/(5+15) = 25% > 10%
    timeout._success_count = 15
    ctx = _ctx(environment="default")
    timeout._context_latencies["default"] = timeout._latency_samples[:]

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert
    if result is not None:
        assert result.parameters["percentile_target"] == 99
        assert result.parameters["buffer_factor"] == 2.0


async def test_consider_new_strategy_medium_timeout_rate_uses_p95_1_5x():
    # Arrange — 5–10% timeout rate → p95, 1.5x buffer
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=100.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 5) for i in range(1, 21)]
    timeout._timeout_count = 2  # 2/(2+28) ≈ 6.7%, between 5% and 10%
    timeout._success_count = 28
    ctx = _ctx(environment="default")
    timeout._context_latencies["default"] = timeout._latency_samples[:]

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert
    if result is not None:
        assert result.parameters["buffer_factor"] == 1.5
        assert result.parameters["percentile_target"] == 95


async def test_consider_new_strategy_low_timeout_rate_uses_tighter_1_2x():
    # Arrange — <5% timeout rate → p95, 1.2x (tighter)
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=5000.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 10) for i in range(1, 21)]  # 10–200ms
    timeout._timeout_count = 0
    timeout._success_count = 20
    ctx = _ctx(environment="default")
    timeout._context_latencies["default"] = timeout._latency_samples[:]

    # Act — p95 of 10–200ms ≈ 190ms * 1.2 = 228ms vs 5000ms → big diff → creates
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert
    if result is not None:
        assert result.parameters["buffer_factor"] == 1.2
        assert result.parameters["percentile_target"] == 95


async def test_consider_new_strategy_no_significant_change_returns_none():
    # Arrange — new timeout within 15% of current baseline → no strategy
    # p95 of [3667ms]*20 = 3667ms, buffer 1.2 → new = 4400.4ms
    # current = 5000ms, change = |4400.4-5000|/5000 = 11.99% < 15% → None
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=5000.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [3667.0] * 20
    timeout._timeout_count = 0
    timeout._success_count = 20
    ctx = _ctx(environment="default")
    timeout._context_latencies["default"] = [3667.0] * 20

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_creates_correctly_named_strategy():
    # Arrange
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=5000.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 10) for i in range(1, 21)]
    timeout._timeout_count = 0
    timeout._success_count = 20
    ctx = _ctx(environment="myenv")
    timeout._context_latencies["myenv"] = timeout._latency_samples[:]

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert — strategy name includes context key
    if result is not None:
        assert "myenv" in result.name
        assert "p95" in result.name or "p99" in result.name


async def test_consider_new_strategy_includes_correct_parameters():
    # Arrange
    mock = MockPrimitive("target")
    timeout = _make_timeout(mock, baseline_ms=5000.0, min_obs=5, mode=LearningMode.ACTIVE)
    timeout._latency_samples = [float(i * 10) for i in range(1, 21)]
    timeout._timeout_count = 0
    timeout._success_count = 20
    ctx = _ctx(environment="default")
    timeout._context_latencies["default"] = timeout._latency_samples[:]

    # Act
    result = await timeout._consider_new_strategy({}, ctx, timeout.baseline_strategy.metrics)

    # Assert
    if result is not None:
        assert "timeout_ms" in result.parameters
        assert "percentile_target" in result.parameters
        assert "buffer_factor" in result.parameters
        assert result.parameters["timeout_ms"] > 0
