#!/usr/bin/env python3
"""
Manage MCP Servers

This script provides a command-line interface for managing MCP servers.
It allows starting, stopping, and checking the status of MCP servers.

Usage:
    python3 scripts/manage_mcp_servers.py start [--servers SERVER_TYPES] [--wait]
    python3 scripts/manage_mcp_servers.py stop [--servers SERVER_TYPES]
    python3 scripts/manage_mcp_servers.py status
    python3 scripts/manage_mcp_servers.py test [--servers SERVER_TYPES]

Examples:
    # Start all servers
    python3 scripts/manage_mcp_servers.py start

    # Start specific servers
    python3 scripts/manage_mcp_servers.py start --servers basic agent_tool

    # Stop all servers
    python3 scripts/manage_mcp_servers.py stop

    # Check server status
    python3 scripts/manage_mcp_servers.py status

    # Run tests for all servers
    python3 scripts/manage_mcp_servers.py test
"""

import argparse
import logging
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the MCP server manager
from src.mcp import MCPConfig, MCPServerManager, MCPServerType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Manage MCP servers")

    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start MCP servers")
    start_parser.add_argument(
        "--servers",
        nargs="+",
        choices=["all", "basic", "agent_tool", "knowledge_resource"],
        default=["all"],
        help="Servers to start (default: all)",
    )
    start_parser.add_argument("--wait", action="store_true", help="Wait for servers to start")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop MCP servers")
    stop_parser.add_argument(
        "--servers",
        nargs="+",
        choices=["all", "basic", "agent_tool", "knowledge_resource"],
        default=["all"],
        help="Servers to stop (default: all)",
    )

    # Status command
    subparsers.add_parser("status", help="Check MCP server status")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test MCP servers")
    test_parser.add_argument(
        "--servers",
        nargs="+",
        choices=["all", "basic", "agent_tool", "knowledge_resource"],
        default=["all"],
        help="Servers to test (default: all)",
    )

    # Debug flag
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def get_server_types(server_names: list[str]) -> list[MCPServerType]:
    """
    Convert server names to MCPServerType enum values.

    Args:
        server_names: List of server names

    Returns:
        List of MCPServerType enum values
    """
    if "all" in server_names:
        return [MCPServerType.BASIC, MCPServerType.AGENT_TOOL, MCPServerType.KNOWLEDGE_RESOURCE]

    server_types = []
    for name in server_names:
        if name == "basic":
            server_types.append(MCPServerType.BASIC)
        elif name == "agent_tool":
            server_types.append(MCPServerType.AGENT_TOOL)
        elif name == "knowledge_resource":
            server_types.append(MCPServerType.KNOWLEDGE_RESOURCE)

    return server_types


def start_servers(
    server_manager: MCPServerManager, server_types: list[MCPServerType], wait: bool = False
) -> None:
    """
    Start MCP servers.

    Args:
        server_manager: MCP server manager
        server_types: List of server types to start
        wait: Whether to wait for servers to start
    """
    logger.info(f"Starting {len(server_types)} MCP servers...")

    for server_type in server_types:
        logger.info(f"Starting {server_type} server...")

        success, process_id = server_manager.start_server(
            server_type=server_type, wait=wait, timeout=30
        )

        if success:
            logger.info(f"Started {server_type} server (PID: {process_id})")
        else:
            logger.error(f"Failed to start {server_type} server")


def stop_servers(server_manager: MCPServerManager, server_types: list[MCPServerType]) -> None:
    """
    Stop MCP servers.

    Args:
        server_manager: MCP server manager
        server_types: List of server types to stop
    """
    if not server_types:
        logger.info("Stopping all MCP servers...")
        server_manager.stop_all_servers()
        logger.info("All MCP servers stopped")
        return

    logger.info(f"Stopping {len(server_types)} MCP servers...")

    for server_type in server_types:
        logger.info(f"Stopping {server_type} server...")

        if server_manager.is_server_running(server_type):
            server_manager.stop_server(server_type)
            logger.info(f"Stopped {server_type} server")
        else:
            logger.info(f"{server_type} server is not running")


def check_server_status(server_manager: MCPServerManager) -> None:
    """
    Check MCP server status.

    Args:
        server_manager: MCP server manager
    """
    logger.info("Checking MCP server status...")

    server_types = [MCPServerType.BASIC, MCPServerType.AGENT_TOOL, MCPServerType.KNOWLEDGE_RESOURCE]

    for server_type in server_types:
        running = server_manager.is_server_running(server_type)
        status = "RUNNING" if running else "STOPPED"
        logger.info(f"{server_type} server: {status}")


def test_servers(server_types: list[MCPServerType]) -> None:
    """
    Test MCP servers.

    Args:
        server_types: List of server types to test
    """
    logger.info(f"Testing {len(server_types)} MCP servers...")

    # Map server types to test files
    test_files = []

    if MCPServerType.BASIC in server_types:
        test_files.append("tests/mcp/test_basic_server.py")

    if MCPServerType.AGENT_TOOL in server_types:
        test_files.append("tests/mcp/test_agent_tool_server.py")

    if MCPServerType.KNOWLEDGE_RESOURCE in server_types:
        test_files.append("tests/mcp/test_knowledge_resource_server.py")

    # Add integration tests if testing all servers
    if len(server_types) == 3:
        test_files.append("tests/mcp/test_integration.py")

    # Run the tests
    import pytest

    logger.info(f"Running tests: {', '.join(test_files)}")
    result = pytest.main(["-v"] + test_files)

    if result == 0:
        logger.info("All tests passed!")
    else:
        logger.error(f"Tests failed with exit code {result}")
        sys.exit(result)


def main():
    """Main entry point."""
    args = parse_args()

    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Create MCP server manager
    config = MCPConfig()
    server_manager = MCPServerManager(config=config)

    # Process command
    if args.command == "start":
        server_types = get_server_types(args.servers)
        start_servers(server_manager, server_types, args.wait)

    elif args.command == "stop":
        server_types = get_server_types(args.servers)
        stop_servers(server_manager, server_types)

    elif args.command == "status":
        check_server_status(server_manager)

    elif args.command == "test":
        server_types = get_server_types(args.servers)
        test_servers(server_types)

    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
