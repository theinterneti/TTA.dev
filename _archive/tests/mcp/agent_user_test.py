#!/usr/bin/env python3
"""
Simulated user test for the Agent Tool MCP server.

This script simulates a user connecting to the Agent Tool MCP server,
and interacting with the server's tools and resources.
"""

import asyncio
import os
import sys

# Add the parent directory to the path so we can import the MCP modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the server modules for testing
from examples.mcp.agent_tool_server import mcp as agent_server


async def simulate_user_interaction():
    """Simulate a user interacting with the agent tool MCP server."""
    print("Starting simulated agent tool user test...")

    # Use the existing server instance
    server = agent_server
    print(f"Using server: {server.name}")

    # List the available tools
    tools = await server.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")

    # Call the list_agents tool
    print("Listing available agents")
    agents_result = await server.call_tool("list_agents", {})
    if isinstance(agents_result, list):
        agents_text = agents_result[0].text
    else:
        agents_text = agents_result
    print(f"Agents result:\n{agents_text}")

    # Call the get_agent_info tool
    print("Getting info for world_building agent")
    agent_info_result = await server.call_tool("get_agent_info", {"agent_id": "world_building"})
    if isinstance(agent_info_result, list):
        agent_info_text = agent_info_result[0].text
    else:
        agent_info_text = agent_info_result
    print(f"Agent info result:\n{agent_info_text}")

    # Call the process_with_agent tool
    print("Processing a goal with the world_building agent")
    process_result = await server.call_tool(
        "process_with_agent",
        {
            "agent_id": "world_building",
            "goal": "Create a small village",
            "context": {"setting": "fantasy", "features": ["tavern", "blacksmith", "town square"]},
        },
    )
    if isinstance(process_result, list):
        process_text = process_result[0].text
    else:
        process_text = process_result
    print(f"Process result (excerpt):\n{process_text[:300]}...")

    # List the available resources
    resources = await server.list_resources()
    print(f"Available resources: {[str(resource.uri) for resource in resources]}")

    # Read the agents list resource
    print("Reading agents list resource")
    agents_list_result = await server.read_resource("agents://list")
    if isinstance(agents_list_result, list):
        agents_list_text = agents_list_result[0].text
    else:
        agents_list_text = agents_list_result
    print(f"Agents list resource (excerpt):\n{agents_list_text[:200]}...")

    print("Simulated agent tool user test completed successfully!")


if __name__ == "__main__":
    asyncio.run(simulate_user_interaction())
