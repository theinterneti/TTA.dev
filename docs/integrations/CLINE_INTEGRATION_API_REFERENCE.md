# Cline Integration API Reference

**Quick reference for TTA.dev's Cline integration features**

---

## Core Components

### Agent Context System

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Agent Instruction System** | Context-aware guidance | `logseq/pages/TTA.dev___Agent Instruction System.md` |
| **Setup Automation** | Environment configuration | `scripts/setup/cline-agent.sh` |
| **MCP Integration** | Server ecosystem | `.vscode/settings.json` |
| **Custom Instructions** | TTA.dev guidance | `.cline/instructions.md` |

## Setup Commands

### Quick Setup

```bash
# Auto-setup with context detection
./scripts/setup-agent-workspace.sh

# Cline-specific configuration
./scripts/setup/cline-agent.sh

# Verify setup
cline "What packages are in this TTA.dev monorepo?"
```

### Environment Variables

```bash
export CLINE_API_PROVIDER=openrouter
export CLINE_API_KEY=sk-or-v1-your-key
export TTA_DEV_CONTEXT=cline-local
```

## MCP Servers

### Available Servers

- **Context7** - Documentation search and lookup
- **Sequential Thinking** - Multi-step reasoning
- **Serena** - Code symbol analysis
- **Redis MCP** - Database operations
- **Neo4j MCP** - Graph database operations
- **Playwright** - Web application testing

### Configuration

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-context7"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

## Usage Patterns

### Agent Handoffs

```python
# Copilot Planning → Cline Implementation
@workspace #tta-cline
"Implement adaptive retry with learning from execution patterns"
```

### Role-Based Assistance

```python
@workspace #tta-package-dev     # Core development
@workspace #tta-observability   # Monitoring and metrics
@workspace #tta-mcp-integration # Server coordination
@workspace #tta-testing         # Quality assurance
```

### TTA.dev Patterns

```python
# Always use TTA.dev patterns with Cline
@cline "Implement a CachePrimitive with TTL and LRU eviction using TTA.dev primitives"

# Reference existing patterns
@cline "Follow the same patterns used in RetryPrimitive and FallbackPrimitive"
```

## Context Detection

### Environment Matrix

| Context | Tools Available | Setup |
|---------|----------------|-------|
| **Cline Extension** | Enhanced MCP, VS Code API | `scripts/setup/cline-agent.sh` |
| **VS Code Copilot** | Standard MCP, toolsets | `scripts/setup/vscode-agent.sh` |
| **GitHub Actions** | CLI tools, CI/CD | `scripts/setup/github-actions-agent.sh` |

## Troubleshooting

### Common Issues

```bash
# Cline not reading instructions
cline "What package manager does this project use?"
# Expected: "uv" (not pip/poetry)

# Check MCP configuration
cat ~/.config/mcp/mcp_settings.json

# Verify Node.js
node --version && npx --version
```

### Performance

```bash
# Test Cline integration
cline "List all Python files in platform/primitives/src/"

# Test MCP integration
cline "Use Context7 to search for documentation about primitives"
```

## Best Practices

### Context Management

- Provide specific file paths: `platform/primitives/src/`
- Use role-specific toolsets: `@workspace #tta-package-dev`
- Reference existing patterns: `Follow RetryPrimitive patterns`

### Quality Assurance

- Request 100% test coverage: `Add tests with pytest-asyncio`
- Follow TTA.dev standards: `Use str | None for type hints`
- Include comprehensive documentation: `Add docstrings and examples`

## Future Primitives

### Planned Components

```python
# LogseqContextLoader - Auto-load historical context
class LogseqContextLoaderPrimitive(WorkflowPrimitive[dict, dict]):
    """Loads relevant context from Logseq knowledge base."""

# ClineEnvSensor - Runtime environment sensing
class ClineEnvSensorPrimitive(WorkflowPrimitive[dict, dict]):
    """Captures VS Code/MCP environment state."""

# Adaptive Strategy Integration - Context-aware strategies
class AdaptiveStrategyIntegration(WorkflowPrimitive[dict, dict]):
    """Integrates learned strategies with Cline workflows."""
```

## Quick Reference

### File Locations

- **Main Guide:** `docs/integrations/CLINE_CONTEXT_INTEGRATION_GUIDE.md`
- **Agent System:** `logseq/pages/TTA.dev___Agent Instruction System.md`
- **Setup Script:** `scripts/setup/cline-agent.sh`
- **Custom Instructions:** `.cline/instructions.md`
- **MCP Config:** `.vscode/settings.json`

### Status Indicators

- **✅ Implemented:** Core integration, setup automation, MCP servers
- **⏳ Planned:** LogseqContextLoader, ClineEnvSensor primitives
- **🔄 Active:** Multi-agent workflows, context sharing

---

**Version:** 1.0
**Last Updated:** November 8, 2025
**Related:** [CLINE_CONTEXT_INTEGRATION_GUIDE.md](./CLINE_CONTEXT_INTEGRATION_GUIDE.md)
