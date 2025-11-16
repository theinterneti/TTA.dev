"""
ClarifyPrimitive Examples - Iterative Specification Refinement

Demonstrates the ClarifyPrimitive for refining specifications generated
by SpecifyPrimitive through structured questions and answers.

Examples:
1. Basic Specify → Clarify workflow with batch answers
2. Iterative refinement with multiple rounds
3. Coverage improvement tracking
4. Error handling

Run: uv run python examples/speckit_clarify_example.py
"""

import asyncio
import tempfile
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import ClarifyPrimitive, SpecifyPrimitive


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")


async def example_1_basic_clarify_workflow() -> None:
    """
    Example 1: Basic Specify → Clarify Workflow

    Demonstrates:
    - Creating initial spec with SpecifyPrimitive
    - Refining spec with ClarifyPrimitive using batch answers
    - Coverage improvement tracking
    """
    print_header("Example 1: Basic Specify → Clarify Workflow")

    # Create primitives
    specify = SpecifyPrimitive()
    clarify = ClarifyPrimitive(max_iterations=3, target_coverage=0.9, questions_per_gap=2)

    # Create temporary directory for specs
    with tempfile.TemporaryDirectory() as tmpdir:
        context = WorkflowContext(
            correlation_id="example-1",
            data={"output_dir": tmpdir},
        )

        # Step 1: Generate initial specification
        print("Step 1: Generating initial specification...")
        spec_result = await specify.execute(
            {
                "requirement": "Add caching layer to improve API response times",
                "context": {
                    "current_system": "REST API with database queries",
                    "performance_issue": "Response times >2s for common queries",
                },
            },
            context,
        )

        print(f"✓ Specification created: {spec_result['spec_path']}")
        print(f"  Initial coverage: {spec_result['coverage_score']:.2f}")
        print(f"  Gaps identified: {len(spec_result['gaps'])}")
        for gap in spec_result["gaps"][:3]:  # Show first 3 gaps
            print(f"    - {gap}")
        if len(spec_result["gaps"]) > 3:
            print(f"    ... and {len(spec_result['gaps']) - 3} more")

        # Step 2: Prepare answers for clarification
        print("\nStep 2: Preparing answers for key questions...")
        answers = {
            "Problem Statement": "Users experience slow response times (>2s) "
            "for frequently accessed API endpoints. Target: <200ms for 95th percentile.",
            "Proposed Solution": "Implement Redis-based caching layer with "
            "TTL-based expiration and cache invalidation on data updates.",
            "Success Criteria": "95th percentile response time <200ms for cached "
            "endpoints. Cache hit rate >80%. No stale data served to users.",
            "Functional Requirements": "Cache GET requests with configurable TTL. "
            "Invalidate cache on PUT/POST/DELETE. Support cache warming for common queries.",
            "Non-Functional Requirements": "Cache layer should not increase P99 "
            "latency by >10ms. Redis cluster should handle 10k ops/sec. Monitor cache hit rates.",
        }

        # Step 3: Refine specification with answers
        print("\nStep 3: Refining specification with answers...")
        clarify_result = await clarify.execute(
            {
                "spec_path": spec_result["spec_path"],
                "gaps": spec_result["gaps"],
                "current_coverage": spec_result["coverage_score"],
                "answers": answers,
            },
            context,
        )

        print(f"✓ Specification refined: {clarify_result['updated_spec_path']}")
        print(
            f"  Final coverage: {clarify_result['final_coverage']:.2f} "
            f"(+{clarify_result['coverage_improvement']:.2f})"
        )
        print(f"  Iterations used: {clarify_result['iterations_used']}")
        print(f"  Remaining gaps: {len(clarify_result['remaining_gaps'])}")
        if clarify_result["remaining_gaps"]:
            print("  Sections still needing clarification:")
            for gap in clarify_result["remaining_gaps"][:5]:
                print(f"    - {gap}")

        # Show clarification history
        print("\n  Clarification History:")
        for entry in clarify_result["clarification_history"]:
            print(f"    Iteration {entry['iteration']}:")
            print(f"      Questions asked: {len(entry['questions'])}")
            print(f"      Gaps addressed: {entry['gaps_addressed']}")
            print(f"      Coverage: {entry['coverage_before']:.2f} → {entry['coverage_after']:.2f}")


async def example_2_iterative_refinement() -> None:
    """
    Example 2: Iterative Refinement with Multiple Rounds

    Demonstrates:
    - Multiple refinement iterations
    - Incremental coverage improvement
    - Reaching target coverage
    """
    print_header("Example 2: Iterative Refinement (Multiple Rounds)")

    clarify = ClarifyPrimitive(
        max_iterations=5,  # Allow more iterations
        target_coverage=0.95,  # Higher target
        questions_per_gap=3,  # More questions per gap
    )

    # Create a test spec with many gaps
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "feature.spec.md"

        # Create a minimal spec with multiple gaps
        spec_content = """# Feature Specification: Multi-Tenant Authorization

## Problem Statement
[CLARIFY: What is the specific problem?]

## Proposed Solution
[CLARIFY: What approach will be used?]

## Success Criteria
[CLARIFY: How will success be measured?]

## Functional Requirements
[CLARIFY: What are the core requirements?]

## Non-Functional Requirements
[CLARIFY: What are performance/security requirements?]

## Data Model
[CLARIFY: What data structures are needed?]
"""
        spec_path.write_text(spec_content)

        context = WorkflowContext(correlation_id="example-2")

        # Round 1: Answer problem and solution
        print("Round 1: Addressing problem and solution...")
        round1_answers = {
            "Problem Statement": "Need to support multiple tenants with isolated data "
            "and role-based access control within each tenant.",
            "Proposed Solution": "Implement tenant_id scoping on all data models with "
            "middleware to enforce tenant isolation. Add role hierarchy (admin/member/viewer).",
        }

        result1 = await clarify.execute(
            {
                "spec_path": str(spec_path),
                "gaps": [
                    "Problem Statement",
                    "Proposed Solution",
                    "Success Criteria",
                    "Functional Requirements",
                    "Non-Functional Requirements",
                    "Data Model",
                ],
                "current_coverage": 0.0,
                "answers": round1_answers,
            },
            context,
        )

        print("✓ Round 1 complete")
        print(f"  Coverage: {result1['final_coverage']:.2f}")
        print(f"  Remaining gaps: {len(result1['remaining_gaps'])}")

        # Round 2: Answer success criteria and requirements
        print("\nRound 2: Adding success criteria and requirements...")
        round2_answers = {
            "Success Criteria": "All data queries scoped to tenant. No cross-tenant "
            "data leakage. Role permissions enforced. <10ms authorization overhead.",
            "Functional Requirements": "Tenant scoping on all models. Role-based "
            "permissions (admin/member/viewer). API key per tenant. Tenant switching UI.",
        }

        result2 = await clarify.execute(
            {
                "spec_path": str(spec_path),
                "gaps": result1["remaining_gaps"],
                "current_coverage": result1["final_coverage"],
                "answers": round2_answers,
            },
            context,
        )

        print("✓ Round 2 complete")
        print(
            f"  Coverage: {result2['final_coverage']:.2f} (+{result2['coverage_improvement']:.2f})"
        )
        print(f"  Remaining gaps: {len(result2['remaining_gaps'])}")

        # Round 3: Complete the spec
        print("\nRound 3: Completing specification...")
        round3_answers = {
            "Non-Functional Requirements": "Support 1000 tenants. Authorization "
            "cache to minimize DB queries. Audit log for all permission checks.",
            "Data Model": "Add tenant_id column to all tables. Create tenants, "
            "tenant_users, and roles tables. Foreign key constraints enforce isolation.",
        }

        result3 = await clarify.execute(
            {
                "spec_path": str(spec_path),
                "gaps": result2["remaining_gaps"],
                "current_coverage": result2["final_coverage"],
                "answers": round3_answers,
            },
            context,
        )

        print("✓ Round 3 complete")
        print(
            f"  Final coverage: {result3['final_coverage']:.2f} "
            f"(+{result3['coverage_improvement']:.2f})"
        )
        print(f"  Target reached: {result3['target_reached']}")
        print(f"  Total iterations: {result3['iterations_used']}")

        # Show progression
        print("\n  Coverage Progression:")
        print("    Initial:  0.00")
        print(f"    Round 1: {result1['final_coverage']:.2f}")
        print(f"    Round 2: {result2['final_coverage']:.2f}")
        print(f"    Round 3: {result3['final_coverage']:.2f}")


async def example_3_integration_with_specify() -> None:
    """
    Example 3: Seamless Specify → Clarify Integration

    Demonstrates:
    - Using SpecifyPrimitive output directly as ClarifyPrimitive input
    - Workflow chaining
    - Composition via >> operator (future enhancement)
    """
    print_header("Example 3: Seamless Specify → Clarify Integration")

    specify = SpecifyPrimitive()
    clarify = ClarifyPrimitive(max_iterations=2, target_coverage=0.85)

    with tempfile.TemporaryDirectory() as tmpdir:
        context = WorkflowContext(
            correlation_id="example-3",
            data={"output_dir": tmpdir},
        )

        # Generate spec
        print("Generating specification...")
        spec_result = await specify.execute(
            {
                "requirement": "Add real-time notifications for order status updates",
                "context": {"current_system": "E-commerce platform with order tracking"},
            },
            context,
        )

        print(f"✓ Spec created with {spec_result['coverage_score']:.2f} coverage")

        # Prepare targeted answers for most critical gaps
        print("\nRefining specification...")
        answers = {
            "Problem Statement": "Customers want instant updates when order status "
            "changes instead of manually refreshing the page. Reduces support inquiries.",
            "Proposed Solution": "WebSocket-based real-time notifications with "
            "fallback to polling for older browsers. Push notifications for mobile app.",
            "Success Criteria": "Notifications delivered within 5s of status change. "
            "Support 10k concurrent WebSocket connections. <1% message delivery failure.",
        }

        # Use specify output directly as clarify input
        clarify_result = await clarify.execute(
            {
                "spec_path": spec_result["spec_path"],
                "gaps": spec_result["gaps"],
                "current_coverage": spec_result["coverage_score"],
                "answers": answers,
            },
            context,
        )

        print(f"✓ Spec refined to {clarify_result['final_coverage']:.2f} coverage")
        print(
            f"  Improvement: +{clarify_result['coverage_improvement']:.2f} "
            f"in {clarify_result['iterations_used']} iterations"
        )

        # Future: Workflow composition
        print("\n  Future Enhancement:")
        print("    # Compose primitives with >> operator")
        print("    workflow = specify >> clarify")
        print("    result = await workflow.execute(input_data, context)")


async def example_4_error_handling() -> None:
    """
    Example 4: Error Handling

    Demonstrates:
    - Handling missing spec files
    - Handling invalid input
    - Graceful degradation
    """
    print_header("Example 4: Error Handling")

    clarify = ClarifyPrimitive()
    context = WorkflowContext(correlation_id="example-4")

    # Error 1: Missing spec file
    print("Error Case 1: Missing spec file")
    try:
        await clarify.execute(
            {
                "spec_path": "/nonexistent/path/spec.md",
                "gaps": ["Problem Statement"],
                "current_coverage": 0.0,
            },
            context,
        )
    except FileNotFoundError as e:
        print(f"✓ Handled gracefully: {e}")

    # Error 2: Missing required field
    print("\nError Case 2: Missing required field")
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "test.spec.md"
        spec_path.write_text("# Test Spec\n\n## Problem Statement\n[CLARIFY: What?]")

        try:
            await clarify.execute(
                {
                    "spec_path": str(spec_path),
                    # Missing 'gaps' field
                    "current_coverage": 0.0,
                },
                context,
            )
        except (KeyError, ValueError) as e:
            print(f"✓ Validation error: {type(e).__name__}")

    # Error 3: Malformed spec (missing sections)
    print("\nError Case 3: Malformed spec (minimal sections)")
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "malformed.spec.md"
        spec_path.write_text("# Just a title\n\nNo sections here.")

        result = await clarify.execute(
            {
                "spec_path": str(spec_path),
                "gaps": [],  # No gaps in malformed spec
                "current_coverage": 1.0,  # Already "complete"
            },
            context,
        )

        print("✓ Handled gracefully:")
        print(f"  Final coverage: {result['final_coverage']:.2f}")
        print(f"  Iterations: {result['iterations_used']}")
        print(f"  Target reached: {result['target_reached']}")


async def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ClarifyPrimitive Examples")
    print("Iterative Specification Refinement")
    print("=" * 60)

    await example_1_basic_clarify_workflow()
    await example_2_iterative_refinement()
    await example_3_integration_with_specify()
    await example_4_error_handling()

    print("\n" + "=" * 60)
    print("All Examples Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. ClarifyPrimitive refines specs through structured questions")
    print("2. Iterative refinement improves coverage incrementally")
    print("3. Seamlessly integrates with SpecifyPrimitive output")
    print("4. Robust error handling for production use")
    print("\nNext Steps:")
    print("- Try with your own requirements")
    print("- Experiment with different iteration limits")
    print("- Integrate into your development workflow")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
