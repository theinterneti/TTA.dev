"""Phase 4 tests for RetryPrimitive focusing on context and checkpoints.

These tests exercise the real RetryPrimitive implementation and
WorkflowContext, with an emphasis on how retries are recorded in
checkpoints and how the same context instance is propagated across
attempts.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_retry_propagates_same_context_across_attempts() -> None:
    """The same WorkflowContext instance is passed for each retry attempt."""

    side_effects: list[Any] = [ValueError("fail"), {"value": 42}]

    def handler(input_data: Any, context: WorkflowContext) -> Any:
        effect = side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    primitive = MockPrimitive(name="flaky", side_effect=handler)
    workflow = RetryPrimitive(
        primitive=primitive,
        strategy=RetryStrategy(max_retries=1, backoff_base=0.01, jitter=False),
    )
    context = WorkflowContext(workflow_id="retry-phase4-context")

    result = await workflow.execute({"input": "data"}, context)

    assert result == {"value": 42}
    assert primitive.call_count == 2
    # Both calls should have received the exact same context object
    assert all(call_ctx is context for _, call_ctx in primitive.calls)


@pytest.mark.asyncio
async def test_retry_records_backoff_checkpoints(monkeypatch: Any) -> None:
    """Backoff periods are recorded as checkpoints in the WorkflowContext."""

    recorded_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:  # pragma: no cover - trivial
        recorded_delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    primitive = MockPrimitive(name="always-fail", raise_error=RuntimeError("boom"))
    strategy = RetryStrategy(max_retries=1, backoff_base=2.0, max_backoff=60.0, jitter=False)
    workflow = RetryPrimitive(primitive=primitive, strategy=strategy)
    context = WorkflowContext(workflow_id="retry-phase4-backoff")

    with pytest.raises(RuntimeError):
        await workflow.execute({"input": "data"}, context)

    # With max_retries=1 we expect a single backoff between two attempts
    assert recorded_delays == [strategy.calculate_delay(0)]

    checkpoint_names = [name for name, _ in context.checkpoints]
    # We should see both attempt and backoff checkpoints recorded
    assert "retry.attempt_0.start" in checkpoint_names
    assert "retry.attempt_0.end" in checkpoint_names
    assert "retry.backoff_0.start" in checkpoint_names
    assert "retry.backoff_0.end" in checkpoint_names
