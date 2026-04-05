"""Comprehensive unit tests for CircuitBreakerPrimitive and legacy utilities.

Coverage targets:
- CircuitBreakerConfig: defaults and all validation branches
- CircuitBreakerError: attributes and string representation
- CircuitState: enum values
- CircuitBreakerPrimitive state machine:
    CLOSED normal pass-through
    CLOSED -> OPEN on consecutive failures
    OPEN raises CircuitBreakerError without calling wrapped primitive
    OPEN -> HALF_OPEN after recovery_timeout (time-mocked)
    HALF_OPEN -> OPEN on any failure
    HALF_OPEN -> CLOSED after success_threshold consecutive successes
- Properties: state, failure_count, success_count
- reset() method
- expected_exception filter (non-matching exceptions pass through)
- _should_attempt_reset edge cases
- Legacy: ErrorCategory, ErrorSeverity, RetryConfig,
          classify_error, should_retry, calculate_delay,
          CircuitBreaker, with_retry, with_retry_async
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerPrimitive,
    CircuitState,
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    calculate_delay,
    classify_error,
    should_retry,
    with_retry,
    with_retry_async,
)
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(wid: str = "test-cb") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


def _mock_primitive(
    return_value: object = None,
    raises: Exception | None = None,
) -> MagicMock:
    """Return a MagicMock whose execute is an AsyncMock."""
    prim = MagicMock()
    if raises is not None:
        prim.execute = AsyncMock(side_effect=raises)
    else:
        prim.execute = AsyncMock(return_value=return_value or {"result": "ok"})
    return prim


def _raises(exc: Exception):
    """Return a zero-arg callable that raises exc — for legacy CircuitBreaker tests."""

    def f():
        raise exc

    return f


async def _trip_circuit(cb: CircuitBreakerPrimitive, threshold: int) -> None:
    """Drive the circuit from CLOSED to OPEN by producing `threshold` tracked failures."""
    for _ in range(threshold):
        try:
            await cb.execute({}, _ctx())
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CircuitState
# ---------------------------------------------------------------------------


class TestCircuitState:
    def test_closed_value(self) -> None:
        assert CircuitState.CLOSED == "closed"

    def test_open_value(self) -> None:
        assert CircuitState.OPEN == "open"

    def test_half_open_value(self) -> None:
        assert CircuitState.HALF_OPEN == "half_open"

    def test_is_str(self) -> None:
        assert isinstance(CircuitState.CLOSED, str)


# ---------------------------------------------------------------------------
# CircuitBreakerConfig — defaults
# ---------------------------------------------------------------------------


class TestCircuitBreakerConfigDefaults:
    def test_failure_threshold_default(self) -> None:
        assert CircuitBreakerConfig().failure_threshold == 5

    def test_recovery_timeout_default(self) -> None:
        assert CircuitBreakerConfig().recovery_timeout == 60.0

    def test_success_threshold_default(self) -> None:
        assert CircuitBreakerConfig().success_threshold == 2

    def test_expected_exception_default(self) -> None:
        assert CircuitBreakerConfig().expected_exception is Exception

    def test_custom_values_stored(self) -> None:
        cfg = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=10.0,
            success_threshold=1,
            expected_exception=ValueError,
        )
        assert cfg.failure_threshold == 3
        assert cfg.recovery_timeout == 10.0
        assert cfg.success_threshold == 1
        assert cfg.expected_exception is ValueError


# ---------------------------------------------------------------------------
# CircuitBreakerConfig — validation
# ---------------------------------------------------------------------------


class TestCircuitBreakerConfigValidation:
    def test_failure_threshold_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreakerConfig(failure_threshold=0)

    def test_failure_threshold_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreakerConfig(failure_threshold=-1)

    def test_recovery_timeout_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreakerConfig(recovery_timeout=0)

    def test_recovery_timeout_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreakerConfig(recovery_timeout=-5.0)

    def test_success_threshold_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="success_threshold"):
            CircuitBreakerConfig(success_threshold=0)

    def test_success_threshold_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="success_threshold"):
            CircuitBreakerConfig(success_threshold=-3)

    def test_boundary_values_are_valid(self) -> None:
        cfg = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.001,
            success_threshold=1,
        )
        assert cfg.failure_threshold == 1


# ---------------------------------------------------------------------------
# CircuitBreakerError
# ---------------------------------------------------------------------------


class TestCircuitBreakerError:
    def test_failure_count_stored(self) -> None:
        err = CircuitBreakerError(failure_count=7)
        assert err.failure_count == 7

    def test_last_error_stored(self) -> None:
        cause = RuntimeError("underlying")
        err = CircuitBreakerError(failure_count=3, last_error=cause)
        assert err.last_error is cause

    def test_last_error_defaults_to_none(self) -> None:
        err = CircuitBreakerError(failure_count=1)
        assert err.last_error is None

    def test_str_contains_failure_count(self) -> None:
        err = CircuitBreakerError(failure_count=5)
        assert "5" in str(err)

    def test_is_exception(self) -> None:
        assert isinstance(CircuitBreakerError(failure_count=1), Exception)


# ---------------------------------------------------------------------------
# CircuitBreakerPrimitive — construction
# ---------------------------------------------------------------------------


class TestCircuitBreakerPrimitiveInit:
    def test_initial_state_is_closed(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        assert cb.state == CircuitState.CLOSED

    def test_initial_failure_count_is_zero(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        assert cb.failure_count == 0

    def test_initial_success_count_is_zero(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        assert cb.success_count == 0

    def test_default_config_when_none(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive(), config=None)
        assert cb.config.failure_threshold == 5

    def test_custom_config_stored(self) -> None:
        cfg = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreakerPrimitive(_mock_primitive(), config=cfg)
        assert cb.config.failure_threshold == 2


# ---------------------------------------------------------------------------
# CLOSED state — normal pass-through
# ---------------------------------------------------------------------------


class TestClosedStatePassThrough:
    @pytest.mark.asyncio
    async def test_returns_primitive_result(self) -> None:
        # Arrange
        inner = _mock_primitive(return_value={"data": 42})
        cb = CircuitBreakerPrimitive(inner)

        # Act
        result = await cb.execute({"req": "x"}, _ctx())

        # Assert
        assert result == {"data": 42}

    @pytest.mark.asyncio
    async def test_calls_primitive_with_correct_args(self) -> None:
        # Arrange
        inner = _mock_primitive(return_value="ok")
        cb = CircuitBreakerPrimitive(inner)
        ctx = _ctx("wf-123")

        # Act
        await cb.execute("my-input", ctx)

        # Assert
        inner.execute.assert_awaited_once_with("my-input", ctx)

    @pytest.mark.asyncio
    async def test_state_remains_closed_on_success(self) -> None:
        # Arrange
        cb = CircuitBreakerPrimitive(_mock_primitive(return_value="ok"))

        # Act
        await cb.execute({}, _ctx())

        # Assert
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=5)
        calls = {"n": 0}

        async def sometimes_fails(input_data, context):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise ValueError("transient")
            return "ok"

        inner = MagicMock()
        inner.execute = AsyncMock(side_effect=sometimes_fails)
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Trigger 2 failures (below threshold of 5)
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.execute({}, _ctx())

        assert cb.failure_count == 2

        # Act — one success resets failure_count
        await cb.execute({}, _ctx())

        # Assert
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_multiple_calls_all_succeed(self) -> None:
        # Arrange
        inner = _mock_primitive(return_value="ok")
        cb = CircuitBreakerPrimitive(inner)

        # Act + Assert
        for i in range(5):
            result = await cb.execute(i, _ctx())
            assert result == "ok"

        assert cb.state == CircuitState.CLOSED
        assert inner.execute.await_count == 5


# ---------------------------------------------------------------------------
# CLOSED → OPEN: consecutive failures trigger threshold
# ---------------------------------------------------------------------------


class TestClosedToOpenTransition:
    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=3)
        inner = _mock_primitive(raises=RuntimeError("boom"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act — exactly 3 failures
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.execute({}, _ctx())

        # Assert
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_failure_count_increments(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=5)
        inner = _mock_primitive(raises=ValueError("err"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act + Assert
        for i in range(1, 4):
            with pytest.raises(ValueError):
                await cb.execute({}, _ctx())
            assert cb.failure_count == i

    @pytest.mark.asyncio
    async def test_original_exception_propagates(self) -> None:
        # Arrange
        inner = _mock_primitive(raises=TypeError("type error"))
        cb = CircuitBreakerPrimitive(inner)

        # Act + Assert
        with pytest.raises(TypeError, match="type error"):
            await cb.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_stays_closed_below_threshold(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=3)
        inner = _mock_primitive(raises=ValueError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act — only 2 failures (threshold is 3)
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.execute({}, _ctx())

        # Assert
        assert cb.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# OPEN state — immediately raises CircuitBreakerError
# ---------------------------------------------------------------------------


class TestOpenStateImmediateFailure:
    @pytest.mark.asyncio
    async def test_raises_circuit_breaker_error(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreakerPrimitive(_mock_primitive(raises=ValueError("fail")), config=cfg)
        await _trip_circuit(cb, 2)

        # Act + Assert
        with pytest.raises(CircuitBreakerError):
            await cb.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_wrapped_primitive_not_called_when_open(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2)
        inner = _mock_primitive(raises=ValueError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        await _trip_circuit(cb, 2)
        call_count_before = inner.execute.await_count

        # Act
        with pytest.raises(CircuitBreakerError):
            await cb.execute({}, _ctx())

        # Assert — inner was NOT called again
        assert inner.execute.await_count == call_count_before

    @pytest.mark.asyncio
    async def test_error_has_correct_failure_count(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreakerPrimitive(_mock_primitive(raises=RuntimeError("err")), config=cfg)
        await _trip_circuit(cb, 3)

        # Act
        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.execute({}, _ctx())

        # Assert
        assert exc_info.value.failure_count == 3

    @pytest.mark.asyncio
    async def test_error_has_last_error(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2)
        root_cause = RuntimeError("root cause")
        cb = CircuitBreakerPrimitive(_mock_primitive(raises=root_cause), config=cfg)
        await _trip_circuit(cb, 2)

        # Act
        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.execute({}, _ctx())

        # Assert
        assert exc_info.value.last_error is root_cause

    @pytest.mark.asyncio
    async def test_repeated_open_calls_all_raise_circuit_breaker_error(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreakerPrimitive(_mock_primitive(raises=ValueError("fail")), config=cfg)
        await _trip_circuit(cb, 2)

        # Act + Assert — all further calls fail fast
        for _ in range(5):
            with pytest.raises(CircuitBreakerError):
                await cb.execute({}, _ctx())


# ---------------------------------------------------------------------------
# OPEN → HALF_OPEN: after recovery_timeout allows one probe
# ---------------------------------------------------------------------------


class TestOpenToHalfOpenTransition:
    @pytest.mark.asyncio
    async def test_transitions_and_allows_probe_through(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=30.0)
        inner = _mock_primitive(raises=ValueError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        await _trip_circuit(cb, 2)
        assert cb.state == CircuitState.OPEN

        # Swap inner to return success
        inner.execute = AsyncMock(return_value={"recovered": True})

        # Act — patch time so elapsed >= recovery_timeout
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=cb._last_failure_time + 31.0,
        ):
            result = await cb.execute({}, _ctx())

        # Assert
        assert result == {"recovered": True}

    @pytest.mark.asyncio
    async def test_single_success_stays_half_open_when_threshold_is_2(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=30.0,
            success_threshold=2,
        )
        inner = _mock_primitive(raises=ValueError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        await _trip_circuit(cb, 2)

        inner.execute = AsyncMock(return_value="ok")

        # Act — one probe succeeds; need 2 to fully close
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=cb._last_failure_time + 31.0,
        ):
            await cb.execute({}, _ctx())

        # Assert — still HALF_OPEN after 1 of 2 needed successes
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.success_count == 1

    @pytest.mark.asyncio
    async def test_does_not_transition_before_timeout(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60.0)
        inner = _mock_primitive(raises=ValueError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        await _trip_circuit(cb, 2)

        # Act — patch time so elapsed < recovery_timeout
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=cb._last_failure_time + 10.0,
        ):
            with pytest.raises(CircuitBreakerError):
                await cb.execute({}, _ctx())

        # Assert — remains OPEN
        assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# HALF_OPEN → CLOSED: success_threshold consecutive successes close circuit
# ---------------------------------------------------------------------------


class TestHalfOpenToClosedTransition:
    @pytest.mark.asyncio
    async def test_closes_after_success_threshold(self) -> None:
        # Arrange — manually place in HALF_OPEN
        cfg = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=30.0,
            success_threshold=2,
        )
        inner = _mock_primitive(return_value="ok")
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        cb._state = CircuitState.HALF_OPEN
        cb._failure_count = 2
        cb._success_count = 0
        cb._last_failure_time = 0.0

        # Act — first success: stays HALF_OPEN
        await cb.execute({}, _ctx())
        assert cb.state == CircuitState.HALF_OPEN

        # Act — second success: crosses threshold → CLOSED
        await cb.execute({}, _ctx())

        # Assert
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_count_reset_on_close(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, success_threshold=1)
        inner = _mock_primitive(return_value="ok")
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        cb._state = CircuitState.HALF_OPEN
        cb._failure_count = 2
        cb._last_failure_time = 0.0

        # Act
        await cb.execute({}, _ctx())

        # Assert
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_success_count_reset_on_close(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, success_threshold=1)
        inner = _mock_primitive(return_value="ok")
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        cb._state = CircuitState.HALF_OPEN
        cb._last_failure_time = 0.0

        # Act
        await cb.execute({}, _ctx())

        # Assert
        assert cb.success_count == 0
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_last_error_cleared_on_close(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, success_threshold=1)
        inner = _mock_primitive(return_value="ok")
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        cb._state = CircuitState.HALF_OPEN
        cb._last_error = RuntimeError("old error")
        cb._last_failure_time = 0.0

        # Act
        await cb.execute({}, _ctx())

        # Assert
        assert cb._last_error is None

    @pytest.mark.asyncio
    async def test_result_returned_on_successful_probe(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, success_threshold=1)
        inner = _mock_primitive(return_value={"healed": True})
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        cb._state = CircuitState.HALF_OPEN
        cb._last_failure_time = 0.0

        # Act
        result = await cb.execute({}, _ctx())

        # Assert
        assert result == {"healed": True}


# ---------------------------------------------------------------------------
# HALF_OPEN → OPEN: failure in half-open re-opens circuit
# ---------------------------------------------------------------------------


class TestHalfOpenToOpenTransition:
    @pytest.mark.asyncio
    async def test_reopens_on_failure(self) -> None:
        # Arrange
        inner = _mock_primitive(raises=RuntimeError("still broken"))
        cb = CircuitBreakerPrimitive(inner)
        cb._state = CircuitState.HALF_OPEN
        cb._failure_count = 3
        cb._last_failure_time = 0.0

        # Act
        with pytest.raises(RuntimeError):
            await cb.execute({}, _ctx())

        # Assert
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_success_count_reset_on_reopen(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=3, success_threshold=3)
        inner = _mock_primitive(raises=RuntimeError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        cb._state = CircuitState.HALF_OPEN
        cb._success_count = 2  # Had partial progress
        cb._last_failure_time = 0.0

        # Act
        with pytest.raises(RuntimeError):
            await cb.execute({}, _ctx())

        # Assert
        assert cb.state == CircuitState.OPEN
        assert cb.success_count == 0

    @pytest.mark.asyncio
    async def test_original_exception_propagates_from_half_open(self) -> None:
        # Arrange
        inner = _mock_primitive(raises=KeyError("missing"))
        cb = CircuitBreakerPrimitive(inner)
        cb._state = CircuitState.HALF_OPEN
        cb._last_failure_time = 0.0

        # Act + Assert
        with pytest.raises(KeyError):
            await cb.execute({}, _ctx())


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestProperties:
    def test_state_property(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        assert cb.state == CircuitState.CLOSED

    def test_failure_count_property(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._failure_count = 7
        assert cb.failure_count == 7

    def test_success_count_property(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._success_count = 3
        assert cb.success_count == 3


# ---------------------------------------------------------------------------
# reset() method
# ---------------------------------------------------------------------------


class TestResetMethod:
    def test_reset_from_open_restores_closed(self) -> None:
        # Arrange
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._state = CircuitState.OPEN
        cb._failure_count = 10

        # Act
        cb.reset()

        # Assert
        assert cb.state == CircuitState.CLOSED

    def test_reset_clears_failure_count(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._failure_count = 5
        cb.reset()
        assert cb.failure_count == 0

    def test_reset_clears_success_count(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._success_count = 2
        cb.reset()
        assert cb.success_count == 0

    def test_reset_clears_last_failure_time(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._last_failure_time = 12345.0
        cb.reset()
        assert cb._last_failure_time is None

    def test_reset_clears_last_error(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._last_error = RuntimeError("old")
        cb.reset()
        assert cb._last_error is None

    @pytest.mark.asyncio
    async def test_reset_from_open_allows_execution(self) -> None:
        # Arrange — trip the circuit
        cfg = CircuitBreakerConfig(failure_threshold=2)
        inner = _mock_primitive(raises=ValueError("fail"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)
        await _trip_circuit(cb, 2)
        assert cb.state == CircuitState.OPEN

        # Reset and execute successfully
        cb.reset()
        inner.execute = AsyncMock(return_value={"healed": True})
        result = await cb.execute({}, _ctx())

        # Assert
        assert result == {"healed": True}
        assert cb.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# expected_exception filter
# ---------------------------------------------------------------------------


class TestExpectedExceptionFilter:
    @pytest.mark.asyncio
    async def test_non_matching_exception_not_counted(self) -> None:
        # Arrange — only catch ValueError; inner raises TypeError
        cfg = CircuitBreakerConfig(failure_threshold=2, expected_exception=ValueError)
        inner = _mock_primitive(raises=TypeError("not counted"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act
        with pytest.raises(TypeError):
            await cb.execute({}, _ctx())

        # Assert — failure_count stays 0; circuit stays CLOSED
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_matching_exception_increments_failure_count(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=5, expected_exception=ValueError)
        inner = _mock_primitive(raises=ValueError("counted"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act
        with pytest.raises(ValueError):
            await cb.execute({}, _ctx())

        # Assert
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_non_matching_exceptions_never_open_circuit(self) -> None:
        # Arrange
        cfg = CircuitBreakerConfig(failure_threshold=2, expected_exception=ValueError)
        inner = _mock_primitive(raises=TypeError("never tracked"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act — many non-matching failures
        for _ in range(10):
            with pytest.raises(TypeError):
                await cb.execute({}, _ctx())

        # Assert — circuit never opens
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_subclass_of_expected_exception_is_caught(self) -> None:
        # Arrange — expected=Exception catches subclasses like ValueError
        cfg = CircuitBreakerConfig(failure_threshold=5, expected_exception=Exception)
        inner = _mock_primitive(raises=ValueError("subclass"))
        cb = CircuitBreakerPrimitive(inner, config=cfg)

        # Act
        with pytest.raises(ValueError):
            await cb.execute({}, _ctx())

        # Assert
        assert cb.failure_count == 1


# ---------------------------------------------------------------------------
# _should_attempt_reset edge cases
# ---------------------------------------------------------------------------


class TestShouldAttemptReset:
    def test_returns_true_when_no_failure_time(self) -> None:
        cb = CircuitBreakerPrimitive(_mock_primitive())
        cb._last_failure_time = None
        assert cb._should_attempt_reset() is True

    def test_returns_false_when_elapsed_less_than_timeout(self) -> None:
        cfg = CircuitBreakerConfig(recovery_timeout=60.0)
        cb = CircuitBreakerPrimitive(_mock_primitive(), config=cfg)

        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=1010.0,
        ):
            cb._last_failure_time = 1000.0  # only 10s elapsed, need 60s
            assert cb._should_attempt_reset() is False

    def test_returns_true_when_elapsed_exceeds_timeout(self) -> None:
        cfg = CircuitBreakerConfig(recovery_timeout=60.0)
        cb = CircuitBreakerPrimitive(_mock_primitive(), config=cfg)

        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=1070.0,
        ):
            cb._last_failure_time = 1000.0  # 70s elapsed
            assert cb._should_attempt_reset() is True

    def test_returns_true_at_exact_timeout_boundary(self) -> None:
        cfg = CircuitBreakerConfig(recovery_timeout=60.0)
        cb = CircuitBreakerPrimitive(_mock_primitive(), config=cfg)

        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=1060.0,
        ):
            cb._last_failure_time = 1000.0  # exactly 60s
            assert cb._should_attempt_reset() is True


# ---------------------------------------------------------------------------
# MockPrimitive integration (canonical pattern from the project)
# ---------------------------------------------------------------------------


class TestWithMockPrimitive:
    @pytest.mark.asyncio
    async def test_success_through_circuit_breaker(self) -> None:
        # Arrange
        mock = MockPrimitive("op", return_value={"status": "ok"})
        cb = CircuitBreakerPrimitive(mock)

        # Act
        result = await cb.execute({"input": "data"}, _ctx())

        # Assert
        assert result == {"status": "ok"}
        assert mock.call_count == 1

    @pytest.mark.asyncio
    async def test_failure_tracked_via_mock_primitive(self) -> None:
        # Arrange
        mock = MockPrimitive("op", raise_error=RuntimeError("fail"))
        cfg = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreakerPrimitive(mock, config=cfg)

        # Act
        with pytest.raises(RuntimeError):
            await cb.execute({}, _ctx())

        # Assert
        assert mock.call_count == 1
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_opens_circuit_and_stops_calling_inner(self) -> None:
        # Arrange
        mock = MockPrimitive("op", raise_error=RuntimeError("fail"))
        cfg = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreakerPrimitive(mock, config=cfg)

        # Trip circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.execute({}, _ctx())

        assert cb.state == CircuitState.OPEN
        calls_when_open = mock.call_count

        # Act — circuit is open; inner must NOT be called
        with pytest.raises(CircuitBreakerError):
            await cb.execute({}, _ctx())

        # Assert
        assert mock.call_count == calls_when_open


# ---------------------------------------------------------------------------
# Legacy: ErrorCategory and ErrorSeverity
# ---------------------------------------------------------------------------


class TestErrorEnums:
    def test_error_category_network(self) -> None:
        assert ErrorCategory.NETWORK.value == "network"

    def test_error_category_rate_limit(self) -> None:
        assert ErrorCategory.RATE_LIMIT.value == "rate_limit"

    def test_error_category_resource(self) -> None:
        assert ErrorCategory.RESOURCE.value == "resource"

    def test_error_category_transient(self) -> None:
        assert ErrorCategory.TRANSIENT.value == "transient"

    def test_error_category_permanent(self) -> None:
        assert ErrorCategory.PERMANENT.value == "permanent"

    def test_error_severity_low(self) -> None:
        assert ErrorSeverity.LOW.value == "low"

    def test_error_severity_medium(self) -> None:
        assert ErrorSeverity.MEDIUM.value == "medium"

    def test_error_severity_high(self) -> None:
        assert ErrorSeverity.HIGH.value == "high"

    def test_error_severity_critical(self) -> None:
        assert ErrorSeverity.CRITICAL.value == "critical"


# ---------------------------------------------------------------------------
# Legacy: RetryConfig
# ---------------------------------------------------------------------------


class TestRetryConfig:
    def test_defaults(self) -> None:
        cfg = RetryConfig()
        assert cfg.max_retries == 3
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 60.0
        assert cfg.exponential_base == 2.0
        assert cfg.jitter is True

    def test_negative_max_retries_raises(self) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            RetryConfig(max_retries=-1)

    def test_zero_max_retries_is_valid(self) -> None:
        assert RetryConfig(max_retries=0).max_retries == 0

    def test_non_positive_base_delay_raises(self) -> None:
        with pytest.raises(ValueError, match="base_delay"):
            RetryConfig(base_delay=0)

    def test_max_delay_less_than_base_raises(self) -> None:
        with pytest.raises(ValueError, match="max_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_exponential_base_le_one_raises(self) -> None:
        with pytest.raises(ValueError, match="exponential_base"):
            RetryConfig(exponential_base=1.0)

    def test_custom_values_stored(self) -> None:
        cfg = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
        )
        assert cfg.max_retries == 5
        assert cfg.base_delay == 0.5
        assert cfg.max_delay == 30.0
        assert cfg.exponential_base == 3.0
        assert cfg.jitter is False


# ---------------------------------------------------------------------------
# Legacy: classify_error
# ---------------------------------------------------------------------------


class TestClassifyError:
    def test_connection_error_is_network(self) -> None:
        cat, sev = classify_error(ConnectionError("refused"))
        assert cat == ErrorCategory.NETWORK
        assert sev == ErrorSeverity.MEDIUM

    def test_timeout_in_message_is_network(self) -> None:
        cat, _ = classify_error(RuntimeError("timeout occurred"))
        assert cat == ErrorCategory.NETWORK

    def test_network_in_message_is_network(self) -> None:
        cat, _ = classify_error(RuntimeError("network failure"))
        assert cat == ErrorCategory.NETWORK

    def test_rate_limit_in_message(self) -> None:
        cat, sev = classify_error(RuntimeError("rate limit exceeded"))
        assert cat == ErrorCategory.RATE_LIMIT
        assert sev == ErrorSeverity.MEDIUM

    def test_429_in_message_is_rate_limit(self) -> None:
        cat, _ = classify_error(RuntimeError("got 429 from server"))
        assert cat == ErrorCategory.RATE_LIMIT

    def test_quota_in_message_is_rate_limit(self) -> None:
        cat, _ = classify_error(RuntimeError("quota exceeded"))
        assert cat == ErrorCategory.RATE_LIMIT

    def test_too_many_requests_is_rate_limit(self) -> None:
        cat, _ = classify_error(RuntimeError("too many requests"))
        assert cat == ErrorCategory.RATE_LIMIT

    def test_memory_error_is_resource(self) -> None:
        cat, sev = classify_error(MemoryError("out of memory"))
        assert cat == ErrorCategory.RESOURCE
        assert sev == ErrorSeverity.HIGH

    def test_resource_in_message_is_resource(self) -> None:
        cat, _ = classify_error(RuntimeError("resource exhausted"))
        assert cat == ErrorCategory.RESOURCE

    def test_disk_in_message_is_resource(self) -> None:
        cat, _ = classify_error(RuntimeError("disk full"))
        assert cat == ErrorCategory.RESOURCE

    def test_temporary_unavailable_is_transient(self) -> None:
        cat, sev = classify_error(RuntimeError("service temporary unavailable"))
        assert cat == ErrorCategory.TRANSIENT
        assert sev == ErrorSeverity.MEDIUM

    def test_503_in_message_is_transient(self) -> None:
        cat, _ = classify_error(RuntimeError("got 503"))
        assert cat == ErrorCategory.TRANSIENT

    def test_502_in_message_is_transient(self) -> None:
        cat, _ = classify_error(RuntimeError("502 bad gateway"))
        assert cat == ErrorCategory.TRANSIENT

    def test_504_in_message_is_transient(self) -> None:
        cat, _ = classify_error(RuntimeError("service unavailable 504"))
        assert cat == ErrorCategory.TRANSIENT

    def test_unknown_error_is_permanent(self) -> None:
        cat, sev = classify_error(ValueError("some random failure"))
        assert cat == ErrorCategory.PERMANENT
        assert sev == ErrorSeverity.HIGH

    def test_generic_exception_is_permanent(self) -> None:
        cat, _ = classify_error(Exception("generic"))
        assert cat == ErrorCategory.PERMANENT


# ---------------------------------------------------------------------------
# Legacy: should_retry
# ---------------------------------------------------------------------------


class TestShouldRetry:
    def test_attempt_at_max_returns_false(self) -> None:
        assert should_retry(ConnectionError("net"), attempt=3, max_retries=3) is False

    def test_attempt_beyond_max_returns_false(self) -> None:
        assert should_retry(ConnectionError("net"), attempt=5, max_retries=3) is False

    def test_network_error_below_max_returns_true(self) -> None:
        assert should_retry(ConnectionError("net"), attempt=0, max_retries=3) is True

    def test_rate_limit_below_max_returns_true(self) -> None:
        assert should_retry(RuntimeError("rate limit exceeded"), attempt=1, max_retries=3) is True

    def test_transient_below_max_returns_true(self) -> None:
        assert (
            should_retry(RuntimeError("service temporary unavailable"), attempt=0, max_retries=3)
            is True
        )

    def test_permanent_error_returns_false(self) -> None:
        assert should_retry(ValueError("permanent failure"), attempt=0, max_retries=3) is False


# ---------------------------------------------------------------------------
# Legacy: calculate_delay
# ---------------------------------------------------------------------------


class TestCalculateDelay:
    def test_delay_increases_with_attempt_no_jitter(self) -> None:
        cfg = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        assert calculate_delay(0, cfg) < calculate_delay(1, cfg) < calculate_delay(2, cfg)

    def test_delay_capped_at_max_delay(self) -> None:
        cfg = RetryConfig(base_delay=1.0, max_delay=5.0, exponential_base=10.0, jitter=False)
        assert calculate_delay(10, cfg) <= 5.0

    def test_no_jitter_is_deterministic(self) -> None:
        cfg = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        assert calculate_delay(2, cfg) == calculate_delay(2, cfg)

    def test_first_attempt_equals_base_delay_no_jitter(self) -> None:
        cfg = RetryConfig(base_delay=2.0, exponential_base=2.0, jitter=False)
        assert calculate_delay(0, cfg) == 2.0

    def test_jitter_produces_varied_results(self) -> None:
        cfg = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=True)
        results = {calculate_delay(1, cfg) for _ in range(20)}
        assert len(results) > 1  # randomness produces multiple distinct values


# ---------------------------------------------------------------------------
# Legacy: CircuitBreaker (synchronous class)
# ---------------------------------------------------------------------------


class TestLegacyCircuitBreaker:
    def test_initial_state_is_closed(self) -> None:
        assert CircuitBreaker().state == "CLOSED"

    def test_initial_failure_count_is_zero(self) -> None:
        assert CircuitBreaker().failure_count == 0

    def test_successful_call_returns_result(self) -> None:
        result = CircuitBreaker().call(lambda: 42)
        assert result == 42

    def test_successful_call_resets_failure_count(self) -> None:
        cb = CircuitBreaker(failure_threshold=5)
        cb.failure_count = 3
        cb.call(lambda: "ok")
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    def test_failure_increments_count(self) -> None:
        cb = CircuitBreaker(failure_threshold=5)
        with pytest.raises(ValueError):
            cb.call(_raises(ValueError("fail")))
        assert cb.failure_count == 1

    def test_opens_after_threshold_failures(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            try:
                cb.call(_raises(RuntimeError("err")))
            except RuntimeError:
                pass
        assert cb.state == "OPEN"

    def test_open_state_raises_immediately(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        for _ in range(2):
            try:
                cb.call(_raises(RuntimeError("err")))
            except RuntimeError:
                pass

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(lambda: "should not run")

    def test_transitions_to_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0)
        for _ in range(2):
            try:
                cb.call(_raises(RuntimeError("err")))
            except RuntimeError:
                pass

        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=cb.last_failure_time + 31.0,
        ):
            result = cb.call(lambda: "recovered")

        assert result == "recovered"

    def test_expected_exception_filter(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)
        with pytest.raises(TypeError):
            cb.call(_raises(TypeError("not tracked")))
        assert cb.failure_count == 0

    def test_custom_failure_threshold_of_one(self) -> None:
        cb = CircuitBreaker(failure_threshold=1)
        try:
            cb.call(_raises(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == "OPEN"

    def test_half_open_success_closes_circuit(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5.0)
        for _ in range(2):
            try:
                cb.call(_raises(RuntimeError("fail")))
            except RuntimeError:
                pass

        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.time.time",
            return_value=cb.last_failure_time + 10.0,
        ):
            cb.call(lambda: "ok")

        assert cb.state == "CLOSED"
        assert cb.failure_count == 0


# ---------------------------------------------------------------------------
# Legacy: with_retry decorator
# ---------------------------------------------------------------------------


class TestWithRetryDecorator:
    def test_success_on_first_attempt(self) -> None:
        # Arrange
        @with_retry(RetryConfig(max_retries=3))
        def always_succeeds():
            return "success"

        # Act
        with patch("ttadev.primitives.recovery.circuit_breaker_primitive.time.sleep"):
            result = always_succeeds()

        # Assert
        assert result == "success"

    def test_succeeds_after_transient_failures(self) -> None:
        # Arrange
        calls = {"n": 0}

        @with_retry(RetryConfig(max_retries=3, base_delay=0.01, jitter=False))
        def eventually_succeeds():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("transient network")
            return "ok"

        # Act
        with patch("ttadev.primitives.recovery.circuit_breaker_primitive.time.sleep"):
            result = eventually_succeeds()

        # Assert
        assert result == "ok"
        assert calls["n"] == 3

    def test_raises_after_max_retries_exhausted(self) -> None:
        # Arrange
        @with_retry(RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        def always_fails():
            raise ConnectionError("network down")

        # Act + Assert
        with patch("ttadev.primitives.recovery.circuit_breaker_primitive.time.sleep"):
            with pytest.raises(ConnectionError, match="network down"):
                always_fails()

    def test_fallback_called_on_exhaustion(self) -> None:
        # Arrange
        def my_fallback():
            return "fallback_result"

        @with_retry(
            RetryConfig(max_retries=2, base_delay=0.01, jitter=False),
            fallback=my_fallback,
        )
        def always_fails():
            raise ConnectionError("network fail")

        # Act
        with patch("ttadev.primitives.recovery.circuit_breaker_primitive.time.sleep"):
            result = always_fails()

        # Assert
        assert result == "fallback_result"

    def test_permanent_error_stops_retrying_immediately(self) -> None:
        # Arrange — ValueError classified as PERMANENT; no retries
        calls = {"n": 0}

        @with_retry(RetryConfig(max_retries=5, base_delay=0.01, jitter=False))
        def permanent_fail():
            calls["n"] += 1
            raise ValueError("permanent")

        # Act
        with patch("ttadev.primitives.recovery.circuit_breaker_primitive.time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                permanent_fail()

        # Assert — no sleep means no retry attempt
        mock_sleep.assert_not_called()
        assert calls["n"] == 1

    def test_default_config_when_none(self) -> None:
        # Arrange
        @with_retry()
        def succeeds():
            return "done"

        # Act
        with patch("ttadev.primitives.recovery.circuit_breaker_primitive.time.sleep"):
            result = succeeds()

        # Assert
        assert result == "done"


# ---------------------------------------------------------------------------
# Legacy: with_retry_async decorator
# ---------------------------------------------------------------------------


class TestWithRetryAsyncDecorator:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        # Arrange
        @with_retry_async(RetryConfig(max_retries=3))
        async def always_succeeds():
            return "async_success"

        # Act
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            result = await always_succeeds()

        # Assert
        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_succeeds_after_transient_failures(self) -> None:
        # Arrange
        calls = {"n": 0}

        @with_retry_async(RetryConfig(max_retries=3, base_delay=0.01, jitter=False))
        async def eventually_succeeds():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("transient")
            return "async_ok"

        # Act
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            result = await eventually_succeeds()

        # Assert
        assert result == "async_ok"
        assert calls["n"] == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries_exhausted(self) -> None:
        # Arrange
        @with_retry_async(RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        async def always_fails():
            raise ConnectionError("async network down")

        # Act + Assert
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            with pytest.raises(ConnectionError, match="async network down"):
                await always_fails()

    @pytest.mark.asyncio
    async def test_async_fallback_called_on_exhaustion(self) -> None:
        # Arrange
        async def async_fallback():
            return "async_fallback"

        @with_retry_async(
            RetryConfig(max_retries=2, base_delay=0.01, jitter=False),
            fallback=async_fallback,
        )
        async def always_fails():
            raise ConnectionError("network fail")

        # Act
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            result = await always_fails()

        # Assert
        assert result == "async_fallback"

    @pytest.mark.asyncio
    async def test_permanent_error_stops_retrying(self) -> None:
        # Arrange
        calls = {"n": 0}

        @with_retry_async(RetryConfig(max_retries=5, base_delay=0.01, jitter=False))
        async def permanent_fail():
            calls["n"] += 1
            raise ValueError("permanent")

        # Act
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            with pytest.raises(ValueError):
                await permanent_fail()

        # Assert
        mock_sleep.assert_not_called()
        assert calls["n"] == 1

    @pytest.mark.asyncio
    async def test_default_config_when_none(self) -> None:
        # Arrange
        @with_retry_async()
        async def succeeds():
            return "async_done"

        # Act
        with patch(
            "ttadev.primitives.recovery.circuit_breaker_primitive.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            result = await succeeds()

        # Assert
        assert result == "async_done"
