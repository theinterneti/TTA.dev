"""TTA.dev MCP Server entry point.

Allows running as: python -m tta_dev_primitives.mcp_server
"""

from tta_dev_primitives.mcp_server.server import run_server

if __name__ == "__main__":
    run_server()
