"""
Main entry point for the TTA project.

This module provides the main entry point for running the Therapeutic Text Adventure.
"""

import logging
import argparse
from typing import Dict, Any, Optional, List

from ..knowledge import get_neo4j_manager
from ..models import get_llm_client
from ..tools import get_tool_registry
from ..agents import create_dynamic_agents
from ..mcp import MCPServerManager, MCPConfig, MCPServerType
from .dynamic_game import run_dynamic_game

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Therapeutic Text Adventure")

    # Neo4j options
    neo4j_group = parser.add_argument_group("Neo4j Options")
    neo4j_group.add_argument(
        "--neo4j-uri",
        type=str,
        default=None,
        help="Neo4j URI (default: from environment)",
    )
    neo4j_group.add_argument(
        "--neo4j-user",
        type=str,
        default=None,
        help="Neo4j username (default: from environment)",
    )
    neo4j_group.add_argument(
        "--neo4j-password",
        type=str,
        default=None,
        help="Neo4j password (default: from environment)",
    )

    # LLM options
    llm_group = parser.add_argument_group("LLM Options")
    llm_group.add_argument(
        "--llm-api-base",
        type=str,
        default=None,
        help="LLM API base URL (default: from environment)",
    )

    # MCP options
    mcp_group = parser.add_argument_group("MCP Options")
    mcp_group.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help="Path to MCP configuration file",
    )
    mcp_group.add_argument(
        "--start-mcp-servers",
        action="store_true",
        help="Start MCP servers",
    )
    mcp_group.add_argument(
        "--mcp-servers",
        type=str,
        nargs="+",
        choices=["basic", "agent_tool", "knowledge_resource", "all"],
        default=["all"],
        help="MCP servers to start (default: all)",
    )

    # Debug options
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    return parser.parse_args()


def main():
    """Main entry point for the TTA project."""
    # Parse command line arguments
    args = parse_args()

    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Initialize Neo4j manager
    neo4j_kwargs = {}
    if args.neo4j_uri:
        neo4j_kwargs["uri"] = args.neo4j_uri
    if args.neo4j_user:
        neo4j_kwargs["username"] = args.neo4j_user
    if args.neo4j_password:
        neo4j_kwargs["password"] = args.neo4j_password

    neo4j_manager = get_neo4j_manager(**neo4j_kwargs)

    # Initialize LLM client
    llm_kwargs = {}
    if args.llm_api_base:
        llm_kwargs["api_base"] = args.llm_api_base

    llm_client = get_llm_client(**llm_kwargs)

    # Initialize tool registry
    tool_registry = get_tool_registry()

    # Load tools from Neo4j
    tool_registry.load_tools_from_neo4j()

    # Initialize dynamic agents
    agents = create_dynamic_agents(
        neo4j_manager=neo4j_manager,
        tools=tool_registry.get_all_tools()
    )

    # Initialize MCP
    mcp_config = MCPConfig(config_path=args.mcp_config)
    mcp_server_manager = MCPServerManager(config=mcp_config)

    # Start MCP servers if requested
    if args.start_mcp_servers:
        logger.info("Starting MCP servers...")

        # Determine which servers to start
        servers_to_start = []

        if "all" in args.mcp_servers:
            servers_to_start = [
                MCPServerType.BASIC,
                MCPServerType.AGENT_TOOL,
                MCPServerType.KNOWLEDGE_RESOURCE
            ]
        else:
            for server_name in args.mcp_servers:
                try:
                    server_type = MCPServerType.from_string(server_name)
                    servers_to_start.append(server_type)
                except ValueError:
                    logger.warning(f"Unknown server type: {server_name}")

        # Start the servers
        started_servers = []

        for server_type in servers_to_start:
            logger.info(f"Starting server: {server_type}")

            success, process_id = mcp_server_manager.start_server(
                server_type=server_type,
                wait=True,
                timeout=30
            )

            if success:
                logger.info(f"Started server {server_type} (PID: {process_id})")
                started_servers.append(server_type)
            else:
                logger.error(f"Failed to start server {server_type}")

        # Skip agent servers for now
        logger.info("Skipping agent servers for now")

    # Run the game
    try:
        run_dynamic_game(
            neo4j_manager=neo4j_manager,
            llm_client=llm_client,
            tool_registry=tool_registry,
            agent_registry=agents
        )
    finally:
        # Stop MCP servers if they were started
        if args.start_mcp_servers:
            logger.info("Stopping MCP servers...")
            mcp_server_manager.stop_all_servers()
            logger.info("All MCP servers stopped")


if __name__ == "__main__":
    main()
