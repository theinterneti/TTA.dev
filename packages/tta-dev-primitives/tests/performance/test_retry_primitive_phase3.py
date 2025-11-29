"""Phase 3 tests for RetryPrimitive using the *real* implementation.

These tests focus on validating RetryStrategy behavior and ensuring that
RetryPrimitive delegates backoff timing to the configured strategy
without relying on long wall-clock sleeps.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.testing import MockPrimitive


def test_retry_strategy_exponential_backoff_without_jitter() -> None:
    """RetryStrategy uses exponential backoff and respects max_backoff.

    This test exercises the production RetryStrategy directly without
    executing any async retries.
    """

    strategy = RetryStrategy(backoff_base=2.0, max_backoff=60.0, jitter=False)

    # attempt is 0-indexed – first delay is base**0 == 1.0
    assert strategy.calculate_delay(0) == pytest.approx(1.0)
    assert strategy.calculate_delay(1) == pytest.approx(2.0)
    assert strategy.calculate_delay(2) == pytest.approx(4.0)

    # Large attempts are capped by max_backoff
    capped = strategy.calculate_delay(10)
    assert capped == pytest.approx(60.0)


def test_retry_strategy_jitter_within_expected_bounds() -> None:
    """When jitter is enabled, delays stay within the 0.5x–1.5x range.

    We don't assert a specific value – only that jitter is applied within
    the documented bounds.
    """

    strategy = RetryStrategy(backoff_base=2.0, max_backoff=100.0, jitter=True)

    base_delay = 2.0**2  # attempt index 2 -> 4.0 seconds before jitter
    lower_bound = 0.5 * base_delay
    upper_bound = 1.5 * base_delay

    samples: list[float] = [strategy.calculate_delay(2) for _ in range(50)]

    for value in samples:
        assert lower_bound <= value < upper_bound


@pytest.mark.asyncio
async def test_retry_primitive_uses_strategy_delays(monkeypatch: Any) -> None:
    """RetryPrimitive uses the strategy's calculate_delay for backoff.

    Instead of sleeping in real time, we monkeypatch asyncio.sleep to
    record the delays passed by RetryPrimitive.
    """

    recorded_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:  # pragma: no cover - trivial
        recorded_delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    failing = MockPrimitive(
        name="failing",
        raise_error=ValueError("boom"),
    )

    strategy = RetryStrategy(max_retries=2, backoff_base=2.0, max_backoff=60.0, jitter=False)
    workflow = RetryPrimitive(primitive=failing, strategy=strategy)
    context = WorkflowContext(workflow_id="retry-phase3")

    with pytest.raises(ValueError):
        await workflow.execute({"input": "data"}, context)

    # With max_retries=2, we expect 3 attempts and therefore 2 backoff sleeps
    expected = [strategy.calculate_delay(0), strategy.calculate_delay(1)]
    assert recorded_delays == expected


@pytest.mark.asyncio
async def test_retry_primitive_eventually_succeeds() -> None:
    """RetryPrimitive retries a failing primitive until success.

    This validates end-to-end behavior using the real implementation
    while keeping delays very small to avoid slow tests.
    """

    side_effects: list[Any] = [ValueError("fail1"), ValueError("fail2"), {"ok": True}]

    def handler(input_data: Any, context: WorkflowContext) -> Any:
        effect = side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    primitive = MockPrimitive(name="flaky", side_effect=handler)
    strategy = RetryStrategy(max_retries=3, backoff_base=0.01, max_backoff=1.0, jitter=False)
    workflow = RetryPrimitive(primitive=primitive, strategy=strategy)
    context = WorkflowContext(workflow_id="retry-phase3-success")

    result = await workflow.execute({"input": "data"}, context)

    assert result == {"ok": True}
    # Two failures + one success
    assert primitive.call_count == 3
