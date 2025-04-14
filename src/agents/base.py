"""
Base Agent for the TTA.dev Framework.

This module provides the base agent class for all agents in the TTA.dev framework.
It is designed to be a reusable component that can be extended for various agent types.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents in the TTA.dev framework.

    This class provides the foundation for building agents that can be used
    with the TTA.dev framework. It includes support for tools, database integration,
    and MCP server creation.
    """

    def __init__(
        self,
        name: str,
        description: str,
        database_manager=None,
        tools: Dict[str, Callable] = None,
        system_prompt: str = None
    ):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            description: Description of the agent
            database_manager: Database manager for knowledge operations
            tools: Dictionary of tools available to the agent
            system_prompt: System prompt for the agent
        """
        self.name = name
        self.description = description
        self.database_manager = database_manager
        self.tools = tools or {}
        self.system_prompt = system_prompt or f"You are {name}, {description}."

        logger.info(f"Initialized {name} agent")

    def process(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input data and return a response.

        Args:
            input_data: Input data to process
            context: Additional context information

        Returns:
            The result of processing the input data
        """
        # This is a placeholder method that should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement process method")

    def add_tool(self, name: str, tool: Callable) -> None:
        """
        Add a tool to the agent.

        Args:
            name: Name of the tool
            tool: Tool function
        """
        self.tools[name] = tool
        logger.info(f"Added tool {name} to {self.name} agent")

    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool from the agent.

        Args:
            name: Name of the tool

        Returns:
            True if the tool was removed, False otherwise
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Removed tool {name} from {self.name} agent")
            return True
        return False

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Get a list of available tools.

        Returns:
            List of available tools with name and description
        """
        return [
            {
                "name": name,
                "description": getattr(tool, "__doc__", "No description")
            }
            for name, tool in self.tools.items()
        ]

    def update_system_prompt(self, system_prompt: str) -> None:
        """
        Update the system prompt.

        Args:
            system_prompt: New system prompt
        """
        self.system_prompt = system_prompt
        logger.info(f"Updated system prompt for {self.name} agent")

    def __str__(self) -> str:
        """Return a string representation of the agent."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Return a string representation of the agent."""
        return f"Agent(name='{self.name}', description='{self.description}', tools={list(self.tools.keys())})"

    def to_json(self) -> str:
        """
        Convert this agent to a JSON string.

        Returns:
            JSON string representation of the agent
        """
        return json.dumps(self.get_info(), indent=2)

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.

        Returns:
            Dictionary with agent information
        """
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.get_available_tools(),
            "system_prompt": self.system_prompt
        }

    def to_mcp_server(self, server_name: Optional[str] = None, server_description: Optional[str] = None):
        """
        Convert this agent to an MCP server.

        Args:
            server_name: Name for the MCP server (defaults to agent.name + " MCP Server")
            server_description: Description for the MCP server

        Returns:
            An AgentMCPAdapter instance
        """
        # Import here to avoid circular imports
        from ..mcp import create_agent_mcp_server

        return create_agent_mcp_server(
            agent=self,
            server_name=server_name,
            server_description=server_description
        )
