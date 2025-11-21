#!/usr/bin/env python3
"""Adaptive Coordination Demo - Learning orchestration in action."""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.orchestration import AdaptiveWorkflowEngine


async def demo_learning_orchestration():
    """Demonstrate adaptive coordination learning."""

    print("🧠 Adaptive Coordination Learning Demo")
    print("=" * 50)

    # Initialize learning coordination engine
    engine = AdaptiveWorkflowEngine()

    context = WorkflowContext(correlation_id="adaptive-demo")

    # Test scenarios
    scenarios = [
        {"task": "Build REST API endpoints", "context": {"env": "dev"}},
        {"task": "Deploy with monitoring", "context": {"env": "prod"}},
        {"task": "Run test suite", "context": {"env": "ci"}},
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\nTest {i}: {scenario['task']}")

        result = await engine.execute(scenario, context)
        print(f"✅ Primitives used: {result['primitivesUsed']}")
        print(f"🎯 Success: {result['result']['status']}")
        print(f"⏱️  Execution time: {result['executionTime']}s")
        print(f"🧠 Learning applied: {result['learningApplied']}")

    print("\n🎉 Adaptive coordination system operational!")


if __name__ == "__main__":
    asyncio.run(demo_learning_orchestration())
