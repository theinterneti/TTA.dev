#!/usr/bin/env python3
"""
Adaptive/Self-Improving Primitives Demo

This demonstrates the revolutionary combination of:
- ACE-inspired self-learning patterns
- Observability data as learning input
- Strategy adaptation based on real execution patterns
- Circuit breakers and validation for safety

Key Innovation: Instead of static retry logic, these primitives learn optimal
strategies from actual execution patterns and observability data.

Run with: python examples/adaptive_primitives_demo.py
"""

import asyncio
import logging
import random

from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive, LearningMode
from tta_dev_primitives.core.base import WorkflowContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnreliableAPI:
    """Simulates an unreliable API for testing adaptive retry strategies."""

    def __init__(self, failure_rate: float = 0.4, error_types: list[str] | None = None):
        self.failure_rate = failure_rate
        self.error_types = error_types or [
            "TimeoutError",
            "ConnectionError",
            "HTTPException",
        ]
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Simulate API call with configurable failure patterns."""
        self.call_count += 1

        # Simulate different failure patterns based on context
        environment = context.metadata.get("environment", "unknown")
        priority = context.metadata.get("priority", "normal")

        # Adjust failure rate based on environment
        actual_failure_rate = self.failure_rate
        if environment == "production":
            actual_failure_rate *= 0.7  # More reliable in prod
        elif environment == "development":
            actual_failure_rate *= 1.3  # Less reliable in dev

        # Higher priority gets better reliability
        if priority == "high":
            actual_failure_rate *= 0.6
        elif priority == "low":
            actual_failure_rate *= 1.4

        # Decide if this call should fail
        if random.random() < actual_failure_rate:
            error_type = random.choice(self.error_types)
            error_msg = f"Simulated {error_type} in {environment} environment"

            if error_type == "TimeoutError":
                raise TimeoutError(error_msg)
            elif error_type == "ConnectionError":
                raise ConnectionError(error_msg)
            else:
                raise Exception(error_msg)

        # Success!
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            "data": f"Success after {self.call_count} total calls",
            "environment": environment,
            "priority": priority,
        }


async def demonstrate_adaptive_learning():
    """Show how adaptive retry primitive learns optimal strategies over time."""

    print("🧠 Adaptive Retry Primitive Learning Demo")
    print("=" * 60)
    print("This shows how primitives learn from observability data to improve over time.\n")

    # Create unreliable API to test against
    unreliable_api = UnreliableAPI(failure_rate=0.5)

    # Create adaptive retry primitive
    adaptive_retry = AdaptiveRetryPrimitive(
        target_primitive=unreliable_api,
        learning_mode=LearningMode.VALIDATE,  # Only use validated strategies
        max_strategies=6,  # Limit strategy collection
        circuit_breaker_threshold=0.8,  # Fall back if >80% failures
    )

    print("📊 Initial Configuration:")
    print(f"   Learning Mode: {adaptive_retry.learning_mode.value}")
    print(f"   Max Strategies: {adaptive_retry.max_strategies}")
    print(f"   Circuit Breaker: {adaptive_retry.circuit_breaker_threshold:.0%}")
    print()

    # Test scenarios that will drive learning
    test_scenarios = [
        {
            "name": "Production High Priority",
            "context": {"environment": "production", "priority": "high"},
            "iterations": 8,
            "description": "Should learn fast, minimal retry strategy",
        },
        {
            "name": "Development Normal Priority",
            "context": {"environment": "development", "priority": "normal"},
            "iterations": 10,
            "description": "Should learn more aggressive retry strategy",
        },
        {
            "name": "Test Environment Low Priority",
            "context": {
                "environment": "test",
                "priority": "low",
                "time_sensitive": False,
            },
            "iterations": 6,
            "description": "Should learn patient, high-retry strategy",
        },
        {
            "name": "Time-Sensitive Operations",
            "context": {
                "environment": "production",
                "priority": "normal",
                "time_sensitive": True,
            },
            "iterations": 7,
            "description": "Should learn fast backoff strategy",
        },
    ]

    # Execute scenarios and observe learning
    total_executions = 0
    total_successes = 0

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'=' * 60}")
        print(f"📝 Scenario {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"{'=' * 60}")
        print(f"Description: {scenario['description']}")
        print(f"Iterations: {scenario['iterations']}\n")

        scenario_successes = 0
        scenario_attempts = 0

        for iteration in range(scenario["iterations"]):
            context = WorkflowContext(
                correlation_id=f"adaptive-demo-{i}-{iteration}",
                metadata=scenario["context"],
            )

            try:
                result = await adaptive_retry.execute(
                    {
                        "operation": f"test_call_{iteration}",
                        "scenario": scenario["name"],
                    },
                    context,
                )

                success = result.get("success", False)
                attempts = result.get("attempts", 1)
                strategy_used = result.get("strategy_used", "unknown")

                total_executions += 1
                scenario_attempts += attempts

                if success:
                    total_successes += 1
                    scenario_successes += 1
                    status_icon = "✅"
                else:
                    status_icon = "❌"

                print(
                    f"   {status_icon} Iteration {iteration + 1:2d}: "
                    f"{attempts} attempts, strategy='{strategy_used}'"
                )

            except Exception as e:
                print(f"   ❌ Iteration {iteration + 1:2d}: Failed with {type(e).__name__}")
                total_executions += 1

        # Show scenario summary
        success_rate = scenario_successes / scenario["iterations"]
        avg_attempts = (
            scenario_attempts / scenario["iterations"] if scenario["iterations"] > 0 else 0
        )

        print("\n📊 Scenario Summary:")
        print(f"   Success Rate: {success_rate:.1%}")
        print(f"   Avg Attempts: {avg_attempts:.1f}")

        # Show learning progress
        learning_summary = adaptive_retry.get_learning_summary()
        print(f"   Strategies Learned: {learning_summary['total_strategies']}")
        print(f"   Total Adaptations: {learning_summary['total_adaptations']}")

        # Brief pause between scenarios to show learning progression
        await asyncio.sleep(0.5)

    # Final learning summary
    print(f"\n{'=' * 60}")
    print("🎯 Final Learning Summary")
    print(f"{'=' * 60}")

    overall_success_rate = total_successes / total_executions if total_executions > 0 else 0
    learning_summary = adaptive_retry.get_learning_summary()

    print(f"Overall Success Rate: {overall_success_rate:.1%}")
    print(f"Total Executions: {total_executions}")
    print(f"Strategies Learned: {learning_summary['total_strategies']}")
    print(f"Successful Adaptations: {learning_summary['successful_adaptations']}")
    print(
        f"Circuit Breaker Triggered: {'Yes' if learning_summary['circuit_breaker_active'] else 'No'}"
    )

    print("\n📋 Learned Strategies:")
    for name, metrics in learning_summary["strategies"].items():
        print(f"   • {name}:")
        print(f"     - Success Rate: {metrics['success_rate']:.1%}")
        print(f"     - Avg Latency: {metrics['avg_latency']:.3f}s")
        print(f"     - Executions: {metrics['executions']}")
        print(f"     - Contexts: {metrics['contexts']}")
        print(f"     - Validated: {'✅' if metrics['validated'] else '⏳'}")


async def demonstrate_observability_integration():
    """Show how observability data feeds into learning."""

    print(f"\n{'=' * 60}")
    print("🔍 Observability → Learning Integration")
    print(f"{'=' * 60}")

    print("Key Learning Inputs from Observability:")
    print("• Error types and frequencies from spans/logs")
    print("• Success/failure patterns by retry count")
    print("• Latency distributions for different backoff strategies")
    print("• Resource usage patterns during retries")
    print("• Context patterns (environment, priority, error types)")
    print()

    print("Learning Outputs:")
    print("• Optimal retry counts for different error types")
    print("• Best backoff strategies for different environments")
    print("• Context-aware strategy selection")
    print("• Circuit breaker thresholds based on failure patterns")
    print("• Performance vs reliability tradeoffs")


async def demonstrate_safety_mechanisms():
    """Show built-in safety mechanisms in adaptive primitives."""

    print(f"\n{'=' * 60}")
    print("🛡️ Safety Mechanisms Demo")
    print(f"{'=' * 60}")

    print("Critical Safeguards Built Into Adaptive Primitives:")
    print()
    print("1. 🎚️  Learning Modes:")
    print("   • DISABLED: No learning, baseline only")
    print("   • OBSERVE: Collect data but don't adapt")
    print("   • VALIDATE: Only use validated strategies")
    print("   • ACTIVE: Full learning with validation")
    print()
    print("2. ⚡ Circuit Breakers:")
    print("   • Fall back to baseline when failure rate exceeds threshold")
    print("   • Temporary learning suspension during issues")
    print("   • Automatic recovery after cooling period")
    print()
    print("3. ✅ Strategy Validation:")
    print("   • New strategies tested before adoption")
    print("   • Statistical significance testing")
    print("   • Minimum sample sizes for decisions")
    print()
    print("4. 📊 Conservative Learning:")
    print("   • Strategies must prove improvement over baseline")
    print("   • Limited strategy collection (prevents explosion)")
    print("   • Context-aware strategy selection")
    print()
    print("5. 🔍 Meta-Observability:")
    print("   • Learning process itself is observable")
    print("   • Strategy performance tracking")
    print("   • Adaptation success/failure metrics")


async def main():
    """Run the complete adaptive primitives demonstration."""

    print("🚀 Welcome to the Adaptive/Self-Improving Primitives Demo!")
    print("This demonstrates primitives that learn from observability data to improve over time.")
    print()

    try:
        # Core learning demonstration
        await demonstrate_adaptive_learning()

        # Show observability integration
        await demonstrate_observability_integration()

        # Show safety mechanisms
        await demonstrate_safety_mechanisms()

        print("\n✨ Demo Complete!")
        print("Key Takeaways:")
        print("• Primitives learn optimal strategies from real execution patterns")
        print("• Observability data (traces, metrics, logs) becomes learning input")
        print("• Built-in safety prevents learning pathologies")
        print("• Context awareness enables environment-specific strategies")
        print("• Circuit breakers provide graceful degradation")
        print("• Meta-observability makes learning process transparent")
        print()
        print("This represents a new paradigm: Infrastructure that gets smarter with use! 🧠")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo encountered an error: {e}")
        print("This is expected during development - the adaptive system is learning!")


if __name__ == "__main__":
    asyncio.run(main())
