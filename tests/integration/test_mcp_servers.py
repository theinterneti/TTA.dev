"""
Integration tests for MCP servers.

This module contains integration tests for the Knowledge Resource and Agent Tool MCP servers.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# Import the example MCP servers
import sys

from src.mcp import MCPServerManager, MCPServerType

# Add the examples directory to the Python path
examples_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples"
)
sys.path.append(examples_path)

# Import the example MCP servers directly
sys.path.insert(0, examples_path)

# Test constants
KNOWLEDGE_SERVER_PORT = 8002
AGENT_TOOL_SERVER_PORT = 8001
TIMEOUT = 5  # seconds


@pytest.fixture
def server_manager():
    """
    Fixture for the MCP server manager.

    Returns:
        The MCP server manager instance.
    """
    return MCPServerManager()


@pytest.fixture
def knowledge_server():
    """
    Fixture for the Knowledge Resource MCP server.

    This fixture starts a Knowledge Resource MCP server on a test port
    and cleans it up after the test.

    Returns:
        The server process.
    """
    # Create and start the server
    process = subprocess.Popen(
        [
            "python3",
            "-c",
            f"import sys; sys.path.append('{examples_path}'); from examples.mcp.knowledge_resource_server import mcp; mcp.settings.port = {KNOWLEDGE_SERVER_PORT}; mcp.run('sse')",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give the server a moment to start
    time.sleep(2)

    yield process

    # Clean up
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def agent_tool_server():
    """
    Fixture for the Agent Tool MCP server.

    This fixture starts an Agent Tool MCP server on a test port
    and cleans it up after the test.

    Returns:
        The server process.
    """
    # Create and start the server
    process = subprocess.Popen(
        [
            "python3",
            "-c",
            f"import sys; sys.path.append('{examples_path}'); from examples.mcp.agent_tool_server import mcp; mcp.settings.port = {AGENT_TOOL_SERVER_PORT}; mcp.run('sse')",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give the server a moment to start
    time.sleep(2)

    yield process

    # Clean up
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def test_knowledge_server_http_connection(knowledge_server):
    """Test that the Knowledge Resource server can be connected to via HTTP."""
    # Wait a moment for the server to start
    time.sleep(5)

    # Try to connect to the server
    try:
        response = requests.get(f"http://localhost:{KNOWLEDGE_SERVER_PORT}/sse")
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        # Print any server output if available
        try:
            stdout, stderr = knowledge_server.communicate(timeout=0.1)
            print(f"Server stdout: {stdout}")
            print(f"Server stderr: {stderr}")
        except subprocess.TimeoutExpired:
            # Server is still running, which is expected
            pass

        pytest.fail("Could not connect to Knowledge Resource server")


def test_agent_tool_server_http_connection(agent_tool_server):
    """Test that the Agent Tool server can be connected to via HTTP."""
    # Wait a moment for the server to start
    time.sleep(5)

    # Try to connect to the server
    try:
        response = requests.get(f"http://localhost:{AGENT_TOOL_SERVER_PORT}/sse")
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        # Print any server output if available
        try:
            stdout, stderr = agent_tool_server.communicate(timeout=0.1)
            print(f"Server stdout: {stdout}")
            print(f"Server stderr: {stderr}")
        except subprocess.TimeoutExpired:
            # Server is still running, which is expected
            pass

        pytest.fail("Could not connect to Agent Tool server")


def test_knowledge_server_mcp_handshake(knowledge_server):
    """Test that the Knowledge Resource server responds to MCP handshake."""
    # Create a simple MCP handshake message
    handshake = {
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {"transports": ["http"]},
    }

    # Send the handshake
    try:
        response = requests.post(f"http://localhost:{KNOWLEDGE_SERVER_PORT}/mcp", json=handshake)
        assert response.status_code == 200

        # Parse the response
        response_data = response.json()
        assert response_data["type"] == "handshake_response"
        assert "capabilities" in response_data
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Knowledge Resource server")
    except Exception as e:
        pytest.fail(f"Error during handshake: {e}")


def test_agent_tool_server_mcp_handshake(agent_tool_server):
    """Test that the Agent Tool server responds to MCP handshake."""
    # Create a simple MCP handshake message
    handshake = {
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {"transports": ["http"]},
    }

    # Send the handshake
    try:
        response = requests.post(f"http://localhost:{AGENT_TOOL_SERVER_PORT}/mcp", json=handshake)
        assert response.status_code == 200

        # Parse the response
        response_data = response.json()
        assert response_data["type"] == "handshake_response"
        assert "capabilities" in response_data
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Agent Tool server")
    except Exception as e:
        pytest.fail(f"Error during handshake: {e}")


def test_knowledge_server_list_resources(knowledge_server):
    """Test that the Knowledge Resource server can list resources."""
    # Create a session
    handshake = {
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {"transports": ["http"]},
    }

    # Send the handshake
    try:
        response = requests.post(f"http://localhost:{KNOWLEDGE_SERVER_PORT}/mcp", json=handshake)
        assert response.status_code == 200

        # Get the session ID
        response_data = response.json()
        session_id = response_data.get("sessionId")
        assert session_id is not None

        # List resources
        list_resources_request = {
            "type": "list_resources_request",
            "sessionId": session_id,
            "requestId": "test-request-1",
        }

        response = requests.post(
            f"http://localhost:{KNOWLEDGE_SERVER_PORT}/mcp", json=list_resources_request
        )
        assert response.status_code == 200

        # Parse the response
        response_data = response.json()
        assert response_data["type"] == "list_resources_response"
        assert "resources" in response_data
        assert len(response_data["resources"]) > 0

        # Check that the expected resources are present
        resource_uris = [resource["uri"] for resource in response_data["resources"]]
        assert "kg://info" in resource_uris
        assert "kg://schema" in resource_uris
        assert "kg://locations" in resource_uris
        assert "kg://characters" in resource_uris
        assert "kg://items" in resource_uris
        assert "kg://concepts" in resource_uris
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Knowledge Resource server")
    except Exception as e:
        pytest.fail(f"Error during resource listing: {e}")


def test_agent_tool_server_list_tools(agent_tool_server):
    """Test that the Agent Tool server can list tools."""
    # Create a session
    handshake = {
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {"transports": ["http"]},
    }

    # Send the handshake
    try:
        response = requests.post(f"http://localhost:{AGENT_TOOL_SERVER_PORT}/mcp", json=handshake)
        assert response.status_code == 200

        # Get the session ID
        response_data = response.json()
        session_id = response_data.get("sessionId")
        assert session_id is not None

        # List tools
        list_tools_request = {
            "type": "list_tools_request",
            "sessionId": session_id,
            "requestId": "test-request-1",
        }

        response = requests.post(
            f"http://localhost:{AGENT_TOOL_SERVER_PORT}/mcp", json=list_tools_request
        )
        assert response.status_code == 200

        # Parse the response
        response_data = response.json()
        assert response_data["type"] == "list_tools_response"
        assert "tools" in response_data
        assert len(response_data["tools"]) > 0

        # Check that the expected tools are present
        tool_names = [tool["name"] for tool in response_data["tools"]]
        assert "list_agents" in tool_names
        assert "get_agent_info" in tool_names
        assert "invoke_agent" in tool_names
        assert "generate_world" in tool_names
        assert "generate_character" in tool_names
        assert "generate_narrative" in tool_names
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Agent Tool server")
    except Exception as e:
        pytest.fail(f"Error during tool listing: {e}")


def test_knowledge_server_read_resource(knowledge_server):
    """Test that the Knowledge Resource server can read resources."""
    # Create a session
    handshake = {
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {"transports": ["http"]},
    }

    # Send the handshake
    try:
        response = requests.post(f"http://localhost:{KNOWLEDGE_SERVER_PORT}/mcp", json=handshake)
        assert response.status_code == 200

        # Get the session ID
        response_data = response.json()
        session_id = response_data.get("sessionId")
        assert session_id is not None

        # Read a resource
        read_resource_request = {
            "type": "read_resource_request",
            "sessionId": session_id,
            "requestId": "test-request-2",
            "uri": "kg://info",
        }

        response = requests.post(
            f"http://localhost:{KNOWLEDGE_SERVER_PORT}/mcp", json=read_resource_request
        )
        assert response.status_code == 200

        # Parse the response
        response_data = response.json()
        assert response_data["type"] == "read_resource_response"
        assert "contents" in response_data
        assert len(response_data["contents"]) > 0

        # Check the content
        content = response_data["contents"][0]
        assert content["type"] == "text"
        assert "TTA Knowledge Graph" in content["text"]
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Knowledge Resource server")
    except Exception as e:
        pytest.fail(f"Error during resource reading: {e}")


def test_agent_tool_server_call_tool(agent_tool_server):
    """Test that the Agent Tool server can call tools."""
    # Create a session
    handshake = {
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {"transports": ["http"]},
    }

    # Send the handshake
    try:
        response = requests.post(f"http://localhost:{AGENT_TOOL_SERVER_PORT}/mcp", json=handshake)
        assert response.status_code == 200

        # Get the session ID
        response_data = response.json()
        session_id = response_data.get("sessionId")
        assert session_id is not None

        # Call a tool
        call_tool_request = {
            "type": "call_tool_request",
            "sessionId": session_id,
            "requestId": "test-request-2",
            "name": "list_agents",
            "arguments": {},
        }

        response = requests.post(
            f"http://localhost:{AGENT_TOOL_SERVER_PORT}/mcp", json=call_tool_request
        )
        assert response.status_code == 200

        # Parse the response
        response_data = response.json()
        assert response_data["type"] == "call_tool_response"
        assert "content" in response_data
        assert len(response_data["content"]) > 0

        # Check the content
        content = response_data["content"][0]
        assert content["type"] == "text"

        # Parse the JSON content
        tool_result = json.loads(content["text"])
        assert "agents" in tool_result
        assert "count" in tool_result
        assert tool_result["count"] >= 0
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Agent Tool server")
    except Exception as e:
        pytest.fail(f"Error during tool calling: {e}")


def test_server_manager_start_stop(server_manager):
    """Test that the server manager can start and stop servers."""
    # Start the Knowledge Resource server
    success, process_id = server_manager.start_server(
        server_type=MCPServerType.KNOWLEDGE_RESOURCE, wait=True, timeout=TIMEOUT
    )

    assert success
    assert process_id is not None

    # Check that the server is running
    assert server_manager.is_server_running(MCPServerType.KNOWLEDGE_RESOURCE)

    # Stop the server
    server_manager.stop_server(MCPServerType.KNOWLEDGE_RESOURCE)

    # Check that the server is stopped
    assert not server_manager.is_server_running(MCPServerType.KNOWLEDGE_RESOURCE)


def test_server_manager_start_multiple_servers(server_manager):
    """Test that the server manager can start multiple servers."""
    # Start the Knowledge Resource server
    success1, process_id1 = server_manager.start_server(
        server_type=MCPServerType.KNOWLEDGE_RESOURCE, wait=True, timeout=TIMEOUT
    )

    # Start the Agent Tool server
    success2, process_id2 = server_manager.start_server(
        server_type=MCPServerType.AGENT_TOOL, wait=True, timeout=TIMEOUT
    )

    assert success1
    assert process_id1 is not None
    assert success2
    assert process_id2 is not None

    # Check that both servers are running
    assert server_manager.is_server_running(MCPServerType.KNOWLEDGE_RESOURCE)
    assert server_manager.is_server_running(MCPServerType.AGENT_TOOL)

    # Stop all servers
    server_manager.stop_all_servers()

    # Check that all servers are stopped
    assert not server_manager.is_server_running(MCPServerType.KNOWLEDGE_RESOURCE)
    assert not server_manager.is_server_running(MCPServerType.AGENT_TOOL)


def test_server_manager_start_script(server_manager):
    """Test that the start_mcp_servers.py script works correctly."""
    # Start the script
    process = subprocess.Popen(
        ["python3", "scripts/start_mcp_servers.py", "--servers", "knowledge_resource", "--wait"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give the script a moment to start the server
    time.sleep(3)

    # Check that the server is running
    try:
        response = requests.get("http://localhost:8002/health")
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        process.terminate()
        process.wait()
        pytest.fail("Could not connect to Knowledge Resource server started by script")

    # Clean up
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
