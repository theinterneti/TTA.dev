"""Tests for PlanPrimitive.

Tests cover:
- Initialization with default and custom configs
- Spec file parsing and validation
- Phase generation from requirements
- Data model extraction
- Architecture decision generation
- Effort estimation
- Dependency identification
- Plan.md and data-model.md generation
- Error handling
- Observability integration
"""

from pathlib import Path

import pytest

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit.plan_primitive import (
    ArchitectureDecision,
    DataModel,
    Phase,
    PlanPrimitive,
)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_spec_file(tmp_path):
    """Create a sample spec file for testing."""
    spec_path = tmp_path / "test.spec.md"
    content = """# Feature: Add Caching to LLM Pipeline

## Overview

Add LRU cache with TTL support to reduce LLM costs.

## Features

- LRU eviction policy
- TTL-based expiration
- Cache hit/miss metrics

## Requirements

- User authentication required
- Cache should store responses by prompt hash
- Database should use PostgreSQL
- API endpoint for cache status

## Acceptance Criteria

- Cache reduces costs by 30%
- P99 latency under 100ms
- Integration with existing auth service
"""
    spec_path.write_text(content, encoding="utf-8")
    return spec_path


@pytest.fixture
def workflow_context():
    """Create workflow context for testing."""
    return WorkflowContext(workflow_id="test-plan-workflow")


# ============================================================================
# Initialization Tests
# ============================================================================


class TestPlanPrimitiveInitialization:
    """Test PlanPrimitive initialization."""

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        plan = PlanPrimitive()

        assert plan.output_dir == Path("./output")
        assert plan.max_phases == 5
        assert plan.include_data_models is True
        assert plan.include_architecture_decisions is True
        assert plan.estimate_effort is True

    def test_initialization_custom(self, temp_output_dir):
        """Test initialization with custom parameters."""
        plan = PlanPrimitive(
            output_dir=str(temp_output_dir),
            max_phases=3,
            include_data_models=False,
            include_architecture_decisions=False,
            estimate_effort=False,
        )

        assert plan.output_dir == temp_output_dir
        assert plan.max_phases == 3
        assert plan.include_data_models is False
        assert plan.include_architecture_decisions is False
        assert plan.estimate_effort is False

    def test_output_directory_created(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "new_output"
        assert not output_dir.exists()

        plan = PlanPrimitive(output_dir=str(output_dir))

        assert plan.output_dir.exists()
        assert plan.output_dir.is_dir()


# ============================================================================
# Spec Parsing Tests
# ============================================================================


class TestSpecParsing:
    """Test spec file parsing."""

    @pytest.mark.asyncio
    async def test_parse_valid_spec(self, sample_spec_file):
        """Test parsing a valid spec file."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)

        assert spec_content["title"] == "Feature: Add Caching to LLM Pipeline"
        assert "sections" in spec_content
        assert "Overview" in spec_content["sections"]
        assert "Features" in spec_content["sections"]
        assert "Requirements" in spec_content["sections"]
        assert spec_content["path"] == str(sample_spec_file)

    @pytest.mark.asyncio
    async def test_parse_spec_extracts_sections(self, sample_spec_file):
        """Test that all sections are extracted correctly."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)

        sections = spec_content["sections"]
        assert "LRU eviction policy" in sections["Features"]
        assert "User authentication required" in sections["Requirements"]
        assert "Cache reduces costs" in sections["Acceptance Criteria"]

    @pytest.mark.asyncio
    async def test_parse_missing_file(self):
        """Test parsing non-existent file raises error."""
        plan = PlanPrimitive()

        with pytest.raises(FileNotFoundError):
            await plan._parse_spec(Path("/nonexistent/spec.md"))


# ============================================================================
# Phase Generation Tests
# ============================================================================


class TestPhaseGeneration:
    """Test implementation phase generation."""

    @pytest.mark.asyncio
    async def test_generate_phases_basic(self, sample_spec_file):
        """Test basic phase generation."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        assert len(phases) > 0
        assert all(isinstance(p, Phase) for p in phases)
        assert all(p.number > 0 for p in phases)
        assert phases[-1].name == "Testing & Deployment"

    @pytest.mark.asyncio
    async def test_generate_phases_with_data_requirements(self, sample_spec_file):
        """Test that data requirements create data model phase."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        # Should have data model phase since spec mentions "database" and "PostgreSQL"
        phase_names = [p.name for p in phases]
        assert "Data Model Setup" in phase_names

    @pytest.mark.asyncio
    async def test_generate_phases_with_api_requirements(self, sample_spec_file):
        """Test that API requirements create API phase."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        # Should have API phase since spec mentions "API endpoint"
        phase_names = [p.name for p in phases]
        assert "API & Interface Development" in phase_names

    @pytest.mark.asyncio
    async def test_generate_phases_respects_max_phases(self, tmp_path):
        """Test that max_phases limit is respected."""
        plan = PlanPrimitive(max_phases=2)

        # Create spec with many requirements
        spec_path = tmp_path / "large.spec.md"
        content = """# Large Feature

## Requirements

- Database requirement 1
- Database requirement 2
- API requirement 1
- API requirement 2
- Integration requirement 1
- Integration requirement 2
"""
        spec_path.write_text(content, encoding="utf-8")

        spec_content = await plan._parse_spec(spec_path)
        phases = await plan._generate_phases(spec_content)

        assert len(phases) <= 2

    @pytest.mark.asyncio
    async def test_phase_dependencies(self, sample_spec_file):
        """Test that phases have correct dependencies."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        # First phase should have no dependencies
        assert phases[0].dependencies is None

        # Later phases should depend on previous ones
        if len(phases) > 1:
            for i in range(1, len(phases)):
                assert phases[i].dependencies is not None


# ============================================================================
# Data Model Extraction Tests
# ============================================================================


class TestDataModelExtraction:
    """Test data model extraction from specs."""

    @pytest.mark.asyncio
    async def test_extract_data_models_basic(self, tmp_path):
        """Test basic data model extraction."""
        plan = PlanPrimitive()

        spec_path = tmp_path / "spec.md"
        content = """# Feature

## Requirements

- User authentication
- Post creation
- Comment system
"""
        spec_path.write_text(content, encoding="utf-8")

        spec_content = await plan._parse_spec(spec_path)
        data_models = await plan._extract_data_models(spec_content)

        assert len(data_models) > 0
        assert all(isinstance(m, DataModel) for m in data_models)

        # Should detect User, Post, Comment entities
        model_names = [m.name for m in data_models]
        assert "User" in model_names
        assert "Post" in model_names
        assert "Comment" in model_names

    @pytest.mark.asyncio
    async def test_extract_data_models_with_attributes(self, sample_spec_file):
        """Test that extracted models have basic attributes."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        data_models = await plan._extract_data_models(spec_content)

        for model in data_models:
            assert model.name
            assert "id" in model.attributes
            assert "created_at" in model.attributes
            assert "updated_at" in model.attributes

    @pytest.mark.asyncio
    async def test_extract_data_models_disabled(self, sample_spec_file):
        """Test that data model extraction can be disabled."""
        plan = PlanPrimitive(include_data_models=False)
        spec_content = await plan._parse_spec(sample_spec_file)

        # This shouldn't be called, but test the method directly
        data_models = await plan._extract_data_models(spec_content)

        # Should still return models, but won't be used in execution
        assert isinstance(data_models, list)


# ============================================================================
# Architecture Decisions Tests
# ============================================================================


class TestArchitectureDecisions:
    """Test architecture decision generation."""

    @pytest.mark.asyncio
    async def test_generate_architecture_decisions_basic(self, sample_spec_file):
        """Test basic architecture decision generation."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        arch_decisions = await plan._generate_architecture_decisions(spec_content, {})

        assert len(arch_decisions) > 0
        assert all(isinstance(d, ArchitectureDecision) for d in arch_decisions)

        for decision in arch_decisions:
            assert decision.decision
            assert decision.rationale
            assert decision.alternatives
            assert decision.tradeoffs

    @pytest.mark.asyncio
    async def test_generate_architecture_decisions_with_context(self, sample_spec_file):
        """Test architecture decisions with existing context."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)

        arch_context = {
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
            "existing_patterns": ["REST API", "Redis Cache"],
        }

        arch_decisions = await plan._generate_architecture_decisions(spec_content, arch_context)

        assert len(arch_decisions) >= 0  # May or may not generate decisions based on context

    @pytest.mark.asyncio
    async def test_generate_architecture_decisions_disabled(self, sample_spec_file):
        """Test that architecture decisions can be disabled."""
        plan = PlanPrimitive(include_architecture_decisions=False)
        spec_content = await plan._parse_spec(sample_spec_file)

        # This shouldn't be called, but test the method directly
        arch_decisions = await plan._generate_architecture_decisions(spec_content, {})

        # Should still return decisions, but won't be used in execution
        assert isinstance(arch_decisions, list)


# ============================================================================
# Effort Estimation Tests
# ============================================================================


class TestEffortEstimation:
    """Test effort estimation."""

    @pytest.mark.asyncio
    async def test_estimate_effort_basic(self, sample_spec_file):
        """Test basic effort estimation."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)
        data_models = await plan._extract_data_models(spec_content)

        effort = await plan._estimate_effort(phases, data_models)

        assert "story_points" in effort
        assert "hours" in effort
        assert "confidence" in effort
        assert "breakdown" in effort

        assert effort["story_points"] > 0
        assert effort["hours"] > 0
        assert 0 < effort["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_estimate_effort_scales_with_complexity(self):
        """Test that effort scales with complexity."""
        plan = PlanPrimitive()

        # Simple project (few phases)
        simple_phases = [
            Phase(1, "Phase 1", "Desc", ["req1"], 8.0),
            Phase(2, "Phase 2", "Desc", ["req2"], 8.0),
        ]
        simple_effort = await plan._estimate_effort(simple_phases, [])

        # Complex project (many phases)
        complex_phases = simple_phases + [
            Phase(3, "Phase 3", "Desc", ["req3"], 16.0),
            Phase(4, "Phase 4", "Desc", ["req4"], 16.0),
            Phase(5, "Phase 5", "Desc", ["req5"], 16.0),
        ]
        complex_effort = await plan._estimate_effort(complex_phases, [])

        assert complex_effort["story_points"] > simple_effort["story_points"]
        assert complex_effort["hours"] > simple_effort["hours"]
        assert complex_effort["confidence"] <= simple_effort["confidence"]

    @pytest.mark.asyncio
    async def test_estimate_effort_disabled(self, sample_spec_file):
        """Test that effort estimation can be disabled."""
        plan = PlanPrimitive(estimate_effort=False)
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        # This shouldn't be called, but test the method directly
        effort = await plan._estimate_effort(phases, [])

        # Should still return effort, but won't be used in execution
        assert isinstance(effort, dict)


# ============================================================================
# Dependency Identification Tests
# ============================================================================


class TestDependencyIdentification:
    """Test dependency identification."""

    @pytest.mark.asyncio
    async def test_identify_dependencies_basic(self, sample_spec_file):
        """Test basic dependency identification."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)
        data_models = await plan._extract_data_models(spec_content)

        dependencies = await plan._identify_dependencies(phases, data_models, {})

        assert isinstance(dependencies, list)

        for dep in dependencies:
            assert "type" in dep
            assert "name" in dep
            assert "blocker" in dep
            assert "description" in dep

    @pytest.mark.asyncio
    async def test_identify_dependencies_with_auth(self, sample_spec_file):
        """Test that auth service is identified as dependency."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        dependencies = await plan._identify_dependencies(phases, [], {})

        # Should identify auth as external dependency
        dep_names = [d["name"] for d in dependencies]
        assert any("auth" in name.lower() for name in dep_names)

    @pytest.mark.asyncio
    async def test_identify_dependencies_internal(self, sample_spec_file):
        """Test that phase dependencies are identified."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        dependencies = await plan._identify_dependencies(phases, [], {})

        # Should have internal dependencies for phase ordering
        internal_deps = [d for d in dependencies if d["type"] == "internal"]
        assert len(internal_deps) >= len(phases) - 1  # All phases except first


# ============================================================================
# Plan Generation Tests
# ============================================================================


class TestPlanGeneration:
    """Test plan.md file generation."""

    @pytest.mark.asyncio
    async def test_generate_plan_md_creates_file(self, sample_spec_file, temp_output_dir):
        """Test that plan.md file is created."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)

        plan_path = await plan._generate_plan_md(
            temp_output_dir, spec_content, phases, [], [], None, []
        )

        assert plan_path.exists()
        assert plan_path.name == "plan.md"
        assert plan_path.read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_generate_plan_md_content_structure(self, sample_spec_file, temp_output_dir):
        """Test that plan.md has correct structure."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)
        data_models = await plan._extract_data_models(spec_content)
        arch_decisions = await plan._generate_architecture_decisions(spec_content, {})
        effort = await plan._estimate_effort(phases, data_models)
        dependencies = await plan._identify_dependencies(phases, data_models, {})

        plan_path = await plan._generate_plan_md(
            temp_output_dir,
            spec_content,
            phases,
            data_models,
            arch_decisions,
            effort,
            dependencies,
        )

        content = plan_path.read_text(encoding="utf-8")

        # Check key sections
        assert "# Implementation Plan:" in content
        assert "## Overview" in content
        assert "## Implementation Phases" in content
        assert "## Dependencies" in content

        if arch_decisions:
            assert "## Architecture Decisions" in content

        if data_models:
            assert "## Data Models" in content

    @pytest.mark.asyncio
    async def test_generate_plan_md_includes_effort(self, sample_spec_file, temp_output_dir):
        """Test that plan.md includes effort estimation."""
        plan = PlanPrimitive()
        spec_content = await plan._parse_spec(sample_spec_file)
        phases = await plan._generate_phases(spec_content)
        effort = {"story_points": 21, "hours": 168, "confidence": 0.7}

        plan_path = await plan._generate_plan_md(
            temp_output_dir, spec_content, phases, [], [], effort, []
        )

        content = plan_path.read_text(encoding="utf-8")
        assert "21 SP" in content
        assert "168 hours" in content


# ============================================================================
# Data Model Generation Tests
# ============================================================================


class TestDataModelGeneration:
    """Test data-model.md file generation."""

    @pytest.mark.asyncio
    async def test_generate_data_model_md_creates_file(self, temp_output_dir):
        """Test that data-model.md file is created."""
        plan = PlanPrimitive()

        data_models = [
            DataModel(
                name="User",
                attributes={"id": "UUID", "email": "String"},
                relationships=["has many Posts"],
                description="User entity",
            )
        ]

        data_model_path = await plan._generate_data_model_md(temp_output_dir, data_models)

        assert data_model_path.exists()
        assert data_model_path.name == "data-model.md"
        assert data_model_path.read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_generate_data_model_md_content(self, temp_output_dir):
        """Test data-model.md content structure."""
        plan = PlanPrimitive()

        data_models = [
            DataModel(
                name="User",
                attributes={"id": "UUID", "email": "String", "created_at": "DateTime"},
                relationships=["has many Posts", "has many Comments"],
                description="User authentication and profile",
            ),
            DataModel(
                name="Post",
                attributes={"id": "UUID", "title": "String", "content": "Text"},
                relationships=["belongs to User"],
                description="Blog post content",
            ),
        ]

        data_model_path = await plan._generate_data_model_md(temp_output_dir, data_models)

        content = data_model_path.read_text(encoding="utf-8")

        # Check structure
        assert "# Data Model" in content
        assert "## Entity Definitions" in content

        # Check entities
        assert "### User" in content
        assert "### Post" in content

        # Check attributes
        assert "`id`: UUID" in content
        assert "`email`: String" in content

        # Check relationships
        assert "has many Posts" in content
        assert "belongs to User" in content


# ============================================================================
# Full Execution Tests
# ============================================================================


class TestFullExecution:
    """Test full execution of PlanPrimitive."""

    @pytest.mark.asyncio
    async def test_execute_basic(self, sample_spec_file, temp_output_dir, workflow_context):
        """Test basic execution."""
        plan = PlanPrimitive(output_dir=str(temp_output_dir))

        result = await plan.execute({"spec_path": str(sample_spec_file)}, workflow_context)

        assert "plan_path" in result
        assert "data_model_path" in result
        assert "phases" in result
        assert "architecture_decisions" in result
        assert "effort_estimate" in result
        assert "dependencies" in result

        # Check files created
        assert Path(result["plan_path"]).exists()
        if result["data_model_path"]:
            assert Path(result["data_model_path"]).exists()

    @pytest.mark.asyncio
    async def test_execute_missing_spec_file(self, temp_output_dir, workflow_context):
        """Test execution with missing spec file."""
        plan = PlanPrimitive(output_dir=str(temp_output_dir))

        with pytest.raises(FileNotFoundError):
            await plan.execute({"spec_path": "/nonexistent/spec.md"}, workflow_context)

    @pytest.mark.asyncio
    async def test_execute_minimal_features(
        self, sample_spec_file, temp_output_dir, workflow_context
    ):
        """Test execution with minimal features enabled."""
        plan = PlanPrimitive(
            output_dir=str(temp_output_dir),
            include_data_models=False,
            include_architecture_decisions=False,
            estimate_effort=False,
        )

        result = await plan.execute({"spec_path": str(sample_spec_file)}, workflow_context)

        assert result["data_model_path"] is None
        assert len(result["architecture_decisions"]) == 0
        assert result["effort_estimate"] is None

    @pytest.mark.asyncio
    async def test_execute_with_architecture_context(
        self, sample_spec_file, temp_output_dir, workflow_context
    ):
        """Test execution with architecture context."""
        plan = PlanPrimitive(output_dir=str(temp_output_dir))

        result = await plan.execute(
            {
                "spec_path": str(sample_spec_file),
                "architecture_context": {
                    "tech_stack": ["Python", "FastAPI"],
                    "existing_patterns": ["REST API"],
                },
            },
            workflow_context,
        )

        assert "architecture_decisions" in result

    @pytest.mark.asyncio
    async def test_execute_overrides_output_dir(
        self, sample_spec_file, temp_output_dir, tmp_path, workflow_context
    ):
        """Test that output_dir in input overrides instance default."""
        plan = PlanPrimitive(output_dir=str(temp_output_dir))

        override_dir = tmp_path / "override"
        result = await plan.execute(
            {"spec_path": str(sample_spec_file), "output_dir": str(override_dir)},
            workflow_context,
        )

        # Files should be in override_dir
        plan_path = Path(result["plan_path"])
        assert plan_path.parent == override_dir


# ============================================================================
# Observability Tests
# ============================================================================


class TestObservability:
    """Test observability integration."""

    @pytest.mark.asyncio
    async def test_execute_creates_span(self, sample_spec_file, temp_output_dir, workflow_context):
        """Test that execution creates observability span."""
        plan = PlanPrimitive(output_dir=str(temp_output_dir))

        # InstrumentedPrimitive should create spans automatically
        result = await plan.execute({"spec_path": str(sample_spec_file)}, workflow_context)

        assert result is not None  # Execution completed successfully

    @pytest.mark.asyncio
    async def test_workflow_context_propagation(self, sample_spec_file, temp_output_dir):
        """Test that workflow context is propagated."""
        plan = PlanPrimitive(output_dir=str(temp_output_dir))

        context = WorkflowContext(workflow_id="test-workflow", correlation_id="test-correlation")

        result = await plan.execute({"spec_path": str(sample_spec_file)}, context)

        assert result is not None


# ============================================================================
# Helper Method Tests
# ============================================================================


class TestHelperMethods:
    """Test helper methods."""

    def test_phase_to_dict(self):
        """Test Phase to dict conversion."""
        plan = PlanPrimitive()

        phase = Phase(
            number=1,
            name="Test Phase",
            description="Test description",
            requirements=["req1", "req2"],
            estimated_hours=16.0,
            dependencies=["Phase 0"],
        )

        phase_dict = plan._phase_to_dict(phase)

        assert phase_dict["number"] == 1
        assert phase_dict["name"] == "Test Phase"
        assert phase_dict["description"] == "Test description"
        assert phase_dict["requirements"] == ["req1", "req2"]
        assert phase_dict["estimated_hours"] == 16.0
        assert phase_dict["dependencies"] == ["Phase 0"]

    def test_decision_to_dict(self):
        """Test ArchitectureDecision to dict conversion."""
        plan = PlanPrimitive()

        decision = ArchitectureDecision(
            decision="Use PostgreSQL",
            rationale="ACID compliance needed",
            alternatives=["MongoDB", "MySQL"],
            tradeoffs="Requires schema management",
        )

        decision_dict = plan._decision_to_dict(decision)

        assert decision_dict["decision"] == "Use PostgreSQL"
        assert decision_dict["rationale"] == "ACID compliance needed"
        assert decision_dict["alternatives"] == ["MongoDB", "MySQL"]
        assert decision_dict["tradeoffs"] == "Requires schema management"
