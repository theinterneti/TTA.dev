# Jaeger Integration Guide

This guide provides a starting point for programmatically integrating with the Jaeger MCP server.

## Overview

The Jaeger MCP server provides a set of tools for interacting with your Jaeger instance. Integrating with this server allows you to build tools that can query and analyze your distributed tracing data.

## Connecting to the Server

To connect to the Jaeger MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the Jaeger server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Finding Traces

Here's a conceptual example of how you might use a Python-based MCP client to find traces using the Jaeger MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(
    server_command="npx -y jaeger-mcp-server",
    env={"JAEGER_URL": "http://localhost:16686"},
)

# 2. Connect to the server
client.connect()

# 3. Call the find-traces tool
result = client.call_tool(
    "find-traces",
    {
        "serviceName": "my-service",
        "startTimeMin": "2025-11-14T00:00:00Z",
        "startTimeMax": "2025-11-14T23:59:59Z",
    },
)

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [Jaeger MCP Server Documentation](https://github.com/serkan-ozal/jaeger-mcp-server)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Integrations/Jaeger-integration]]
