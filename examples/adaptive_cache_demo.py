"""
Demo: AdaptiveCachePrimitive - Learn Optimal TTL

This demo shows how AdaptiveCachePrimitive automatically learns optimal
cache TTL values for different query patterns.

Scenario:
- Fast queries: Quick lookups that get reused frequently (benefit from longer TTL)
- Slow queries: Complex operations that change often (benefit from shorter TTL)
- The adaptive cache learns optimal TTL for each pattern
"""

import asyncio
import random
import time

from tta_dev_primitives.adaptive import AdaptiveCachePrimitive, LearningMode
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class SlowDatabaseQuery(InstrumentedPrimitive[dict, dict]):
    """Simulates a slow database query."""

    def __init__(self):
        super().__init__()
        self.call_count = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute a slow query (simulated)."""
        self.call_count += 1
        query_type = input_data.get("type", "default")

        # Simulate query execution time
        if query_type == "fast":
            await asyncio.sleep(0.1)  # Fast query: 100ms
        else:
            await asyncio.sleep(0.5)  # Slow query: 500ms

        return {
            "result": f"Query result for {query_type}",
            "timestamp": time.time(),
            "call_number": self.call_count,
        }


async def demo_adaptive_cache_learning():
    """Demonstrate adaptive cache learning optimal TTL."""

    print("=" * 70)
    print("AdaptiveCachePrimitive - Learning Optimal TTL")
    print("=" * 70)
    print()

    # Create the primitive to cache
    db_query = SlowDatabaseQuery()

    # Create adaptive cache
    adaptive_cache = AdaptiveCachePrimitive(
        target_primitive=db_query,
        cache_key_fn=lambda data, ctx: f"{data['type']}:{data.get('id', 'default')}",
        learning_mode=LearningMode.ACTIVE,  # Learn and adapt strategies
    )

    print("📊 Initial Strategy:")
    print(f"  Name: {adaptive_cache.baseline_strategy.name}")
    print(f"  TTL: {adaptive_cache.baseline_strategy.parameters['ttl_seconds']}s (default)")
    print()

    # Scenario 1: Fast queries with high reuse (benefit from longer TTL)
    print("🔵 Scenario 1: Fast Queries (High Reuse Pattern)")
    print("-" * 70)

    fast_context = WorkflowContext(metadata={"environment": "production", "type": "fast"})

    # Simulate 30 fast queries with high reuse (same IDs repeated)
    print("Executing 30 fast queries with high reuse...")
    fast_query_ids = [1, 2, 3, 4, 5] * 6  # Repeat 5 IDs 6 times each

    for i, query_id in enumerate(fast_query_ids, 1):
        _ = await adaptive_cache.execute({"type": "fast", "id": query_id}, fast_context)

        if i % 10 == 0:
            stats = adaptive_cache.get_cache_stats()
            fast_ctx_key = "production_fast"
            if fast_ctx_key in stats["contexts"]:
                ctx_stats = stats["contexts"][fast_ctx_key]
                print(
                    f"  After {i} queries: "
                    f"Hit Rate={ctx_stats['hit_rate']:.1%}, "
                    f"Avg Hit Age={ctx_stats['avg_hit_age']:.1f}s, "
                    f"DB Calls={db_query.call_count}"
                )

    print()
    print(f"✅ Fast queries completed. Total DB calls: {db_query.call_count}")
    print()

    # Check if new strategy was learned
    print("📈 Learned Strategies:")
    for name, strategy in adaptive_cache.strategies.items():
        print(f"  {name}:")
        print(f"    TTL: {strategy.parameters['ttl_seconds']:.0f}s")
        print(f"    Success Rate: {strategy.metrics.success_rate:.1%}")
        print(f"    Description: {strategy.description}")
    print()

    # Scenario 2: Slow queries with low reuse (benefit from shorter TTL)
    print("🟡 Scenario 2: Slow Queries (Low Reuse Pattern)")
    print("-" * 70)

    slow_context = WorkflowContext(metadata={"environment": "production", "type": "slow"})

    # Reset call count to isolate slow query metrics
    db_calls_before_slow = db_query.call_count

    # Simulate 20 slow queries with low reuse (mostly unique IDs)
    print("Executing 20 slow queries with low reuse...")
    for i in range(20):
        # Mostly unique IDs with occasional repeats
        query_id = random.randint(100, 200) if random.random() > 0.3 else random.randint(100, 105)
        _ = await adaptive_cache.execute({"type": "slow", "id": query_id}, slow_context)

        if (i + 1) % 10 == 0:
            stats = adaptive_cache.get_cache_stats()
            slow_ctx_key = "production_slow"
            if slow_ctx_key in stats["contexts"]:
                ctx_stats = stats["contexts"][slow_ctx_key]
                print(
                    f"  After {i + 1} queries: "
                    f"Hit Rate={ctx_stats['hit_rate']:.1%}, "
                    f"DB Calls={db_query.call_count - db_calls_before_slow}"
                )

    print()
    print(
        f"✅ Slow queries completed. Total new DB calls: {db_query.call_count - db_calls_before_slow}"
    )
    print()

    # Final statistics
    print("=" * 70)
    print("📊 Final Statistics & Learned Behaviors")
    print("=" * 70)
    print()

    stats = adaptive_cache.get_cache_stats()

    print("Overall Cache Performance:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Total Hits: {stats['total_hits']}")
    print(f"  Total Misses: {stats['total_misses']}")
    print(f"  Overall Hit Rate: {stats['overall_hit_rate']:.1%}")
    print(f"  Cache Size: {stats['total_size']} entries")
    print()

    print("Per-Context Performance:")
    for context_key, ctx_stats in stats["contexts"].items():
        print(f"  {context_key}:")
        print(f"    Executions: {ctx_stats['executions']}")
        print(f"    Hit Rate: {ctx_stats['hit_rate']:.1%}")
        print(f"    Avg Hit Age: {ctx_stats['avg_hit_age']:.1f}s")
    print()

    print("Learned Strategies (vs Baseline):")
    baseline_ttl = 3600.0  # Default
    for name, strategy in adaptive_cache.strategies.items():
        learned_ttl = strategy.parameters["ttl_seconds"]
        ttl_change = ((learned_ttl - baseline_ttl) / baseline_ttl) * 100

        print(f"  {name}:")
        print(f"    TTL: {learned_ttl:.0f}s ({ttl_change:+.0f}% vs baseline)")
        print(f"    Context: {strategy.context_pattern}")
        print(f"    Rationale: {strategy.description}")
    print()

    # Cost savings
    total_queries = stats["total_requests"]
    cache_hits = stats["total_hits"]
    cache_savings = (cache_hits / total_queries * 100) if total_queries > 0 else 0

    print("💰 Cost Impact:")
    print(f"  Total Queries: {total_queries}")
    print(f"  Queries Served from Cache: {cache_hits} ({cache_savings:.1f}%)")
    print(f"  Database Calls Avoided: {cache_hits}")
    print(
        f"  Total Database Calls Made: {db_query.call_count} (vs {total_queries} without caching)"
    )
    print()


async def demo_cache_adaptation():
    """Show how cache adapts TTL over time."""

    print("=" * 70)
    print("Cache Adaptation Over Time")
    print("=" * 70)
    print()

    db_query = SlowDatabaseQuery()

    adaptive_cache = AdaptiveCachePrimitive(
        target_primitive=db_query,
        cache_key_fn=lambda data, ctx: f"user:{data.get('user_id')}",
        learning_mode=LearningMode.ACTIVE,
    )

    context = WorkflowContext(metadata={"environment": "production"})

    print("Phase 1: High Reuse Pattern (Same users repeatedly)")
    for round_num in range(3):
        print(f"\n  Round {round_num + 1}:")

        # Execute queries for 5 users, 10 times each
        for _ in range(10):
            for user_id in range(5):
                await adaptive_cache.execute({"user_id": user_id}, context)

        stats = adaptive_cache.get_cache_stats()
        if stats["contexts"]:
            ctx_key = list(stats["contexts"].keys())[0]
            ctx_stats = stats["contexts"][ctx_key]
            print(
                f"    Hit Rate: {ctx_stats['hit_rate']:.1%}, "
                f"Avg Hit Age: {ctx_stats['avg_hit_age']:.1f}s"
            )

        # Check strategies for the production context
        strategies_info = []
        for name, strategy in adaptive_cache.strategies.items():
            if strategy.context_pattern == "production":
                ttl = strategy.parameters["ttl_seconds"]
                strategies_info.append(f"{name} (TTL: {ttl:.0f}s)")

        if strategies_info:
            print(f"    Active Strategies: {', '.join(strategies_info)}")
        else:
            print(
                f"    Using Baseline TTL: {adaptive_cache.baseline_strategy.parameters['ttl_seconds']:.0f}s"
            )

    print()
    print("✅ Adaptive cache learned optimal TTL based on reuse patterns!")
    print()


async def main():
    """Run all demos."""

    # Demo 1: Learning optimal TTL
    await demo_adaptive_cache_learning()

    print("\n" * 2)

    # Demo 2: Adaptation over time
    await demo_cache_adaptation()

    print()
    print("=" * 70)
    print("✅ All Demos Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  • AdaptiveCachePrimitive learns context-specific TTL values")
    print("  • High-reuse queries get longer TTL (better hit rates)")
    print("  • Low-reuse queries get shorter TTL (less memory waste)")
    print("  • Adapts automatically based on actual usage patterns")
    print("  • Maintains safety with validation and circuit breakers")
    print()


if __name__ == "__main__":
    asyncio.run(main())
