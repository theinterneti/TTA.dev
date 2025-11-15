#!/usr/bin/env python3
"""
Start MCP Servers for the TTA project.

This script starts the MCP servers for the TTA project.
"""

import argparse
import logging
import os
import sys
import time

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp import MCPConfig, MCPServerManager, MCPServerType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start MCP servers for the TTA project")

    parser.add_argument(
        "--servers",
        type=str,
        nargs="+",
        choices=["basic", "agent_tool", "knowledge_resource", "all"],
        default=["all"],
        help="Servers to start (default: all)",
    )

    parser.add_argument(
        "--config", type=str, default=None, help="Path to the MCP configuration file"
    )

    parser.add_argument("--wait", action="store_true", help="Wait for servers to start")

    parser.add_argument(
        "--timeout", type=int, default=5, help="Timeout in seconds for waiting (default: 5)"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_args()

    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Create MCP configuration
    config = MCPConfig(config_path=args.config)

    # Create MCP server manager
    server_manager = MCPServerManager(config=config)

    # Determine which servers to start
    servers_to_start = []

    if "all" in args.servers:
        servers_to_start = [
            MCPServerType.BASIC,
            MCPServerType.AGENT_TOOL,
            MCPServerType.KNOWLEDGE_RESOURCE,
        ]
    else:
        for server_name in args.servers:
            try:
                server_type = MCPServerType.from_string(server_name)
                servers_to_start.append(server_type)
            except ValueError:
                logger.warning(f"Unknown server type: {server_name}")

    # Start the servers
    started_servers = []

    for server_type in servers_to_start:
        logger.info(f"Starting server: {server_type}")

        success, process_id = server_manager.start_server(
            server_type=server_type, wait=args.wait, timeout=args.timeout
        )

        if success:
            logger.info(f"Started server {server_type} (PID: {process_id})")
            started_servers.append(server_type)
        else:
            logger.error(f"Failed to start server {server_type}")

    # Print summary
    logger.info(
        f"Started {len(started_servers)} servers: {', '.join(str(s) for s in started_servers)}"
    )

    # Keep the script running to keep the servers running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping servers...")
        server_manager.stop_all_servers()
        logger.info("All servers stopped")


if __name__ == "__main__":
    main()
