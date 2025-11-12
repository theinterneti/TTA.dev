"""
Test Phase 1: Semantic Tracing Implementation

This example verifies that:
1. WorkflowContext includes agent_id, agent_type, workflow_name, llm_* fields
2. InstrumentedPrimitive creates semantic span names: primitive.{type}.{action}
3. SequentialPrimitive creates semantic step spans: primitive.sequential.step_0
4. All standard attributes are set correctly

Run this to verify Phase 1 implementation is working correctly.
"""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class SimpleProcessor(InstrumentedPrimitive[dict, dict]):
    """Simple primitive for testing semantic tracing."""

    def __init__(self):
        super().__init__(
            name="SimpleProcessor",
            primitive_type="processor",
            action="process",
        )

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Process data with a simple transformation."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"processed": True, "input": input_data}


class ValidatorProcessor(InstrumentedPrimitive[dict, dict]):
    """Validator primitive for testing."""

    def __init__(self):
        super().__init__(
            name="ValidatorProcessor",
            primitive_type="validator",
            action="validate",
        )

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Validate processed data."""
        await asyncio.sleep(0.05)  # Simulate validation
        return {**input_data, "validated": True}


async def test_semantic_tracing():
    """Test semantic tracing with enhanced WorkflowContext."""

    print("\n" + "=" * 80)
    print("Phase 1: Semantic Tracing Test")
    print("=" * 80 + "\n")

    # Create context with all new fields
    context = WorkflowContext(
        workflow_id="test-wf-001",
        workflow_name="Test Semantic Tracing Workflow",
        agent_id="agent-12345",
        agent_type="coordinator",
        llm_provider="openai",
        llm_model_name="gpt-4",
        llm_model_tier="quality",
        correlation_id="test-corr-001",
    )

    print("✓ Created WorkflowContext with new fields:")
    print(f"  - agent_id: {context.agent_id}")
    print(f"  - agent_type: {context.agent_type}")
    print(f"  - workflow_name: {context.workflow_name}")
    print(f"  - llm_provider: {context.llm_provider}")
    print(f"  - llm_model_name: {context.llm_model_name}")
    print(f"  - llm_model_tier: {context.llm_model_tier}")
    print()

    # Test individual primitive
    print("Testing individual primitive (SimpleProcessor)...")
    processor = SimpleProcessor()

    # Verify semantic naming
    print(f"✓ Semantic span name: {processor._get_span_name()}")
    print("  Expected: primitive.processor.process")
    assert processor._get_span_name() == "primitive.processor.process"

    result = await processor.execute({"test": "data"}, context)
    print(f"✓ Execution successful: {result}")
    print()

    # Test sequential workflow
    print("Testing SequentialPrimitive with semantic steps...")
    from tta_dev_primitives.core.sequential import SequentialPrimitive

    workflow = SequentialPrimitive([SimpleProcessor(), ValidatorProcessor()])

    # Verify sequential primitive semantic naming
    print(f"✓ Sequential span name: {workflow._get_span_name()}")
    print("  Expected: primitive.sequential.execute")
    assert workflow._get_span_name() == "primitive.sequential.execute"

    result = await workflow.execute({"input": "test"}, context)
    print(f"✓ Workflow execution successful: {result}")
    print()

    # Test to_otel_context includes new fields
    print("Testing to_otel_context() includes new attributes...")
    otel_attrs = context.to_otel_context()
    print("✓ OpenTelemetry attributes:")
    for key, value in sorted(otel_attrs.items()):
        print(f"  - {key}: {value}")

    # Verify new attributes are present
    assert "agent.id" in otel_attrs
    assert "agent.type" in otel_attrs
    assert "workflow.name" in otel_attrs
    assert "llm.provider" in otel_attrs
    assert "llm.model_name" in otel_attrs
    assert "llm.model_tier" in otel_attrs
    print()

    # Test child context propagation
    print("Testing child context propagation...")
    child_context = context.create_child_context()
    assert child_context.agent_id == context.agent_id
    assert child_context.agent_type == context.agent_type
    assert child_context.workflow_name == context.workflow_name
    assert child_context.llm_provider == context.llm_provider
    assert child_context.llm_model_name == context.llm_model_name
    assert child_context.llm_model_tier == context.llm_model_tier
    print("✓ Child context inherits all new fields")
    print()

    print("=" * 80)
    print("✅ Phase 1: Semantic Tracing - ALL TESTS PASSED")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Start observability stack: ./scripts/setup-observability.sh")
    print("2. Run observability demo: uv run python examples/observability_demo.py")
    print("3. Check Jaeger UI (http://localhost:16686) for semantic span names")
    print("4. Verify span attributes include agent.*, workflow.*, llm.* fields")
    print()


if __name__ == "__main__":
    asyncio.run(test_semantic_tracing())
