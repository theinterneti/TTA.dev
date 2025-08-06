"""
Unit tests for the basic MCP server.

This module contains tests for the basic MCP server's tools and resources.
"""

import pytest
import json
import pytest_asyncio
from fastmcp import FastMCP

@pytest.mark.asyncio
async def test_basic_server_initialization(basic_server):
    """Test that the basic server initializes correctly."""
    assert isinstance(basic_server, FastMCP)
    assert basic_server.name == "TTA Basic Server"

    # Get the tools using the list_tools method
    tools = [tool.name for tool in await basic_server.list_tools()]
    assert "echo" in tools
    assert "calculate" in tools

@pytest.mark.asyncio
async def test_echo_tool(basic_server):
    """Test the echo tool."""
    # Get the echo tool
    tools = await basic_server.list_tools()
    echo_tool = None
    for tool in tools:
        if tool.name == "echo":
            echo_tool = tool
            break

    assert echo_tool is not None

    # Test the tool's metadata
    assert echo_tool.name == "echo"
    assert "Echo a message back to the user" in echo_tool.description

    # Test the tool's parameters
    assert "properties" in echo_tool.inputSchema
    assert "message" in echo_tool.inputSchema["properties"]
    assert echo_tool.inputSchema["properties"]["message"]["type"] == "string"

    # Test the tool's function by calling the server's call_tool method
    result = await basic_server.call_tool("echo", {"message": "Hello, world!"})
    assert len(result) > 0
    assert result[0].text == "Echo: Hello, world!"

@pytest.mark.asyncio
async def test_calculate_tool(basic_server):
    """Test the calculate tool."""
    # Get the calculate tool
    tools = await basic_server.list_tools()
    calculate_tool = None
    for tool in tools:
        if tool.name == "calculate":
            calculate_tool = tool
            break

    assert calculate_tool is not None

    # Test the tool's metadata
    assert calculate_tool.name == "calculate"
    assert "Safely evaluate a mathematical expression" in calculate_tool.description

    # Test the tool's parameters
    assert "properties" in calculate_tool.inputSchema
    assert "expression" in calculate_tool.inputSchema["properties"]
    assert calculate_tool.inputSchema["properties"]["expression"]["type"] == "string"

    # Test the tool's function by calling the server's call_tool method

    # Test valid expressions
    result = await basic_server.call_tool("calculate", {"expression": "2 + 2"})
    assert len(result) > 0
    assert result[0].text == "Result: 4"

    result = await basic_server.call_tool("calculate", {"expression": "10 * 5"})
    assert len(result) > 0
    assert result[0].text == "Result: 50"

    result = await basic_server.call_tool("calculate", {"expression": "(10 + 5) * 2"})
    assert len(result) > 0
    assert result[0].text == "Result: 30"

    # Test invalid expressions
    result = await basic_server.call_tool("calculate", {"expression": "import os"})
    assert len(result) > 0
    assert any("Error:" in r.text for r in result), "Dangerous expression was not blocked"

    result = await basic_server.call_tool("calculate", {"expression": "__import__('os').system('ls')"})
    assert len(result) > 0
    assert "Error:" in result[0].text

@pytest.mark.asyncio
async def test_server_info_resource(basic_server):
    """Test the server info resource."""
    # Get the resources
    resources = await basic_server.list_resources()

    # Check that the resource exists
    resource_uris = [str(resource.uri) for resource in resources]
    assert "info://server" in resource_uris

    # Get the resource
    server_info_resource = None
    for resource in resources:
        if str(resource.uri) == "info://server":
            server_info_resource = resource
            break

    assert server_info_resource is not None

    # Test the resource's metadata
    assert str(server_info_resource.uri) == "info://server"
    # The description might be None in the new API
    if server_info_resource.description is not None:
        assert "Get information about this MCP server" in server_info_resource.description

    # Test the resource by reading it
    result = await basic_server.read_resource("info://server")

    # Check that the result contains expected information
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "TTA Basic MCP Server" in result[0].text
        assert "Available tools:" in result[0].text
        assert "echo" in result[0].text
        assert "calculate" in result[0].text
    else:
        assert "TTA Basic MCP Server" in result
        assert "Available tools:" in result
        assert "echo" in result
        assert "calculate" in result

@pytest.mark.asyncio
async def test_system_info_resource(basic_server):
    """Test the system info resource."""
    # Get the resources
    resources = await basic_server.list_resources()

    # Check that the resource exists
    resource_uris = [str(resource.uri) for resource in resources]
    assert "info://system" in resource_uris

    # Get the resource
    system_info_resource = None
    for resource in resources:
        if str(resource.uri) == "info://system":
            system_info_resource = resource
            break

    assert system_info_resource is not None

    # Test the resource's metadata
    assert str(system_info_resource.uri) == "info://system"
    # The description might be None in the new API
    if system_info_resource.description is not None:
        assert "Get basic system information" in system_info_resource.description

    # Test the resource by reading it
    result = await basic_server.read_resource("info://system")

    # Check that the result contains expected information
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "System Information" in result[0].text
        assert "Python version:" in result[0].text
        assert "Platform:" in result[0].text
        assert "Processor:" in result[0].text
    else:
        assert "System Information" in result
        assert "Python version:" in result
        assert "Platform:" in result
        assert "Processor:" in result

@pytest.mark.asyncio
@pytest.mark.skip("Environment variable resource is no longer available in the API")
async def test_environment_variable_resource(basic_server):
    """Test the environment variable resource."""
    # Get the resources
    resources = await basic_server.list_resources()

    # Check that the resource exists
    resource_uris = [str(resource.uri) for resource in resources]
    assert "info://environment/{var_name}" in resource_uris

    # Get the resource
    env_var_resource = None
    for resource in resources:
        if str(resource.uri) == "info://environment/{var_name}":
            env_var_resource = resource
            break

    assert env_var_resource is not None

    # Test the resource's metadata
    assert str(env_var_resource.uri) == "info://environment/{var_name}"
    # The description might be None in the new API
    if env_var_resource.description is not None:
        assert "Get an environment variable" in env_var_resource.description

    # Test the resource by reading it with allowed variables

    # Test with PATH (should be allowed)
    result = await basic_server.read_resource("info://environment/PATH")
    # The result might be a string or a list of TextContent objects
    if isinstance(result, list):
        assert len(result) > 0
        assert "PATH=" in result[0].text
    else:
        assert "PATH=" in result

    # Test with a disallowed variable
    try:
        result = await basic_server.read_resource("info://environment/SECRET_KEY")
        # The result might be a string or a list of TextContent objects
        if isinstance(result, list):
            assert len(result) > 0
            assert "Error:" in result[0].text
            assert "Access to environment variable 'SECRET_KEY' is not allowed" in result[0].text
        else:
            assert "Error:" in result
            assert "Access to environment variable 'SECRET_KEY' is not allowed" in result
    except Exception as e:
        # If the server raises an exception, that's also acceptable
        assert "SECRET_KEY" in str(e)
