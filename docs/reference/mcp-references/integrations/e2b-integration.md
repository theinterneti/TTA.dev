# E2B Integration Guide

This guide provides a starting point for programmatically integrating with the E2B MCP server.

## Overview

The E2B MCP server provides a secure and isolated environment for executing code. Integrating with this server allows you to build tools that can safely run untrusted code, test code snippets, and execute external commands.

## Connecting to the Server

To connect to the E2B MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the E2B server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Executing a Python Script

Here's a conceptual example of how you might use a Python-based MCP client to execute a Python script using the E2B MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(
    server_command="npx -y @e2b/mcp-server",
    env={"E2B_API_KEY": "your_e2b_api_key"},
)

# 2. Connect to the server
client.connect()

# 3. Call the execute_script tool
result = client.call_tool(
    "execute_script",
    {
        "language": "python",
        "code": "print('Hello, world!')",
    },
)

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [E2B MCP Server Documentation](https://github.com/e2b-dev/mcp-server)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Integrations/E2b-integration]]
