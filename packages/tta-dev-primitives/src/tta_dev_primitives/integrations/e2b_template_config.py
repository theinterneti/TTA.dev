"""E2B Template Configuration for PTC (Programmatic Tool Calling).

Provides configuration and utilities for creating custom E2B sandbox templates
that include MCP client capabilities for tool execution.

Features:
- Pre-configured Python environment with MCP dependencies
- Generated server modules for tool access
- MCP client for JSON-RPC communication
- Hypertool persona-based access control

Example:
    ```python
    from tta_dev_primitives.integrations.e2b_template_config import (
        E2BTemplateConfig,
        create_mcp_sandbox_files,
    )

    # Create template config
    config = E2BTemplateConfig(
        template_id="mcp-python-sandbox",
        python_version="3.11",
    )

    # Generate sandbox files for a persona
    files = create_mcp_sandbox_files(
        persona=persona,
        servers=allowed_servers,
    )
    ```
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from tta_dev_primitives.integrations.hypertool_bridge import (
    HypertoolMCPConfig,
    HypertoolPersona,
)
from tta_dev_primitives.integrations.mcp_schema_generator import (
    MCPToolSchema,
    PythonModuleGenerator,
)

logger = logging.getLogger(__name__)


@dataclass
class E2BTemplateConfig:
    """Configuration for E2B sandbox template with MCP support.

    Attributes:
        template_id: E2B template identifier (default uses base Python template).
        python_version: Python version for the sandbox.
        timeout_seconds: Default execution timeout.
        memory_mb: Memory limit in MB.
        cpu_count: Number of CPU cores.
        pip_packages: Additional pip packages to install.
        env_vars: Environment variables to set.
        enable_networking: Whether to allow network access.
    """

    template_id: str = "base"  # E2B base Python template
    python_version: str = "3.11"
    timeout_seconds: int = 60
    memory_mb: int = 512
    cpu_count: int = 1
    pip_packages: list[str] = field(default_factory=lambda: ["aiohttp"])
    env_vars: dict[str, str] = field(default_factory=dict)
    enable_networking: bool = True

    def to_e2b_options(self) -> dict[str, Any]:
        """Convert to E2B sandbox options dict."""
        return {
            "template": self.template_id,
            "timeout": self.timeout_seconds,
            "metadata": {
                "python_version": self.python_version,
                "memory_mb": self.memory_mb,
                "cpu_count": self.cpu_count,
            },
        }


@dataclass
class SandboxFile:
    """Represents a file to be created in the E2B sandbox."""

    path: str
    content: str
    executable: bool = False


def create_mcp_sandbox_files(
    persona: HypertoolPersona,
    servers: dict[str, HypertoolMCPConfig],
    tool_schemas: dict[str, list[MCPToolSchema]] | None = None,
) -> list[SandboxFile]:
    """Create all files needed for MCP execution in E2B sandbox.

    Args:
        persona: Hypertool persona for access control.
        servers: Allowed MCP server configurations.
        tool_schemas: Optional pre-fetched tool schemas per server.

    Returns:
        List of SandboxFile objects to create in sandbox.
    """
    files: list[SandboxFile] = []
    generator = PythonModuleGenerator()

    # Create servers directory structure
    files.append(SandboxFile(path="servers/__init__.py", content='"""MCP Servers."""\n'))

    # Generate server modules if schemas provided
    if tool_schemas:
        for server_name, tools in tool_schemas.items():
            if server_name in servers:
                config = servers[server_name]
                modules = generator.generate_server_modules(server_name, tools, config.description)
                for path, content in modules.items():
                    files.append(SandboxFile(path=path, content=content))

    # Generate MCP client with server configs
    server_configs_dict = {
        name: {
            "command": config.command,
            "args": config.args,
            "env": config.env,
            "url": config.url,
            "transport": config.transport,
        }
        for name, config in servers.items()
    }

    mcp_client_code = generator.generate_mcp_client_module(server_configs_dict)
    # Inject actual server configs
    mcp_client_code = mcp_client_code.replace(
        "SERVER_CONFIGS: dict[str, dict[str, Any]] = {}",
        f"SERVER_CONFIGS: dict[str, dict[str, Any]] = {repr(server_configs_dict)}",
    )
    files.append(SandboxFile(path="mcp_client.py", content=mcp_client_code))

    # Create persona info file for debugging/logging
    persona_info = f'''"""Persona: {persona.name}

Display Name: {persona.display_name}
Description: {persona.description}
Allowed Servers: {persona.allowed_servers}
Token Budget: {persona.token_budget}
"""

PERSONA_NAME = "{persona.name}"
ALLOWED_SERVERS = {persona.allowed_servers}
'''
    files.append(SandboxFile(path="persona_info.py", content=persona_info))

    logger.info(
        f"Created {len(files)} sandbox files for persona '{persona.name}' "
        f"with {len(servers)} servers"
    )

    return files


# Export classes
__all__ = [
    "E2BTemplateConfig",
    "SandboxFile",
    "create_mcp_sandbox_files",
]
