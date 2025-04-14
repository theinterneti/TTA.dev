"""
MCP Server Types for the TTA.dev framework.

This module defines the different types of MCP servers that can be used in the TTA.dev framework.
"""

from enum import Enum, auto


class MCPServerType(Enum):
    """Enum for different types of MCP servers."""

    # Basic development server for testing and learning
    BASIC = auto()

    # Agent tool server for interacting with TTA.dev agents
    AGENT_TOOL = auto()

    # Knowledge resource server for accessing the knowledge graph
    KNOWLEDGE_RESOURCE = auto()

    # Agent-specific server created with the AgentMCPAdapter
    AGENT_ADAPTER = auto()

    def __str__(self):
        """Return a string representation of the server type."""
        return self.name.lower()

    @classmethod
    def from_string(cls, server_type_str: str):
        """
        Create an MCPServerType from a string.

        Args:
            server_type_str: String representation of the server type

        Returns:
            MCPServerType enum value
        """
        try:
            return cls[server_type_str.upper()]
        except KeyError:
            raise ValueError(f"Unknown server type: {server_type_str}")
