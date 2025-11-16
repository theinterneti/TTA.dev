# DevContext Integration Guide

This guide provides a starting point for programmatically integrating with the DevContext MCP server.

## Overview

The DevContext MCP server provides continuous, project-centric context awareness. Integrating with this server allows you to build tools that can understand and adapt to your development patterns, providing highly relevant context exactly when you need it.

## Connecting to the Server

To connect to the DevContext MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the DevContext server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Initializing a Conversation

Here's a conceptual example of how you might use a Python-based MCP client to initialize a conversation using the DevContext MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(
    server_command="npx -y devcontext@latest",
    env={
        "TURSO_DATABASE_URL": "your-turso-database-url",
        "TURSO_AUTH_TOKEN": "your-turso-auth-token",
    },
)

# 2. Connect to the server
client.connect()

# 3. Call the initialize_conversation_context tool
result = client.call_tool(
    "initialize_conversation_context",
    {"initialQuery": "How do I add a new feature?"},
)

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [DevContext MCP Server Documentation](https://github.com/aiurda/devcontext)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)
