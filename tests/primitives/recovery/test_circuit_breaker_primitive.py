"""Unit tests for CircuitBreakerPrimitive — AAA pattern throughout."""

import asyncio
import time

import pytest

from ttadev.primitives import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery.circuit_breaker import (
    CircuitBreaker,
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    calculate_delay,
    classify_error,
    should_retry,
    with_retry,
    with_retry_async,
)
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerPrimitive,
    CircuitState,
)

# ---------------------------------------------------------------------------
# CircuitBreakerConfig
# ---------------------------------------------------------------------------


def test_circuit_breaker_config_defaults():
    # Arrange / Act
    config = CircuitBreakerConfig()

    # Assert
    assert config.failure_threshold == 5
    assert config.recovery_timeout == 60.0
    assert config.success_threshold == 2
    assert config.expected_exception is Exception


def test_circuit_breaker_config_validates_failure_threshold():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="failure_threshold"):
        CircuitBreakerConfig(failure_threshold=0)


def test_circuit_breaker_config_validates_recovery_timeout():
    with pytest.raises(ValueError, match="recovery_timeout"):
        CircuitBreakerConfig(recovery_timeout=0)


def test_circuit_breaker_config_validates_success_threshold():
    with pytest.raises(ValueError, match="success_threshold"):
        CircuitBreakerConfig(success_threshold=0)


# ---------------------------------------------------------------------------
# CircuitBreakerError
# ---------------------------------------------------------------------------


def test_circuit_breaker_error_message():
    # Arrange / Act
    err = CircuitBreakerError(failure_count=3)

    # Assert
    assert "3" in str(err)
    assert err.failure_count == 3
    assert err.last_error is None


def test_circuit_breaker_error_preserves_last_error():
    # Arrange
    cause = RuntimeError("root cause")

    # Act
    err = CircuitBreakerError(failure_count=1, last_error=cause)

    # Assert
    assert err.last_error is cause


# ---------------------------------------------------------------------------
# CircuitBreakerPrimitive — initial state
# ---------------------------------------------------------------------------


async def test_circuit_breaker_initial_state():
    # Arrange
    async def op(_inp, _ctx):
        _ = _ctx
        return _inp

    # Act
    cb = CircuitBreakerPrimitive(LambdaPrimitive(op))

    # Assert
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.success_count == 0


# ---------------------------------------------------------------------------
# CLOSED state — happy path
# ---------------------------------------------------------------------------


async def test_circuit_breaker_allows_requests_when_closed():
    # Arrange
    async def op(_inp, _ctx):
        return "ok"

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(op),
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60),
    )
    ctx = WorkflowContext()

    # Act
    result = await cb.execute("input", ctx)

    # Assert
    assert result == "ok"
    assert cb.state == CircuitState.CLOSED


async def test_circuit_breaker_passes_input_unchanged():
    # Arrange
    received = []

    async def op(inp, _ctx):
        received.append(inp)
        return inp * 2

    cb = CircuitBreakerPrimitive(LambdaPrimitive(op))
    ctx = WorkflowContext()

    # Act
    result = await cb.execute(21, ctx)

    # Assert
    assert result == 42
    assert received == [21]


async def test_success_resets_failure_count():
    # Arrange
    call_count = 0

    async def flaky(_inp, _ctx):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("transient")
        return "ok"

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(flaky),
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60),
    )
    ctx = WorkflowContext()

    # Act — one failure then one success
    with pytest.raises(RuntimeError):
        await cb.execute("x", ctx)
    assert cb.failure_count == 1

    result = await cb.execute("x", ctx)

    # Assert — failure count reset
    assert result == "ok"
    assert cb.failure_count == 0


# ---------------------------------------------------------------------------
# CLOSED -> OPEN transition
# ---------------------------------------------------------------------------


async def test_circuit_breaker_opens_after_failure_threshold():
    # Arrange
    async def always_fails(_inp, _ctx):
        raise RuntimeError("fail")

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(always_fails),
        CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60),
    )
    ctx = WorkflowContext()

    # Act — reach threshold
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.execute("input", ctx)

    # Assert — now OPEN; next call raises CircuitBreakerError
    assert cb.state == CircuitState.OPEN
    with pytest.raises(CircuitBreakerError):
        await cb.execute("input", ctx)


async def test_circuit_open_blocks_without_calling_wrapped_primitive():
    # Arrange
    call_count = 0

    async def op(_inp, _ctx):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("fail")

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(op),
        CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60),
    )
    ctx = WorkflowContext()

    # Trip the breaker
    with pytest.raises(RuntimeError):
        await cb.execute("input", ctx)
    assert cb.state == CircuitState.OPEN
    calls_after_open = call_count

    # Act — call while OPEN
    with pytest.raises(CircuitBreakerError):
        await cb.execute("input", ctx)

    # Assert — wrapped primitive not called again
    assert call_count == calls_after_open


async def test_circuit_breaker_error_carries_failure_count():
    # Arrange
    async def fails(_inp, _ctx):
        _, _ = _inp, _ctx
        raise RuntimeError("boom")

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(fails),
        CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60),
    )
    ctx = WorkflowContext()

    # Trip the breaker
    with pytest.raises(RuntimeError):
        await cb.execute("input", ctx)

    # Act
    with pytest.raises(CircuitBreakerError) as exc_info:
        await cb.execute("input", ctx)

    # Assert
    assert exc_info.value.failure_count >= 1
    assert isinstance(exc_info.value.last_error, RuntimeError)


# ---------------------------------------------------------------------------
# OPEN -> HALF_OPEN transition (recovery timeout)
# ---------------------------------------------------------------------------


async def test_circuit_breaker_transitions_to_half_open_after_recovery_timeout():
    # Arrange
    call_count = 0

    async def op(_inp, _ctx):
        _, _ = _inp, _ctx
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("first call fails")
        return "recovered"

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(op),
        CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01),
    )
    ctx = WorkflowContext()

    # Trip the breaker
    with pytest.raises(RuntimeError):
        await cb.execute("input", ctx)

    # Allow recovery timeout to pass
    await asyncio.sleep(0.05)

    # Act
    result = await cb.execute("input", ctx)

    # Assert
    assert result == "recovered"


async def test_circuit_in_half_open_closes_after_success_threshold():
    # Arrange
    call_count = 0

    async def op(_inp, _ctx):
        _, _ = _inp, _ctx
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("trip")
        return "ok"

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(op),
        CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01, success_threshold=2),
    )
    ctx = WorkflowContext()

    # Trip the breaker
    with pytest.raises(RuntimeError):
        await cb.execute("x", ctx)
    await asyncio.sleep(0.05)

    # Act — two successes in HALF_OPEN should close
    await cb.execute("x", ctx)  # success_count=1, still HALF_OPEN
    assert cb.state == CircuitState.HALF_OPEN
    await cb.execute("x", ctx)  # success_count=2 -> CLOSED

    # Assert
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


async def test_circuit_half_open_failure_reopens_circuit():
    # Arrange
    call_count = 0

    async def op(_inp, _ctx):
        _, _ = _inp, _ctx
        nonlocal call_count
        call_count += 1
        if call_count in (1, 3):
            raise RuntimeError("fail")
        return "ok"

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(op),
        CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01, success_threshold=3),
    )
    ctx = WorkflowContext()

    # Trip -> wait -> enter HALF_OPEN
    with pytest.raises(RuntimeError):
        await cb.execute("x", ctx)
    await asyncio.sleep(0.05)

    # One success in HALF_OPEN
    await cb.execute("x", ctx)
    assert cb.state == CircuitState.HALF_OPEN

    # Failure in HALF_OPEN -> reopen
    with pytest.raises(RuntimeError):
        await cb.execute("x", ctx)

    # Assert
    assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Manual reset
# ---------------------------------------------------------------------------


async def test_manual_reset_clears_state():
    # Arrange
    async def fails(_inp, _ctx):
        _, _ = _inp, _ctx
        raise RuntimeError("boom")

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(fails),
        CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60),
    )
    ctx = WorkflowContext()

    with pytest.raises(RuntimeError):
        await cb.execute("x", ctx)
    assert cb.state == CircuitState.OPEN

    # Act
    cb.reset()

    # Assert
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.success_count == 0


# ---------------------------------------------------------------------------
# expected_exception filtering
# ---------------------------------------------------------------------------


async def test_circuit_breaker_only_counts_expected_exceptions():
    # Arrange
    async def raises_value_error(_inp, _ctx):
        raise ValueError("not tracked")

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(raises_value_error),
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=60,
            expected_exception=RuntimeError,  # ValueError does NOT match
        ),
    )
    ctx = WorkflowContext()

    # Act — ValueError should propagate but NOT trip the breaker
    with pytest.raises(ValueError):
        await cb.execute("x", ctx)

    # Assert — circuit still CLOSED because ValueError wasn't expected
    assert cb.state == CircuitState.CLOSED


async def test_circuit_breaker_counts_matching_expected_exceptions():
    # Arrange
    async def fails(_inp, _ctx):
        raise RuntimeError("expected")

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(fails),
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=60,
            expected_exception=RuntimeError,
        ),
    )
    ctx = WorkflowContext()

    # Act
    with pytest.raises(RuntimeError):
        await cb.execute("x", ctx)

    # Assert
    assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# circuit_breaker.py — legacy module tests
# ---------------------------------------------------------------------------


class TestErrorClassification:
    def test_network_error_classified_correctly(self):
        err = ConnectionError("connection refused")
        category, severity = classify_error(err)
        assert category == ErrorCategory.NETWORK
        assert severity == ErrorSeverity.MEDIUM

    def test_rate_limit_error_classified_correctly(self):
        err = Exception("rate limit exceeded")
        category, severity = classify_error(err)
        assert category == ErrorCategory.RATE_LIMIT
        assert severity == ErrorSeverity.MEDIUM

    def test_resource_error_classified_correctly(self):
        err = MemoryError("out of memory")
        category, severity = classify_error(err)
        assert category == ErrorCategory.RESOURCE
        assert severity == ErrorSeverity.HIGH

    def test_transient_error_503(self):
        err = Exception("service 503 unavailable")
        category, severity = classify_error(err)
        assert category == ErrorCategory.TRANSIENT
        assert severity == ErrorSeverity.MEDIUM

    def test_permanent_error_default(self):
        err = Exception("unknown failure")
        category, severity = classify_error(err)
        assert category == ErrorCategory.PERMANENT
        assert severity == ErrorSeverity.HIGH

    def test_429_rate_limit(self):
        err = Exception("429 too many requests")
        category, severity = classify_error(err)
        assert category == ErrorCategory.RATE_LIMIT

    def test_timeout_error(self):
        err = TimeoutError("request timed out")
        category, severity = classify_error(err)
        assert category == ErrorCategory.NETWORK

    def test_quota_exceeded(self):
        err = Exception("quota exceeded")
        category, severity = classify_error(err)
        assert category == ErrorCategory.RATE_LIMIT

    def test_502_bad_gateway(self):
        err = Exception("502 bad gateway")
        category, severity = classify_error(err)
        assert category == ErrorCategory.TRANSIENT

    def test_disk_resource_error(self):
        err = OSError("no space left on device")
        category, severity = classify_error(err)
        assert category == ErrorCategory.RESOURCE


class TestShouldRetry:
    def test_network_error_retried(self):
        err = ConnectionError("connection refused")
        assert should_retry(err, attempt=0, max_retries=3) is True

    def test_permanent_error_not_retried(self):
        err = Exception("unknown failure")
        assert should_retry(err, attempt=0, max_retries=3) is False

    def test_max_retries_exceeded(self):
        err = ConnectionError("fail")
        assert should_retry(err, attempt=3, max_retries=3) is False

    def test_rate_limit_retried(self):
        err = Exception("rate limit hit")
        assert should_retry(err, attempt=0, max_retries=3) is True

    def test_transient_error_retried(self):
        err = Exception("503 service unavailable")
        assert should_retry(err, attempt=1, max_retries=3) is True

    def test_permanent_critical_not_retried(self, monkeypatch):
        # Covers line 140: PERMANENT + CRITICAL branch in should_retry
        monkeypatch.setattr(
            "ttadev.primitives.recovery.circuit_breaker.classify_error",
            lambda e: (ErrorCategory.PERMANENT, ErrorSeverity.CRITICAL),
        )
        err = Exception("critical permanent failure")
        assert should_retry(err, attempt=0, max_retries=3) is False


class TestCalculateDelay:
    def test_delay_within_bounds(self):
        config = RetryConfig(base_delay=1.0, max_delay=60.0, jitter=False)
        delay = calculate_delay(0, config)
        assert delay >= 1.0
        assert delay <= 60.0

    def test_delay_grows_exponentially(self):
        config = RetryConfig(base_delay=1.0, max_delay=1000.0, jitter=False)
        d0 = calculate_delay(0, config)
        d1 = calculate_delay(1, config)
        d2 = calculate_delay(2, config)
        assert d0 < d1 < d2

    def test_delay_capped_at_max(self):
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=False)
        delay = calculate_delay(100, config)
        assert delay <= 5.0

    def test_jitter_produces_variance(self):
        config = RetryConfig(base_delay=1.0, max_delay=60.0, jitter=True)
        delays = {calculate_delay(0, config) for _ in range(20)}
        # With jitter there should be at least 2 distinct values
        assert len(delays) >= 2


class TestRetryConfig:
    def test_invalid_max_retries(self):
        with pytest.raises(ValueError):
            RetryConfig(max_retries=-1)

    def test_invalid_base_delay(self):
        with pytest.raises(ValueError):
            RetryConfig(base_delay=0)

    def test_max_delay_less_than_base_delay(self):
        with pytest.raises(ValueError):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_exponential_base_too_low(self):
        with pytest.raises(ValueError):
            RetryConfig(exponential_base=1.0)


class TestWithRetry:
    def test_succeeds_on_first_attempt(self):
        @with_retry(RetryConfig(max_retries=3))
        def func():
            return "done"

        assert func() == "done"

    def test_uses_default_config_when_none_passed(self):
        # Covers line 198: `config = RetryConfig()` inside with_retry when config is None
        @with_retry()
        def func():
            return "ok"

        assert func() == "ok"

    def test_raises_after_all_retries_exhausted(self):
        calls = []

        @with_retry(RetryConfig(max_retries=2, base_delay=0.001))
        def func():
            calls.append(1)
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            func()
        # 1 initial + 2 retries = 3 total for retriable errors
        assert len(calls) == 3

    def test_fallback_called_after_failure(self):
        @with_retry(RetryConfig(max_retries=1, base_delay=0.001), fallback=lambda: "fallback")
        def func():
            raise ConnectionError("fail")

        result = func()
        assert result == "fallback"

    def test_permanent_error_not_retried(self):
        calls = []

        @with_retry(RetryConfig(max_retries=3, base_delay=0.001))
        def func():
            calls.append(1)
            raise ValueError("permanent unknown failure")

        with pytest.raises(ValueError):
            func()
        # Only 1 call — permanent errors don't retry
        assert len(calls) == 1


class TestWithRetryAsync:
    async def test_async_succeeds_on_first_attempt(self):
        @with_retry_async(RetryConfig(max_retries=3))
        async def func():
            return "done"

        assert await func() == "done"

    async def test_uses_default_config_when_none_passed(self):
        # Covers line 263: `config = RetryConfig()` inside with_retry_async when config is None
        @with_retry_async()
        async def func():
            return "ok"

        assert await func() == "ok"

    async def test_async_raises_after_all_retries(self):
        calls = []

        @with_retry_async(RetryConfig(max_retries=2, base_delay=0.001))
        async def func():
            calls.append(1)
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            await func()
        assert len(calls) == 3

    async def test_async_fallback(self):
        async def fallback():
            return "async-fallback"

        @with_retry_async(RetryConfig(max_retries=1, base_delay=0.001), fallback=fallback)
        async def func():
            raise ConnectionError("fail")

        result = await func()
        assert result == "async-fallback"

    async def test_async_permanent_not_retried(self):
        calls = []

        @with_retry_async(RetryConfig(max_retries=3, base_delay=0.001))
        async def func():
            calls.append(1)
            raise ValueError("permanent failure")

        with pytest.raises(ValueError):
            await func()
        assert len(calls) == 1


async def test_should_attempt_reset_when_no_failure_time_recorded():
    # Arrange — primitive that always succeeds so _last_failure_time stays None
    async def op(_inp, _ctx):
        return "ok"

    cb = CircuitBreakerPrimitive(
        LambdaPrimitive(op),
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60),
    )
    # _last_failure_time is None at construction
    assert cb._last_failure_time is None

    # Act — _should_attempt_reset returns True when no failure time
    assert cb._should_attempt_reset() is True

    # Verify execution still works fine
    ctx = WorkflowContext()
    result = await cb.execute("x", ctx)
    assert result == "ok"


class TestLegacyCircuitBreaker:
    """Tests for the synchronous CircuitBreaker in circuit_breaker.py."""

    def test_closed_passes_through(self):
        cb = CircuitBreaker(failure_threshold=3)
        result = cb.call(lambda: "ok")
        assert result == "ok"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        assert cb.state == "OPEN"
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(lambda: "x")

    def test_success_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        time.sleep(0.02)
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == "CLOSED"

    def test_half_open_transition(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        time.sleep(0.02)
        assert cb._should_attempt_reset() is True

    def test_should_attempt_reset_with_no_failure_time(self):
        cb = CircuitBreaker()
        assert cb._should_attempt_reset() is True

    def test_expected_exception_filters(self):
        cb = CircuitBreaker(failure_threshold=1, expected_exception=ValueError)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("not caught")))

        # RuntimeError is not the expected_exception, so circuit stays CLOSED
        assert cb.state == "CLOSED"
