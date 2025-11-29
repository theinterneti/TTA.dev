#!/usr/bin/env python3
"""
Simulated user test for MCP servers.

This script simulates a user connecting to an MCP server, sending a handshake,
and interacting with the server's tools and resources.
"""

import asyncio
import os
import sys

# Add the parent directory to the path so we can import the MCP modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the server modules for testing
from examples.mcp.basic_server import mcp as basic_server


async def simulate_user_interaction():
    """Simulate a user interacting with the basic MCP server."""
    print("Starting simulated user test...")

    # Use the existing server instance
    server = basic_server
    print(f"Using server: {server.name}")

    # List the available tools
    tools = await server.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")

    # Call the echo tool
    echo_result = await server.call_tool("echo", {"message": "Hello from simulated user!"})
    if isinstance(echo_result, list):
        echo_text = echo_result[0].text
    else:
        echo_text = echo_result
    print(f"Echo tool result: {echo_text}")

    # Call the calculate tool
    calc_result = await server.call_tool("calculate", {"expression": "2 + 2 * 10"})
    if isinstance(calc_result, list):
        calc_text = calc_result[0].text
    else:
        calc_text = calc_result
    print(f"Calculate tool result: {calc_text}")

    # List the available resources
    resources = await server.list_resources()
    print(f"Available resources: {[str(resource.uri) for resource in resources]}")

    # Read the server info resource
    info_result = await server.read_resource("info://server")
    if isinstance(info_result, list):
        info_text = info_result[0].text
    else:
        info_text = info_result
    print(f"Server info resource:\n{info_text}")

    # Read the system info resource
    sys_result = await server.read_resource("info://system")
    if isinstance(sys_result, list):
        sys_text = sys_result[0].text
    else:
        sys_text = sys_result
    print(f"System info resource:\n{sys_text}")

    print("Simulated user test completed successfully!")


if __name__ == "__main__":
    asyncio.run(simulate_user_interaction())
