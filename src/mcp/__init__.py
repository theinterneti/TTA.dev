"""
MCP package for the TTA.dev framework.

This package provides MCP (Model Context Protocol) server implementations
and utilities for integrating AI agents with external systems.
"""

from .agent_adapter import AgentMCPAdapter, create_agent_mcp_server
from .server_types import MCPServerType
from .config import MCPConfig
from .server_manager import MCPServerManager

__all__ = [
    'AgentMCPAdapter',
    'create_agent_mcp_server',
    'MCPServerType',
    'MCPConfig',
    'MCPServerManager'
]
