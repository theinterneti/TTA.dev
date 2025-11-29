#!/usr/bin/env python3
"""
MCP Configuration Parser - Extract MCP server definitions from various sources.

This script parses MCP configurations from:
- .hypertool/mcp_servers.json (Hypertool format)
- Remote repositories (GitHub MCP registries)
- Docker containers (container-based MCP servers)
- NPX packages (npm-based MCP servers)

Output formats:
- VS Code Copilot format (~/.config/mcp/mcp_settings.json)
- Cline format (shared with VS Code)
- Hypertool format (.hypertool/mcp_servers.json)
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class MCPConfigParser:
    """Parse and convert MCP server configurations between formats."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.hypertool_config = workspace_root / ".hypertool" / "mcp_servers.json"
        self.vscode_mcp_config = Path.home() / ".config" / "mcp" / "mcp_settings.json"

    def parse_hypertool_config(self) -> dict[str, Any]:
        """Parse .hypertool/mcp_servers.json format."""
        if not self.hypertool_config.exists():
            return {"mcpServers": {}}

        with open(self.hypertool_config) as f:
            config = json.load(f)

        return config.get("mcpServers", {})

    def parse_repo_uri(self, repo_uri: str) -> dict[str, Any] | None:
        """
        Parse repository URI and extract MCP configuration.

        Supports:
        - GitHub repos: https://github.com/owner/repo
        - GitMCP: https://gitmcp.io/owner/repo
        - NPM packages: npm:package-name
        - Docker images: docker:image-name
        """
        # GitMCP format
        try:
            parsed = urlparse(repo_uri)
            host = parsed.hostname
        except Exception:
            host = None
        if host and (host == "gitmcp.io" or host.endswith(".gitmcp.io")):
            # Extract owner/repo from URL
            match = re.search(r"gitmcp\.io/([^/]+/[^/]+)", repo_uri)
            if match:
                return {
                    "url": repo_uri,
                    "description": f"GitMCP repository: {match.group(1)}",
                    "tags": ["vcs", "repository"],
                }

        # GitHub repository
        if "github.com" in repo_uri:
            parsed = urlparse(repo_uri)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                # Check for MCP server in repo
                # This would require API call or clone - simplified for now
                return {
                    "command": "/usr/bin/npx",
                    "args": ["-y", f"@{owner}/{repo}"],
                    "description": f"MCP server from {owner}/{repo}",
                    "tags": ["github", "custom"],
                }

        # NPM package
        if repo_uri.startswith("npm:"):
            package = repo_uri[4:]
            return {
                "command": "/usr/bin/npx",
                "args": ["-y", package],
                "description": f"NPM package: {package}",
                "tags": ["npm"],
            }

        # Docker image
        if repo_uri.startswith("docker:"):
            image = repo_uri[7:]
            return {
                "command": "/usr/bin/docker",
                "args": ["run", "--rm", "-i", image],
                "description": f"Docker image: {image}",
                "tags": ["docker"],
            }

        return None

    def convert_to_vscode_format(self, servers: dict[str, Any]) -> dict[str, Any]:
        """
        Convert MCP server definitions to VS Code Copilot format.

        Input: Hypertool format
        Output: ~/.config/mcp/mcp_settings.json format
        """
        vscode_config = {"mcpServers": {}}

        for name, config in servers.items():
            # Copy base configuration
            server_config = {
                "command": config.get("command"),
                "args": config.get("args", []),
            }

            # Add environment variables if present
            if "env" in config:
                server_config["env"] = config["env"]

            # Add metadata as comments (VS Code supports this)
            if "description" in config:
                server_config["__description"] = config["description"]

            vscode_config["mcpServers"][name] = server_config

        return vscode_config

    def convert_to_cline_format(self, servers: dict[str, Any]) -> dict[str, Any]:
        """
        Convert to Cline format (currently same as VS Code).

        Cline uses the same ~/.config/mcp/mcp_settings.json as VS Code,
        but may have additional preferences.
        """
        cline_config = self.convert_to_vscode_format(servers)

        # Add Cline-specific preferences
        cline_config["cline"] = {
            "preferredServers": self._get_preferred_servers(servers),
            "autoConnect": True,
            "maxConcurrentConnections": 3,
        }

        return cline_config

    def _get_preferred_servers(self, servers: dict[str, Any]) -> list[str]:
        """Determine preferred servers based on tags."""
        preferred = []

        # Priority order based on tags
        priority_tags = [
            "documentation",
            "reasoning",
            "code-analysis",
            "vcs",
        ]

        for tag in priority_tags:
            for name, config in servers.items():
                if tag in config.get("tags", []):
                    if name not in preferred:
                        preferred.append(name)

        return preferred[:3]  # Top 3 preferred servers

    def generate_configs(
        self, output_vscode: bool = True, output_cline: bool = True
    ) -> None:
        """Generate configuration files for agents."""
        # Parse Hypertool configuration
        servers = self.parse_hypertool_config()

        if not servers:
            print("⚠️  No MCP servers found in .hypertool/mcp_servers.json")
            return

        print(f"✅ Found {len(servers)} MCP servers")

        # Generate VS Code configuration
        if output_vscode:
            vscode_config = self.convert_to_vscode_format(servers)
            self._write_vscode_config(vscode_config)

        # Generate Cline configuration
        if output_cline:
            cline_config = self.convert_to_cline_format(servers)
            self._write_cline_config(cline_config)

    def _write_vscode_config(self, config: dict[str, Any]) -> None:
        """Write VS Code MCP configuration."""
        config_dir = self.vscode_mcp_config.parent
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.vscode_mcp_config, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ VS Code config written to: {self.vscode_mcp_config}")

    def _write_cline_config(self, config: dict[str, Any]) -> None:
        """Write Cline MCP configuration (currently same location as VS Code)."""
        # Cline uses the same file as VS Code
        self._write_vscode_config(config)
        print("✅ Cline config shares VS Code configuration")

    def add_repo_uri(self, repo_uri: str, name: str | None = None) -> None:
        """Add MCP server from repository URI."""
        server_config = self.parse_repo_uri(repo_uri)

        if not server_config:
            print(f"❌ Could not parse repository URI: {repo_uri}")
            return

        # Load existing Hypertool config
        if self.hypertool_config.exists():
            with open(self.hypertool_config) as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}

        # Generate name if not provided
        if not name:
            if "gitmcp.io" in repo_uri:
                name = repo_uri.split("/")[-1]
            elif "github.com" in repo_uri:
                name = repo_uri.split("/")[-1]
            elif repo_uri.startswith("npm:"):
                name = repo_uri[4:].replace("@", "").replace("/", "-")
            elif repo_uri.startswith("docker:"):
                name = repo_uri[7:].replace("/", "-")
            else:
                name = "custom-server"

        # Add to config
        config["mcpServers"][name] = server_config

        # Write back to Hypertool config
        self.hypertool_config.parent.mkdir(parents=True, exist_ok=True)
        with open(self.hypertool_config, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ Added '{name}' to {self.hypertool_config}")

        # Regenerate agent configs
        self.generate_configs()


def main():
    """CLI interface for MCP configuration parser."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse and convert MCP server configurations"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root directory",
    )
    parser.add_argument(
        "--add-repo",
        type=str,
        help="Add MCP server from repository URI",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Name for the MCP server (auto-generated if not provided)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate agent configuration files",
    )
    parser.add_argument(
        "--vscode-only",
        action="store_true",
        help="Generate only VS Code configuration",
    )
    parser.add_argument(
        "--cline-only",
        action="store_true",
        help="Generate only Cline configuration",
    )

    args = parser.parse_args()

    config_parser = MCPConfigParser(args.workspace)

    if args.add_repo:
        config_parser.add_repo_uri(args.add_repo, args.name)
    elif args.generate:
        output_vscode = not args.cline_only
        output_cline = not args.vscode_only
        config_parser.generate_configs(
            output_vscode=output_vscode, output_cline=output_cline
        )
    else:
        # Default: parse and display current configuration
        servers = config_parser.parse_hypertool_config()
        print(json.dumps({"mcpServers": servers}, indent=2))


if __name__ == "__main__":
    main()
