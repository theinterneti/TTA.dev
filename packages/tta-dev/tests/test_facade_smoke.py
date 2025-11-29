"""Smoke tests for tta_dev façade: demonstrate primitive composition via the façade."""

import pytest
from tta_dev import (
    CachePrimitive,
    MockPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    RetryStrategy,
    SequentialPrimitive,
    WorkflowContext,
)


class TestPrimitiveComposition:
    """Smoke tests demonstrating that primitives compose correctly via the façade."""

    @pytest.mark.asyncio
    async def test_sequential_composition_operator(self) -> None:
        """Test that >> operator works for sequential composition."""
        step1 = MockPrimitive(name="step1", return_value={"step": 1})
        step2 = MockPrimitive(name="step2", return_value={"step": 2})

        workflow = step1 >> step2

        assert isinstance(workflow, SequentialPrimitive)

        ctx = WorkflowContext(workflow_id="smoke-seq")
        result = await workflow.execute({"input": "data"}, ctx)

        assert result == {"step": 2}
        assert step1.call_count == 1
        assert step2.call_count == 1

    @pytest.mark.asyncio
    async def test_parallel_composition_operator(self) -> None:
        """Test that | operator works for parallel composition."""
        branch1 = MockPrimitive(name="branch1", return_value={"branch": 1})
        branch2 = MockPrimitive(name="branch2", return_value={"branch": 2})

        workflow = branch1 | branch2

        assert isinstance(workflow, ParallelPrimitive)

        ctx = WorkflowContext(workflow_id="smoke-par")
        results = await workflow.execute({"input": "data"}, ctx)

        assert len(results) == 2
        assert branch1.call_count == 1
        assert branch2.call_count == 1

    @pytest.mark.asyncio
    async def test_mixed_composition(self) -> None:
        """Test mixed sequential and parallel composition."""
        step1 = MockPrimitive(name="step1", return_value={"stage": "pre"})
        branch_a = MockPrimitive(name="branch_a", return_value={"branch": "a"})
        branch_b = MockPrimitive(name="branch_b", return_value={"branch": "b"})
        step3 = MockPrimitive(name="step3", return_value={"stage": "post"})

        # step1 >> (branch_a | branch_b) >> step3
        parallel_part = branch_a | branch_b
        workflow = step1 >> parallel_part >> step3

        ctx = WorkflowContext(workflow_id="smoke-mixed")
        result = await workflow.execute({"input": "data"}, ctx)

        assert result == {"stage": "post"}

    @pytest.mark.asyncio
    async def test_workflow_context_propagation(self) -> None:
        """Test that WorkflowContext is properly propagated through primitives."""
        received_contexts: list[WorkflowContext] = []

        class CapturingPrimitive(MockPrimitive):
            async def execute(self, input_data, context):
                received_contexts.append(context)
                return await super().execute(input_data, context)

        step1 = CapturingPrimitive(name="step1", return_value={"ok": True})
        step2 = CapturingPrimitive(name="step2", return_value={"ok": True})

        workflow = step1 >> step2

        ctx = WorkflowContext(workflow_id="ctx-propagation-test")
        await workflow.execute({"input": "data"}, ctx)

        # Both primitives should have received a context
        assert len(received_contexts) >= 2
        # All contexts should have the same workflow_id
        for received_ctx in received_contexts:
            assert received_ctx.workflow_id == "ctx-propagation-test"


class TestRetryPrimitiveViaFacade:
    """Test RetryPrimitive usage via the façade."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_immediately(self) -> None:
        """Test retry when underlying primitive succeeds on first try."""
        inner = MockPrimitive(name="inner", return_value={"success": True})
        strategy = RetryStrategy(max_retries=3)
        retry = RetryPrimitive(primitive=inner, strategy=strategy)

        ctx = WorkflowContext(workflow_id="retry-success")
        result = await retry.execute({"input": "data"}, ctx)

        assert result == {"success": True}
        assert inner.call_count == 1


class TestCachePrimitiveViaFacade:
    """Test CachePrimitive usage via the façade."""

    @pytest.mark.asyncio
    async def test_cache_hit_on_repeat_call(self) -> None:
        """Test that repeated calls hit the cache."""
        call_count = 0

        class CountingPrimitive(MockPrimitive):
            async def execute(self, input_data, context):
                nonlocal call_count
                call_count += 1
                return {"count": call_count}

        inner = CountingPrimitive(name="counter", return_value={})
        cache = CachePrimitive(
            primitive=inner,
            cache_key_fn=lambda data, ctx: str(data),
            ttl_seconds=60.0,
        )

        ctx = WorkflowContext(workflow_id="cache-test")

        result1 = await cache.execute({"key": "value"}, ctx)
        result2 = await cache.execute({"key": "value"}, ctx)

        # First call: cache miss, second call: cache hit
        assert result1 == result2
        # Inner primitive should only be called once
        assert call_count == 1
