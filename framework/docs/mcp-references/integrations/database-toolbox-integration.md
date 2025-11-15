# MCP Toolbox for Databases Integration Guide

This guide provides a starting point for programmatically integrating with the MCP Toolbox for Databases.

## Overview

The MCP Toolbox for Databases provides a suite of tools for interacting with Google Cloud databases, such as BigQuery, using natural language. Integrating with this server allows you to build tools that can query and analyze data in your Google Cloud databases.

## Connecting to the Server

To connect to the MCP Toolbox for Databases, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the MCP Toolbox for Databases.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Listing BigQuery Datasets

Here's a conceptual example of how you might use a Python-based MCP client to list the available datasets in a BigQuery project:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(
    server_command="toolbox --prebuilt bigquery --stdio",
    env={
        "BIGQUERY_PROJECT": "your-gcp-project-id",
        "BIGQUERY_LOCATION": "your-gcp-region",
    },
)

# 2. Connect to the server
client.connect()

# 3. Call the list_datasets tool
result = client.call_tool("list_datasets", {})

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [MCP Toolbox for Databases Documentation](https://googleapis.github.io/genai-toolbox/getting-started/)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)
