"""Tests for SpecifyPrimitive."""

from pathlib import Path

import pytest

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import SpecifyPrimitive


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory for tests."""
    output_dir = tmp_path / "specs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def specify_primitive(tmp_output_dir):
    """Create SpecifyPrimitive instance for testing."""
    return SpecifyPrimitive(output_dir=str(tmp_output_dir))


@pytest.fixture
def workflow_context():
    """Create workflow context for testing."""
    return WorkflowContext(workflow_id="test-123")


class TestSpecifyPrimitiveInitialization:
    """Test SpecifyPrimitive initialization."""

    def test_init_with_defaults(self, tmp_output_dir):
        """Test initialization with default parameters."""
        primitive = SpecifyPrimitive(output_dir=str(tmp_output_dir))
        assert primitive.output_dir == tmp_output_dir
        assert primitive.min_coverage == 0.7
        assert primitive.template_path is None
        assert tmp_output_dir.exists()

    def test_init_with_custom_parameters(self, tmp_output_dir):
        """Test initialization with custom parameters."""
        primitive = SpecifyPrimitive(
            template_path="/custom/template.md",
            output_dir=str(tmp_output_dir),
            min_coverage=0.8,
        )
        assert primitive.template_path == "/custom/template.md"
        assert primitive.min_coverage == 0.8


class TestSpecifyPrimitiveExecution:
    """Test SpecifyPrimitive execution."""

    @pytest.mark.asyncio
    async def test_execute_with_simple_requirement(
        self, specify_primitive, workflow_context, tmp_output_dir
    ):
        """Test execution with a simple requirement."""
        result = await specify_primitive.execute(
            {
                "requirement": "Add LRU cache with TTL to LLM pipeline",
                "feature_name": "llm-cache",
            },
            workflow_context,
        )

        # Verify output structure
        assert "spec_path" in result
        assert "coverage_score" in result
        assert "gaps" in result
        assert "sections_completed" in result

        # Verify file was created
        spec_path = Path(result["spec_path"])
        assert spec_path.exists()
        assert spec_path.parent == tmp_output_dir
        assert spec_path.name == "llm-cache.spec.md"

        # Verify coverage
        assert 0.0 <= result["coverage_score"] <= 1.0
        assert isinstance(result["gaps"], list)

    @pytest.mark.asyncio
    async def test_execute_with_complex_requirement(self, specify_primitive, workflow_context):
        """Test execution with a complex multi-part requirement."""
        result = await specify_primitive.execute(
            {
                "requirement": "Implement distributed tracing with OpenTelemetry, "
                "add Prometheus metrics, and integrate structured logging",
                "context": {
                    "architecture": "microservices",
                    "tech_stack": ["Python", "Docker", "Kubernetes"],
                },
            },
            workflow_context,
        )

        # Verify multiple requirements extracted
        spec_content = Path(result["spec_path"]).read_text()
        assert "distributed tracing" in spec_content.lower()
        assert "prometheus" in spec_content.lower() or "metrics" in spec_content.lower()
        assert "logging" in spec_content.lower()

        # Verify project context included
        assert "microservices" in spec_content.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_requirement(self, specify_primitive, workflow_context):
        """Test execution with missing requirement raises error."""
        with pytest.raises(ValueError, match="requirement must be provided"):
            await specify_primitive.execute({}, workflow_context)

    @pytest.mark.asyncio
    async def test_execute_empty_requirement(self, specify_primitive, workflow_context):
        """Test execution with empty requirement raises error."""
        with pytest.raises(ValueError, match="requirement must be provided"):
            await specify_primitive.execute({"requirement": "   "}, workflow_context)

    @pytest.mark.asyncio
    async def test_execute_auto_generates_feature_name(
        self, specify_primitive, workflow_context, tmp_output_dir
    ):
        """Test execution auto-generates feature name if not provided."""
        result = await specify_primitive.execute(
            {"requirement": "Add caching to API gateway for improved performance"},
            workflow_context,
        )

        spec_path = Path(result["spec_path"])
        # Should use first 5 words as kebab-case name
        assert spec_path.name.startswith("add-caching-to-api")


class TestCoverageAnalysis:
    """Test coverage analysis functionality."""

    @pytest.mark.asyncio
    async def test_coverage_score_calculation(self, specify_primitive, workflow_context):
        """Test coverage score is calculated correctly."""
        result = await specify_primitive.execute(
            {
                "requirement": "Add authentication middleware to API",
                "context": {"architecture": "REST API"},
            },
            workflow_context,
        )

        # Coverage should be between 0 and 1
        assert 0.0 <= result["coverage_score"] <= 1.0

        # Should have gaps since template-based (no AI clarification yet)
        assert len(result["gaps"]) > 0

    @pytest.mark.asyncio
    async def test_gaps_identification(self, specify_primitive, workflow_context):
        """Test gaps are identified correctly."""
        result = await specify_primitive.execute(
            {"requirement": "Implement rate limiting"},
            workflow_context,
        )

        # Should identify underspecified sections
        assert "gaps" in result
        assert isinstance(result["gaps"], list)

        # Common gaps in template-based spec
        gap_names = " ".join(result["gaps"]).lower()
        # At least some of these should be gaps
        possible_gaps = [
            "non-functional",
            "testing",
            "data model",
            "risks",
        ]
        assert any(gap in gap_names for gap in possible_gaps)

    @pytest.mark.asyncio
    async def test_sections_completed_status(self, specify_primitive, workflow_context):
        """Test sections_completed provides status for each section."""
        result = await specify_primitive.execute(
            {"requirement": "Add email notification system"},
            workflow_context,
        )

        sections = result["sections_completed"]
        assert isinstance(sections, dict)

        # Should have status for common sections
        assert len(sections) > 0

        # Status values should be valid
        valid_statuses = {"complete", "incomplete", "missing"}
        for status in sections.values():
            assert status in valid_statuses


class TestSpecificationContent:
    """Test generated specification content."""

    @pytest.mark.asyncio
    async def test_spec_contains_required_sections(self, specify_primitive, workflow_context):
        """Test generated spec contains all required sections."""
        result = await specify_primitive.execute(
            {"requirement": "Add caching layer to database queries"},
            workflow_context,
        )

        spec_content = Path(result["spec_path"]).read_text()

        # Check for required sections
        required_sections = [
            "## Overview",
            "## Requirements",
            "## Architecture",
            "## Implementation Plan",
            "## Testing Strategy",
            "## Clarification History",
            "## Validation",
        ]

        for section in required_sections:
            assert section in spec_content, f"Missing section: {section}"

    @pytest.mark.asyncio
    async def test_spec_has_proper_metadata(self, specify_primitive, workflow_context):
        """Test specification has proper metadata."""
        result = await specify_primitive.execute(
            {"requirement": "Implement OAuth2 authentication"},
            workflow_context,
        )

        spec_content = Path(result["spec_path"]).read_text()

        # Check metadata
        assert "**Status**: Draft" in spec_content
        assert "**Created**:" in spec_content
        assert "**Last Updated**:" in spec_content

    @pytest.mark.asyncio
    async def test_spec_includes_validation_checklist(self, specify_primitive, workflow_context):
        """Test specification includes human validation checklist."""
        result = await specify_primitive.execute(
            {"requirement": "Add WebSocket support for real-time updates"},
            workflow_context,
        )

        spec_content = Path(result["spec_path"]).read_text()

        # Check for validation checklist items
        validation_items = [
            "[ ] Architecture aligns with project standards",
            "[ ] Test strategy is comprehensive",
            "[ ] Breaking changes are documented",
            "[ ] Dependencies are identified",
            "[ ] Risks have mitigations",
        ]

        for item in validation_items:
            assert item in spec_content, f"Missing validation item: {item}"


class TestFeatureNameGeneration:
    """Test feature name generation from requirements."""

    @pytest.mark.asyncio
    async def test_feature_name_from_action_verb(
        self, specify_primitive, workflow_context, tmp_output_dir
    ):
        """Test feature name generated from action verb requirement."""
        result = await specify_primitive.execute(
            {"requirement": "Implement distributed caching with Redis cluster"},
            workflow_context,
        )

        spec_path = Path(result["spec_path"])
        assert "implement-distributed-caching" in spec_path.name

    @pytest.mark.asyncio
    async def test_feature_name_custom_override(
        self, specify_primitive, workflow_context, tmp_output_dir
    ):
        """Test custom feature name overrides auto-generation."""
        result = await specify_primitive.execute(
            {
                "requirement": "Add feature X",
                "feature_name": "custom-feature",
            },
            workflow_context,
        )

        spec_path = Path(result["spec_path"])
        assert spec_path.name == "custom-feature.spec.md"


class TestErrorHandling:
    """Test error handling in SpecifyPrimitive."""

    @pytest.mark.asyncio
    async def test_handles_special_characters_in_requirement(
        self, specify_primitive, workflow_context
    ):
        """Test handling of special characters in requirement."""
        result = await specify_primitive.execute(
            {
                "requirement": "Add support for UTF-8 encoding: 日本語, émojis 🎉",
            },
            workflow_context,
        )

        # Should not raise error
        assert result["spec_path"] is not None

    @pytest.mark.asyncio
    async def test_handles_very_long_requirement(self, specify_primitive, workflow_context):
        """Test handling of very long requirements."""
        long_requirement = "Implement feature " + "that does something " * 100

        result = await specify_primitive.execute(
            {"requirement": long_requirement},
            workflow_context,
        )

        # Should not raise error and file should be created
        assert Path(result["spec_path"]).exists()


class TestIntegrationWithWorkflowContext:
    """Test integration with WorkflowContext."""

    @pytest.mark.asyncio
    async def test_observability_integration(self, specify_primitive, workflow_context):
        """Test observability is properly integrated."""
        # Execute primitive
        result = await specify_primitive.execute(
            {"requirement": "Add logging infrastructure"},
            workflow_context,
        )

        # Verify execution completed successfully
        assert result is not None

        # Primitive should have instrumentation from InstrumentedPrimitive base
        assert hasattr(specify_primitive, "name")
        assert specify_primitive.name == "SpecifyPrimitive"
