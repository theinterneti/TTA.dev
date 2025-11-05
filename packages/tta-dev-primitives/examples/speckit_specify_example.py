"""Example: Using SpecifyPrimitive to generate specifications.

This example demonstrates how to use SpecifyPrimitive to transform
high-level feature requirements into structured specification documents.
"""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import SpecifyPrimitive


async def basic_specification_example():
    """Basic example: Generate spec from simple requirement."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Specification Generation")
    print("=" * 70 + "\n")

    # Create primitive
    specify = SpecifyPrimitive(output_dir="examples/specs")

    # Define requirement
    requirement = "Add LRU cache with TTL support to LLM pipeline"

    # Generate specification
    context = WorkflowContext(workflow_id="feature-001")
    result = await specify.execute(
        {
            "requirement": requirement,
            "feature_name": "llm-cache",
        },
        context,
    )

    # Print results
    print(f"Requirement: {requirement}")
    print(f"\nGenerated Specification: {result['spec_path']}")
    print(f"Coverage Score: {result['coverage_score']:.1%}")
    print(f"Gaps Identified: {len(result['gaps'])}")

    if result["gaps"]:
        print("\nSections needing clarification:")
        for gap in result["gaps"][:5]:  # Show first 5 gaps
            print(f"  - {gap}")


async def complex_specification_example():
    """Complex example: Specification with project context."""
    print("\n" + "=" * 70)
    print("Example 2: Specification with Project Context")
    print("=" * 70 + "\n")

    specify = SpecifyPrimitive(output_dir="examples/specs", min_coverage=0.8)

    # Complex requirement with context
    requirement = (
        "Implement distributed tracing with OpenTelemetry, "
        "add Prometheus metrics export, and integrate structured logging"
    )

    project_context = {
        "architecture": "microservices",
        "tech_stack": ["Python 3.11", "FastAPI", "Docker", "Kubernetes"],
        "observability_stack": ["Prometheus", "Grafana", "Jaeger"],
        "constraints": ["Must be backwards compatible", "Zero downtime deployment"],
    }

    context = WorkflowContext(workflow_id="feature-002")
    result = await specify.execute(
        {
            "requirement": requirement,
            "context": project_context,
            "feature_name": "observability-integration",
        },
        context,
    )

    print(f"Requirement: {requirement[:60]}...")
    print(f"\nGenerated Specification: {result['spec_path']}")
    print(f"Coverage Score: {result['coverage_score']:.1%}")
    print(f"Minimum Required: {specify.min_coverage:.1%}")

    status = result["sections_completed"]
    complete = sum(1 for s in status.values() if s == "complete")
    total = len(status)
    print(f"\nSections Completed: {complete}/{total}")

    print("\nSection Status:")
    for section, status_val in list(status.items())[:8]:
        emoji = (
            "✅"
            if status_val == "complete"
            else "⚠️"
            if status_val == "incomplete"
            else "❌"
        )
        print(f"  {emoji} {section}: {status_val}")


async def workflow_composition_example():
    """Example: SpecifyPrimitive in a workflow."""
    print("\n" + "=" * 70)
    print("Example 3: Specification Workflow (Specify → Review → Iterate)")
    print("=" * 70 + "\n")

    specify = SpecifyPrimitive(output_dir="examples/specs")

    # Step 1: Generate initial spec
    print("Step 1: Generate Initial Specification")
    print("-" * 40)

    requirement = "Add rate limiting to API endpoints with Redis backend"

    context = WorkflowContext(workflow_id="feature-003")
    result = await specify.execute(
        {
            "requirement": requirement,
            "context": {
                "api_framework": "FastAPI",
                "rate_limit_strategy": "token bucket",
                "backend": "Redis",
            },
        },
        context,
    )

    print(f"Requirement: {requirement}")
    print(f"Initial Coverage: {result['coverage_score']:.1%}")
    print(f"Gaps: {len(result['gaps'])} sections need clarification")

    # Step 2: Review gaps
    print("\nStep 2: Review Identified Gaps")
    print("-" * 40)

    if result["gaps"]:
        print("Sections requiring human input:")
        for gap in result["gaps"]:
            print(f"  • {gap}")

        print("\n➡️  Next step: Use ClarifyPrimitive to refine these sections")
        print("     (ClarifyPrimitive will be implemented in Day 3-4)")

    # Step 3: Show next steps in workflow
    print("\nStep 3: Specification Workflow Process")
    print("-" * 40)
    print("""
Typical workflow after SpecifyPrimitive:

1. ✅ SpecifyPrimitive: requirement → .spec.md (DONE)
2. ⏩ ClarifyPrimitive: iterative refinement (NEXT)
3. ⏩ ValidationGatePrimitive: human approval
4. ⏩ PlanPrimitive: generate implementation plan
5. ⏩ TasksPrimitive: break into ordered tasks
    """)


async def batch_specification_example():
    """Example: Generate multiple specs in batch."""
    print("\n" + "=" * 70)
    print("Example 4: Batch Specification Generation")
    print("=" * 70 + "\n")

    specify = SpecifyPrimitive(output_dir="examples/specs")

    requirements = [
        ("Add OAuth2 authentication", "oauth2-auth"),
        ("Implement WebSocket support for real-time updates", "websocket-realtime"),
        ("Add email notification system with templates", "email-notifications"),
    ]

    print("Generating specifications for multiple features...\n")

    for requirement, feature_name in requirements:
        context = WorkflowContext(workflow_id=f"batch-{feature_name}")

        result = await specify.execute(
            {
                "requirement": requirement,
                "feature_name": feature_name,
            },
            context,
        )

        coverage_emoji = "✅" if result["coverage_score"] >= 0.7 else "⚠️"
        print(f"{coverage_emoji} {feature_name}:")
        print(f"   Coverage: {result['coverage_score']:.1%}")
        print(f"   Gaps: {len(result['gaps'])} sections\n")

    print("All specifications generated successfully!")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("SpecifyPrimitive Examples")
    print("Systematic Spec-Driven Development for TTA.dev")
    print("=" * 70)

    await basic_specification_example()
    await complex_specification_example()
    await workflow_composition_example()
    await batch_specification_example()

    print("\n" + "=" * 70)
    print("Examples Complete!")
    print("=" * 70)
    print("""
Next Steps:
1. Review generated specs in examples/specs/
2. Try ClarifyPrimitive (Day 3-4) for iterative refinement
3. Use ValidationGatePrimitive (Day 5) for approval gates
4. Complete workflow with PlanPrimitive + TasksPrimitive (Week 2)

Documentation: docs/planning/SPECKIT_IMPLEMENTATION_PLAN.md
    """)


if __name__ == "__main__":
    asyncio.run(main())
