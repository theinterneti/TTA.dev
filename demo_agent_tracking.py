"""Demo script showing agent activity tracking in action."""

import asyncio
import sys
from pathlib import Path

# Add ttadev to path
sys.path.insert(0, str(Path(__file__).parent))

from ttadev.observability.agent_tracker import track_action
from ttadev.primitives.core import SequentialPrimitive, ParallelPrimitive
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext

async def demo_copilot_working():
    """Simulate GitHub Copilot (me!) working on tasks."""
    print("🤖 Simulating GitHub Copilot CLI agent activity...")
    
    # Track: I'm starting to work
    track_action(
        provider="github-copilot",
        model="claude-sonnet-4.5",
        action_type="session_start",
        action_data={"task": "Building agent activity dashboard"},
        user="thein"
    )
    
    await asyncio.sleep(1)
    
    # Track: Using primitives
    track_action(
        provider="github-copilot",
        model="claude-sonnet-4.5",
        action_type="primitive_execution",
        action_data={
            "primitive": "SequentialPrimitive",
            "workflow": "dashboard_enhancement",
        },
        user="thein"
    )
    
    await asyncio.sleep(1)
    
    # Track: Activating backend-engineer agent
    track_action(
        provider="github-copilot",
        model="claude-sonnet-4.5",
        action_type="agent_activation",
        action_data={"task": "Implement agent tracker module"},
        tta_agent="backend-engineer",
        user="thein"
    )
    
    await asyncio.sleep(1)
    
    # Track: Code generation
    track_action(
        provider="github-copilot",
        model="claude-sonnet-4.5",
        action_type="code_generation",
        action_data={
            "files_created": ["agent_tracker.py", "auto_track_copilot.py"],
            "lines_of_code": 250,
        },
        tta_agent="backend-engineer",
        user="thein"
    )
    
    await asyncio.sleep(1)
    
    # Track: Running tests
    track_action(
        provider="github-copilot",
        model="claude-sonnet-4.5",
        action_type="test_execution",
        action_data={
            "test_file": "test_agent_tracker.py",
            "tests_passed": 8,
            "tests_failed": 0,
        },
        user="thein"
    )
    
    print("✓ Generated agent activity data!")
    print("✓ Check the dashboard at http://localhost:8000")

async def demo_workflow_with_tracking():
    """Run a workflow that generates tracked activity."""
    print("\n�� Running instrumented workflow...")
    
    async def task1(data, ctx):
        track_action(
            provider="github-copilot",
            model="claude-sonnet-4.5",
            action_type="workflow_step",
            action_data={"step": "task1", "data": str(data)},
            user="thein"
        )
        return {"result": "task1_complete"}
    
    async def task2(data, ctx):
        track_action(
            provider="github-copilot",
            model="claude-sonnet-4.5",
            action_type="workflow_step",
            action_data={"step": "task2", "data": str(data)},
            user="thein"
        )
        return {"result": "task2_complete"}
    
    workflow = SequentialPrimitive([
        LambdaPrimitive(task1),
        LambdaPrimitive(task2),
    ])
    
    context = WorkflowContext(workflow_id="demo-workflow")
    result = await workflow.execute({"input": "test"}, context)
    
    print(f"✓ Workflow completed: {result}")

async def main():
    """Run all demos."""
    await demo_copilot_working()
    await demo_workflow_with_tracking()
    
    print("\n✅ Demo complete! View activity at http://localhost:8000")
    print("   Look for:")
    print("   - Active Agents section showing GitHub Copilot")
    print("   - Recent Actions showing all tracked activities")
    print("   - Agent details: provider=github-copilot, model=claude-sonnet-4.5")

if __name__ == "__main__":
    asyncio.run(main())
