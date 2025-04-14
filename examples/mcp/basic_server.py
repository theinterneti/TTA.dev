#!/usr/bin/env python3
"""
Basic MCP Server Example

This is a simple example of an MCP server using FastMCP.
It demonstrates the core concepts of MCP: tools, resources, and prompts.
"""

import argparse
import logging
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server
app = FastMCP(
    "Basic MCP Server",
    description="A simple example MCP server for the TTA.dev framework",
    dependencies=["fastmcp"]
)

# Define a tool
@app.tool()
async def hello(name: str = "World") -> str:
    """
    Say hello to someone.

    Args:
        name: The name to greet (default: "World")

    Returns:
        A greeting message
    """
    return f"Hello, {name}!"

# Define a resource
@app.resource("example://greeting")
def greeting() -> str:
    """
    Get a greeting message.

    Returns:
        A greeting message
    """
    return """
    # Welcome to the Basic MCP Server!

    This is a simple example of an MCP server using FastMCP.
    It demonstrates the core concepts of MCP: tools, resources, and prompts.

    ## Available Tools

    - `hello(name)`: Say hello to someone

    ## Available Resources

    - `example://greeting`: This greeting message
    - `example://info`: Information about the server
    """

@app.resource("example://info")
def info() -> str:
    """
    Get information about the server.

    Returns:
        Information about the server
    """
    return """
    # Server Information

    This server is a simple example of an MCP server using FastMCP.
    It is part of the TTA.dev framework, which provides reusable components
    for working with AI, agents, agentic RAG, and database integrations.

    ## MCP

    The Model Context Protocol (MCP) is a standardized way to provide context
    and tools to LLMs. MCP servers can:

    - Expose data through **Resources** (file-like data that can be read by clients)
    - Provide functionality through **Tools** (functions that can be called by the LLM)
    - Define interaction patterns through **Prompts** (reusable templates for LLM interactions)

    For more information, see the [MCP documentation](https://modelcontextprotocol.io).
    """

# Define a prompt
@app.prompt()
def help_prompt() -> str:
    """
    Create a help prompt for the server.

    Returns:
        A help prompt
    """
    return """
    I'd like to use the Basic MCP Server.

    Please help me understand what this server can do and how I can use it effectively.
    """

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Basic MCP Server")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Run the server
    app.run(host=args.host, port=args.port, debug=args.debug)
