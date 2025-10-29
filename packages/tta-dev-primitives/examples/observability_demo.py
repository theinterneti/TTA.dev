#!/usr/bin/env python3
"""
Demonstration of Phase 2 observability instrumentation.

Shows structured logging, checkpoint tracking, and trace propagation
for all instrumented primitives.
"""

import asyncio

from tta_dev_primitives import (
    ConditionalPrimitive,
    FallbackPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    SagaPrimitive,
    SequentialPrimitive,
    SwitchPrimitive,
    WorkflowContext,
)
from tta_dev_primitives.core.base import LambdaPrimitive
from tta_dev_primitives.recovery.retry import RetryStrategy


async def demo_sequential():
    """Demonstrate Sequential primitive instrumentation."""
    print("\n=== Sequential Primitive Demo ===")
    
    step1 = LambdaPrimitive(lambda x, ctx: {"step": 1, "data": x})
    step2 = LambdaPrimitive(lambda x, ctx: {"step": 2, "data": x})
    step3 = LambdaPrimitive(lambda x, ctx: {"step": 3, "data": x})
    
    workflow = step1 >> step2 >> step3
    context = WorkflowContext(workflow_id="sequential-demo")
    
    result = await workflow.execute("input", context)
    
    print(f"Result: {result}")
    print(f"Checkpoints: {[name for name, _ in context.checkpoints]}")
    print(f"Elapsed: {context.elapsed_ms():.2f}ms")


async def demo_parallel():
    """Demonstrate Parallel primitive instrumentation."""
    print("\n=== Parallel Primitive Demo ===")
    
    branch1 = LambdaPrimitive(lambda x, ctx: f"branch1_{x}")
    branch2 = LambdaPrimitive(lambda x, ctx: f"branch2_{x}")
    branch3 = LambdaPrimitive(lambda x, ctx: f"branch3_{x}")
    
    workflow = branch1 | branch2 | branch3
    context = WorkflowContext(workflow_id="parallel-demo", correlation_id="demo-123")
    
    results = await workflow.execute("input", context)
    
    print(f"Results: {results}")
    print(f"Checkpoints: {[name for name, _ in context.checkpoints]}")
    print(f"Correlation ID: {context.correlation_id}")


async def demo_conditional():
    """Demonstrate Conditional primitive instrumentation."""
    print("\n=== Conditional Primitive Demo ===")
    
    then_branch = LambdaPrimitive(lambda x, ctx: "HIGH_VALUE")
    else_branch = LambdaPrimitive(lambda x, ctx: "LOW_VALUE")
    
    workflow = ConditionalPrimitive(
        condition=lambda x, ctx: x > 50,
        then_primitive=then_branch,
        else_primitive=else_branch,
    )
    
    # Test then branch
    context1 = WorkflowContext(workflow_id="conditional-demo-1")
    result1 = await workflow.execute(75, context1)
    print(f"Input 75 -> Result: {result1}, Branch: {context1.state.get('last_conditional_branch')}")
    
    # Test else branch
    context2 = WorkflowContext(workflow_id="conditional-demo-2")
    result2 = await workflow.execute(25, context2)
    print(f"Input 25 -> Result: {result2}, Branch: {context2.state.get('last_conditional_branch')}")


async def demo_switch():
    """Demonstrate Switch primitive instrumentation."""
    print("\n=== Switch Primitive Demo ===")
    
    case_a = LambdaPrimitive(lambda x, ctx: "CASE_A_RESULT")
    case_b = LambdaPrimitive(lambda x, ctx: "CASE_B_RESULT")
    default = LambdaPrimitive(lambda x, ctx: "DEFAULT_RESULT")
    
    workflow = SwitchPrimitive(
        selector=lambda x, ctx: x.get("type", ""),
        cases={"type_a": case_a, "type_b": case_b},
        default=default,
    )
    
    # Test different cases
    context1 = WorkflowContext()
    result1 = await workflow.execute({"type": "type_a"}, context1)
    print(f"Case 'type_a' -> Result: {result1}, Selected: {context1.state.get('last_switch_case')}")
    
    context2 = WorkflowContext()
    result2 = await workflow.execute({"type": "unknown"}, context2)
    print(f"Case 'unknown' -> Result: {result2}, Selected: {context2.state.get('last_switch_case')}")


async def demo_retry():
    """Demonstrate Retry primitive instrumentation."""
    print("\n=== Retry Primitive Demo ===")
    
    attempt_count = 0
    
    async def flaky_operation(data, ctx):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")
        return "SUCCESS"
    
    primitive = LambdaPrimitive(flaky_operation)
    workflow = RetryPrimitive(
        primitive,
        strategy=RetryStrategy(max_retries=3, backoff_base=0.01),
    )
    
    context = WorkflowContext(workflow_id="retry-demo")
    result = await workflow.execute("input", context)
    
    print(f"Result: {result} (succeeded after {attempt_count} attempts)")


async def demo_fallback():
    """Demonstrate Fallback primitive instrumentation."""
    print("\n=== Fallback Primitive Demo ===")
    
    primary = LambdaPrimitive(lambda x, ctx: (_ for _ in ()).throw(ValueError("Primary failed")))
    fallback = LambdaPrimitive(lambda x, ctx: "FALLBACK_SUCCESS")
    
    workflow = FallbackPrimitive(primary=primary, fallback=fallback)
    
    context = WorkflowContext(workflow_id="fallback-demo")
    result = await workflow.execute("input", context)
    
    print(f"Result: {result}")


async def demo_saga():
    """Demonstrate Saga primitive instrumentation."""
    print("\n=== Saga Primitive Demo ===")
    
    forward = LambdaPrimitive(lambda x, ctx: (_ for _ in ()).throw(RuntimeError("Forward failed")))
    compensation = LambdaPrimitive(lambda x, ctx: "COMPENSATED")
    
    workflow = SagaPrimitive(forward=forward, compensation=compensation)
    
    context = WorkflowContext(workflow_id="saga-demo")
    
    try:
        await workflow.execute("input", context)
    except RuntimeError:
        print("Forward failed, compensation executed (check logs)")


async def demo_complex_workflow():
    """Demonstrate complex workflow with multiple primitives."""
    print("\n=== Complex Workflow Demo ===")
    
    # Build: validate >> (analyze_a | analyze_b) >> conditional
    validate = LambdaPrimitive(lambda x, ctx: {"validated": True, "value": 75})
    
    analyze_a = LambdaPrimitive(lambda x, ctx: "analysis_a")
    analyze_b = LambdaPrimitive(lambda x, ctx: "analysis_b")
    
    high_value = LambdaPrimitive(lambda x, ctx: f"HIGH_VALUE: {x}")
    low_value = LambdaPrimitive(lambda x, ctx: f"LOW_VALUE: {x}")
    
    conditional = ConditionalPrimitive(
        condition=lambda x, ctx: isinstance(x, list) and len(x) == 2,
        then_primitive=high_value,
        else_primitive=low_value,
    )
    
    workflow = validate >> (analyze_a | analyze_b) >> conditional
    
    context = WorkflowContext(workflow_id="complex-demo", correlation_id="complex-123")
    result = await workflow.execute("input", context)
    
    print(f"Result: {result}")
    print(f"Checkpoints: {[name for name, _ in context.checkpoints]}")
    print(f"Elapsed: {context.elapsed_ms():.2f}ms")


async def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("Phase 2 Observability Instrumentation Demo")
    print("=" * 60)
    
    await demo_sequential()
    await demo_parallel()
    await demo_conditional()
    await demo_switch()
    await demo_retry()
    await demo_fallback()
    await demo_saga()
    await demo_complex_workflow()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nAll primitives now emit structured logs with:")
    print("  - Correlation IDs for distributed tracing")
    print("  - Timing checkpoints for performance analysis")
    print("  - Branch/case tracking for decision visibility")
    print("  - Retry/fallback/compensation tracking for resilience")


if __name__ == "__main__":
    asyncio.run(main())
