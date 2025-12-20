#!/usr/bin/env python3
"""
Run MCP servers manually.

This script runs the MCP servers manually for testing.
"""

import argparse
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the examples directory to the Python path
examples_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples"
)
sys.path.append(examples_path)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run MCP servers manually")

    parser.add_argument(
        "--server",
        type=str,
        choices=["knowledge", "agent", "all"],
        default="all",
        help="Server to run (default: all)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to run the server on (default: 8002 for knowledge, 8001 for agent)",
    )

    parser.add_argument(
        "--transport",
        type=str,
        choices=["sse", "ws"],
        default="sse",
        help="Transport to use (default: sse)",
    )

    return parser.parse_args()


def run_knowledge_server(port=8002, transport="sse"):
    """Run the Knowledge Resource server."""
    print(f"Running Knowledge Resource server on port {port} with {transport} transport...")

    from examples.mcp.knowledge_resource_server import mcp

    mcp.settings.port = port
    mcp.run(transport)


def run_agent_tool_server(port=8001, transport="sse"):
    """Run the Agent Tool server."""
    print(f"Running Agent Tool server on port {port} with {transport} transport...")

    from examples.mcp.agent_tool_server import mcp

    mcp.settings.port = port
    mcp.run(transport)


def main():
    """Main entry point."""
    args = parse_args()

    if args.server == "knowledge":
        port = args.port if args.port is not None else 8002
        run_knowledge_server(port=port, transport=args.transport)
    elif args.server == "agent":
        port = args.port if args.port is not None else 8001
        run_agent_tool_server(port=port, transport=args.transport)
    elif args.server == "all":
        print("Cannot run both servers in the same process.")
        print("Please run each server in a separate terminal:")
        print("\npython3 tests/integration/run_mcp_servers.py --server knowledge")
        print("python3 tests/integration/run_mcp_servers.py --server agent\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
