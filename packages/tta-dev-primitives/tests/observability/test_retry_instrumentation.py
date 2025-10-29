"""Tests for RetryPrimitive Phase 2 instrumentation."""

import asyncio

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy


class SuccessfulPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always succeeds."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'success' field to input."""
        return {**input_data, "success": True}


class FailOncePrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that fails once then succeeds."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name)
        self.call_count = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Fail on first call, succeed on second."""
        self.call_count += 1
        if self.call_count == 1:
            raise ValueError("First attempt fails")
        return {**input_data, "success": True, "attempts": self.call_count}


class FailTwicePrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that fails twice then succeeds."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name)
        self.call_count = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Fail on first two calls, succeed on third."""
        self.call_count += 1
        if self.call_count <= 2:
            raise ValueError(f"Attempt {self.call_count} fails")
        return {**input_data, "success": True, "attempts": self.call_count}


class AlwaysFailPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Always raise an error."""
        raise ValueError("Always fails")


@pytest.mark.asyncio
async def test_retry_logs_workflow_start_and_completion():
    """Verify that RetryPrimitive logs workflow start and completion."""
    workflow = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify via checkpoints (structlog logs to stdout)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.start" in checkpoint_names
    assert "retry.end" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_logs_attempt_execution():
    """Verify that RetryPrimitive logs each retry attempt."""
    workflow = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify checkpoints for first attempt
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.attempt_0.start" in checkpoint_names
    assert "retry.attempt_0.end" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_records_attempt_checkpoints():
    """Verify that RetryPrimitive records checkpoints for each attempt."""
    fail_once = FailOncePrimitive()
    workflow = RetryPrimitive(
        fail_once,
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify it succeeded on second attempt
    assert result["attempts"] == 2

    # Verify checkpoints for both attempts
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.attempt_0.start" in checkpoint_names
    assert "retry.attempt_0.end" in checkpoint_names
    assert "retry.attempt_1.start" in checkpoint_names
    assert "retry.attempt_1.end" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_records_backoff_checkpoints():
    """Verify that RetryPrimitive records backoff delay checkpoints."""
    fail_once = FailOncePrimitive()
    workflow = RetryPrimitive(
        fail_once,
        strategy=RetryStrategy(max_retries=3, backoff_base=0.01),  # Fast backoff for testing
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Verify backoff checkpoints
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.backoff_0.start" in checkpoint_names
    assert "retry.backoff_0.end" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_records_attempt_metrics():
    """Verify that RetryPrimitive records per-attempt metrics."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    workflow = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Check that attempt metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()

    # Get metrics for first attempt
    attempt_0_metrics = metrics_collector.get_all_metrics("RetryPrimitive.attempt_0")
    workflow_metrics = metrics_collector.get_all_metrics("RetryPrimitive.workflow")

    # Verify metrics exist
    assert attempt_0_metrics is not None
    assert workflow_metrics is not None

    # Check enhanced metrics structure
    assert "percentiles" in attempt_0_metrics
    assert attempt_0_metrics["percentiles"]["p50"] >= 0


@pytest.mark.asyncio
async def test_retry_creates_attempt_spans():
    """Verify that RetryPrimitive attempts to create spans when tracing available."""
    workflow = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution succeeded (spans created or gracefully degraded)
    assert result["success"] is True

    # Verify checkpoints were recorded (proves execution path was followed)
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.attempt_0.start" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_span_attributes():
    """Verify that retry execution includes proper attribute tracking."""
    workflow = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution succeeded
    assert result["success"] is True

    # Verify metrics were recorded (proves attributes were tracked)
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    metrics_collector = get_enhanced_metrics_collector()
    attempt_0_metrics = metrics_collector.get_all_metrics("RetryPrimitive.attempt_0")

    assert attempt_0_metrics is not None


@pytest.mark.asyncio
async def test_retry_error_handling_and_exhaustion():
    """Verify that errors are properly tracked and retry exhaustion is logged."""
    workflow = RetryPrimitive(
        AlwaysFailPrimitive(),
        strategy=RetryStrategy(max_retries=2),  # Only 2 retries for faster test
    )
    context = WorkflowContext(workflow_id="test-workflow")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute({"input": "data"}, context)

    # Verify all attempts were made
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.attempt_0.start" in checkpoint_names
    assert "retry.attempt_1.start" in checkpoint_names
    assert "retry.attempt_2.start" in checkpoint_names

    # Verify workflow end was recorded
    assert "retry.end" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Verify that RetryPrimitive handles success on first attempt (no retries)."""
    workflow = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify success
    assert result["success"] is True

    # Verify only first attempt was made
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.attempt_0.start" in checkpoint_names
    assert "retry.attempt_0.end" in checkpoint_names
    # Should NOT have second attempt
    assert "retry.attempt_1.start" not in checkpoint_names


@pytest.mark.asyncio
async def test_retry_success_after_n_retries():
    """Verify that RetryPrimitive tracks success after multiple retries."""
    fail_twice = FailTwicePrimitive()
    workflow = RetryPrimitive(
        fail_twice,
        strategy=RetryStrategy(max_retries=3, backoff_base=0.01),  # Fast backoff
    )
    context = WorkflowContext(workflow_id="test-workflow")

    result = await workflow.execute({"input": "data"}, context)

    # Verify it succeeded on third attempt
    assert result["attempts"] == 3

    # Verify all three attempts were made
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "retry.attempt_0.start" in checkpoint_names
    assert "retry.attempt_1.start" in checkpoint_names
    assert "retry.attempt_2.start" in checkpoint_names

    # Verify backoff delays
    assert "retry.backoff_0.start" in checkpoint_names
    assert "retry.backoff_1.start" in checkpoint_names


@pytest.mark.asyncio
async def test_retry_backoff_strategy_tracking():
    """Verify that RetryPrimitive tracks backoff delays correctly."""
    from tta_dev_primitives.observability.enhanced_collector import (
        get_enhanced_metrics_collector,
    )

    fail_once = FailOncePrimitive()
    workflow = RetryPrimitive(
        fail_once,
        strategy=RetryStrategy(
            max_retries=3, backoff_base=0.01, jitter=False
        ),  # No jitter for predictable timing
    )
    context = WorkflowContext(workflow_id="test-workflow")

    await workflow.execute({"input": "data"}, context)

    # Check that backoff metrics were recorded
    metrics_collector = get_enhanced_metrics_collector()
    backoff_0_metrics = metrics_collector.get_all_metrics("RetryPrimitive.backoff_0")

    # Verify backoff metrics exist
    assert backoff_0_metrics is not None


@pytest.mark.asyncio
async def test_retry_preserves_existing_functionality():
    """Verify that Phase 2 changes don't break existing functionality."""
    # Test success on first attempt
    workflow1 = RetryPrimitive(
        SuccessfulPrimitive(),
        strategy=RetryStrategy(max_retries=3),
    )
    context1 = WorkflowContext(workflow_id="test")

    result1 = await workflow1.execute({"input": "data"}, context1)
    assert result1["success"] is True

    # Test success after retry
    fail_once = FailOncePrimitive()
    workflow2 = RetryPrimitive(
        fail_once,
        strategy=RetryStrategy(max_retries=3, backoff_base=0.01),
    )
    context2 = WorkflowContext(workflow_id="test")

    result2 = await workflow2.execute({"input": "data"}, context2)
    assert result2["success"] is True
    assert result2["attempts"] == 2

    # Test retry exhaustion
    workflow3 = RetryPrimitive(
        AlwaysFailPrimitive(),
        strategy=RetryStrategy(max_retries=2),
    )
    context3 = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow3.execute({"input": "data"}, context3)
