"""Demo: AdaptiveFallbackPrimitive learning optimal fallback strategies.

This demo shows how AdaptiveFallbackPrimitive learns which fallback chains
work best for different failure scenarios.

Scenarios:
1. Unreliable Primary - Frequent failures, learns to use fast fallback first
2. Context-Specific Patterns - Different optimal orders for prod vs dev
3. Progressive Learning - Fallback order improves over time
"""

import asyncio
import random
import time
from typing import Any

from tta_dev_primitives.adaptive import AdaptiveFallbackPrimitive, LearningMode
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class UnreliableService(InstrumentedPrimitive):
    """Mock service that fails randomly."""

    def __init__(self, name: str, failure_rate: float = 0.5, latency_ms: float = 100):
        super().__init__()
        self.name = name
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.call_count = 0

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(self.latency_ms / 1000.0)

        if random.random() < self.failure_rate:
            raise Exception(f"{self.name} failed (random failure)")

        return {
            "service": self.name,
            "result": f"Success from {self.name}",
            "timestamp": time.time(),
        }


async def scenario_1_unreliable_primary():
    """Scenario 1: Primary fails often, learn to use fast fallback first."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Unreliable Primary - Learning Fast Fallback Priority")
    print("=" * 80)

    # Create services with different characteristics
    primary = UnreliableService(
        "Primary", failure_rate=0.8, latency_ms=50
    )  # Fails often
    fallback_slow = UnreliableService("SlowBackup", failure_rate=0.3, latency_ms=200)
    fallback_fast = UnreliableService("FastBackup", failure_rate=0.2, latency_ms=50)
    fallback_local = UnreliableService("LocalCache", failure_rate=0.1, latency_ms=10)

    # Create adaptive fallback
    adaptive_fallback = AdaptiveFallbackPrimitive(
        primary=primary,
        fallbacks={
            "slow_backup": fallback_slow,
            "fast_backup": fallback_fast,
            "local_cache": fallback_local,
        },
        learning_mode=LearningMode.ACTIVE,
        min_observations_before_learning=10,
    )

    print("\n📊 Initial Baseline:")
    stats = adaptive_fallback.get_fallback_stats()
    print(
        f"Baseline fallback order: {adaptive_fallback.baseline_strategy.parameters['fallback_order']}"
    )

    # Run 30 requests
    print("\n🚀 Running 30 requests...")
    successes = 0
    failures = 0

    for i in range(30):
        try:
            context = WorkflowContext(
                correlation_id=f"req-{i}",
                data={"environment": "production", "request_id": i},
            )
            result = await adaptive_fallback.execute({"query": f"request-{i}"}, context)
            successes += 1
            if i % 10 == 9:
                print(f"  Request {i + 1}/30: ✅ Success ({result['service']})")
        except Exception:
            failures += 1
            if i % 10 == 9:
                print(f"  Request {i + 1}/30: ❌ Failed")

    # Show results
    print("\n📈 Results:")
    print(f"  Successes: {successes}/30 ({successes / 30 * 100:.1f}%)")
    print(f"  Failures: {failures}/30 ({failures / 30 * 100:.1f}%)")

    stats = adaptive_fallback.get_fallback_stats()
    print("\n📊 Learned Fallback Statistics:")
    print(f"  Primary attempts: {stats['primary_attempts']}")
    print(
        f"  Primary failures: {stats['primary_failures']} ({stats['primary_failure_rate'] * 100:.1f}%)"
    )
    print("\n  Fallback Performance:")
    for name, fb_stats in stats["fallbacks"].items():
        print(
            f"    {name}: {fb_stats['successes']}/{fb_stats['attempts']} "
            f"({fb_stats['success_rate'] * 100:.1f}% success, "
            f"{fb_stats['avg_latency_ms']:.1f}ms avg latency)"
        )

    print("\n🎯 Optimal Fallback Order (learned):")
    print(f"  {stats['best_fallback_order']}")

    print("\n💡 Active Strategies:")
    for strategy_name, strategy_info in stats["strategies"].items():
        print(
            f"  {strategy_name}: {strategy_info['fallback_order']} "
            f"({strategy_info['success_rate'] * 100:.1f}% success)"
        )


async def scenario_2_context_specific():
    """Scenario 2: Different optimal orders for production vs development."""
    print("\n" + "=" * 80)
    print(
        "SCENARIO 2: Context-Specific Learning - Different Strategies per Environment"
    )
    print("=" * 80)

    # Production: Cloud services work better
    primary = UnreliableService("Primary", failure_rate=0.7, latency_ms=50)
    cloud_backup = UnreliableService(
        "CloudBackup", failure_rate=0.2, latency_ms=100
    )  # Good in prod
    local_backup = UnreliableService(
        "LocalBackup", failure_rate=0.6, latency_ms=50
    )  # Bad in prod

    adaptive_fallback = AdaptiveFallbackPrimitive(
        primary=primary,
        fallbacks={
            "cloud_backup": cloud_backup,
            "local_backup": local_backup,
        },
        learning_mode=LearningMode.ACTIVE,
        min_observations_before_learning=8,
    )

    # Run production requests
    print("\n🏭 Running 15 PRODUCTION requests...")
    prod_successes = 0
    for i in range(15):
        try:
            context = WorkflowContext(
                correlation_id=f"prod-{i}",
                data={"environment": "production"},
            )
            await adaptive_fallback.execute({"query": f"prod-{i}"}, context)
            prod_successes += 1
        except Exception:
            pass

    print(
        f"  Production success: {prod_successes}/15 ({prod_successes / 15 * 100:.1f}%)"
    )

    # Switch: In development, local works better
    cloud_backup.failure_rate = 0.6  # Cloud worse in dev
    local_backup.failure_rate = 0.2  # Local better in dev

    # Run development requests
    print("\n💻 Running 15 DEVELOPMENT requests...")
    dev_successes = 0
    for i in range(15):
        try:
            context = WorkflowContext(
                correlation_id=f"dev-{i}",
                data={"environment": "development"},
            )
            await adaptive_fallback.execute({"query": f"dev-{i}"}, context)
            dev_successes += 1
        except Exception:
            pass

    print(
        f"  Development success: {dev_successes}/15 ({dev_successes / 15 * 100:.1f}%)"
    )

    # Show context-specific learning
    stats = adaptive_fallback.get_fallback_stats()
    print("\n📊 Context-Specific Statistics:")
    for ctx_name, ctx_stats in stats["contexts"].items():
        print(f"\n  {ctx_name.upper()} environment:")
        print(
            f"    Primary: {ctx_stats['primary_failures']}/{ctx_stats['primary_attempts']} failures"
        )
        print("    Fallback usage:")
        for fb_name, usage in ctx_stats["fallback_usage"].items():
            successes = ctx_stats["fallback_successes"][fb_name]
            success_rate = successes / usage if usage > 0 else 0
            print(
                f"      {fb_name}: {successes}/{usage} ({success_rate * 100:.1f}% success)"
            )

    print("\n🎯 Learned Strategies:")
    for strategy_name, strategy_info in stats["strategies"].items():
        print(f"  {strategy_name}: {strategy_info['fallback_order']}")


async def scenario_3_progressive_learning():
    """Scenario 3: Watch fallback order improve over time."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Progressive Learning - Fallback Order Optimization")
    print("=" * 80)

    # Create services with clear quality differences
    primary = UnreliableService(
        "Primary", failure_rate=0.9, latency_ms=50
    )  # Fails almost always
    fallback_a = UnreliableService(
        "FallbackA", failure_rate=0.5, latency_ms=100
    )  # Medium
    fallback_b = UnreliableService(
        "FallbackB", failure_rate=0.2, latency_ms=80
    )  # Best success
    fallback_c = UnreliableService(
        "FallbackC", failure_rate=0.4, latency_ms=150
    )  # Slow

    adaptive_fallback = AdaptiveFallbackPrimitive(
        primary=primary,
        fallbacks={
            "fallback_a": fallback_a,
            "fallback_b": fallback_b,
            "fallback_c": fallback_c,
        },
        learning_mode=LearningMode.ACTIVE,
        min_observations_before_learning=5,
    )

    print("\n📊 Initial state:")
    stats = adaptive_fallback.get_fallback_stats()
    print(
        f"Baseline order: {adaptive_fallback.baseline_strategy.parameters['fallback_order']}"
    )

    # Run in batches to see progression
    for batch in range(1, 4):
        print(f"\n🔄 Batch {batch} - Running 10 requests...")
        batch_successes = 0

        for i in range(10):
            try:
                context = WorkflowContext(
                    correlation_id=f"batch{batch}-{i}",
                    data={"environment": "production"},
                )
                await adaptive_fallback.execute({"query": f"req-{i}"}, context)
                batch_successes += 1
            except Exception:
                pass

        stats = adaptive_fallback.get_fallback_stats()
        print(f"  Success rate: {batch_successes}/10 ({batch_successes * 10:.0f}%)")
        print(f"  Current best order: {stats['best_fallback_order']}")

        # Show fallback stats
        print("  Fallback performance:")
        for name, fb_stats in stats["fallbacks"].items():
            if fb_stats["attempts"] > 0:
                print(
                    f"    {name}: {fb_stats['success_rate'] * 100:.1f}% success "
                    f"({fb_stats['avg_latency_ms']:.1f}ms latency)"
                )

    print("\n🎉 Final Results:")
    print(f"  Total primary attempts: {stats['primary_attempts']}")
    print(f"  Optimal fallback order learned: {stats['best_fallback_order']}")
    print(
        "  Expected: ['fallback_b', 'fallback_a', 'fallback_c'] (b has best success + good latency)"
    )


async def main():
    """Run all demo scenarios."""
    print("\n" + "=" * 80)
    print("AdaptiveFallbackPrimitive Demo")
    print("Learning Optimal Fallback Strategies from Execution Patterns")
    print("=" * 80)

    await scenario_1_unreliable_primary()
    await scenario_2_context_specific()
    await scenario_3_progressive_learning()

    print("\n" + "=" * 80)
    print("✅ Demo Complete!")
    print("=" * 80)
    print(
        """
Key Takeaways:
1. AdaptiveFallbackPrimitive learns which fallbacks work best
2. Different contexts (prod/dev) can have different optimal orders
3. Learning improves over time as more patterns are observed
4. Strategies balance success rate (70%) and latency (30%)
"""
    )


if __name__ == "__main__":
    asyncio.run(main())
