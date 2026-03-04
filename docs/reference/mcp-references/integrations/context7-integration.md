# Context7 Integration Guide

This guide provides a starting point for programmatically integrating with the Context7 MCP server.

## Overview

The Context7 MCP server provides access to up-to-date documentation for a wide range of libraries and frameworks. Integrating with this server allows you to build tools that can automatically fetch documentation and use it to inform their work.

## Connecting to the Server

To connect to the Context7 MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the Context7 server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Getting Documentation for a Library

Here's a conceptual example of how you might use a Python-based MCP client to get documentation for a library using the Context7 MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(server_command="npx -y @upstash/context7-mcp@latest")

# 2. Connect to the server
client.connect()

# 3. Call the resolve-library-id tool
library_id_result = client.call_tool(
    "resolve-library-id",
    {"libraryName": "react"},
)

# 4. Call the get-library-docs tool
docs_result = client.call_tool(
    "get-library-docs",
    {
        "context7CompatibleLibraryID": library_id_result["id"],
        "topic": "hooks",
    },
)

print(docs_result)

# 5. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [Context7 MCP Server Documentation](https://github.com/upstash/context7-mcp)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Integrations/Context7-integration]]
