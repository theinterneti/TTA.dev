"""Demo workflow to test observability dashboard."""
import asyncio
from primitives.core import SequentialPrimitive, ParallelPrimitive
from primitives.recovery import RetryPrimitive, RetryStrategy
from primitives.core.base import WorkflowContext, LambdaPrimitive

async def fetch_data(data, ctx):
    """Simulate data fetching."""
    await asyncio.sleep(0.2)
    return {"fetched": True, "value": data.get("id", 0)}

async def process_data(data, ctx):
    """Simulate data processing."""
    await asyncio.sleep(0.3)
    return {"processed": True, "result": data.get("value", 0) * 2}

async def validate_data(data, ctx):
    """Simulate validation."""
    await asyncio.sleep(0.1)
    return {"valid": True, "final": data.get("result", 0) + 10}

async def main():
    """Run demo workflow."""
    # Build complex workflow
    workflow = SequentialPrimitive([
        RetryPrimitive(
            LambdaPrimitive(fetch_data),
            strategy=RetryStrategy(max_retries=3)
        ),
        ParallelPrimitive([
            LambdaPrimitive(process_data),
            LambdaPrimitive(validate_data)
        ])
    ])
    
    ctx = WorkflowContext(workflow_id="demo-workflow")
    result = await workflow.execute({"id": 42}, ctx)
    print(f"✓ Workflow completed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
