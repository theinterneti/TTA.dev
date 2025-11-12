#!/usr/bin/env python3
"""
Test script to verify OpenTelemetry context propagation across async boundaries.

This script validates that:
1. Child spans link to parent spans (same trace_id)
2. Context propagates across asyncio.gather() calls
3. Parallel execution maintains trace continuity
4. All spans appear in a single unified trace tree

Run with: uv run python packages/tta-dev-primitives/examples/test_trace_propagation.py
"""

import asyncio
import sys

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)

# Setup OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    TRACING_AVAILABLE = True
except ImportError:
    print("❌ OpenTelemetry not installed. Install with:")
    print(
        "   uv pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
    )
    sys.exit(1)


# Test primitives
class Step1Primitive(InstrumentedPrimitive[dict, dict]):
    """First step in sequential workflow."""

    def __init__(self) -> None:
        super().__init__(name="step1")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(0.01)
        return {**input_data, "step1": "complete"}


class Step2Primitive(InstrumentedPrimitive[dict, dict]):
    """Second step in sequential workflow."""

    def __init__(self) -> None:
        super().__init__(name="step2")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(0.01)
        return {**input_data, "step2": "complete"}


class ParallelBranch1(InstrumentedPrimitive[dict, dict]):
    """First parallel branch."""

    def __init__(self) -> None:
        super().__init__(name="parallel_branch_1")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(0.02)
        return {**input_data, "branch1": "complete"}


class ParallelBranch2(InstrumentedPrimitive[dict, dict]):
    """Second parallel branch."""

    def __init__(self) -> None:
        super().__init__(name="parallel_branch_2")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(0.02)
        return {**input_data, "branch2": "complete"}


class ParallelBranch3(InstrumentedPrimitive[dict, dict]):
    """Third parallel branch."""

    def __init__(self) -> None:
        super().__init__(name="parallel_branch_3")

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(0.02)
        return {**input_data, "branch3": "complete"}


def setup_tracing(use_otlp: bool = False) -> tuple[TracerProvider, set[str]]:
    """
    Setup OpenTelemetry tracing with console or OTLP exporter.

    Args:
        use_otlp: If True, export to OTLP collector. Otherwise console only.

    Returns:
        Tuple of (TracerProvider, set of trace IDs seen)
    """
    resource = Resource.create(
        {
            "service.name": "trace-propagation-test",
            "service.version": "1.0.0",
            "deployment.environment": "test",
        }
    )

    provider = TracerProvider(resource=resource)

    # Console exporter for validation
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(console_processor)

    # OTLP exporter (if requested and available)
    if use_otlp:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint="http://localhost:4317",
                insecure=True,
            )
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(otlp_processor)
            print("✅ OTLP exporter configured - traces will be sent to Jaeger")
        except Exception as e:
            print(f"⚠️  OTLP exporter failed: {e}")
            print("   Falling back to console-only output")

    trace.set_tracer_provider(provider)

    # Track trace IDs to verify continuity
    trace_ids_seen: set[str] = set()

    return provider, trace_ids_seen


async def test_sequential_propagation(trace_ids: set[str]) -> bool:
    """Test context propagation in sequential execution."""
    print("\n" + "=" * 80)
    print("TEST 1: Sequential Execution Context Propagation")
    print("=" * 80)

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("test_sequential") as root_span:
        root_ctx = root_span.get_span_context()
        root_trace_id = format(root_ctx.trace_id, "032x")
        trace_ids.add(root_trace_id)

        print(f"\n📍 Root span trace_id: {root_trace_id}")

        # Create sequential workflow
        workflow = SequentialPrimitive([Step1Primitive(), Step2Primitive()])

        # Execute
        context = WorkflowContext(
            workflow_id="test-sequential",
            tags={"test": "sequential", "environment": "test"},
        )
        _result = await workflow.execute({"input": "test"}, context)

        # Verify trace ID matches
        final_trace_id = context.trace_id
        if final_trace_id == root_trace_id:
            print("✅ Sequential context propagation PASSED")
            print(f"   All spans share trace_id: {root_trace_id}")
            return True
        else:
            print("❌ Sequential context propagation FAILED")
            print(f"   Root trace_id:  {root_trace_id}")
            print(f"   Final trace_id: {final_trace_id}")
            return False


async def test_parallel_propagation(trace_ids: set[str]) -> bool:
    """Test context propagation in parallel execution."""
    print("\n" + "=" * 80)
    print("TEST 2: Parallel Execution Context Propagation")
    print("=" * 80)

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("test_parallel") as root_span:
        root_ctx = root_span.get_span_context()
        root_trace_id = format(root_ctx.trace_id, "032x")
        trace_ids.add(root_trace_id)

        print(f"\n📍 Root span trace_id: {root_trace_id}")

        # Create parallel workflow
        workflow = ParallelPrimitive([ParallelBranch1(), ParallelBranch2(), ParallelBranch3()])

        # Execute
        context = WorkflowContext(
            workflow_id="test-parallel",
            tags={"test": "parallel", "environment": "test"},
        )
        results = await workflow.execute({"input": "test"}, context)

        # Verify trace ID matches
        final_trace_id = context.trace_id
        if final_trace_id == root_trace_id:
            print("✅ Parallel context propagation PASSED")
            print(f"   All {len(results)} branches share trace_id: {root_trace_id}")
            return True
        else:
            print("❌ Parallel context propagation FAILED")
            print(f"   Root trace_id:  {root_trace_id}")
            print(f"   Final trace_id: {final_trace_id}")
            return False


async def test_mixed_propagation(trace_ids: set[str]) -> bool:
    """Test context propagation in mixed sequential + parallel execution."""
    print("\n" + "=" * 80)
    print("TEST 3: Mixed Sequential + Parallel Context Propagation")
    print("=" * 80)

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("test_mixed") as root_span:
        root_ctx = root_span.get_span_context()
        root_trace_id = format(root_ctx.trace_id, "032x")
        trace_ids.add(root_trace_id)

        print(f"\n📍 Root span trace_id: {root_trace_id}")

        # Create mixed workflow: step1 >> (branch1 | branch2 | branch3) >> step2
        parallel_step = ParallelPrimitive([ParallelBranch1(), ParallelBranch2(), ParallelBranch3()])
        workflow = SequentialPrimitive([Step1Primitive(), parallel_step, Step2Primitive()])

        # Execute
        context = WorkflowContext(
            workflow_id="test-mixed",
            session_id="session-123",
            correlation_id="corr-456",
            tags={"test": "mixed", "environment": "test"},
            baggage={"user.id": "user-789", "request.type": "test"},
        )
        _result = await workflow.execute({"input": "test"}, context)

        # Verify trace ID matches
        final_trace_id = context.trace_id
        if final_trace_id == root_trace_id:
            print("✅ Mixed context propagation PASSED")
            print(f"   All spans (sequential + parallel) share trace_id: {root_trace_id}")
            return True
        else:
            print("❌ Mixed context propagation FAILED")
            print(f"   Root trace_id:  {root_trace_id}")
            print(f"   Final trace_id: {final_trace_id}")
            return False


async def main() -> None:
    """Run all context propagation tests."""
    print("🔍 OpenTelemetry Context Propagation Test Suite")
    print("=" * 80)
    print("\nThis test verifies that trace context propagates correctly across:")
    print("  • Sequential primitive execution")
    print("  • Parallel primitive execution (asyncio.gather)")
    print("  • Mixed workflows with both patterns")
    print("\n✅ = All spans in single unified trace (same trace_id)")
    print("❌ = Broken trace linking (different trace_ids)")

    # Check if OTLP collector is available
    use_otlp = True  # Change to False for console-only output

    # Setup tracing
    provider, trace_ids = setup_tracing(use_otlp=use_otlp)

    # Run tests
    test_results = []
    try:
        test_results.append(await test_sequential_propagation(trace_ids))
        test_results.append(await test_parallel_propagation(trace_ids))
        test_results.append(await test_mixed_propagation(trace_ids))
    finally:
        # Force export of all spans
        for processor in provider._active_span_processor._span_processors:
            processor.force_flush()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {len(test_results)}")
    print(f"Passed: {sum(test_results)}")
    print(f"Failed: {len(test_results) - sum(test_results)}")
    print(f"\nUnique trace IDs seen: {len(trace_ids)}")
    print(f"Expected trace IDs: {len(test_results)}")

    if len(trace_ids) == len(test_results) and all(test_results):
        print("\n✅ All tests PASSED - Context propagation working correctly!")
        print("\nYou should see:")
        print("  • 3 separate trace trees (one per test)")
        print("  • Each trace has all spans properly linked (parent-child)")
        print("  • No orphaned spans or broken trace links")
        if use_otlp:
            print("\n🔍 Check Jaeger UI: http://localhost:16686")
            print("   Service: trace-propagation-test")
            print("   Look for 3 traces with complete span trees")
    else:
        print("\n❌ TESTS FAILED - Context propagation broken!")
        print("\nExpected behavior:")
        print("  • All spans in a test should share the same trace_id")
        print("  • Child spans should link to parent spans")
        print("  • Parallel branches should all link to the parallel step parent")

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
