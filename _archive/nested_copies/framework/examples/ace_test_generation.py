#!/usr/bin/env python3
"""
ACE + E2B Test Generation Example

Demonstrates self-learning test generation that improves through actual execution.
The primitive learns what makes tests pass and accumulates testing strategies.

This example generates pytest tests for TTA.dev's CachePrimitive and validates
them by actually running them in E2B sandboxes.

Run with: python examples/ace_test_generation.py
"""

import asyncio
import logging
from pathlib import Path

from tta_dev_primitives.ace import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_cache_primitive_tests():
    """Generate comprehensive tests for CachePrimitive using ACE + E2B."""

    print("🧪 ACE + E2B Test Generation Demo")
    print("=" * 60)
    print("Target: CachePrimitive from tta-dev-primitives")
    print()

    # Create self-learning test generator
    test_generator = SelfLearningCodePrimitive(playbook_file=Path("test_generation_playbook.json"))

    context = WorkflowContext(
        correlation_id="test-gen-cache-primitive",
        metadata={"target": "CachePrimitive", "package": "tta-dev-primitives"},
    )

    # Test scenarios to generate
    test_scenarios = [
        {
            "task": "Generate pytest test for cache hit scenario",
            "language": "python",
            "context": """
CachePrimitive caches results with TTL expiration.
Test should:
1. Create a CachePrimitive wrapping a mock primitive
2. Execute twice with same input
3. Verify second call is cached (faster, no primitive execution)
4. Check cache hit stats
""",
            "description": "Basic cache hit test",
        },
        {
            "task": "Generate pytest test for cache miss scenario",
            "language": "python",
            "context": """
CachePrimitive should execute primitive on cache miss.
Test should:
1. Create a CachePrimitive
2. Execute with unique input
3. Verify primitive was called
4. Check cache miss stats
""",
            "description": "Cache miss test",
        },
        {
            "task": "Generate pytest test for TTL expiration",
            "language": "python",
            "context": """
CachePrimitive expires entries after TTL.
Test should:
1. Create CachePrimitive with short TTL (e.g., 0.1 seconds)
2. Execute and cache result
3. Wait for TTL to expire
4. Execute again and verify cache miss
5. Check expiration stats
""",
            "description": "TTL expiration test",
        },
        {
            "task": "Generate pytest test for cache statistics",
            "language": "python",
            "context": """
CachePrimitive tracks hits, misses, and hit rate.
Test should:
1. Create CachePrimitive
2. Execute multiple times (mix of hits and misses)
3. Verify get_stats() returns correct counts
4. Verify hit_rate calculation is accurate
""",
            "description": "Statistics tracking test",
        },
    ]

    results = []
    total_strategies_learned = 0

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'=' * 60}")
        print(f"🎯 Test Scenario {i}/{len(test_scenarios)}: {scenario['description']}")
        print(f"{'=' * 60}")
        print(f"Current playbook: {test_generator.playbook_size} strategies")
        print(f"Success rate: {test_generator.success_rate:.1%}")
        print()

        try:
            result = await test_generator.execute(scenario, context)
            results.append(result)

            # Display results
            print(f"\n{'✅' if result['execution_success'] else '❌'} Generation Result:")
            print(f"  Execution: {'PASSED' if result['execution_success'] else 'FAILED'}")
            print(f"  Strategies learned: {result['strategies_learned']}")
            print(f"  Playbook size: {result['playbook_size']}")
            print(f"  Improvement: {result['improvement_score']:.1%}")
            print(f"  Summary: {result['learning_summary']}")

            total_strategies_learned += result["strategies_learned"]

            if result["code_generated"]:
                print("\n📝 Generated Test Code Preview:")
                lines = result["code_generated"].split("\n")[:15]
                for line in lines:
                    print(f"  {line}")
                if len(result["code_generated"].split("\n")) > 15:
                    print("  ...")

        except Exception as e:
            logger.error(f"Test generation {i} failed: {e}")
            print(f"❌ Failed: {e}")

    # Final summary
    print(f"\n{'=' * 60}")
    print("🏆 Test Generation Summary")
    print(f"{'=' * 60}")
    print(f"Total test scenarios: {len(test_scenarios)}")
    print(f"Successful generations: {sum(1 for r in results if r['execution_success'])}")
    print(f"Total strategies learned: {total_strategies_learned}")
    print(f"Final playbook size: {test_generator.playbook_size}")
    print(f"Final success rate: {test_generator.success_rate:.1%}")
    print()

    return results, test_generator


async def main():
    """Run the test generation demo."""

    print("🚀 ACE + E2B Test Generation Demo")
    print("Generating tests that actually work!\n")

    try:
        results, generator = await generate_cache_primitive_tests()

        print("\n✨ Demo Complete!")
        print("\nKey Insights:")
        print("• Generated tests are validated by actual execution")
        print("• Learning accumulates testing patterns that work")
        print("• Each iteration improves test quality")
        print("• Playbook persists knowledge across sessions")

        if generator.playbook_size > 0:
            print(f"\n📚 Learned {generator.playbook_size} testing strategies")
            print("Run again to see improved test generation!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("Make sure E2B_API_KEY is set in your environment")


if __name__ == "__main__":
    asyncio.run(main())
