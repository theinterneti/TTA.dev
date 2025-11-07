"""
ACE + E2B: CachePrimitive Test Generation with Phase 3 Iterative Refinement

This script demonstrates the full ACE system with:
1. Source code injection (prevents API hallucination)
2. Iterative refinement (fixes errors automatically)
3. Strategy learning (improves over time)

Expected: 90%+ test pass rate after 2-3 iterations
"""

import asyncio
from pathlib import Path

from tta_dev_primitives.ace.cognitive_manager import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Read CachePrimitive source code to inject into prompts
CACHE_PRIMITIVE_SOURCE = """
class CachePrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        primitive: WorkflowPrimitive,
        cache_key_fn: Callable[[Any, WorkflowContext], str],
        ttl_seconds: float = 3600.0,
    ) -> None:
        '''Initialize cache primitive.
        
        Args:
            primitive: Primitive to cache
            cache_key_fn: Function to generate cache key from input/context
            ttl_seconds: Time-to-live for cached values (default 1 hour)
        '''
        self.primitive = primitive
        self.cache_key_fn = cache_key_fn
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}
        self._stats = {"hits": 0, "misses": 0, "expirations": 0}

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        '''Execute with caching.'''
        cache_key = self.cache_key_fn(input_data, context)
        # ... caching logic ...
        
    def get_stats(self) -> dict[str, int]:
        '''Get cache statistics.'''
        return self._stats.copy()
"""


async def main():
    """Generate comprehensive tests for CachePrimitive with Phase 3."""

    print("🎯 ACE + E2B: CachePrimitive Test Generation (Phase 3)")
    print("=" * 70)
    print("Completing TODO: Add comprehensive tests for CachePrimitive")
    print()
    print("Phase 3 Enhancements:")
    print("✅ Source code injection (prevents API hallucination)")
    print("✅ Iterative refinement (fixes errors automatically)")
    print("✅ Up to 3 iterations per scenario")
    print()
    print("=" * 70)
    print()

    # Initialize learner
    learner = SelfLearningCodePrimitive(
        playbook_file=Path("cache_primitive_tests_playbook_phase3.json")
    )
    context = WorkflowContext(correlation_id="cache-tests-phase3")

    # Test scenarios
    scenarios = [
        {
            "name": "Cache Hit and Miss Scenarios",
            "task": "Generate pytest tests for CachePrimitive cache hit/miss behavior",
            "context": f"""Create comprehensive pytest tests that validate:
1. Cache miss on first access (primitive executed)
2. Cache hit on second access (primitive NOT executed)
3. Different cache keys result in different cached values

Use the actual CachePrimitive API shown in the reference source code.

Reference Source Code:
{CACHE_PRIMITIVE_SOURCE}

IMPORTANT: Use the exact API from the reference code:
- Constructor: CachePrimitive(primitive=..., cache_key_fn=..., ttl_seconds=...)
- Method: await cache.execute(input_data, context)
- NOT: wrapped_primitive, run(), get()
""",
        },
        {
            "name": "TTL Expiration Tests",
            "task": "Generate pytest tests for CachePrimitive TTL expiration",
            "context": f"""Create tests that validate time-to-live expiration:
1. Cached value returned before TTL expires
2. Primitive re-executed after TTL expires
3. Statistics track expirations correctly

Reference Source Code:
{CACHE_PRIMITIVE_SOURCE}

Use exact API: CachePrimitive(primitive=..., cache_key_fn=..., ttl_seconds=...)
""",
        },
    ]

    all_tests_code = []
    total_strategies = 0

    for i, scenario in enumerate(scenarios, 1):
        print(f"📝 Scenario {i}/{len(scenarios)}: {scenario['name']}")
        print("-" * 70)
        print(f"Description: {scenario['task']}")
        print()

        result = await learner.execute(
            {
                "task": scenario["task"],
                "language": "python",
                "context": scenario["context"],
                "max_iterations": 3,  # Phase 3: Allow up to 3 refinement iterations
            },
            context,
        )

        print(f"✅ Execution Success: {result.get('execution_success', False)}")
        print(f"🔄 Iterations: {result.get('iterations_used', 'N/A')}")
        print(f"📚 Strategies Learned: {result.get('strategies_learned', 0)}")
        print()

        if result.get("code_generated"):
            all_tests_code.append(f"# {scenario['name']}\n{result['code_generated']}\n")

        total_strategies += result.get("strategies_learned", 0)

    # Save generated tests
    output_file = Path(
        "packages/tta-dev-primitives/tests/performance/test_cache_primitive_phase3.py"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write('"""Comprehensive tests for CachePrimitive (Phase 3).\n\n')
        f.write("Generated by ACE + E2B with iterative refinement.\n")
        f.write(f"Total scenarios: {len(scenarios)}\n")
        f.write(f"Strategies learned: {total_strategies}\n")
        f.write('"""\n\n')
        f.write("\n\n".join(all_tests_code))

    print("=" * 70)
    print("📊 Test Generation Summary (Phase 3)")
    print("=" * 70)
    print(f"Scenarios completed: {len(scenarios)}/{len(scenarios)}")
    print(f"Total strategies learned: {total_strategies}")
    print(f"Tests saved to: {output_file}")
    print()
    print("✨ Test Generation Complete!")
    print()
    print("Next Steps:")
    print("1. Run tests: uv run pytest", output_file, "-v")
    print("2. Measure pass rate (expected: 90%+)")
    print("3. Compare to Phase 2 results (24% pass rate)")


if __name__ == "__main__":
    asyncio.run(main())

