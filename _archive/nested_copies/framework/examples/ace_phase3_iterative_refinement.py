"""
ACE Phase 3: Iterative Refinement Demo

Demonstrates the error feedback loop where:
1. LLM generates code
2. E2B executes and finds errors
3. LLM fixes errors based on feedback
4. Repeat until code works

This is the key innovation that makes ACE self-improving!
"""

import asyncio
from pathlib import Path

from tta_dev_primitives.ace.cognitive_manager import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext


async def demo_iterative_refinement():
    """Demonstrate Phase 3 iterative refinement with error feedback."""

    print("🔄 ACE Phase 3: Iterative Refinement Demo")
    print("=" * 70)
    print()

    # Initialize learner with playbook
    learner = SelfLearningCodePrimitive(playbook_file=Path("phase3_refinement_playbook.json"))

    # Create context
    context = WorkflowContext(correlation_id="phase3-demo")

    # Test 1: Intentionally vague task that will likely fail first time
    print("📝 Test 1: Vague Task (Expected to need refinement)")
    print("-" * 70)
    print("Task: Create a function to validate email addresses")
    print("Expected: First attempt may have bugs, refinement should fix them")
    print()

    result1 = await learner.execute(
        {
            "task": "Create a Python function to validate email addresses",
            "language": "python",
            "context": "Should handle common edge cases and return True/False",
            "max_iterations": 3,  # Allow up to 3 refinement iterations
        },
        context,
    )

    print(f"\n✅ Execution Success: {result1.get('execution_success', False)}")
    print(f"🔄 Iterations Used: {result1.get('iterations_used', 'N/A')}")
    print(f"📚 Strategies Learned: {result1.get('strategies_learned', 0)}")
    print(f"📈 Playbook Size: {result1.get('playbook_size', 0)}")
    print(f"📊 Improvement Score: {result1.get('improvement_score', 0.0):.2%}")

    if result1.get("code_generated"):
        print("\n📝 Final Generated Code:")
        print("-" * 70)
        print(result1.get("code_generated", "No code generated"))
        print("-" * 70)

    print("\n" + "=" * 70)
    print()

    # Test 2: Task with known API (should succeed faster)
    print("📝 Test 2: Well-Defined Task (Expected to succeed quickly)")
    print("-" * 70)
    print("Task: Create a simple calculator class")
    print("Expected: Should succeed in 1-2 iterations")
    print()

    result2 = await learner.execute(
        {
            "task": "Create a Calculator class with add, subtract, multiply, divide methods",
            "language": "python",
            "context": "Include error handling for division by zero and type checking",
            "max_iterations": 3,
        },
        context,
    )

    print(f"\n✅ Execution Success: {result2.get('execution_success', False)}")
    print(f"🔄 Iterations Used: {result2.get('iterations_used', 'N/A')}")
    print(f"📚 Strategies Learned: {result2.get('strategies_learned', 0)}")
    print(f"📈 Playbook Size: {result2.get('playbook_size', 0)}")
    print(f"📊 Improvement Score: {result2.get('improvement_score', 0.0):.2%}")

    print("\n" + "=" * 70)
    print()

    # Summary
    print("📊 Phase 3 Iterative Refinement Summary")
    print("=" * 70)
    print("Total Tests: 2")
    print(f"Test 1 Success: {result1.get('execution_success', False)}")
    print(f"Test 2 Success: {result2.get('execution_success', False)}")
    print(
        f"Total Strategies Learned: {result1.get('strategies_learned', 0) + result2.get('strategies_learned', 0)}"
    )
    print(f"Final Playbook Size: {result2.get('playbook_size', 0)}")
    print()
    print("✨ Phase 3 Demo Complete!")
    print()
    print("Key Learnings:")
    print("1. Error feedback loop enables automatic refinement")
    print("2. LLM learns from execution failures")
    print("3. Strategies accumulate in playbook for future use")
    print("4. Each iteration improves code quality")
    print()
    print("Next Steps:")
    print("- Apply to CachePrimitive test generation")
    print("- Measure improvement over multiple iterations")
    print("- Build reusable playbooks for common patterns")


if __name__ == "__main__":
    asyncio.run(demo_iterative_refinement())
