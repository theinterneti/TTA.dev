#!/usr/bin/env python3
"""
ACE + E2B Integration Demo

Demonstrates self-learning code generation that improves through actual execution
feedback using Agentic Context Engine patterns with E2B sandboxes.

This shows the revolutionary combination of:
- ACE's self-reflection and learning patterns
- E2B's secure, fast code execution
- TTA.dev's primitive composition system

Run with: python examples/ace_e2b_demo.py
"""

import asyncio
import logging
from pathlib import Path

from tta_dev_primitives.ace import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_learning_progression():
    """Show how the primitive learns and improves over multiple executions."""

    print("🧠 ACE + E2B Self-Learning Demo")
    print("=" * 50)

    # Create a self-learning primitive
    learner = SelfLearningCodePrimitive(playbook_file=Path("ace_demo_playbook.json"))

    # Create workflow context
    context = WorkflowContext(
        correlation_id="ace-e2b-demo", metadata={"demo": "learning_progression"}
    )

    # Test scenarios that will drive learning
    test_scenarios = [
        {
            "task": "Create a function to calculate fibonacci numbers",
            "language": "python",
            "description": "Basic recursion test - may hit recursion limit",
        },
        {
            "task": "Create a function to calculate fibonacci numbers",
            "language": "python",
            "description": "Same task - should learn from previous attempt",
        },
        {
            "task": "Create a function to check if a number is prime",
            "language": "python",
            "description": "Different task - can reuse learned strategies",
        },
        {
            "task": "Create a function to generate prime numbers up to a limit",
            "language": "python",
            "description": "Related task - should benefit from prime checking knowledge",
        },
    ]

    results = []

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 Test {i}: {scenario['description']}")
        print(f"Task: {scenario['task']}")
        print(f"Current playbook size: {learner.playbook_size} strategies")
        print(f"Current success rate: {learner.success_rate:.1%}")

        try:
            result = await learner.execute(scenario, context)
            results.append(result)

            print(f"✅ Execution {'succeeded' if result['execution_success'] else 'failed'}")
            print(f"📚 Strategies learned this round: {result['strategies_learned']}")
            print(f"📈 New playbook size: {result['playbook_size']}")
            print(f"🎯 Success rate: {learner.success_rate:.1%}")
            print(f"📊 Improvement score: {result['improvement_score']:.1%}")

            if result["code_generated"]:
                print("🔧 Generated code preview:")
                code_lines = result["code_generated"].split("\n")[:5]
                for line in code_lines:
                    print(f"    {line}")
                if len(result["code_generated"].split("\n")) > 5:
                    print("    ...")

        except Exception as e:
            logger.error(f"Error in test {i}: {e}")
            print(f"❌ Test {i} failed with error: {e}")

    # Summary
    print("\n🏆 Final Results")
    print("=" * 50)
    print(f"Total executions: {learner.total_executions}")
    print(f"Successful executions: {learner.successful_executions}")
    print(f"Final success rate: {learner.success_rate:.1%}")
    print(f"Final playbook size: {learner.playbook_size} strategies")
    print(f"Overall improvement: {learner.improvement_score:.1%}")

    # Show learning summary
    if results:
        print("\n📋 Learning Summary:")
        for i, result in enumerate(results, 1):
            print(f"  Test {i}: {result['learning_summary']}")

    return results


async def demonstrate_specific_learning_patterns():
    """Show specific learning patterns that ACE + E2B enables."""

    print("\n🔬 Advanced Learning Patterns Demo")
    print("=" * 50)

    learner = SelfLearningCodePrimitive(playbook_file=Path("ace_advanced_playbook.json"))

    context = WorkflowContext(
        correlation_id="ace-patterns-demo", metadata={"demo": "learning_patterns"}
    )

    # Test error recovery learning
    print("\n1️⃣ Error Recovery Learning")
    print("Testing how ACE learns from execution failures...")

    error_scenario = {
        "task": "Create a function that calculates factorial of 1000",
        "language": "python",
        "context": "This will likely cause recursion issues, teaching error handling",
    }

    result = await learner.execute(error_scenario, context)
    print(f"Error recovery result: {result['learning_summary']}")

    # Test optimization learning
    print("\n2️⃣ Performance Optimization Learning")
    print("Testing how ACE learns performance patterns...")

    optimization_scenario = {
        "task": "Create a function to calculate fibonacci of 35",
        "language": "python",
        "context": "Performance-sensitive task that benefits from memoization",
    }

    result = await learner.execute(optimization_scenario, context)
    print(f"Optimization result: {result['learning_summary']}")

    return learner


async def demonstrate_playbook_inspection():
    """Show how to inspect what the ACE system has learned."""

    print("\n🔍 Playbook Inspection Demo")
    print("=" * 50)

    # Load an existing playbook if available
    playbook_file = Path("ace_demo_playbook.json")
    if playbook_file.exists():
        learner = SelfLearningCodePrimitive(playbook_file=playbook_file)

        print(f"📚 Playbook contains {learner.playbook_size} strategies")

        # Show some learned strategies
        print("\n🧠 Sample Learned Strategies:")
        for i, strategy in enumerate(learner.playbook.strategies[:5], 1):
            success_rate = strategy["successes"] / max(
                1, strategy["successes"] + strategy["failures"]
            )
            print(f"  {i}. Context: {strategy['context']}")
            print(f"     Strategy: {strategy['strategy']}")
            print(
                f"     Success rate: {success_rate:.1%} ({strategy['successes']} successes, {strategy['failures']} failures)"
            )
            print()

        if len(learner.playbook.strategies) > 5:
            print(f"     ... and {len(learner.playbook.strategies) - 5} more strategies")
    else:
        print("No existing playbook found. Run the main demo first to generate learnings.")


async def main():
    """Run the complete ACE + E2B demonstration."""

    print("🚀 Welcome to the ACE + E2B Integration Demo!")
    print("This demonstrates self-learning code generation that improves through execution.")
    print()

    try:
        # Basic learning progression
        await demonstrate_learning_progression()

        # Advanced patterns
        await demonstrate_specific_learning_patterns()

        # Playbook inspection
        await demonstrate_playbook_inspection()

        print("\n✨ Demo Complete!")
        print("Key takeaways:")
        print("• ACE learns strategies from actual execution results")
        print("• E2B provides safe, fast execution environments")
        print("• Strategies improve success rates over time")
        print("• Learning is observable and interpretable")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo encountered an error: {e}")
        print("This might be due to missing E2B configuration.")
        print("Make sure E2B_API_KEY is set in your environment.")


if __name__ == "__main__":
    asyncio.run(main())
