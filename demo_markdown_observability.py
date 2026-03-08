"""Demo: Markdown-based observability in action."""

import asyncio
import time

from ttadev.observability.markdown_logger import log_agent_activity, log_primitive_usage, log_workflow_start
from ttadev.primitives.adaptive.base import WorkflowContext
from ttadev.primitives.adaptive import SequentialPrimitive
from ttadev.primitives.adaptive import RetryPrimitive


async def process_data(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate data processing."""
    start = time.time()
    await asyncio.sleep(0.1)  # Simulate work
    result = {"processed": data.get("value", 0) * 2}
    duration = (time.time() - start) * 1000
    
    log_primitive_usage("DataProcessor", data, result, duration)
    return result


async def main():
    """Run observability demo."""
    print("🔍 Running markdown observability demo...\n")
    
    # Log agent startup
    log_agent_activity(
        "DemoAgent",
        "startup",
        {"version": "1.0.0", "capabilities": ["data_processing", "retry_logic"]}
    )
    
    # Create workflow
    context = WorkflowContext(workflow_id="demo-001", metadata={"user": "demo", "env": "dev"})
    log_workflow_start("demo-001", "DataProcessingWorkflow", context)
    
    # Execute workflow with primitives
    workflow = RetryPrimitive(
        SequentialPrimitive(process_data),
        max_attempts=3
    )
    
    result = await workflow.execute({"value": 42}, context)
    
    log_agent_activity(
        "DemoAgent",
        "workflow_completed",
        {"workflow_id": "demo-001", "result": result, "status": "success"}
    )
    
    print(f"✅ Result: {result}\n")
    print("📊 Observability logs written to .tta/logs/")
    print("   - workflows.md")
    print("   - primitives.md")
    print("   - agents.md")


if __name__ == "__main__":
    asyncio.run(main())
