# Sequential Thinking Integration Guide

This guide provides a starting point for programmatically integrating with the Sequential Thinking MCP server.

## Overview

The Sequential Thinking MCP server facilitates a structured, progressive thinking process through defined stages. Integrating with this server allows you to build tools that can break down complex problems into sequential thoughts, track the progression of a thinking process, and generate summaries.

## Connecting to the Server

To connect to the Sequential Thinking MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the Sequential Thinking server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Processing a Thought

Here's a conceptual example of how you might use a Python-based MCP client to process a thought using the Sequential Thinking MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(server_command="mcp-sequential-thinking")

# 2. Connect to the server
client.connect()

# 3. Call the process_thought tool
result = client.call_tool(
    "process_thought",
    {
        "thought": "The first step is to define the problem.",
        "thought_number": 1,
        "total_thoughts": 5,
        "next_thought_needed": True,
        "stage": "Problem Definition",
    },
)

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [Sequential Thinking MCP Server Documentation](https://github.com/arben-adm/mcp-sequential-thinking)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)


---
**Logseq:** [[TTA.dev/Docs/Mcp-references/Integrations/Sequential-thinking-integration]]
