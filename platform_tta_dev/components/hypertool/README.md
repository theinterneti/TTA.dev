# Hypertool Component

**Component Type:** MCP Server Orchestration + Workflow/Persona Foundation
**Status:** Migrated from `platform/dev/agentic/hypertool/`
**Migration Date:** 2025-11-16

## Overview

Hypertool is the foundational component for TTA.dev platform, providing:

- **MCP Server Configuration**: Centralized configuration for all Model Context Protocol servers
- **Workflow Primitives**: Markdown-based prompt templates with trace metadata
- **Chatmode Definitions**: Persona-driven conversation modes
- **Persona Library**: Shared persona definitions for all platform tools

## Architecture

```text
hypertool/
├── mcp/                    # MCP Server configurations
│   ├── config.json         # Primary MCP server registry
│   └── README.md           # MCP configuration documentation
├── workflows/              # Markdown-as-code workflow definitions
│   ├── prompts/            # .prompt.md files with frontmatter
│   ├── chatmodes/          # .chatmode.md persona definitions
│   ├── scenarios/          # .scenario.md test scenarios
│   └── README.md           # Workflow DSL documentation
├── personas/               # Persona definition library
│   ├── personas/           # Individual persona .md files
│   ├── persona-overrides.json
│   └── README.md           # Persona schema documentation
├── integrations/           # Integration adapters
│   ├── tta_app/            # TTA application integration hooks
│   ├── platform/           # Platform component integrations
│   ├── external/           # External tool adapters (VS Code, etc.)
│   └── README.md
└── observability/          # Hypertool-specific observability
    ├── traces/             # Trace configurations
    ├── metrics/            # Metric definitions
    ├── logs/               # Log schemas
    └── README.md           # Observability integration guide
```

## Key Files

### MCP Configuration

- `mcp/config.json` - MCP server registry with all server definitions
  - **Symlinked From Root**: `/.mcp.hypertool.json` → `platform_tta_dev/components/hypertool/mcp/config.json`
  - **Enabled Servers**: context7, playwright, github, sequential-thinking, gitmcp, neo4j, postgresql
  - **Disabled Servers**: grafana, notebooklm

### Workflows

- `workflows/chatmodes/*.chatmode.md` - Persona-driven conversation modes
  - architect.chatmode.md
  - backend-dev.chatmode.md
  - backend-implementer.chatmode.md
  - devops.chatmode.md
  - frontend-dev.chatmode.md
  - qa-engineer.chatmode.md
  - safety-architect.chatmode.md

- `workflows/prompts/*.prompt.md` - Reusable prompt templates
  - bug-fix.prompt.md
  - component-promotion.prompt.md
  - feature-implementation.prompt.md
  - quality-gate-fix.prompt.md
  - test-coverage-improvement.prompt.md
  - augster-axiomatic-workflow.prompt.md

### Personas

- `personas/personas/*.md` - Core persona definitions
  - DevOpsGuardian.md
  - PrimitiveArchitect.md
  - QualityGuardian.md

## Dependencies

### Platform Dependencies

- **Core**: None (foundation component)
- **Used By**: All other platform components rely on hypertool's MCP/persona/workflow definitions

### External Dependencies

- **Runtime**: Node.js (npx for MCP servers), Docker (containerized MCP servers)
- **MCP Servers**:
  - `@upstash/context7-mcp@latest`
  - `@playwright/mcp@latest`
  - `ghcr.io/github/github-mcp-server`
  - `@modelcontextprotocol/server-sequential-thinking`
  - `gitmcp`
  - `ghcr.io/grafana/mcp-grafana:latest` (disabled)
  - `notebooklm-mcp` (disabled)
  - `mcp-neo4j-cypher@0.3.0`
  - `@executeautomation/database-server`

## Observability Integration

### Trace Configuration

- **Workflow Traces**: All `.prompt.md` and `.chatmode.md` files include frontmatter with trace metadata
- **MCP Call Traces**: Instrumenting MCP server invocations (pending implementation)
- **Persona Activation Traces**: Track when personas are loaded/activated

### Metrics

- MCP server response times
- Workflow execution counts
- Persona activation frequency

### Logs

- MCP server connection/disconnection events
- Workflow validation errors
- Persona loading failures

## Usage

### MCP Server Configuration

The `.mcp.hypertool.json` symlink at repository root points to `mcp/config.json`:

```bash
# MCP servers are automatically loaded by Copilot/Cline via symlink
# Configuration file location: /platform_tta_dev/components/hypertool/mcp/config.json
```

### Workflow Invocation

Workflows are invoked via chatmode activation or direct prompt loading:

```markdown
# In Copilot/Cline chat
/chatmode architect
# Loads: platform_tta_dev/components/hypertool/workflows/chatmodes/architect.chatmode.md
```

### Persona Loading

Personas are referenced by other platform components:

```python
# Example persona reference
persona_path = "platform_tta_dev/components/hypertool/personas/personas/QualityGuardian.md"
```

## Migration Notes

### Source Locations

- **Original MCP Config**: `platform/dev/agentic/hypertool/config.json`
- **Original Workflows**: `platform/dev/agentic/augment/{chatmodes,workflows}/`
- **Original Personas**: `platform/dev/agentic/personas/personas/`

### Symlink Updates

- ✅ `.mcp.hypertool.json` → `platform_tta_dev/components/hypertool/mcp/config.json`

### Validation Checklist

- [ ] MCP servers connect successfully
- [ ] Chatmodes load in Copilot/Cline
- [ ] Workflow prompts resolve correctly
- [ ] Persona files accessible to other components
- [ ] Trace metadata validates against schema

## Next Steps

1. **Immediate**: Verify all MCP servers connect with updated symlink
2. **Phase 4**: Migrate serena component (depends on hypertool personas)
3. **Phase 5**: Add observability instrumentation for MCP calls
4. **Phase 6**: Document workflow DSL schema with trace requirements


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Hypertool/Readme]]
