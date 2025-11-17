"""Adaptive MCP configuration detection and validation for TTA.dev.

This module provides self-updating MCP configuration workflows that detect
AI agent types, validate setup, and provide actionable suggestions for fixes.

The workflows are designed to adapt to changes in:
- VS Code Copilot MCP configuration format
- Cline MCP configuration format
- New AI coding agents with MCP support
- GitHub MCP API changes
- Context7/Upstash API changes

Example:
    ```python
    from tta_dev_primitives.integrations.mcp_config import (
        MCPConfigurationPrimitive,
        detect_all_mcp_servers
    )

    # Validate all MCP servers
    validator = MCPConfigurationPrimitive()
    result = await validator.execute(None, context)

    if result["all_valid"]:
        print("✅ All MCP servers configured correctly")
    else:
        print("❌ Issues found:")
        for server, issues in result["issues"].items():
            print(f"\n{server}:")
            for suggestion in issues:
                print(f"  - {suggestion}")

    # Auto-detect available servers
    servers = detect_all_mcp_servers()
    print(f"Detected {len(servers)} MCP servers")
    ```
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""

    name: str
    agent_type: Literal["copilot", "cline", "unknown"]
    config_path: Path | None
    is_configured: bool
    requires_auth: bool
    auth_env_var: str | None = None


def detect_all_mcp_servers() -> list[MCPServerInfo]:
    """Detect all configured MCP servers.

    Returns:
        List of detected MCP servers with configuration info
    """
    servers: list[MCPServerInfo] = []

    # Check VS Code Copilot config
    vscode_mcp = Path(".vscode/mcp.json")
    if vscode_mcp.exists():
        try:
            with open(vscode_mcp) as f:
                config = json.load(f)
                mcp_servers = config.get("mcpServers", {})
                for server_name in mcp_servers.keys():
                    servers.append(
                        MCPServerInfo(
                            name=server_name,
                            agent_type="copilot",
                            config_path=vscode_mcp,
                            is_configured=True,
                            requires_auth=_server_requires_auth(server_name),
                            auth_env_var=_get_auth_env_var(server_name),
                        )
                    )
        except (json.JSONDecodeError, KeyError):
            pass

    # Check Cline config
    cline_mcp = Path.home() / ".config" / "cline" / "mcp_settings.json"
    if cline_mcp.exists():
        try:
            with open(cline_mcp) as f:
                config = json.load(f)
                mcp_servers = config.get("mcpServers", {})
                for server_name in mcp_servers.keys():
                    # Don't duplicate if already found in VS Code config
                    if not any(
                        s.name == server_name and s.agent_type == "copilot"
                        for s in servers
                    ):
                        servers.append(
                            MCPServerInfo(
                                name=server_name,
                                agent_type="cline",
                                config_path=cline_mcp,
                                is_configured=True,
                                requires_auth=_server_requires_auth(server_name),
                                auth_env_var=_get_auth_env_var(server_name),
                            )
                        )
        except (json.JSONDecodeError, KeyError):
            pass

    return servers


def _server_requires_auth(server_name: str) -> bool:
    """Check if MCP server requires authentication.

    This is adaptive - add new servers here as they're discovered.
    """
    auth_required_servers = {
        "mcp_github",
        "github",
        "openai",
        "anthropic",
        "google-ai-studio",
    }
    return any(auth in server_name.lower() for auth in auth_required_servers)


def _get_auth_env_var(server_name: str) -> str | None:
    """Get environment variable name for server authentication.

    This is adaptive - add new mappings as servers are discovered.
    """
    auth_mapping = {
        "github": "GITHUB_TOKEN",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google-ai-studio": "GOOGLE_AI_STUDIO_API_KEY",
    }

    for key, env_var in auth_mapping.items():
        if key in server_name.lower():
            return env_var

    return None


class MCPConfigurationPrimitive(WorkflowPrimitive[None, dict[str, Any]]):
    """Validates all MCP server configurations and provides fix suggestions.

    This primitive adapts to:
    - New MCP servers being added
    - Configuration format changes in AI agents
    - New authentication requirements

    Example:
        ```python
        validator = MCPConfigurationPrimitive()
        result = await validator.execute(None, context)

        print(f"Found {result['total_servers']} MCP servers")
        print(f"Valid: {result['valid_servers']}")
        print(f"Invalid: {result['invalid_servers']}")

        if not result["all_valid"]:
            for server, issues in result["issues"].items():
                print(f"\n{server} issues:")
                for issue in issues:
                    print(f"  - {issue}")
        ```
    """

    async def execute(
        self, input_data: None, context: WorkflowContext
    ) -> dict[str, Any]:
        """Validate all MCP configurations.

        Returns:
            Comprehensive validation report
        """
        servers = detect_all_mcp_servers()

        issues: dict[str, list[str]] = {}
        valid_count = 0
        invalid_count = 0

        for server in servers:
            server_issues = []

            # Check authentication if required
            if server.requires_auth and server.auth_env_var:
                import os

                if not os.getenv(server.auth_env_var):
                    server_issues.append(
                        f"Missing {server.auth_env_var}. "
                        f"Set with: export {server.auth_env_var}=your_key_here"
                    )

            # Check config path exists
            if not server.config_path or not server.config_path.exists():
                server_issues.append(
                    f"Configuration file not found: {server.config_path}"
                )

            if server_issues:
                issues[server.name] = server_issues
                invalid_count += 1
            else:
                valid_count += 1

        # Generate setup suggestions if no servers found
        suggestions = []
        if not servers:
            suggestions.append(
                "No MCP servers detected. To set up:\n"
                "  1. For VS Code Copilot: Create .vscode/mcp.json\n"
                "  2. For Cline: Configure via Cline → Settings → MCP Servers\n"
                "  3. See docs/guides/MCP_SETUP_GUIDE.md for templates"
            )

        return {
            "all_valid": len(issues) == 0 and len(servers) > 0,
            "total_servers": len(servers),
            "valid_servers": valid_count,
            "invalid_servers": invalid_count,
            "servers": [
                {
                    "name": s.name,
                    "agent_type": s.agent_type,
                    "config_path": str(s.config_path) if s.config_path else None,
                    "requires_auth": s.requires_auth,
                    "auth_env_var": s.auth_env_var,
                }
                for s in servers
            ],
            "issues": issues,
            "suggestions": suggestions,
        }


class MCPSetupGuidePrimitive(WorkflowPrimitive[dict[str, str], dict[str, Any]]):
    """Generates step-by-step setup guide for specific MCP server.

    This primitive adapts to provide current, accurate setup instructions
    based on detected agent type and server requirements.

    Example:
        ```python
        guide = MCPSetupGuidePrimitive()
        result = await guide.execute(
            {"server": "github", "agent": "copilot"},
            context
        )

        print(result["guide"])
        # Outputs step-by-step instructions
        ```
    """

    async def execute(
        self, input_data: dict[str, str], context: WorkflowContext
    ) -> dict[str, Any]:
        """Generate setup guide for MCP server.

        Args:
            input_data: Dict with 'server' and 'agent' keys

        Returns:
            Setup guide with steps
        """
        server_name = input_data.get("server", "").lower()
        agent_type = input_data.get("agent", "copilot").lower()

        # Adaptive guide generation based on server and agent
        guide_steps = []

        if agent_type == "copilot":
            guide_steps.append("1. Create/edit .vscode/mcp.json in your workspace")
        elif agent_type == "cline":
            guide_steps.append("1. Open Cline → Settings → MCP Servers")
        else:
            guide_steps.append("1. Configure MCP server for your AI agent")

        # Server-specific steps (adaptive)
        if "github" in server_name:
            guide_steps.extend(
                [
                    "2. Add GitHub MCP server configuration:",
                    '   - Server name: "mcp_github"',
                    "   - Command: See MCP_SERVERS.md for current command",
                    "3. Set GITHUB_TOKEN environment variable:",
                    "   - Create token at https://github.com/settings/tokens",
                    "   - export GITHUB_TOKEN=ghp_your_token_here",
                    "   - Add to shell profile (~/.zshrc or ~/.bashrc)",
                    "4. Reload VS Code window to apply changes",
                    "5. Test with: @workspace #tta-mcp-integration list GitHub repos",
                ]
            )
        elif "context7" in server_name or "upstash" in server_name:
            guide_steps.extend(
                [
                    "2. Add Context7 MCP server configuration:",
                    '   - Server name: "mcp_upstash_conte"',
                    "   - Command: See MCP_SERVERS.md for current command",
                    "3. No authentication required (public API)",
                    "4. Reload VS Code window to apply changes",
                    "5. Test with: @workspace #tta-mcp-integration resolve library httpx",
                ]
            )
        else:
            guide_steps.extend(
                [
                    f"2. Add {server_name} MCP server configuration",
                    "3. Check MCP_SERVERS.md for authentication requirements",
                    "4. Reload VS Code window to apply changes",
                ]
            )

        return {
            "server": server_name,
            "agent": agent_type,
            "guide": "\n".join(guide_steps),
            "steps": guide_steps,
        }
