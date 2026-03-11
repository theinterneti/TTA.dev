#!/usr/bin/env python3
"""Test real-time trace generation and streaming."""

import asyncio
import time

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.core.sequential import SequentialPrimitive


class SimpleTask(WorkflowPrimitive):
    """A simple test primitive."""

    def __init__(self, name: str, delay: float = 0.1):
        super().__init__()
        self.name = name
        self.delay = delay

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute the task."""
        await asyncio.sleep(self.delay)
        return {**input_data, self.name: f"completed at {time.time()}"}


async def main():
    """Run test workflows."""
    print("🚀 Generating real-time traces...")

    # Create test workflow
    workflow = SequentialPrimitive(
        [
            SimpleTask("task1", 0.5),
            SimpleTask("task2", 0.5),
            SimpleTask("task3", 0.5),
        ]
    )

    # Execute with context
    ctx = WorkflowContext(
        workflow_id="realtime_test",
        metadata={
            "provider": "GitHub Copilot",
            "model": "Claude Sonnet 4.5",
            "agent": "test-automation",
            "user": "thein",
            "purpose": "Testing real-time trace streaming",
        },
    )

    result = await workflow.execute({"test": "data"}, ctx)
    print(f"✅ Workflow completed: {result}")
    print("\n📊 Check the dashboard to see this trace appear in real-time!")


if __name__ == "__main__":
    asyncio.run(main())
