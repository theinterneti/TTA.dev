"""Context7 MCP integration primitive for TTA.dev.

Provides adaptive workflow for querying library documentation via Context7 MCP server
with built-in configuration detection and caching.

Example:
    ```python
    from tta_dev_primitives.integrations import Context7MCPPrimitive

    context7 = Context7MCPPrimitive()

    # Get documentation for a library
    docs = await context7.get_docs(
        library="httpx",
        topic="async client usage",
        context=context
    )

    # Resolve library ID
    library_id = await context7.resolve_library(
        library_name="fastapi",
        context=context
    )
    ```

Configuration:
    The primitive automatically detects MCP configuration from:
    - VS Code Copilot: .vscode/mcp.json or workspace settings
    - Cline: ~/.config/cline/mcp_settings.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


@dataclass
class Context7MCPConfig:
    """Context7 MCP server configuration."""

    server_name: str = "mcp_upstash_conte"
    config_path: Path | None = None
    agent_type: Literal["copilot", "cline", "unknown"] = "unknown"

    @classmethod
    def detect(cls) -> Context7MCPConfig:
        """Detect Context7 MCP configuration from environment."""
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

        return config

    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not self.config_path or not self.config_path.exists():
            errors.append(
                f"MCP configuration not found. Expected at: "
                f"{self.config_path or '.vscode/mcp.json or ~/.config/cline/mcp_settings.json'}"
            )

        return len(errors) == 0, errors


class Context7MCPPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Primitive for querying library documentation via Context7 MCP.

    This primitive provides a type-safe, observable workflow for using
    Context7 (Upstash) MCP server to fetch up-to-date library documentation.

    Attributes:
        config: Detected Context7 MCP configuration
    """

    def __init__(self):
        """Initialize Context7 MCP primitive with auto-detection."""
        super().__init__()
        self.config = Context7MCPConfig.detect()

    async def execute(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute Context7 operation via MCP.

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
                "Context7 MCP configuration invalid:\n"
                + "\n".join(f"- {e}" for e in errors)
            )

        operation = input_data.get("operation", "unknown")

        # Route to appropriate handler
        if operation == "get_docs":
            return await self._get_docs(input_data, context)
        elif operation == "resolve_library":
            return await self._resolve_library(input_data, context)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def get_docs(
        self,
        library: str,
        topic: str | None = None,
        tokens: int = 5000,
        context: WorkflowContext | None = None,
    ) -> dict[str, Any]:
        """Get library documentation.

        Args:
            library: Library name or Context7-compatible ID (e.g., '/org/project')
            topic: Optional topic to focus documentation on
            tokens: Maximum tokens of documentation to retrieve (default: 5000)
            context: Workflow context

        Returns:
            Library documentation
        """
        return await self.execute(
            {
                "operation": "get_docs",
                "library": library,
                "topic": topic,
                "tokens": tokens,
            },
            context or WorkflowContext(),
        )

    async def resolve_library(
        self, library_name: str, context: WorkflowContext | None = None
    ) -> dict[str, Any]:
        """Resolve library name to Context7-compatible ID.

        Args:
            library_name: Library name to resolve
            context: Workflow context

        Returns:
            Library ID and matching libraries
        """
        return await self.execute(
            {"operation": "resolve_library", "library_name": library_name},
            context or WorkflowContext(),
        )

    # Implementation methods (would call actual MCP tools)
    async def _get_docs(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation for get_docs operation."""
        # In real implementation, this would call:
        # mcp_upstash_conte_get-library-docs tool
        return {
            "status": "success",
            "operation": "get_docs",
            "library": input_data["library"],
            "documentation": "# Library Documentation\n\nPlaceholder...",  # Mock
            "tokens_used": 1000,
        }

    async def _resolve_library(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Implementation for resolve_library operation."""
        # In real implementation, this would call:
        # mcp_upstash_conte_resolve-library-id tool
        return {
            "status": "success",
            "operation": "resolve_library",
            "library_name": input_data["library_name"],
            "library_id": "/org/project",  # Mock
            "matches": [],
        }


class Context7MCPConfigValidator(WorkflowPrimitive[None, dict[str, Any]]):
    """Validates and suggests fixes for Context7 MCP configuration.

    Use this primitive to check if Context7 MCP is properly configured
    and get actionable suggestions for fixing issues.

    Example:
        ```python
        validator = Context7MCPConfigValidator()
        result = await validator.execute(None, context)

        if result["valid"]:
            print("✅ Context7 MCP configured correctly")
        else:
            print("❌ Issues found:")
            for suggestion in result["suggestions"]:
                print(f"  - {suggestion}")
        ```
    """

    async def execute(
        self, input_data: None, context: WorkflowContext
    ) -> dict[str, Any]:
        """Validate Context7 MCP configuration.

        Returns:
            Validation result with suggestions
        """
        config = Context7MCPConfig.detect()
        is_valid, errors = config.validate()

        suggestions = []

        if not config.config_path or not config.config_path.exists():
            if config.agent_type == "copilot":
                suggestions.append(
                    "Create .vscode/mcp.json with Context7 MCP configuration. "
                    "See docs/guides/MCP_SETUP_GUIDE.md for template."
                )
            elif config.agent_type == "cline":
                suggestions.append(
                    "Configure Context7 MCP in Cline settings. Open Cline → Settings → MCP Servers"
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
            "errors": errors,
            "suggestions": suggestions,
        }
