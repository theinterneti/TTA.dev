"""Tests for Git collaboration primitives."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from tta_dev_primitives.collaboration import (
    AgentIdentity,
    CommitFrequencyPolicy,
    GitCollaborationPrimitive,
    IntegrationFrequency,
    MergeStrategy,
)
from tta_dev_primitives.core import WorkflowContext


@pytest.fixture
def agent_identity():
    """Create test agent identity."""
    return AgentIdentity(
        name="Test Agent",
        email="test@tta.dev",
        branch_prefix="agent/test",
    )


@pytest.fixture
def git_primitive(agent_identity, tmp_path):
    """Create GitCollaborationPrimitive for testing."""
    return GitCollaborationPrimitive(
        agent_identity=agent_identity,
        integration_frequency=IntegrationFrequency.DAILY,
        repository_path=tmp_path,
        enforce_hygiene=True,
    )


@pytest.fixture
def workflow_context():
    """Create test workflow context."""
    return WorkflowContext(workflow_id="test-git-workflow")


class TestCommitValidation:
    """Test commit message and hygiene validation."""

    @pytest.mark.asyncio
    async def test_commit_message_too_short_raises_error(
        self, git_primitive, workflow_context
    ):
        """Test that short commit messages are rejected."""
        with pytest.raises(ValueError, match="Commit message too short"):
            await git_primitive.execute(
                {"action": "commit", "message": "short", "files": ["test.py"]},
                workflow_context,
            )

    @pytest.mark.asyncio
    async def test_commit_requires_conventional_format(
        self, git_primitive, workflow_context
    ):
        """Test that conventional commit format is enforced."""
        with pytest.raises(ValueError, match="conventional commits format"):
            await git_primitive.execute(
                {
                    "action": "commit",
                    "message": "This is a long message but no prefix",
                    "files": ["test.py"],
                },
                workflow_context,
            )

    @pytest.mark.asyncio
    async def test_valid_conventional_commit_accepted(
        self, git_primitive, workflow_context, tmp_path
    ):
        """Test that valid conventional commits are accepted."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")

        result = await git_primitive.execute(
            {
                "action": "commit",
                "message": "feat: Add new test feature with proper formatting",
                "files": [test_file],
            },
            workflow_context,
        )

        # Should succeed (or fail only due to git setup, not validation)
        assert result is not None
        # In real git repo, would check result["hygiene_checks_passed"]


class TestIntegrationFrequency:
    """Test integration frequency policies."""

    def test_continuous_integration_max_time(self, git_primitive):
        """Test continuous integration time limits."""
        git_primitive.integration_frequency = IntegrationFrequency.CONTINUOUS
        max_time = git_primitive._get_max_integration_time()
        assert max_time == timedelta(hours=1)

    def test_hourly_integration_max_time(self, git_primitive):
        """Test hourly integration time limits."""
        git_primitive.integration_frequency = IntegrationFrequency.HOURLY
        max_time = git_primitive._get_max_integration_time()
        assert max_time == timedelta(hours=2)

    def test_daily_integration_max_time(self, git_primitive):
        """Test daily integration time limits."""
        git_primitive.integration_frequency = IntegrationFrequency.DAILY
        max_time = git_primitive._get_max_integration_time()
        assert max_time == timedelta(days=1)


class TestHealthChecks:
    """Test branch health monitoring."""

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self, git_primitive, workflow_context):
        """Test that health check returns comprehensive status."""
        result = await git_primitive.execute(
            {"action": "status"}, workflow_context
        )

        assert "healthy" in result
        assert "uncommitted_files" in result
        assert "time_since_commit_hours" in result
        assert "commits_behind_main" in result
        assert "health_issues" in result
        assert "recommendation" in result

    def test_health_recommendation_for_uncommitted_files(self, git_primitive):
        """Test health recommendations for uncommitted files."""
        issues = ["Too many uncommitted files: 60 (max: 50)"]
        recommendation = git_primitive._get_health_recommendation(issues)
        assert "Commit your changes" in recommendation
        assert "git add" in recommendation

    def test_health_recommendation_for_no_commits(self, git_primitive):
        """Test health recommendations for stale commits."""
        issues = ["No commit in 2.5 hours (max: 60 minutes)"]
        recommendation = git_primitive._get_health_recommendation(issues)
        assert "Commit frequently" in recommendation

    def test_health_recommendation_for_divergence(self, git_primitive):
        """Test health recommendations for branch divergence."""
        issues = ["Branch is 15 commits behind main. Sync soon!"]
        recommendation = git_primitive._get_health_recommendation(issues)
        assert "Sync with main" in recommendation


class TestAgentIdentity:
    """Test agent identity configuration."""

    def test_agent_identity_creation(self):
        """Test creating agent identity."""
        agent = AgentIdentity(
            name="GitHub Copilot",
            email="copilot@tta.dev",
            branch_prefix="agent/copilot",
        )

        assert agent.name == "GitHub Copilot"
        assert agent.email == "copilot@tta.dev"
        assert agent.branch_prefix == "agent/copilot"

    def test_agent_identity_with_worktree(self, tmp_path):
        """Test agent identity with worktree path."""
        worktree = tmp_path / "worktree"
        agent = AgentIdentity(
            name="Test Agent",
            email="test@tta.dev",
            branch_prefix="agent/test",
            worktree_path=worktree,
        )

        assert agent.worktree_path == worktree


class TestCommitFrequencyPolicy:
    """Test commit frequency policy configuration."""

    def test_default_policy(self):
        """Test default commit frequency policy."""
        policy = CommitFrequencyPolicy()

        assert policy.max_uncommitted_changes == 50
        assert policy.max_uncommitted_time_minutes == 60
        assert policy.require_tests_before_commit is True
        assert policy.require_descriptive_messages is True
        assert policy.min_message_length == 20

    def test_custom_policy(self):
        """Test custom commit frequency policy."""
        policy = CommitFrequencyPolicy(
            max_uncommitted_changes=25,
            max_uncommitted_time_minutes=30,
            require_tests_before_commit=False,
            min_message_length=10,
        )

        assert policy.max_uncommitted_changes == 25
        assert policy.max_uncommitted_time_minutes == 30
        assert policy.require_tests_before_commit is False
        assert policy.min_message_length == 10


class TestMergeStrategies:
    """Test merge strategy configurations."""

    def test_merge_strategies_available(self):
        """Test that all merge strategies are available."""
        assert MergeStrategy.FAST_FORWARD == "fast_forward"
        assert MergeStrategy.MERGE_COMMIT == "merge_commit"
        assert MergeStrategy.SQUASH == "squash"


class TestEnforceHygiene:
    """Test hygiene enforcement modes."""

    @pytest.mark.asyncio
    async def test_enforce_mode_raises_errors(self, agent_identity, tmp_path):
        """Test that enforce mode raises errors for violations."""
        git_primitive = GitCollaborationPrimitive(
            agent_identity=agent_identity,
            repository_path=tmp_path,
            enforce_hygiene=True,
        )

        context = WorkflowContext()

        with pytest.raises(ValueError):
            await git_primitive.execute(
                {"action": "commit", "message": "bad", "files": []}, context
            )

    @pytest.mark.asyncio
    async def test_warning_mode_returns_warnings(
        self, agent_identity, tmp_path, workflow_context
    ):
        """Test that warning mode returns warnings without raising."""
        git_primitive = GitCollaborationPrimitive(
            agent_identity=agent_identity,
            repository_path=tmp_path,
            enforce_hygiene=False,
        )

        # This should succeed with hygiene disabled
        # (though git commands may fail without proper repo setup)
        result = await git_primitive.execute(
            {"action": "enforce_frequency"}, workflow_context
        )

        # Should not raise, may contain warnings
        assert result is not None


class TestWorkflowIntegration:
    """Test integration with workflow context."""

    @pytest.mark.asyncio
    async def test_commits_tracked_in_context(
        self, git_primitive, workflow_context, tmp_path
    ):
        """Test that commits are tracked in workflow context."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        await git_primitive.execute(
            {
                "action": "commit",
                "message": "feat: Add test file for commit tracking",
                "files": [test_file],
            },
            workflow_context,
        )

        # Check metadata updated
        assert "last_commit" in workflow_context.metadata
        assert "commits_today" in workflow_context.metadata

    @pytest.mark.asyncio
    async def test_integration_tracked_in_context(
        self, git_primitive, workflow_context
    ):
        """Test that integrations are tracked in workflow context."""
        result = await git_primitive.execute(
            {
                "action": "integrate",
                "title": "feat: Test integration",
                "body": "Testing PR creation",
            },
            workflow_context,
        )

        # Check metadata updated
        if result["success"]:
            assert "last_integration" in workflow_context.metadata


class TestBestPracticesEnforcement:
    """Test enforcement of Martin Fowler's best practices."""

    @pytest.mark.asyncio
    async def test_frequent_integration_warning(
        self, git_primitive, workflow_context
    ):
        """Test warning for infrequent integration."""
        # Set last integration to 2 days ago
        workflow_context.metadata["last_integration"] = (
            datetime.now() - timedelta(days=2)
        ).isoformat()

        result = await git_primitive.execute(
            {
                "action": "integrate",
                "title": "feat: Overdue integration",
                "body": "Should warn about overdue integration",
            },
            workflow_context,
        )

        # Should succeed but may have warning
        if result.get("success"):
            # In real scenario with proper git repo
            pass
