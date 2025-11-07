#!/usr/bin/env python3
"""
ACE + E2B: Generate Comprehensive Tests for CachePrimitive

Real TODO completion using self-learning code generation.

This example demonstrates:
- Generating pytest tests for production code
- Validating tests through E2B execution
- Learning from test failures
- Iterating until comprehensive coverage

TODO Being Completed:
- TODO Add comprehensive tests for CachePrimitive #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  component:: CachePrimitive

Run with: python examples/ace_cache_primitive_tests.py
"""

import asyncio
import logging
from pathlib import Path

from tta_dev_primitives.ace import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test scenarios to generate
TEST_SCENARIOS = [
    {
        "id": "cache_hit_miss",
        "name": "Cache Hit and Miss Scenarios",
        "description": "Generate tests for basic cache hit/miss behavior",
        "task": """Create pytest tests for CachePrimitive that validate:
1. Cache miss on first access (executes primitive)
2. Cache hit on second access (returns cached value, doesn't execute primitive)
3. Multiple cache hits return same cached value
4. Different cache keys result in different cached values

Use pytest-asyncio and mock the wrapped primitive to verify execution counts.
Import: from tta_dev_primitives.performance import CachePrimitive
Import: from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
Import: from tta_dev_primitives.testing import MockPrimitive

Test class name: TestCacheHitMiss
""",
        "language": "python",
        "validation": "Tests must use pytest-asyncio, have proper imports, and test cache hit/miss logic",
    },
    {
        "id": "ttl_expiration",
        "name": "TTL Expiration Tests",
        "description": "Generate tests for time-to-live expiration",
        "task": """Create pytest tests for CachePrimitive TTL expiration that validate:
1. Cached value is returned before TTL expires
2. Cached value expires after TTL seconds
3. Expired entry is removed from cache
4. New execution happens after expiration
5. Statistics track expirations correctly

Use asyncio.sleep() to simulate time passing, or mock time.time().
Test TTL values: 0.1 seconds (fast tests), 1 second, 5 seconds

Test class name: TestCacheTTLExpiration
""",
        "language": "python",
        "validation": "Tests must handle async time delays and verify TTL behavior",
    },
    {
        "id": "statistics_tracking",
        "name": "Statistics Tracking Tests",
        "description": "Generate tests for cache statistics",
        "task": """Create pytest tests for CachePrimitive statistics that validate:
1. get_stats() returns correct structure (size, hits, misses, expirations, hit_rate)
2. Hit count increments on cache hits
3. Miss count increments on cache misses
4. Expiration count increments when entries expire
5. Hit rate calculation is correct (hits / (hits + misses) * 100)
6. Hit rate is 0.0 when no accesses yet
7. clear_cache() resets cache but preserves stats

Test class name: TestCacheStatistics
""",
        "language": "python",
        "validation": "Tests must verify all statistics fields and calculations",
    },
    {
        "id": "edge_cases",
        "name": "Edge Cases and Error Handling",
        "description": "Generate tests for edge cases",
        "task": """Create pytest tests for CachePrimitive edge cases that validate:
1. Empty cache returns correct stats (size=0, hits=0, misses=0)
2. Cache key function can handle various input types (dict, str, int)
3. Cache works with None as input_data
4. Cache works with empty dict as input_data
5. Very long cache keys are handled (truncated in logs)
6. Concurrent access to same cache key (use asyncio.gather)
7. evict_expired() manually removes expired entries

Test class name: TestCacheEdgeCases
""",
        "language": "python",
        "validation": "Tests must cover edge cases and concurrent access patterns",
    },
]


async def generate_cache_primitive_tests():
    """Generate comprehensive tests for CachePrimitive using ACE + E2B."""

    print("🎯 ACE + E2B: CachePrimitive Test Generation")
    print("=" * 70)
    print("Completing TODO: Add comprehensive tests for CachePrimitive\n")

    # Initialize self-learning primitive
    playbook_file = Path("cache_primitive_tests_playbook.json")
    learner = SelfLearningCodePrimitive(playbook_file=playbook_file)

    # Create context
    context = WorkflowContext(correlation_id="cache-primitive-tests")

    # Track all generated tests
    all_tests = []
    total_iterations = 0
    total_strategies = 0

    # Generate tests for each scenario
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{'=' * 70}")
        print(f"📝 Scenario {i}/{len(TEST_SCENARIOS)}: {scenario['name']}")
        print(f"{'=' * 70}")
        print(f"Description: {scenario['description']}\n")

        try:
            # Generate tests
            result = await learner.execute(
                {
                    "task": scenario["task"],
                    "language": scenario["language"],
                    "context": scenario["description"],
                    "max_iterations": 5,
                },
                context,
            )

            # Track results
            iterations = result.get("iterations_used", 0)
            strategies = result.get("strategies_learned", 0)
            total_iterations += iterations
            total_strategies += strategies

            print("\n✅ Scenario complete:")
            print(f"   Iterations: {iterations}")
            print(f"   Strategies learned: {strategies}")
            print(f"   Execution success: {result['execution_success']}")

            if result.get("code_generated"):
                all_tests.append(
                    {
                        "scenario": scenario["name"],
                        "code": result["code_generated"],
                        "success": result["execution_success"],
                    }
                )

        except Exception as e:
            logger.error(f"Failed to generate tests for {scenario['name']}: {e}")
            print(f"\n❌ Scenario failed: {e}")

    # Print summary
    print(f"\n{'=' * 70}")
    print("📊 Test Generation Summary")
    print(f"{'=' * 70}")
    print(f"Scenarios completed: {len(all_tests)}/{len(TEST_SCENARIOS)}")
    print(f"Total iterations: {total_iterations}")
    print(f"Total strategies learned: {total_strategies}")
    print(f"Playbook size: {learner.playbook_size} strategies")
    print(f"Success rate: {learner.success_rate:.1%}")

    # Save combined test file
    if all_tests:
        output_file = Path(
            "packages/tta-dev-primitives/tests/performance/test_cache_primitive_comprehensive.py"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Combine all test code
        combined_code = '"""Comprehensive tests for CachePrimitive.\n\n'
        combined_code += "Generated by ACE + E2B self-learning system.\n"
        combined_code += f"Total scenarios: {len(all_tests)}\n"
        combined_code += f"Total iterations: {total_iterations}\n"
        combined_code += f"Strategies learned: {total_strategies}\n"
        combined_code += '"""\n\n'

        for test in all_tests:
            combined_code += f"# {test['scenario']}\n"
            combined_code += test["code"]
            combined_code += "\n\n"

        output_file.write_text(combined_code)
        print(f"\n📁 Tests saved to: {output_file}")

    return {
        "scenarios_completed": len(all_tests),
        "total_iterations": total_iterations,
        "total_strategies": total_strategies,
        "playbook_size": learner.playbook_size,
        "success_rate": learner.success_rate,
        "output_file": str(output_file) if all_tests else None,
    }


async def main():
    """Run the test generation workflow."""
    try:
        results = await generate_cache_primitive_tests()

        print("\n✨ Test Generation Complete!")
        print("\nNext Steps:")
        print("1. Review generated tests in packages/tta-dev-primitives/tests/performance/")
        print(
            "2. Run tests: uv run pytest packages/tta-dev-primitives/tests/performance/test_cache_primitive_comprehensive.py -v"
        )
        print("3. Update Logseq TODO to DONE with metrics")
        print("4. Commit tests to repository")

        return results

    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        print(f"\n❌ Test generation failed: {e}")
        print("Make sure E2B_API_KEY is set in your environment")
        raise


if __name__ == "__main__":
    asyncio.run(main())
