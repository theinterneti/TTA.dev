"""Comprehensive tests for AdaptiveRetryPrimitive — AAA pattern throughout.

Coverage targets:
- RetryStrategyParams: to_dict, from_dict, roundtrip
- AdaptiveRetryPrimitive.__init__, _get_default_strategy, _create_baseline_strategy
- _execute_with_strategy (both tracer/no-tracer branches)
- _execute_retry_with_tracing (success, retry, exhaustion; with/without span)
- _context_extractor (all hint branches: timeout, rate_limit, network, multiple)
- _learn_from_execution (OBSERVE early return, non-observe path)
- _consider_reducing_retries (creates, skips-existing, skips-max)
- _consider_increasing_retries (creates, skips-existing)
- _consider_error_specific_strategy (TimeoutError, ConnectionError, HTTPException,
  RequestException, unknown; skips-existing)
- _consider_faster_backoff (creates, skips-existing)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from ttadev.primitives.adaptive.base import LearningMode, LearningStrategy
from ttadev.primitives.adaptive.retry import AdaptiveRetryPrimitive, RetryStrategyParams
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**metadata) -> WorkflowContext:
    return WorkflowContext(metadata=metadata)


def _make_strategy(name: str = "test", max_retries: int = 3) -> LearningStrategy:
    return LearningStrategy(
        name=name,
        description="test strategy",
        parameters=RetryStrategyParams(max_retries=max_retries, initial_delay=0.01).to_dict(),
        context_pattern="",
    )


# ---------------------------------------------------------------------------
# RetryStrategyParams
# ---------------------------------------------------------------------------


def test_retry_strategy_params_defaults():
    # Arrange / Act
    params = RetryStrategyParams()

    # Assert
    assert params.max_retries == 3
    assert params.initial_delay == 1.0
    assert params.backoff_factor == 2.0
    assert params.max_delay == 60.0
    assert params.jitter is True
    assert params.jitter_factor == 0.1


def test_retry_strategy_params_to_dict():
    # Arrange
    params = RetryStrategyParams(max_retries=5, initial_delay=0.5, jitter=False)

    # Act
    d = params.to_dict()

    # Assert
    assert d["max_retries"] == 5
    assert d["initial_delay"] == 0.5
    assert d["jitter"] is False
    assert set(d.keys()) == {
        "max_retries",
        "initial_delay",
        "backoff_factor",
        "max_delay",
        "jitter",
        "jitter_factor",
    }


def test_retry_strategy_params_from_dict():
    # Arrange
    d = {
        "max_retries": 7,
        "initial_delay": 2.0,
        "backoff_factor": 3.0,
        "max_delay": 120.0,
        "jitter": False,
        "jitter_factor": 0.05,
    }

    # Act
    params = RetryStrategyParams.from_dict(d)

    # Assert
    assert params.max_retries == 7
    assert params.initial_delay == 2.0
    assert params.jitter is False
    assert params.jitter_factor == 0.05


def test_retry_strategy_params_roundtrip():
    # Arrange
    original = RetryStrategyParams(
        max_retries=6,
        initial_delay=0.25,
        backoff_factor=1.5,
        max_delay=45.0,
        jitter=False,
        jitter_factor=0.15,
    )

    # Act
    restored = RetryStrategyParams.from_dict(original.to_dict())

    # Assert
    assert restored.max_retries == original.max_retries
    assert restored.initial_delay == original.initial_delay
    assert restored.backoff_factor == original.backoff_factor
    assert restored.max_delay == original.max_delay
    assert restored.jitter == original.jitter
    assert restored.jitter_factor == original.jitter_factor


# ---------------------------------------------------------------------------
# AdaptiveRetryPrimitive.__init__ / _get_default_strategy
# ---------------------------------------------------------------------------


def test_adaptive_retry_init_stores_target():
    # Arrange / Act
    mock = MockPrimitive("target", return_value={"data": "ok"})
    retry = AdaptiveRetryPrimitive(mock)

    # Assert
    assert retry.target_primitive is mock
    assert retry.learning_mode == LearningMode.VALIDATE


def test_adaptive_retry_init_creates_baseline_strategy():
    # Arrange / Act
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)

    # Assert
    assert "baseline_exponential" in retry.strategies
    assert retry.baseline_strategy is not None
    assert retry.baseline_strategy.name == "baseline_exponential"


def test_get_default_strategy_returns_baseline_exponential():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)

    # Act
    strategy = retry._get_default_strategy()

    # Assert
    assert strategy.name == "baseline_exponential"
    assert strategy.parameters["max_retries"] == 3
    assert strategy.parameters["jitter"] is True
    assert strategy.context_pattern == ""


# ---------------------------------------------------------------------------
# _execute_retry_with_tracing — no span (normal test path)
# ---------------------------------------------------------------------------


async def test_execute_retry_success_on_first_attempt(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock = MockPrimitive("target", return_value={"data": "result"})
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=3, initial_delay=0.01)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, None)

    # Assert
    assert result["success"] is True
    assert result["attempts"] == 1
    assert mock.call_count == 1


async def test_execute_retry_succeeds_after_failures(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    call_count = 0

    def flaky(inp, ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient")
        return {"data": "recovered"}

    mock = MockPrimitive("target", side_effect=flaky)
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=5, initial_delay=0.01)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, None)

    # Assert
    assert result["success"] is True
    assert result["attempts"] == 3


async def test_execute_retry_exhaustion_returns_failure_dict(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock = MockPrimitive("target", raise_error=ValueError("always fails"))
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=2, initial_delay=0.01)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, None)

    # Assert
    assert result["success"] is False
    assert result["attempts"] == 3  # 1 initial + 2 retries
    assert result["error"] is not None
    assert result["error_type"] == "ValueError"
    assert result["result"] is None


async def test_execute_retry_no_sleep_after_last_attempt(monkeypatch):
    # Arrange
    mock_sleep = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", mock_sleep)
    mock = MockPrimitive("target", raise_error=ValueError("fail"))
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=3, initial_delay=0.01)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    await retry._execute_retry_with_tracing({}, ctx, strategy, params, None)

    # Assert — sleep called exactly max_retries times (not after last attempt)
    assert mock_sleep.call_count == 3


async def test_execute_retry_with_jitter_no_negative_delay(monkeypatch):
    # Arrange — extreme jitter_factor ensures we test max(0, ...) floor
    mock_sleep = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", mock_sleep)
    call_count = 0

    def flaky(inp, ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("fail")
        return {"data": "ok"}

    mock = MockPrimitive("target", side_effect=flaky)
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=3, initial_delay=0.01, jitter=True, jitter_factor=10.0)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, None)

    # Assert — jitter shouldn't cause negative delays (max(0, delay) applied)
    assert result["success"] is True
    for call_args in mock_sleep.call_args_list:
        assert call_args[0][0] >= 0


async def test_execute_retry_max_delay_capped(monkeypatch):
    # Arrange
    mock_sleep = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", mock_sleep)
    mock = MockPrimitive("target", raise_error=ValueError("fail"))
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    # Large backoff but small max_delay
    params = RetryStrategyParams(
        max_retries=3, initial_delay=100.0, backoff_factor=10.0, max_delay=0.05, jitter=False
    )
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    await retry._execute_retry_with_tracing({}, ctx, strategy, params, None)

    # Assert — all sleep calls capped at max_delay
    for call_args in mock_sleep.call_args_list:
        assert call_args[0][0] <= 0.05


# ---------------------------------------------------------------------------
# _execute_retry_with_tracing — with mock span (covers span attribute lines)
# ---------------------------------------------------------------------------


async def test_execute_retry_success_with_mock_span(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock_span = MagicMock()
    mock = MockPrimitive("target", return_value={"data": "ok"})
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=1, initial_delay=0.01)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, mock_span)

    # Assert — span attributes set
    assert result["success"] is True
    mock_span.set_attribute.assert_called()
    # Verify some key attributes were set
    attribute_names = [call[0][0] for call in mock_span.set_attribute.call_args_list]
    assert "retry.strategy_name" in attribute_names
    assert "retry.max_retries" in attribute_names
    assert "retry.final_attempts" in attribute_names
    assert "retry.success" in attribute_names


async def test_execute_retry_failure_with_mock_span(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock_span = MagicMock()
    mock = MockPrimitive("target", raise_error=RuntimeError("fail"))
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=2, initial_delay=0.01)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, mock_span)

    # Assert
    assert result["success"] is False
    mock_span.set_attribute.assert_called()
    mock_span.add_event.assert_called()
    # Verify attempt failure events recorded
    event_names = [call[0][0] for call in mock_span.add_event.call_args_list]
    assert "retry_attempt_failed" in event_names


async def test_execute_retry_delay_attribute_set_per_attempt_with_span(monkeypatch):
    # Arrange
    mock_sleep = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", mock_sleep)
    mock_span = MagicMock()
    call_count = 0

    def flaky(inp, ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("transient")
        return {"data": "ok"}

    mock = MockPrimitive("target", side_effect=flaky)
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    params = RetryStrategyParams(max_retries=3, initial_delay=0.01, jitter=False)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    result = await retry._execute_retry_with_tracing({}, ctx, strategy, params, mock_span)

    # Assert — delay attribute for attempt 1 was set
    assert result["success"] is True
    attribute_names = [call[0][0] for call in mock_span.set_attribute.call_args_list]
    assert "retry.delay_attempt_1" in attribute_names


# ---------------------------------------------------------------------------
# execute() full path via InstrumentedPrimitive
# ---------------------------------------------------------------------------


async def test_execute_full_path_success(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock = MockPrimitive("target", return_value={"data": "result"})
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    ctx = _ctx()

    # Act
    result = await retry.execute({}, ctx)

    # Assert
    assert result["success"] is True
    assert mock.call_count == 1


async def test_execute_full_path_with_active_learning(monkeypatch):
    # Arrange — ACTIVE mode uses _learn_from_execution path
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock = MockPrimitive("target", return_value={"data": "ok"})
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    ctx = _ctx(environment="prod", priority="high")

    # Act — no error should occur even with ACTIVE learning
    result = await retry.execute({}, ctx)

    # Assert
    assert result["success"] is True


async def test_execute_full_path_observe_learning(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock = MockPrimitive("target", return_value={"data": "ok"})
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.OBSERVE)
    ctx = _ctx()

    # Act
    result = await retry.execute({}, ctx)

    # Assert — observe mode still executes successfully
    assert result["success"] is True


# ---------------------------------------------------------------------------
# _context_extractor
# ---------------------------------------------------------------------------


def test_context_extractor_default_values():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = _ctx(environment="production", priority="critical")

    # Act
    key = retry._context_extractor({}, ctx)

    # Assert
    assert "env:production" in key
    assert "priority:critical" in key
    assert "errors:general" in key


def test_context_extractor_unknown_defaults():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = WorkflowContext()  # No metadata

    # Act
    key = retry._context_extractor({}, ctx)

    # Assert
    assert "env:unknown" in key
    assert "priority:normal" in key
    assert "time_sensitive:False" in key
    assert "errors:general" in key


def test_context_extractor_timeout_hint_in_input():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = _ctx()

    # Act
    key = retry._context_extractor({"operation": "timeout_based_check"}, ctx)

    # Assert
    assert "timeout" in key
    assert "general" not in key  # replaced by actual hints


def test_context_extractor_rate_limit_hint_in_input():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = _ctx()

    # Act
    key = retry._context_extractor({"error": "rate_limit_exceeded"}, ctx)

    # Assert
    assert "rate_limit" in key


def test_context_extractor_network_hint_in_input():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = _ctx()

    # Act
    key = retry._context_extractor({"type": "network_request"}, ctx)

    # Assert
    assert "network" in key


def test_context_extractor_multiple_hints():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = _ctx()

    # Act
    key = retry._context_extractor({"msg": "timeout rate_limit network error"}, ctx)

    # Assert
    assert "timeout" in key
    assert "rate_limit" in key
    assert "network" in key


def test_context_extractor_time_sensitive_flag():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock)
    ctx = _ctx(time_sensitive=True)

    # Act
    key = retry._context_extractor({}, ctx)

    # Assert
    assert "time_sensitive:True" in key


# ---------------------------------------------------------------------------
# _learn_from_execution
# ---------------------------------------------------------------------------


async def test_learn_from_execution_observe_mode_returns_early():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.OBSERVE)
    strategy = retry.baseline_strategy
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._learn_from_execution({}, ctx, strategy, {"success": True, "attempts": 1}, 0.1)

    # Assert — OBSERVE mode: returns immediately, no adaptations
    assert retry.total_adaptations == initial_adaptations


async def test_learn_from_execution_non_observe_no_tracer():
    # Arrange — without tracer, learning block is skipped
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    ctx = _ctx(environment="test")
    initial_adaptations = retry.total_adaptations

    # Act — no error; tracer is None so adaptation code is skipped
    await retry._learn_from_execution(
        {}, ctx, strategy, {"success": True, "attempts": 1, "error_type": "unknown"}, 0.1
    )

    # Assert
    assert retry.total_adaptations == initial_adaptations  # no tracer → no learning


# ---------------------------------------------------------------------------
# _consider_reducing_retries
# ---------------------------------------------------------------------------


async def test_consider_reducing_retries_creates_new_strategy():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    ctx = _ctx()
    context_key = "env:prod"
    initial_count = len(retry.strategies)

    # Act
    await retry._consider_reducing_retries(context_key, strategy, ctx)

    # Assert — new strategy added
    assert len(retry.strategies) > initial_count
    assert retry.total_adaptations == 1
    new_strategy = next(s for s in retry.strategies.values() if "low_retry" in s.name)
    assert new_strategy.parameters["max_retries"] < strategy.parameters["max_retries"]


async def test_consider_reducing_retries_skips_if_strategy_exists():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    context_key = "env:prod"
    strategy_name = f"low_retry_{hash(context_key) % 1000}"
    retry.strategies[strategy_name] = LearningStrategy(
        name=strategy_name, description="pre-existing", parameters={}, context_pattern=""
    )
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_reducing_retries(context_key, strategy, ctx)

    # Assert — already exists, no new adaptation
    assert retry.total_adaptations == initial_adaptations


async def test_consider_reducing_retries_skips_when_at_max_strategies():
    # Arrange — max_strategies=1, baseline already occupies the slot
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE, max_strategies=1)
    strategy = retry.baseline_strategy
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_reducing_retries("env:prod", strategy, ctx)

    # Assert — max reached, no adaptation
    assert retry.total_adaptations == initial_adaptations


async def test_consider_reducing_retries_initial_delay_clamped():
    # Arrange — baseline has large initial_delay; reduced strategy should clamp to 0.5
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    # Give the baseline a very large initial delay
    retry.baseline_strategy.parameters["initial_delay"] = 10.0
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    await retry._consider_reducing_retries("env:staging", strategy, ctx)

    # Assert — new strategy has initial_delay <= 0.5
    new = next(s for s in retry.strategies.values() if "low_retry" in s.name)
    assert new.parameters["initial_delay"] <= 0.5


# ---------------------------------------------------------------------------
# _consider_increasing_retries
# ---------------------------------------------------------------------------


async def test_consider_increasing_retries_creates_new_strategy():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    await retry._consider_increasing_retries("env:prod", strategy, "ValueError", ctx)

    # Assert
    new = [s for s in retry.strategies.values() if "high_retry" in s.name]
    assert len(new) == 1
    assert new[0].parameters["max_retries"] > strategy.parameters["max_retries"]
    assert retry.total_adaptations == 1


async def test_consider_increasing_retries_max_retries_capped_at_8():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    retry.baseline_strategy.parameters["max_retries"] = 7  # near cap
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    await retry._consider_increasing_retries("env:prod", strategy, "IOError", ctx)

    new = [s for s in retry.strategies.values() if "high_retry" in s.name]
    # Assert — capped at 8
    assert new[0].parameters["max_retries"] <= 8


async def test_consider_increasing_retries_skips_if_exists():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    context_key = "env:prod"
    error_type = "ValueError"
    strategy_name = f"high_retry_{error_type.lower()}_{hash(context_key) % 1000}"
    retry.strategies[strategy_name] = LearningStrategy(
        name=strategy_name, description="existing", parameters={}, context_pattern=""
    )
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_increasing_retries(context_key, strategy, error_type, ctx)

    # Assert
    assert retry.total_adaptations == initial_adaptations


# ---------------------------------------------------------------------------
# _consider_error_specific_strategy
# ---------------------------------------------------------------------------


async def test_consider_error_specific_timeout_error():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    ctx = _ctx()
    initial_count = len(retry.strategies)

    # Act
    await retry._consider_error_specific_strategy("env:prod", "TimeoutError", False, 3, ctx)

    # Assert — TimeoutError-specific parameters applied
    assert len(retry.strategies) > initial_count
    new = next(s for s in retry.strategies.values() if "error_specific" in s.name)
    assert new.parameters["max_retries"] == 2
    assert new.parameters["initial_delay"] == 2.0
    assert new.parameters["backoff_factor"] == 3.0
    assert new.parameters["jitter_factor"] == 0.2


async def test_consider_error_specific_connection_error():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    ctx = _ctx()

    # Act
    await retry._consider_error_specific_strategy("env:prod", "ConnectionError", False, 6, ctx)

    # Assert — ConnectionError-specific parameters
    new = next(s for s in retry.strategies.values() if "error_specific" in s.name)
    assert new.parameters["max_retries"] == 5
    assert new.parameters["initial_delay"] == 0.5
    assert new.parameters["backoff_factor"] == 1.8
    assert new.parameters["max_delay"] == 30.0


async def test_consider_error_specific_http_exception():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    ctx = _ctx()

    # Act
    await retry._consider_error_specific_strategy("env:prod", "HTTPException", False, 5, ctx)

    # Assert — HTTPException-specific parameters
    new = next(s for s in retry.strategies.values() if "error_specific" in s.name)
    assert new.parameters["max_retries"] == 4
    assert new.parameters["initial_delay"] == 0.2
    assert new.parameters["backoff_factor"] == 2.5
    assert new.parameters["max_delay"] == 45.0


async def test_consider_error_specific_request_exception():
    # Arrange — "RequestException" falls into the HTTPException elif branch
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    ctx = _ctx()

    # Act
    await retry._consider_error_specific_strategy("env:prod", "RequestException", False, 5, ctx)

    # Assert — also uses HTTP parameters
    new = next(s for s in retry.strategies.values() if "error_specific" in s.name)
    assert new.parameters["max_retries"] == 4


async def test_consider_error_specific_unknown_type_uses_default_params():
    # Arrange — unknown error type → default RetryStrategyParams()
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    ctx = _ctx()

    # Act
    await retry._consider_error_specific_strategy("env:prod", "UnknownError", False, 2, ctx)

    # Assert — strategy still created with default params
    new = [s for s in retry.strategies.values() if "error_specific" in s.name]
    assert len(new) == 1


async def test_consider_error_specific_skips_if_exists():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    context_key = "env:prod"
    error_type = "TimeoutError"
    strategy_name = f"error_specific_{error_type.lower()}_{hash(context_key) % 1000}"
    retry.strategies[strategy_name] = LearningStrategy(
        name=strategy_name, description="existing", parameters={}, context_pattern=""
    )
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_error_specific_strategy(context_key, error_type, False, 1, ctx)

    # Assert
    assert retry.total_adaptations == initial_adaptations


async def test_consider_error_specific_skips_when_at_max_strategies():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE, max_strategies=1)
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_error_specific_strategy("env:prod", "TimeoutError", False, 1, ctx)

    # Assert
    assert retry.total_adaptations == initial_adaptations


# ---------------------------------------------------------------------------
# _consider_faster_backoff
# ---------------------------------------------------------------------------


async def test_consider_faster_backoff_creates_strategy():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    ctx = _ctx()
    initial_count = len(retry.strategies)

    # Act
    await retry._consider_faster_backoff("env:prod", strategy, ctx)

    # Assert
    assert len(retry.strategies) > initial_count
    assert retry.total_adaptations == 1
    new = next(s for s in retry.strategies.values() if "fast_backoff" in s.name)
    # New strategy should have faster (smaller) initial_delay
    assert new.parameters["initial_delay"] < strategy.parameters["initial_delay"]
    assert new.parameters["max_delay"] < strategy.parameters["max_delay"]
    assert new.parameters["jitter_factor"] == 0.05


async def test_consider_faster_backoff_skips_if_exists():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    strategy = retry.baseline_strategy
    context_key = "env:prod"
    strategy_name = f"fast_backoff_{hash(context_key) % 1000}"
    retry.strategies[strategy_name] = LearningStrategy(
        name=strategy_name, description="existing", parameters={}, context_pattern=""
    )
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_faster_backoff(context_key, strategy, ctx)

    # Assert
    assert retry.total_adaptations == initial_adaptations


async def test_consider_faster_backoff_initial_delay_floor():
    # Arrange — very small initial_delay; floor should be 0.1
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE)
    retry.baseline_strategy.parameters["initial_delay"] = 0.05  # 0.05 * 0.5 = 0.025 < 0.1
    strategy = retry.baseline_strategy
    ctx = _ctx()

    # Act
    await retry._consider_faster_backoff("env:staging", strategy, ctx)

    # Assert — initial_delay floored at 0.1
    new = next(s for s in retry.strategies.values() if "fast_backoff" in s.name)
    assert new.parameters["initial_delay"] >= 0.1


async def test_consider_faster_backoff_skips_when_at_max_strategies():
    # Arrange
    mock = MockPrimitive("target")
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.ACTIVE, max_strategies=1)
    strategy = retry.baseline_strategy
    ctx = _ctx()
    initial_adaptations = retry.total_adaptations

    # Act
    await retry._consider_faster_backoff("env:prod", strategy, ctx)

    # Assert
    assert retry.total_adaptations == initial_adaptations


# ---------------------------------------------------------------------------
# Learning mode: DISABLED uses baseline
# ---------------------------------------------------------------------------


async def test_learning_mode_disabled_uses_baseline_strategy(monkeypatch):
    # Arrange
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    mock = MockPrimitive("target", return_value={"data": "ok"})
    retry = AdaptiveRetryPrimitive(mock, learning_mode=LearningMode.DISABLED)
    ctx = _ctx()

    # Act
    result = await retry.execute({}, ctx)

    # Assert — disabled mode still works, uses baseline
    assert result["success"] is True
    assert retry.total_adaptations == 0
