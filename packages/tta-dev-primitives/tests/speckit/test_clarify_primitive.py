"""Tests for ClarifyPrimitive."""

import pytest

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import ClarifyPrimitive, SpecifyPrimitive


@pytest.fixture
def tmp_specs_dir(tmp_path):
    """Create temporary specs directory."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    return specs_dir


@pytest.fixture
def sample_spec_file(tmp_specs_dir):
    """Create a sample specification with gaps."""
    spec_content = """# Feature Specification: Test Feature

**Status**: Draft
**Created**: 2025-11-04
**Last Updated**: 2025-11-04

---

## Overview

### Problem Statement
[CLARIFY]

### Proposed Solution
Add test feature implementation

### Success Criteria
- [CLARIFY]

---

## Requirements

### Functional Requirements
- Implement core functionality
- Add test coverage

### Non-Functional Requirements
[CLARIFY]

### Out of Scope
[CLARIFY]

---

## Architecture

### Component Design
[CLARIFY]

### Data Model
[CLARIFY]

### API Changes
[CLARIFY]

---

## Implementation Plan

### Phases
[CLARIFY]

### Dependencies
[CLARIFY]

### Risks
[CLARIFY]

---

## Testing Strategy

### Unit Tests
[CLARIFY]

### Integration Tests
[CLARIFY]

### Performance Tests
[CLARIFY]

---

## Clarification History

*(No clarifications yet)*

---

## Validation

### Human Review Checklist
- [ ] Architecture aligns with project standards
- [ ] Test strategy is comprehensive

### Approvals
- [ ] Technical Lead: (pending)
"""
    spec_file = tmp_specs_dir / "test-feature.spec.md"
    spec_file.write_text(spec_content, encoding="utf-8")
    return spec_file


@pytest.fixture
def clarify_primitive():
    """Create ClarifyPrimitive instance."""
    return ClarifyPrimitive(max_iterations=3, target_coverage=0.9)


@pytest.fixture
def workflow_context():
    """Create workflow context."""
    return WorkflowContext(workflow_id="test-clarify-001")


class TestClarifyPrimitiveInitialization:
    """Test ClarifyPrimitive initialization."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default parameters."""
        primitive = ClarifyPrimitive()
        assert primitive.max_iterations == 3
        assert primitive.target_coverage == 0.9
        assert primitive.questions_per_gap == 2

    def test_init_with_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        primitive = ClarifyPrimitive(max_iterations=5, target_coverage=0.95, questions_per_gap=3)
        assert primitive.max_iterations == 5
        assert primitive.target_coverage == 0.95
        assert primitive.questions_per_gap == 3


class TestClarifyPrimitiveExecution:
    """Test ClarifyPrimitive execution."""

    @pytest.mark.asyncio
    async def test_execute_with_batch_answers(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test execution with pre-provided answers."""
        # Provide answers for gaps
        answers = {
            "Problem Statement": "Users need faster response times for API calls",
            "Success Criteria": "95% of requests complete in < 100ms",
            "Non-Functional Requirements": "Latency < 100ms, throughput > 1000 RPS",
        }

        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": [
                    "Problem Statement",
                    "Success Criteria",
                    "Non-Functional Requirements",
                ],
                "current_coverage": 0.13,
                "answers": answers,
            },
            workflow_context,
        )

        # Verify output structure
        assert "updated_spec_path" in result
        assert "final_coverage" in result
        assert "coverage_improvement" in result
        assert "iterations_used" in result
        assert "remaining_gaps" in result
        assert "clarification_history" in result
        assert "target_reached" in result

        # Verify improvements
        assert result["final_coverage"] > 0.13
        assert result["coverage_improvement"] > 0
        assert result["iterations_used"] >= 1

        # Verify spec was updated
        updated_content = sample_spec_file.read_text()
        assert answers["Problem Statement"] in updated_content
        assert answers["Success Criteria"] in updated_content

    @pytest.mark.asyncio
    async def test_execute_missing_spec_path(self, clarify_primitive, workflow_context) -> None:
        """Test execution with missing spec_path raises error."""
        with pytest.raises(ValueError, match="spec_path is required"):
            await clarify_primitive.execute({}, workflow_context)

    @pytest.mark.asyncio
    async def test_execute_nonexistent_spec(self, clarify_primitive, workflow_context) -> None:
        """Test execution with nonexistent spec file raises error."""
        with pytest.raises(FileNotFoundError):
            await clarify_primitive.execute(
                {
                    "spec_path": "/nonexistent/spec.md",
                    "gaps": [],
                    "current_coverage": 0.0,
                },
                workflow_context,
            )

    @pytest.mark.asyncio
    async def test_execute_with_empty_gaps(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test execution with no gaps to clarify."""
        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": [],
                "current_coverage": 1.0,
            },
            workflow_context,
        )

        # Should complete immediately
        assert result["iterations_used"] == 0
        assert result["final_coverage"] == 1.0
        assert result["coverage_improvement"] == 0.0

    @pytest.mark.asyncio
    async def test_execute_reaches_target_coverage(self, sample_spec_file, workflow_context) -> None:
        """Test execution stops when target coverage is reached."""
        primitive = ClarifyPrimitive(max_iterations=5, target_coverage=0.3)

        # Provide answers for enough sections to reach target
        answers = {
            "Problem Statement": "Detailed problem description",
            "Success Criteria": "Measurable success metrics",
            "Non-Functional Requirements": "Performance requirements",
            "Component Design": "System components",
            "Data Model": "Database schema",
        }

        result = await primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": list(answers.keys()),
                "current_coverage": 0.13,
                "answers": answers,
            },
            workflow_context,
        )

        # Should reach target and stop
        assert result["target_reached"] is True
        assert result["final_coverage"] >= 0.3


class TestQuestionGeneration:
    """Test question generation functionality."""

    @pytest.mark.asyncio
    async def test_generates_questions_for_gaps(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that questions are generated for each gap."""
        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement", "Data Model"],
                "current_coverage": 0.13,
                "answers": {},  # No answers, will use placeholders
            },
            workflow_context,
        )

        # Check clarification history has questions
        assert len(result["clarification_history"]) > 0
        first_iteration = result["clarification_history"][0]
        assert "questions" in first_iteration
        assert len(first_iteration["questions"]) > 0

        # Verify questions have proper structure
        for question in first_iteration["questions"]:
            assert "section" in question
            assert "question" in question
            assert "type" in question

    @pytest.mark.asyncio
    async def test_question_templates_for_known_sections(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that appropriate question templates are used for known sections."""
        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement", "API Changes"],
                "current_coverage": 0.13,
                "answers": {},
            },
            workflow_context,
        )

        questions = result["clarification_history"][0]["questions"]

        # Verify sections match gaps
        sections_asked = {q["section"] for q in questions}
        assert "Problem Statement" in sections_asked or "API Changes" in sections_asked


class TestSpecificationUpdates:
    """Test specification update functionality."""

    @pytest.mark.asyncio
    async def test_updates_spec_with_answers(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that specification is updated with provided answers."""
        answer_text = "This is the detailed problem statement"

        await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.13,
                "answers": {"Problem Statement": answer_text},
            },
            workflow_context,
        )

        # Read updated spec
        updated_content = sample_spec_file.read_text()

        # Verify answer is in spec
        assert answer_text in updated_content

        # Verify [CLARIFY] was replaced in Problem Statement section
        assert "### Problem Statement\n[CLARIFY]" not in updated_content

    @pytest.mark.asyncio
    async def test_adds_clarification_history(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that clarification history is added to spec."""
        await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.13,
                "answers": {"Problem Statement": "Test answer"},
            },
            workflow_context,
        )

        updated_content = sample_spec_file.read_text()

        # Verify history section exists
        assert "## Clarification History" in updated_content
        assert "*(No clarifications yet)*" not in updated_content

        # Verify iteration information
        assert "### Iteration 1" in updated_content
        assert "**Questions Asked:**" in updated_content
        assert "**Answers Provided:**" in updated_content


class TestIterativeRefinement:
    """Test iterative refinement functionality."""

    @pytest.mark.asyncio
    async def test_multiple_iterations(self, sample_spec_file, workflow_context) -> None:
        """Test that multiple iterations work correctly."""
        primitive = ClarifyPrimitive(max_iterations=2, target_coverage=0.9)

        # First iteration answers
        answers_iter1 = {
            "Problem Statement": "Problem description",
            "Success Criteria": "Success metrics",
        }

        result = await primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement", "Success Criteria", "Data Model"],
                "current_coverage": 0.13,
                "answers": answers_iter1,
            },
            workflow_context,
        )

        # Should have performed iterations
        assert result["iterations_used"] > 0
        assert len(result["clarification_history"]) == result["iterations_used"]

        # Verify each iteration has proper structure
        for iteration in result["clarification_history"]:
            assert "iteration" in iteration
            assert "questions" in iteration
            assert "answers" in iteration
            assert "coverage_before" in iteration
            assert "coverage_after" in iteration
            assert "gaps_addressed" in iteration

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, sample_spec_file, workflow_context) -> None:
        """Test that max iterations limit is respected."""
        primitive = ClarifyPrimitive(max_iterations=2, target_coverage=1.0)

        result = await primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement", "Data Model", "API Changes"],
                "current_coverage": 0.13,
                "answers": {"Problem Statement": "Test"},  # Only partial answers
            },
            workflow_context,
        )

        # Should not exceed max iterations
        assert result["iterations_used"] <= 2

    @pytest.mark.asyncio
    async def test_coverage_improvement_tracking(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that coverage improvement is tracked correctly."""
        initial_coverage = 0.13

        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": initial_coverage,
                "answers": {"Problem Statement": "Detailed problem"},
            },
            workflow_context,
        )

        # Verify improvement calculation
        expected_improvement = result["final_coverage"] - initial_coverage
        assert abs(result["coverage_improvement"] - expected_improvement) < 0.01


class TestCoverageAnalysis:
    """Test coverage analysis functionality."""

    @pytest.mark.asyncio
    async def test_recalculates_coverage_after_updates(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that coverage is recalculated after each update."""
        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement", "Data Model"],
                "current_coverage": 0.13,
                "answers": {
                    "Problem Statement": "Problem details",
                    "Data Model": "Schema details",
                },
            },
            workflow_context,
        )

        # Coverage should improve
        assert result["final_coverage"] > 0.13

        # Check history shows coverage progression
        for iteration in result["clarification_history"]:
            assert iteration["coverage_after"] >= iteration["coverage_before"]

    @pytest.mark.asyncio
    async def test_identifies_remaining_gaps(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test that remaining gaps are identified correctly."""
        # Read initial spec to count total [CLARIFY] markers
        initial_content = sample_spec_file.read_text()
        initial_clarify_count = initial_content.count("[CLARIFY]")

        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement", "Data Model", "API Changes"],
                "current_coverage": 0.13,
                "answers": {
                    "Problem Statement": "Only one answer",
                    "Data Model": "Database schema with entities",
                    "API Changes": "New REST endpoints",
                },
            },
            workflow_context,
        )

        # Should have remaining gaps (we only answered 3 out of 13)
        assert len(result["remaining_gaps"]) > 0

        # Final [CLARIFY] count should be less than initial (reduced by 3)
        final_content = sample_spec_file.read_text()
        final_clarify_count = final_content.count("[CLARIFY]")
        assert final_clarify_count == initial_clarify_count - 3

        # Answered gaps should not be in remaining
        assert "Problem Statement" not in result["remaining_gaps"]
        assert "Data Model" not in result["remaining_gaps"]
        assert "API Changes" not in result["remaining_gaps"]


class TestIntegrationWithSpecifyPrimitive:
    """Test integration with SpecifyPrimitive."""

    @pytest.mark.asyncio
    async def test_clarify_after_specify(self, tmp_specs_dir, workflow_context) -> None:
        """Test ClarifyPrimitive works with SpecifyPrimitive output."""
        # First, create spec with SpecifyPrimitive
        specify = SpecifyPrimitive(output_dir=str(tmp_specs_dir))

        specify_result = await specify.execute(
            {
                "requirement": "Add caching to API",
                "feature_name": "api-cache",
            },
            workflow_context,
        )

        # Then, clarify the spec
        clarify = ClarifyPrimitive(max_iterations=2, target_coverage=0.5)

        clarify_result = await clarify.execute(
            {
                "spec_path": specify_result["spec_path"],
                "gaps": specify_result["gaps"],
                "current_coverage": specify_result["coverage_score"],
                "answers": {
                    "Problem Statement": "API responses are slow due to repeated DB queries",
                    "Success Criteria": "90% cache hit rate, <50ms response time",
                    "Data Model": "Redis key-value store with TTL",
                },
            },
            workflow_context,
        )

        # Verify workflow
        assert clarify_result["final_coverage"] > specify_result["coverage_score"]
        assert clarify_result["coverage_improvement"] > 0
        # We answered 3 questions, so we should have 3 fewer gaps
        assert len(clarify_result["remaining_gaps"]) <= len(specify_result["gaps"]) - 3


class TestErrorHandling:
    """Test error handling in ClarifyPrimitive."""

    @pytest.mark.asyncio
    async def test_handles_malformed_spec(self, clarify_primitive, tmp_specs_dir, workflow_context) -> None:
        """Test handling of malformed specification files."""
        # Create malformed spec (missing sections)
        malformed_spec = tmp_specs_dir / "malformed.spec.md"
        malformed_spec.write_text("# Malformed Spec\n\nNo proper structure", encoding="utf-8")

        result = await clarify_primitive.execute(
            {
                "spec_path": str(malformed_spec),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.0,
                "answers": {"Problem Statement": "Test"},
            },
            workflow_context,
        )

        # Should not crash
        assert result is not None


class TestObservability:
    """Test observability integration."""

    @pytest.mark.asyncio
    async def test_observability_integration(
        self, clarify_primitive, sample_spec_file, workflow_context
    ) -> None:
        """Test observability is properly integrated."""
        result = await clarify_primitive.execute(
            {
                "spec_path": str(sample_spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.13,
                "answers": {"Problem Statement": "Test problem"},
            },
            workflow_context,
        )

        # Verify execution completed
        assert result is not None

        # Primitive should have instrumentation
        assert hasattr(clarify_primitive, "name")
        assert clarify_primitive.name == "ClarifyPrimitive"
