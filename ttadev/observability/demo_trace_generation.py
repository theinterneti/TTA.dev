"""Demo script to generate traces with full metadata."""

import asyncio
import os

from ttadev.observability.collector import TraceCollector
from ttadev.observability.context import ExecutionContext
from ttadev.primitives.core import LambdaPrimitive, SequentialPrimitive, WorkflowContext


async def simulate_backend_engineer_workflow():
    """Simulate backend engineer building an API endpoint."""
    # Set agent role
    os.environ["TTA_AGENT_ROLE"] = "backend-engineer"

    ctx = ExecutionContext.detect_current()
    ctx.workflow_id = "build_api_endpoint"

    print(f"🤖 Agent: {ctx.agent}")
    print(f"👤 User: {ctx.user}")
    print(f"🏢 Provider: {ctx.provider}")
    print(f"🧠 Model: {ctx.model}")

    async def design_schema(data, wctx):
        await asyncio.sleep(0.5)
        return {"schema": "User(id, name, email)", **data}

    async def write_tests(data, wctx):
        await asyncio.sleep(0.7)
        return {"tests": ["test_create_user", "test_get_user"], **data}

    async def implement_endpoint(data, wctx):
        await asyncio.sleep(1.0)
        return {"endpoint": "/api/users", "status": "implemented", **data}

    workflow = SequentialPrimitive(
        [
            LambdaPrimitive(design_schema),
            LambdaPrimitive(write_tests),
            LambdaPrimitive(implement_endpoint),
        ]
    )

    wctx = WorkflowContext(workflow_id=ctx.workflow_id)
    result = await workflow.execute({"task": "Create user API"}, wctx)
    print(f"✅ Result: {result}")

    # Clean up
    del os.environ["TTA_AGENT_ROLE"]


async def simulate_architect_workflow():
    """Simulate architect reviewing system design."""
    os.environ["TTA_AGENT_ROLE"] = "architect"

    ctx = ExecutionContext.detect_current()
    ctx.workflow_id = "review_system_design"

    print(f"\n🤖 Agent: {ctx.agent}")
    print("📐 Reviewing architecture...")

    async def analyze_structure(data, wctx):
        await asyncio.sleep(0.8)
        return {"structure": "microservices", "rating": "good", **data}

    async def check_scalability(data, wctx):
        await asyncio.sleep(0.6)
        return {"scalability": "horizontal", "bottlenecks": [], **data}

    workflow = SequentialPrimitive(
        [
            LambdaPrimitive(analyze_structure),
            LambdaPrimitive(check_scalability),
        ]
    )

    wctx = WorkflowContext(workflow_id=ctx.workflow_id)
    result = await workflow.execute({"system": "TTA.dev"}, wctx)
    print(f"✅ Result: {result}")

    del os.environ["TTA_AGENT_ROLE"]


async def main():
    print("=" * 60)
    print("🚀 Generating Demo Traces with Full Metadata")
    print("=" * 60)

    await simulate_backend_engineer_workflow()
    await simulate_architect_workflow()

    print("\n" + "=" * 60)
    print("📊 Checking Trace Collection")
    print("=" * 60)

    collector = TraceCollector()
    traces = collector.get_all_traces()[:10]
    print(f"\n✅ Captured {len(traces)} traces")

    for i, trace in enumerate(traces, 1):
        print(f"\n{i}. Trace {trace.get('trace_id', 'N/A')[:8]}")
        print(f"   Workflow: {trace.get('workflow_id', 'N/A')}")
        print(f"   Agent: {trace.get('agent', 'N/A')}")
        print(f"   Provider: {trace.get('provider', 'N/A')}")
        print(f"   Model: {trace.get('model', 'N/A')}")
        print(f"   Spans: {len(trace.get('spans', []))}")


if __name__ == "__main__":
    asyncio.run(main())
