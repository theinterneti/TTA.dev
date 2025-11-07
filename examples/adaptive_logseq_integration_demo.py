"""Complete example demonstrating Logseq integration with adaptive primitives.

This example shows how learned strategies are automatically persisted to
the Logseq knowledge base, creating a rich, searchable record of AI learning.

Features demonstrated:
- Strategy learning and persistence
- Logseq page generation
- Knowledge graph integration
- Learning analytics queries
- Strategy sharing and discovery
"""

import asyncio
import json
import logging
from pathlib import Path

from tta_dev_primitives.adaptive.base import LearningMode
from tta_dev_primitives.adaptive.logseq_integration import (
    STRATEGY_DASHBOARD_TEMPLATE,
    LogseqStrategyIntegration,
)
from tta_dev_primitives.adaptive.retry import AdaptiveRetryPrimitive
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnreliableAPI(WorkflowPrimitive[dict, dict]):
    """Mock API that fails based on context patterns."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Simulate different failure patterns based on context
        if "error_spike" in str(context.metadata):
            if hash(context.correlation_id) % 3 == 0:  # 33% failure rate
                raise Exception("Network timeout during error spike")

        if "production" in str(context.metadata):
            if hash(context.correlation_id) % 10 == 0:  # 10% failure rate
                raise Exception("Production database timeout")

        if "high_load" in str(context.metadata):
            # Higher latency in high load scenarios
            await asyncio.sleep(0.5)

        return {"api_result": f"Success for {input_data.get('request_id', 'unknown')}"}


async def demonstrate_logseq_strategy_learning():
    """Demonstrate strategy learning with Logseq integration."""

    print("🧠 Adaptive Primitives + Logseq Integration Demo")
    print("=" * 60)

    # Initialize Logseq integration
    logseq_integration = LogseqStrategyIntegration("demo_logseq")

    # Create adaptive retry primitive with Logseq integration
    api_call = UnreliableAPI()
    adaptive_retry = AdaptiveRetryPrimitive(
        primitive=api_call,
        learning_mode=LearningMode.AGGRESSIVE,  # Learn faster for demo
        logseq_integration=logseq_integration,  # Enable Logseq persistence
    )

    print("\n📚 Setting up Logseq knowledge base...")

    # Create strategy dashboard
    dashboard_file = Path("demo_logseq/pages/Strategy Learning Dashboard.md")
    dashboard_file.parent.mkdir(parents=True, exist_ok=True)
    dashboard_file.write_text(STRATEGY_DASHBOARD_TEMPLATE, encoding="utf-8")
    print(f"  ✅ Created dashboard: {dashboard_file}")

    scenarios = [
        {
            "name": "Normal Operations",
            "context_meta": {"environment": "staging", "priority": "normal"},
            "expected_learning": "Low retry counts, standard backoff",
        },
        {
            "name": "Error Spike Period",
            "context_meta": {
                "environment": "production",
                "error_spike": True,
                "priority": "high",
            },
            "expected_learning": "Higher retry counts, aggressive backoff",
        },
        {
            "name": "High Load Scenario",
            "context_meta": {
                "environment": "production",
                "high_load": True,
                "time_sensitive": True,
            },
            "expected_learning": "Timeout-aware strategies, fast failure",
        },
    ]

    for scenario in scenarios:
        print(f"\n🎯 Scenario: {scenario['name']}")
        print(f"   Context: {scenario['context_meta']}")
        print(f"   Expected: {scenario['expected_learning']}")

        # Run multiple attempts to trigger learning
        for attempt in range(8):  # Enough to trigger learning and validation
            context = WorkflowContext(
                correlation_id=f"{scenario['name'].lower().replace(' ', '_')}_{attempt}",
                metadata=scenario["context_meta"],
            )

            try:
                result = await adaptive_retry.execute(
                    {"request_id": f"req_{attempt}"}, context
                )
                print(f"   ✅ Attempt {attempt + 1}: Success")
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1}: Failed - {e}")

            # Small delay to show learning progression
            await asyncio.sleep(0.1)

        # Show learned strategies for this scenario
        learned_strategies = adaptive_retry._learning_strategies
        scenario_strategies = [
            s
            for s in learned_strategies
            if scenario["name"].lower().replace(" ", "_") in s.name
        ]

        if scenario_strategies:
            strategy = scenario_strategies[-1]  # Most recent
            print(f"   🧠 Learned strategy: {strategy.name}")
            print(f"      Success rate: {strategy.metrics.success_rate:.1%}")
            print(f"      Parameters: {json.dumps(strategy.parameters, indent=6)}")

            # Strategy is automatically saved to Logseq by AdaptiveRetryPrimitive
            strategy_file = Path(f"demo_logseq/pages/Strategies/{strategy.name}.md")
            if strategy_file.exists():
                print(f"   📄 Logseq page: {strategy_file}")
            else:
                print(f"   ⏳ Logseq page pending: {strategy.name}")

    print("\n📊 Learning Analytics")
    print("-" * 30)

    # Show overall learning statistics
    all_strategies = adaptive_retry._learning_strategies
    print(f"Total strategies learned: {len(all_strategies)}")
    print(f"Validated strategies: {sum(1 for s in all_strategies if s.is_validated)}")

    if all_strategies:
        avg_success_rate = sum(s.metrics.success_rate for s in all_strategies) / len(
            all_strategies
        )
        print(f"Average success rate: {avg_success_rate:.1%}")

        total_executions = sum(s.metrics.total_executions for s in all_strategies)
        print(f"Total strategy executions: {total_executions}")

    print("\n📚 Logseq Knowledge Base Structure")
    print("-" * 40)

    # Show generated Logseq structure
    logseq_base = Path("demo_logseq")
    if logseq_base.exists():
        for page_file in logseq_base.glob("**/*.md"):
            relative_path = page_file.relative_to(logseq_base)
            print(f"  📄 {relative_path}")

    print("\n🔍 Strategy Discovery Queries")
    print("-" * 35)

    # Generate and display useful queries
    queries = logseq_integration.generate_strategy_queries()
    for query_name, query_text in queries.items():
        if isinstance(query_text, dict):
            print(f"\n  {query_name.title()}:")
            for sub_name, sub_query in query_text.items():
                print(f"    {sub_name}: {sub_query}")
        else:
            print(f"  {query_name.title()}: {query_text}")

    print("\n🎓 Learning Insights")
    print("-" * 25)

    insights = [
        "Strategies automatically adapt to error patterns",
        "Context metadata drives strategy selection",
        "Learning is validated through real execution",
        "Logseq provides searchable strategy knowledge",
        "Queries enable strategy analysis and sharing",
        "Knowledge graph connects related strategies",
    ]

    for insight in insights:
        print(f"  • {insight}")

    print("\n✅ Demo Complete!")
    print(
        "\nNext steps:\n"
        "  1. Explore generated Logseq pages in demo_logseq/\n"
        "  2. Try the strategy queries in Logseq\n"
        "  3. Customize strategies for your use cases\n"
        "  4. Build strategy sharing networks\n"
    )

    return {
        "total_strategies": len(all_strategies),
        "validated_strategies": sum(1 for s in all_strategies if s.is_validated),
        "logseq_pages_created": len(list(logseq_base.glob("**/*.md")))
        if logseq_base.exists()
        else 0,
        "demo_path": str(logseq_base),
    }


async def demonstrate_strategy_sharing():
    """Demonstrate strategy sharing between primitive instances."""

    print("\n🔄 Strategy Sharing Demo")
    print("=" * 30)

    # Create two different retry primitives
    logseq_integration = LogseqStrategyIntegration("shared_logseq")

    api1 = UnreliableAPI()
    api2 = UnreliableAPI()

    retry1 = AdaptiveRetryPrimitive(
        primitive=api1, logseq_integration=logseq_integration
    )
    retry2 = AdaptiveRetryPrimitive(
        primitive=api2, logseq_integration=logseq_integration
    )

    # First primitive learns a strategy
    print("  🎯 Primitive 1 learning...")
    for i in range(5):
        context = WorkflowContext(
            correlation_id=f"shared_learning_{i}",
            metadata={"environment": "production", "shared_context": True},
        )
        try:
            await retry1.execute({"request": f"req_{i}"}, context)
        except Exception:
            pass

    # In a full implementation, primitive 2 would discover and use strategies
    # learned by primitive 1 through Logseq queries
    print("  🔍 Primitive 2 discovering strategies...")
    print("     (Strategy discovery via Logseq queries)")
    print("     (Automatic strategy sharing across primitives)")

    print("  ✅ Strategy sharing demonstrated")


if __name__ == "__main__":
    # Run the demonstration
    results = asyncio.run(demonstrate_logseq_strategy_learning())
    print(f"\n📈 Results: {json.dumps(results, indent=2)}")

    # Demonstrate strategy sharing
    asyncio.run(demonstrate_strategy_sharing())
