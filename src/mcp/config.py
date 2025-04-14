"""
MCP Configuration for the TTA.dev framework.

This module provides configuration utilities for MCP servers in the TTA.dev framework.
"""

import os
import json
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

from .server_types import MCPServerType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPConfig:
    """Configuration for MCP servers."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        default_host: str = "localhost",
        default_port_start: int = 8000
    ):
        """
        Initialize the MCP configuration.

        Args:
            config_path: Path to the configuration file
            default_host: Default host for MCP servers
            default_port_start: Default starting port for MCP servers
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "mcp_config.json"
        )
        self.default_host = default_host
        self.default_port_start = default_port_start
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the configuration file.

        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    return json.load(f)
            else:
                # Create default configuration
                default_config = self._create_default_config()
                self._save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create a default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "servers": {
                str(MCPServerType.BASIC): {
                    "enabled": True,
                    "host": self.default_host,
                    "port": self.default_port_start,
                    "script_path": "examples/mcp/basic_server.py",
                    "dependencies": ["fastmcp", "requests"]
                },
                str(MCPServerType.AGENT_TOOL): {
                    "enabled": True,
                    "host": self.default_host,
                    "port": self.default_port_start + 1,
                    "script_path": "examples/mcp/agent_tool_server.py",
                    "dependencies": ["fastmcp", "requests", "pydantic"]
                },
                str(MCPServerType.KNOWLEDGE_RESOURCE): {
                    "enabled": True,
                    "host": self.default_host,
                    "port": self.default_port_start + 2,
                    "script_path": "examples/mcp/knowledge_resource_server.py",
                    "dependencies": ["fastmcp", "requests", "neo4j"]
                }
            },
            "agent_servers": {}
        }

    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save the configuration to the configuration file.

        Args:
            config: Configuration dictionary
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)

            logger.info(f"Saved MCP configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving MCP configuration: {e}")

    def get_server_config(self, server_type: MCPServerType) -> Dict[str, Any]:
        """
        Get the configuration for a specific server type.

        Args:
            server_type: Type of the server

        Returns:
            Server configuration dictionary
        """
        server_type_str = str(server_type)

        if server_type_str in self.config["servers"]:
            return self.config["servers"][server_type_str]
        else:
            logger.warning(f"No configuration found for server type {server_type_str}")
            return {}

    def get_agent_server_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific agent server.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent server configuration dictionary
        """
        if agent_name in self.config["agent_servers"]:
            return self.config["agent_servers"][agent_name]
        else:
            logger.warning(f"No configuration found for agent server {agent_name}")
            return {}

    def add_agent_server_config(
        self,
        agent_name: str,
        host: str = None,
        port: int = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add configuration for an agent server.

        Args:
            agent_name: Name of the agent
            host: Host for the agent server
            port: Port for the agent server
            enabled: Whether the agent server is enabled

        Returns:
            Updated agent server configuration dictionary
        """
        # Find the next available port if not specified
        if port is None:
            port = self._find_next_available_port()

        # Use default host if not specified
        if host is None:
            host = self.default_host

        # Create agent server configuration
        agent_config = {
            "enabled": enabled,
            "host": host,
            "port": port,
            "dependencies": ["fastmcp", "requests", "neo4j"]
        }

        # Add to configuration
        self.config["agent_servers"][agent_name] = agent_config

        # Save configuration
        self._save_config(self.config)

        return agent_config

    def _find_next_available_port(self) -> int:
        """
        Find the next available port.

        Returns:
            Next available port
        """
        # Get all used ports
        used_ports = []

        # Add ports from server configurations
        for server_config in self.config["servers"].values():
            if "port" in server_config:
                used_ports.append(server_config["port"])

        # Add ports from agent server configurations
        for agent_config in self.config["agent_servers"].values():
            if "port" in agent_config:
                used_ports.append(agent_config["port"])

        # Find the next available port
        next_port = self.default_port_start
        while next_port in used_ports:
            next_port += 1

        return next_port

    def update_server_config(
        self,
        server_type: MCPServerType,
        enabled: Optional[bool] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        script_path: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update the configuration for a specific server type.

        Args:
            server_type: Type of the server
            enabled: Whether the server is enabled
            host: Host for the server
            port: Port for the server
            script_path: Path to the server script
            dependencies: List of dependencies for the server

        Returns:
            Updated server configuration dictionary
        """
        server_type_str = str(server_type)

        # Get current configuration or create a new one
        if server_type_str in self.config["servers"]:
            server_config = self.config["servers"][server_type_str]
        else:
            server_config = {}

        # Update configuration
        if enabled is not None:
            server_config["enabled"] = enabled

        if host is not None:
            server_config["host"] = host

        if port is not None:
            server_config["port"] = port

        if script_path is not None:
            server_config["script_path"] = script_path

        if dependencies is not None:
            server_config["dependencies"] = dependencies

        # Save configuration
        self.config["servers"][server_type_str] = server_config
        self._save_config(self.config)

        return server_config
