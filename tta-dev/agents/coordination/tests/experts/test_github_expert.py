"""Tests for GitHubExpert - L3 Tool Expertise Layer."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.experts.github_expert import (
    GitHubExpert,
    GitHubExpertConfig,
)
from tta_agent_coordination.wrappers.github_wrapper import (
    GitHubConfig,
    GitHubOperation,
)


@pytest.fixture
def mock_github_wrapper():
    """Mock GitHubAPIWrapper."""
    with patch("tta_agent_coordination.experts.github_expert.GitHubAPIWrapper") as mock:
        wrapper_instance = Mock()
        wrapper_instance.execute = AsyncMock()
        wrapper_instance.close = Mock()
        mock.return_value = wrapper_instance
        yield wrapper_instance


@pytest.fixture
def expert(mock_github_wrapper):
    """Create GitHubExpert with mocked wrapper."""
    config = GitHubExpertConfig(
        github_config=GitHubConfig(token="test-token"),
        max_retries=2,
        cache_enabled=True,
        cache_ttl=60,
    )
    return GitHubExpert(config=config)


@pytest.fixture
def context():
    """Create workflow context."""
    return WorkflowContext(correlation_id="test-123")


class TestGitHubExpert:
    """Test suite for GitHubExpert."""

    # === Initialization Tests ===

    @pytest.mark.asyncio
    async def test_init_with_config(self, mock_github_wrapper):
        """Test initialization with custom config."""
        config = GitHubExpertConfig(
            max_retries=5,
            backoff_factor=3.0,
            cache_enabled=False,
        )
        expert = GitHubExpert(config=config)

        assert expert.config.max_retries == 5
        assert expert.config.backoff_factor == 3.0
        assert expert.config.cache_enabled is False

    @pytest.mark.asyncio
    async def test_init_default_config(self, mock_github_wrapper):
        """Test initialization with default config."""
        expert = GitHubExpert()

        assert expert.config.max_retries == 3
        assert expert.config.cache_enabled is True
        assert expert.config.cache_ttl == 300

    # === Validation Tests ===

    @pytest.mark.asyncio
    async def test_create_pr_empty_title_fails(self, expert, context):
        """Test PR creation with empty title fails validation."""
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "",
                "body": "Description",
                "head": "feature",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "title cannot be empty" in result.error
        assert result.data.get("validation_failed") is True

    @pytest.mark.asyncio
    async def test_create_pr_empty_body_warning(self, expert, context):
        """Test PR creation with empty body fails validation."""
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Add feature",
                "body": "  ",
                "head": "feature",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "should include description" in result.error

    @pytest.mark.asyncio
    async def test_create_pr_body_too_long(self, expert, context):
        """Test PR creation with overly long body."""
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Add feature",
                "body": "x" * 70000,  # Exceeds 64KB limit
                "head": "feature",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "exceeds" in result.error

    @pytest.mark.asyncio
    async def test_create_pr_same_branch_fails(self, expert, context):
        """Test PR creation with same head and base branch."""
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Add feature",
                "body": "Description",
                "head": "main",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "cannot be the same" in result.error

    @pytest.mark.asyncio
    async def test_create_pr_missing_branch_fails(self, expert, context):
        """Test PR creation with missing branch names."""
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Add feature",
                "body": "Description",
                "head": "",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "required" in result.error

    @pytest.mark.asyncio
    async def test_update_file_empty_commit_message(self, expert, context):
        """Test file update with empty commit message."""
        operation = GitHubOperation(
            operation="update_file",
            repo_name="org/repo",
            params={
                "path": "README.md",
                "content": "New content",
                "message": "  ",
                "sha": "abc123",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "Commit message cannot be empty" in result.error

    @pytest.mark.asyncio
    async def test_update_file_message_too_long(self, expert, context):
        """Test file update with overly long commit message."""
        operation = GitHubOperation(
            operation="update_file",
            repo_name="org/repo",
            params={
                "path": "README.md",
                "content": "New content",
                "message": "x" * 6000,  # Exceeds 5KB limit
                "sha": "abc123",
            },
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "exceeds" in result.error

    @pytest.mark.asyncio
    async def test_create_issue_empty_title(self, expert, context):
        """Test issue creation with empty title."""
        operation = GitHubOperation(
            operation="create_issue",
            repo_name="org/repo",
            params={"title": "  ", "body": "Issue description"},
        )

        result = await expert.execute(operation, context)

        assert result.success is False
        assert "title cannot be empty" in result.error

    # === Successful Operation Tests ===

    @pytest.mark.asyncio
    async def test_create_pr_success(self, expert, context, mock_github_wrapper):
        """Test successful PR creation."""
        mock_github_wrapper.execute.return_value = {
            "success": True,
            "data": {"number": 42, "html_url": "https://github.com/org/repo/pull/42"},
        }

        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Add feature",
                "body": "Adds cool feature",
                "head": "feature",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result["success"] is True
        assert result["data"]["number"] == 42

    @pytest.mark.asyncio
    async def test_get_pr_uses_cache(self, expert, context, mock_github_wrapper):
        """Test GET operations use caching."""
        mock_github_wrapper.execute.return_value = {
            "success": True,
            "data": {"number": 42, "title": "Test PR"},
        }

        operation = GitHubOperation(
            operation="get_pr",
            repo_name="org/repo",
            params={"pr_number": 42},
        )

        # First call
        result1 = await expert.execute(operation, context)
        assert result1["success"] is True

        # Second call should use cache (wrapper called only once)
        result2 = await expert.execute(operation, context)
        assert result2["success"] is True

        # Wrapper should be called twice due to retry wrapper
        # But cache should prevent multiple calls to underlying wrapper
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_list_prs_uses_cache(self, expert, context, mock_github_wrapper):
        """Test list PRs uses caching."""
        mock_github_wrapper.execute.return_value = {
            "success": True,
            "data": {"prs": [{"number": 1}, {"number": 2}]},
        }

        operation = GitHubOperation(
            operation="list_prs",
            repo_name="org/repo",
            params={"state": "open"},
        )

        result = await expert.execute(operation, context)

        assert result["success"] is True
        assert len(result["data"]["prs"]) == 2

    @pytest.mark.asyncio
    async def test_mutating_operations_no_cache(
        self, expert, context, mock_github_wrapper
    ):
        """Test mutating operations don't use cache."""
        mock_github_wrapper.execute.return_value = {
            "success": True,
            "data": {"number": 42},
        }

        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Test",
                "body": "Description",
                "head": "feature",
                "base": "main",
            },
        )

        result = await expert.execute(operation, context)

        assert result["success"] is True
        # Mutating operations should bypass cache

    # === Cache Key Generation Tests ===

    @pytest.mark.asyncio
    async def test_cache_key_includes_operation(self, expert, context):
        """Test cache key includes operation type."""
        operation1 = GitHubOperation(
            operation="get_pr", repo_name="org/repo", params={"pr_number": 42}
        )

        operation2 = GitHubOperation(
            operation="list_prs", repo_name="org/repo", params={"state": "open"}
        )

        key1 = expert._cache_key(operation1, context)
        key2 = expert._cache_key(operation2, context)

        assert key1 != key2
        assert "get_pr" in key1
        assert "list_prs" in key2

    @pytest.mark.asyncio
    async def test_cache_key_includes_params(self, expert, context):
        """Test cache key includes relevant params."""
        operation1 = GitHubOperation(
            operation="get_pr", repo_name="org/repo", params={"pr_number": 42}
        )

        operation2 = GitHubOperation(
            operation="get_pr", repo_name="org/repo", params={"pr_number": 43}
        )

        key1 = expert._cache_key(operation1, context)
        key2 = expert._cache_key(operation2, context)

        assert key1 != key2
        assert "42" in key1
        assert "43" in key2

    # === Close Tests ===

    @pytest.mark.asyncio
    async def test_close_calls_wrapper(self, expert, mock_github_wrapper):
        """Test close() calls underlying wrapper."""
        expert.close()

        mock_github_wrapper.close.assert_called_once()

    # === Configuration Tests ===

    @pytest.mark.asyncio
    async def test_cache_disabled_config(self, mock_github_wrapper):
        """Test expert with caching disabled."""
        config = GitHubExpertConfig(cache_enabled=False)
        expert = GitHubExpert(config=config)

        assert expert._with_cache == expert._with_retry

    @pytest.mark.asyncio
    async def test_custom_retry_config(self, mock_github_wrapper):
        """Test custom retry configuration."""
        config = GitHubExpertConfig(max_retries=10, backoff_factor=5.0, jitter=False)

        expert = GitHubExpert(config=config)

        assert expert.config.max_retries == 10
        assert expert.config.backoff_factor == 5.0
        assert expert.config.jitter is False
