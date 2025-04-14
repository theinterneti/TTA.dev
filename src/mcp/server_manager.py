"""
MCP Server Manager for the TTA.dev framework.

This module provides a centralized manager for MCP servers in the TTA.dev framework.
"""

import os
import sys
import subprocess
import logging
import socket
from typing import Optional, Tuple
import time
import atexit

from .server_types import MCPServerType
from .config import MCPConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manager for MCP servers."""

    def __init__(self, config: Optional[MCPConfig] = None):
        """
        Initialize the MCP server manager.

        Args:
            config: MCP configuration
        """
        self.config = config or MCPConfig()
        self.servers = {}
        self.processes = {}

        # Register cleanup handler
        atexit.register(self.stop_all_servers)

    def start_server(
        self,
        server_type: MCPServerType,
        wait: bool = False,
        timeout: int = 30
    ) -> Tuple[bool, Optional[int]]:
        """
        Start an MCP server.

        Args:
            server_type: Type of the server to start
            wait: Whether to wait for the server to start
            timeout: Timeout in seconds for waiting

        Returns:
            Tuple of (success, process_id)
        """
        server_type_str = str(server_type)

        # Check if server is already running
        if server_type_str in self.processes and self.processes[server_type_str].poll() is None:
            logger.info(f"Server {server_type_str} is already running")
            return True, self.processes[server_type_str].pid

        # Get server configuration
        server_config = self.config.get_server_config(server_type)

        if not server_config:
            logger.error(f"No configuration found for server type {server_type_str}")
            return False, None

        if not server_config.get("enabled", True):
            logger.warning(f"Server {server_type_str} is disabled in configuration")
            return False, None

        # Get script path
        script_path = server_config.get("script_path")

        if not script_path:
            logger.error(f"No script path found for server type {server_type_str}")
            return False, None

        # Get host and port
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8000)

        # Start the server
        try:
            # Construct the command
            cmd = [
                sys.executable,
                script_path,
                "--host", host,
                "--port", str(port),
                "--debug"
            ]

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store the process
            self.processes[server_type_str] = process

            logger.info(f"Started server {server_type_str} on {host}:{port} (PID: {process.pid})")

            # Wait for the server to start if requested
            if wait:
                start_time = time.time()
                while time.time() - start_time < timeout:
                    # Check if the process is still running
                    if process.poll() is not None:
                        logger.error(f"Server {server_type_str} failed to start")
                        return False, None

                    # Check if the server is ready
                    if self._check_server_ready(host, port):
                        logger.info(f"Server {server_type_str} is ready")
                        return True, process.pid

                    time.sleep(0.1)

                logger.warning(f"Timeout waiting for server {server_type_str} to start")
                return False, process.pid

            return True, process.pid
        except Exception as e:
            logger.error(f"Error starting server {server_type_str}: {e}")
            return False, None

    def start_agent_server(
        self,
        agent,
        wait: bool = False,
        timeout: int = 5
    ) -> Tuple[bool, Optional[int]]:
        """
        Start an MCP server for an agent.

        Args:
            agent: Agent to create a server for
            wait: Whether to wait for the server to start
            timeout: Timeout in seconds for waiting

        Returns:
            Tuple of (success, process_id)
        """
        agent_name = agent.name
        agent_id = agent_name.lower().replace(' ', '_')

        # Check if server is already running
        if agent_id in self.processes and self.processes[agent_id].poll() is None:
            logger.info(f"Agent server for {agent_name} is already running")
            return True, self.processes[agent_id].pid

        # Get agent server configuration
        agent_config = self.config.get_agent_server_config(agent_name)

        if not agent_config:
            # Create new agent server configuration
            agent_config = self.config.add_agent_server_config(agent_name)

        if not agent_config.get("enabled", True):
            logger.warning(f"Agent server for {agent_name} is disabled in configuration")
            return False, None

        # Get host and port
        host = agent_config.get("host", "localhost")
        port = agent_config.get("port", 8000)

        # Create the agent server
        try:
            # Create a temporary script for the agent server
            script_content = f'''#!/usr/bin/env python3
"""
MCP Server for {agent_name}
"""

import sys
import os

# Add the project root to the Python path
sys.path.append('/app')

from tta.dev.mcp import create_agent_mcp_server
from tta.dev.agents import BaseAgent
from tta.dev.database import get_neo4j_manager

# Create a simple agent for testing
agent = BaseAgent(
    name="{agent_name}",
    description="Agent created for MCP server testing",
    database_manager=get_neo4j_manager()
)

# Create the MCP server
adapter = create_agent_mcp_server(
    agent=agent,
    server_name="{agent_name} MCP Server",
    server_description="MCP server for {agent_name}",
    dependencies=["fastmcp"]
)

# Run the server
adapter.run(host="{host}", port={port})
'''

            # Create a temporary directory for the script if it doesn't exist
            os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp"), exist_ok=True)

            # Save the script to a temporary file
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp", f"{agent_id}_server.py")
            with open(script_path, "w") as f:
                f.write(script_content)

            # Make the script executable
            os.chmod(script_path, 0o755)

            # Start the server
            cmd = [
                sys.executable,
                script_path
            ]

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store the process
            self.processes[agent_id] = process

            logger.info(f"Started agent server for {agent_name} on {host}:{port} (PID: {process.pid})")

            # Wait for the server to start if requested
            if wait:
                start_time = time.time()
                while time.time() - start_time < timeout:
                    # Check if the process is still running
                    if process.poll() is not None:
                        logger.error(f"Agent server for {agent_name} failed to start")
                        return False, None

                    # Check if the server is ready
                    if self._check_server_ready(host, port):
                        logger.info(f"Agent server for {agent_name} is ready")
                        return True, process.pid

                    time.sleep(0.1)

                logger.warning(f"Timeout waiting for agent server for {agent_name} to start")
                return False, process.pid

            return True, process.pid
        except Exception as e:
            logger.error(f"Error starting agent server for {agent_name}: {e}")
            return False, None

    def stop_server(self, server_type: MCPServerType) -> bool:
        """
        Stop an MCP server.

        Args:
            server_type: Type of the server to stop

        Returns:
            Whether the server was stopped successfully
        """
        server_type_str = str(server_type)

        # Check if server is running
        if server_type_str not in self.processes:
            logger.warning(f"Server {server_type_str} is not running")
            return False

        process = self.processes[server_type_str]

        # Check if process is still running
        if process.poll() is not None:
            logger.info(f"Server {server_type_str} is already stopped")
            del self.processes[server_type_str]
            return True

        # Stop the process
        try:
            process.terminate()

            # Wait for the process to terminate
            process.wait(timeout=5)

            logger.info(f"Stopped server {server_type_str}")

            # Remove the process
            del self.processes[server_type_str]

            return True
        except subprocess.TimeoutExpired:
            # Force kill the process
            process.kill()

            logger.warning(f"Force killed server {server_type_str}")

            # Remove the process
            del self.processes[server_type_str]

            return True
        except Exception as e:
            logger.error(f"Error stopping server {server_type_str}: {e}")
            return False

    def stop_agent_server(self, agent_name: str) -> bool:
        """
        Stop an MCP server for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Whether the server was stopped successfully
        """
        # Convert agent name to agent_id
        agent_id = agent_name.lower().replace(' ', '_')

        # Check if server is running
        if agent_id not in self.processes:
            logger.warning(f"Agent server for {agent_name} is not running")
            return False

        process = self.processes[agent_id]

        # Check if process is still running
        if process.poll() is not None:
            logger.info(f"Agent server for {agent_name} is already stopped")
            del self.processes[agent_id]
            return True

        # Stop the process
        try:
            process.terminate()

            # Wait for the process to terminate
            process.wait(timeout=5)

            logger.info(f"Stopped agent server for {agent_name}")

            # Remove the process
            del self.processes[agent_id]

            # Remove the temporary script
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp", f"{agent_id}_server.py")
            if os.path.exists(script_path):
                os.remove(script_path)

            return True
        except subprocess.TimeoutExpired:
            # Force kill the process
            process.kill()

            logger.warning(f"Force killed agent server for {agent_name}")

            # Remove the process
            del self.processes[agent_id]

            # Remove the temporary script
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp", f"{agent_id}_server.py")
            if os.path.exists(script_path):
                os.remove(script_path)

            return True
        except Exception as e:
            logger.error(f"Error stopping agent server for {agent_name}: {e}")
            return False

    def stop_all_servers(self) -> None:
        """Stop all running MCP servers."""
        # Copy the keys to avoid modifying the dictionary during iteration
        server_keys = list(self.processes.keys())

        for server_key in server_keys:
            # Check if this is a server type or an agent name
            try:
                server_type = MCPServerType.from_string(server_key)
                self.stop_server(server_type)
            except ValueError:
                # This is an agent name
                self.stop_agent_server(server_key)

    def _check_server_ready(self, host: str, port: int) -> bool:
        """
        Check if a server is ready.

        Args:
            host: Host of the server
            port: Port of the server

        Returns:
            Whether the server is ready
        """
        # Try to connect to the server
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            return False
