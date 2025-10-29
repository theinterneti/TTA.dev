"""
Unit tests for the agent adapter.

This module contains tests for the agent adapter.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
sys.path.append("/app")

# Import the agent adapter
from src.mcp.agent_adapter import AgentMCPAdapter, create_agent_mcp_server


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name="Mock Agent", description="A mock agent for testing"):
        self.name = name
        self.description = description
        self.tools = {"test_tool": MagicMock(__doc__="A test tool")}
        self.neo4j_manager = MagicMock()

    def test_method(self, param1, param2=None):
        """A test method."""
        return f"Test method called with {param1} and {param2}"

    def another_method(self):
        """Another test method."""
        return "Another method called"


@pytest.fixture
def mock_agent():
    """Fixture for a mock agent."""
    return MockAgent()


@pytest.fixture
def mock_fastmcp():
    """Fixture for a mock FastMCP instance."""
    mock = MagicMock()
    mock.tool.return_value = lambda x: x
    return mock


@patch("src.mcp.agent_adapter.FastMCP")
def test_agent_adapter_initialization(mock_fastmcp_class, mock_agent):
    """Test that the agent adapter initializes correctly."""
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_class.return_value = mock_fastmcp_instance

    adapter = AgentMCPAdapter(mock_agent)

    # Check that FastMCP was initialized correctly
    mock_fastmcp_class.assert_called_once_with(
        f"{mock_agent.name} MCP Server",
        description=f"MCP server for {mock_agent.name}",
        dependencies=["fastmcp"],
    )

    # Check that the adapter's properties were set correctly
    assert adapter.agent == mock_agent
    assert adapter.server_name == f"{mock_agent.name} MCP Server"
    assert adapter.server_description == f"MCP server for {mock_agent.name}"
    assert adapter.dependencies == ["fastmcp"]
    assert adapter.mcp == mock_fastmcp_instance


@patch("src.mcp.agent_adapter.FastMCP")
def test_register_agent_methods(mock_fastmcp_class, mock_agent):
    """Test that agent methods are registered as MCP tools."""
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_class.return_value = mock_fastmcp_instance

    adapter = AgentMCPAdapter(mock_agent)

    # Check that the tool decorator was called for each method
    assert mock_fastmcp_instance.tool.call_count >= 2

    # Check that the run method was not registered as a tool
    for call in mock_fastmcp_instance.tool.call_args_list:
        args, kwargs = call
        if "name" in kwargs:
            assert kwargs["name"] != "run"


@patch("src.mcp.agent_adapter.FastMCP")
def test_register_agent_resources(mock_fastmcp_class, mock_agent):
    """Test that agent data is registered as MCP resources."""
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_class.return_value = mock_fastmcp_instance

    adapter = AgentMCPAdapter(mock_agent)

    # Check that the resource decorator was called
    assert mock_fastmcp_instance.resource.call_count >= 1

    # Check that the agent info resource was registered
    mock_fastmcp_instance.resource.assert_any_call("agent://info")


@patch("src.mcp.agent_adapter.FastMCP")
def test_register_agent_prompts(mock_fastmcp_class, mock_agent):
    """Test that agent prompts are registered."""
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_class.return_value = mock_fastmcp_instance

    adapter = AgentMCPAdapter(mock_agent)

    # Check that the prompt decorator was called
    assert mock_fastmcp_instance.prompt.call_count >= 1


@patch("src.mcp.agent_adapter.FastMCP")
def test_run_method(mock_fastmcp_class, mock_agent):
    """Test that the run method calls the MCP server's run method."""
    mock_fastmcp_instance = MagicMock()
    mock_fastmcp_class.return_value = mock_fastmcp_instance

    adapter = AgentMCPAdapter(mock_agent)
    adapter.run(port=8000)

    # Check that the MCP server's run method was called with the correct arguments
    mock_fastmcp_instance.run.assert_called_once_with(port=8000)


@patch("src.mcp.agent_adapter.AgentMCPAdapter")
def test_create_agent_mcp_server(mock_adapter_class, mock_agent):
    """Test that create_agent_mcp_server creates an AgentMCPAdapter."""
    mock_adapter_instance = MagicMock()
    mock_adapter_class.return_value = mock_adapter_instance

    adapter = create_agent_mcp_server(
        agent=mock_agent,
        server_name="Test Server",
        server_description="A test server",
        dependencies=["fastmcp", "test"],
    )

    # Check that AgentMCPAdapter was initialized correctly
    mock_adapter_class.assert_called_once_with(
        agent=mock_agent,
        server_name="Test Server",
        server_description="A test server",
        dependencies=["fastmcp", "test"],
    )

    # Check that the adapter was returned
    assert adapter == mock_adapter_instance
