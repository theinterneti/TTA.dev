"""
Configuration for MCP server tests.

This module provides fixtures and utilities for testing MCP servers.
"""

import os
import subprocess
import sys
import time

import pytest
import pytest_asyncio


# Add the project root to the Python path dynamically by searching for a marker file
def find_project_root(marker_files=("pyproject.toml", ".git")):
    current = os.path.abspath(os.path.dirname(__file__))
    while True:
        if any(os.path.exists(os.path.join(current, marker)) for marker in marker_files):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    raise RuntimeError("Project root not found. Please ensure a marker file exists.")


project_root = find_project_root()
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the MCP servers
from examples.mcp.agent_tool_server import mcp as agent_tool_mcp
from examples.mcp.basic_server import mcp as basic_mcp
from examples.mcp.knowledge_resource_server import mcp as knowledge_resource_mcp


@pytest_asyncio.fixture
async def basic_server():
    """
    Fixture for the basic MCP server.

    Returns:
        The basic MCP server instance.
    """
    return basic_mcp


@pytest_asyncio.fixture
async def agent_tool_server():
    """
    Fixture for the agent tool MCP server.

    Returns:
        The agent tool MCP server instance.
    """
    return agent_tool_mcp


@pytest_asyncio.fixture
async def knowledge_resource_server():
    """
    Fixture for the knowledge resource MCP server.

    Returns:
        The knowledge resource MCP server instance.
    """
    return knowledge_resource_mcp


@pytest.fixture
def server_process():
    """
    Fixture for running an MCP server as a subprocess.

    This fixture provides a function that can be used to start an MCP server
    as a subprocess and automatically clean it up after the test.

    Returns:
        A function that starts an MCP server subprocess.
    """
    processes = []

    def _start_server(script_path: str) -> subprocess.Popen:
        """
        Start an MCP server as a subprocess.

        Args:
            script_path: Path to the server script.

        Returns:
            The subprocess.Popen instance.
        """
        process = subprocess.Popen(
            ["python3", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        processes.append(process)

        # Give the server a moment to start
        time.sleep(2)

        return process

    yield _start_server

    # Clean up all processes
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
