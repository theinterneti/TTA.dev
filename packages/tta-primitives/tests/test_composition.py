"""Tests for workflow primitive composition."""

from typing import Any

import pytest

from tta_dev_primitives import (
    ConditionalPrimitive,
    WorkflowContext,
)
from tta_dev_primitives.core.base import LambdaPrimitive
from tta_dev_primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_sequential_composition() -> None:
    """Test sequential primitive composition."""
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    mock3 = MockPrimitive("step3", return_value="result3")

    workflow = mock1 >> mock2 >> mock3

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1
    assert result == "result3"


@pytest.mark.asyncio
async def test_parallel_composition() -> None:
    """Test parallel primitive composition."""
    mock1 = MockPrimitive("branch1", return_value="result1")
    mock2 = MockPrimitive("branch2", return_value="result2")
    mock3 = MockPrimitive("branch3", return_value="result3")

    workflow = mock1 | mock2 | mock3

    context = WorkflowContext()
    results = await workflow.execute("input", context)

    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1
    assert results == ["result1", "result2", "result3"]


@pytest.mark.asyncio
async def test_conditional_composition() -> None:
    """Test conditional primitive composition."""
    then_mock = MockPrimitive("then", return_value="then_result")
    else_mock = MockPrimitive("else", return_value="else_result")

    # Test then branch
    workflow = ConditionalPrimitive(
        condition=lambda x, ctx: x > 10, then_primitive=then_mock, else_primitive=else_mock
    )

    context = WorkflowContext()
    result = await workflow.execute(15, context)

    assert then_mock.call_count == 1
    assert else_mock.call_count == 0
    assert result == "then_result"

    # Reset and test else branch
    then_mock.reset()
    else_mock.reset()

    result = await workflow.execute(5, context)

    assert then_mock.call_count == 0
    assert else_mock.call_count == 1
    assert result == "else_result"


@pytest.mark.asyncio
async def test_mixed_composition() -> None:
    """Test mixed sequential and parallel composition."""
    step1 = MockPrimitive("step1", return_value="processed")
    branch1 = MockPrimitive("branch1", return_value="b1")
    branch2 = MockPrimitive("branch2", return_value="b2")
    step2 = LambdaPrimitive(lambda x, ctx: f"final: {x}")

    workflow = step1 >> (branch1 | branch2) >> step2

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert step1.call_count == 1
    assert branch1.call_count == 1
    assert branch2.call_count == 1
    assert result == "final: ['b1', 'b2']"


@pytest.mark.asyncio
async def test_lambda_primitive() -> None:
    """Test lambda primitive."""

    def transform(x: str, ctx: WorkflowContext) -> str:
        return x.upper()

    workflow = LambdaPrimitive(transform)

    context = WorkflowContext()
    result = await workflow.execute("hello", context)

    assert result == "HELLO"


@pytest.mark.asyncio
async def test_workflow_context() -> None:
    """Test workflow context passing."""
    collected_contexts = []

    def collect_context(x: Any, ctx: WorkflowContext) -> Any:
        collected_contexts.append(ctx)
        return x

    p1 = LambdaPrimitive(collect_context)
    p2 = LambdaPrimitive(collect_context)

    workflow = p1 >> p2

    context = WorkflowContext(workflow_id="test123", session_id="session456")
    await workflow.execute("input", context)

    assert len(collected_contexts) == 2
    assert all(c.workflow_id == "test123" for c in collected_contexts)
    assert all(c.session_id == "session456" for c in collected_contexts)
