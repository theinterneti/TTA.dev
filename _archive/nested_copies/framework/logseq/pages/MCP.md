# MCP

**Model Context Protocol - Standard for AI tool integration.**

## Overview

MCP (Model Context Protocol) is an open standard for connecting AI applications to external data sources and tools. TTA.dev integrates with multiple MCP servers for enhanced agent capabilities.

## TTA.dev MCP Integration

### Available MCP Servers
- [[MCP Servers]] - Complete MCP server registry
- [[TTA.dev/MCP/Context7]] - Library documentation server
- [[TTA.dev/MCP/AI Toolkit]] - Agent development guidance
- [[TTA.dev/MCP/Grafana]] - Observability queries
- [[TTA.dev/MCP/Pylance]] - Python development tools

### Configuration
- **Location:** `.vscode/mcp-settings.json`
- **Toolsets:** `.vscode/copilot-toolsets.jsonc`
- **Documentation:** [[MCP_SERVERS]] file

## MCP in TTA.dev

### Agent Context Integration
- [[TTA.dev/Packages/universal-agent-context]] - Agent coordination
- [[TTA.dev/Guides/MCP Integration Patterns]] - Integration guide

### Custom MCP Servers
- [[TTA.dev/MCP/Development]] - Building custom servers
- [[TTA.dev/Examples/MCP Server]] - Example implementation

## Key Concepts

**MCP provides:**
- **Tools**: Functions AI can call
- **Resources**: Data sources AI can query
- **Prompts**: Reusable prompt templates
- **Context**: Shared context between tools

## Related Pages

- [[MCP Servers]] - Server registry and usage
- [[MCP_SERVERS]] - Main documentation file
- [[TTA.dev/Guides/Agent Development]] - Agent patterns
- [[Contributors]] - Contributing to MCP integration

## External Resources

- Official: <https://modelcontextprotocol.io>
- Spec: <https://spec.modelcontextprotocol.io>
- SDK: <https://github.com/modelcontextprotocol/sdk>

## Tags

integration:: mcp
protocol:: standard

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Mcp]]
