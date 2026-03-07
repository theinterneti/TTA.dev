"""Formal performance benchmarks for TTA.dev primitives.

Run with: uv run pytest tests/benchmarks/ --benchmark-only
Compare: uv run pytest tests/benchmarks/ --benchmark-compare
Save baseline: uv run pytest tests/benchmarks/ --benchmark-save=baseline
"""

import asyncio

import pytest
from tta_dev_primitives import (
    CachePrimitive,
    ConditionalPrimitive,
    FallbackPrimitive,
    LambdaPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    WorkflowContext,
)


@pytest.fixture
def context():
    """Create a workflow context for benchmarks."""
    return WorkflowContext(workflow_id="benchmark")


@pytest.fixture
def simple_op():
    """Simple operation that returns input."""

    async def op(data: dict, ctx: WorkflowContext) -> dict:
        return {"result": data.get("value", 0) * 2}

    return LambdaPrimitive(op)


@pytest.fixture
def cpu_bound_op():
    """CPU-intensive operation for stress testing."""

    async def op(data: dict, ctx: WorkflowContext) -> dict:
        # Simulate computation
        result = 0
        for i in range(1000):
            result += i * data.get("value", 1)
        return {"result": result}

    return LambdaPrimitive(op)


class TestLambdaPrimitive:
    """Benchmark Lambda primitive - baseline performance."""

    def test_sync_execution(self, benchmark, simple_op, context):
        """Benchmark synchronous execution overhead."""

        def run():
            return asyncio.run(simple_op.execute({"value": 42}, context))

        result = benchmark(run)
        assert result["result"] == 84

    @pytest.mark.asyncio
    async def test_async_execution(self, benchmark, simple_op, context):
        """Benchmark async execution overhead."""

        async def run():
            return await simple_op.execute({"value": 42}, context)

        result = await benchmark(run)
        assert result["result"] == 84


class TestSequentialPrimitive:
    """Benchmark Sequential primitive - chaining overhead."""

    def test_two_step_chain(self, benchmark, simple_op, context):
        """Benchmark 2-step sequential workflow."""
        workflow = simple_op >> simple_op

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 40  # 10 * 2 * 2

    def test_five_step_chain(self, benchmark, simple_op, context):
        """Benchmark 5-step sequential workflow."""
        workflow = simple_op >> simple_op >> simple_op >> simple_op >> simple_op

        def run():
            return asyncio.run(workflow.execute({"value": 1}, context))

        result = benchmark(run)
        assert result["result"] == 32  # 1 * 2^5


class TestParallelPrimitive:
    """Benchmark Parallel primitive - concurrency overhead."""

    def test_two_parallel(self, benchmark, simple_op, context):
        """Benchmark 2 parallel operations."""
        workflow = ParallelPrimitive([simple_op, simple_op])

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        benchmark(run)

    def test_ten_parallel(self, benchmark, simple_op, context):
        """Benchmark 10 parallel operations."""
        workflow = ParallelPrimitive([simple_op] * 10)

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        benchmark(run)

    def test_fifty_parallel(self, benchmark, cpu_bound_op, context):
        """Benchmark 50 parallel CPU-bound operations."""
        workflow = ParallelPrimitive([cpu_bound_op] * 50)

        def run():
            return asyncio.run(workflow.execute({"value": 5}, context))

        benchmark(run)


class TestRetryPrimitive:
    """Benchmark Retry primitive - recovery overhead."""

    def test_success_first_try(self, benchmark, simple_op, context):
        """Benchmark retry with immediate success."""
        workflow = RetryPrimitive(simple_op, max_attempts=3)

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 20

    def test_success_third_try(self, benchmark, context):
        """Benchmark retry succeeding on 3rd attempt."""
        attempt_count = 0

        async def flaky_op(data: dict, ctx: WorkflowContext) -> dict:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Simulated failure")
            return {"result": data["value"] * 2}

        workflow = RetryPrimitive(
            LambdaPrimitive(flaky_op), max_attempts=5, backoff_factor=0.01
        )

        def run():
            nonlocal attempt_count
            attempt_count = 0
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 20


class TestCachePrimitive:
    """Benchmark Cache primitive - caching performance."""

    def test_cache_miss(self, benchmark, cpu_bound_op, context):
        """Benchmark cache miss (full execution)."""
        workflow = CachePrimitive(cpu_bound_op, ttl=300)

        counter = {"value": 0}

        def run():
            # Use unique key each time to force miss
            counter["value"] += 1
            ctx = WorkflowContext(workflow_id=f"benchmark-{counter['value']}")
            return asyncio.run(workflow.execute({"value": 10}, ctx))

        benchmark(run)

    def test_cache_hit(self, benchmark, cpu_bound_op, context):
        """Benchmark cache hit (no execution)."""
        workflow = CachePrimitive(cpu_bound_op, ttl=300)

        # Warm up cache
        asyncio.run(workflow.execute({"value": 10}, context))

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert "result" in result


class TestConditionalPrimitive:
    """Benchmark Conditional primitive - branching overhead."""

    def test_true_branch(self, benchmark, simple_op, context):
        """Benchmark conditional taking true branch."""

        async def always_true(data: dict, ctx: WorkflowContext) -> bool:
            return True

        async def zero_result(data: dict, ctx: WorkflowContext) -> dict:
            return {"result": 0}

        workflow = ConditionalPrimitive(
            condition=LambdaPrimitive(always_true),
            if_true=simple_op,
            if_false=LambdaPrimitive(zero_result),
        )

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 20

    def test_false_branch(self, benchmark, simple_op, context):
        """Benchmark conditional taking false branch."""

        async def always_false(data: dict, ctx: WorkflowContext) -> bool:
            return False

        async def zero_result(data: dict, ctx: WorkflowContext) -> dict:
            return {"result": 0}

        workflow = ConditionalPrimitive(
            condition=LambdaPrimitive(always_false),
            if_true=simple_op,
            if_false=LambdaPrimitive(zero_result),
        )

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 0


class TestTimeoutPrimitive:
    """Benchmark Timeout primitive - timeout overhead."""

    def test_fast_operation(self, benchmark, simple_op, context):
        """Benchmark timeout with fast operation."""
        workflow = TimeoutPrimitive(simple_op, timeout_seconds=5.0)

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 20

    def test_timeout_trigger(self, benchmark, context):
        """Benchmark timeout actually timing out."""

        async def slow_op(data: dict, ctx: WorkflowContext) -> dict:
            await asyncio.sleep(10)
            return {"result": data["value"]}

        workflow = TimeoutPrimitive(LambdaPrimitive(slow_op), timeout_seconds=0.01)

        def run():
            try:
                return asyncio.run(workflow.execute({"value": 10}, context))
            except TimeoutError:
                return {"timed_out": True}

        result = benchmark(run)
        assert result.get("timed_out") is True


class TestFallbackPrimitive:
    """Benchmark Fallback primitive - fallback overhead."""

    def test_primary_success(self, benchmark, simple_op, context):
        """Benchmark fallback with primary succeeding."""

        async def zero_result(data: dict, ctx: WorkflowContext) -> dict:
            return {"result": 0}

        fallback_op = LambdaPrimitive(zero_result)
        workflow = FallbackPrimitive([simple_op, fallback_op])

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 20

    def test_fallback_used(self, benchmark, simple_op, context):
        """Benchmark fallback being used."""

        async def failing_op(data: dict, ctx: WorkflowContext) -> dict:
            raise ValueError("Primary failed")

        workflow = FallbackPrimitive([LambdaPrimitive(failing_op), simple_op])

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        result = benchmark(run)
        assert result["result"] == 20


class TestComplexWorkflows:
    """Benchmark realistic complex workflows."""

    def test_parallel_sequential_mix(self, benchmark, simple_op, context):
        """Benchmark mixed parallel and sequential operations."""
        # (op1 || op2) >> op3 >> (op4 || op5 || op6)
        parallel1 = ParallelPrimitive([simple_op, simple_op])
        parallel2 = ParallelPrimitive([simple_op, simple_op, simple_op])
        workflow = parallel1 >> simple_op >> parallel2

        def run():
            return asyncio.run(workflow.execute({"value": 5}, context))

        benchmark(run)

    def test_retry_with_cache(self, benchmark, cpu_bound_op, context):
        """Benchmark retry wrapping cached operation."""
        cached = CachePrimitive(cpu_bound_op, ttl=300)
        workflow = RetryPrimitive(cached, max_attempts=3)

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        benchmark(run)

    def test_conditional_with_fallback(self, benchmark, simple_op, context):
        """Benchmark conditional with fallback strategies."""

        async def condition(data: dict, ctx: WorkflowContext) -> bool:
            return data.get("value", 0) > 5

        async def failing_op(data: dict, ctx: WorkflowContext) -> dict:
            raise ValueError("Failed")

        async def zero_result(data: dict, ctx: WorkflowContext) -> dict:
            return {"result": 0}

        fallback = FallbackPrimitive([LambdaPrimitive(failing_op), simple_op])
        workflow = ConditionalPrimitive(
            condition=LambdaPrimitive(condition),
            if_true=fallback,
            if_false=LambdaPrimitive(zero_result),
        )

        def run():
            return asyncio.run(workflow.execute({"value": 10}, context))

        benchmark(run)
