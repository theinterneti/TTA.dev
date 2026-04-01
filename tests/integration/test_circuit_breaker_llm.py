"""Integration test: CircuitBreakerPrimitive full lifecycle with a mock LLM provider.

Exercises the complete CLOSED → OPEN → HALF_OPEN → CLOSED state machine using
MockPrimitive so no real LLM is required.

Scenarios covered
-----------------
1. test_circuit_stays_closed_on_success
2. test_circuit_opens_after_failure_threshold
3. test_circuit_rejects_calls_when_open
4. test_circuit_moves_to_half_open_after_timeout
5. test_circuit_closes_after_success_threshold_in_half_open
6. test_circuit_reopens_on_failure_in_half_open
"""

from __future__ import annotations

import asyncio

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerPrimitive,
    CircuitState,
)
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Shared constants and helpers
# ---------------------------------------------------------------------------

_FAILURE_THRESHOLD = 3
_SUCCESS_THRESHOLD = 2
_RECOVERY_TIMEOUT = 0.05  # 50 ms — short enough to keep the suite fast


def _ctx() -> WorkflowContext:
    """Return a fresh WorkflowContext for each call."""
    return WorkflowContext(workflow_id="circuit-breaker-llm-test")


def _make_circuit(
    *,
    failure_threshold: int = _FAILURE_THRESHOLD,
    recovery_timeout: float = _RECOVERY_TIMEOUT,
    success_threshold: int = _SUCCESS_THRESHOLD,
    failing: bool = False,
) -> tuple[CircuitBreakerPrimitive, MockPrimitive]:
    """Build a CircuitBreakerPrimitive wrapping a MockPrimitive.

    Args:
        failure_threshold: Consecutive failures before opening the circuit.
        recovery_timeout: Seconds before an OPEN circuit allows a probe call.
        success_threshold: Consecutive successes in HALF_OPEN needed to close.
        failing: When True the inner mock raises RuntimeError on every call;
            when False it returns ``{"text": "Hello"}``.

    Returns:
        ``(circuit, inner_mock)`` tuple.
    """
    if failing:
        inner: MockPrimitive = MockPrimitive("llm", raise_error=RuntimeError("LLM unavailable"))
    else:
        inner = MockPrimitive("llm", return_value={"text": "Hello"})

    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
    )
    circuit = CircuitBreakerPrimitive(primitive=inner, config=config)
    return circuit, inner


async def _drive_to_open(
    circuit: CircuitBreakerPrimitive,
    failure_threshold: int = _FAILURE_THRESHOLD,
) -> None:
    """Force *circuit* into OPEN state by triggering *failure_threshold* failures.

    Pre-condition: ``circuit.primitive`` must be a failing MockPrimitive.
    Post-condition: ``circuit.state == CircuitState.OPEN``.
    """
    ctx = _ctx()
    for _ in range(failure_threshold):
        with pytest.raises(RuntimeError):
            await circuit.execute({"prompt": "test"}, ctx)
    assert circuit.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# 1. Circuit stays CLOSED on repeated successes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_stays_closed_on_success() -> None:
    """Successive successful calls keep the circuit in CLOSED state.

    Arrange: succeeding mock wrapped by circuit breaker.
    Act:     execute 5 times, collecting results.
    Assert:  state remains CLOSED; failure counter stays at 0; mock called 5×.
    """
    # Arrange
    circuit, mock = _make_circuit(failing=False)
    ctx = _ctx()

    # Act
    for _ in range(5):
        result = await circuit.execute({"prompt": "hello"}, ctx)
        assert result == {"text": "Hello"}

    # Assert
    assert circuit.state == CircuitState.CLOSED
    assert circuit.failure_count == 0
    assert mock.call_count == 5


# ---------------------------------------------------------------------------
# 2. Circuit opens after failure_threshold consecutive failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_opens_after_failure_threshold() -> None:
    """Exactly failure_threshold consecutive failures transition state to OPEN.

    Arrange: failing mock, threshold = 3.
    Act:     call 3 times; check state after each.
    Assert:  CLOSED after 1st and 2nd failure, OPEN after 3rd.
    """
    # Arrange
    circuit, mock = _make_circuit(failing=True, failure_threshold=_FAILURE_THRESHOLD)
    ctx = _ctx()

    # Act — failures 1 … (threshold-1): circuit must stay CLOSED
    for i in range(1, _FAILURE_THRESHOLD):
        with pytest.raises(RuntimeError):
            await circuit.execute({"prompt": "test"}, ctx)
        assert circuit.state == CircuitState.CLOSED, (
            f"Expected CLOSED after {i} failure(s), got {circuit.state}"
        )

    # Threshold-hitting failure
    with pytest.raises(RuntimeError):
        await circuit.execute({"prompt": "test"}, ctx)

    # Assert
    assert circuit.state == CircuitState.OPEN
    assert circuit.failure_count == _FAILURE_THRESHOLD
    assert mock.call_count == _FAILURE_THRESHOLD


# ---------------------------------------------------------------------------
# 3. Circuit rejects calls immediately when OPEN (no inner call made)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_rejects_calls_when_open() -> None:
    """A call while OPEN raises CircuitBreakerError without touching the inner mock.

    Arrange: drive circuit to OPEN, record inner mock call_count.
    Act:     attempt one more call through the circuit.
    Assert:  CircuitBreakerError raised; inner mock call_count unchanged.
    """
    # Arrange
    circuit, mock = _make_circuit(failing=True)
    await _drive_to_open(circuit)
    call_count_before = mock.call_count

    # Act
    with pytest.raises(CircuitBreakerError) as exc_info:
        await circuit.execute({"prompt": "should be rejected"}, _ctx())

    # Assert — error references OPEN state; inner mock was NOT called again
    assert "OPEN" in str(exc_info.value)
    assert exc_info.value.failure_count == _FAILURE_THRESHOLD
    assert mock.call_count == call_count_before


# ---------------------------------------------------------------------------
# 4. Circuit moves to HALF_OPEN after recovery_timeout elapses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_moves_to_half_open_after_timeout() -> None:
    """After recovery_timeout the next call transitions OPEN → HALF_OPEN and executes.

    Arrange: open circuit, swap inner mock to succeeding, sleep past timeout.
    Act:     execute one probe call (success_threshold=2, so one success is not enough to close).
    Assert:  state is HALF_OPEN; result is the recovered value; inner mock called once.
    """
    # Arrange
    circuit, _ = _make_circuit(failing=True, success_threshold=2)
    await _drive_to_open(circuit)

    recovering_mock = MockPrimitive("llm", return_value={"text": "recovered"})
    circuit.primitive = recovering_mock

    await asyncio.sleep(_RECOVERY_TIMEOUT + 0.02)

    # Act — probe; with success_threshold=2 one success leaves circuit in HALF_OPEN
    result = await circuit.execute({"prompt": "probe"}, _ctx())

    # Assert
    assert circuit.state == CircuitState.HALF_OPEN
    assert result == {"text": "recovered"}
    assert recovering_mock.call_count == 1


# ---------------------------------------------------------------------------
# 5. Circuit closes after success_threshold successes in HALF_OPEN
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_closes_after_success_threshold_in_half_open() -> None:
    """success_threshold consecutive successes in HALF_OPEN transition to CLOSED.

    Arrange: open circuit, swap to succeeding mock, sleep past timeout.
    Act:     execute success_threshold probe calls.
    Assert:  after last probe state is CLOSED; failure_count reset to 0.
    """
    # Arrange
    circuit, _ = _make_circuit(failing=True, success_threshold=_SUCCESS_THRESHOLD)
    await _drive_to_open(circuit)

    recovering_mock = MockPrimitive("llm", return_value={"text": "ok"})
    circuit.primitive = recovering_mock
    await asyncio.sleep(_RECOVERY_TIMEOUT + 0.02)

    ctx = _ctx()

    # First probe: OPEN → HALF_OPEN, success_count = 1, still HALF_OPEN
    await circuit.execute({"prompt": "probe-1"}, ctx)
    assert circuit.state == CircuitState.HALF_OPEN

    # Act — second probe: success_count = 2 >= success_threshold → CLOSED
    await circuit.execute({"prompt": "probe-2"}, ctx)

    # Assert
    assert circuit.state == CircuitState.CLOSED
    assert circuit.failure_count == 0
    assert recovering_mock.call_count == _SUCCESS_THRESHOLD


# ---------------------------------------------------------------------------
# 6. Circuit reopens on failure in HALF_OPEN
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_reopens_on_failure_in_half_open() -> None:
    """A single failure in HALF_OPEN immediately reopens the circuit.

    Arrange: open circuit, get to HALF_OPEN with one successful probe
             (success_threshold=2 so one success is not enough to close).
    Act:     swap inner mock back to failing, execute one call.
    Assert:  RuntimeError propagated; circuit state is OPEN again.
    """
    # Arrange — get to OPEN
    circuit, _ = _make_circuit(failing=True, success_threshold=2)
    await _drive_to_open(circuit)

    # One successful probe to reach HALF_OPEN
    probe_mock = MockPrimitive("llm", return_value={"text": "ok"})
    circuit.primitive = probe_mock
    await asyncio.sleep(_RECOVERY_TIMEOUT + 0.02)

    await circuit.execute({"prompt": "probe"}, _ctx())
    assert circuit.state == CircuitState.HALF_OPEN  # one success, threshold=2

    # Swap back to a failing mock (service regressed)
    circuit.primitive = MockPrimitive("llm", raise_error=RuntimeError("still broken"))

    # Act — failure in HALF_OPEN must reopen the circuit
    with pytest.raises(RuntimeError, match="still broken"):
        await circuit.execute({"prompt": "fail-in-half-open"}, _ctx())

    # Assert
    assert circuit.state == CircuitState.OPEN
