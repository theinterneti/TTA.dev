"""
Unit tests for the agent tool MCP server.

This module contains tests for the agent tool MCP server's tools and resources.
"""

import pytest
from fastmcp import FastMCP


@pytest.mark.asyncio
async def test_agent_tool_server_initialization(agent_tool_server):
    """Test that the agent tool server initializes correctly."""
    assert isinstance(agent_tool_server, FastMCP)
    assert agent_tool_server.name == "TTA Agent Tool Server"

    # Get the tools using the list_tools method
    tools = [tool.name for tool in await agent_tool_server.list_tools()]
    assert "list_agents" in tools
    assert "get_agent_info" in tools
    assert "process_with_agent" in tools


@pytest.mark.asyncio
async def test_list_agents_tool(agent_tool_server):
    """Test the list_agents tool."""
    # Get the list_agents tool
    tools = await agent_tool_server.list_tools()
    list_agents_tool = None
    for tool in tools:
        if tool.name == "list_agents":
            list_agents_tool = tool
            break

    assert list_agents_tool is not None

    # Test the tool's metadata
    assert list_agents_tool.name == "list_agents"
    assert "List all available agents" in list_agents_tool.description

    # Test the tool's parameters
    assert "properties" in list_agents_tool.inputSchema
    assert len(list_agents_tool.inputSchema["properties"]) == 0

    # Test the tool's function by calling the server's call_tool method
    result = await agent_tool_server.call_tool("list_agents", {})

    # Check that the result contains expected information
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "Available Agents:" in result[0].text
        assert "world_building" in result[0].text
        assert "character_creation" in result[0].text
        assert "lore_keeper" in result[0].text
        assert "narrative_management" in result[0].text
    else:
        assert "Available Agents:" in result
        assert "world_building" in result
        assert "character_creation" in result
        assert "lore_keeper" in result
        assert "narrative_management" in result


@pytest.mark.asyncio
async def test_get_agent_info_tool(agent_tool_server):
    """Test the get_agent_info tool."""
    # Get the get_agent_info tool
    tools = await agent_tool_server.list_tools()
    get_agent_info_tool = None
    for tool in tools:
        if tool.name == "get_agent_info":
            get_agent_info_tool = tool
            break

    assert get_agent_info_tool is not None

    # Test the tool's metadata
    assert get_agent_info_tool.name == "get_agent_info"
    assert "Get detailed information about a specific agent" in get_agent_info_tool.description

    # Test the tool's parameters
    assert "properties" in get_agent_info_tool.inputSchema
    assert "agent_id" in get_agent_info_tool.inputSchema["properties"]
    assert get_agent_info_tool.inputSchema["properties"]["agent_id"]["type"] == "string"

    # Test the tool's function by calling the server's call_tool method

    # Test with a valid agent ID
    result = await agent_tool_server.call_tool("get_agent_info", {"agent_id": "world_building"})
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "World Building Agent" in result[0].text
        assert "world_building" in result[0].text
    else:
        assert "World Building Agent" in result
        assert "world_building" in result

    # Test with an invalid agent ID
    result = await agent_tool_server.call_tool("get_agent_info", {"agent_id": "nonexistent_agent"})
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "Error:" in result[0].text
        assert "Agent 'nonexistent_agent' not found" in result[0].text
    else:
        assert "Error:" in result
        assert "Agent 'nonexistent_agent' not found" in result


@pytest.mark.asyncio
async def test_process_with_agent_tool(agent_tool_server):
    """Test the process_with_agent tool."""
    # Get the process_with_agent tool
    tools = await agent_tool_server.list_tools()
    process_with_agent_tool = None
    for tool in tools:
        if tool.name == "process_with_agent":
            process_with_agent_tool = tool
            break

    assert process_with_agent_tool is not None

    # Test the tool's metadata
    assert process_with_agent_tool.name == "process_with_agent"
    assert "Process a goal using a specific agent" in process_with_agent_tool.description

    # Test the tool's parameters
    assert "properties" in process_with_agent_tool.inputSchema
    assert "agent_id" in process_with_agent_tool.inputSchema["properties"]
    assert process_with_agent_tool.inputSchema["properties"]["agent_id"]["type"] == "string"
    assert "goal" in process_with_agent_tool.inputSchema["properties"]
    assert process_with_agent_tool.inputSchema["properties"]["goal"]["type"] == "string"
    assert "context" in process_with_agent_tool.inputSchema["properties"]

    # Test the tool's function by calling the server's call_tool method

    # Test with a valid agent ID and goal
    result = await agent_tool_server.call_tool(
        "process_with_agent",
        {
            "agent_id": "world_building",
            "goal": "Create a forest",
            "context": {"type": "forest", "features": ["trees", "wildlife"]},
        },
    )

    # Check that the result contains expected information
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "Processed goal with World Building Agent" in result[0].text
        assert "Goal: Create a forest" in result[0].text
        assert "Context:" in result[0].text
        assert "trees" in result[0].text
        assert "wildlife" in result[0].text
    else:
        assert "Processed goal with World Building Agent" in result
        assert "Goal: Create a forest" in result
        assert "Context:" in result
        assert "trees" in result
        assert "wildlife" in result

    # Test with an invalid agent ID
    result = await agent_tool_server.call_tool(
        "process_with_agent",
        {"agent_id": "nonexistent_agent", "goal": "Create a forest", "context": {}},
    )
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "Error:" in result[0].text
        assert "Agent 'nonexistent_agent' not found" in result[0].text
    else:
        assert "Error:" in result
        assert "Agent 'nonexistent_agent' not found" in result


@pytest.mark.asyncio
async def test_agents_list_resource(agent_tool_server):
    """Test the agents list resource."""
    # Get the resources
    resources = await agent_tool_server.list_resources()

    # Check that the resource exists
    resource_uris = [str(resource.uri) for resource in resources]
    assert "agents://list" in resource_uris

    # Get the resource
    agents_list_resource = None
    for resource in resources:
        if str(resource.uri) == "agents://list":
            agents_list_resource = resource
            break

    assert agents_list_resource is not None

    # Test the resource's metadata
    assert str(agents_list_resource.uri) == "agents://list"
    # The description might be None in the new API
    if agents_list_resource.description is not None:
        assert "Get a list of all available agents" in agents_list_resource.description

    # Test the resource by reading it
    result = await agent_tool_server.read_resource("agents://list")

    # Check that the result contains expected information
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "# Available Agents" in result[0].text
        assert "World Building Agent" in result[0].text
        assert "Character Creation Agent" in result[0].text
        assert "Lore Keeper Agent" in result[0].text
        assert "Narrative Management Agent" in result[0].text
    else:
        assert "# Available Agents" in result
        assert "World Building Agent" in result
        assert "Character Creation Agent" in result
        assert "Lore Keeper Agent" in result
        assert "Narrative Management Agent" in result


@pytest.mark.asyncio
@pytest.mark.skip("Agent info resource with parameters is no longer available in the API")
async def test_agent_info_resource(agent_tool_server):
    """Test the agent info resource."""
    # Get the resources
    resources = await agent_tool_server.list_resources()

    # Check that the resource exists
    resource_uris = [str(resource.uri) for resource in resources]
    assert "agents://{agent_id}/info" in resource_uris

    # Get the resource
    agent_info_resource = None
    for resource in resources:
        if str(resource.uri) == "agents://{agent_id}/info":
            agent_info_resource = resource
            break

    assert agent_info_resource is not None

    # Test the resource's metadata
    assert str(agent_info_resource.uri) == "agents://{agent_id}/info"
    # The description might be None in the new API
    if agent_info_resource.description is not None:
        assert "Get detailed information about a specific agent" in agent_info_resource.description

    # Test the resource by reading it

    # Test with a valid agent ID
    result = await agent_tool_server.read_resource("agents://world_building/info")
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "# World Building Agent" in result[0].text
        assert "ID: `world_building`" in result[0].text
        assert "## Description" in result[0].text
        assert "## Usage" in result[0].text
    else:
        assert "# World Building Agent" in result
        assert "ID: `world_building`" in result
        assert "## Description" in result
        assert "## Usage" in result

    # Test with an invalid agent ID
    try:
        result = await agent_tool_server.read_resource("agents://nonexistent_agent/info")
        # The result might be a string or a list of TextContent objects
        if isinstance(result, list):
            assert len(result) > 0
            assert "Error:" in result[0].text
            assert "Agent 'nonexistent_agent' not found" in result[0].text
        else:
            assert "Error:" in result
            assert "Agent 'nonexistent_agent' not found" in result
    except Exception as e:
        # If the server raises an exception, that's also acceptable
        assert "nonexistent_agent" in str(e)
