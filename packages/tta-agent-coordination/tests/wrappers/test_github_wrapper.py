"""
Tests for GitHub API Wrapper (L4 Execution Layer).

Comprehensive test coverage for GitHubAPIWrapper including:
- All supported operations
- Error handling
- Rate limiting
- Authentication
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from github import GithubException, RateLimitExceededException
from tta_dev_primitives import WorkflowContext

from tta_agent_coordination.wrappers.github_wrapper import (
    GitHubAPIWrapper,
    GitHubConfig,
    GitHubOperation,
)


@pytest.fixture
def mock_github_client():
    """Mock GitHub client."""
    with patch("tta_agent_coordination.wrappers.github_wrapper.Github") as mock:
        yield mock


@pytest.fixture
def mock_repo():
    """Mock repository."""
    repo = MagicMock()
    repo.name = "test-repo"
    repo.full_name = "owner/test-repo"
    return repo


@pytest.fixture
def wrapper(mock_github_client):
    """Create GitHub wrapper with mock client."""
    config = GitHubConfig(token="test-token")
    wrapper = GitHubAPIWrapper(config=config)
    return wrapper


@pytest.fixture
def context():
    """Create workflow context."""
    return WorkflowContext(correlation_id="test-123")


class TestGitHubAPIWrapper:
    """Test suite for GitHubAPIWrapper."""

    def test_init_with_config(self, mock_github_client):
        """Test initialization with explicit config."""
        config = GitHubConfig(token="explicit-token", timeout=60)
        wrapper = GitHubAPIWrapper(config=config)

        assert wrapper.config.token == "explicit-token"
        assert wrapper.config.timeout == 60

    def test_init_without_token_raises(self, mock_github_client):
        """Test initialization without token raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token required"):
                GitHubAPIWrapper(config=GitHubConfig())

    def test_init_with_env_token(self, mock_github_client):
        """Test initialization with GITHUB_TOKEN env var."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env-token"}):
            wrapper = GitHubAPIWrapper()
            assert wrapper.config.token is None  # Config uses env default

    @pytest.mark.asyncio
    async def test_create_pr_success(self, wrapper, mock_repo, context):
        """Test successful PR creation."""
        # Setup mock
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.html_url = "https://github.com/owner/repo/pull/123"
        mock_pr.state = "open"
        mock_pr.created_at = None
        mock_repo.create_pull = MagicMock(return_value=mock_pr)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4999
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        # Execute
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="owner/repo",
            params={
                "title": "Test PR",
                "body": "Test body",
                "head": "feature",
                "base": "main",
            },
        )

        result = await wrapper.execute(operation, context)

        # Assert
        assert result.success is True
        assert result.operation == "create_pr"
        assert result.data["number"] == 123
        assert result.data["url"] == "https://github.com/owner/repo/pull/123"
        assert result.rate_limit_remaining == 4999

    @pytest.mark.asyncio
    async def test_create_pr_missing_params(self, wrapper, mock_repo, context):
        """Test PR creation with missing parameters."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        operation = GitHubOperation(
            operation="create_pr",
            repo_name="owner/repo",
            params={"title": "Test PR"},  # Missing body, head, base
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Missing required parameters" in result.error

    @pytest.mark.asyncio
    async def test_list_prs_success(self, wrapper, mock_repo, context):
        """Test listing pull requests."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_pr1 = MagicMock()
        mock_pr1.number = 1
        mock_pr1.title = "PR 1"
        mock_pr1.state = "open"
        mock_pr1.html_url = "https://github.com/owner/repo/pull/1"
        mock_pr1.created_at = None

        mock_pr2 = MagicMock()
        mock_pr2.number = 2
        mock_pr2.title = "PR 2"
        mock_pr2.state = "closed"
        mock_pr2.html_url = "https://github.com/owner/repo/pull/2"
        mock_pr2.created_at = None

        mock_repo.get_pulls = MagicMock(return_value=[mock_pr1, mock_pr2])

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4998
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="list_prs",
            repo_name="owner/repo",
            params={"state": "all", "max_results": 10},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["count"] == 2
        assert len(result.data["prs"]) == 2

    @pytest.mark.asyncio
    async def test_get_pr_success(self, wrapper, mock_repo, context):
        """Test getting specific PR."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.title = "Feature PR"
        mock_pr.body = "PR description"
        mock_pr.state = "open"
        mock_pr.html_url = "https://github.com/owner/repo/pull/42"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.mergeable = True
        mock_pr.merged = False
        mock_pr.created_at = None
        mock_pr.updated_at = None

        mock_repo.get_pull = MagicMock(return_value=mock_pr)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4997
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="get_pr", repo_name="owner/repo", params={"number": 42}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["number"] == 42
        assert result.data["title"] == "Feature PR"
        assert result.data["mergeable"] is True

    @pytest.mark.asyncio
    async def test_merge_pr_success(self, wrapper, mock_repo, context):
        """Test merging PR."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_pr = MagicMock()
        mock_merge_result = MagicMock()
        mock_merge_result.merged = True
        mock_merge_result.sha = "abc123"
        mock_merge_result.message = "Merged successfully"
        mock_pr.merge = MagicMock(return_value=mock_merge_result)

        mock_repo.get_pull = MagicMock(return_value=mock_pr)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4996
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="merge_pr",
            repo_name="owner/repo",
            params={
                "number": 42,
                "merge_method": "squash",
                "commit_title": "Merge feature",
            },
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["merged"] is True
        assert result.data["sha"] == "abc123"

    @pytest.mark.asyncio
    async def test_create_branch_success(self, wrapper, mock_repo, context):
        """Test creating branch."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_source_ref = MagicMock()
        mock_source_ref.object.sha = "source-sha"
        mock_repo.get_git_ref = MagicMock(return_value=mock_source_ref)

        mock_new_ref = MagicMock()
        mock_new_ref.object.sha = "new-sha"
        mock_new_ref.url = (
            "https://api.github.com/repos/owner/repo/git/refs/heads/new-branch"
        )
        mock_repo.create_git_ref = MagicMock(return_value=mock_new_ref)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4995
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="create_branch",
            repo_name="owner/repo",
            params={"branch_name": "new-branch", "source_branch": "main"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["branch"] == "new-branch"
        assert result.data["sha"] == "new-sha"

    @pytest.mark.asyncio
    async def test_list_commits_success(self, wrapper, mock_repo, context):
        """Test listing commits."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_commit1 = MagicMock()
        mock_commit1.sha = "commit1"
        mock_commit1.commit.message = "First commit"
        mock_commit1.commit.author.name = "Author 1"
        mock_commit1.commit.author.date = None

        mock_commit2 = MagicMock()
        mock_commit2.sha = "commit2"
        mock_commit2.commit.message = "Second commit"
        mock_commit2.commit.author.name = "Author 2"
        mock_commit2.commit.author.date = None

        mock_repo.get_commits = MagicMock(return_value=[mock_commit1, mock_commit2])

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4994
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="list_commits",
            repo_name="owner/repo",
            params={"sha": "main", "max_results": 5},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["count"] == 2
        assert result.data["commits"][0]["sha"] == "commit1"

    @pytest.mark.asyncio
    async def test_get_file_success(self, wrapper, mock_repo, context):
        """Test getting file content."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_file = MagicMock()
        mock_file.path = "README.md"
        mock_file.decoded_content = b"# README"
        mock_file.sha = "file-sha"
        mock_file.size = 8
        mock_file.encoding = "base64"

        mock_repo.get_contents = MagicMock(return_value=mock_file)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4993
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="get_file",
            repo_name="owner/repo",
            params={"path": "README.md", "ref": "main"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["path"] == "README.md"
        assert result.data["content"] == "# README"

    @pytest.mark.asyncio
    async def test_update_file_success(self, wrapper, mock_repo, context):
        """Test updating file."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_current_file = MagicMock()
        mock_current_file.sha = "old-sha"
        mock_repo.get_contents = MagicMock(return_value=mock_current_file)

        mock_commit = MagicMock()
        mock_commit.sha = "commit-sha"
        mock_commit.commit.message = "Update file"

        mock_new_file = MagicMock()
        mock_new_file.path = "README.md"
        mock_new_file.sha = "new-sha"

        mock_repo.update_file = MagicMock(
            return_value={"commit": mock_commit, "content": mock_new_file}
        )

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4992
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="update_file",
            repo_name="owner/repo",
            params={
                "path": "README.md",
                "content": "# Updated README",
                "message": "Update README",
                "branch": "main",
            },
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["commit"]["sha"] == "commit-sha"
        assert result.data["content"]["sha"] == "new-sha"

    @pytest.mark.asyncio
    async def test_create_issue_success(self, wrapper, mock_repo, context):
        """Test creating issue."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_issue = MagicMock()
        mock_issue.number = 10
        mock_issue.html_url = "https://github.com/owner/repo/issues/10"
        mock_issue.state = "open"
        mock_issue.created_at = None

        mock_repo.create_issue = MagicMock(return_value=mock_issue)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4991
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="create_issue",
            repo_name="owner/repo",
            params={"title": "Bug report", "body": "Found a bug", "labels": ["bug"]},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["number"] == 10

    @pytest.mark.asyncio
    async def test_add_comment_success(self, wrapper, mock_repo, context):
        """Test adding comment."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        mock_issue = MagicMock()
        mock_comment = MagicMock()
        mock_comment.id = 12345
        mock_comment.html_url = "https://github.com/owner/repo/issues/10#comment-12345"
        mock_comment.created_at = None
        mock_issue.create_comment = MagicMock(return_value=mock_comment)

        mock_repo.get_issue = MagicMock(return_value=mock_issue)

        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 4990
        wrapper.client.get_rate_limit = MagicMock(return_value=mock_rate_limit)

        operation = GitHubOperation(
            operation="add_comment",
            repo_name="owner/repo",
            params={"number": 10, "body": "Test comment", "type": "issue"},
        )

        result = await wrapper.execute(operation, context)

        assert result.success is True
        assert result.data["id"] == 12345

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, wrapper, mock_repo, context):
        """Test rate limit exceeded handling."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        rate_limit_exception = RateLimitExceededException(
            status=403,
            data={"message": "API rate limit exceeded"},
            headers={"X-RateLimit-Reset": "1234567890"},
        )
        mock_repo.get_pulls = MagicMock(side_effect=rate_limit_exception)

        operation = GitHubOperation(
            operation="list_prs", repo_name="owner/repo", params={}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Rate limit exceeded" in result.error
        assert result.rate_limit_remaining == 0

    @pytest.mark.asyncio
    async def test_github_api_error(self, wrapper, mock_repo, context):
        """Test GitHub API error handling."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        github_exception = GithubException(
            status=404, data={"message": "Not Found"}, headers={}
        )
        mock_repo.get_pull = MagicMock(side_effect=github_exception)

        operation = GitHubOperation(
            operation="get_pr", repo_name="owner/repo", params={"number": 999}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "GitHub API error" in result.error
        assert "404" in result.error

    @pytest.mark.asyncio
    async def test_invalid_operation(self, wrapper, mock_repo, context):
        """Test invalid operation handling."""
        wrapper.client.get_repo = MagicMock(return_value=mock_repo)

        operation = GitHubOperation(
            operation="invalid_operation", repo_name="owner/repo", params={}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Unknown operation" in result.error

    @pytest.mark.asyncio
    async def test_repository_not_found(self, wrapper, context):
        """Test repository not found handling."""
        github_exception = GithubException(
            status=404, data={"message": "Not Found"}, headers={}
        )
        wrapper.client.get_repo = MagicMock(side_effect=github_exception)

        operation = GitHubOperation(
            operation="list_prs", repo_name="invalid/repo", params={}
        )

        result = await wrapper.execute(operation, context)

        assert result.success is False
        assert "Failed to access repository" in result.error

    def test_close_client(self, wrapper):
        """Test client cleanup."""
        wrapper.close()
        wrapper.client.close.assert_called_once()
