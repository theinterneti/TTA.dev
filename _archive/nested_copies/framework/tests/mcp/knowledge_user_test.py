#!/usr/bin/env python3
"""
Simulated user test for the Knowledge Resource MCP server.

This script simulates a user connecting to the Knowledge Resource MCP server,
and interacting with the server's tools and resources.
"""

import asyncio
import os
import sys

# Add the parent directory to the path so we can import the MCP modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the server modules for testing
from examples.mcp.knowledge_resource_server import mcp as knowledge_server


async def simulate_user_interaction():
    """Simulate a user interacting with the knowledge resource MCP server."""
    print("Starting simulated knowledge resource user test...")

    # Use the existing server instance
    server = knowledge_server
    print(f"Using server: {server.name}")

    # List the available tools
    tools = await server.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")

    # Call the query_knowledge_graph tool
    query = "MATCH (l:Location) RETURN l LIMIT 3"
    print(f"Executing query: {query}")
    query_result = await server.call_tool("query_knowledge_graph", {"query": query})
    if isinstance(query_result, list):
        query_text = query_result[0].text
    else:
        query_text = query_result
    print(f"Query result:\n{query_text}")

    # Call the get_entity_by_name tool
    print("Getting entity: Location/The Nexus")
    entity_result = await server.call_tool(
        "get_entity_by_name", {"entity_type": "Location", "name": "The Nexus"}
    )
    if isinstance(entity_result, list):
        entity_text = entity_result[0].text
    else:
        entity_text = entity_result
    print(f"Entity result:\n{entity_text}")

    # List the available resources
    resources = await server.list_resources()
    print(f"Available resources: {[str(resource.uri) for resource in resources]}")

    # Read the locations resource
    print("Reading locations resource")
    locations_result = await server.read_resource("knowledge://locations")
    if isinstance(locations_result, list):
        locations_text = locations_result[0].text
    else:
        locations_text = locations_result
    print(f"Locations resource (excerpt):\n{locations_text[:200]}...")

    # Read the characters resource
    print("Reading characters resource")
    characters_result = await server.read_resource("knowledge://characters")
    if isinstance(characters_result, list):
        characters_text = characters_result[0].text
    else:
        characters_text = characters_result
    print(f"Characters resource (excerpt):\n{characters_text[:200]}...")

    # Read the items resource
    print("Reading items resource")
    items_result = await server.read_resource("knowledge://items")
    if isinstance(items_result, list):
        items_text = items_result[0].text
    else:
        items_text = items_result
    print(f"Items resource (excerpt):\n{items_text[:200]}...")

    print("Simulated knowledge resource user test completed successfully!")


if __name__ == "__main__":
    asyncio.run(simulate_user_interaction())
