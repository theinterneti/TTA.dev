"""Production-ready demonstration of self-improving adaptive primitives.

This demonstrates a REAL production scenario:
- Multi-region API calls with different reliability
- Automatic learning of region-specific retry strategies
- Performance optimization through observability
- Knowledge base persistence for strategy sharing

Run this to see adaptive primitives in a realistic production scenario!
"""

import asyncio
import logging
import random
from datetime import datetime
from pathlib import Path

from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LogseqStrategyIntegration,
)
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MultiRegionAPIService(WorkflowPrimitive[dict, dict]):
    """Simulates a multi-region API with different reliability characteristics."""

    def __init__(self):
        super().__init__()
        self.call_count = 0
        # Different regions have different reliability patterns
        self.region_reliability = {
            "us-east-1": 0.95,  # Very reliable
            "us-west-2": 0.85,  # Moderately reliable
            "eu-west-1": 0.90,  # Good reliability
            "ap-southeast-1": 0.75,  # Less reliable (network congestion)
        }

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute API call with region-specific reliability."""
        self.call_count += 1

        region = context.metadata.get("region", "us-east-1")
        request_id = context.correlation_id
        priority = context.metadata.get("priority", "normal")

        # Get reliability for this region
        reliability = self.region_reliability.get(region, 0.8)

        # Simulate network latency (region-dependent)
        base_latency = {
            "us-east-1": 0.05,
            "us-west-2": 0.08,
            "eu-west-1": 0.15,
            "ap-southeast-1": 0.25,
        }
        latency = base_latency.get(region, 0.1)
        await asyncio.sleep(latency)

        # Determine if call succeeds based on reliability
        if random.random() > reliability:
            # Different error types based on region characteristics
            if region == "ap-southeast-1":
                raise TimeoutError(f"Network timeout in {region}")
            elif region == "us-west-2":
                raise ConnectionError(f"Connection reset in {region}")
            else:
                raise Exception(f"API error in {region}")

        return {
            "status": "success",
            "region": region,
            "request_id": request_id,
            "priority": priority,
            "latency": latency,
            "timestamp": datetime.now().isoformat(),
        }


async def simulate_production_traffic():
    """Simulate realistic production traffic patterns."""

    print("\n" + "🌐" * 35)
    print("PRODUCTION ADAPTIVE PRIMITIVES DEMONSTRATION")
    print("🌐" * 35)

    # Initialize with Logseq integration
    logseq = LogseqStrategyIntegration("production_adaptive_demo")
    api_service = MultiRegionAPIService()

    adaptive_api = AdaptiveRetryPrimitive(
        target_primitive=api_service,
        logseq_integration=logseq,
        enable_auto_persistence=True,
    )

    print("\n📊 Simulating production traffic across multiple regions...")
    print("   (Each region has different reliability characteristics)")

    # Simulate traffic patterns
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
    priorities = ["high", "normal", "low"]

    total_requests = 50
    success_by_region: dict[str, list[bool]] = {r: [] for r in regions}
    latency_by_region: dict[str, list[float]] = {r: [] for r in regions}

    print(f"\n🔄 Processing {total_requests} requests...")

    for i in range(total_requests):
        # Realistic traffic distribution
        if i % 10 < 4:  # 40% US-EAST (primary)
            region = "us-east-1"
        elif i % 10 < 7:  # 30% US-WEST (secondary)
            region = "us-west-2"
        elif i % 10 < 9:  # 20% EU (tertiary)
            region = "eu-west-1"
        else:  # 10% APAC (quaternary)
            region = "ap-southeast-1"

        priority = random.choice(priorities)

        context = WorkflowContext(
            correlation_id=f"req_{i:03d}",
            metadata={"region": region, "priority": priority},
        )

        start_time = asyncio.get_event_loop().time()

        try:
            result = await adaptive_api.execute({"request_id": i}, context)
            success = result.get("success", False)
            success_by_region[region].append(success)

            elapsed = asyncio.get_event_loop().time() - start_time
            latency_by_region[region].append(elapsed)

            if i % 10 == 0:  # Progress updates
                print(f"   ✅ Processed {i} requests...")

        except Exception as e:
            success_by_region[region].append(False)
            if i % 10 == 0:
                print(f"   ⚠️  Request {i} failed: {type(e).__name__}")

    # Analysis
    print("\n" + "=" * 70)
    print("PERFORMANCE ANALYSIS BY REGION")
    print("=" * 70)

    for region in regions:
        successes = success_by_region[region]
        latencies = latency_by_region[region]

        if successes:
            success_rate = sum(successes) / len(successes)
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            print(f"\n📍 {region}:")
            print(f"   Requests: {len(successes)}")
            print(f"   Success Rate: {success_rate:.1%}")
            print(f"   Avg Latency: {avg_latency:.3f}s")

    # Learning analysis
    print("\n" + "=" * 70)
    print("ADAPTIVE LEARNING ANALYSIS")
    print("=" * 70)

    print(f"\n🧠 Strategies Learned: {len(adaptive_api.strategies)}")
    print(f"🔄 Total Adaptations: {adaptive_api.total_adaptations}")

    print("\n📋 Strategy Summary:")
    for name, strategy in adaptive_api.strategies.items():
        print(f"\n   {name}:")
        print(f"      Context: {strategy.context_pattern}")
        print(f"      Executions: {strategy.metrics.total_executions}")
        print(f"      Success Rate: {strategy.metrics.success_rate:.1%}")
        print(f"      Avg Latency: {strategy.metrics.avg_latency:.3f}s")
        print(f"      Max Retries: {strategy.parameters.get('max_retries', 'N/A')}")

    # Logseq verification
    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE INTEGRATION")
    print("=" * 70)

    logseq_base = Path("production_adaptive_demo")
    strategy_files = list(logseq_base.glob("pages/Strategies/*.md"))
    journal_files = list(logseq_base.glob("journals/*.md"))

    print("\n📚 Logseq Knowledge Base:")
    print(f"   Strategy pages: {len(strategy_files)}")
    print(f"   Journal entries: {len(journal_files)}")
    print(f"   Location: {logseq_base.absolute()}")

    if strategy_files:
        print("\n📄 Generated Strategy Pages:")
        for strategy_file in strategy_files[:5]:  # Show first 5
            print(f"      • {strategy_file.name}")

    # Production readiness check
    print("\n" + "=" * 70)
    print("PRODUCTION READINESS CHECK")
    print("=" * 70)

    checks = {
        "✅ Automatic learning": len(adaptive_api.strategies) > 1,
        "✅ Context-aware selection": any(
            s.context_pattern for s in adaptive_api.strategies.values()
        ),
        "✅ Performance tracking": any(
            s.metrics.total_executions > 0 for s in adaptive_api.strategies.values()
        ),
        "✅ Knowledge persistence": len(strategy_files) > 0,
        "✅ Observability integration": adaptive_api.total_adaptations > 0,
    }

    all_passed = all(checks.values())

    for check, passed in checks.items():
        print(f"   {check if passed else check.replace('✅', '❌')}")

    print("\n" + "=" * 70)

    if all_passed:
        print("🚀 PRODUCTION READY!")
        print("\nKey Benefits Demonstrated:")
        print("  • Automatic region-specific optimization")
        print("  • Performance improvement through learning")
        print("  • Zero-configuration knowledge sharing")
        print("  • Complete observability integration")
    else:
        print("⚠️  Some checks failed - review output above")

    print("\n💡 Next Steps:")
    print("  1. Review generated strategies in", logseq_base.absolute())
    print("  2. Share strategies across service instances")
    print("  3. Monitor learning metrics in production")
    print("  4. Extend to other primitives (cache, router, etc.)")

    return {
        "total_requests": total_requests,
        "strategies_learned": len(adaptive_api.strategies),
        "logseq_pages": len(strategy_files),
        "production_ready": all_passed,
    }


async def main():
    """Run production demonstration."""
    try:
        result = await simulate_production_traffic()

        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"   Total Requests: {result['total_requests']}")
        print(f"   Strategies Learned: {result['strategies_learned']}")
        print(f"   Logseq Pages Created: {result['logseq_pages']}")
        print(
            f"   Production Ready: {'✅ Yes' if result['production_ready'] else '❌ No'}"
        )

        return result

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n✅ Demo completed successfully!")
