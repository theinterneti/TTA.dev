# Prometheus Integration Guide

This guide provides a starting point for programmatically integrating with the Prometheus MCP server.

## Overview

The Prometheus MCP server provides a set of tools for interacting with your Prometheus instance. Integrating with this server allows you to build tools that can query and analyze your Prometheus metrics.

## Connecting to the Server

To connect to the Prometheus MCP server, you'll need to use an MCP client library that is compatible with your programming language. The specific details of how you connect will depend on the library you are using, but the general process is as follows:

1.  **Instantiate an MCP Client:** Create an instance of the MCP client, providing it with the necessary configuration to connect to the Prometheus server.
2.  **Connect to the Server:** Establish a connection to the server.
3.  **Call Tools:** Once connected, you can call the tools provided by the server.

## Example: Executing a PromQL Query

Here's a conceptual example of how you might use a Python-based MCP client to execute a PromQL query using the Prometheus MCP server:

```python
from mcp_client import MCPClient

# 1. Instantiate the MCP client
client = MCPClient(
    server_command="docker run -i --rm -e PROMETHEUS_URL ghcr.io/pab1it0/prometheus-mcp-server:latest",
    env={"PROMETHEUS_URL": "http://localhost:9090"},
)

# 2. Connect to the server
client.connect()

# 3. Call the execute_query tool
result = client.call_tool(
    "execute_query",
    {"query": "up"},
)

print(result)

# 4. Disconnect from the server
client.disconnect()
```

## Further Reading

*   [Prometheus MCP Server Documentation](https://github.com/pab1it0/prometheus-mcp-server)
*   [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Mcp-references/Integrations/Prometheus-integration]]
