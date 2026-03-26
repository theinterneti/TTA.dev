# Hypertool Integration Guide (Historical)

> [!WARNING]
> This guide is historical reference material only.
>
> Do not treat Hypertool as a current TTA.dev dependency. Use the current MCP setup in
> [`.mcp/config.json`](../../../../.mcp/config.json) instead.

This guide preserves an older integration pattern for the retired Hypertool MCP server.

## Historical Overview

The Hypertool MCP server allowed dynamic exposure of tools from proxied MCP servers based on an
agent persona. That approach has been superseded in this repository.

## Historical Connection Pattern

To connect to the Hypertool MCP server, you needed an MCP client library compatible with your
language. The general process was:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the Hypertool server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Historical Example: Creating a Toolset

Here is a conceptual example of the older integration style:

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


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Integrations/Hypertool-integration]]
