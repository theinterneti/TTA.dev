"""
Example: ValidationGatePrimitive - Human Approval Gates

This example demonstrates how ValidationGatePrimitive enforces human validation
before proceeding with implementation. It shows:

1. Basic validation gate with pending approval
2. Programmatic approval/rejection
3. Complete workflow: Specify → Clarify → Validate → Plan
4. Checking approval status and reusing approvals
5. Multiple artifacts validation

Phase 1: File-based approval mechanism (no interactive blocking)
Phase 2: Web UI, multi-reviewer, approval delegation (future)

Design Philosophy:
- Async-compatible (doesn't block execution)
- File-based approvals (edit JSON to approve/reject)
- Reuses existing approval decisions
- Comprehensive audit trail
"""

import asyncio
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import (
    ClarifyPrimitive,
    SpecifyPrimitive,
    ValidationGatePrimitive,
)


async def example1_basic_validation_gate() -> None:
    """
    Example 1: Basic Validation Gate with Pending Approval

    Shows how to create a pending approval that can be manually reviewed.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Validation Gate with Pending Approval")
    print("=" * 80 + "\n")

    # Create validation gate
    validation_gate = ValidationGatePrimitive(
        timeout_seconds=3600,  # 1 hour
        auto_approve_on_timeout=False,
        require_feedback_on_rejection=True,
    )

    # Create sample specification file
    spec_path = Path("examples/feature.spec.md")
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        """# Feature Specification: Add Caching

## Overview
Implement LRU cache with TTL for expensive operations.

## Technical Details
- Cache size: 1000 entries
- TTL: 3600 seconds
- Thread-safe with asyncio.Lock

## Test Coverage
- Cache hit/miss scenarios
- TTL expiration
- LRU eviction
- Thread safety
"""
    )

    # Execute validation gate
    context = WorkflowContext(correlation_id="example1")
    result = await validation_gate.execute(
        {
            "artifacts": [str(spec_path)],
            "validation_criteria": {
                "min_coverage": 0.9,
                "required_sections": ["Overview", "Technical Details"],
                "completeness_check": True,
            },
            "reviewer": "tech-lead@example.com",
            "context_info": {
                "feature": "caching",
                "priority": "high",
            },
        },
        context,
    )

    print("Validation Result:")
    print(f"  Status: {result['status']}")
    print(f"  Approved: {result['approved']}")
    print(f"  Approval Path: {result['approval_path']}")
    print(f"  Validation Results: {result['validation_results']}")
    print(f"\nInstructions:\n{result['instructions']}")

    # Cleanup
    spec_path.unlink()


async def example2_programmatic_approval() -> None:
    """
    Example 2: Programmatic Approval/Rejection

    Shows how to approve or reject validations programmatically (useful for testing
    or automated workflows).
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Programmatic Approval/Rejection")
    print("=" * 80 + "\n")

    # Create validation gate
    validation_gate = ValidationGatePrimitive()

    # Create sample specification
    spec_path = Path("examples/feature2.spec.md")
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text("# Feature Spec\n## Overview\nSimple feature.")

    # Create pending approval
    context = WorkflowContext(correlation_id="example2")
    result = await validation_gate.execute(
        {
            "artifacts": [str(spec_path)],
            "validation_criteria": {"min_coverage": 0.8},
            "reviewer": "tech-lead@example.com",
        },
        context,
    )

    approval_path = Path(result["approval_path"])
    print(f"Created pending approval at: {approval_path}")

    # Option A: Approve programmatically
    print("\nApproving validation...")
    await validation_gate.approve(
        approval_path=approval_path,
        reviewer="tech-lead@example.com",
        feedback="Specification looks good. All sections are complete.",
    )

    # Check approval status
    status = await validation_gate.check_approval_status(approval_path)
    print(f"  Approval Status: {status['status']}")
    print(f"  Approved: {status['approved']}")
    print(f"  Feedback: {status.get('feedback', 'N/A')}")

    # Option B: Reject programmatically (demonstration with different spec)
    print("\nDemonstrating rejection...")
    spec_path2 = Path("examples/feature2b.spec.md")
    spec_path2.write_text("# Feature Spec B\n## Overview\nAnother feature.")

    result2 = await validation_gate.execute(
        {
            "artifacts": [str(spec_path2)],
            "validation_criteria": {"min_coverage": 0.8},
            "reviewer": "tech-lead@example.com",
        },
        context,
    )
    approval_path2 = Path(result2["approval_path"])

    await validation_gate.reject(
        approval_path=approval_path2,
        reviewer="tech-lead@example.com",
        feedback="Missing performance requirements. Please add latency SLOs.",
    )

    status2 = await validation_gate.check_approval_status(approval_path2)
    print(f"  Rejection Status: {status2['status']}")
    print(f"  Approved: {status2['approved']}")
    print(f"  Feedback: {status2['feedback']}")

    # Cleanup
    spec_path.unlink()
    spec_path2.unlink()
    approval_path.unlink()
    approval_path2.unlink()


async def example3_complete_workflow() -> None:
    """
    Example 3: Complete Workflow - Specify → Clarify → Validate → Plan

    Shows how ValidationGatePrimitive fits into the complete Speckit workflow.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Complete Workflow - Specify → Clarify → Validate")
    print("=" * 80 + "\n")

    # Step 1: Specify
    print("Step 1: Creating initial specification...")
    specify = SpecifyPrimitive()
    context = WorkflowContext(correlation_id="example3")

    spec_result = await specify.execute(
        {
            "requirement": "Add distributed tracing to all primitives",
            "output_dir": "examples",
        },
        context,
    )
    print(f"  ✓ Created spec: {spec_result['spec_path']}")
    print(f"  Coverage Score: {spec_result['coverage_score']:.2f}")

    # Step 2: Clarify
    print("\nStep 2: Refining specification...")
    clarify = ClarifyPrimitive()

    clarify_result = await clarify.execute(
        {
            "spec_path": spec_result["spec_path"],
            "gaps": spec_result["gaps"],
            "current_coverage": spec_result["coverage_score"],
            "answers": {
                "What tracing library should be used?": "OpenTelemetry",
                "What metrics should be collected?": "Execution time, success rate, error rate",
                "How should context be propagated?": "Via WorkflowContext",
            },
        },
        context,
    )
    print(f"  ✓ Updated spec: {clarify_result['updated_spec_path']}")
    print(f"  New Gaps: {len(clarify_result.get('new_gaps', []))}")

    # Step 3: Validate
    print("\nStep 3: Validating refined specification...")
    validation_gate = ValidationGatePrimitive()

    validation_result = await validation_gate.execute(
        {
            "artifacts": [clarify_result["updated_spec_path"]],
            "validation_criteria": {
                "min_coverage": 0.9,
                "required_sections": [
                    "Overview",
                    "Technical Details",
                    "Implementation Plan",
                ],
            },
            "reviewer": "tech-lead@example.com",
            "context_info": {
                "feature": "distributed-tracing",
                "priority": "high",
                "sprint": "2025-Q1",
            },
        },
        context,
    )

    print(f"  Status: {validation_result['status']}")
    print(f"  Approval Path: {validation_result['approval_path']}")

    # For demo: Auto-approve
    await validation_gate.approve(
        approval_path=Path(validation_result["approval_path"]),
        reviewer="tech-lead@example.com",
        feedback="Comprehensive specification. Ready for implementation planning.",
    )

    status = await validation_gate.check_approval_status(Path(validation_result["approval_path"]))
    print(f"  ✓ Approved: {status['approved']}")
    print(f"  Feedback: {status['feedback']}")

    # Step 4: Plan (placeholder - not implemented yet)
    print("\nStep 4: Generate implementation plan (coming in Day 6-7)...")
    print("  → plan.md with detailed steps")
    print("  → data-model.md with schemas")

    # Cleanup
    Path(spec_result["spec_path"]).unlink()
    Path(validation_result["approval_path"]).unlink()


async def example4_reuse_approvals() -> None:
    """
    Example 4: Checking Approval Status and Reusing Approvals

    Shows how to check approval status and reuse existing approval decisions
    without re-prompting the reviewer.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Checking Approval Status and Reusing Approvals")
    print("=" * 80 + "\n")

    validation_gate = ValidationGatePrimitive()

    # Create sample spec
    spec_path = Path("examples/feature4.spec.md")
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text("# Feature Spec\n## Overview\nSample feature.")

    context = WorkflowContext(correlation_id="example4")

    # First execution: Create pending approval
    print("First execution: Creating pending approval...")
    result1 = await validation_gate.execute(
        {
            "artifacts": [str(spec_path)],
            "validation_criteria": {"min_coverage": 0.8},
            "reviewer": "tech-lead@example.com",
        },
        context,
    )
    approval_path = Path(result1["approval_path"])
    print(f"  Status: {result1['status']}")
    print(f"  Approval Path: {approval_path}")

    # Approve it
    print("\nApproving the specification...")
    await validation_gate.approve(
        approval_path=approval_path,
        reviewer="tech-lead@example.com",
        feedback="Looks good!",
    )

    # Second execution: Reuse existing approval
    print("\nSecond execution: Reusing existing approval...")
    result2 = await validation_gate.execute(
        {
            "artifacts": [str(spec_path)],
            "validation_criteria": {"min_coverage": 0.8},
            "reviewer": "tech-lead@example.com",
        },
        context,
    )
    print(f"  Approved: {result2['approved']}")
    print(f"  Reused Approval: {result2.get('reused_approval', False)}")
    print(f"  Feedback: {result2.get('feedback', 'N/A')}")

    # Check various statuses
    print("\nChecking approval status...")
    status = await validation_gate.check_approval_status(str(approval_path))
    print(f"  Current Status: {status['status']}")
    print(f"  Approved: {status['approved']}")

    # Check nonexistent approval
    print("\nChecking nonexistent approval...")
    nonexistent_status = await validation_gate.check_approval_status(
        "examples/.approvals/nonexistent.approval.json"
    )
    print(f"  Status: {nonexistent_status['status']}")
    print(f"  Approved: {nonexistent_status['approved']}")

    # Cleanup
    spec_path.unlink()
    approval_path.unlink()


async def example5_multiple_artifacts() -> None:
    """
    Example 5: Multiple Artifacts Validation

    Shows how to validate multiple artifacts (specs, plans, data models) together
    before proceeding to implementation.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Multiple Artifacts Validation")
    print("=" * 80 + "\n")

    validation_gate = ValidationGatePrimitive()

    # Create multiple artifacts
    spec_path = Path("examples/feature.spec.md")
    plan_path = Path("examples/feature.plan.md")
    datamodel_path = Path("examples/feature.data-model.md")

    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text("# Feature Specification\n## Overview\nComplete feature spec.")
    plan_path.write_text("# Implementation Plan\n## Steps\n1. Step one\n2. Step two")
    datamodel_path.write_text("# Data Model\n## Schemas\n- User\n- Session\n- Event")

    context = WorkflowContext(correlation_id="example5")

    print("Validating multiple artifacts together...")
    result = await validation_gate.execute(
        {
            "artifacts": [str(spec_path), str(plan_path), str(datamodel_path)],
            "validation_criteria": {
                "min_coverage": 0.9,
                "required_sections": ["Overview", "Steps", "Schemas"],
                "completeness_check": True,
            },
            "reviewer": "tech-lead@example.com",
            "context_info": {
                "feature": "multi-artifact-validation",
                "artifacts_count": 3,
            },
        },
        context,
    )

    print(f"  Status: {result['status']}")
    print(f"  Approved: {result['approved']}")
    print(f"  Approval Path: {result['approval_path']}")
    print(
        f"  Artifacts in Approval: {len(result.get('validation_results', {}).get('artifacts_checked', []))}"
    )

    # Check approval filename
    approval_filename = Path(result["approval_path"]).name
    print(f"  Approval Filename: {approval_filename}")
    print("  (Filename includes first 3 artifact names for multiple artifacts)")

    # Cleanup
    spec_path.unlink()
    plan_path.unlink()
    datamodel_path.unlink()


async def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 80)
    print("VALIDATION GATE PRIMITIVE EXAMPLES")
    print("=" * 80)
    print("\nValidationGatePrimitive enforces human validation before implementation.")
    print("Phase 1: File-based approval mechanism (no interactive blocking)")
    print("Phase 2: Web UI, multi-reviewer, approval delegation (future)\n")

    # Create examples directory
    Path("examples").mkdir(exist_ok=True)
    Path("examples/.approvals").mkdir(exist_ok=True)

    try:
        await example1_basic_validation_gate()
        await example2_programmatic_approval()
        await example3_complete_workflow()
        await example4_reuse_approvals()
        await example5_multiple_artifacts()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 80 + "\n")

        print("Key Takeaways:")
        print("1. ValidationGatePrimitive creates pending approvals in .approvals/ directory")
        print("2. Phase 1 returns 'pending' status with instructions (no blocking)")
        print("3. Approvals can be manual (edit JSON) or programmatic (utility methods)")
        print("4. Existing approval decisions are automatically reused")
        print("5. Multiple artifacts can be validated together")
        print("6. Full audit trail with timestamps and reviewer info")
        print("\nNext Steps:")
        print("- Days 6-7: PlanPrimitive (plan.md + data-model.md generation)")
        print("- Days 8-9: TasksPrimitive (ordered task breakdown)")
        print("- Day 10: Integration example (5-primitive workflow)")

    finally:
        # Cleanup
        import shutil

        if Path("examples").exists():
            shutil.rmtree("examples")


if __name__ == "__main__":
    asyncio.run(main())
