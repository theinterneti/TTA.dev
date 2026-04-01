"""Spec-Driven Development (SDD) workflow example.

Shows the complete speckit pipeline:
    SpecifyPrimitive → ClarifyPrimitive → PlanPrimitive → TasksPrimitive → ValidationGatePrimitive

Usage:
    # Mock mode (default, no LLM needed)
    uv run python examples/sdd_workflow.py

    # Live mode (template-based, no LLM required — writes files to ./sdd-demo/)
    MOCK_MODE=false uv run python examples/sdd_workflow.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Make the package importable when run directly from the repo root
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# MOCK_MODE flag — True by default so CI runs without file I/O or API keys.
# Override:  MOCK_MODE=false uv run python examples/sdd_workflow.py
# ---------------------------------------------------------------------------
MOCK_MODE: bool = os.environ.get("MOCK_MODE", "true").lower() != "false"

from ttadev.primitives.core.base import WorkflowContext  # noqa: E402
from ttadev.primitives.speckit import (  # noqa: E402
    ClarifyPrimitive,
    PlanPrimitive,
    SpecifyPrimitive,
    TasksPrimitive,
    ValidationGatePrimitive,
)
from ttadev.primitives.testing.mocks import MockPrimitive  # noqa: E402

REQUIREMENT = "Add Redis caching to the LLM pipeline with configurable TTL and LRU eviction"


def build_mock_pipeline() -> tuple[object, list[MockPrimitive]]:
    """Build a MockPrimitive pipeline that simulates the full SDD flow.

    Each stage is a MockPrimitive whose return_value carries plausible-looking
    output that becomes the next stage's input via the >> (SequentialPrimitive)
    operator.

    Returns:
        Tuple of (composed_pipeline, list_of_stage_mocks) so callers can
        inspect per-stage return values for display after execution.
    """
    mock_specify = MockPrimitive(
        name="specify",
        return_value={
            "spec_path": "docs/specs/add-redis-caching-to-the.spec.md",
            "coverage_score": 0.40,
            "gaps": [
                "Problem Statement",
                "Non-Functional Requirements",
                "Data Model",
                "Unit Tests",
                "Integration Tests",
                "Performance Tests",
            ],
            "sections_completed": {
                "Proposed Solution": "complete",
                "Functional Requirements": "complete",
                "Problem Statement": "incomplete",
            },
        },
    )

    mock_clarify = MockPrimitive(
        name="clarify",
        return_value={
            "updated_spec_path": "docs/specs/add-redis-caching-to-the.spec.md",
            "final_coverage": 0.87,
            "coverage_improvement": 0.47,
            "iterations_used": 2,
            "remaining_gaps": ["Performance Tests"],
            "clarification_history": [
                {
                    "iteration": 1,
                    "coverage_before": 0.40,
                    "coverage_after": 0.73,
                    "gaps_addressed": 4,
                },
                {
                    "iteration": 2,
                    "coverage_before": 0.73,
                    "coverage_after": 0.87,
                    "gaps_addressed": 1,
                },
            ],
            "target_reached": False,
        },
    )

    mock_plan = MockPrimitive(
        name="plan",
        return_value={
            "plan_path": "sdd-demo/plan.md",
            "data_model_path": "sdd-demo/data-model.md",
            "phases": [
                {
                    "number": 1,
                    "name": "Infrastructure Setup",
                    "description": "Add Redis client and connection pooling",
                    "estimated_hours": 8.0,
                    "requirements": ["redis>=5.0", "connection pool config"],
                },
                {
                    "number": 2,
                    "name": "Cache Implementation",
                    "description": "Implement LRU cache with TTL in CachePrimitive",
                    "estimated_hours": 16.0,
                    "requirements": ["CachePrimitive extension", "TTL support"],
                },
                {
                    "number": 3,
                    "name": "Testing & Integration",
                    "description": "Unit tests, integration tests, benchmarks",
                    "estimated_hours": 8.0,
                    "requirements": ["test suite", "performance benchmarks"],
                },
            ],
            "architecture_decisions": [
                {
                    "decision": "Use Redis as cache backend",
                    "rationale": "Scalable, supports TTL natively, cluster-ready",
                    "alternatives": ["in-memory dict", "Memcached"],
                    "tradeoffs": "External dependency vs. simplicity",
                }
            ],
            "effort_estimate": {"story_points": 13, "hours": 32.0},
            "dependencies": [{"name": "redis", "version": ">=5.0"}],
        },
    )

    mock_tasks = MockPrimitive(
        name="tasks",
        return_value={
            "tasks_path": "sdd-demo/tasks.md",
            "tasks": [
                {
                    "id": "T-001",
                    "title": "Add Redis dependency and connection configuration",
                    "phase": "Infrastructure Setup",
                    "priority": "critical",
                    "story_points": 2,
                    "hours": 4.0,
                    "dependencies": [],
                    "is_critical_path": True,
                },
                {
                    "id": "T-002",
                    "title": "Implement RedisCache backend class",
                    "phase": "Cache Implementation",
                    "priority": "high",
                    "story_points": 5,
                    "hours": 12.0,
                    "dependencies": ["T-001"],
                    "is_critical_path": True,
                },
                {
                    "id": "T-003",
                    "title": "Extend CachePrimitive with TTL and LRU eviction",
                    "phase": "Cache Implementation",
                    "priority": "high",
                    "story_points": 3,
                    "hours": 8.0,
                    "dependencies": ["T-002"],
                    "is_critical_path": True,
                },
                {
                    "id": "T-004",
                    "title": "Write unit tests for cache layer",
                    "phase": "Testing & Integration",
                    "priority": "medium",
                    "story_points": 2,
                    "hours": 4.0,
                    "dependencies": ["T-002"],
                    "is_critical_path": False,
                },
                {
                    "id": "T-005",
                    "title": "Integration tests and performance benchmarks",
                    "phase": "Testing & Integration",
                    "priority": "medium",
                    "story_points": 1,
                    "hours": 4.0,
                    "dependencies": ["T-003", "T-004"],
                    "is_critical_path": True,
                },
            ],
            "critical_path": ["T-001", "T-002", "T-003", "T-005"],
            "parallel_streams": {"P-001": ["T-004"]},
            "total_effort": {"story_points": 13, "hours": 32.0},
        },
    )

    mock_validate = MockPrimitive(
        name="validate",
        return_value={
            "approved": True,
            "feedback": "Spec and plan look comprehensive. Critical path is clear.",
            "timestamp": "2026-01-15T09:00:00+00:00",
            "reviewer": "automated-gate",
            "validation_results": {
                "artifacts_exist": True,
                "coverage_check": {"required": 0.8, "status": "manual_check_required"},
            },
            "approval_path": "sdd-demo/.approvals/plan.approval.json",
            "status": "approved",
        },
    )

    # Compose with >> — creates a SequentialPrimitive chain
    pipeline = mock_specify >> mock_clarify >> mock_plan >> mock_tasks >> mock_validate
    return pipeline, [mock_specify, mock_clarify, mock_plan, mock_tasks, mock_validate]


async def run_live_pipeline(requirement: str, ctx: WorkflowContext) -> dict:
    """Run the real speckit pipeline step-by-step.

    The Phase 1 primitives are template-based and do not require any LLM
    API key.  Output keys are remapped between stages where necessary.

    Args:
        requirement: Free-form feature description to drive the pipeline.
        ctx: Workflow context for tracing and observability.

    Returns:
        Dictionary with spec_path, plan_path, tasks, critical_path, validation.
    """
    output_root = Path("./sdd-demo")
    specs_dir = output_root / "specs"
    plan_dir = output_root / "plan"
    tasks_dir = output_root / "tasks"

    # Step 1: Specify
    print("\n📝  Step 1/5: SpecifyPrimitive — generating formal spec...")
    specify = SpecifyPrimitive(output_dir=str(specs_dir))
    specify_result = await specify.execute(
        {"requirement": requirement, "context": {"tech_stack": ["Python", "Redis"]}},
        ctx,
    )
    spec_path = specify_result["spec_path"]
    print(f"   ✅  Spec: {spec_path}")
    print(f"   📊  Coverage: {specify_result['coverage_score']:.0%}")
    gaps_preview = ", ".join(specify_result["gaps"][:3])
    print(f"   🔍  Gaps (first 3): {gaps_preview}...")

    # Step 2: Clarify
    print("\n💬  Step 2/5: ClarifyPrimitive — refining gaps...")
    clarify = ClarifyPrimitive(max_iterations=2)
    clarify_result = await clarify.execute(
        {
            "spec_path": spec_path,
            "gaps": specify_result["gaps"],
            "current_coverage": specify_result["coverage_score"],
            "answers": {
                "Problem Statement": "LLM inference is slow and expensive without caching.",
                "Non-Functional Requirements": "Cache hit rate >80%, latency overhead <5ms.",
                "Data Model": (
                    "CacheEntry { key: str, value: bytes, ttl: int, created_at: datetime }"
                ),
                "Unit Tests": "Test cache hit/miss, TTL expiry, LRU eviction.",
                "Integration Tests": "Full pipeline with Redis stub.",
                "Performance Tests": "Benchmark cache vs. no-cache for repeated prompts.",
            },
        },
        ctx,
    )
    refined_spec_path = clarify_result["updated_spec_path"]
    improvement = clarify_result["coverage_improvement"]
    print(f"   ✅  Refined spec: {refined_spec_path}")
    print(f"   📊  Coverage: {clarify_result['final_coverage']:.0%} (+{improvement:.0%})")

    # Step 3: Plan
    print("\n📋  Step 3/5: PlanPrimitive — generating implementation plan...")
    plan = PlanPrimitive(output_dir=str(plan_dir))
    plan_result = await plan.execute({"spec_path": refined_spec_path}, ctx)
    plan_path = plan_result["plan_path"]
    print(f"   ✅  Plan: {plan_path}")
    print(f"   📦  Phases: {len(plan_result['phases'])}")
    if plan_result.get("effort_estimate"):
        effort = plan_result["effort_estimate"]
        print(
            f"   ⏱️   Estimate: {effort.get('story_points', '?')} SP / {effort.get('hours', '?')}h"
        )

    # Step 4: Tasks
    print("\n✅  Step 4/5: TasksPrimitive — breaking plan into tasks...")
    tasks_primitive = TasksPrimitive(output_dir=str(tasks_dir))
    tasks_input: dict = {"plan_path": plan_path}
    if plan_result.get("data_model_path"):
        tasks_input["data_model_path"] = plan_result["data_model_path"]
    tasks_result = await tasks_primitive.execute(tasks_input, ctx)
    cp_preview = " → ".join(tasks_result["critical_path"][:4])
    print(f"   ✅  Tasks: {tasks_result['tasks_path']}")
    print(f"   🗂️   Count: {len(tasks_result['tasks'])} tasks")
    print(f"   🔴  Critical path: {cp_preview}")

    # Step 5: Validate
    print("\n🔒  Step 5/5: ValidationGatePrimitive — requesting approval...")
    gate = ValidationGatePrimitive(name="sdd_gate")
    gate_result = await gate.execute(
        {
            "artifacts": [refined_spec_path, plan_path],
            "validation_criteria": {"min_coverage": 0.8},
            "reviewer": "tech-lead",
        },
        ctx,
    )
    print(f"   📋  Status: {gate_result.get('status', 'unknown')}")
    print(f"   📂  Approval file: {gate_result['approval_path']}")
    feedback = gate_result.get("feedback", "")
    if feedback:
        print(f"   💡  {feedback[:80]}")

    return {
        "spec_path": refined_spec_path,
        "plan_path": plan_path,
        "tasks": tasks_result["tasks"],
        "critical_path": tasks_result["critical_path"],
        "validation": gate_result,
    }


async def main() -> None:
    """Run the SDD pipeline and print stage-by-stage output."""
    ctx = WorkflowContext(workflow_id="sdd-demo")

    print()
    print("🚀  Spec-Driven Development (SDD) Pipeline")
    print("=" * 60)
    print(f"📋  Requirement: {REQUIREMENT}")
    print()

    if MOCK_MODE:
        print("🧪  Running in MOCK_MODE — no real files will be written.")
        print()

        pipeline, mocks = build_mock_pipeline()
        await pipeline.execute({"requirement": REQUIREMENT}, ctx)

        specify_rv = mocks[0].return_value
        clarify_rv = mocks[1].return_value
        plan_rv = mocks[2].return_value
        tasks_rv = mocks[3].return_value
        gate_rv = mocks[4].return_value

        print("📝  Step 1/5: SpecifyPrimitive")
        print(f"   📂  Spec: {specify_rv['spec_path']}")
        print(f"   📊  Coverage: {specify_rv['coverage_score']:.0%}")
        gaps_preview = ", ".join(specify_rv["gaps"][:3])
        print(f"   🔍  Gaps (first 3): {gaps_preview}...")

        print("\n💬  Step 2/5: ClarifyPrimitive")
        print(
            f"   📈  Coverage: {clarify_rv['final_coverage']:.0%}"
            f" (+{clarify_rv['coverage_improvement']:.0%})"
        )
        print(f"   🔄  Iterations: {clarify_rv['iterations_used']}")

        print("\n📋  Step 3/5: PlanPrimitive")
        print(f"   📦  Phases: {len(plan_rv['phases'])}")
        effort = plan_rv["effort_estimate"]
        print(f"   ⏱️   Estimate: {effort['story_points']} SP / {effort['hours']}h")

        print("\n✅  Step 4/5: TasksPrimitive")
        print(f"   🗂️   Tasks: {len(tasks_rv['tasks'])}")
        cp_preview = " → ".join(tasks_rv["critical_path"])
        print(f"   🔴  Critical path: {cp_preview}")
        for task in tasks_rv["tasks"]:
            flag = "🔴" if task["is_critical_path"] else "⚪"
            print(f"      {flag} {task['id']}: {task['title']} ({task['story_points']} SP)")

        print("\n🔒  Step 5/5: ValidationGatePrimitive")
        print(f"   ✅  Approved: {gate_rv['approved']}")
        print(f"   💬  Feedback: {gate_rv['feedback']}")

    else:
        print("🌐  Running in LIVE_MODE — writing real files to ./sdd-demo/")
        await run_live_pipeline(REQUIREMENT, ctx)

    print()
    print("=" * 60)
    print("\n💡  Pipeline pattern:")
    print()
    print("    pipeline = (")
    print("        SpecifyPrimitive()")
    print("        >> ClarifyPrimitive(max_iterations=2)")
    print("        >> PlanPrimitive()")
    print("        >> TasksPrimitive()")
    print("        >> ValidationGatePrimitive()")
    print("    )")
    print()
    print("    result = await pipeline.execute(")
    print('        {"requirement": "Add Redis caching to the LLM pipeline"},')
    print("        WorkflowContext(workflow_id='sdd-demo'),")
    print("    )")
    print()
    print("📚  See PRIMITIVES_CATALOG.md for full SDD pipeline reference.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
