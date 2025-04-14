"""
Agent to MCP Adapter

This module provides an adapter that allows TTA.dev agents to be exposed as MCP servers.
It converts agent methods and capabilities into MCP tools and resources.
"""

from fastmcp import FastMCP, Context
from typing import Dict, List, Any, Optional, Type, Callable
import inspect
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentMCPAdapter:
    """
    Adapter that converts a TTA.dev agent into an MCP server.

    This adapter takes a TTA.dev agent and exposes its methods and capabilities
    as MCP tools and resources.
    """

    def __init__(
        self,
        agent,
        server_name: Optional[str] = None,
        server_description: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ):
        """
        Initialize the adapter.

        Args:
            agent: The agent to adapt
            server_name: Name for the MCP server (defaults to agent.name + " MCP Server")
            server_description: Description for the MCP server
            dependencies: List of dependencies for the MCP server
        """
        self.agent = agent

        # Set server name and description
        self.server_name = server_name or f"{agent.name} MCP Server"
        self.server_description = server_description or f"MCP server for {agent.name}"

        # Set dependencies
        self.dependencies = dependencies or ["fastmcp"]

        # Create the MCP server
        self.mcp = FastMCP(
            self.server_name,
            description=self.server_description,
            dependencies=self.dependencies
        )

        # Register agent methods as tools
        self._register_agent_methods()

        # Register agent data as resources
        self._register_agent_resources()

        # Register agent prompts
        self._register_agent_prompts()

        logger.info(f"Created MCP adapter for agent: {agent.name}")

    def _register_agent_methods(self):
        """
        Register agent methods as MCP tools.
        """
        # Get all public methods of the agent
        methods = inspect.getmembers(
            self.agent,
            predicate=lambda x: inspect.ismethod(x) and not x.__name__.startswith('_')
        )

        for name, method in methods:
            # Skip certain methods that shouldn't be exposed
            if name in ["__init__", "run", "start", "stop"]:
                continue

            # Get method signature and docstring
            sig = inspect.signature(method)
            doc = inspect.getdoc(method) or f"Call the {name} method of {self.agent.name}"

            # Create a wrapper function that calls the agent method
            def create_wrapper(method_name, method_func):
                # Use a unique name for each wrapper function
                wrapper_name = f"agent_{self.agent.name.lower().replace(' ', '_')}_{method_name}"

                async def wrapper_func(*args, **kwargs):
                    try:
                        result = method_func(*args, **kwargs)

                        # Convert result to string if it's not already
                        if not isinstance(result, str):
                            result = json.dumps(result, indent=2)

                        return result
                    except Exception as e:
                        logger.error(f"Error calling agent method {method_name}: {e}")
                        return f"Error: {str(e)}"

                # Set the wrapper's signature and docstring to match the original method
                wrapper_func.__signature__ = sig
                wrapper_func.__doc__ = doc
                wrapper_func.__name__ = wrapper_name

                return wrapper_func

            # Register the wrapper as an MCP tool
            wrapper = create_wrapper(name, method)
            self.mcp.tool(name=name)(wrapper)

            logger.info(f"Registered agent method as MCP tool: {name}")

    def _register_agent_resources(self):
        """
        Register agent data as MCP resources.
        """
        # Register basic agent info
        @self.mcp.resource("agent://info")
        def get_agent_info() -> str:
            """
            Get basic information about the agent.
            """
            return f"""
            # {self.agent.name}

            {self.agent.description}

            ## Tools

            {self._get_tools_description()}
            """

        # If the agent has a database_manager, register knowledge graph resources
        if hasattr(self.agent, "database_manager") and self.agent.database_manager:
            @self.mcp.resource("agent://knowledge/{query}")
            def get_knowledge(query: str) -> str:
                """
                Query the agent's knowledge graph.

                Args:
                    query: The query to execute
                """
                try:
                    # This is a simplified example - in a real implementation,
                    # you would need to validate and sanitize the query
                    results = self.agent.database_manager.query(query)

                    if not results:
                        return "No results found"

                    # Format the results
                    return json.dumps(results, indent=2)
                except Exception as e:
                    logger.error(f"Error querying knowledge graph: {e}")
                    return f"Error: {str(e)}"

        # If the agent has tools, register them as resources
        if hasattr(self.agent, "tools") and self.agent.tools:
            @self.mcp.resource("agent://tools")
            def get_tools() -> str:
                """
                Get a list of tools available to the agent.
                """
                return self._get_tools_description()

    def _register_agent_prompts(self):
        """
        Register agent prompts.
        """
        @self.mcp.prompt()
        def agent_help_prompt() -> str:
            """
            Create a help prompt for the agent.
            """
            return f"""
            I'd like to work with the {self.agent.name} agent.

            This agent is described as: {self.agent.description}

            Please help me understand what this agent can do and how I can use it effectively.
            """

    def _get_tools_description(self) -> str:
        """
        Get a description of the agent's tools.

        Returns:
            A formatted string describing the agent's tools
        """
        if not hasattr(self.agent, "tools") or not self.agent.tools:
            return "No tools available"

        result = "Available tools:\n\n"

        for name, tool in self.agent.tools.items():
            # Get tool description
            description = getattr(tool, "__doc__", "No description available")

            result += f"- **{name}**: {description}\n"

        return result

    def run(self, **kwargs):
        """
        Run the MCP server.

        Args:
            **kwargs: Additional arguments to pass to the MCP server's run method
        """
        self.mcp.run(**kwargs)


def create_agent_mcp_server(
    agent,
    server_name: Optional[str] = None,
    server_description: Optional[str] = None,
    dependencies: Optional[List[str]] = None
) -> AgentMCPAdapter:
    """
    Create an MCP server for an agent.

    Args:
        agent: The agent to create an MCP server for
        server_name: Name for the MCP server
        server_description: Description for the MCP server
        dependencies: List of dependencies for the MCP server

    Returns:
        An AgentMCPAdapter instance
    """
    return AgentMCPAdapter(
        agent=agent,
        server_name=server_name,
        server_description=server_description,
        dependencies=dependencies
    )
