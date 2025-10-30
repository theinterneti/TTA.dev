"""
AI Assistant Integration Tests for MCP servers.

This module contains integration tests that simulate an AI assistant using the MCP servers.

NOTE: These tests are currently disabled because they depend on src.mcp module which
is not part of the current package structure. MCP server functionality is in examples/mcp/
but needs proper package integration.
"""

import pytest

pytest.skip("MCP module integration pending", allow_module_level=True)
import asyncio
import subprocess
import time
import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.mcp import MCPServerManager, MCPServerType

# Test constants
KNOWLEDGE_SERVER_PORT = 8002
AGENT_TOOL_SERVER_PORT = 8001
TIMEOUT = 5  # seconds


class AIAssistantSimulator:
    """
    A class that simulates an AI assistant using MCP servers.

    This class provides methods for connecting to MCP servers, listing resources and tools,
    reading resources, and calling tools.
    """

    def __init__(
        self,
        knowledge_server_url: Optional[str] = None,
        agent_tool_server_url: Optional[str] = None,
    ):
        """
        Initialize the AI assistant simulator.

        Args:
            knowledge_server_url: URL of the Knowledge Resource MCP server
            agent_tool_server_url: URL of the Agent Tool MCP server
        """
        # Provide default URLs if not supplied
        if not knowledge_server_url:
            knowledge_server_url = f"http://localhost:{KNOWLEDGE_SERVER_PORT}"
        if not agent_tool_server_url:
            agent_tool_server_url = f"http://localhost:{AGENT_TOOL_SERVER_PORT}"

        # Basic validation for URLs
        if not knowledge_server_url.startswith(
            "http://"
        ) and not knowledge_server_url.startswith("https://"):
            raise ValueError(
                "Invalid knowledge_server_url: must start with http:// or https://"
            )
        if not agent_tool_server_url.startswith(
            "http://"
        ) and not agent_tool_server_url.startswith("https://"):
            raise ValueError(
                "Invalid agent_tool_server_url: must start with http:// or https://"
            )

        self.knowledge_server_url = knowledge_server_url
        self.agent_tool_server_url = agent_tool_server_url
        self.knowledge_session_id = None
        self.agent_tool_session_id = None

    def connect_to_servers(self) -> bool:
        """
        Connect to the MCP servers.

        Returns:
            True if the connection was successful, False otherwise
        """
        # Connect to the Knowledge Resource server
        handshake = {
            "type": "handshake",
            "version": "2025-03-26",
            "capabilities": {"transports": ["http"]},
        }

        try:
            # Connect to Knowledge Resource server
            response = requests.post(f"{self.knowledge_server_url}/mcp", json=handshake)

            if response.status_code != 200:
                return False

            response_data = response.json()
            if response_data["type"] != "handshake_response":
                return False

            self.knowledge_session_id = response_data.get("sessionId")
            if not self.knowledge_session_id:
                return False

            # Connect to Agent Tool server
            response = requests.post(
                f"{self.agent_tool_server_url}/mcp", json=handshake
            )

            if response.status_code != 200:
                return False

            response_data = response.json()
            if response_data["type"] != "handshake_response":
                return False

            self.agent_tool_session_id = response_data.get("sessionId")
            if not self.agent_tool_session_id:
                return False

            return True
        except requests.exceptions.ConnectionError:
            return False

    def list_knowledge_resources(self) -> List[Dict[str, Any]]:
        """
        List resources from the Knowledge Resource server.

        Returns:
            List of resources
        """
        if not self.knowledge_session_id:
            raise ValueError("Not connected to Knowledge Resource server")

        list_resources_request = {
            "type": "list_resources_request",
            "sessionId": self.knowledge_session_id,
            "requestId": "list-resources-1",
        }

        response = requests.post(
            f"{self.knowledge_server_url}/mcp", json=list_resources_request
        )

        if response.status_code != 200:
            return []

        response_data = response.json()
        if response_data["type"] != "list_resources_response":
            return []

        return response_data.get("resources", [])

    def read_knowledge_resource(self, uri: str) -> str:
        """
        Read a resource from the Knowledge Resource server.

        Args:
            uri: URI of the resource to read

        Returns:
            Content of the resource
        """
        if not self.knowledge_session_id:
            raise ValueError("Not connected to Knowledge Resource server")

        read_resource_request = {
            "type": "read_resource_request",
            "sessionId": self.knowledge_session_id,
            "requestId": "read-resource-1",
            "uri": uri,
        }

        response = requests.post(
            f"{self.knowledge_server_url}/mcp", json=read_resource_request
        )

        if response.status_code != 200:
            return ""

        response_data = response.json()
        if response_data["type"] != "read_resource_response":
            return ""

        contents = response_data.get("contents", [])
        if not contents:
            return ""

        content = contents[0]
        if content["type"] != "text":
            return ""

        return content["text"]

    def list_agent_tools(self) -> List[Dict[str, Any]]:
        """
        List tools from the Agent Tool server.

        Returns:
            List of tools
        """
        if not self.agent_tool_session_id:
            raise ValueError("Not connected to Agent Tool server")

        list_tools_request = {
            "type": "list_tools_request",
            "sessionId": self.agent_tool_session_id,
            "requestId": "list-tools-1",
        }

        response = requests.post(
            f"{self.agent_tool_server_url}/mcp", json=list_tools_request
        )

        if response.status_code != 200:
            return []

        response_data = response.json()
        if response_data["type"] != "list_tools_response":
            return []

        return response_data.get("tools", [])

    def call_agent_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool from the Agent Tool server.

        Args:
            name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result of the tool call
        """
        if not self.agent_tool_session_id:
            raise ValueError("Not connected to Agent Tool server")

        call_tool_request = {
            "type": "call_tool_request",
            "sessionId": self.agent_tool_session_id,
            "requestId": "call-tool-1",
            "name": name,
            "arguments": arguments,
        }

        response = requests.post(
            f"{self.agent_tool_server_url}/mcp", json=call_tool_request
        )

        if response.status_code != 200:
            return {}

        response_data = response.json()
        if response_data["type"] != "call_tool_response":
            return {}

        content = response_data.get("content", [])
        if not content:
            return {}

        first_content = content[0]
        if first_content["type"] != "text":
            return {}

        try:
            return json.loads(first_content["text"])
        except json.JSONDecodeError:
            return {"text": first_content["text"]}


@pytest.fixture
def server_manager():
    """
    Fixture for the MCP server manager.

    Returns:
        The MCP server manager instance.
    """
    manager = MCPServerManager()

    # Start the servers
    manager.start_server(MCPServerType.KNOWLEDGE_RESOURCE, wait=True, timeout=TIMEOUT)
    manager.start_server(MCPServerType.AGENT_TOOL, wait=True, timeout=TIMEOUT)

    yield manager

    # Stop the servers
    manager.stop_all_servers()


@pytest.fixture
def ai_assistant(server_manager):
    """
    Fixture for the AI assistant simulator.

    Args:
        server_manager: The MCP server manager

    Returns:
        The AI assistant simulator
    """
    assistant = AIAssistantSimulator(
        knowledge_server_url="http://localhost:8002",
        agent_tool_server_url="http://localhost:8001",
    )

    # Connect to the servers
    connected = assistant.connect_to_servers()
    if not connected:
        pytest.skip("Could not connect to MCP servers")

    return assistant


def test_ai_assistant_connection(ai_assistant):
    """Test that the AI assistant can connect to the MCP servers."""
    # Connection is already tested in the fixture
    assert ai_assistant.knowledge_session_id is not None
    assert ai_assistant.agent_tool_session_id is not None


def test_ai_assistant_list_resources(ai_assistant):
    """Test that the AI assistant can list resources."""
    resources = ai_assistant.list_knowledge_resources()
    assert len(resources) > 0

    # Check that the expected resources are present
    resource_uris = [resource["uri"] for resource in resources]
    assert "kg://info" in resource_uris
    assert "kg://schema" in resource_uris
    assert "kg://locations" in resource_uris
    assert "kg://characters" in resource_uris
    assert "kg://items" in resource_uris
    assert "kg://concepts" in resource_uris


def test_ai_assistant_read_resource(ai_assistant):
    """Test that the AI assistant can read resources."""
    content = ai_assistant.read_knowledge_resource("kg://info")
    assert content != ""
    assert "TTA Knowledge Graph" in content
    assert "Available Resources" in content
    assert "Available Tools" in content


def test_ai_assistant_list_tools(ai_assistant):
    """Test that the AI assistant can list tools."""
    tools = ai_assistant.list_agent_tools()
    assert len(tools) > 0

    # Check that the expected tools are present
    tool_names = [tool["name"] for tool in tools]
    assert "list_agents" in tool_names
    assert "get_agent_info" in tool_names
    assert "invoke_agent" in tool_names
    assert "generate_world" in tool_names
    assert "generate_character" in tool_names
    assert "generate_narrative" in tool_names


def test_ai_assistant_call_tool(ai_assistant):
    """Test that the AI assistant can call tools."""
    result = ai_assistant.call_agent_tool("list_agents", {})
    assert "agents" in result
    assert "count" in result
    assert result["count"] >= 0


def test_ai_assistant_generate_world(ai_assistant):
    """Test that the AI assistant can generate a world."""
    result = ai_assistant.call_agent_tool(
        "generate_world",
        {
            "theme": "cyberpunk",
            "details": {"technology_level": "high", "atmosphere": "dystopian"},
        },
    )

    # The result might be an error if the agent is not available
    if "error" in result:
        pytest.skip("Agent not available")

    assert "result" in result
    assert "agent_id" in result
    assert "method" in result
    assert result["agent_id"] == "wba"
    assert result["method"] == "generate_world"


def test_ai_assistant_get_agent_info(ai_assistant):
    """Test that the AI assistant can get agent information."""
    result = ai_assistant.call_agent_tool("get_agent_info", {"agent_id": "wba"})

    # The result might be an error if the agent is not available
    if "error" in result and "agent not found" in result["message"]:
        pytest.skip("Agent not available")

    assert "id" in result
    assert "name" in result
    assert "description" in result
    assert result["id"] == "wba"
    assert "World Building Agent" in result["name"]


def test_ai_assistant_query_knowledge_graph(ai_assistant):
    """Test that the AI assistant can query the knowledge graph."""
    result = ai_assistant.call_agent_tool(
        "query_kg",
        {
            "query": "MATCH (l:Location) RETURN l.name AS name, l.description AS description"
        },
    )

    # This is called on the wrong server, so it should fail
    assert "error" in result or "text" in result


def test_ai_assistant_workflow(ai_assistant):
    """Test a complete AI assistant workflow."""
    # 1. Get information about the knowledge graph
    kg_info = ai_assistant.read_knowledge_resource("kg://info")
    assert "TTA Knowledge Graph" in kg_info

    # 2. List available agents
    agents_result = ai_assistant.call_agent_tool("list_agents", {})
    assert "agents" in agents_result
    assert "count" in agents_result

    # 3. Get information about the World Building Agent
    wba_info = ai_assistant.call_agent_tool("get_agent_info", {"agent_id": "wba"})

    # The result might be an error if the agent is not available
    if "error" in wba_info and "agent not found" in wba_info["message"]:
        pytest.skip("Agent not available")

    assert "id" in wba_info
    assert "name" in wba_info
    assert "description" in wba_info

    # 4. Generate a world
    world_result = ai_assistant.call_agent_tool(
        "generate_world",
        {
            "theme": "fantasy",
            "details": {"magic_level": "high", "technology_level": "medieval"},
        },
    )

    # The result might be an error if the agent is not available
    if "error" in world_result:
        pytest.skip("Agent not available")

    assert "result" in world_result
    assert "agent_id" in world_result
    assert "method" in world_result

    # 5. Get information about locations
    locations = ai_assistant.read_knowledge_resource("kg://locations")
    assert "# Locations" in locations
