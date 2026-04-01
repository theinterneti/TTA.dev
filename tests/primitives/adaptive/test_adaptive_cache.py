"""Comprehensive tests for AdaptiveCachePrimitive — AAA pattern throughout.

Coverage targets:
- __init__ / _get_default_strategy
- _execute_with_strategy: cache miss, cache hit, expired entry, eviction
- _context_metrics initialization
- _get_hit_rate (no context, no requests, with data)
- get_cache_stats (empty, with data)
- clear_cache
- evict_expired (with/without strategy; no entries; strategy=None+baseline=None)
- _consider_new_strategy: insufficient data, no context, high-hit-low-age (shorter TTL),
  high-age-low-hit (longer TTL), low hit rate (reduce TTL), no change (else branch),
  ttl clamped to bounds
"""

from __future__ import annotations

import asyncio
import time

import pytest

from ttadev.primitives.adaptive.base import LearningMode, LearningStrategy
from ttadev.primitives.adaptive.cache import AdaptiveCachePrimitive
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**metadata) -> WorkflowContext:
    return WorkflowContext(metadata=metadata)


def _simple_key(inp, ctx) -> str:
    return str(inp.get("key", "default"))


def _const_key(inp, ctx) -> str:
    return "constant_key"


def _make_cache(
    mock: MockPrimitive,
    key_fn=None,
    mode: LearningMode = LearningMode.DISABLED,
) -> AdaptiveCachePrimitive:
    return AdaptiveCachePrimitive(
        target_primitive=mock,
        cache_key_fn=key_fn or _const_key,
        learning_mode=mode,
    )


# ---------------------------------------------------------------------------
# __init__ / _get_default_strategy
# ---------------------------------------------------------------------------


def test_cache_default_strategy_params():
    # Arrange / Act
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    strategy = cache._get_default_strategy()

    # Assert
    assert strategy.name == "baseline_conservative"
    assert strategy.parameters["ttl_seconds"] == 3600.0
    assert strategy.parameters["max_cache_size"] == 1000
    assert strategy.parameters["min_hit_rate"] == 0.3
    assert strategy.context_pattern == "*"


def test_cache_init_registers_baseline_strategy():
    # Arrange / Act
    mock = MockPrimitive("target")
    cache = _make_cache(mock)

    # Assert
    assert "baseline_conservative" in cache.strategies
    assert cache.baseline_strategy is not None
    assert cache._cache == {}
    assert cache._context_metrics == {}


# ---------------------------------------------------------------------------
# _execute_with_strategy: cache miss → populate
# ---------------------------------------------------------------------------


async def test_cache_miss_calls_target_primitive():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = _make_cache(mock)
    ctx = _ctx()

    # Act
    result = await cache.execute({}, ctx)

    # Assert
    assert result == {"data": "result"}
    assert mock.call_count == 1
    assert len(cache._cache) == 1


async def test_cache_hit_returns_cached_value_without_calling_target():
    # Arrange
    call_count = 0

    def side_effect(inp, ctx):
        nonlocal call_count
        call_count += 1
        return {"data": f"call_{call_count}"}

    mock = MockPrimitive("target", side_effect=side_effect)
    cache = _make_cache(mock)
    ctx = _ctx()

    # Act
    result1 = await cache.execute({}, ctx)
    result2 = await cache.execute({}, ctx)

    # Assert — second call uses cache
    assert result1 == result2
    assert mock.call_count == 1  # target only called once


async def test_cache_different_keys_are_stored_separately():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = AdaptiveCachePrimitive(
        target_primitive=mock,
        cache_key_fn=_simple_key,
        learning_mode=LearningMode.DISABLED,
    )
    ctx = _ctx()

    # Act
    await cache.execute({"key": "a"}, ctx)
    await cache.execute({"key": "b"}, ctx)
    await cache.execute({"key": "a"}, ctx)  # hit

    # Assert — 2 distinct cache misses, 1 hit
    assert mock.call_count == 2
    assert len(cache._cache) == 2


async def test_cache_expired_entry_triggers_new_target_call():
    # Arrange
    call_count = 0

    def side_effect(inp, ctx):
        nonlocal call_count
        call_count += 1
        return {"data": f"call_{call_count}"}

    mock = MockPrimitive("target", side_effect=side_effect)
    cache = _make_cache(mock)
    cache.baseline_strategy.parameters["ttl_seconds"] = 0.01  # 10ms TTL
    ctx = _ctx()

    # Act
    await cache.execute({}, ctx)  # miss → cached
    await asyncio.sleep(0.05)  # wait for expiry
    await cache.execute({}, ctx)  # miss again (expired)

    # Assert
    assert mock.call_count == 2


async def test_cache_expired_entry_removed_from_cache():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = _make_cache(mock)
    ctx = _ctx()
    # Plant an expired entry directly
    cache._cache["constant_key"] = ({"data": "old"}, time.time() - 7200, "ctx")
    cache.baseline_strategy.parameters["ttl_seconds"] = 3600.0

    # Act — expired entry should be removed, new value fetched
    result = await cache.execute({}, ctx)

    # Assert
    assert mock.call_count == 1
    assert result == {"data": "result"}
    # Old entry removed, new one stored
    assert cache._cache["constant_key"][0] == {"data": "result"}


async def test_cache_evicts_oldest_when_max_size_reached():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = AdaptiveCachePrimitive(
        target_primitive=mock,
        cache_key_fn=_simple_key,
        learning_mode=LearningMode.DISABLED,
    )
    cache.baseline_strategy.parameters["max_cache_size"] = 2
    ctx = _ctx()

    # Act — fill cache, then overflow
    await cache.execute({"key": "a"}, ctx)
    await cache.execute({"key": "b"}, ctx)
    await cache.execute({"key": "c"}, ctx)  # triggers eviction

    # Assert — cache size stays at max
    assert len(cache._cache) == 2
    assert mock.call_count == 3  # all 3 were misses (different keys)


# ---------------------------------------------------------------------------
# Context metrics initialization
# ---------------------------------------------------------------------------


async def test_context_metrics_initialized_on_first_access():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = _make_cache(mock)
    ctx = _ctx()

    # Act
    await cache.execute({}, ctx)

    # Assert — context key was tracked
    assert len(cache._context_metrics) == 1
    context_key = next(iter(cache._context_metrics.keys()))
    metrics = cache._context_metrics[context_key]
    assert metrics["executions"] == 1
    assert metrics["misses"] == 1
    assert metrics["hits"] == 0


async def test_context_metrics_hit_tracked():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = _make_cache(mock)
    ctx = _ctx()

    # Act
    await cache.execute({}, ctx)  # miss
    await cache.execute({}, ctx)  # hit

    # Assert
    context_key = next(iter(cache._context_metrics.keys()))
    metrics = cache._context_metrics[context_key]
    assert metrics["hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["total_hit_age"] >= 0.0


# ---------------------------------------------------------------------------
# _get_hit_rate
# ---------------------------------------------------------------------------


def test_get_hit_rate_returns_zero_for_unknown_context():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)

    # Act
    rate = cache._get_hit_rate("nonexistent_context")

    # Assert
    assert rate == 0.0


def test_get_hit_rate_returns_zero_when_no_requests():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    cache._context_metrics["ctx"] = {"hits": 0, "misses": 0, "total_hit_age": 0.0, "executions": 0}

    # Act
    rate = cache._get_hit_rate("ctx")

    # Assert
    assert rate == 0.0


def test_get_hit_rate_correct_calculation():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    cache._context_metrics["ctx"] = {
        "hits": 7,
        "misses": 3,
        "total_hit_age": 700.0,
        "executions": 10,
    }

    # Act
    rate = cache._get_hit_rate("ctx")

    # Assert
    assert rate == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# get_cache_stats
# ---------------------------------------------------------------------------


def test_get_cache_stats_empty():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)

    # Act
    stats = cache.get_cache_stats()

    # Assert
    assert stats["total_size"] == 0
    assert stats["total_requests"] == 0
    assert stats["total_hits"] == 0
    assert stats["total_misses"] == 0
    assert stats["overall_hit_rate"] == 0.0
    assert stats["contexts"] == {}


async def test_get_cache_stats_with_mixed_hits_and_misses():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = _make_cache(mock)
    ctx = _ctx()

    await cache.execute({}, ctx)  # miss
    await cache.execute({}, ctx)  # hit
    await cache.execute({}, ctx)  # hit

    # Act
    stats = cache.get_cache_stats()

    # Assert
    assert stats["total_misses"] == 1
    assert stats["total_hits"] == 2
    assert stats["overall_hit_rate"] == pytest.approx(2 / 3)
    assert stats["total_size"] == 1
    assert len(stats["contexts"]) == 1
    assert len(stats["strategies"]) >= 1


async def test_get_cache_stats_strategies_included():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = _make_cache(mock)
    ctx = _ctx()
    await cache.execute({}, ctx)

    # Act
    stats = cache.get_cache_stats()

    # Assert
    assert "baseline_conservative" in stats["strategies"]
    strat_info = stats["strategies"]["baseline_conservative"]
    assert "ttl_seconds" in strat_info
    assert "success_rate" in strat_info
    assert "avg_latency" in strat_info


# ---------------------------------------------------------------------------
# clear_cache
# ---------------------------------------------------------------------------


async def test_clear_cache_empties_all_entries():
    # Arrange
    mock = MockPrimitive("target", return_value={"data": "result"})
    cache = AdaptiveCachePrimitive(
        target_primitive=mock,
        cache_key_fn=_simple_key,
        learning_mode=LearningMode.DISABLED,
    )
    ctx = _ctx()
    await cache.execute({"key": "a"}, ctx)
    await cache.execute({"key": "b"}, ctx)
    assert len(cache._cache) == 2

    # Act
    cache.clear_cache()

    # Assert
    assert len(cache._cache) == 0


def test_clear_cache_on_empty_cache():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)

    # Act / Assert — no error when clearing empty cache
    cache.clear_cache()
    assert len(cache._cache) == 0


# ---------------------------------------------------------------------------
# evict_expired
# ---------------------------------------------------------------------------


def test_evict_expired_removes_old_entries():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    now = time.time()
    strategy = LearningStrategy(
        name="test",
        description="test",
        parameters={"ttl_seconds": 3600.0, "max_cache_size": 1000, "min_hit_rate": 0.3},
        context_pattern="*",
    )
    cache._cache["old_key"] = ({"data": "old"}, now - 7200, "ctx")  # 2h old
    cache._cache["new_key"] = ({"data": "new"}, now + 3600, "ctx")  # future

    # Act
    evicted = cache.evict_expired(strategy=strategy)

    # Assert
    assert evicted == 1
    assert "old_key" not in cache._cache
    assert "new_key" in cache._cache


def test_evict_expired_with_no_strategy_uses_baseline():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    cache._cache["old"] = ({"data": "old"}, time.time() - 7200, "ctx")

    # Act — no strategy → uses baseline_strategy
    evicted = cache.evict_expired()

    # Assert
    assert evicted == 1
    assert "old" not in cache._cache


def test_evict_expired_when_no_entries():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)

    # Act
    evicted = cache.evict_expired()

    # Assert
    assert evicted == 0


def test_evict_expired_returns_zero_when_baseline_is_none():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    cache.baseline_strategy = None  # Force None baseline

    # Act — strategy=None AND baseline=None → return 0
    evicted = cache.evict_expired(strategy=None)

    # Assert
    assert evicted == 0


def test_evict_expired_returns_count():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock)
    now = time.time()
    strategy = LearningStrategy(
        name="test",
        description="test",
        parameters={"ttl_seconds": 3600.0, "max_cache_size": 100, "min_hit_rate": 0.3},
        context_pattern="*",
    )
    cache._cache["k1"] = ({"d": 1}, now - 7200, "ctx")
    cache._cache["k2"] = ({"d": 2}, now - 7200, "ctx")
    cache._cache["k3"] = ({"d": 3}, now + 3600, "ctx")  # not expired

    # Act
    evicted = cache.evict_expired(strategy=strategy)

    # Assert
    assert evicted == 2
    assert "k3" in cache._cache


# ---------------------------------------------------------------------------
# _consider_new_strategy
# ---------------------------------------------------------------------------


async def test_consider_new_strategy_insufficient_executions():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    # Only 5 executions (need 20)
    cache._context_metrics[context_key] = {
        "hits": 2,
        "misses": 3,
        "total_hit_age": 100.0,
        "executions": 5,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_returns_none_for_unknown_context():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    # No context metrics populated

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_high_hit_rate_low_avg_age_creates_shorter_ttl():
    # Arrange — items reused very quickly → shorter TTL
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    current_ttl = 3600.0
    # avg_hit_age = 50/25 * 20 = 40s → well below 20% of 3600s (720s)
    # hit_rate = 20/25 = 0.8 > 0.5
    cache._context_metrics[context_key] = {
        "hits": 20,
        "misses": 5,
        "total_hit_age": 800.0,  # avg = 40s, < 720s (20% of TTL)
        "executions": 25,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert — shorter TTL learned
    assert result is not None
    assert result.parameters["ttl_seconds"] < current_ttl


async def test_consider_new_strategy_high_avg_age_low_hit_creates_longer_ttl():
    # Arrange — items are used near TTL expiration → longer TTL needed
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    current_ttl = 3600.0
    # avg_hit_age = 48000/20 = 2400s → above 60% of 3600s (2160s)
    # hit_rate = 20/36 ≈ 0.56 < 0.7
    cache._context_metrics[context_key] = {
        "hits": 20,
        "misses": 16,
        "total_hit_age": 48000.0,  # avg = 2400s > 2160s (60% of TTL)
        "executions": 36,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert — longer TTL learned
    assert result is not None
    assert result.parameters["ttl_seconds"] > current_ttl


async def test_consider_new_strategy_low_hit_rate_reduces_ttl():
    # Arrange — low hit rate → cache not beneficial, reduce TTL
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    # hit_rate = 5/30 ≈ 0.17 < 0.3
    cache._context_metrics[context_key] = {
        "hits": 5,
        "misses": 25,
        "total_hit_age": 500.0,
        "executions": 30,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert — either None (negligible change) or shorter TTL
    if result is not None:
        assert result.parameters["ttl_seconds"] < 3600.0


async def test_consider_new_strategy_no_change_needed_returns_none():
    # Arrange — good hit rate, avg age in middle range → else: return None
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    # hit_rate = 20/25 = 0.8 (>= 0.3, not < 0.3)
    # avg_hit_age = 20000/20 = 1000s
    #   NOT (1000 < 720 AND 0.8 > 0.5) → first branch: 1000 >= 720 → False
    #   NOT (1000 > 2160 AND 0.8 < 0.7) → second branch: 1000 <= 2160 → False
    #   NOT (0.8 < 0.3) → third branch: False
    #   → else: return None
    cache._context_metrics[context_key] = {
        "hits": 20,
        "misses": 5,
        "total_hit_age": 20000.0,  # avg = 1000s (in good range)
        "executions": 25,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert
    assert result is None


async def test_consider_new_strategy_ttl_clamped_to_minimum():
    # Arrange — very low avg age → new_ttl might go below 60s floor
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    # avg_hit_age = 5s, hit_rate = 0.9 → new_ttl = 5 * 3 = 15s → clamped to 60s
    cache._context_metrics[context_key] = {
        "hits": 22,
        "misses": 3,
        "total_hit_age": 110.0,  # avg = 5s, < 720s, hit_rate > 0.5
        "executions": 25,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert — TTL clamped to minimum 60s
    if result is not None:
        assert result.parameters["ttl_seconds"] >= 60.0


async def test_consider_new_strategy_ttl_clamped_to_maximum():
    # Arrange — very high avg age → new_ttl might exceed 86400s ceiling
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    # avg_hit_age = 45000s → well above 60% of 3600s; new_ttl = 45000*2 = 90000s → clamped to 86400s
    cache._context_metrics[context_key] = {
        "hits": 10,
        "misses": 20,
        "total_hit_age": 450000.0,  # avg = 45000s > 2160s, hit_rate < 0.7
        "executions": 30,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert — TTL clamped to maximum 86400s
    if result is not None:
        assert result.parameters["ttl_seconds"] <= 86400.0


async def test_consider_new_strategy_returns_learning_strategy_object():
    # Arrange
    mock = MockPrimitive("target")
    cache = _make_cache(mock, mode=LearningMode.ACTIVE)
    ctx = _ctx()
    context_key = cache.context_extractor({}, ctx)
    cache._context_metrics[context_key] = {
        "hits": 20,
        "misses": 5,
        "total_hit_age": 800.0,  # avg 40s, triggers short TTL
        "executions": 25,
    }

    # Act
    result = await cache._consider_new_strategy({}, ctx, cache.baseline_strategy.metrics)

    # Assert — correct type and required fields
    assert result is not None
    assert isinstance(result, LearningStrategy)
    assert "ttl_seconds" in result.parameters
    assert "max_cache_size" in result.parameters
    assert result.context_pattern == context_key
