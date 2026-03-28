"""TTA.dev MCP Server entry point.

Allows running as: python -m ttadev.primitives.mcp_server
"""

from ttadev.primitives.mcp_server.server import run_server

if __name__ == "__main__":
    run_server()
