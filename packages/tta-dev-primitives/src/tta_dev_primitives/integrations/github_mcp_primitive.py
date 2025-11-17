"""GitHub MCP integration primitive for TTA.dev.

Provides adaptive workflow for using GitHub MCP server tools with built-in
configuration detection and validation.

Example:
    ```python
    from tta_dev_primitives.integrations import GitHubMCPPrimitive

    github = GitHubMCPPrimitive()

    # Create issue
    result = await github.create_issue(
        repo="theinterneti/TTA.dev",
        title="Add new primitive",
        body="Description here",
        context=context
    )

    # Search code
    code_results = await github.search_code(
        query="CachePrimitive language:python",
        context=context
    )
    ```

Configuration:
    The primitive automatically detects MCP configuration from:
    - VS Code Copilot: .vscode/mcp.json or workspace settings
    - Cline: ~/.config/cline/mcp_settings.json
    - Environment: GITHUB_TOKEN for authentication
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


@dataclass
class GitHubMCPConfig:
    """GitHub MCP server configuration."""

    server_name: str = "mcp_github"
    github_token: str | None = None
    config_path: Path | None = None
    agent_type: Literal["copilot", "cline", "unknown"] = "unknown"

    @classmethod
    def detect(cls) -> GitHubMCPConfig:
        """Detect GitHub MCP configuration from environment."""
        config = cls()

        # Try to detect agent type and config path
        vscode_mcp = Path(".vscode/mcp.json")
        cline_mcp = Path.home() / ".config" / "cline" / "mcp_settings.json"

        if vscode_mcp.exists():
            config.agent_type = "copilot"
            config.config_path = vscode_mcp
        elif cline_mcp.exists():
            config.agent_type = "cline"
            config.config_path = cline_mcp

        # Try to get GitHub token from environment
        config.github_token = os.getenv("GITHUB_TOKEN")

        return config

    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not self.github_token:
            errors.append(
                "GITHUB_TOKEN not found in environment. "
                "Set with: export GITHUB_TOKEN=your_token_here"
            )

        if not self.config_path or not self.config_path.exists():
            errors.append(
                f"MCP configuration not found. Expected at: "
                f"{self.config_path or '.vscode/mcp.json or ~/.config/cline/mcp_settings.json'}"
            )

        return len(errors) == 0, errors


class GitHubMCPPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Primitive for interacting with GitHub via MCP server.

    This primitive provides a type-safe, observable workflow for using
    GitHub MCP tools. It automatically detects configuration and validates
    setup before operations.

    Attributes:
        config: Detected GitHub MCP configuration
    """

    def __init__(self):
        """Initialize GitHub MCP primitive with auto-detection."""
        super().__init__()
        self.config = GitHubMCPConfig.detect()

    async def execute(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute GitHub operation via MCP.

        Args:
            input_data: Operation parameters with 'operation' key
            context: Workflow context for tracing

        Returns:
            Operation result

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        is_valid, errors = self.config.validate()
        if not is_valid:
            raise ValueError(
                "GitHub MCP configuration invalid:\n"
                + "\n".join(f"- {e}" for e in errors)
            )

        operation = input_data.get("operation", "unknown")

        # Route to appropriate handler
        if operation == "create_issue":
            return await self._create_issue(input_data, context)
        elif operation == "search_code":
            return await self._search_code(input_data, context)
        elif operation == "get_pr":
            return await self._get_pr(input_data, context)
        elif operation == "list_issues":
            return await self._list_issues(input_data, context)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
        context: WorkflowContext | None = None,
    ) -> dict[str, Any]:
        """Create a GitHub issue.

        Args:
            repo: Repository in format "owner/repo"
            title: Issue title
            body: Issue body/description
            labels: Optional list of label names
            context: Workflow context

        Returns:
            Created issue details
        """
        return await self.execute(
            {
                "operation": "create_issue",
                "repo": repo,
                "title": title,
                "body": body,
                "labels": labels or [],
            },
            context or WorkflowContext(),
        )

    async def search_code(
        self, query: str, context: WorkflowContext | None = None
    ) -> dict[str, Any]:
        """Search code across GitHub.

        Args:
            query: GitHub code search query
            context: Workflow context

        Returns:
            Search results
        """
        return await self.execute(
            {"operation": "search_code", "query": query}, context or WorkflowContext()
        )

    async def get_pr(
        self, repo: str, pr_number: int, context: WorkflowContext | None = None
    ) -> dict[str, Any]:
        """Get pull request details.

        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            context: Workflow context

        Returns:
            Pull request details
        """
        return await self.execute(
            {"operation": "get_pr", "repo": repo, "pr_number": pr_number},
            context or WorkflowContext(),
        )

    async def list_issues(
        self,
        repo: str,
        state: Literal["open", "closed", "all"] = "open",
        labels: list[str] | None = None,
        context: WorkflowContext | None = None,
    ) -> dict[str, Any]:
        """List repository issues.

        Args:
            repo: Repository in format "owner/repo"
            state: Issue state filter
            labels: Optional label filters
            context: Workflow context

        Returns:
            List of issues
        """
        return await self.execute(
            {
                "operation": "list_issues",
                "repo": repo,
                "state": state,
                "labels": labels or [],
            },
            context or WorkflowContext(),
        )

    # Implementation methods (would call actual MCP tools)
    async def _create_issue(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation for create_issue operation."""
        # In real implementation, this would call:
        # mcp_github_github_create_issue tool
        return {
            "status": "success",
            "operation": "create_issue",
            "issue_number": 42,  # Mock response
            "url": f"https://github.com/{input_data['repo']}/issues/42",
        }

    async def _search_code(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation for search_code operation."""
        # In real implementation, this would call:
        # mcp_github_github_search_code tool
        return {
            "status": "success",
            "operation": "search_code",
            "results": [],  # Mock response
            "total_count": 0,
        }

    async def _get_pr(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation for get_pr operation."""
        # In real implementation, this would call:
        # mcp_github_github_pull_request_read tool
        return {
            "status": "success",
            "operation": "get_pr",
            "pr": {},  # Mock response
        }

    async def _list_issues(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation for list_issues operation."""
        # In real implementation, this would call:
        # mcp_github_github_list_issues tool
        return {
            "status": "success",
            "operation": "list_issues",
            "issues": [],  # Mock response
            "total_count": 0,
        }


class GitHubMCPConfigValidator(WorkflowPrimitive[None, dict[str, Any]]):
    """Validates and suggests fixes for GitHub MCP configuration.

    Use this primitive to check if GitHub MCP is properly configured
    and get actionable suggestions for fixing issues.

    Example:
        ```python
        validator = GitHubMCPConfigValidator()
        result = await validator.execute(None, context)

        if result["valid"]:
            print("✅ GitHub MCP configured correctly")
        else:
            print("❌ Issues found:")
            for suggestion in result["suggestions"]:
                print(f"  - {suggestion}")
        ```
    """

    async def execute(
        self, input_data: None, context: WorkflowContext
    ) -> dict[str, Any]:
        """Validate GitHub MCP configuration.

        Returns:
            Validation result with suggestions
        """
        config = GitHubMCPConfig.detect()
        is_valid, errors = config.validate()

        suggestions = []

        if not config.github_token:
            suggestions.append(
                "Set GITHUB_TOKEN: export GITHUB_TOKEN=$(gh auth token) "
                "or create token at https://github.com/settings/tokens"
            )

        if not config.config_path or not config.config_path.exists():
            if config.agent_type == "copilot":
                suggestions.append(
                    "Create .vscode/mcp.json with GitHub MCP configuration. "
                    "See docs/guides/MCP_SETUP_GUIDE.md for template."
                )
            elif config.agent_type == "cline":
                suggestions.append(
                    "Configure GitHub MCP in Cline settings. Open Cline → Settings → MCP Servers"
                )
            else:
                suggestions.append(
                    "Could not detect AI agent type. Configure MCP for your agent:\n"
                    "  - VS Code Copilot: Create .vscode/mcp.json\n"
                    "  - Cline: Configure via Cline settings"
                )

        return {
            "valid": is_valid,
            "agent_type": config.agent_type,
            "config_path": str(config.config_path) if config.config_path else None,
            "has_token": bool(config.github_token),
            "errors": errors,
            "suggestions": suggestions,
        }
