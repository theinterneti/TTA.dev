# MCP Servers

**Registry of Model Context Protocol servers integrated with TTA.dev.**

## Overview

TTA.dev integrates with multiple MCP servers to provide enhanced capabilities for AI agents and developers.

**Primary documentation:** [[MCP_SERVERS]] (repository root file)

## Available MCP Servers

### Context7 - Library Documentation
- **Purpose:** Query up-to-date library documentation
- **Tools:** `resolve-library-id`, `get-library-docs`
- **Use case:** Learning new libraries, API reference
- **Toolset:** `#tta-agent-dev`

### AI Toolkit - Agent Development
- **Purpose:** Best practices for AI development
- **Tools:** Agent patterns, model guidance, tracing, evaluation
- **Use case:** Building production AI systems
- **Toolset:** `#tta-agent-dev`

### Grafana - Observability
- **Purpose:** Query Prometheus metrics and Loki logs
- **Tools:** Alert rules, dashboards, Prometheus, Loki queries
- **Use case:** Production monitoring and debugging
- **Toolset:** `#tta-observability`

### Pylance - Python Tools
- **Purpose:** Python development assistance
- **Tools:** Syntax checking, import analysis, environment management
- **Use case:** Python development
- **Toolset:** All toolsets (automatic)

### Database Client - SQL Operations
- **Purpose:** Database queries and schema exploration
- **Tools:** Get databases, get tables, execute queries
- **Use case:** Data analysis, schema documentation
- **Toolset:** `#tta-full-stack`

### GitHub PR - Code Review
- **Purpose:** Pull request information and coding agent coordination
- **Tools:** Active PR, open PR, copilot coding agent
- **Use case:** PR reviews, async agent tasks
- **Toolset:** `#tta-pr-review`

## Configuration

### MCP Settings
- **Location:** `~/.config/mcp/mcp_settings.json`
- **VS Code:** Automatically loaded
- **Toolsets:** `.vscode/copilot-toolsets.jsonc`

### Adding Custom Servers
See: [[TTA.dev/Guides/MCP Server Development]]

## Related Pages

- [[MCP]] - MCP protocol overview
- [[MCP_SERVERS]] - Complete MCP documentation
- [[TTA.dev/Guides/Copilot Toolsets]] - Toolset guide
- [[DevOps]] - Infrastructure setup

## External Links

- MCP Spec: <https://modelcontextprotocol.io>
- Repository: [MCP_SERVERS.md](file://../../MCP_SERVERS.md)

## Tags

integration:: mcp-servers
tools:: available


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Mcp servers]]
