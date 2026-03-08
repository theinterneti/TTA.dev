"""Demo: Markdown observability in action."""
import asyncio
from ttadev.primitives.core.base import WorkflowPrimitive, WorkflowContext

class GreetPrimitive(WorkflowPrimitive[str, str]):
    """Simple greeting primitive."""
    
    async def _execute(self, name: str, context: WorkflowContext) -> str:
        return f"Hello, {name}!"

class ProcessPrimitive(WorkflowPrimitive[str, str]):
    """Processing primitive."""
    
    async def _execute(self, data: str, context: WorkflowContext) -> str:
        return data.upper()

async def main():
    print("🎯 Running TTA.dev with Markdown Observability...")
    print("📝 Check .tta/logs/ for auto-generated activity logs\n")
    
    # Create workflow
    workflow = GreetPrimitive() >> ProcessPrimitive()
    context = WorkflowContext(workflow_id="demo-workflow")
    
    # Execute multiple times
    for name in ["Alice", "Bob", "Charlie"]:
        result = await workflow.execute(name, context)
        print(f"   Result: {result}")
    
    print("\n✅ Done! Check these files:")
    print("   - .tta/logs/primitives.md")
    print("   - .tta/logs/activity-2026-03-08.md")
    print("   - .tta/logs/INDEX.md")

if __name__ == "__main__":
    asyncio.run(main())
