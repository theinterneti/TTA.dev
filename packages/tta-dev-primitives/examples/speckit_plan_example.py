"""PlanPrimitive Examples.

Demonstrates:
1. Basic plan generation from spec.md
2. Plan with architecture context
3. Complete workflow (Specify → Clarify → Validate → Plan)
4. Minimal plan (no data models, no ADRs, no effort estimation)
5. Plan with custom output directory
"""

import asyncio
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import (
    ClarifyPrimitive,
    PlanPrimitive,
    SpecifyPrimitive,
    ValidationGatePrimitive,
)

# ============================================================================
# Example 1: Basic Plan Generation
# ============================================================================


async def example_1_basic_plan() -> None:
    """Example 1: Generate basic implementation plan from spec."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Plan Generation")
    print("=" * 80)

    # Create output directory
    output_dir = Path("./examples/plan_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a sample spec file
    spec_path = output_dir / "cache_feature.spec.md"
    spec_content = """# Feature: Add LRU Cache to LLM Pipeline

## Overview

Add LRU cache with TTL support to reduce LLM API costs by 30-40%.

## Requirements

### Functional Requirements

- Implement LRU eviction policy
- Add TTL-based expiration (default 1 hour)
- Cache responses by prompt hash
- Support cache invalidation
- Provide cache hit/miss metrics

### Non-Functional Requirements

- P99 latency under 100ms for cache operations
- Support 10,000+ cached entries
- Thread-safe for concurrent access

## Architecture

- Use Redis for distributed caching
- Store prompt hash → response mapping
- Monitor with Prometheus metrics

## Acceptance Criteria

- Cache reduces costs by 30%+
- No performance degradation for cache hits
- Cache hit rate > 60% in production
"""
    spec_path.write_text(spec_content, encoding="utf-8")

    # Initialize primitive
    plan = PlanPrimitive(output_dir=str(output_dir))

    # Create workflow context
    context = WorkflowContext(workflow_id="example-1")

    # Execute
    result = await plan.execute({"spec_path": str(spec_path)}, context)

    # Print results
    print("\n✅ Plan generated successfully!")
    print(f"   Plan path: {result['plan_path']}")
    print(f"   Data model path: {result['data_model_path']}")
    print(f"   Phases: {len(result['phases'])}")
    print(f"   Architecture decisions: {len(result['architecture_decisions'])}")
    print(f"   Dependencies: {len(result['dependencies'])}")

    if result["effort_estimate"]:
        effort = result["effort_estimate"]
        print("\n📊 Effort Estimate:")
        print(f"   Story points: {effort['story_points']}")
        print(f"   Hours: {effort['hours']}")
        print(f"   Confidence: {effort['confidence']:.0%}")

    print("\n📋 Implementation Phases:")
    for phase in result["phases"]:
        print(f"   {phase['number']}. {phase['name']} ({phase['estimated_hours']}h)")
        for req in phase["requirements"][:2]:  # Show first 2 requirements
            print(f"      - {req}")


# ============================================================================
# Example 2: Plan with Architecture Context
# ============================================================================


async def example_2_plan_with_architecture_context() -> None:
    """Example 2: Generate plan with existing architecture context."""
    print("\n" + "=" * 80)
    print("Example 2: Plan with Architecture Context")
    print("=" * 80)

    output_dir = Path("./examples/plan_output")

    # Create spec for new API endpoint
    spec_path = output_dir / "api_endpoint.spec.md"
    spec_content = """# Feature: Add User Profile API Endpoint

## Overview

Add RESTful API endpoint for user profile management.

## Requirements

- GET /api/users/{id} - Retrieve user profile
- PUT /api/users/{id} - Update user profile
- POST /api/users/{id}/avatar - Upload avatar
- Authentication required for all endpoints
- Rate limiting: 100 requests/minute per user

## Database

- User table with id, email, name, avatar_url, created_at, updated_at
- Indexed on email for fast lookups

## Integration

- Integrate with existing auth service
- Store avatars in S3-compatible storage
"""
    spec_path.write_text(spec_content, encoding="utf-8")

    # Initialize primitive
    plan = PlanPrimitive(output_dir=str(output_dir))

    # Create workflow context
    context = WorkflowContext(workflow_id="example-2")

    # Execute with architecture context
    result = await plan.execute(
        {
            "spec_path": str(spec_path),
            "architecture_context": {
                "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "existing_patterns": [
                    "REST API with OpenAPI docs",
                    "JWT authentication",
                    "Redis for caching",
                ],
                "existing_services": ["auth-service", "storage-service"],
                "constraints": [
                    "Must use existing PostgreSQL database",
                    "Follow existing API versioning pattern (/api/v1/...)",
                ],
            },
        },
        context,
    )

    print("\n✅ Plan with architecture context generated!")
    print(f"   Plan path: {result['plan_path']}")

    print(f"\n🏗️ Architecture Decisions ({len(result['architecture_decisions'])}):")
    for i, decision in enumerate(result["architecture_decisions"][:2], 1):
        print(f"   {i}. {decision['decision']}")
        print(f"      Rationale: {decision['rationale']}")

    print(f"\n🔗 Dependencies ({len(result['dependencies'])}):")
    for dep in result["dependencies"]:
        blocker = "🔴" if dep["blocker"] else "🟢"
        print(f"   {blocker} {dep['type']}: {dep['name']}")


# ============================================================================
# Example 3: Complete Workflow (Specify → Clarify → Validate → Plan)
# ============================================================================


async def example_3_complete_workflow() -> None:
    """Example 3: Demonstrate complete workflow from requirement to plan."""
    print("\n" + "=" * 80)
    print("Example 3: Complete Workflow (Specify → Clarify → Validate → Plan)")
    print("=" * 80)

    output_dir = Path("./examples/plan_output")

    # Step 1: Specify - Generate initial spec
    print("\n📝 Step 1: Specify - Generate initial specification")
    specify = SpecifyPrimitive(output_dir=str(output_dir))
    context = WorkflowContext(workflow_id="example-3")

    specify_result = await specify.execute(
        {
            "requirement": "Add real-time notification system with WebSocket support and push notifications",
            "project_context": {
                "tech_stack": ["Python", "FastAPI"],
                "existing_features": ["User management", "Authentication"],
            },
        },
        context,
    )

    print(f"   ✅ Initial spec: {specify_result['spec_path']}")
    print(f"   Coverage: {specify_result['coverage_score']:.1%}")

    # Step 2: Clarify - Refine specification
    print("\n🔍 Step 2: Clarify - Refine specification (2 iterations)")
    clarify = ClarifyPrimitive()

    # First clarification
    clarify_result = await clarify.execute(
        {
            "spec_path": specify_result["spec_path"],
            "clarifications": [
                "WebSocket protocol: Use Socket.IO for connection management",
                "Push notifications: Support both FCM (Firebase) and APNs (Apple)",
                "Database: Use PostgreSQL for notification history",
                "Message queue: Use Redis pub/sub for message routing",
            ],
        },
        context,
    )

    print(f"   ✅ After clarification 1: {clarify_result['updated_spec_path']}")

    # Second clarification
    clarify_result = await clarify.execute(
        {
            "spec_path": clarify_result["updated_spec_path"],
            "clarifications": [
                "Notification types: System, user, broadcast",
                "Retry logic: Exponential backoff for failed push notifications",
                "Metrics: Track delivery rate, latency, connection count",
            ],
        },
        context,
    )

    print(f"   ✅ After clarification 2: {clarify_result['updated_spec_path']}")

    # Step 3: Validate - Human approval gate
    print("\n✋ Step 3: Validate - Human approval gate")
    validation_gate = ValidationGatePrimitive()

    # First, try without approval (should prompt)
    validation_result = await validation_gate.execute(
        {
            "artifacts": [clarify_result["updated_spec_path"]],
            "validation_criteria": [
                "Architecture aligns with existing system",
                "All technical decisions are justified",
                "Breaking changes are documented",
            ],
            "reviewer": "tech-lead@example.com",
        },
        context,
    )

    if validation_result["status"] == "pending":
        print("   ⏳ Approval pending")
        print(f"   Instructions: {validation_result['instructions']}")

        # Simulate approval (in real workflow, human would approve)
        import json
        from datetime import UTC, datetime

        approval_path = Path(validation_result["approval_path"])
        approval_data = json.loads(approval_path.read_text(encoding="utf-8"))
        approval_data["status"] = "approved"
        approval_data["feedback"] = "Specification looks good, proceeding with plan"
        approval_data["approved_at"] = datetime.now(UTC).isoformat()
        approval_path.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")

        # Re-run validation
        validation_result = await validation_gate.execute(
            {
                "artifacts": [clarify_result["updated_spec_path"]],
                "validation_criteria": [
                    "Architecture aligns with existing system",
                    "All technical decisions are justified",
                    "Breaking changes are documented",
                ],
                "reviewer": "tech-lead@example.com",
            },
            context,
        )

    print(f"   ✅ Approved by: {validation_result['reviewer']}")
    print(f"   Approved at: {validation_result['timestamp']}")

    # Step 4: Plan - Generate implementation plan
    print("\n📋 Step 4: Plan - Generate implementation plan")
    plan = PlanPrimitive(output_dir=str(output_dir))

    plan_result = await plan.execute(
        {
            "spec_path": clarify_result["updated_spec_path"],
            "architecture_context": {
                "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "existing_patterns": ["REST API", "JWT auth", "WebSocket"],
            },
        },
        context,
    )

    print(f"   ✅ Plan generated: {plan_result['plan_path']}")
    print(f"   Phases: {len(plan_result['phases'])}")
    print(f"   Data models: {len(plan_result.get('data_models', []))}")

    if plan_result["effort_estimate"]:
        effort = plan_result["effort_estimate"]
        print(f"\n   📊 Effort: {effort['story_points']} SP ({effort['hours']}h)")

    print("\n🎯 Complete workflow finished!")
    print("   Requirement → Spec → Clarify → Validate → Plan")
    print("   Ready for implementation (Day 8-9: TasksPrimitive)")


# ============================================================================
# Example 4: Minimal Plan (No Extras)
# ============================================================================


async def example_4_minimal_plan() -> None:
    """Example 4: Generate minimal plan without extra features."""
    print("\n" + "=" * 80)
    print("Example 4: Minimal Plan (No Data Models, No ADRs, No Effort)")
    print("=" * 80)

    output_dir = Path("./examples/plan_output")

    # Create simple spec
    spec_path = output_dir / "simple_feature.spec.md"
    spec_content = """# Feature: Add Search Functionality

## Requirements

- Add search bar to homepage
- Search by title and content
- Display results in grid layout
- Pagination: 20 results per page
"""
    spec_path.write_text(spec_content, encoding="utf-8")

    # Initialize with minimal features
    plan = PlanPrimitive(
        output_dir=str(output_dir),
        include_data_models=False,
        include_architecture_decisions=False,
        estimate_effort=False,
    )

    context = WorkflowContext(workflow_id="example-4")

    result = await plan.execute({"spec_path": str(spec_path)}, context)

    print("\n✅ Minimal plan generated!")
    print(f"   Plan path: {result['plan_path']}")
    print(f"   Data models: {result['data_model_path']}")  # Should be None
    print(f"   Architecture decisions: {len(result['architecture_decisions'])}")  # 0
    print(f"   Effort estimate: {result['effort_estimate']}")  # None

    print("\n📋 Phases (no extra data):")
    for phase in result["phases"]:
        print(f"   {phase['number']}. {phase['name']}")


# ============================================================================
# Example 5: Custom Output Directory
# ============================================================================


async def example_5_custom_output_directory() -> None:
    """Example 5: Use custom output directory per execution."""
    print("\n" + "=" * 80)
    print("Example 5: Custom Output Directory")
    print("=" * 80)

    # Default directory
    default_dir = Path("./examples/plan_output")

    # Custom directories for different features
    feature_dirs = {
        "auth": Path("./examples/features/auth"),
        "payments": Path("./examples/features/payments"),
        "notifications": Path("./examples/features/notifications"),
    }

    for _feature_name, feature_dir in feature_dirs.items():
        feature_dir.mkdir(parents=True, exist_ok=True)

    # Create specs for each feature
    specs = {
        "auth": """# Feature: OAuth2 Integration

## Requirements

- Add OAuth2 authentication
- Support Google and GitHub providers
""",
        "payments": """# Feature: Stripe Integration

## Requirements

- Add Stripe payment processing
- Support credit cards and ACH
""",
        "notifications": """# Feature: Email Notifications

## Requirements

- Send transactional emails
- Use SendGrid API
""",
    }

    # Generate plans in separate directories
    plan = PlanPrimitive(output_dir=str(default_dir))  # Default, but override per call
    context = WorkflowContext(workflow_id="example-5")

    for feature_name, spec_content in specs.items():
        # Write spec
        spec_path = feature_dirs[feature_name] / f"{feature_name}.spec.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        # Generate plan with custom output directory
        result = await plan.execute(
            {
                "spec_path": str(spec_path),
                "output_dir": str(feature_dirs[feature_name]),  # Override
            },
            context,
        )

        print(f"\n✅ {feature_name.capitalize()} plan:")
        print(f"   Output directory: {feature_dirs[feature_name]}")
        print(f"   Plan: {Path(result['plan_path']).name}")


# ============================================================================
# Main
# ============================================================================


async def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PlanPrimitive Examples")
    print("=" * 80)
    print("\nDemonstrates plan generation from validated specifications.")
    print("Part of the Speckit workflow: Specify → Clarify → Validate → Plan")

    await example_1_basic_plan()
    await example_2_plan_with_architecture_context()
    await example_3_complete_workflow()
    await example_4_minimal_plan()
    await example_5_custom_output_directory()

    print("\n" + "=" * 80)
    print("✅ All examples completed successfully!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - examples/plan_output/plan.md (various features)")
    print("  - examples/plan_output/data-model.md (where applicable)")
    print("  - examples/features/{auth,payments,notifications}/plan.md")
    print("\nNext: TasksPrimitive (Day 8-9) - Break plan into concrete tasks")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
