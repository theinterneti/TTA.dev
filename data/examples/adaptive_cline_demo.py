#!/usr/bin/env python3
"""
Adaptive Cline Primitive Demo

This demonstrates the AdaptiveClinePrimitive - a self-improving Cline CLI that learns
optimal personas, prompts, and configurations for different task types.

Features demonstrated:
- Automatic persona selection based on task analysis
- Learning from execution patterns and validation
- E2B integration for code validation
- ACE integration for advanced analysis
- Logseq persistence of learned strategies
- Safety mechanisms and circuit breakers

Run with: python examples/adaptive_cline_demo.py
"""

import asyncio
import logging
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../packages"))

from tta_dev_primitives.adaptive import (
    ClineCLISubAgentPrimitive,
    LearningMode,
    create_cline_cli_subagent,
)
from tta_dev_primitives.core.base import WorkflowContext

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_mock_cline_binary():
    """Create a mock Cline binary for demonstration purposes."""
    import tempfile
    import stat

    mock_script = """#!/bin/bash
# Mock Cline CLI for demonstration
echo "Mock Cline CLI Output:"
echo "Task completed successfully with persona: $CLINE_PERSONA"
echo "Executed prompt: $CLINE_PROMPT"
exit 0
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='_cline', delete=False) as f:
        f.write(mock_script)
        f.flush()
        os.chmod(f.name, stat.S_IEXEC | stat.S_IRUSR | stat.S_IWUSR)

    return f.name


async def demonstrate_adaptive_cline_learning():
    """Show how the adaptive Cline primitive learns from task execution."""

    print("🧠 Adaptive Cline Primitive Learning Demo")
    print("=" * 60)
    print("This shows how Cline CLI becomes smarter with each task execution.\n")

    # Create mock Cline binary for demo (replace with real one in production)
    mock_cline = await create_mock_cline_binary()
    print(f"Using mock Cline binary at: {mock_cline}\n")

    try:
        # Create adaptive Cline executor
        adaptive_cline = create_cline_cli_subagent(
            learning_mode=LearningMode.VALIDATE,
            enable_e2b=False,  # Disable for demo (E2B not available)
            enable_ace=False,  # Disable for demo (ACE not available)
        )

        # Override to use our mock binary
        adaptive_cline.cline_binary = mock_cline

        print("📊 Initial Configuration:")
        print("  Learning Mode: VALIDATE (only use validated strategies)")
        print("  E2B Validation: Disabled for demo")
        print("  ACE Analysis: Disabled for demo")
        print("  Circuit Breaker: 0.6 threshold")
        print()

        # Test scenarios that will drive learning
        test_scenarios = [
            {
                "task": "Implement a user authentication function in Python",
                "context": {
                    "environment": "development",
                    "priority": "high",
                    "code_context": "def authenticate_user(username: str) -> bool:"
                },
                "expected_persona": "backend-developer",
                "iterations": 5,
            },
            {
                "task": "Create comprehensive unit tests for data validation",
                "context": {
                    "environment": "testing",
                    "priority": "medium",
                },
                "expected_persona": "testing-specialist",
                "iterations": 4,
            },
            {
                "task": "Add observability metrics to cache operations",
                "context": {
                    "environment": "production",
                    "priority": "medium",
                },
                "expected_persona": "observability-expert",
                "iterations": 3,
            },
            {
                "task": "Build a React component for user profile display",
                "context": {
                    "environment": "development",
                    "priority": "normal",
                    "code_context": "function UserProfile({ user }) {"
                },
                "expected_persona": "frontend-developer",
                "iterations": 3,
            },
        ]

        total_executions = 0
        total_successes = 0

        for i, scenario in enumerate(test_scenarios, 1):
            print("
" + "=" * 60)
            print(f"📝 Scenario {i}/{len(test_scenarios)}: {scenario['task'][:50]}...")
            print("=" * 60)
            print(f"Expected Persona: {scenario['expected_persona']}")
            print(f"Iterations: {scenario['iterations']}\n")

            scenario_successes = 0

            for iteration in range(scenario["iterations"]):
                # Create workflow context
                context = WorkflowContext(
                    correlation_id=f"cline-demo-{i}-{iteration}",
                    data={"code_context": scenario["context"].get("code_context", "")},
                    metadata={
                        "environment": scenario["context"]["environment"],
                        "priority": scenario["context"]["priority"],
                    }
                )

                # Execute task
                try:
                    result = await adaptive_cline.execute(scenario["task"], context)

                    success = result.get("success", False)
                    persona_used = result.get("persona", "unknown")

                    if success:
                        total_executions += 1
                        total_successes += 1
                        scenario_successes += 1

                        status = "✅"
                        persona_match = persona_used == scenario["expected_persona"]
                        persona_note = " (expected)" if persona_match else f" (was {persona_used})"
                    else:
                        total_executions += 1
                        status = "❌"
                        persona_note = f" ({persona_used})"

                        print(
                            f"   {status} Iteration {iteration + 1:2d}: "
                            f"Persona {persona_note:<15}"
                            f"output length: {len(result.get('stdout', ''))}"
                        )

                except Exception as e:
                    print(f"   ❌ Iteration {iteration + 1:2d}: Exception - {e}")
                    total_executions += 1

            # Scenario summary
            success_rate = scenario_successes / scenario["iterations"]
            print("\n🎯 Scenario Results:")
            print(f"   Success Rate: {success_rate:.1%}")
            adaptation = adaptive_cline.get_learning_summary()
            print(f"   Strategies After: {adaptation['total_strategies']}")
            print(f"   Adaptations: {adaptation['total_adaptations']}")

        # Final learning summary
        print("\n" + "=" * 60)
        print("🎯 Final Learning Summary")
        print("=" * 60)

        overall_success_rate = total_successes / total_executions if total_executions > 0 else 0
        learning_summary = adaptive_cline.get_learning_summary()
        cline_metrics = adaptive_cline.get_cline_specific_metrics()

        print(f"Overall Success Rate: {overall_success_rate:.1%}")
        print(f"Learning Mode: {adaptive_cline.learning_mode.value}")
        print(f"Total Strategies: {learning_summary['total_strategies']}")
        print(f"Successful Adaptations: {learning_summary['successful_adaptations']}")
        print(f"Total Cline Executions: {cline_metrics['total_executions']}")
        print(f"Circuit Breaker Active: {learning_summary['circuit_breaker_active']}")

        print("\n📊 Learned Strategy Performance:")
        for name, metrics in learning_summary["strategies"].items():
            print(f"   • {name}:")
            print(f"     - Success Rate: {metrics['success_rate']:.1%}")
            print(f"     - Avg Latency: {metrics['avg_latency']:.3f}s")
            print(f"     - Executions: {metrics['executions']}")

        if cline_metrics['persona_performance']:
            print("\n👥 Persona Effectiveness by Task Type:")
            for persona, task_types in cline_metrics['persona_performance'].items():
                print(f"   • {persona}:")
                for task_type, perf in task_types.items():
                    print(f"     - {task_type}: {perf['success_rate']:.1%} ({perf['executions']} executions)")

    finally:
        # Clean up mock binary
        if 'mock_cline' in locals():
            try:
                os.unlink(mock_cline)
            except:
                pass


async def demonstrate_cline_task_classification():
    """Show the task classification and persona selection logic."""

    print(f"\n{'=' * 60}")
    print("🔬 Task Classification & Persona Selection Demo")
    print(f"{'=' * 60}")

    from tta_dev_primitives.adaptive.cline import ClineTaskClassifier

    test_tasks = [
        "Implement a REST API endpoint for user registration",
        "Create unit tests for the authentication module",
        "Add OpenTelemetry metrics to the database layer",
        "Build a dashboard UI component for analytics",
        "Write documentation for the deployment process",
        "Optimize the SQL query for better performance",
        "Design the database schema for the new feature",
        "Debug the memory leak in the worker process",
        "Set up CI/CD pipeline with GitHub Actions",
        "Analyze ML model performance and accuracy",
    ]

    print("Task Classification Results:")
    print("-" * 80)
    print(f"{'Task':<50} {'Type':<12} {'Persona':<15} {'Complexity':<10} {'Flags'}")
    print("-" * 80)

    for task in test_tasks:
        classification = ClineTaskClassifier.classify_task(task)
        complexity = classification['complexity']
        persona = classification['recommended_persona']
        task_type = classification['task_type']
        needs_validation = classification['needs_validation']
        has_generation = classification['has_code_generation']

        flags = []
        if needs_validation:
            flags.append("🔍")
        if has_generation:
            flags.append("⚡")

        flag_str = " ".join(flags) if flags else ""

        print(f"{task:<50} {task_type:<12} {persona:<15} {complexity:<10} {flag_str}")


async def demonstrate_safety_mechanisms():
    """Show built-in safety mechanisms in the adaptive Cline primitive."""

    print(f"\n{'=' * 60}")
    print("🛡️ Safety Mechanisms Demo")
    print(f"{'=' * 60}")

    print("Built-in Safety Features:")
    print()
    print("1. 🔄 Learning Modes:")
    print("   • DISABLED: Use only baseline strategies")
    print("   • OBSERVE: Learn but don't change behavior")
    print("   • VALIDATE: Test strategies before adoption")
    print("   • ACTIVE: Full learning with validation")
    print()
    print("2. ⚡ Circuit Breakers:")
    print("   • Automatic fallback when failure rate exceeds threshold")
    print("   • Gradual recovery after cooling period")
    print("   • Prevents learning-induced outages")
    print()
    print("3. ✅ Strategy Validation:")
    print("   • Minimum sample sizes for statistical significance")
    print("   • Performance regression detection")
    print("   • Context-specific validation")
    print()
    print("4. 📊 Conservative Learning:")
    print("   • Prove improvement before strategy adoption")
    print("   • Baseline strategies always available")
    print("   • Limited strategy count to prevent explosion")
    print()
    print("5. 🔍 Meta-Observability:")
    print("   • Learning process itself is tracked")
    print("   • Strategy performance metrics")
    print("   • Execution history and patterns")


async def main():
    """Run the complete adaptive Cline demonstration."""

    print("🚀 Welcome to the Adaptive Cline Primitive Demo!")
    print("\nThis demonstrates how Cline CLI can become self-improving:")
    print("• Automatic persona selection for different task types")
    print("• Learning optimal prompts and configurations")
    print("• Code validation with E2B integration")
    print("• Advanced analysis with ACE integration")
    print("• Knowledge persistence with Logseq integration")
    print("• Built-in safety mechanisms and circuit breakers")
    print()

    try:
        # Show task classification
        await demonstrate_cline_task_classification()

        # Show learning in action
        await demonstrate_adaptive_cline_learning()

        # Show safety mechanisms
        await demonstrate_safety_mechanisms()

        print("\n✨ Demo Complete!")
        print("\n🎯 Key Takeaways:")
        print("• Cline CLI learns optimal configurations from task execution")
        print("• Personas are automatically selected based on task analysis")
        print("• Validation catches issues before they reach production")
        print("• Strategies improve continuously while maintaining safety")
        print("• All learning is persisted to the knowledge base")
        print("\nThis represents the next evolution: AI agents that teach themselves! 🧠")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo encountered an error: {e}")
        print("This may be due to missing dependencies - check E2B/ACE availability")


if __name__ == "__main__":
    asyncio.run(main())
