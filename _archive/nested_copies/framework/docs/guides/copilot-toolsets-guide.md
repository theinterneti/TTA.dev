# TTA.dev Copilot Toolsets Guide

## Overview

TTA.dev includes pre-configured **Copilot toolsets** to optimize AI-assisted development. These toolsets solve the problem of having too many tools enabled (130+), which degrades Copilot performance.

## What are Toolsets?

Toolsets are curated collections of Copilot tools organized by workflow. Instead of enabling all 130 tools, you activate only the tools relevant to your current task.

**Benefits:**
- ✅ **Better Performance** - Fewer tools = faster responses
- ✅ **Focused Context** - Copilot understands your workflow intent
- ✅ **Improved Accuracy** - Less noise in tool selection
- ✅ **Clear Organization** - Tools grouped by use case

## TTA.dev Toolsets

### Core Development

#### `#tta-minimal` (3 tools)
Quick queries and analysis without modifications.
```
Tools: search, problems, think
Use for: Quick questions, understanding code flow
```

#### `#tta-package-dev` (12 tools)
Primary toolset for developing TTA.dev packages.
```
Tools: edit, search, usages, problems, Python env management, tasks
Use for: Working on primitives, observability, keploy packages
Example: "Using #tta-package-dev, add logging to the coordinator"
```

#### `#tta-testing` (10 tools)
Testing and validation workflows.
```
Tools: runTests, testFailure, runTasks, problems, changes
Use for: Running pytest, validation scripts, CI checks
Example: "Using #tta-testing, run all integration tests"
```

### Specialized Workflows

#### `#tta-observability` (12 tools)
Observability integration development.
```
Tools: Prometheus, Loki, dashboard queries, tracing
Use for: tta-observability-integration package work
Example: "Using #tta-observability, query Prometheus for error rates"
```

#### `#tta-agent-dev` (13 tools)
AI agent development and coordination.
```
Tools: AI Toolkit, Context7, agent best practices
Use for: tta-agent-coordination, MCP integration
Example: "Using #tta-agent-dev, implement a new agent handler"
```

#### `#tta-mcp-integration` (10 tools)
MCP server development and integration.
```
Tools: MCP tools, VS Code API, Context7
Use for: Model Context Protocol server work
Example: "Using #tta-mcp-integration, create a new MCP tool"
```

#### `#tta-validation` (12 tools)
Quality validation and script running.
```
Tools: validation scripts, syntax checks, imports analysis
Use for: Running validation/, checking package consistency
Example: "Using #tta-validation, validate all packages"
```

### Workflow Combinations

#### `#tta-pr-review` (10 tools)
Pull request review and validation.
```
Tools: PR operations, tests, changes, problems
Use for: Reviewing PRs, ensuring quality
Example: "Using #tta-pr-review, analyze PR #26"
```

#### `#tta-package-setup` (10 tools)
Creating new packages in the monorepo.
```
Tools: new workspace, editing, Python setup
Use for: Scaffolding new packages
Example: "Using #tta-package-setup, create tta-new-package"
```

#### `#tta-troubleshoot` (11 tools)
Debugging issues across packages.
```
Tools: logs, errors, syntax checks, search
Use for: Investigating bugs, tracing issues
Example: "Using #tta-troubleshoot, find why tests are failing"
```

#### `#tta-docs` (9 tools)
Documentation and knowledge base work.
```
Tools: edit, search, fetch, Context7
Use for: Writing guides, updating docs
Example: "Using #tta-docs, update architecture documentation"
```

### Full Stack (Use Sparingly)

#### `#tta-full-stack` (20 tools)
Complete TTA.dev development stack.
```
⚠️ WARNING: Use only for complex multi-package workflows
Includes: All core tools + observability + AI + GitHub
Use for: Major refactors, multi-package features
Example: "Using #tta-full-stack, implement distributed tracing across all packages"
```

## Usage Examples

### In Copilot Chat

```markdown
# Quick query
@workspace #tta-minimal What does the coordinator class do?

# Package development
@workspace #tta-package-dev Add error handling to the ObservabilityIntegration class

# Testing
@workspace #tta-testing Run all unit tests and show me failures

# Multi-step workflow
@workspace #tta-agent-dev Create a new agent that integrates with Keploy,
then switch to #tta-testing to add test coverage
```

### Combining Toolsets

You can reference multiple toolsets in sequence:
```markdown
@workspace First use #tta-package-dev to implement the feature,
then use #tta-testing to add tests,
finally use #tta-docs to document it
```

## Best Practices

### ✅ DO

- **Start small**: Use `#tta-minimal` or `#tta-package-dev` first
- **Be specific**: Choose the toolset matching your current task
- **Combine sequentially**: Reference different toolsets for multi-step work
- **Keep focused**: Avoid enabling multiple large toolsets simultaneously

### ❌ DON'T

- **Avoid full-stack**: Only use `#tta-full-stack` when absolutely necessary
- **Don't over-combine**: Enabling 5+ toolsets defeats the purpose
- **Skip context**: Don't use `#tta-troubleshoot` for simple questions

## Extending Toolsets

### Adding Custom Tools

When you add MCP servers or VS Code extensions that expose tools:

1. **Identify the tool name** (shown in Copilot tool list)
2. **Edit `.vscode/copilot-toolsets.jsonc`**
3. **Add tool to relevant toolset**

Example - Adding a new database tool:
```jsonc
"tta-data-ops": {
  "tools": [
    "search",
    "problems",
    "dbclient-executeQuery",
    "dbclient-getDatabases",
    "your-new-mcp-tool",  // ← Add here
    "think",
    "todos"
  ],
  "description": "TTA.dev database operations",
  "icon": "database"
}
```

### Creating New Toolsets

For new workflows, create focused toolsets:

```jsonc
"tta-performance": {
  "tools": [
    "search",
    "problems",
    "query_prometheus",
    "fetch_pyroscope_profile",
    "runCommands",
    "think"
  ],
  "description": "Performance analysis and profiling",
  "icon": "dashboard"
}
```

**Guidelines:**
- Keep under 15 tools per toolset
- Include `think` and `todos` for planning
- Use descriptive names prefixed with `tta-`
- Choose meaningful icons

## Architecture Integration

### Synergy with TTA.dev Components

Toolsets complement TTA.dev's architecture:

```
┌─────────────────────────────────────────┐
│  GitHub Copilot with Toolsets           │
│  ├─ #tta-package-dev                    │
│  ├─ #tta-observability                  │
│  └─ #tta-agent-dev                      │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  TTA.dev Primitives                     │
│  (Orchestration Layer)                  │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      ↓           ↓           ↓
┌─────────┐ ┌──────────┐ ┌─────────────┐
│Observ-  │ │Universal │ │  Keploy     │
│ability  │ │Agent     │ │  Framework  │
│Package  │ │Context   │ │             │
└─────────┘ └──────────┘ └─────────────┘
```

### With Custom Instructions

Toolsets work with `.github/copilot-instructions.md`:

```markdown
# .github/copilot-instructions.md
We use tta-dev-primitives for orchestration.
Python packages follow the monorepo structure.
Use uv for dependency management.
```

Copilot applies these instructions **and** uses toolset-specific tools.

### With MCP Servers

MCP servers expose tools that can be included in toolsets:

```jsonc
// MCP server provides: mcp_custom_validator
"tta-validation": {
  "tools": [
    // ... existing tools
    "mcp_custom_validator",  // ← From MCP server
    "think"
  ]
}
```

## Performance Impact

### Before Toolsets (130 tools enabled)
```
⚠️ Warning: 130 tools enabled
- Slower response times
- More tool calling errors
- Reduced accuracy
- Higher token usage
```

### After Toolsets (8-15 tools per workflow)
```
✅ Optimized: 12 tools enabled (#tta-package-dev)
- Faster responses
- Better tool selection
- Improved accuracy
- Lower token usage
```

## Troubleshooting

### "Tool not found" Error

If Copilot can't find a tool in your toolset:

1. Check tool name spelling in `.vscode/copilot-toolsets.jsonc`
2. Verify the tool is available: Copilot menu → "Available Tools"
3. Ensure MCP servers are running if using MCP tools
4. Restart VS Code to reload toolsets

### Toolset Not Applying

If `#toolset-name` isn't working:

1. Verify file location: `.vscode/copilot-toolsets.jsonc`
2. Check JSON syntax (use VS Code validation)
3. Ensure toolset name matches exactly
4. Try reloading: `Ctrl+Shift+P` → "Developer: Reload Window"

### Too Many Tools Still

If performance is still degraded:

1. Check how many tools are in your active toolset
2. Consider splitting into smaller, focused toolsets
3. Remove rarely-used tools from the toolset
4. Use `#tta-minimal` for simple queries

## Version History

- **v1.0** (2025-10-29): Initial TTA.dev toolsets
  - 12 core toolsets for major workflows
  - Aligned with Phase 1 architecture
  - Observability and agent development support

## Contributing

To suggest new toolsets or improvements:

1. Create an issue describing the workflow
2. Propose tools that would help
3. Explain the use case
4. Submit PR with updated `.vscode/copilot-toolsets.jsonc`

## Related Documentation

- [TTA.dev Architecture](../architecture/README.md)
- [Copilot Custom Instructions](../../.github/copilot-instructions.md)
- [Package Development Guide](./package-development.md)
- [VS Code Copilot Docs](https://code.visualstudio.com/docs/copilot/copilot-customization)


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Guides/Copilot-toolsets-guide]]
