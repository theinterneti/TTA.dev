#!/usr/bin/env python3
"""
Agent MCP Adapter Example

This example demonstrates how to use the AgentMCPAdapter to expose a TTA.dev agent as an MCP server.
"""

import argparse
import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tta.dev.agents import BaseAgent
from tta.dev.mcp import create_agent_mcp_server
from tta.dev.database import get_neo4j_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Agent MCP Adapter Example")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Create a simple agent
    agent = BaseAgent(
        name="ExampleAgent",
        description="A simple agent for demonstrating the AgentMCPAdapter",
        database_manager=get_neo4j_manager()
    )

    # Add some tools to the agent
    agent.add_tool("greet", lambda name="World": f"Hello, {name}!")
    agent.add_tool("echo", lambda text: text)
    agent.add_tool("add", lambda a, b: a + b)

    # Create an MCP server for the agent
    server = create_agent_mcp_server(
        agent=agent,
        server_name="Example Agent Server",
        server_description="MCP server for the example agent"
    )

    # Run the server
    logger.info(f"Starting MCP server for {agent.name} on {args.host}:{args.port}")
    server.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
