"""Tests for primitive instrumentation and observability."""

import pytest

from tta_dev_primitives import (
    ConditionalPrimitive,
    FallbackPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    SequentialPrimitive,
    SwitchPrimitive,
    WorkflowContext,
)
from tta_dev_primitives.recovery.compensation import SagaPrimitive
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_workflow_context_checkpoints() -> None:
    """Test WorkflowContext checkpoint tracking."""
    context = WorkflowContext(workflow_id="test")

    # Record checkpoints
    context.checkpoint("step1")
    context.checkpoint("step2")
    context.checkpoint("step3")

    # Verify checkpoints recorded
    assert len(context.checkpoints) == 3
    assert context.checkpoints[0][0] == "step1"
    assert context.checkpoints[1][0] == "step2"
    assert context.checkpoints[2][0] == "step3"

    # Verify elapsed_ms works
    elapsed = context.elapsed_ms()
    assert elapsed >= 0


@pytest.mark.asyncio
async def test_workflow_context_child_creation() -> None:
    """Test WorkflowContext child context creation."""
    parent = WorkflowContext(
        workflow_id="parent",
        session_id="session123",
        trace_id="abc123",
        span_id="def456",
        correlation_id="corr789",
    )

    parent.metadata["key"] = "value"
    parent.state["data"] = "state"
    parent.baggage["baggage_key"] = "baggage_value"
    parent.tags["tag_key"] = "tag_value"

    child = parent.create_child_context()

    # Verify inheritance
    assert child.workflow_id == parent.workflow_id
    assert child.session_id == parent.session_id
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id  # Parent's span becomes parent_span_id
    assert child.correlation_id == parent.correlation_id
    assert child.causation_id == parent.correlation_id

    # Verify metadata/state copied
    assert child.metadata == parent.metadata
    assert child.state == parent.state
    assert child.baggage == parent.baggage
    assert child.tags == parent.tags


@pytest.mark.asyncio
async def test_sequential_instrumentation() -> None:
    """Test SequentialPrimitive instrumentation."""
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    mock3 = MockPrimitive("step3", return_value="result3")

    workflow = SequentialPrimitive([mock1, mock2, mock3])
    context = WorkflowContext(workflow_id="seq-test", correlation_id="corr-123")

    result = await workflow.execute("input", context)

    # Verify execution
    assert result == "result3"
    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1

    # Verify checkpoints recorded
    assert len(context.checkpoints) >= 5  # start + 3 steps + end
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "sequential_start" in checkpoint_names
    assert "sequential_end" in checkpoint_names
    assert "step_0_MockPrimitive" in checkpoint_names
    assert "step_1_MockPrimitive" in checkpoint_names
    assert "step_2_MockPrimitive" in checkpoint_names


@pytest.mark.asyncio
async def test_parallel_instrumentation() -> None:
    """Test ParallelPrimitive instrumentation with child contexts."""
    mock1 = MockPrimitive("branch1", return_value="result1")
    mock2 = MockPrimitive("branch2", return_value="result2")
    mock3 = MockPrimitive("branch3", return_value="result3")

    workflow = ParallelPrimitive([mock1, mock2, mock3])
    context = WorkflowContext(
        workflow_id="par-test",
        correlation_id="corr-456",
        trace_id="trace123",
        span_id="span456",
    )

    results = await workflow.execute("input", context)

    # Verify execution
    assert results == ["result1", "result2", "result3"]
    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1

    # Verify checkpoints recorded
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "parallel_start" in checkpoint_names
    assert "parallel_end" in checkpoint_names

    # Verify child contexts were used (each mock should receive a child context)
    # The child contexts should have the same correlation_id but different span hierarchy
    assert mock1.last_context.correlation_id == context.correlation_id
    assert mock2.last_context.correlation_id == context.correlation_id
    assert mock3.last_context.correlation_id == context.correlation_id


@pytest.mark.asyncio
async def test_parallel_exception_handling() -> None:
    """Test ParallelPrimitive exception handling and logging."""
    mock1 = MockPrimitive("branch1", return_value="result1")
    mock2 = MockPrimitive("branch2", side_effect=ValueError("Test error"))
    mock3 = MockPrimitive("branch3", return_value="result3")

    workflow = ParallelPrimitive([mock1, mock2, mock3])
    context = WorkflowContext(workflow_id="par-error-test")

    # Should raise the first exception
    with pytest.raises(ValueError, match="Test error"):
        await workflow.execute("input", context)


@pytest.mark.asyncio
async def test_conditional_instrumentation() -> None:
    """Test ConditionalPrimitive instrumentation."""
    then_mock = MockPrimitive("then", return_value="then_result")
    else_mock = MockPrimitive("else", return_value="else_result")

    workflow = ConditionalPrimitive(
        condition=lambda x, ctx: x > 10,
        then_primitive=then_mock,
        else_primitive=else_mock,
    )

    # Test then branch
    context = WorkflowContext(workflow_id="cond-test")
    result = await workflow.execute(15, context)

    assert result == "then_result"
    assert then_mock.call_count == 1
    assert else_mock.call_count == 0

    # Verify decision tracked in context
    assert "conditional_decisions" in context.state
    assert len(context.state["conditional_decisions"]) == 1
    assert context.state["conditional_decisions"][0]["branch"] == "then"
    assert context.state["conditional_decisions"][0]["result"] is True

    # Test else branch
    then_mock.reset()
    else_mock.reset()
    context2 = WorkflowContext(workflow_id="cond-test2")
    result = await workflow.execute(5, context2)

    assert result == "else_result"
    assert then_mock.call_count == 0
    assert else_mock.call_count == 1

    # Verify decision tracked
    assert "conditional_decisions" in context2.state
    assert context2.state["conditional_decisions"][0]["branch"] == "else"
    assert context2.state["conditional_decisions"][0]["result"] is False


@pytest.mark.asyncio
async def test_conditional_passthrough() -> None:
    """Test ConditionalPrimitive passthrough when no else branch."""
    then_mock = MockPrimitive("then", return_value="then_result")

    workflow = ConditionalPrimitive(
        condition=lambda x, ctx: x > 10,
        then_primitive=then_mock,
        else_primitive=None,
    )

    # Test passthrough (condition false, no else branch)
    context = WorkflowContext(workflow_id="cond-pass-test")
    result = await workflow.execute(5, context)

    assert result == 5  # Input passed through
    assert then_mock.call_count == 0


@pytest.mark.asyncio
async def test_switch_instrumentation() -> None:
    """Test SwitchPrimitive instrumentation."""
    case1 = MockPrimitive("case1", return_value="case1_result")
    case2 = MockPrimitive("case2", return_value="case2_result")
    default = MockPrimitive("default", return_value="default_result")

    workflow = SwitchPrimitive(
        selector=lambda x, ctx: x.get("type"),
        cases={"type1": case1, "type2": case2},
        default=default,
    )

    # Test case1
    context = WorkflowContext(workflow_id="switch-test")
    result = await workflow.execute({"type": "type1"}, context)

    assert result == "case1_result"
    assert case1.call_count == 1
    assert case2.call_count == 0
    assert default.call_count == 0

    # Verify selection tracked
    assert "switch_selections" in context.state
    assert len(context.state["switch_selections"]) == 1
    assert context.state["switch_selections"][0]["case_key"] == "type1"
    assert context.state["switch_selections"][0]["matched"] is True
    assert context.state["switch_selections"][0]["used_default"] is False

    # Test default case
    case1.reset()
    context2 = WorkflowContext(workflow_id="switch-test2")
    result = await workflow.execute({"type": "unknown"}, context2)

    assert result == "default_result"
    assert default.call_count == 1

    # Verify default selection tracked
    assert context2.state["switch_selections"][0]["case_key"] == "unknown"
    assert context2.state["switch_selections"][0]["matched"] is False
    assert context2.state["switch_selections"][0]["used_default"] is True


@pytest.mark.asyncio
async def test_retry_instrumentation() -> None:
    """Test RetryPrimitive enhanced instrumentation."""
    # Mock that fails twice then succeeds
    call_count = [0]

    async def flaky_op(data, ctx):
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError(f"Attempt {call_count[0]} failed")
        return "success"

    flaky_mock = MockPrimitive("flaky", side_effect=flaky_op)

    from tta_dev_primitives.recovery.retry import RetryStrategy

    workflow = RetryPrimitive(flaky_mock, strategy=RetryStrategy(max_retries=3))

    context = WorkflowContext(workflow_id="retry-test")
    result = await workflow.execute("input", context)

    assert result == "success"
    assert call_count[0] == 3  # Failed twice, succeeded on third

    # Verify retry statistics tracked
    assert "retry_statistics" in context.state
    assert len(context.state["retry_statistics"]) == 1
    assert context.state["retry_statistics"][0]["attempts"] == 3
    assert context.state["retry_statistics"][0]["success"] is True


@pytest.mark.asyncio
async def test_retry_exhausted() -> None:
    """Test RetryPrimitive when retries exhausted."""

    async def always_fails(data, ctx):
        raise ValueError("Always fails")

    failing_mock = MockPrimitive("failing", side_effect=always_fails)

    from tta_dev_primitives.recovery.retry import RetryStrategy

    workflow = RetryPrimitive(failing_mock, strategy=RetryStrategy(max_retries=2))

    context = WorkflowContext(workflow_id="retry-fail-test")

    with pytest.raises(ValueError, match="Always fails"):
        await workflow.execute("input", context)

    # Verify failure statistics tracked
    assert "retry_statistics" in context.state
    assert context.state["retry_statistics"][0]["success"] is False
    assert context.state["retry_statistics"][0]["error_type"] == "ValueError"


@pytest.mark.asyncio
async def test_fallback_instrumentation() -> None:
    """Test FallbackPrimitive enhanced instrumentation."""
    primary = MockPrimitive("primary", side_effect=ValueError("Primary failed"))
    fallback = MockPrimitive("fallback", return_value="fallback_result")

    workflow = FallbackPrimitive(primary=primary, fallback=fallback)

    context = WorkflowContext(workflow_id="fallback-test")
    result = await workflow.execute("input", context)

    assert result == "fallback_result"
    assert primary.call_count == 1
    assert fallback.call_count == 1

    # Verify fallback statistics tracked
    assert "fallback_statistics" in context.state
    assert len(context.state["fallback_statistics"]) == 1
    assert context.state["fallback_statistics"][0]["used_fallback"] is True
    assert context.state["fallback_statistics"][0]["success"] is True
    assert context.state["fallback_statistics"][0]["primary_error_type"] == "ValueError"


@pytest.mark.asyncio
async def test_fallback_primary_success() -> None:
    """Test FallbackPrimitive when primary succeeds."""
    primary = MockPrimitive("primary", return_value="primary_result")
    fallback = MockPrimitive("fallback", return_value="fallback_result")

    workflow = FallbackPrimitive(primary=primary, fallback=fallback)

    context = WorkflowContext(workflow_id="fallback-success-test")
    result = await workflow.execute("input", context)

    assert result == "primary_result"
    assert primary.call_count == 1
    assert fallback.call_count == 0

    # Verify statistics tracked
    assert "fallback_statistics" in context.state
    assert context.state["fallback_statistics"][0]["used_fallback"] is False
    assert context.state["fallback_statistics"][0]["success"] is True


@pytest.mark.asyncio
async def test_saga_instrumentation() -> None:
    """Test SagaPrimitive enhanced instrumentation."""
    forward = MockPrimitive("forward", side_effect=ValueError("Forward failed"))
    compensation = MockPrimitive("compensation", return_value="compensated")

    workflow = SagaPrimitive(forward=forward, compensation=compensation)

    context = WorkflowContext(workflow_id="saga-test")

    with pytest.raises(ValueError, match="Forward failed"):
        await workflow.execute("input", context)

    # Verify compensation executed
    assert forward.call_count == 1
    assert compensation.call_count == 1

    # Verify saga statistics tracked
    assert "saga_statistics" in context.state
    assert len(context.state["saga_statistics"]) == 1
    assert context.state["saga_statistics"][0]["compensated"] is True
    assert context.state["saga_statistics"][0]["compensation_success"] is True
    assert context.state["saga_statistics"][0]["forward_error_type"] == "ValueError"


@pytest.mark.asyncio
async def test_saga_forward_success() -> None:
    """Test SagaPrimitive when forward succeeds."""
    forward = MockPrimitive("forward", return_value="forward_result")
    compensation = MockPrimitive("compensation", return_value="compensated")

    workflow = SagaPrimitive(forward=forward, compensation=compensation)

    context = WorkflowContext(workflow_id="saga-success-test")
    result = await workflow.execute("input", context)

    assert result == "forward_result"
    assert forward.call_count == 1
    assert compensation.call_count == 0

    # Verify statistics tracked
    assert "saga_statistics" in context.state
    assert context.state["saga_statistics"][0]["compensated"] is False
    assert context.state["saga_statistics"][0]["success"] is True


@pytest.mark.asyncio
async def test_complex_workflow_instrumentation() -> None:
    """Test instrumentation in complex workflow with multiple primitive types."""
    # Build a complex workflow: sequential -> parallel -> conditional
    step1 = MockPrimitive("validate", return_value={"valid": True, "score": 15})

    branch1 = MockPrimitive("branch1", return_value="b1_result")
    branch2 = MockPrimitive("branch2", return_value="b2_result")
    parallel = ParallelPrimitive([branch1, branch2])

    then_mock = MockPrimitive("high_score", return_value="high_score_result")
    else_mock = MockPrimitive("low_score", return_value="low_score_result")
    conditional = ConditionalPrimitive(
        condition=lambda x, ctx: x[0].get("score", 0) > 10,
        then_primitive=then_mock,
        else_primitive=else_mock,
    )

    workflow = step1 >> parallel >> conditional

    context = WorkflowContext(workflow_id="complex-test", correlation_id="corr-complex")
    result = await workflow.execute("input", context)

    # Verify execution
    assert result == "high_score_result"

    # Verify checkpoints from sequential primitive
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "sequential_start" in checkpoint_names
    assert "sequential_end" in checkpoint_names
    assert "parallel_start" in checkpoint_names
    assert "parallel_end" in checkpoint_names

    # Verify conditional decision tracked
    assert "conditional_decisions" in context.state
    assert context.state["conditional_decisions"][0]["branch"] == "then"

    # Verify correlation_id propagated
    assert context.correlation_id == "corr-complex"
