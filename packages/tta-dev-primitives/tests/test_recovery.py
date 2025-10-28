"""Tests for error recovery primitives."""

import pytest

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import (
    FallbackPrimitive,
    RetryPrimitive,
    RetryStrategy,
    SagaPrimitive,
)
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_retry_success_on_second_attempt() -> None:
    """Test retry succeeds on second attempt."""
    call_count = 0

    def flaky_operation(x, ctx) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First attempt fails")
        return "success"

    from tta_dev_primitives.core.base import LambdaPrimitive

    flaky = LambdaPrimitive(flaky_operation)
    workflow = RetryPrimitive(flaky, strategy=RetryStrategy(max_retries=3, backoff_base=0.01))

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert call_count == 2
    assert result == "success"


@pytest.mark.asyncio
async def test_retry_exhaustion() -> None:
    """Test retry exhaustion raises error."""
    mock = MockPrimitive("failing", raise_error=ValueError("Always fails"))

    workflow = RetryPrimitive(mock, strategy=RetryStrategy(max_retries=2, backoff_base=0.01))

    context = WorkflowContext()

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute("input", context)

    assert mock.call_count == 3  # Initial + 2 retries


@pytest.mark.asyncio
async def test_fallback_on_failure() -> None:
    """Test fallback activates on primary failure."""
    primary = MockPrimitive("primary", raise_error=ValueError("Primary fails"))
    fallback = MockPrimitive("fallback", return_value="fallback_result")

    workflow = FallbackPrimitive(primary=primary, fallback=fallback)

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert primary.call_count == 1
    assert fallback.call_count == 1
    assert result == "fallback_result"


@pytest.mark.asyncio
async def test_fallback_not_used_on_success() -> None:
    """Test fallback is not used when primary succeeds."""
    primary = MockPrimitive("primary", return_value="primary_result")
    fallback = MockPrimitive("fallback", return_value="fallback_result")

    workflow = FallbackPrimitive(primary=primary, fallback=fallback)

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert primary.call_count == 1
    assert fallback.call_count == 0
    assert result == "primary_result"


@pytest.mark.asyncio
async def test_saga_compensation_on_failure() -> None:
    """Test saga runs compensation on failure."""
    forward = MockPrimitive("forward", raise_error=ValueError("Forward fails"))
    compensation = MockPrimitive("compensation", return_value=None)

    workflow = SagaPrimitive(forward=forward, compensation=compensation)

    context = WorkflowContext()

    with pytest.raises(ValueError, match="Forward fails"):
        await workflow.execute("input", context)

    assert forward.call_count == 1
    assert compensation.call_count == 1


@pytest.mark.asyncio
async def test_saga_no_compensation_on_success() -> None:
    """Test saga does not run compensation on success."""
    forward = MockPrimitive("forward", return_value="success")
    compensation = MockPrimitive("compensation", return_value=None)

    workflow = SagaPrimitive(forward=forward, compensation=compensation)

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert forward.call_count == 1
    assert compensation.call_count == 0
    assert result == "success"
