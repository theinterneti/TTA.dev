# Grafana MCP Server

This document provides an overview of the Grafana MCP server and how it is used by TTA.dev agents.

## Purpose and Capabilities

*   **Primary Function:** To provide access to your Grafana instance and the surrounding ecosystem.
*   **Key Features:**
    *   **Dashboard Management:** Search, retrieve, update, and create Grafana dashboards.
    *   **Datasource Interaction:** List and fetch information about datasources, and query Prometheus and Loki datasources.
    *   **Incident Management:** Search, create, and update incidents in Grafana Incident.
    *   **Alerting and OnCall:** View alert rules, contact points, and manage on-call schedules.
    *   **Administration:** List teams and users in your Grafana organization.

## Usage by TTA.dev Agents

TTA.dev agents use the Grafana MCP server to:

*   **Monitor and Analyze Data:** Monitor and analyze data from your Grafana instance to gain insights and troubleshoot issues.
*   **Automate Grafana Operations:** Automate common Grafana operations, such as creating dashboards and managing incidents.
*   **Integrate with Other Tools:** Integrate with other tools and services to create powerful and flexible solutions.

## Developer Use Cases

As a developer, you can use the Grafana MCP server to:

*   **Enable Your AI Agents to Interact with Grafana:** Enable your AI agents to interact with Grafana to perform a wide range of tasks.
*   **Build Grafana-Aware Applications:** Build applications that are aware of your Grafana instance and can interact with it.
*   **Automate Your Grafana Workflows:** Automate your Grafana workflows by creating AI agents that can interact with the Grafana API.

## Example

Here's an example of how you might configure the Grafana MCP server to connect to a local Grafana instance:

```json
{
  "mcpServers": {
    "grafana": {
      "command": "mcp-grafana",
      "args": [],
      "env": {
        "GRAFANA_URL": "http://localhost:3000",
        "GRAFANA_SERVICE_ACCOUNT_TOKEN": "<your service account token>"
      }
    }
  }
}


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Mcp-references/Grafana]]
