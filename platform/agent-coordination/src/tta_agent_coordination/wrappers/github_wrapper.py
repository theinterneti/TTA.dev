"""
GitHub API Wrapper - L4 Execution Layer.

Production-ready wrapper around PyGithub with:
- Rate limit handling
- Comprehensive error handling
- Type-safe operations
- Observable execution
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from github import Auth, Github, GithubException, RateLimitExceededException
from github.GithubObject import NotSet
from github.PullRequest import PullRequest
from github.Repository import Repository
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


@dataclass
class GitHubConfig:
    """Configuration for GitHub API wrapper."""

    token: str | None = None  # GitHub PAT (defaults to GITHUB_TOKEN env var)
    base_url: str = "https://api.github.com"  # For GitHub Enterprise
    timeout: int = 30  # Request timeout in seconds
    per_page: int = 100  # Pagination size


@dataclass
class GitHubOperation:
    """Input for GitHub operations."""

    operation: str  # "create_pr", "list_prs", "merge_pr", "create_branch", etc.
    repo_name: str  # "owner/repo"
    params: dict[str, Any]  # Operation-specific parameters


@dataclass
class GitHubResult:
    """Output from GitHub operations."""

    success: bool
    operation: str
    data: dict[str, Any] | None = None
    error: str | None = None
    rate_limit_remaining: int | None = None


class GitHubAPIWrapper(WorkflowPrimitive[GitHubOperation, GitHubResult]):
    """
    L4 Execution Wrapper for GitHub API.

    Wraps PyGithub with production-grade error handling, rate limiting,
    and observability.

    Supported Operations:
    - create_pr: Create pull request
    - list_prs: List pull requests
    - get_pr: Get specific pull request
    - merge_pr: Merge pull request
    - create_branch: Create branch
    - list_commits: List commits
    - get_file: Get file content
    - update_file: Update file
    - create_issue: Create issue
    - add_comment: Add PR/issue comment

    Example:
        ```python
        wrapper = GitHubAPIWrapper(config=GitHubConfig(token="ghp_xxx"))

        # Create PR
        operation = GitHubOperation(
            operation="create_pr",
            repo_name="org/repo",
            params={
                "title": "Add feature",
                "body": "Description",
                "head": "feature-branch",
                "base": "main"
            }
        )

        context = WorkflowContext(correlation_id="req-123")
        result = await wrapper.execute(operation, context)
        ```
    """

    def __init__(self, config: GitHubConfig | None = None):
        """
        Initialize GitHub API wrapper.

        Args:
            config: GitHub configuration. If None, uses defaults with GITHUB_TOKEN env var.
        """
        super().__init__()
        self.config = config or GitHubConfig()

        # Get token from config or environment
        token = self.config.token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN env var or pass token in config."
            )

        # Initialize PyGithub client
        auth = Auth.Token(token)
        self.client = Github(
            auth=auth,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            per_page=self.config.per_page,
        )

    async def execute(
        self, input_data: GitHubOperation, context: WorkflowContext
    ) -> GitHubResult:
        """
        Execute GitHub operation.

        Args:
            input_data: Operation to perform
            context: Workflow context for tracing

        Returns:
            Result of operation with rate limit info

        Raises:
            ValueError: Invalid operation or parameters
            GithubException: GitHub API errors
        """
        try:
            # Get repository
            repo = self._get_repository(input_data.repo_name)

            # Dispatch to operation handler
            operation_handlers = {
                "create_pr": self._create_pr,
                "list_prs": self._list_prs,
                "get_pr": self._get_pr,
                "merge_pr": self._merge_pr,
                "create_branch": self._create_branch,
                "list_commits": self._list_commits,
                "get_file": self._get_file,
                "update_file": self._update_file,
                "create_issue": self._create_issue,
                "add_comment": self._add_comment,
            }

            handler = operation_handlers.get(input_data.operation)
            if not handler:
                raise ValueError(
                    f"Unknown operation: {input_data.operation}. "
                    f"Supported: {list(operation_handlers.keys())}"
                )

            # Execute operation
            data = handler(repo, input_data.params)

            # Get rate limit info
            rate_limit = self.client.get_rate_limit()
            remaining = rate_limit.core.remaining  # type: ignore[attr-defined]

            return GitHubResult(
                success=True,
                operation=input_data.operation,
                data=data,
                rate_limit_remaining=remaining,
            )

        except RateLimitExceededException as e:
            reset_time = e.headers.get("X-RateLimit-Reset") if e.headers else "unknown"
            return GitHubResult(
                success=False,
                operation=input_data.operation,
                error=f"Rate limit exceeded. Reset at: {reset_time}",
                rate_limit_remaining=0,
            )

        except GithubException as e:
            return GitHubResult(
                success=False,
                operation=input_data.operation,
                error=f"GitHub API error: {e.status} - {e.data.get('message', str(e))}",
            )

        except Exception as e:
            return GitHubResult(
                success=False,
                operation=input_data.operation,
                error=f"Unexpected error: {type(e).__name__}: {e}",
            )

    def _get_repository(self, repo_name: str) -> Repository:
        """Get repository by name."""
        try:
            return self.client.get_repo(repo_name)
        except GithubException as e:
            raise ValueError(
                f"Failed to access repository '{repo_name}': {e.data.get('message', str(e))}"
            ) from e

    def _create_pr(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Create pull request."""
        required = ["title", "body", "head", "base"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        pr = repo.create_pull(
            title=params["title"],
            body=params["body"],
            head=params["head"],
            base=params["base"],
            draft=params.get("draft", False),
        )

        return {
            "number": pr.number,
            "url": pr.html_url,
            "state": pr.state,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
        }

    def _list_prs(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """List pull requests."""
        state = params.get("state", "open")
        sort = params.get("sort", "created")
        direction = params.get("direction", "desc")

        prs = repo.get_pulls(state=state, sort=sort, direction=direction)

        # Limit results for performance
        max_results = params.get("max_results", 30)
        pr_list = []
        for i, pr in enumerate(prs):
            if i >= max_results:
                break
            pr_list.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "url": pr.html_url,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                }
            )

        return {"prs": pr_list, "count": len(pr_list)}

    def _get_pr(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Get specific pull request."""
        if "number" not in params:
            raise ValueError("Missing required parameter: number")

        pr = repo.get_pull(params["number"])

        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "url": pr.html_url,
            "head": pr.head.ref,
            "base": pr.base.ref,
            "mergeable": pr.mergeable,
            "merged": pr.merged,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        }

    def _merge_pr(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Merge pull request."""
        if "number" not in params:
            raise ValueError("Missing required parameter: number")

        pr: PullRequest = repo.get_pull(params["number"])

        merge_method = params.get("merge_method", "merge")
        commit_title: str | None = params.get("commit_title")
        commit_message: str | None = params.get("commit_message")

        result = pr.merge(
            commit_title=commit_title or NotSet,
            commit_message=commit_message or NotSet,
            merge_method=merge_method,
        )

        return {
            "merged": result.merged,
            "sha": result.sha,
            "message": result.message,
        }

    def _create_branch(
        self, repo: Repository, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Create branch."""
        required = ["branch_name", "source_branch"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Get source branch ref
        source_ref = repo.get_git_ref(f"heads/{params['source_branch']}")
        source_sha = source_ref.object.sha

        # Create new branch
        ref = repo.create_git_ref(
            ref=f"refs/heads/{params['branch_name']}", sha=source_sha
        )

        return {
            "branch": params["branch_name"],
            "sha": ref.object.sha,
            "url": ref.url,
        }

    def _list_commits(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """List commits."""
        sha: str | None = params.get("sha")
        path: str | None = params.get("path")

        commits = repo.get_commits(sha=sha or NotSet, path=path or NotSet)

        # Limit results
        max_results = params.get("max_results", 30)
        commit_list = []
        for i, commit in enumerate(commits):
            if i >= max_results:
                break
            commit_list.append(
                {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name
                    if commit.commit.author
                    else None,
                    "date": commit.commit.author.date.isoformat()
                    if commit.commit.author and commit.commit.author.date
                    else None,
                }
            )

        return {"commits": commit_list, "count": len(commit_list)}

    def _get_file(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Get file content."""
        if "path" not in params:
            raise ValueError("Missing required parameter: path")

        ref = params.get("ref", "main")
        content = repo.get_contents(params["path"], ref=ref)

        if isinstance(content, list):
            raise ValueError(f"Path is a directory: {params['path']}")

        return {
            "path": content.path,
            "content": content.decoded_content.decode("utf-8"),
            "sha": content.sha,
            "size": content.size,
            "encoding": content.encoding,
        }

    def _update_file(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Update file."""
        required = ["path", "content", "message"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Get current file to get SHA
        branch = params.get("branch", "main")
        current_file = repo.get_contents(params["path"], ref=branch)

        if isinstance(current_file, list):
            raise ValueError(f"Path is a directory: {params['path']}")

        result = repo.update_file(
            path=params["path"],
            message=params["message"],
            content=params["content"],
            sha=current_file.sha,
            branch=branch,
        )

        return {
            "commit": {
                "sha": result["commit"].sha,
                "message": result["commit"].commit.message,
            },
            "content": {
                "path": getattr(result["content"], "path", params.get("path", "")),
                "sha": result["content"].sha,
            },
        }

    def _create_issue(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Create issue."""
        required = ["title"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        body: str | None = params.get("body")
        issue = repo.create_issue(
            title=params["title"],
            body=body or NotSet,
            labels=params.get("labels", []),
        )

        return {
            "number": issue.number,
            "url": issue.html_url,
            "state": issue.state,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
        }

    def _add_comment(self, repo: Repository, params: dict[str, Any]) -> dict[str, Any]:
        """Add comment to PR or issue."""
        required = ["number", "body"]
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        comment_type = params.get("type", "issue")  # "issue" or "pr"

        if comment_type == "pr":
            pr = repo.get_pull(params["number"])
            comment = pr.create_issue_comment(params["body"])
        else:
            issue = repo.get_issue(params["number"])
            comment = issue.create_comment(params["body"])

        return {
            "id": comment.id,
            "url": comment.html_url,
            "created_at": comment.created_at.isoformat()
            if comment.created_at
            else None,
        }

    def close(self) -> None:
        """Close GitHub client."""
        if hasattr(self, "client"):
            self.client.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
