"""Tests for ValidationGatePrimitive."""

import json
import tempfile
from pathlib import Path

import pytest

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import ValidationGatePrimitive


@pytest.fixture
def temp_artifacts_dir():
    """Create temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_spec_file(temp_artifacts_dir):
    """Create sample specification file."""
    spec_path = temp_artifacts_dir / "feature.spec.md"
    spec_content = """# Feature Specification: Add Caching

## Problem Statement
Need to improve API response times through caching.

## Proposed Solution
Implement Redis-based caching layer with TTL.

## Success Criteria
- 95th percentile response time <200ms
- Cache hit rate >80%
"""
    spec_path.write_text(spec_content)
    return spec_path


@pytest.fixture
def validation_gate():
    """Create ValidationGatePrimitive instance."""
    return ValidationGatePrimitive(
        timeout_seconds=60,
        auto_approve_on_timeout=False,
        require_feedback_on_rejection=True,
    )


@pytest.fixture
def workflow_context():
    """Create workflow context."""
    return WorkflowContext(correlation_id="test-validation")


class TestValidationGatePrimitiveInitialization:
    """Test ValidationGatePrimitive initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        gate = ValidationGatePrimitive()
        assert gate.timeout_seconds == 3600  # 1 hour default
        assert gate.auto_approve_on_timeout is False
        assert gate.require_feedback_on_rejection is True

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        gate = ValidationGatePrimitive(
            name="custom_gate",
            timeout_seconds=120,
            auto_approve_on_timeout=True,
            require_feedback_on_rejection=False,
        )
        assert gate.timeout_seconds == 120
        assert gate.auto_approve_on_timeout is True
        assert gate.require_feedback_on_rejection is False


class TestValidationGateExecution:
    """Test ValidationGatePrimitive execution."""

    @pytest.mark.asyncio
    async def test_create_pending_approval(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test creating pending approval."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {"min_coverage": 0.9},
                "reviewer": "test@example.com",
            },
            workflow_context,
        )

        assert result["status"] == "pending"
        assert result["approved"] is False
        assert "approval_path" in result
        assert "instructions" in result
        assert result["reviewer"] == "test@example.com"

        # Verify approval file created
        approval_path = Path(result["approval_path"])
        assert approval_path.exists()

        # Verify approval file content
        approval_data = json.loads(approval_path.read_text())
        assert approval_data["status"] == "pending"
        assert approval_data["reviewer"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_missing_artifacts_raises_error(self, validation_gate, workflow_context):
        """Test that missing artifacts raises ValueError."""
        with pytest.raises(ValueError, match="At least one artifact required"):
            await validation_gate.execute(
                {"artifacts": [], "validation_criteria": {}},
                workflow_context,
            )

    @pytest.mark.asyncio
    async def test_nonexistent_artifact_raises_error(self, validation_gate, workflow_context):
        """Test that nonexistent artifact raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Artifact not found"):
            await validation_gate.execute(
                {
                    "artifacts": ["/nonexistent/path/spec.md"],
                    "validation_criteria": {},
                },
                workflow_context,
            )

    @pytest.mark.asyncio
    async def test_reuse_existing_approval(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test reusing existing approval decision."""
        # Create initial pending approval
        result1 = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        # Manually approve
        approval_path = result1["approval_path"]
        await validation_gate.approve(
            approval_path,
            reviewer="approver@example.com",
            feedback="Looks good!",
        )

        # Execute again - should reuse approval
        result2 = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        assert result2["approved"] is True
        assert result2["reused_approval"] is True
        assert result2["feedback"] == "Looks good!"
        assert result2["reviewer"] == "approver@example.com"


class TestValidationCriteria:
    """Test validation criteria checking."""

    @pytest.mark.asyncio
    async def test_check_coverage_criterion(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test coverage criterion checking."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {"min_coverage": 0.9},
            },
            workflow_context,
        )

        validation_results = result["validation_results"]
        assert "coverage_check" in validation_results
        assert validation_results["coverage_check"]["required"] == 0.9

    @pytest.mark.asyncio
    async def test_check_required_sections_criterion(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test required sections criterion checking."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {
                    "required_sections": [
                        "Problem Statement",
                        "Proposed Solution",
                        "Success Criteria",
                    ]
                },
            },
            workflow_context,
        )

        validation_results = result["validation_results"]
        assert "required_sections_check" in validation_results

    @pytest.mark.asyncio
    async def test_artifacts_exist_check(self, validation_gate, sample_spec_file, workflow_context):
        """Test that artifacts existence is checked."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        validation_results = result["validation_results"]
        assert validation_results["artifacts_exist"] is True


class TestApprovalOperations:
    """Test approval and rejection operations."""

    @pytest.mark.asyncio
    async def test_approve_pending_validation(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test approving a pending validation."""
        # Create pending approval
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = result["approval_path"]

        # Approve
        approval_result = await validation_gate.approve(
            approval_path,
            reviewer="approver@example.com",
            feedback="All criteria met",
        )

        assert approval_result["approved"] is True
        assert approval_result["feedback"] == "All criteria met"
        assert approval_result["reviewer"] == "approver@example.com"
        assert "timestamp" in approval_result

    @pytest.mark.asyncio
    async def test_reject_pending_validation(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test rejecting a pending validation."""
        # Create pending approval
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = result["approval_path"]

        # Reject
        rejection_result = await validation_gate.reject(
            approval_path,
            reviewer="reviewer@example.com",
            feedback="Coverage too low",
        )

        assert rejection_result["approved"] is False
        assert rejection_result["feedback"] == "Coverage too low"
        assert rejection_result["reviewer"] == "reviewer@example.com"

    @pytest.mark.asyncio
    async def test_reject_without_feedback_raises_error(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test that rejection without feedback raises error."""
        # Create pending approval
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = result["approval_path"]

        # Try to reject without feedback
        with pytest.raises(ValueError, match="Feedback required"):
            await validation_gate.reject(
                approval_path,
                reviewer="reviewer@example.com",
                feedback="",  # Empty feedback
            )

    @pytest.mark.asyncio
    async def test_approve_nonexistent_raises_error(self, validation_gate):
        """Test that approving nonexistent validation raises error."""
        with pytest.raises(FileNotFoundError, match="Approval file not found"):
            await validation_gate.approve(
                "/nonexistent/approval.json",
                reviewer="test@example.com",
            )

    @pytest.mark.asyncio
    async def test_reject_nonexistent_raises_error(self, validation_gate):
        """Test that rejecting nonexistent validation raises error."""
        with pytest.raises(FileNotFoundError, match="Approval file not found"):
            await validation_gate.reject(
                "/nonexistent/approval.json",
                reviewer="test@example.com",
                feedback="Test feedback",
            )


class TestApprovalStatus:
    """Test approval status checking."""

    @pytest.mark.asyncio
    async def test_check_pending_status(self, validation_gate, sample_spec_file, workflow_context):
        """Test checking pending approval status."""
        # Create pending approval
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = result["approval_path"]

        # Check status
        status = await validation_gate.check_approval_status(approval_path)
        assert status["status"] == "pending"
        assert status["approved"] is False

    @pytest.mark.asyncio
    async def test_check_approved_status(self, validation_gate, sample_spec_file, workflow_context):
        """Test checking approved status."""
        # Create and approve
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = result["approval_path"]
        await validation_gate.approve(approval_path, reviewer="test@example.com")

        # Check status
        status = await validation_gate.check_approval_status(approval_path)
        assert status["status"] == "approved"
        assert status["approved"] is True

    @pytest.mark.asyncio
    async def test_check_rejected_status(self, validation_gate, sample_spec_file, workflow_context):
        """Test checking rejected status."""
        # Create and reject
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = result["approval_path"]
        await validation_gate.reject(
            approval_path,
            reviewer="test@example.com",
            feedback="Needs work",
        )

        # Check status
        status = await validation_gate.check_approval_status(approval_path)
        assert status["status"] == "rejected"
        assert status["approved"] is False

    @pytest.mark.asyncio
    async def test_check_nonexistent_approval(self, validation_gate):
        """Test checking status of nonexistent approval."""
        status = await validation_gate.check_approval_status("/nonexistent/approval.json")
        assert status["status"] == "not_found"
        assert status["approved"] is False


class TestMultipleArtifacts:
    """Test validation with multiple artifacts."""

    @pytest.mark.asyncio
    async def test_validate_multiple_artifacts(
        self, validation_gate, temp_artifacts_dir, workflow_context
    ):
        """Test validating multiple artifacts."""
        # Create multiple artifacts
        spec1 = temp_artifacts_dir / "feature1.spec.md"
        spec2 = temp_artifacts_dir / "feature2.spec.md"
        plan = temp_artifacts_dir / "plan.md"

        spec1.write_text("# Spec 1")
        spec2.write_text("# Spec 2")
        plan.write_text("# Plan")

        result = await validation_gate.execute(
            {
                "artifacts": [str(spec1), str(spec2), str(plan)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        assert result["status"] == "pending"
        assert len(json.loads(Path(result["approval_path"]).read_text())["artifacts"]) == 3

    @pytest.mark.asyncio
    async def test_approval_filename_with_multiple_artifacts(
        self, validation_gate, temp_artifacts_dir, workflow_context
    ):
        """Test that approval filename includes artifact names."""
        # Create 5 artifacts
        artifacts = []
        for i in range(5):
            artifact = temp_artifacts_dir / f"artifact{i}.md"
            artifact.write_text(f"# Artifact {i}")
            artifacts.append(str(artifact))

        result = await validation_gate.execute(
            {
                "artifacts": artifacts,
                "validation_criteria": {},
            },
            workflow_context,
        )

        approval_path = Path(result["approval_path"])
        # Should include first 3 names and indicate more
        assert "artifact0" in approval_path.name
        assert "artifact1" in approval_path.name
        assert "artifact2" in approval_path.name
        assert "and_2_more" in approval_path.name


class TestObservability:
    """Test observability integration."""

    @pytest.mark.asyncio
    async def test_observability_integration(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test that primitive integrates with observability."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        # Should complete without errors
        assert result is not None
        assert "approval_path" in result


class TestInstructions:
    """Test approval instructions generation."""

    @pytest.mark.asyncio
    async def test_instructions_include_artifacts(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test that instructions include artifact paths."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {},
            },
            workflow_context,
        )

        instructions = result["instructions"]
        assert str(sample_spec_file) in instructions
        assert "VALIDATION GATE" in instructions
        assert "approved" in instructions.lower()
        assert "rejected" in instructions.lower()

    @pytest.mark.asyncio
    async def test_instructions_include_validation_results(
        self, validation_gate, sample_spec_file, workflow_context
    ):
        """Test that instructions include validation results."""
        result = await validation_gate.execute(
            {
                "artifacts": [str(sample_spec_file)],
                "validation_criteria": {"min_coverage": 0.9},
            },
            workflow_context,
        )

        instructions = result["instructions"]
        assert "Validation Results" in instructions
