# Jaeger MCP Server

This document provides an overview of the Jaeger MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To provide access to your Jaeger instance for distributed tracing.
*   **Key Features:**
    *   **Trace Discovery:** Find and retrieve traces and spans.
    *   **Service and Operation Discovery:** Get a list of services and operations from your Jaeger instance.
    *   **gRPC and HTTP Support:** Supports both gRPC and HTTP APIs for interacting with Jaeger.

## Usage by TTA.dev Agents

TTA.dev agents use the Jaeger MCP server to:

*   **Analyze Distributed Traces:** Analyze distributed traces to understand the flow of requests through a system.
*   **Troubleshoot Performance Issues:** Troubleshoot performance issues by identifying bottlenecks and latency in your services.
*   **Gain Insights into System Behavior:** Gain insights into the behavior of your system by exploring the relationships between services and operations.

## Developer Use Cases

As a developer, you can use the Jaeger MCP server to:

*   **Enable Your AI Agents to Interact with Jaeger:** Enable your AI agents to interact with Jaeger to perform a wide range of tasks.
*   **Build Jaeger-Aware Applications:** Build applications that are aware of your Jaeger instance and can interact with it.
*   **Automate Your Tracing Workflows:** Automate your tracing workflows by creating AI agents that can interact with the Jaeger API.

## Example

Here's an example of how you might configure the Jaeger MCP server in your Claude Desktop app:

```json
{
  "mcpServers": {
    "jaeger-mcp-server": {
      "command": "npx",
      "args": ["-y", "jaeger-mcp-server"],
      "env": {
        "JAEGER_URL": "<YOUR_JAEGER_HTTP_OR_GRPC_API_URL>"
      }
    }
  }
}
