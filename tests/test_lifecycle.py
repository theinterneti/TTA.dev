"""Comprehensive tests for the Development Lifecycle Meta-Framework.

Tests cover:
- Stage enum and ordering
- Severity enum and ordering
- ValidationCheck execution
- ValidationResult creation
- StageCriteria and StageReadiness
- StageManager readiness checks and transitions
- ReadinessCheckPrimitive parallel execution
- Pre-built checks (generic, documentation, git, security)
- Stage definitions and criteria maps
"""

import subprocess
import tempfile
from pathlib import Path

import pytest
from ttadev.core.base import WorkflowContext
from ttadev.lifecycle import (
    DEPLOYMENT_TO_PRODUCTION,
    EXPERIMENTATION_TO_TESTING,
    STAGE_CRITERIA_MAP,
    STAGING_TO_DEPLOYMENT,
    TESTING_TO_STAGING,
    ReadinessCheckPrimitive,
    ReadinessCheckResult,
    Severity,
    Stage,
    StageCriteria,
    StageManager,
    StageReadiness,
    StageRequest,
    StageTransitionError,
    TransitionResult,
    ValidationCheck,
    ValidationPrimitive,
    ValidationResult,
)
from ttadev.lifecycle.checks import (
    DEPENDENCIES_UP_TO_DATE,
    FORMAT_CHECK_PASSES,
    HAS_CHANGELOG,
    HAS_DOCSTRINGS,
    HAS_EXAMPLES,
    HAS_LICENSE,
    HAS_PACKAGE_MANIFEST,
    HAS_README,
    HAS_README_SECTIONS,
    HAS_SRC_DIRECTORY,
    HAS_TESTS_DIRECTORY,
    LINT_PASSES,
    NO_KNOWN_VULNERABILITIES,
    NO_SECRETS_IN_CODE,
    ON_CORRECT_BRANCH,
    REMOTE_UP_TO_DATE,
    TESTS_PASS,
    TYPE_CHECK_PASSES,
    VERSION_BUMPED,
    WORKING_TREE_CLEAN,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def context() -> WorkflowContext:
    """Create a test WorkflowContext."""
    return WorkflowContext(workflow_id="test-lifecycle")


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project structure in a temp directory."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\nversion = "1.0.0"\n'
    )
    (tmp_path / "README.md").write_text(
        "# Test Project\n\n## Installation\n\npip install test\n"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text('"""Main module."""\nprint("hello")\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text(
        "def test_main():\n    assert True\n"
    )
    return tmp_path


@pytest.fixture
def complete_project(tmp_project: Path) -> Path:
    """Create a fully complete project with all required files."""
    (tmp_project / "LICENSE").write_text("MIT License\n")
    (tmp_project / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 1.0.0\n\n- Initial release\n"
    )
    (tmp_project / "examples").mkdir()
    (tmp_project / "examples" / "basic.py").write_text("print('example')\n")
    return tmp_project


# ---------------------------------------------------------------------------
# Stage Enum Tests
# ---------------------------------------------------------------------------


class TestStage:
    """Tests for the Stage enum."""

    def test_stage_values(self) -> None:
        """Test all stage values exist."""
        assert Stage.EXPERIMENTATION.value == "experimentation"
        assert Stage.TESTING.value == "testing"
        assert Stage.STAGING.value == "staging"
        assert Stage.DEPLOYMENT.value == "deployment"
        assert Stage.PRODUCTION.value == "production"

    def test_stage_ordering(self) -> None:
        """Test stage comparison operators."""
        assert Stage.EXPERIMENTATION < Stage.TESTING
        assert Stage.TESTING < Stage.STAGING
        assert Stage.STAGING < Stage.DEPLOYMENT
        assert Stage.DEPLOYMENT < Stage.PRODUCTION
        assert not (Stage.PRODUCTION < Stage.EXPERIMENTATION)

    def test_stage_str(self) -> None:
        """Test stage string representation."""
        assert str(Stage.EXPERIMENTATION) == "Experimentation"
        assert str(Stage.PRODUCTION) == "Production"

    def test_stage_from_string(self) -> None:
        """Test Stage.from_string factory method."""
        assert Stage.from_string("testing") == Stage.TESTING
        assert Stage.from_string("TESTING") == Stage.TESTING
        assert Stage.from_string("Testing") == Stage.TESTING

    def test_stage_from_string_invalid(self) -> None:
        """Test Stage.from_string with invalid value."""
        with pytest.raises(ValueError, match="Invalid stage"):
            Stage.from_string("invalid")

    def test_stage_lt_with_non_stage(self) -> None:
        """Test Stage.__lt__ returns NotImplemented for non-Stage."""
        assert Stage.TESTING.__lt__("not_a_stage") is NotImplemented


# ---------------------------------------------------------------------------
# Severity Enum Tests
# ---------------------------------------------------------------------------


class TestSeverity:
    """Tests for the Severity enum."""

    def test_severity_values(self) -> None:
        """Test all severity values exist."""
        assert Severity.BLOCKER.value == "blocker"
        assert Severity.CRITICAL.value == "critical"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_severity_ordering(self) -> None:
        """Test severity ordering (BLOCKER > CRITICAL > WARNING > INFO)."""
        assert Severity.INFO < Severity.WARNING
        assert Severity.WARNING < Severity.CRITICAL
        assert Severity.CRITICAL < Severity.BLOCKER

    def test_severity_str(self) -> None:
        """Test severity string representation."""
        assert str(Severity.BLOCKER) == "Blocker"
        assert str(Severity.INFO) == "Info"

    def test_severity_lt_with_non_severity(self) -> None:
        """Test Severity.__lt__ returns NotImplemented for non-Severity."""
        assert Severity.BLOCKER.__lt__("not_a_severity") is NotImplemented


# ---------------------------------------------------------------------------
# ValidationResult Tests
# ---------------------------------------------------------------------------


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_passing_result(self) -> None:
        """Test creation of a passing result."""
        result = ValidationResult(
            check_name="test",
            passed=True,
            severity=Severity.BLOCKER,
            message="All good",
        )
        assert result.passed
        assert "✅ PASS" in str(result)

    def test_failing_result(self) -> None:
        """Test creation of a failing result."""
        result = ValidationResult(
            check_name="test",
            passed=False,
            severity=Severity.CRITICAL,
            message="Something wrong",
            fix_command="fix it",
        )
        assert not result.passed
        assert "❌ FAIL" in str(result)
        assert result.fix_command == "fix it"


# ---------------------------------------------------------------------------
# ValidationCheck Tests
# ---------------------------------------------------------------------------


class TestValidationCheck:
    """Tests for ValidationCheck execution."""

    @pytest.mark.asyncio
    async def test_check_passes(self, context: WorkflowContext, tmp_path: Path) -> None:
        """Test ValidationCheck that passes."""

        async def always_true(path: Path, ctx: WorkflowContext) -> bool:
            return True

        check = ValidationCheck(
            name="always_pass",
            description="Always passes",
            severity=Severity.BLOCKER,
            check_function=always_true,
            failure_message="Failed",
            success_message="Passed",
        )
        result = await check.execute(tmp_path, context)
        assert result.passed
        assert result.message == "Passed"
        assert result.fix_command is None

    @pytest.mark.asyncio
    async def test_check_fails(self, context: WorkflowContext, tmp_path: Path) -> None:
        """Test ValidationCheck that fails."""

        async def always_false(path: Path, ctx: WorkflowContext) -> bool:
            return False

        check = ValidationCheck(
            name="always_fail",
            description="Always fails",
            severity=Severity.WARNING,
            check_function=always_false,
            failure_message="Failed",
            fix_command="run fix",
        )
        result = await check.execute(tmp_path, context)
        assert not result.passed
        assert result.message == "Failed"
        assert result.fix_command == "run fix"

    @pytest.mark.asyncio
    async def test_check_exception(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test ValidationCheck that raises an exception."""

        async def raise_error(path: Path, ctx: WorkflowContext) -> bool:
            raise RuntimeError("boom")

        check = ValidationCheck(
            name="error_check",
            description="Raises error",
            severity=Severity.INFO,
            check_function=raise_error,
            failure_message="Failed",
        )
        result = await check.execute(tmp_path, context)
        assert not result.passed
        assert result.severity == Severity.CRITICAL  # Escalated on error
        assert "boom" in result.message


# ---------------------------------------------------------------------------
# ValidationPrimitive Tests
# ---------------------------------------------------------------------------


class TestValidationPrimitive:
    """Tests for ValidationPrimitive workflow integration."""

    @pytest.mark.asyncio
    async def test_validation_primitive_execute(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test ValidationPrimitive wraps ValidationCheck correctly."""

        async def check_fn(path: Path, ctx: WorkflowContext) -> bool:
            return (path / "README.md").exists()

        check = ValidationCheck(
            name="readme",
            description="Check README",
            severity=Severity.BLOCKER,
            check_function=check_fn,
            failure_message="No README",
        )
        primitive = ValidationPrimitive(check)

        # No README
        result = await primitive.execute(context, tmp_path)
        assert not result.passed

        # Create README
        (tmp_path / "README.md").write_text("# Hello")
        result = await primitive.execute(context, tmp_path)
        assert result.passed


# ---------------------------------------------------------------------------
# ReadinessCheckResult Tests
# ---------------------------------------------------------------------------


class TestReadinessCheckResult:
    """Tests for ReadinessCheckResult categorization."""

    def test_from_results_ready(self) -> None:
        """Test ready when no blockers."""
        results = [
            ValidationResult("a", True, Severity.BLOCKER, "ok"),
            ValidationResult("b", True, Severity.CRITICAL, "ok"),
        ]
        check_result = ReadinessCheckResult.from_results(results)
        assert check_result.ready
        assert len(check_result.blockers) == 0

    def test_from_results_not_ready(self) -> None:
        """Test not ready when blockers exist."""
        results = [
            ValidationResult("a", False, Severity.BLOCKER, "bad"),
            ValidationResult("b", False, Severity.CRITICAL, "warn"),
            ValidationResult("c", False, Severity.WARNING, "meh"),
            ValidationResult("d", False, Severity.INFO, "fyi"),
        ]
        check_result = ReadinessCheckResult.from_results(results)
        assert not check_result.ready
        assert len(check_result.blockers) == 1
        assert len(check_result.critical) == 1
        assert len(check_result.warnings) == 1
        assert len(check_result.info) == 1

    def test_from_results_critical_not_blocking(self) -> None:
        """Test that critical issues don't block readiness."""
        results = [
            ValidationResult("a", False, Severity.CRITICAL, "issue"),
        ]
        check_result = ReadinessCheckResult.from_results(results)
        assert check_result.ready  # Critical doesn't block


# ---------------------------------------------------------------------------
# ReadinessCheckPrimitive Tests
# ---------------------------------------------------------------------------


class TestReadinessCheckPrimitive:
    """Tests for ReadinessCheckPrimitive parallel execution."""

    @pytest.mark.asyncio
    async def test_parallel_execution(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test that multiple checks run in parallel."""

        async def check_readme(path: Path, ctx: WorkflowContext) -> bool:
            return (path / "README.md").exists()

        async def check_src(path: Path, ctx: WorkflowContext) -> bool:
            return (path / "src").exists()

        checks = [
            ValidationCheck(
                name="readme",
                description="README check",
                severity=Severity.BLOCKER,
                check_function=check_readme,
                failure_message="No README",
            ),
            ValidationCheck(
                name="src",
                description="Source check",
                severity=Severity.BLOCKER,
                check_function=check_src,
                failure_message="No src",
            ),
        ]

        primitive = ReadinessCheckPrimitive(checks)
        result = await primitive.execute(context, tmp_project)

        assert result.ready
        assert len(result.all_results) == 2
        assert all(r.passed for r in result.all_results)


# ---------------------------------------------------------------------------
# StageCriteria Tests
# ---------------------------------------------------------------------------


class TestStageCriteria:
    """Tests for StageCriteria dataclass."""

    def test_get_all_checks(self) -> None:
        """Test get_all_checks combines entry and exit criteria."""

        async def dummy(path: Path, ctx: WorkflowContext) -> bool:
            return True

        entry = ValidationCheck("e1", "entry", Severity.BLOCKER, dummy, "fail")
        exit_ = ValidationCheck("x1", "exit", Severity.WARNING, dummy, "fail")

        criteria = StageCriteria(
            stage=Stage.TESTING,
            entry_criteria=[entry],
            exit_criteria=[exit_],
        )
        all_checks = criteria.get_all_checks()
        assert len(all_checks) == 2
        assert all_checks[0].name == "e1"
        assert all_checks[1].name == "x1"


# ---------------------------------------------------------------------------
# StageReadiness Tests
# ---------------------------------------------------------------------------


class TestStageReadiness:
    """Tests for StageReadiness summary generation."""

    def test_get_summary_ready(self) -> None:
        """Test summary for a ready state."""
        readiness = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
        )
        summary = readiness.get_summary()
        assert "✅ READY" in summary
        assert "Testing" in summary
        assert "Staging" in summary

    def test_get_summary_not_ready(self) -> None:
        """Test summary for a not-ready state with blockers."""
        readiness = StageReadiness(
            current_stage=Stage.STAGING,
            target_stage=Stage.DEPLOYMENT,
            ready=False,
            blockers=[
                ValidationResult(
                    "x", False, Severity.BLOCKER, "missing license", "add license"
                )
            ],
            next_steps=["Add LICENSE file"],
            recommended_actions=["Run quality checks"],
        )
        summary = readiness.get_summary()
        assert "❌ NOT READY" in summary
        assert "missing license" in summary
        assert "NEXT STEPS" in summary
        assert "RECOMMENDED ACTIONS" in summary


# ---------------------------------------------------------------------------
# TransitionResult Tests
# ---------------------------------------------------------------------------


class TestTransitionResult:
    """Tests for TransitionResult."""

    def test_transition_result_timestamp(self) -> None:
        """Test auto-generated timestamp."""
        readiness = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
        )
        result = TransitionResult(
            success=True,
            from_stage=Stage.TESTING,
            to_stage=Stage.STAGING,
            message="ok",
            readiness=readiness,
        )
        assert result.timestamp  # Auto-generated
        assert "T" in result.timestamp  # ISO format

    def test_get_summary(self) -> None:
        """Test transition result summary."""
        readiness = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
        )
        result = TransitionResult(
            success=True,
            from_stage=Stage.TESTING,
            to_stage=Stage.STAGING,
            message="All good",
            readiness=readiness,
        )
        summary = result.get_summary()
        assert "✅ SUCCESS" in summary


# ---------------------------------------------------------------------------
# StageManager Tests
# ---------------------------------------------------------------------------


class TestStageManager:
    """Tests for StageManager readiness and transitions."""

    @pytest.mark.asyncio
    async def test_check_readiness_no_criteria(self, context: WorkflowContext) -> None:
        """Test readiness with no criteria defined returns ready."""
        manager = StageManager(stage_criteria_map={})
        readiness = await manager.check_readiness(
            current_stage=Stage.EXPERIMENTATION,
            target_stage=Stage.TESTING,
            project_path=Path("."),
            context=context,
        )
        assert readiness.ready

    @pytest.mark.asyncio
    async def test_check_readiness_with_checks(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test readiness with custom criteria checks."""

        async def check_readme(path: Path, ctx: WorkflowContext) -> bool:
            return (path / "README.md").exists()

        criteria = StageCriteria(
            stage=Stage.TESTING,
            entry_criteria=[
                ValidationCheck(
                    name="readme",
                    description="README check",
                    severity=Severity.BLOCKER,
                    check_function=check_readme,
                    failure_message="No README",
                )
            ],
        )

        manager = StageManager(stage_criteria_map={Stage.TESTING: criteria})
        readiness = await manager.check_readiness(
            current_stage=Stage.EXPERIMENTATION,
            target_stage=Stage.TESTING,
            project_path=tmp_project,
            context=context,
        )
        assert readiness.ready  # README exists in tmp_project

    @pytest.mark.asyncio
    async def test_check_readiness_with_blockers(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test readiness fails when blockers exist."""

        async def check_missing(path: Path, ctx: WorkflowContext) -> bool:
            return False

        criteria = StageCriteria(
            stage=Stage.TESTING,
            entry_criteria=[
                ValidationCheck(
                    name="missing",
                    description="Always fails",
                    severity=Severity.BLOCKER,
                    check_function=check_missing,
                    failure_message="Missing something",
                    fix_command="fix it",
                )
            ],
        )

        manager = StageManager(stage_criteria_map={Stage.TESTING: criteria})
        readiness = await manager.check_readiness(
            current_stage=Stage.EXPERIMENTATION,
            target_stage=Stage.TESTING,
            project_path=tmp_path,
            context=context,
        )
        assert not readiness.ready
        assert len(readiness.blockers) == 1
        assert len(readiness.next_steps) == 1

    @pytest.mark.asyncio
    async def test_execute_via_stage_request(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test execute() method via StageRequest."""
        manager = StageManager(stage_criteria_map={})
        request = StageRequest(
            project_path=tmp_project,
            current_stage=Stage.EXPERIMENTATION,
            target_stage=Stage.TESTING,
        )
        readiness = await manager.execute(context, request)
        assert readiness.ready

    @pytest.mark.asyncio
    async def test_transition_success(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test successful stage transition."""
        manager = StageManager(stage_criteria_map={})
        result = await manager.transition(
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            project_path=tmp_project,
            context=context,
        )
        assert result.success
        assert "✅" in result.message

    @pytest.mark.asyncio
    async def test_transition_failure_raises(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test transition raises StageTransitionError on blockers."""

        async def always_fail(path: Path, ctx: WorkflowContext) -> bool:
            return False

        criteria = StageCriteria(
            stage=Stage.TESTING,
            entry_criteria=[
                ValidationCheck(
                    name="blocker",
                    description="Always fails",
                    severity=Severity.BLOCKER,
                    check_function=always_fail,
                    failure_message="blocked",
                )
            ],
        )

        manager = StageManager(stage_criteria_map={Stage.TESTING: criteria})
        with pytest.raises(StageTransitionError):
            await manager.transition(
                from_stage=Stage.EXPERIMENTATION,
                to_stage=Stage.TESTING,
                project_path=tmp_path,
                context=context,
            )

    @pytest.mark.asyncio
    async def test_transition_force(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test forced transition overrides blockers."""

        async def always_fail(path: Path, ctx: WorkflowContext) -> bool:
            return False

        criteria = StageCriteria(
            stage=Stage.TESTING,
            entry_criteria=[
                ValidationCheck(
                    name="blocker",
                    description="Always fails",
                    severity=Severity.BLOCKER,
                    check_function=always_fail,
                    failure_message="blocked",
                )
            ],
        )

        manager = StageManager(stage_criteria_map={Stage.TESTING: criteria})
        result = await manager.transition(
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            project_path=tmp_path,
            context=context,
            force=True,
        )
        assert result.success
        assert "Forced" in result.message


# ---------------------------------------------------------------------------
# Generic Checks Tests
# ---------------------------------------------------------------------------


class TestGenericChecks:
    """Tests for language-agnostic validation checks."""

    @pytest.mark.asyncio
    async def test_has_package_manifest(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test HAS_PACKAGE_MANIFEST check."""
        result = await HAS_PACKAGE_MANIFEST.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_package_manifest_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_PACKAGE_MANIFEST fails when no manifest."""
        result = await HAS_PACKAGE_MANIFEST.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_readme(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test HAS_README check."""
        result = await HAS_README.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_readme_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_README fails when no README."""
        result = await HAS_README.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_license(
        self, context: WorkflowContext, complete_project: Path
    ) -> None:
        """Test HAS_LICENSE check."""
        result = await HAS_LICENSE.execute(complete_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_license_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_LICENSE fails when no LICENSE."""
        result = await HAS_LICENSE.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_tests_directory(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test HAS_TESTS_DIRECTORY check."""
        result = await HAS_TESTS_DIRECTORY.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_tests_directory_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_TESTS_DIRECTORY fails when no tests/."""
        result = await HAS_TESTS_DIRECTORY.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_src_directory(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test HAS_SRC_DIRECTORY check."""
        result = await HAS_SRC_DIRECTORY.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_src_directory_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_SRC_DIRECTORY fails when no source code."""
        result = await HAS_SRC_DIRECTORY.execute(tmp_path, context)
        assert not result.passed


# ---------------------------------------------------------------------------
# Documentation Checks Tests
# ---------------------------------------------------------------------------


class TestDocumentationChecks:
    """Tests for documentation validation checks."""

    @pytest.mark.asyncio
    async def test_readme_has_sections(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test HAS_README_SECTIONS passes when README has required sections."""
        result = await HAS_README_SECTIONS.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_readme_has_sections_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_README_SECTIONS fails when README has no required sections."""
        (tmp_path / "README.md").write_text("# My Project\n\nJust a description.\n")
        result = await HAS_README_SECTIONS.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_readme_has_sections_no_readme(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_README_SECTIONS fails when no README."""
        result = await HAS_README_SECTIONS.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_changelog(
        self, context: WorkflowContext, complete_project: Path
    ) -> None:
        """Test HAS_CHANGELOG passes when CHANGELOG.md exists."""
        result = await HAS_CHANGELOG.execute(complete_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_changelog_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_CHANGELOG fails when no CHANGELOG."""
        result = await HAS_CHANGELOG.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_changelog_changes_md(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_CHANGELOG passes with CHANGES.md variant."""
        (tmp_path / "CHANGES.md").write_text("# Changes\n")
        result = await HAS_CHANGELOG.execute(tmp_path, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_examples(
        self, context: WorkflowContext, complete_project: Path
    ) -> None:
        """Test HAS_EXAMPLES passes when examples/ exists."""
        result = await HAS_EXAMPLES.execute(complete_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_examples_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_EXAMPLES fails when no examples."""
        result = await HAS_EXAMPLES.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_examples_via_files(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_EXAMPLES passes with example_*.py files."""
        (tmp_path / "example_basic.py").write_text("print('hello')\n")
        result = await HAS_EXAMPLES.execute(tmp_path, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_docstrings(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test HAS_DOCSTRINGS passes when source files have docstrings."""
        result = await HAS_DOCSTRINGS.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_has_docstrings_missing(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_DOCSTRINGS fails when files lack docstrings."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text("x = 1\n")
        (src / "b.py").write_text("y = 2\n")
        result = await HAS_DOCSTRINGS.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_has_docstrings_no_src(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test HAS_DOCSTRINGS passes vacuously when no src/."""
        result = await HAS_DOCSTRINGS.execute(tmp_path, context)
        assert result.passed


# ---------------------------------------------------------------------------
# Git Checks Tests
# ---------------------------------------------------------------------------


class TestGitChecks:
    """Tests for git validation checks."""

    @pytest.mark.asyncio
    async def test_working_tree_clean(self, context: WorkflowContext) -> None:
        """Test WORKING_TREE_CLEAN against a clean git repo."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmp_path,
                capture_output=True,
            )
            (tmp_path / "file.txt").write_text("hello")
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True
            )

            result = await WORKING_TREE_CLEAN.execute(tmp_path, context)
            assert result.passed

    @pytest.mark.asyncio
    async def test_working_tree_dirty(self, context: WorkflowContext) -> None:
        """Test WORKING_TREE_CLEAN fails with uncommitted changes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmp_path,
                capture_output=True,
            )
            (tmp_path / "file.txt").write_text("hello")
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True
            )
            # Now make a dirty change
            (tmp_path / "dirty.txt").write_text("uncommitted")

            result = await WORKING_TREE_CLEAN.execute(tmp_path, context)
            assert not result.passed

    @pytest.mark.asyncio
    async def test_on_correct_branch_main(self, context: WorkflowContext) -> None:
        """Test ON_CORRECT_BRANCH passes on main branch."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmp_path,
                capture_output=True,
            )
            (tmp_path / "f.txt").write_text("x")
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True
            )

            result = await ON_CORRECT_BRANCH.execute(tmp_path, context)
            assert result.passed

    @pytest.mark.asyncio
    async def test_on_correct_branch_feature(self, context: WorkflowContext) -> None:
        """Test ON_CORRECT_BRANCH fails on feature branch."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmp_path,
                capture_output=True,
            )
            (tmp_path / "f.txt").write_text("x")
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True
            )
            subprocess.run(
                ["git", "checkout", "-b", "feature/my-branch"],
                cwd=tmp_path,
                capture_output=True,
            )

            result = await ON_CORRECT_BRANCH.execute(tmp_path, context)
            assert not result.passed

    @pytest.mark.asyncio
    async def test_version_bumped_no_tags(self, context: WorkflowContext) -> None:
        """Test VERSION_BUMPED passes when no tags exist (first release)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmp_path,
                capture_output=True,
            )
            (tmp_path / "pyproject.toml").write_text(
                '[project]\nname = "test"\nversion = "0.1.0"\n'
            )
            subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True
            )

            result = await VERSION_BUMPED.execute(tmp_path, context)
            assert result.passed  # No tags = version considered bumped

    @pytest.mark.asyncio
    async def test_version_bumped_no_manifest(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test VERSION_BUMPED fails with no manifest file."""
        result = await VERSION_BUMPED.execute(tmp_path, context)
        assert not result.passed


# ---------------------------------------------------------------------------
# Security Checks Tests
# ---------------------------------------------------------------------------


class TestSecurityChecks:
    """Tests for security validation checks."""

    @pytest.mark.asyncio
    async def test_no_secrets_clean(
        self, context: WorkflowContext, tmp_project: Path
    ) -> None:
        """Test NO_SECRETS_IN_CODE passes on clean project."""
        result = await NO_SECRETS_IN_CODE.execute(tmp_project, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_no_secrets_with_secret(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test NO_SECRETS_IN_CODE fails when secret is detected."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.py").write_text('api_key = "sk_test_FAKE_KEY_FOR_TESTING"\n')
        result = await NO_SECRETS_IN_CODE.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_no_secrets_test_files_skipped(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test NO_SECRETS_IN_CODE skips test files."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "test_config.py").write_text(
            'api_key = "sk_test_FAKE_KEY_FOR_TESTING"\n'
        )
        result = await NO_SECRETS_IN_CODE.execute(tmp_path, context)
        assert result.passed  # Skipped because it's a test file

    @pytest.mark.asyncio
    async def test_dependencies_up_to_date_with_lock(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test DEPENDENCIES_UP_TO_DATE passes with lock file."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "uv.lock").write_text("# lock\n")
        result = await DEPENDENCIES_UP_TO_DATE.execute(tmp_path, context)
        assert result.passed

    @pytest.mark.asyncio
    async def test_dependencies_up_to_date_no_lock(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test DEPENDENCIES_UP_TO_DATE fails without lock file."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        result = await DEPENDENCIES_UP_TO_DATE.execute(tmp_path, context)
        assert not result.passed

    @pytest.mark.asyncio
    async def test_dependencies_up_to_date_no_project(
        self, context: WorkflowContext, tmp_path: Path
    ) -> None:
        """Test DEPENDENCIES_UP_TO_DATE passes with no recognizable project."""
        result = await DEPENDENCIES_UP_TO_DATE.execute(tmp_path, context)
        assert result.passed  # Vacuously true


# ---------------------------------------------------------------------------
# Stage Definitions Tests
# ---------------------------------------------------------------------------


class TestStageDefinitions:
    """Tests for predefined stage criteria and STAGE_CRITERIA_MAP."""

    def test_stage_criteria_map_has_all_stages(self) -> None:
        """Test STAGE_CRITERIA_MAP covers all non-experimentation stages."""
        assert Stage.TESTING in STAGE_CRITERIA_MAP
        assert Stage.STAGING in STAGE_CRITERIA_MAP
        assert Stage.DEPLOYMENT in STAGE_CRITERIA_MAP
        assert Stage.PRODUCTION in STAGE_CRITERIA_MAP

    def test_experimentation_to_testing_has_entry_and_exit(self) -> None:
        """Test EXPERIMENTATION_TO_TESTING has entry and exit criteria."""
        assert len(EXPERIMENTATION_TO_TESTING.entry_criteria) >= 2
        assert len(EXPERIMENTATION_TO_TESTING.exit_criteria) >= 2
        assert len(EXPERIMENTATION_TO_TESTING.recommended_actions) > 0

    def test_testing_to_staging_has_entry_and_exit(self) -> None:
        """Test TESTING_TO_STAGING has entry and exit criteria."""
        assert len(TESTING_TO_STAGING.entry_criteria) >= 2
        assert len(TESTING_TO_STAGING.exit_criteria) >= 3
        assert len(TESTING_TO_STAGING.recommended_actions) > 0

    def test_staging_to_deployment_includes_new_checks(self) -> None:
        """Test STAGING_TO_DEPLOYMENT includes documentation, git, security checks."""
        all_check_names = [c.name for c in STAGING_TO_DEPLOYMENT.get_all_checks()]
        assert "CHANGELOG exists" in all_check_names
        assert "No secrets in code" in all_check_names
        assert "Working tree clean" in all_check_names
        assert "Version bumped" in all_check_names

    def test_deployment_to_production_includes_security(self) -> None:
        """Test DEPLOYMENT_TO_PRODUCTION includes security checks."""
        all_check_names = [c.name for c in DEPLOYMENT_TO_PRODUCTION.get_all_checks()]
        assert "No secrets in code" in all_check_names
        assert "Dependencies up to date" in all_check_names

    def test_all_checks_have_required_fields(self) -> None:
        """Test all checks in all stages have required fields."""
        for stage, criteria in STAGE_CRITERIA_MAP.items():
            for check in criteria.get_all_checks():
                assert check.name, f"Check missing name in {stage}"
                assert check.description, (
                    f"Check '{check.name}' missing description in {stage}"
                )
                assert check.failure_message, (
                    f"Check '{check.name}' missing failure_message"
                )
                assert check.severity is not None, (
                    f"Check '{check.name}' missing severity"
                )


# ---------------------------------------------------------------------------
# All Checks Import Test
# ---------------------------------------------------------------------------


class TestAllChecksImportable:
    """Test that all 20 checks are importable from the checks package."""

    def test_all_generic_checks(self) -> None:
        """Test all 5 generic checks are importable."""
        assert HAS_PACKAGE_MANIFEST is not None
        assert HAS_README is not None
        assert HAS_LICENSE is not None
        assert HAS_TESTS_DIRECTORY is not None
        assert HAS_SRC_DIRECTORY is not None

    def test_all_python_checks(self) -> None:
        """Test all 4 Python checks are importable."""
        assert TESTS_PASS is not None
        assert TYPE_CHECK_PASSES is not None
        assert LINT_PASSES is not None
        assert FORMAT_CHECK_PASSES is not None

    def test_all_documentation_checks(self) -> None:
        """Test all 4 documentation checks are importable."""
        assert HAS_README_SECTIONS is not None
        assert HAS_CHANGELOG is not None
        assert HAS_EXAMPLES is not None
        assert HAS_DOCSTRINGS is not None

    def test_all_git_checks(self) -> None:
        """Test all 4 git checks are importable."""
        assert WORKING_TREE_CLEAN is not None
        assert ON_CORRECT_BRANCH is not None
        assert REMOTE_UP_TO_DATE is not None
        assert VERSION_BUMPED is not None

    def test_all_security_checks(self) -> None:
        """Test all 3 security checks are importable."""
        assert NO_SECRETS_IN_CODE is not None
        assert DEPENDENCIES_UP_TO_DATE is not None
        assert NO_KNOWN_VULNERABILITIES is not None

    def test_total_check_count(self) -> None:
        """Test we have the expected number of checks (20 total)."""
        from ttadev.lifecycle import checks

        all_names = checks.__all__
        assert len(all_names) == 20
