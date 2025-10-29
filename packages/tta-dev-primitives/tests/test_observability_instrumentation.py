"""Tests for observability instrumentation in primitives."""

from typing import Any

import pytest

from tta_dev_primitives import (
    ConditionalPrimitive,
    FallbackPrimitive,
    RetryPrimitive,
    SagaPrimitive,
    SwitchPrimitive,
    WorkflowContext,
)
from tta_dev_primitives.core.base import LambdaPrimitive
from tta_dev_primitives.recovery.retry import RetryStrategy
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_workflow_context_checkpoints() -> None:
    """Test checkpoint recording in WorkflowContext."""
    context = WorkflowContext(workflow_id="test")
    
    # Record checkpoints
    context.checkpoint("start")
    context.checkpoint("middle")
    context.checkpoint("end")
    
    # Verify checkpoints were recorded
    assert len(context.checkpoints) == 3
    assert context.checkpoints[0][0] == "start"
    assert context.checkpoints[1][0] == "middle"
    assert context.checkpoints[2][0] == "end"
    
    # Verify timestamps are increasing
    assert context.checkpoints[0][1] <= context.checkpoints[1][1]
    assert context.checkpoints[1][1] <= context.checkpoints[2][1]


@pytest.mark.asyncio
async def test_workflow_context_elapsed_ms() -> None:
    """Test elapsed time calculation."""
    import time
    
    context = WorkflowContext()
    time.sleep(0.01)  # Sleep 10ms
    
    elapsed = context.elapsed_ms()
    assert elapsed >= 10.0  # At least 10ms elapsed


@pytest.mark.asyncio
async def test_workflow_context_create_child() -> None:
    """Test child context creation inherits trace info."""
    parent = WorkflowContext(
        workflow_id="parent-wf",
        session_id="session-123",
        trace_id="abc123",
        span_id="def456",
        correlation_id="corr-789",
    )
    
    child = parent.create_child_context()
    
    # Verify inherited fields
    assert child.workflow_id == parent.workflow_id
    assert child.session_id == parent.session_id
    assert child.trace_id == parent.trace_id
    assert child.correlation_id == parent.correlation_id
    
    # Verify parent-child relationship
    assert child.parent_span_id == parent.span_id
    assert child.causation_id == parent.correlation_id


@pytest.mark.asyncio
async def test_workflow_context_to_otel_context() -> None:
    """Test conversion to OpenTelemetry context attributes."""
    context = WorkflowContext(
        workflow_id="wf-123",
        session_id="sess-456",
        player_id="player-789",
        correlation_id="corr-abc",
    )
    
    otel_attrs = context.to_otel_context()
    
    assert otel_attrs["workflow.id"] == "wf-123"
    assert otel_attrs["workflow.session_id"] == "sess-456"
    assert otel_attrs["workflow.player_id"] == "player-789"
    assert otel_attrs["workflow.correlation_id"] == "corr-abc"
    assert "workflow.elapsed_ms" in otel_attrs


@pytest.mark.asyncio
async def test_sequential_primitive_checkpoints() -> None:
    """Test that SequentialPrimitive records checkpoints."""
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    mock3 = MockPrimitive("step3", return_value="result3")
    
    workflow = mock1 >> mock2 >> mock3
    context = WorkflowContext()
    
    result = await workflow.execute("input", context)
    
    # Verify checkpoints were recorded
    assert len(context.checkpoints) >= 4  # sequential_start + 3 steps + sequential_end
    
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "sequential_start" in checkpoint_names
    assert "sequential_end" in checkpoint_names
    
    # Verify result
    assert result == "result3"


@pytest.mark.asyncio
async def test_parallel_primitive_child_contexts() -> None:
    """Test that ParallelPrimitive creates child contexts."""
    contexts_seen: list[WorkflowContext] = []
    
    def capture_context(data: Any, ctx: WorkflowContext) -> Any:
        contexts_seen.append(ctx)
        return data
    
    branch1 = LambdaPrimitive(capture_context)
    branch2 = LambdaPrimitive(capture_context)
    branch3 = LambdaPrimitive(capture_context)
    
    workflow = branch1 | branch2 | branch3
    
    parent_context = WorkflowContext(
        workflow_id="parent",
        correlation_id="corr-123",
    )
    
    await workflow.execute("input", parent_context)
    
    # Verify child contexts were created
    assert len(contexts_seen) == 3
    
    # All children should have same correlation_id as parent
    for child_ctx in contexts_seen:
        assert child_ctx.correlation_id == parent_context.correlation_id
        assert child_ctx.workflow_id == parent_context.workflow_id
    
    # Verify checkpoints were recorded in parent
    checkpoint_names = [name for name, _ in parent_context.checkpoints]
    assert "parallel_start" in checkpoint_names
    assert "parallel_end" in checkpoint_names


@pytest.mark.asyncio
async def test_conditional_primitive_branch_tracking() -> None:
    """Test that ConditionalPrimitive tracks branch decisions."""
    then_mock = MockPrimitive("then", return_value="then_result")
    else_mock = MockPrimitive("else", return_value="else_result")
    
    workflow = ConditionalPrimitive(
        condition=lambda x, ctx: x > 10,
        then_primitive=then_mock,
        else_primitive=else_mock,
    )
    
    # Test then branch
    context1 = WorkflowContext()
    result1 = await workflow.execute(15, context1)
    
    assert result1 == "then_result"
    assert context1.state.get("last_conditional_branch") == "then"
    
    # Test else branch
    context2 = WorkflowContext()
    result2 = await workflow.execute(5, context2)
    
    assert result2 == "else_result"
    assert context2.state.get("last_conditional_branch") == "else"


@pytest.mark.asyncio
async def test_switch_primitive_case_tracking() -> None:
    """Test that SwitchPrimitive tracks case selection."""
    case_a = MockPrimitive("case_a", return_value="result_a")
    case_b = MockPrimitive("case_b", return_value="result_b")
    default_case = MockPrimitive("default", return_value="result_default")
    
    workflow = SwitchPrimitive(
        selector=lambda x, ctx: x.get("case", ""),
        cases={"a": case_a, "b": case_b},
        default=default_case,
    )
    
    # Test case A
    context1 = WorkflowContext()
    result1 = await workflow.execute({"case": "a"}, context1)
    
    assert result1 == "result_a"
    assert context1.state.get("last_switch_case") == "a"
    
    # Test case B
    context2 = WorkflowContext()
    result2 = await workflow.execute({"case": "b"}, context2)
    
    assert result2 == "result_b"
    assert context2.state.get("last_switch_case") == "b"
    
    # Test default case
    context3 = WorkflowContext()
    result3 = await workflow.execute({"case": "unknown"}, context3)
    
    assert result3 == "result_default"
    assert context3.state.get("last_switch_case") == "unknown"


@pytest.mark.asyncio
async def test_retry_primitive_attempt_tracking() -> None:
    """Test that RetryPrimitive tracks retry attempts."""
    call_count = 0
    
    async def flaky_operation(data: Any, ctx: WorkflowContext) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    primitive = LambdaPrimitive(flaky_operation)
    retry_workflow = RetryPrimitive(
        primitive,
        strategy=RetryStrategy(max_retries=3, backoff_base=0.01),
    )
    
    context = WorkflowContext()
    result = await retry_workflow.execute("input", context)
    
    assert result == "success"
    assert call_count == 3  # Failed twice, succeeded on third attempt


@pytest.mark.asyncio
async def test_fallback_primitive_tracking() -> None:
    """Test that FallbackPrimitive tracks fallback triggers."""
    primary_fail = MockPrimitive("primary", side_effect=ValueError("Primary failed"))
    fallback_success = MockPrimitive("fallback", return_value="fallback_result")
    
    workflow = FallbackPrimitive(primary=primary_fail, fallback=fallback_success)
    
    context = WorkflowContext()
    result = await workflow.execute("input", context)
    
    assert result == "fallback_result"
    assert primary_fail.call_count == 1
    assert fallback_success.call_count == 1


@pytest.mark.asyncio
async def test_saga_primitive_compensation_tracking() -> None:
    """Test that SagaPrimitive tracks compensation execution."""
    forward_fail = MockPrimitive("forward", side_effect=ValueError("Forward failed"))
    compensation = MockPrimitive("compensation", return_value=None)
    
    workflow = SagaPrimitive(forward=forward_fail, compensation=compensation)
    
    context = WorkflowContext()
    
    with pytest.raises(ValueError, match="Forward failed"):
        await workflow.execute("input", context)
    
    # Verify compensation was executed
    assert forward_fail.call_count == 1
    assert compensation.call_count == 1


@pytest.mark.asyncio
async def test_complex_workflow_instrumentation() -> None:
    """Test instrumentation in a complex workflow combining multiple primitives."""
    # Build a complex workflow: sequential -> parallel -> conditional
    step1 = MockPrimitive("validate", return_value={"validated": True, "value": 15})
    
    branch1 = MockPrimitive("analyze_a", return_value="analysis_a")
    branch2 = MockPrimitive("analyze_b", return_value="analysis_b")
    
    then_branch = MockPrimitive("high_value", return_value="high_value_result")
    else_branch = MockPrimitive("low_value", return_value="low_value_result")
    
    conditional = ConditionalPrimitive(
        condition=lambda x, ctx: isinstance(x, list) and len(x) == 2,
        then_primitive=then_branch,
        else_primitive=else_branch,
    )
    
    # step1 >> (branch1 | branch2) >> conditional
    workflow = step1 >> (branch1 | branch2) >> conditional
    
    context = WorkflowContext(workflow_id="complex-workflow")
    result = await workflow.execute("input", context)
    
    # Verify result
    assert result == "high_value_result"
    
    # Verify all primitives were called
    assert step1.call_count == 1
    assert branch1.call_count == 1
    assert branch2.call_count == 1
    assert then_branch.call_count == 1
    assert else_branch.call_count == 0
    
    # Verify checkpoints were recorded
    assert len(context.checkpoints) > 0
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "sequential_start" in checkpoint_names
    assert "parallel_start" in checkpoint_names


@pytest.mark.asyncio
async def test_instrumentation_with_errors() -> None:
    """Test that instrumentation works correctly when primitives fail."""
    failing_primitive = MockPrimitive("fail", side_effect=RuntimeError("Expected failure"))
    success_primitive = MockPrimitive("success", return_value="success")
    
    workflow = failing_primitive >> success_primitive
    
    context = WorkflowContext()
    
    with pytest.raises(RuntimeError, match="Expected failure"):
        await workflow.execute("input", context)
    
    # Verify checkpoints were still recorded up to the failure
    assert len(context.checkpoints) >= 1
    checkpoint_names = [name for name, _ in context.checkpoints]
    assert "sequential_start" in checkpoint_names
    
    # Second primitive should not have been called
    assert failing_primitive.call_count == 1
    assert success_primitive.call_count == 0
