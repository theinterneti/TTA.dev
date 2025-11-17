# Cline Context Integration Implementation Guide

**Comprehensive documentation for TTA.dev's Cline integration system**

---

## Overview

TTA.dev provides comprehensive integration with Cline (Claude-powered VS Code extension) through a dual-strategy context management system. This integration enables seamless agent coordination, enhanced MCP server connectivity, and intelligent context sharing between different agent environments.

## Architecture

### Core Integration Components

1. **Agent Instruction System** - Context-aware guidance for all agent types
2. **Setup Automation Scripts** - Environment-specific configuration
3. **MCP Server Integration** - Shared infrastructure between Cline and TTA.dev
4. **Context Detection** - Automatic environment recognition and adaptation

### Current Implementation Status

- ✅ **Agent Instruction System** - Complete with role-based guidance
- ✅ **Setup Automation** - Scripts for all contexts (VS Code, Cline, GitHub Actions)
- ✅ **MCP Integration** - Full server ecosystem available
- ✅ **Context Detection** - Automatic environment recognition
- ⏳ **LogseqContextLoader** - Planned primitive for historical context loading
- ⏳ **ClineEnvSensor** - Planned primitive for runtime environment sensing

## Cline Integration Features

### 1. Agent Context Support

**Context Detection Matrix:**

| Environment | Available Tools | Configuration | Setup Script |
|-------------|-----------------|---------------|--------------|
| **Cline Extension** | Enhanced MCP, VS Code API | `.cline/instructions.md` | `scripts/setup/cline-agent.sh` |
| **VS Code Copilot** | Standard MCP, toolsets | `.github/copilot-instructions.md` | `scripts/setup/vscode-agent.sh` |
| **GitHub Actions** | CLI tools, CI/CD | `.github/copilot-instructions.md` | `scripts/setup/github-actions-agent.sh` |

### 2. MCP Server Ecosystem

**Available MCP Servers:**


- **Context7** - Documentation lookup and search
- **Sequential Thinking** - Multi-step reasoning
- **Serena** - Code symbol analysis
- **Redis MCP** - Database operations
- **Neo4j MCP** - Graph database operations
- **Playwright** - Web application testing

**Configuration Location:** `.vscode/settings.json`

### 3. Enhanced Agent Coordination

**Role-Based Agent System:**

```python
# Cline Extension with Enhanced Context
@workspace #tta-agent-dev
Design multi-agent workflow for code generation with validation

# Specialized toolsets available:
# #tta-package-dev - Core development
# #tta-observability - Monitoring and metrics
# #tta-mcp-integration - Server coordination
# #tta-testing - Quality assurance
```

## Setup and Configuration

### Automatic Setup


**Master Setup Script:**

```bash
# Auto-detect environment and configure Cline integration
./scripts/setup-agent-workspace.sh
```


**Context-Specific Setup:**

```bash
# Cline-specific configuration
./scripts/setup/cline-agent.sh

# Verify setup
cline "What packages are in this TTA.dev monorepo?"
```

### Manual Configuration

**1. Cline Custom Instructions**

TTA.dev provides Cline-specific instructions via `.cline/instructions.md`:

```markdown
# TTA.dev Context for Cline
- Package Manager: `uv` (NOT pip/poetry)
- Python Version: 3.11+ required
- Type Hints: Use `str | None` NOT `Optional[str]`
- Primitives: Use composition with `>>` and `|` operators
- Testing: 100% coverage required, use `MockPrimitive`
```


**2. MCP Server Configuration**

Cline automatically detects TTA.dev MCP servers:

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

**3. Environment Variables**

```bash
# Required for Cline integration
export CLINE_API_PROVIDER=openrouter
export CLINE_API_KEY=sk-or-v1-your-key
export TTA_DEV_CONTEXT=cline-local
```

## Usage Patterns


### 1. Cline-Specific Workflows

**Code Development with TTA.dev Primitives:**

```python

# Ask Cline to implement using TTA.dev patterns
@cline "Implement a CachePrimitive wrapper for LLM calls with TTL and LRU eviction"
```

**Multi-File Refactoring:**


```python
# Cline can handle complex refactoring across multiple files
@cline "Refactor all retry patterns in tta-dev-primitives to use RetryPrimitive"
```

**MCP Server Integration:**

```python

# Leverage TTA.dev's MCP ecosystem
@cline "Use the Context7 MCP server to find all documentation about CachePrimitive"
```

### 2. Agent Handoff Patterns

**Copilot Planning → Cline Implementation:**

```markdown

User: "@workspace #tta-cline Implement adaptive retry with learning"
↓
Copilot: Plans the adaptive retry architecture
↓
Cline: Implements the primitive with tests and documentation
```

**Cline → Observability Integration:**

```python
@cline "Add Prometheus metrics to track CachePrimitive performance"
# Cline implements with full observability integration
```

## Integration Benefits

### 1. Enhanced Context Awareness

- **Project-Specific Guidance:** Cline understands TTA.dev patterns, package manager, and coding standards
- **Role-Based Assistance:** Different toolsets and guidance based on agent role
- **Context Continuity:** Maintains state across different agent interactions

### 2. MCP Server Advantages

- **Shared Infrastructure:** Same MCP servers available to both Cline and TTA.dev agents
- **Enhanced Capabilities:** Access to Context7, Sequential Thinking, and other specialized servers
- **Unified Configuration:** Single MCP setup serves multiple agent types

### 3. Workflow Optimization

- **Task Persistence:** Cline maintains task state across interruptions
- **Autonomous Execution:** Cline can implement complex multi-step workflows
- **Quality Integration:** Built-in adherence to TTA.dev quality standards

## Examples and Use Cases


### 1. Package Development

```python
# Cline implements new primitive following TTA.dev patterns
@cline "Create a new RouterPrimitive that routes based on LLM response time and accuracy"
```

**Expected Implementation:**

```python
from tta_dev_primitives import WorkflowPrimitive
from tta_dev_primitives.core import RouterPrimitive

class LatencyRouterPrimitive(RouterPrimitive):
    """Routes based on latency and accuracy metrics."""
    def __init__(self):
        super().__init__()
        self.metrics = {}
```

### 2. Observability Integration

```python
# Add monitoring to existing primitives
@cline "Add OpenTelemetry tracing to all adaptive primitives"
```

### 3. Documentation Generation


```python
# Generate comprehensive documentation
@cline "Create API documentation for all primitives in tta-dev-primitives with usage examples"
```

## Future Enhancements

### Planned Primitives

**1. LogseqContextLoader Primitive**

```python

class LogseqContextLoaderPrimitive(WorkflowPrimitive[dict, dict]):
    """Automatically loads historical context from Logseq knowledge base."""

    async def execute(self, context: WorkflowContext, request: dict) -> dict:
        # Load relevant historical context
        # Merge with current request
        # Return enhanced context
        pass
```

**2. ClineEnvSensor Primitive**

```python

class ClineEnvSensorPrimitive(WorkflowPrimitive[dict, dict]):
    """Captures runtime environment state for Cline workflows."""

    async def execute(self, context: WorkflowContext, request: dict) -> dict:
        # Detect VS Code extension state
        # Capture MCP server availability
        # Monitor resource usage
        # Return environment snapshot
        pass
```

**3. Adaptive Strategy Integration**

```python
class AdaptiveStrategyIntegration(WorkflowPrimitive[dict, dict]):
    """Integrates learned strategies with Cline context."""


    async def execute(self, context: WorkflowContext, request: dict) -> dict:
        # Load strategies from logseq/pages/ClineStrategies
        # Apply context-appropriate strategies
        # Persist new learnings
        pass
```

## Troubleshooting


### Common Issues

**1. Cline Not Reading Custom Instructions**

```bash
# Verify .cline/instructions.md exists
ls -la .cline/instructions.md

# Test with simple question

cline "What package manager does this project use?"
```

**2. MCP Servers Not Available**

```bash
# Check MCP configuration
cat ~/.config/mcp/mcp_settings.json

# Verify Node.js installation
node --version

npx --version
```

**3. Environment Detection Issues**


```bash
# Run setup script with debug output
./scripts/setup/cline-agent.sh --verbose

# Check environment variables
env | grep CLINE
```

### Performance Optimization

**1. Context Loading**

- Cline automatically caches context for faster subsequent queries
- Large projects may require explicit context specification
- Use `exclude` patterns in `.gitignore` to limit file scanning

**2. MCP Server Efficiency**

- Start with essential servers (Context7, Sequential Thinking)
- Add specialized servers as needed
- Monitor server performance with `mcp logs`

## Best Practices

### 1. Context Management

```python
# Provide clear, specific context
@cline "In platform/primitives/src/tta_dev_primitives/performance/, implement a new cache primitive"

# Use role-specific toolsets
@workspace #tta-package-dev  # For development tasks
@workspace #tta-observability  # For monitoring tasks
```

### 2. Error Handling

```python
# Let Cline handle complexity
@cline "Implement error handling with proper exception types and recovery patterns"

# Reference existing patterns
@cline "Follow the same patterns used in RetryPrimitive and FallbackPrimitive"
```

### 3. Quality Assurance

```python
# Require comprehensive testing
@cline "Add 100% test coverage with pytest-asyncio for this new primitive"

# Follow TTA.dev standards
@cline "Use str | None for type hints and include full docstrings"
```

## Integration Testing

### Validation Checklist

- [ ] Cline reads custom instructions correctly
- [ ] MCP servers are accessible and functional
- [ ] Context detection works across environments
- [ ] Agent handoffs preserve state and context
- [ ] Setup scripts run without errors

- [ ] Documentation remains synchronized

### Test Commands

```bash

# Test Cline configuration
cline "List all Python files in platform/primitives/src/"

# Test MCP integration
cline "Use Context7 to search for documentation about primitives"


# Test multi-agent workflow
cline "Implement a simple primitive and add tests following TTA.dev patterns"
```

## Related Documentation

### Core Integration

- [TTA.dev Agent Instruction System](./TTA.dev___Agent Instruction System.md) - Complete agent guidance
- [MCP Servers Guide](./MCP_SERVERS.md) - Server ecosystem documentation
- [Setup Scripts](./scripts/) - Automation and configuration

### Cline-Specific

- [Cline CLI Configuration](./CLINE_CLI_CUSTOM_INSTRUCTIONS.md) - CLI setup guide
- [Cline Integration Guide](./CLINE_INTEGRATION_GUIDE.md) - Detailed integration walkthrough
- [Cline Troubleshooting](./CLINE_CLI_TROUBLESHOOTING.md) - Common issues and solutions

### Development Patterns

- [TTA Primitives/CachePrimitive] - Cache primitive documentation
- [AGENTS.md] - Main agent entry point and patterns
- [Package-Specific AGENTS.md] - Individual package guidance

---

**Status:** Production Ready (Core Integration)
**Next Phase:** Implement LogseqContextLoader and ClineEnvSensor primitives
**Last Updated:** November 8, 2025
**Integration Version:** 1.0

## Summary

TTA.dev's Cline integration provides a comprehensive agent coordination system with:

- **✅ Complete Integration:** Full Cline support with custom instructions and MCP servers
- **✅ Automated Setup:** Scripts for seamless environment configuration
- **✅ Enhanced Workflows:** Multi-agent coordination with context preservation
- **⏳ Advanced Primitives:** LogseqContextLoader and ClineEnvSensor planned for future implementation

The integration enables Cline to work seamlessly within the TTA.dev ecosystem while maintaining the project's quality standards and development patterns.
