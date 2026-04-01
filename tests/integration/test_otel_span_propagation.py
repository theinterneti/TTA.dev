"""Integration tests: OTel span context propagation across primitive handoffs.

Verifies that WorkflowContext correctly propagates trace/span IDs through
Sequential and Parallel primitive composition.

Covers
------
1. test_workflow_context_child_has_parent_span_id
2. test_nested_children_form_correct_chain
3. test_sequential_primitive_creates_child_contexts
4. test_to_otel_context_includes_span_ids
5. test_parallel_primitive_creates_child_contexts
"""

from __future__ import annotations

import asyncio
from typing import Any

from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext
from ttadev.primitives.core.parallel import ParallelPrimitive
from ttadev.primitives.core.sequential import SequentialPrimitive

_KNOWN_SPAN_ID = "aabbccdd11223344"
_KNOWN_TRACE_ID = "0102030405060708090a0b0c0d0e0f10"


def _root_ctx(workflow_id: str = "test-workflow") -> WorkflowContext:
    return WorkflowContext(
        workflow_id=workflow_id,
        trace_id=_KNOWN_TRACE_ID,
        span_id=_KNOWN_SPAN_ID,
    )


# ---------------------------------------------------------------------------
# 1. Child context has correct parent_span_id
# ---------------------------------------------------------------------------


async def test_workflow_context_child_has_parent_span_id() -> None:
    """create_child_context() must set child.parent_span_id == root.span_id.

    Arrange: root context with a known span_id.
    Act:     call create_child_context().
    Assert:  child.parent_span_id equals root.span_id.
    """
    root = _root_ctx("root-workflow")

    child = root.create_child_context()

    assert child.parent_span_id == root.span_id
    assert child.parent_span_id == _KNOWN_SPAN_ID


# ---------------------------------------------------------------------------
# 2. Nested children form correct parent chain
# ---------------------------------------------------------------------------


async def test_nested_children_form_correct_chain() -> None:
    """root → child → grandchild must link parent_span_ids in the correct order.

    Arrange: root with span_id; child derived from root (given its own span_id);
             grandchild derived from child.
    Act:     inspect grandchild.parent_span_id.
    Assert:  grandchild.parent_span_id == child.span_id (not root.span_id).
    """
    root = WorkflowContext(workflow_id="root", span_id="root-span-0001")
    child = root.create_child_context().model_copy(
        update={"workflow_id": "child", "span_id": "child-span-0002"}
    )

    grandchild = child.create_child_context()

    assert grandchild.parent_span_id == child.span_id
    assert grandchild.parent_span_id == "child-span-0002"
    assert grandchild.parent_span_id != root.span_id
    assert grandchild.correlation_id == root.correlation_id


# ---------------------------------------------------------------------------
# 3. SequentialPrimitive creates child contexts for each step
# ---------------------------------------------------------------------------


async def test_sequential_primitive_creates_child_contexts() -> None:
    """SequentialPrimitive must pass a child context to each step.

    Each step's context must have parent_span_id == root.span_id, confirming
    that SequentialPrimitive calls create_child_context() before handing off.

    Arrange: root context with known span_id; 3 LambdaPrimitives that each
             capture the context they receive.
    Act:     execute SequentialPrimitive.
    Assert:  all 3 captured contexts have parent_span_id == root.span_id.
    """
    root = _root_ctx("sequential-test")
    captured: list[WorkflowContext] = []

    async def capture(data: Any, ctx: WorkflowContext) -> Any:
        captured.append(ctx)
        return data

    sequential = SequentialPrimitive(
        [LambdaPrimitive(capture), LambdaPrimitive(capture), LambdaPrimitive(capture)]
    )

    await sequential.execute("payload", root)

    assert len(captured) == 3, f"Expected 3 captured contexts, got {len(captured)}"
    for i, ctx in enumerate(captured):
        assert ctx.parent_span_id == root.span_id, (
            f"Step {i}: expected parent_span_id={root.span_id!r}, got {ctx.parent_span_id!r}"
        )
    for ctx in captured:
        assert ctx.correlation_id == root.correlation_id


# ---------------------------------------------------------------------------
# 4. to_otel_context() includes span_id and parent_span_id
# ---------------------------------------------------------------------------


async def test_to_otel_context_includes_span_ids() -> None:
    """to_otel_context() must expose span_id and parent_span_id for cross-agent handoffs.

    Arrange: context with known span_id and parent_span_id.
    Act:     call to_otel_context().
    Assert:  returned dict contains 'workflow.span_id' and 'workflow.parent_span_id'.
    """
    ctx = WorkflowContext(
        workflow_id="otel-serialization-test",
        span_id="span-abc123",
        parent_span_id="parent-xyz789",
    )

    otel_attrs = ctx.to_otel_context()

    assert "workflow.span_id" in otel_attrs, f"Missing 'workflow.span_id'. Keys: {list(otel_attrs)}"
    assert "workflow.parent_span_id" in otel_attrs, (
        f"Missing 'workflow.parent_span_id'. Keys: {list(otel_attrs)}"
    )
    assert otel_attrs["workflow.span_id"] == "span-abc123"
    assert otel_attrs["workflow.parent_span_id"] == "parent-xyz789"
    assert "workflow.id" in otel_attrs
    assert "workflow.correlation_id" in otel_attrs
    assert "workflow.elapsed_ms" in otel_attrs


# ---------------------------------------------------------------------------
# 5. ParallelPrimitive creates child contexts for each branch
# ---------------------------------------------------------------------------


async def test_parallel_primitive_creates_child_contexts() -> None:
    """ParallelPrimitive must pass a child context to each parallel branch.

    Each branch's context must have parent_span_id == root.span_id.

    Arrange: root context with known span_id; 3 LambdaPrimitives capturing ctx.
    Act:     execute ParallelPrimitive.
    Assert:  all 3 captured contexts have parent_span_id == root.span_id.
    """
    root = _root_ctx("parallel-test")
    captured: list[WorkflowContext] = []
    lock = asyncio.Lock()

    async def capture(data: Any, ctx: WorkflowContext) -> Any:
        async with lock:
            captured.append(ctx)
        return data

    parallel = ParallelPrimitive(
        [LambdaPrimitive(capture), LambdaPrimitive(capture), LambdaPrimitive(capture)]
    )

    results = await parallel.execute("payload", root)

    assert len(results) == 3
    assert len(captured) == 3, f"Expected 3 captured contexts, got {len(captured)}"
    for i, ctx in enumerate(captured):
        assert ctx.parent_span_id == root.span_id, (
            f"Branch {i}: expected parent_span_id={root.span_id!r}, got {ctx.parent_span_id!r}"
        )
    for ctx in captured:
        assert ctx.correlation_id == root.correlation_id
