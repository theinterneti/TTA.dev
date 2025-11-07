"""Demonstration of AUTOMATIC self-improving primitives.

This example shows how adaptive primitives automatically:
1. Learn from execution patterns
2. Persist strategies to Logseq knowledge base
3. Adapt behavior without manual intervention

Just run it and watch the magic happen! 🪄
"""

import asyncio
import logging
from pathlib import Path

from tta_dev_primitives.adaptive.logseq_integration import LogseqStrategyIntegration
from tta_dev_primitives.adaptive.retry import AdaptiveRetryPrimitive
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


class UnstableService(WorkflowPrimitive[dict, dict]):
    """Simulates an unstable external service."""

    def __init__(self):
        super().__init__()
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        self.call_count += 1

        # Simulate different failure patterns based on environment
        environment = context.metadata.get("environment", "test")

        if environment == "production":
            # Production: occasional failures
            if self.call_count % 5 == 0:
                raise ConnectionError("Production database connection lost")
        elif environment == "staging":
            # Staging: frequent failures early on
            if self.call_count < 3:
                raise TimeoutError("Staging service timeout")

        return {"status": "success", "data": input_data}


async def main():
    """Run automatic learning demonstration."""

    print("🤖 Automatic Self-Improving Primitives Demo")
    print("=" * 60)
    print("\nThis primitive will AUTOMATICALLY:")
    print("  ✅ Learn from its own execution patterns")
    print("  ✅ Persist learned strategies to Logseq")
    print("  ✅ Adapt retry behavior without manual intervention")
    print("\n" + "=" * 60 + "\n")

    # Setup Logseq integration
    logseq_integration = LogseqStrategyIntegration("auto_learning_demo")

    # Create service and adaptive primitive
    service = UnstableService()
    adaptive_retry = AdaptiveRetryPrimitive(
        target_primitive=service,
        logseq_integration=logseq_integration,
        enable_auto_persistence=True,  # 🔥 This enables automatic persistence!
    )

    print("🎯 Scenario 1: Production Environment")
    print("-" * 40)

    # Run multiple calls in production context
    for i in range(8):
        context = WorkflowContext(
            correlation_id=f"prod_request_{i}",
            metadata={"environment": "production", "priority": "high"},
        )

        try:
            result = await adaptive_retry.execute({"request_id": i}, context)
            if result.get("success"):
                print(
                    f"  ✅ Request {i}: Success (attempts: {result.get('attempts', 1)})"
                )
            else:
                print(
                    f"  ❌ Request {i}: Failed after {result.get('attempts', 0)} attempts"
                )
        except Exception as e:
            print(f"  ❌ Request {i}: Exception - {e}")

        await asyncio.sleep(0.1)  # Small delay between requests

    print(f"\n📚 Learned {len(adaptive_retry.strategies)} strategies so far")

    print("\n🎯 Scenario 2: Staging Environment")
    print("-" * 40)

    # Run calls in staging context (different error pattern)
    for i in range(8):
        context = WorkflowContext(
            correlation_id=f"staging_request_{i}",
            metadata={"environment": "staging", "time_sensitive": True},
        )

        try:
            result = await adaptive_retry.execute({"request_id": i}, context)
            if result.get("success"):
                print(
                    f"  ✅ Request {i}: Success (attempts: {result.get('attempts', 1)})"
                )
            else:
                print(
                    f"  ❌ Request {i}: Failed after {result.get('attempts', 0)} attempts"
                )
        except Exception as e:
            print(f"  ❌ Request {i}: Exception - {e}")

        await asyncio.sleep(0.1)

    print(f"\n📚 Now learned {len(adaptive_retry.strategies)} total strategies")

    # Show what was automatically created
    print("\n🧠 Automatically Learned Strategies:")
    print("-" * 40)
    for name, strategy in adaptive_retry.strategies.items():
        print(f"\n  📋 {name}")
        print(f"     Context: {strategy.context_pattern}")
        print(f"     Success Rate: {strategy.metrics.success_rate:.1%}")
        print(f"     Executions: {strategy.metrics.total_executions}")
        print(f"     Validated: {'✅' if strategy.is_validated else '⏳'}")

    # Show Logseq knowledge base
    print("\n📖 Logseq Knowledge Base:")
    print("-" * 40)

    logseq_base = Path("auto_learning_demo")
    if logseq_base.exists():
        print(f"\n  Knowledge base created at: {logseq_base.absolute()}")

        # Show strategy pages
        strategy_pages = list(logseq_base.glob("pages/Strategies/*.md"))
        if strategy_pages:
            print(f"\n  📄 {len(strategy_pages)} strategy pages automatically created:")
            for page in strategy_pages:
                print(f"     • {page.name}")
        else:
            print("  ⏳ Strategy pages will be created on next learning event")

        # Show journal entries
        journal_entries = list(logseq_base.glob("journals/*.md"))
        if journal_entries:
            print(
                f"\n  📅 {len(journal_entries)} journal entries with learning events:"
            )
            for entry in journal_entries:
                print(f"     • {entry.name}")

    print("\n✨ Summary:")
    print("-" * 40)
    print(f"  • Total strategies learned: {len(adaptive_retry.strategies)}")
    print(
        f"  • Validated strategies: {sum(1 for s in adaptive_retry.strategies.values() if s.is_validated)}"
    )
    print(f"  • Total adaptations: {adaptive_retry.total_adaptations}")
    print("\n  🎉 Everything happened AUTOMATICALLY!")
    print("     No manual intervention required!")
    print("\n  💡 The primitive learned, adapted, and documented itself")
    print("     through real execution experience.\n")


if __name__ == "__main__":
    asyncio.run(main())
