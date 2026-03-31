"""Comprehensive unit tests for ttadev.primitives.speckit module.

Covers:
  - SpecifyPrimitive   (specify_primitive.py)
  - ClarifyPrimitive   (clarify_primitive.py)
  - PlanPrimitive      (plan_primitive.py)
  - TasksPrimitive     (tasks_primitive.py)
  - Task dataclass     (tasks_primitive.py)
  - ValidationGatePrimitive (validation_gate_primitive.py)

Pattern:  AAA (Arrange / Act / Assert)
Markers:  @pytest.mark.unit on every test
Runtime:  asyncio_mode = auto (pytest.ini), no @pytest.mark.asyncio needed
"""

import json
from pathlib import Path

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.speckit import (
    ClarifyPrimitive,
    PlanPrimitive,
    SpecifyPrimitive,
    Task,
    TasksPrimitive,
    ValidationGatePrimitive,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ctx() -> WorkflowContext:
    """Standard WorkflowContext used by all tests."""
    return WorkflowContext(workflow_id="test-speckit")


@pytest.fixture
def spec_file(tmp_path: Path) -> Path:
    """Minimal spec.md file written to tmp_path."""
    content = """\
# Feature Specification: Add caching to LLM pipeline...

**Status**: Draft
**Created**: 2024-01-01
**Last Updated**: 2024-01-01

---

## Overview

### Problem Statement
[CLARIFY]

### Proposed Solution
Add LRU cache with TTL to LLM pipeline

### Success Criteria
- [CLARIFY]

---

## Requirements

### Functional Requirements
- Add LRU cache with TTL to LLM pipeline
- Support configurable TTL per cache entry

### Non-Functional Requirements
- [CLARIFY]

### Out of Scope
- [CLARIFY]

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
- [CLARIFY]

### Dependencies
- [CLARIFY]

### Risks
- [CLARIFY]

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
- [ ] Breaking changes are documented
- [ ] Dependencies are identified
- [ ] Risks have mitigations

### Approvals
- [ ] Technical Lead: (pending)
- [ ] Product Owner: (pending)
"""
    f = tmp_path / "test-feature.spec.md"
    f.write_text(content)
    return f


@pytest.fixture
def plan_file(tmp_path: Path) -> Path:
    """Minimal plan.md file written to tmp_path."""
    content = """\
# Implementation Plan

## Implementation Phases

### Phase 1 - Data Setup
**Effort:** Approximately 8 hours
- Create database schema for User model
- Setup API endpoint for authentication

### Phase 2 - Business Logic
**Effort:** Approximately 16 hours
- Implement caching logic
- Handle cache invalidation

## Dependencies

- PostgreSQL >= 14
- Redis >= 7

## Effort Estimate

- Story Points: 5
- Hours: 24

"""
    f = tmp_path / "plan.md"
    f.write_text(content)
    return f


# ===========================================================================
# SpecifyPrimitive
# ===========================================================================


class TestSpecifyPrimitive:
    """Tests for SpecifyPrimitive."""

    @pytest.mark.unit
    def test_instantiation_defaults(self, tmp_path: Path) -> None:
        # Arrange / Act
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Assert
        assert p.min_coverage == 0.7
        assert p.template_path is None
        assert p.output_dir == tmp_path

    @pytest.mark.unit
    def test_instantiation_custom_params(self, tmp_path: Path) -> None:
        # Arrange / Act
        p = SpecifyPrimitive(
            template_path="/tmpl.md",
            output_dir=str(tmp_path),
            min_coverage=0.85,
        )

        # Assert
        assert p.template_path == "/tmpl.md"
        assert p.min_coverage == 0.85

    @pytest.mark.unit
    def test_output_dir_created_on_init(self, tmp_path: Path) -> None:
        # Arrange
        new_dir = tmp_path / "new" / "nested"

        # Act
        SpecifyPrimitive(output_dir=str(new_dir))

        # Assert
        assert new_dir.exists()

    @pytest.mark.unit
    async def test_execute_success_returns_expected_keys(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute(
            {"requirement": "Add LRU cache with TTL to LLM pipeline"},
            ctx,
        )

        # Assert
        for key in ("spec_path", "coverage_score", "gaps", "sections_completed"):
            assert key in result

    @pytest.mark.unit
    async def test_execute_writes_spec_file(self, tmp_path: Path, ctx: WorkflowContext) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"requirement": "Add caching to pipeline"}, ctx)

        # Assert
        assert Path(result["spec_path"]).exists()

    @pytest.mark.unit
    async def test_execute_spec_file_has_md_extension(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"requirement": "Add caching to pipeline"}, ctx)

        # Assert
        assert result["spec_path"].endswith(".md")

    @pytest.mark.unit
    async def test_execute_coverage_score_in_range(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"requirement": "Add caching to pipeline"}, ctx)

        # Assert
        score = result["coverage_score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.unit
    async def test_execute_gaps_is_list(self, tmp_path: Path, ctx: WorkflowContext) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"requirement": "Add caching to pipeline"}, ctx)

        # Assert
        assert isinstance(result["gaps"], list)

    @pytest.mark.unit
    async def test_execute_sections_completed_is_dict_with_valid_statuses(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"requirement": "Add caching to pipeline"}, ctx)

        # Assert
        sc = result["sections_completed"]
        assert isinstance(sc, dict)
        valid = {"complete", "incomplete", "missing"}
        for v in sc.values():
            assert v in valid

    @pytest.mark.unit
    async def test_execute_uses_provided_feature_name(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute(
            {"requirement": "Add caching", "feature_name": "my-feature"},
            ctx,
        )

        # Assert
        assert "my-feature" in result["spec_path"]

    @pytest.mark.unit
    async def test_execute_with_project_context_embeds_context(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute(
            {
                "requirement": "Add caching",
                "context": {"architecture": "microservices"},
            },
            ctx,
        )

        # Assert
        spec_text = Path(result["spec_path"]).read_text()
        assert "microservices" in spec_text

    @pytest.mark.unit
    async def test_execute_raises_value_error_empty_requirement(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act & Assert
        with pytest.raises(ValueError, match="requirement"):
            await p.execute({"requirement": ""}, ctx)

    @pytest.mark.unit
    async def test_execute_raises_value_error_whitespace_only_requirement(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act & Assert
        with pytest.raises(ValueError, match="requirement"):
            await p.execute({"requirement": "   "}, ctx)

    @pytest.mark.unit
    async def test_execute_raises_value_error_missing_requirement_key(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act & Assert
        with pytest.raises(ValueError, match="requirement"):
            await p.execute({}, ctx)

    @pytest.mark.unit
    async def test_execute_action_verb_requirement_appears_in_spec(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute(
            {"requirement": "Add LRU cache with TTL to LLM pipeline"},
            ctx,
        )
        spec_text = Path(result["spec_path"]).read_text()

        # Assert – solution section should contain the requirement text
        assert "Add LRU cache" in spec_text

    @pytest.mark.unit
    def test_generate_feature_name_kebab_case(self, tmp_path: Path) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))

        # Act
        name = p._generate_feature_name("Add LRU cache with TTL support")

        # Assert
        assert name == "add-lru-cache-with-ttl"

    @pytest.mark.unit
    def test_analyze_coverage_returns_correct_tuple_types(self, tmp_path: Path) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))
        sample = "### Problem Statement\n[CLARIFY]\n### Proposed Solution\nFoo\n"

        # Act
        score, gaps, sections = p._analyze_coverage(sample)

        # Assert
        assert isinstance(score, float)
        assert isinstance(gaps, list)
        assert isinstance(sections, dict)

    @pytest.mark.unit
    def test_analyze_coverage_score_lower_with_more_clarify_markers(self, tmp_path: Path) -> None:
        # Arrange
        p = SpecifyPrimitive(output_dir=str(tmp_path))
        sparse = "### Problem Statement\n[CLARIFY]\n"
        dense = "### Problem Statement\n[CLARIFY]\n" * 10

        # Act
        score_sparse, _, _ = p._analyze_coverage(sparse)
        score_dense, _, _ = p._analyze_coverage(dense)

        # Assert
        assert score_dense <= score_sparse


# ===========================================================================
# ClarifyPrimitive
# ===========================================================================


class TestClarifyPrimitive:
    """Tests for ClarifyPrimitive."""

    @pytest.mark.unit
    def test_instantiation_defaults(self) -> None:
        # Arrange / Act
        p = ClarifyPrimitive()

        # Assert
        assert p.max_iterations == 3
        assert p.target_coverage == 0.9
        assert p.questions_per_gap == 2

    @pytest.mark.unit
    def test_instantiation_custom_params(self) -> None:
        # Arrange / Act
        p = ClarifyPrimitive(max_iterations=5, target_coverage=0.8, questions_per_gap=3)

        # Assert
        assert p.max_iterations == 5
        assert p.target_coverage == 0.8
        assert p.questions_per_gap == 3

    @pytest.mark.unit
    async def test_execute_raises_value_error_missing_spec_path(self, ctx: WorkflowContext) -> None:
        # Arrange
        p = ClarifyPrimitive()

        # Act & Assert
        with pytest.raises(ValueError, match="spec_path"):
            await p.execute({"gaps": [], "current_coverage": 0.5}, ctx)

    @pytest.mark.unit
    async def test_execute_raises_file_not_found_nonexistent_spec(
        self, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await p.execute(
                {"spec_path": "/no/such/spec.md", "gaps": [], "current_coverage": 0.0},
                ctx,
            )

    @pytest.mark.unit
    async def test_execute_with_no_gaps_returns_zero_iterations(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive()

        # Act
        result = await p.execute(
            {"spec_path": str(spec_file), "gaps": [], "current_coverage": 0.95},
            ctx,
        )

        # Assert
        assert result["iterations_used"] == 0
        assert result["clarification_history"] == []

    @pytest.mark.unit
    async def test_execute_returns_expected_keys(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive(max_iterations=1)

        # Act
        result = await p.execute(
            {
                "spec_path": str(spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.1,
            },
            ctx,
        )

        # Assert
        for key in (
            "updated_spec_path",
            "final_coverage",
            "coverage_improvement",
            "iterations_used",
            "remaining_gaps",
            "clarification_history",
            "target_reached",
        ):
            assert key in result

    @pytest.mark.unit
    async def test_execute_coverage_improvement_non_negative_with_answers(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive(max_iterations=1)

        # Act
        result = await p.execute(
            {
                "spec_path": str(spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.1,
                "answers": {"Problem Statement": "Users need faster LLM responses."},
            },
            ctx,
        )

        # Assert
        assert result["coverage_improvement"] >= 0

    @pytest.mark.unit
    async def test_execute_stops_early_when_target_already_reached(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange – target_coverage lower than current_coverage → exit immediately
        p = ClarifyPrimitive(max_iterations=5, target_coverage=0.05)

        # Act
        result = await p.execute(
            {
                "spec_path": str(spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.5,
            },
            ctx,
        )

        # Assert
        assert result["iterations_used"] == 0
        assert result["target_reached"] is True

    @pytest.mark.unit
    async def test_execute_respects_max_iterations_cap(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive(max_iterations=2, target_coverage=1.0)

        # Act
        result = await p.execute(
            {
                "spec_path": str(spec_file),
                "gaps": ["Problem Statement", "Data Model", "Unit Tests"],
                "current_coverage": 0.0,
            },
            ctx,
        )

        # Assert
        assert result["iterations_used"] <= 2

    @pytest.mark.unit
    async def test_execute_updated_spec_path_exists(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive(max_iterations=1)

        # Act
        result = await p.execute(
            {
                "spec_path": str(spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.1,
            },
            ctx,
        )

        # Assert
        assert Path(result["updated_spec_path"]).exists()

    @pytest.mark.unit
    async def test_execute_history_entry_added_after_iteration(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ClarifyPrimitive(max_iterations=1)

        # Act
        result = await p.execute(
            {
                "spec_path": str(spec_file),
                "gaps": ["Problem Statement"],
                "current_coverage": 0.1,
            },
            ctx,
        )

        # Assert – 1 iteration → 1 history entry
        assert result["iterations_used"] == 1
        assert len(result["clarification_history"]) == 1

    @pytest.mark.unit
    def test_generate_questions_known_sections_returns_dicts(self) -> None:
        # Arrange
        p = ClarifyPrimitive()

        # Act
        questions = p._generate_questions(["Problem Statement", "Data Model"], "some content")

        # Assert
        assert len(questions) > 0
        for q in questions:
            assert "section" in q
            assert "question" in q
            assert "type" in q

    @pytest.mark.unit
    def test_generate_questions_unknown_section_returns_default(self) -> None:
        # Arrange
        p = ClarifyPrimitive()

        # Act
        questions = p._generate_questions(["Totally Unknown Section"], "")

        # Assert
        assert len(questions) >= 1
        assert questions[0]["section"] == "Totally Unknown Section"

    @pytest.mark.unit
    def test_generate_questions_respects_questions_per_gap(self) -> None:
        # Arrange – Problem Statement has 2 template questions; cap to 1
        p = ClarifyPrimitive(questions_per_gap=1)

        # Act
        questions = p._generate_questions(["Problem Statement"], "")

        # Assert
        assert len(questions) <= 1

    @pytest.mark.unit
    def test_analyze_updated_spec_returns_tuple_types(self) -> None:
        # Arrange
        p = ClarifyPrimitive()
        spec = "### Problem Statement\n[CLARIFY]\n### Data Model\nFoo bar\n"

        # Act
        coverage, gaps = p._analyze_updated_spec(spec)

        # Assert
        assert isinstance(coverage, float)
        assert isinstance(gaps, list)
        assert 0.0 <= coverage <= 1.0


# ===========================================================================
# PlanPrimitive
# ===========================================================================


class TestPlanPrimitive:
    """Tests for PlanPrimitive."""

    @pytest.mark.unit
    def test_instantiation_defaults(self, tmp_path: Path) -> None:
        # Arrange / Act
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Assert
        assert p.max_phases == 5
        assert p.include_data_models is True
        assert p.include_architecture_decisions is True
        assert p.estimate_effort is True

    @pytest.mark.unit
    def test_instantiation_custom_params(self, tmp_path: Path) -> None:
        # Arrange / Act
        p = PlanPrimitive(
            output_dir=str(tmp_path),
            max_phases=3,
            include_data_models=False,
            estimate_effort=False,
        )

        # Assert
        assert p.max_phases == 3
        assert p.include_data_models is False
        assert p.estimate_effort is False

    @pytest.mark.unit
    def test_output_dir_created_on_init(self, tmp_path: Path) -> None:
        # Arrange
        new_dir = tmp_path / "plan_output"

        # Act
        PlanPrimitive(output_dir=str(new_dir))

        # Assert
        assert new_dir.exists()

    @pytest.mark.unit
    async def test_execute_raises_file_not_found_missing_spec(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await p.execute({"spec_path": "/no/such/spec.md"}, ctx)

    @pytest.mark.unit
    async def test_execute_returns_expected_keys(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        for key in (
            "plan_path",
            "data_model_path",
            "phases",
            "architecture_decisions",
            "effort_estimate",
            "dependencies",
        ):
            assert key in result

    @pytest.mark.unit
    async def test_execute_writes_plan_md(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        assert Path(result["plan_path"]).exists()

    @pytest.mark.unit
    async def test_execute_phases_is_list_with_at_least_one_phase(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert – always has Testing & Deployment phase at minimum
        assert isinstance(result["phases"], list)
        assert len(result["phases"]) >= 1

    @pytest.mark.unit
    async def test_execute_phases_respect_max_phases(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path), max_phases=2)

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        assert len(result["phases"]) <= 2

    @pytest.mark.unit
    async def test_execute_effort_estimate_has_hours_and_story_points(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        effort = result["effort_estimate"]
        assert effort is not None
        assert "story_points" in effort
        assert "hours" in effort

    @pytest.mark.unit
    async def test_execute_effort_estimate_is_none_when_disabled(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path), estimate_effort=False)

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        assert result["effort_estimate"] is None

    @pytest.mark.unit
    async def test_execute_architecture_decisions_is_list(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        assert isinstance(result["architecture_decisions"], list)

    @pytest.mark.unit
    async def test_execute_no_architecture_decisions_when_disabled(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = PlanPrimitive(output_dir=str(tmp_path), include_architecture_decisions=False)

        # Act
        result = await p.execute({"spec_path": str(spec_file)}, ctx)

        # Assert
        assert result["architecture_decisions"] == []

    @pytest.mark.unit
    async def test_execute_output_dir_override_in_input(
        self, spec_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        override = tmp_path / "override"
        override.mkdir()
        p = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute(
            {"spec_path": str(spec_file), "output_dir": str(override)},
            ctx,
        )

        # Assert
        assert str(override) in result["plan_path"]


# ===========================================================================
# Task dataclass
# ===========================================================================


class TestTask:
    """Tests for the Task dataclass."""

    @pytest.mark.unit
    def test_instantiation_required_fields_only(self) -> None:
        # Arrange / Act
        task = Task(id="T-001", title="Implement cache", description="Add LRU", phase="Phase 1")

        # Assert
        assert task.id == "T-001"
        assert task.title == "Implement cache"
        assert task.description == "Add LRU"
        assert task.phase == "Phase 1"

    @pytest.mark.unit
    def test_default_field_values(self) -> None:
        # Arrange / Act
        task = Task(id="T-001", title="X", description="Y", phase="Z")

        # Assert
        assert task.dependencies == []
        assert task.story_points is None
        assert task.hours is None
        assert task.priority == "medium"
        assert task.tags == []
        assert task.acceptance_criteria == []
        assert task.is_critical_path is False
        assert task.parallel_group is None

    @pytest.mark.unit
    def test_to_dict_contains_all_expected_keys(self) -> None:
        # Arrange
        task = Task(id="T-001", title="Implement cache", description="Add LRU", phase="P1")

        # Act
        d = task.to_dict()

        # Assert
        expected = {
            "id",
            "title",
            "description",
            "phase",
            "dependencies",
            "story_points",
            "hours",
            "priority",
            "tags",
            "acceptance_criteria",
            "is_critical_path",
            "parallel_group",
        }
        assert expected == set(d.keys())

    @pytest.mark.unit
    def test_to_dict_reflects_field_values(self) -> None:
        # Arrange
        task = Task(
            id="T-042",
            title="Write tests",
            description="Cover edge cases",
            phase="Testing",
            story_points=3,
            hours=12.5,
            priority="high",
            tags=["testing"],
            acceptance_criteria=["All tests pass"],
            is_critical_path=True,
            parallel_group="P-001",
        )

        # Act
        d = task.to_dict()

        # Assert
        assert d["id"] == "T-042"
        assert d["story_points"] == 3
        assert d["hours"] == 12.5
        assert d["priority"] == "high"
        assert d["tags"] == ["testing"]
        assert d["is_critical_path"] is True
        assert d["parallel_group"] == "P-001"

    @pytest.mark.unit
    def test_default_dependencies_are_independent_per_instance(self) -> None:
        # Arrange – two Tasks must NOT share the same mutable default list
        t1 = Task(id="T-001", title="A", description="", phase="P")
        t2 = Task(id="T-002", title="B", description="", phase="P")

        # Act
        t1.dependencies.append("T-000")

        # Assert – t2's list is unaffected
        assert t2.dependencies == []


# ===========================================================================
# TasksPrimitive
# ===========================================================================


class TestTasksPrimitive:
    """Tests for TasksPrimitive."""

    @pytest.mark.unit
    def test_instantiation_defaults(self, tmp_path: Path) -> None:
        # Arrange / Act
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Assert
        assert p.output_format == "markdown"
        assert p.include_effort is True
        assert p.identify_critical_path_flag is True
        assert p.group_parallel_work_flag is True

    @pytest.mark.unit
    def test_instantiation_custom_params(self, tmp_path: Path) -> None:
        # Arrange / Act
        p = TasksPrimitive(
            output_dir=str(tmp_path),
            output_format="json",
            include_effort=False,
            identify_critical_path=False,
            group_parallel_work=False,
        )

        # Assert
        assert p.output_format == "json"
        assert p.include_effort is False
        assert p.identify_critical_path_flag is False
        assert p.group_parallel_work_flag is False

    @pytest.mark.unit
    async def test_execute_raises_file_not_found_missing_plan(
        self, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await p.execute({"plan_path": "/no/such/plan.md"}, ctx)

    @pytest.mark.unit
    async def test_execute_returns_expected_keys(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        for key in ("tasks_path", "tasks", "critical_path", "parallel_streams", "total_effort"):
            assert key in result

    @pytest.mark.unit
    async def test_execute_tasks_is_list_of_dicts_with_id(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        assert isinstance(result["tasks"], list)
        assert len(result["tasks"]) > 0
        for t in result["tasks"]:
            assert "id" in t
            assert "title" in t

    @pytest.mark.unit
    async def test_execute_writes_tasks_file(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        assert Path(result["tasks_path"]).exists()

    @pytest.mark.unit
    async def test_execute_total_effort_has_required_keys(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        effort = result["total_effort"]
        assert "story_points" in effort
        assert "hours" in effort

    @pytest.mark.unit
    async def test_execute_critical_path_is_list(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        assert isinstance(result["critical_path"], list)

    @pytest.mark.unit
    async def test_execute_parallel_streams_is_dict(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        assert isinstance(result["parallel_streams"], dict)

    @pytest.mark.unit
    async def test_execute_json_format_produces_valid_json_dict(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path), output_format="json")

        # Act
        result = await p.execute({"plan_path": str(plan_file)}, ctx)

        # Assert
        tasks_path = Path(result["tasks_path"])
        assert tasks_path.exists()
        data = json.loads(tasks_path.read_text())
        assert isinstance(data, dict)
        assert "tasks" in data

    @pytest.mark.unit
    async def test_execute_raises_value_error_unknown_format(
        self, plan_file: Path, tmp_path: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange – unknown format set at init; execute should raise
        p = TasksPrimitive(output_dir=str(tmp_path), output_format="xml")

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown output format"):
            await p.execute({"plan_path": str(plan_file)}, ctx)

    @pytest.mark.unit
    def test_parse_plan_file_raises_file_not_found(self, tmp_path: Path) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            p._parse_plan_file(tmp_path / "nonexistent.md")

    @pytest.mark.unit
    def test_parse_plan_file_returns_expected_structure(
        self, plan_file: Path, tmp_path: Path
    ) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        plan_data = p._parse_plan_file(plan_file)

        # Assert
        assert "phases" in plan_data
        assert "dependencies" in plan_data
        assert "total_effort" in plan_data
        assert isinstance(plan_data["phases"], list)

    @pytest.mark.unit
    def test_order_tasks_respects_dependencies(self, tmp_path: Path) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))
        tasks = [
            Task(id="T-002", title="B", description="", phase="P", dependencies=["T-001"]),
            Task(id="T-001", title="A", description="", phase="P", dependencies=[]),
        ]

        # Act
        ordered = p._order_tasks(tasks)
        ids = [t.id for t in ordered]

        # Assert – T-001 must precede T-002
        assert ids.index("T-001") < ids.index("T-002")

    @pytest.mark.unit
    def test_order_tasks_raises_on_circular_dependencies(self, tmp_path: Path) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))
        tasks = [
            Task(id="T-001", title="A", description="", phase="P", dependencies=["T-002"]),
            Task(id="T-002", title="B", description="", phase="P", dependencies=["T-001"]),
        ]

        # Act & Assert
        with pytest.raises(ValueError, match=r"[Cc]ircular"):
            p._order_tasks(tasks)

    @pytest.mark.unit
    def test_identify_critical_path_empty_list(self, tmp_path: Path) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        cp = p._identify_critical_path([])

        # Assert
        assert cp == []

    @pytest.mark.unit
    def test_identify_parallel_streams_empty_list(self, tmp_path: Path) -> None:
        # Arrange
        p = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        streams = p._identify_parallel_streams([])

        # Assert
        assert streams == {}


# ===========================================================================
# ValidationGatePrimitive
# ===========================================================================


class TestValidationGatePrimitive:
    """Tests for ValidationGatePrimitive."""

    @pytest.mark.unit
    def test_instantiation_defaults(self) -> None:
        # Arrange / Act
        p = ValidationGatePrimitive()

        # Assert
        assert p.timeout_seconds == 3600
        assert p.auto_approve_on_timeout is False
        assert p.require_feedback_on_rejection is True

    @pytest.mark.unit
    def test_instantiation_custom_params(self) -> None:
        # Arrange / Act
        p = ValidationGatePrimitive(
            name="custom_gate",
            timeout_seconds=600,
            auto_approve_on_timeout=True,
            require_feedback_on_rejection=False,
        )

        # Assert
        assert p.timeout_seconds == 600
        assert p.auto_approve_on_timeout is True
        assert p.require_feedback_on_rejection is False

    @pytest.mark.unit
    async def test_execute_raises_value_error_empty_artifacts(self, ctx: WorkflowContext) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act & Assert
        with pytest.raises(ValueError, match="artifact"):
            await p.execute({"artifacts": []}, ctx)

    @pytest.mark.unit
    async def test_execute_raises_value_error_missing_artifacts_key(
        self, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act & Assert
        with pytest.raises(ValueError, match="artifact"):
            await p.execute({}, ctx)

    @pytest.mark.unit
    async def test_execute_raises_file_not_found_missing_artifact(
        self, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await p.execute({"artifacts": ["/no/such/artifact.md"]}, ctx)

    @pytest.mark.unit
    async def test_execute_returns_pending_status_first_call(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        assert result["status"] == "pending"
        assert result["approved"] is False

    @pytest.mark.unit
    async def test_execute_returns_expected_keys(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        for key in (
            "approved",
            "feedback",
            "timestamp",
            "reviewer",
            "validation_results",
            "approval_path",
        ):
            assert key in result

    @pytest.mark.unit
    async def test_execute_creates_approval_json_file(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        approval_path = Path(result["approval_path"])
        assert approval_path.exists()
        data = json.loads(approval_path.read_text())
        assert data["status"] == "pending"

    @pytest.mark.unit
    async def test_execute_includes_instructions(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        assert "instructions" in result
        assert "VALIDATION GATE" in result["instructions"]

    @pytest.mark.unit
    async def test_execute_passes_reviewer_to_output(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute(
            {"artifacts": [str(spec_file)], "reviewer": "alice@example.com"},
            ctx,
        )

        # Assert
        assert result["reviewer"] == "alice@example.com"

    @pytest.mark.unit
    async def test_execute_reuses_existing_approved_decision(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        first = await p.execute({"artifacts": [str(spec_file)]}, ctx)
        approval_path = first["approval_path"]

        # Manually set approved
        data = json.loads(Path(approval_path).read_text())
        data["status"] = "approved"
        data["feedback"] = "LGTM"
        Path(approval_path).write_text(json.dumps(data))

        # Act – second call should reuse the decision
        second = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        assert second["approved"] is True
        assert second.get("reused_approval") is True

    @pytest.mark.unit
    async def test_execute_reuses_existing_rejected_decision(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        first = await p.execute({"artifacts": [str(spec_file)]}, ctx)
        approval_path = first["approval_path"]

        # Manually set rejected
        data = json.loads(Path(approval_path).read_text())
        data["status"] = "rejected"
        data["feedback"] = "Not ready"
        Path(approval_path).write_text(json.dumps(data))

        # Act
        second = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        assert second["approved"] is False
        assert second.get("reused_approval") is True

    @pytest.mark.unit
    async def test_execute_validation_results_artifacts_exist_true(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Assert
        assert result["validation_results"]["artifacts_exist"] is True

    @pytest.mark.unit
    async def test_execute_min_coverage_criterion_in_results(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute(
            {
                "artifacts": [str(spec_file)],
                "validation_criteria": {"min_coverage": 0.9},
            },
            ctx,
        )

        # Assert
        vr = result["validation_results"]
        assert "coverage_check" in vr
        assert vr["coverage_check"]["required"] == 0.9

    @pytest.mark.unit
    async def test_execute_required_sections_criterion_in_results(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        result = await p.execute(
            {
                "artifacts": [str(spec_file)],
                "validation_criteria": {"required_sections": ["Problem Statement"]},
            },
            ctx,
        )

        # Assert
        assert "required_sections_check" in result["validation_results"]

    @pytest.mark.unit
    async def test_approve_returns_approved_true(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act
        result = await p.approve(
            approval_path=pending["approval_path"],
            reviewer="bob@example.com",
            feedback="Approved after review",
        )

        # Assert
        assert result["approved"] is True
        assert result["reviewer"] == "bob@example.com"
        assert result["feedback"] == "Approved after review"

    @pytest.mark.unit
    async def test_approve_persists_status_to_disk(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act
        await p.approve(approval_path=pending["approval_path"], reviewer="qa", feedback="OK")

        # Assert
        data = json.loads(Path(pending["approval_path"]).read_text())
        assert data["status"] == "approved"
        assert data["reviewer"] == "qa"

    @pytest.mark.unit
    async def test_approve_raises_file_not_found_missing_approval(self) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await p.approve(
                approval_path="/nonexistent/ghost.approval.json",
                reviewer="test",
                feedback="",
            )

    @pytest.mark.unit
    async def test_reject_returns_approved_false(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act
        result = await p.reject(
            approval_path=pending["approval_path"],
            reviewer="carol@example.com",
            feedback="Coverage too low",
        )

        # Assert
        assert result["approved"] is False
        assert result["reviewer"] == "carol@example.com"
        assert "Coverage too low" in result["feedback"]

    @pytest.mark.unit
    async def test_reject_persists_status_to_disk(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act
        await p.reject(
            approval_path=pending["approval_path"],
            reviewer="qa",
            feedback="Needs more tests",
        )

        # Assert
        data = json.loads(Path(pending["approval_path"]).read_text())
        assert data["status"] == "rejected"

    @pytest.mark.unit
    async def test_reject_raises_value_error_empty_feedback_when_required(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive(require_feedback_on_rejection=True)
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act & Assert
        with pytest.raises(ValueError):
            await p.reject(
                approval_path=pending["approval_path"],
                reviewer="qa",
                feedback="",
            )

    @pytest.mark.unit
    async def test_reject_allows_empty_feedback_when_not_required(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive(require_feedback_on_rejection=False)
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act – should NOT raise
        result = await p.reject(
            approval_path=pending["approval_path"],
            reviewer="qa",
            feedback="",
        )

        # Assert
        assert result["approved"] is False

    @pytest.mark.unit
    async def test_reject_raises_file_not_found_missing_approval(self) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await p.reject(
                approval_path="/nonexistent/ghost.approval.json",
                reviewer="qa",
                feedback="Some feedback",
            )

    @pytest.mark.unit
    async def test_check_approval_status_returns_pending(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)

        # Act
        status = await p.check_approval_status(pending["approval_path"])

        # Assert
        assert status["status"] == "pending"
        assert status["approved"] is False

    @pytest.mark.unit
    async def test_check_approval_status_returns_approved_after_approve(
        self, spec_file: Path, ctx: WorkflowContext
    ) -> None:
        # Arrange
        p = ValidationGatePrimitive()
        pending = await p.execute({"artifacts": [str(spec_file)]}, ctx)
        await p.approve(approval_path=pending["approval_path"], reviewer="qa", feedback="Good")

        # Act
        status = await p.check_approval_status(pending["approval_path"])

        # Assert
        assert status["status"] == "approved"
        assert status["approved"] is True

    @pytest.mark.unit
    async def test_check_approval_status_not_found_for_missing_file(self) -> None:
        # Arrange
        p = ValidationGatePrimitive()

        # Act
        status = await p.check_approval_status("/nonexistent/ghost.approval.json")

        # Assert
        assert status["status"] == "not_found"
        assert status["approved"] is False


# ===========================================================================
# Composition: SpecifyPrimitive → ClarifyPrimitive → PlanPrimitive → TasksPrimitive
# ===========================================================================


class TestSpeckitPipelineComposition:
    """Light pipeline tests verifying primitives compose end-to-end."""

    @pytest.mark.unit
    async def test_specify_output_feeds_clarify(self, tmp_path: Path, ctx: WorkflowContext) -> None:
        # Arrange
        specify = SpecifyPrimitive(output_dir=str(tmp_path))
        clarify = ClarifyPrimitive(max_iterations=1)

        # Act
        spec_result = await specify.execute(
            {"requirement": "Add LRU cache with TTL to LLM pipeline"},
            ctx,
        )
        clarify_result = await clarify.execute(
            {
                "spec_path": spec_result["spec_path"],
                "gaps": spec_result["gaps"],
                "current_coverage": spec_result["coverage_score"],
                "answers": {gap: f"Answer for {gap}" for gap in spec_result["gaps"]},
            },
            ctx,
        )

        # Assert
        assert "final_coverage" in clarify_result
        assert "updated_spec_path" in clarify_result
        assert clarify_result["iterations_used"] <= 1

    @pytest.mark.unit
    async def test_specify_output_feeds_plan(self, tmp_path: Path, ctx: WorkflowContext) -> None:
        # Arrange
        specify = SpecifyPrimitive(output_dir=str(tmp_path))
        plan = PlanPrimitive(output_dir=str(tmp_path))

        # Act
        spec_result = await specify.execute(
            {"requirement": "Add LRU cache with TTL to LLM pipeline"},
            ctx,
        )
        plan_result = await plan.execute({"spec_path": spec_result["spec_path"]}, ctx)

        # Assert
        assert "plan_path" in plan_result
        assert Path(plan_result["plan_path"]).exists()

    @pytest.mark.unit
    async def test_plan_output_feeds_tasks(self, tmp_path: Path, ctx: WorkflowContext) -> None:
        # Arrange
        specify = SpecifyPrimitive(output_dir=str(tmp_path))
        plan = PlanPrimitive(output_dir=str(tmp_path))
        tasks_prim = TasksPrimitive(output_dir=str(tmp_path))

        # Act
        spec_result = await specify.execute(
            {"requirement": "Add LRU cache with TTL to LLM pipeline"},
            ctx,
        )
        plan_result = await plan.execute({"spec_path": spec_result["spec_path"]}, ctx)
        tasks_result = await tasks_prim.execute({"plan_path": plan_result["plan_path"]}, ctx)

        # Assert
        assert "tasks" in tasks_result
        assert len(tasks_result["tasks"]) > 0
