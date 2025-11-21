import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Tests that the primitive succeeds on the first attempt."""
    mock_primitive = MockPrimitive(name="mock_primitive", return_value="success")
    retry_primitive = RetryPrimitive(mock_primitive)
    context = WorkflowContext()

    result = await retry_primitive.execute({}, context)

    assert result == "success"
    assert mock_primitive.call_count == 1


@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Tests that the primitive succeeds after a few failed attempts."""
    mock_primitive = MockPrimitive(name="mock_primitive")
    side_effects = [ValueError("fail1"), ValueError("fail2"), "success"]

    def side_effect_handler(*args, **kwargs):
        effect = side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    mock_primitive.side_effect = side_effect_handler

    retry_primitive = RetryPrimitive(
        mock_primitive, strategy=RetryStrategy(max_retries=3, backoff_base=0.01)
    )
    context = WorkflowContext()

    result = await retry_primitive.execute({}, context)

    assert result == "success"
    assert mock_primitive.call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    """Tests that an exception is raised when all retries are exhausted."""
    mock_primitive = MockPrimitive(
        name="mock_primitive", raise_error=ValueError("persistent failure")
    )
    retry_primitive = RetryPrimitive(
        mock_primitive, strategy=RetryStrategy(max_retries=2, backoff_base=0.01)
    )
    context = WorkflowContext()

    with pytest.raises(ValueError, match="persistent failure"):
        await retry_primitive.execute({}, context)

    assert mock_primitive.call_count == 3


def test_retry_strategy_delay_calculation():
    """Tests the delay calculation of the RetryStrategy."""
    strategy = RetryStrategy(backoff_base=2.0, jitter=False)
    assert strategy.calculate_delay(0) == 1.0
    assert strategy.calculate_delay(1) == 2.0
    assert strategy.calculate_delay(2) == 4.0


def test_retry_strategy_max_backoff():
    """Tests that the backoff delay is capped at max_backoff."""
    strategy = RetryStrategy(backoff_base=2.0, max_backoff=3.0, jitter=False)
    assert strategy.calculate_delay(2) == 3.0


@pytest.mark.asyncio
async def test_retry_with_jitter():
    """Tests that jitter introduces randomness to the delay."""
    strategy = RetryStrategy(backoff_base=2.0, jitter=True)
    # We can't assert a specific value, but we can check it's within a range
    delay = strategy.calculate_delay(1)
    assert 1.0 <= delay <= 3.0


@pytest.mark.asyncio
async def test_retry_context_is_passed_correctly():
    """Tests that the same context object is passed to each attempt."""
    mock_primitive = MockPrimitive(name="mock_primitive")
    side_effects = [ValueError("fail"), "success"]

    def side_effect_handler(*args, **kwargs):
        effect = side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    mock_primitive.side_effect = side_effect_handler
    retry_primitive = RetryPrimitive(
        mock_primitive, strategy=RetryStrategy(max_retries=1, backoff_base=0.01)
    )
    context = WorkflowContext(workflow_id="test_workflow")

    await retry_primitive.execute({}, context)

    assert mock_primitive.call_count == 2
    assert mock_primitive.calls[0][1] is context
    assert mock_primitive.calls[1][1] is context
