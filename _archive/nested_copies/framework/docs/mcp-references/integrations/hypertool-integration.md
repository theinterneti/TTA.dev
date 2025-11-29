# Hypertool Integration Guide

This guide provides a starting point for programmatically integrating with the Hypertool MCP server.

## Overview

The Hypertool MCP server allows you to dynamically expose tools from proxied MCP servers based on an Agent Persona. Integrating with this server allows you to build tools that can create and manage task-specific toolsets, providing a more focused and effective AI assistant.

## Connecting to the Server

To connect to the Hypertool MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the Hypertool server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Creating a Toolset

Here's a conceptual example of how you might use a Python-based MCP client to create a toolset using the Hypertool MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(
    server_command="npx -y @toolprint/hypertool-mcp mcp run --mcp-config .mcp.hypertool.json"
)

# 2. Connect to the server
client.connect()

# 3. Call the create_toolset tool
result = client.call_tool(
    "create_toolset",
    {
        "name": "coding",
        "tools": ["git.status", "git.commit", "docker.build", "docker.run"],
    },
)

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [Hypertool MCP Server Documentation](https://github.com/toolprint/hypertool-mcp)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)
