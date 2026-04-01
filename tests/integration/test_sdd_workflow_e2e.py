"""Integration tests for the SDD (Spec-Driven Development) pipeline.

Tests the full speckit primitive chain:
    SpecifyPrimitive → ClarifyPrimitive → PlanPrimitive → TasksPrimitive
    → ValidationGatePrimitive

Covers:
- Full pipeline end-to-end in mock mode (all 5 stages fire, data flows through)
- Specify → Plan handoff using real primitives with tmp_path
- ValidationGatePrimitive rejection behaviour

Runtime: asyncio_mode = auto (pytest.ini) — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.speckit import (
    PlanPrimitive,
    SpecifyPrimitive,
    ValidationGatePrimitive,
)
from ttadev.primitives.testing.mocks import MockPrimitive


@pytest.fixture
def ctx() -> WorkflowContext:
    """Standard WorkflowContext for all SDD integration tests."""
    return WorkflowContext(workflow_id="test-sdd-e2e")


@pytest.mark.integration
async def test_sdd_pipeline_full_flow_mock_mode(ctx: WorkflowContext) -> None:
    """Full SDD pipeline with MockPrimitive stubs — verifies all 5 stages execute
    and that output from each stage flows as input to the next.

    Arrange: Five MockPrimitive instances wired with >> into a SequentialPrimitive.
    Act: Execute the composed pipeline with a single requirement dict.
    Assert: Every mock called once; intermediate inputs carry prior stage output.
    """
    # Arrange
    mock_specify = MockPrimitive(
        name="specify",
        return_value={
            "spec_path": "/tmp/test.spec.md",
            "coverage_score": 0.40,
            "gaps": ["Problem Statement", "Data Model"],
            "sections_completed": {"Problem Statement": "incomplete"},
        },
    )
    mock_clarify = MockPrimitive(
        name="clarify",
        return_value={
            "updated_spec_path": "/tmp/test.spec.md",
            "final_coverage": 0.85,
            "coverage_improvement": 0.45,
            "iterations_used": 2,
            "remaining_gaps": ["Data Model"],
            "clarification_history": [],
            "target_reached": False,
        },
    )
    mock_plan = MockPrimitive(
        name="plan",
        return_value={
            "plan_path": "/tmp/test.plan.md",
            "data_model_path": None,
            "phases": [
                {"number": 1, "name": "Setup", "description": "Initial setup"},
                {"number": 2, "name": "Core", "description": "Core implementation"},
            ],
            "architecture_decisions": [],
            "effort_estimate": {"story_points": 8, "hours": 16.0},
            "dependencies": [],
        },
    )
    mock_tasks = MockPrimitive(
        name="tasks",
        return_value={
            "tasks_path": "/tmp/test.tasks.md",
            "tasks": [
                {
                    "id": "T-001",
                    "title": "Setup Redis",
                    "phase": "Setup",
                    "priority": "high",
                    "story_points": 3,
                    "hours": 6.0,
                    "dependencies": [],
                    "is_critical_path": True,
                },
                {
                    "id": "T-002",
                    "title": "Implement cache layer",
                    "phase": "Core",
                    "priority": "high",
                    "story_points": 5,
                    "hours": 10.0,
                    "dependencies": ["T-001"],
                    "is_critical_path": True,
                },
            ],
            "critical_path": ["T-001", "T-002"],
            "parallel_streams": {},
            "total_effort": {"story_points": 8, "hours": 16.0},
        },
    )
    mock_validate = MockPrimitive(
        name="validate",
        return_value={
            "approved": True,
            "feedback": "All criteria met",
            "timestamp": "2026-01-15T09:00:00+00:00",
            "reviewer": "automated",
            "validation_results": {"artifacts_exist": True},
            "approval_path": "/tmp/.approvals/test.approval.json",
            "status": "approved",
        },
    )

    pipeline = mock_specify >> mock_clarify >> mock_plan >> mock_tasks >> mock_validate

    # Act
    result = await pipeline.execute(
        {"requirement": "Add Redis caching to the LLM pipeline"},
        ctx,
    )

    # Assert: every stage executed exactly once
    assert mock_specify.call_count == 1
    assert mock_clarify.call_count == 1
    assert mock_plan.call_count == 1
    assert mock_tasks.call_count == 1
    assert mock_validate.call_count == 1

    # Assert: data flowed from stage to stage
    clarify_input = mock_clarify.calls[0][0]
    assert "spec_path" in clarify_input
    assert "gaps" in clarify_input
    assert clarify_input["coverage_score"] == pytest.approx(0.40)

    plan_input = mock_plan.calls[0][0]
    assert "updated_spec_path" in plan_input
    assert "final_coverage" in plan_input
    assert plan_input["final_coverage"] == pytest.approx(0.85)

    tasks_input = mock_tasks.calls[0][0]
    assert "plan_path" in tasks_input
    assert "phases" in tasks_input
    assert len(tasks_input["phases"]) == 2

    validate_input = mock_validate.calls[0][0]
    assert "tasks" in validate_input
    assert "critical_path" in validate_input
    assert validate_input["critical_path"] == ["T-001", "T-002"]

    # Final result is validate's return value
    assert result["approved"] is True
    assert result["status"] == "approved"
    assert result["feedback"] == "All criteria met"


@pytest.mark.integration
async def test_specify_to_plan_handoff(tmp_path: Path, ctx: WorkflowContext) -> None:
    """Specify → Plan using real primitives and a real temp directory.

    Verifies that SpecifyPrimitive writes a valid .spec.md and that
    PlanPrimitive can parse it to produce a plan with at least one phase.

    Arrange: Real SpecifyPrimitive + real PlanPrimitive, both writing to tmp_path.
    Act: Execute both primitives sequentially, remapping spec_path key.
    Assert: spec file on disk; plan file on disk; phases list is non-empty.
    """
    # Arrange
    specs_dir = tmp_path / "specs"
    plan_dir = tmp_path / "plan"

    specify = SpecifyPrimitive(output_dir=str(specs_dir))
    plan = PlanPrimitive(output_dir=str(plan_dir))

    # Act: Step 1 — SpecifyPrimitive
    specify_result = await specify.execute(
        {
            "requirement": "Add Redis caching to the LLM pipeline",
            "feature_name": "redis-cache",
            "context": {"tech_stack": ["Python", "Redis"]},
        },
        ctx,
    )

    # Assert: spec produced
    assert "spec_path" in specify_result
    spec_path = Path(specify_result["spec_path"])
    assert spec_path.exists(), f"Spec file not found: {spec_path}"
    assert specify_result["coverage_score"] >= 0.0
    assert isinstance(specify_result["gaps"], list)
    assert isinstance(specify_result["sections_completed"], dict)

    # Act: Step 2 — PlanPrimitive (consumes spec_path from step 1)
    plan_result = await plan.execute(
        {"spec_path": str(spec_path)},
        ctx,
    )

    # Assert: plan produced with expected structure
    assert "plan_path" in plan_result
    plan_path = Path(plan_result["plan_path"])
    assert plan_path.exists(), f"Plan file not found: {plan_path}"
    assert isinstance(plan_result["phases"], list)
    assert len(plan_result["phases"]) >= 1, "Expected at least one implementation phase"
    assert isinstance(plan_result["architecture_decisions"], list)
    assert "dependencies" in plan_result

    if plan_result.get("effort_estimate"):
        effort = plan_result["effort_estimate"]
        assert "story_points" in effort or "hours" in effort


@pytest.mark.integration
async def test_validation_gate_blocks_on_rejection(tmp_path: Path, ctx: WorkflowContext) -> None:
    """ValidationGatePrimitive returns approved=False after programmatic rejection.

    Arrange: A real spec artifact written to tmp_path; gate instantiated.
    Act-1: Execute gate → pending (approved=False, status='pending').
    Act-2: Call gate.reject() with feedback.
    Act-3: Re-execute gate with the same artifacts.
    Assert: Re-run returns approved=False and reused_approval=True.
    """
    # Arrange
    spec_file = tmp_path / "feature.spec.md"
    spec_file.write_text(
        "# Feature Specification: Redis Cache\n\n"
        "## Overview\n\n"
        "### Problem Statement\n"
        "LLM inference is slow without caching.\n\n"
        "### Proposed Solution\n"
        "Add Redis-backed LRU cache with TTL.\n",
        encoding="utf-8",
    )

    gate = ValidationGatePrimitive(name="test_gate")

    gate_input = {
        "artifacts": [str(spec_file)],
        "validation_criteria": {"min_coverage": 0.9},
        "reviewer": "tech-lead",
    }

    # Act 1: Initial run — should return pending
    first_result = await gate.execute(gate_input, ctx)

    assert first_result["approved"] is False, "Gate must not auto-approve on first run"
    assert first_result.get("status") == "pending"
    approval_path = first_result["approval_path"]
    assert Path(approval_path).exists(), f"Approval file not created: {approval_path}"

    # Act 2: Reviewer rejects
    reject_result = await gate.reject(
        approval_path=approval_path,
        reviewer="tech-lead",
        feedback="Coverage too low — needs Data Model and Testing Strategy sections.",
    )

    assert reject_result["approved"] is False
    assert "Coverage too low" in reject_result["feedback"]

    # Confirm rejection is persisted to disk
    approval_data = json.loads(Path(approval_path).read_text(encoding="utf-8"))
    assert approval_data["status"] == "rejected"
    assert approval_data["reviewer"] == "tech-lead"

    # Act 3: Re-run gate — should load existing rejection
    second_result = await gate.execute(gate_input, ctx)

    # Assert
    assert second_result["approved"] is False
    assert second_result.get("reused_approval") is True, (
        "Gate should indicate it reused the existing rejection decision"
    )
    assert "Coverage too low" in second_result.get("feedback", "")
