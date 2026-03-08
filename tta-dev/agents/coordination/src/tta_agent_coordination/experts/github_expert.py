"""
GitHubExpert - L3 Tool Expertise Layer.

Production-ready GitHub operations with:
- Automatic retry with exponential backoff (rate limiting)
- Response caching for GET operations
- GitHub best practices enforcement
- Intelligent error recovery
- Observable execution
"""

from __future__ import annotations

from dataclasses import dataclass

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

from tta_agent_coordination.wrappers.github_wrapper import (
    GitHubAPIWrapper,
    GitHubConfig,
    GitHubOperation,
    GitHubResult,
)


@dataclass
class GitHubExpertConfig:
    """Configuration for GitHubExpert."""

    # GitHub API configuration
    github_config: GitHubConfig | None = None

    # Retry configuration
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    jitter: bool = True

    # Cache configuration
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    cache_max_size: int = 1000

    # Operation limits
    max_pr_body_length: int = 65536  # 64KB
    max_commit_message_length: int = 5000


class GitHubExpert(WorkflowPrimitive[GitHubOperation, GitHubResult]):
    """
    L3 Tool Expertise Layer for GitHub operations.

    Wraps GitHubAPIWrapper (L4) with:
    - Automatic retry for rate limiting and transient errors
    - Response caching for GET operations (PRs, files, commits)
    - GitHub best practices validation
    - Intelligent error recovery

    Example:
        ```python
        from tta_dev_primitives import WorkflowContext

        # Create expert with automatic retry and caching
        expert = GitHubExpert(
            config=GitHubExpertConfig(
                max_retries=3,
                cache_enabled=True,
                cache_ttl=300
            )
        )

        # Create PR with automatic retry on rate limits
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
        result = await expert.execute(operation, context)
        # Automatically retries on rate limit errors
        # Returns cached results for repeated GET operations
        ```

    Operations with automatic retry:
    - All operations retry on: rate_limit_exceeded, timeout, connection_error
    - GET operations (list_prs, get_pr, get_file, list_commits) are cached

    Best Practices Enforced:
    - PR descriptions must be non-empty
    - PR body length limits (64KB)
    - Commit message length limits (5KB)
    - Branch naming validation
    """

    def __init__(self, config: GitHubExpertConfig | None = None):
        """
        Initialize GitHub expert with retry and caching.

        Args:
            config: Expert configuration. If None, uses defaults.
        """
        super().__init__()
        self.config = config or GitHubExpertConfig()

        # Create L4 wrapper
        self._wrapper = GitHubAPIWrapper(config=self.config.github_config)

        # Wrap with retry primitive for rate limiting
        from tta_dev_primitives.recovery.retry import RetryStrategy

        retry_strategy = RetryStrategy(
            max_retries=self.config.max_retries,
            backoff_base=self.config.backoff_factor,
            jitter=self.config.jitter,
        )
        self._with_retry = RetryPrimitive(
            primitive=self._wrapper,
            strategy=retry_strategy,
        )

        # Wrap cacheable operations with cache primitive
        if self.config.cache_enabled:
            self._with_cache = CachePrimitive(
                primitive=self._with_retry,
                cache_key_fn=self._cache_key,
                ttl_seconds=self.config.cache_ttl,
            )
        else:
            self._with_cache = self._with_retry

        # Operations that benefit from caching (GET operations)
        self._cacheable_operations = {
            "list_prs",
            "get_pr",
            "get_file",
            "list_commits",
        }

    def _cache_key(self, operation: GitHubOperation, context: WorkflowContext) -> str:
        """
        Generate cache key for operation.

        Args:
            operation: GitHub operation
            context: Workflow context

        Returns:
            Cache key string
        """
        # Include operation type, repo, and key params
        parts = [operation.operation, operation.repo_name]

        # Add relevant params to key
        if operation.operation == "get_pr":
            parts.append(str(operation.params.get("pr_number")))
        elif operation.operation == "get_file":
            parts.append(operation.params.get("path", ""))
            parts.append(operation.params.get("ref", "main"))
        elif operation.operation == "list_prs":
            parts.append(operation.params.get("state", "open"))
        elif operation.operation == "list_commits":
            parts.append(operation.params.get("sha", "main"))

        return ":".join(parts)

    def _validate_operation(self, operation: GitHubOperation) -> dict[str, str] | None:
        """
        Validate operation follows GitHub best practices.

        Args:
            operation: Operation to validate

        Returns:
            None if valid, error dict if validation fails
        """
        # Validate PR operations
        if operation.operation == "create_pr":
            # Check required fields
            title = operation.params.get("title", "").strip()
            if not title:
                return {"error": "PR title cannot be empty"}

            body = operation.params.get("body", "")
            if not body.strip():
                return {"error": "PR body should include description"}

            # Check length limits
            if len(body) > self.config.max_pr_body_length:
                return {
                    "error": f"PR body exceeds {self.config.max_pr_body_length} chars"
                }

            # Validate branch names
            head = operation.params.get("head", "")
            if not head:
                return {"error": "Head branch is required"}

            base = operation.params.get("base", "")
            if not base:
                return {"error": "Base branch is required"}

            if head == base:
                return {"error": "Head and base branches cannot be the same"}

        # Validate commit operations
        elif operation.operation == "update_file":
            message = operation.params.get("message", "")
            if not message.strip():
                return {"error": "Commit message cannot be empty"}

            if len(message) > self.config.max_commit_message_length:
                max_len = self.config.max_commit_message_length
                return {"error": f"Commit message exceeds {max_len} chars"}

        # Validate issue operations
        elif operation.operation == "create_issue":
            title = operation.params.get("title", "").strip()
            if not title:
                return {"error": "Issue title cannot be empty"}

        return None

    def _should_cache(self, operation: GitHubOperation) -> bool:
        """
        Determine if operation should use cache.

        Args:
            operation: GitHub operation

        Returns:
            True if operation should be cached
        """
        return (
            self.config.cache_enabled
            and operation.operation in self._cacheable_operations
        )

    async def execute(
        self, input_data: GitHubOperation, context: WorkflowContext
    ) -> GitHubResult:
        """
        Execute GitHub operation with retry, caching, and validation.

        Args:
            input_data: GitHub operation to execute
            context: Workflow context for tracing

        Returns:
            Operation result with automatic retry and caching applied
        """
        # Validate operation follows best practices
        if validation_error := self._validate_operation(input_data):
            return GitHubResult(
                success=False,
                operation=input_data.operation,
                data={"repo_name": input_data.repo_name, "validation_failed": True},
                error=validation_error["error"],
            )

        # Choose execution path based on caching
        if self._should_cache(input_data):
            # Use cached + retry path for GET operations
            result = await self._with_cache.execute(input_data, context)
        else:
            # Use retry-only path for mutating operations
            result = await self._with_retry.execute(input_data, context)

        return result

    def close(self) -> None:
        """Close the underlying GitHub client."""
        self._wrapper.close()
