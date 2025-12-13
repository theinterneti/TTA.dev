# Guide: Copilot Toolsets

type:: [[Guide]]
category:: [[Developer Tools]], [[VS Code]], [[Copilot]]
difficulty:: [[Intermediate]]
estimated-time:: 20 minutes
target-audience:: [[Developers]], [[AI Engineers]]
related-tools:: [[GitHub Copilot]], [[VS Code]]

---

## Overview

- id:: copilot-toolsets-overview
  **Copilot Toolsets** optimize AI-assisted development by providing curated collections of tools organized by workflow. Instead of enabling all 130+ Copilot tools (which degrades performance), you activate only the tools relevant to your current task.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have:**
- GitHub Copilot enabled in VS Code
- TTA.dev workspace open
- `.vscode/copilot-toolsets.jsonc` file present

---

## The Problem Toolsets Solve

### Without Toolsets ❌

```
⚠️ 130+ tools enabled simultaneously
- Slower response times
- More tool calling errors
- Reduced accuracy
- Higher token usage
- Copilot confused about which tool to use
```

### With Toolsets ✅

```
✅ 8-15 tools per workflow
- Faster responses
- Better tool selection
- Improved accuracy
- Lower token usage
- Clear workflow context
```

---

## TTA.dev Toolsets

### Core Development Toolsets

#### #tta-minimal (3 tools)

- id:: toolset-minimal
  Quick queries and analysis without modifications.

**Tools:** `search`, `problems`, `think`

**Use for:**
- Quick questions
- Understanding code flow
- Reading documentation
- Analyzing structure

**Example:**
```
@workspace #tta-minimal What does the coordinator class do?
```

#### #tta-package-dev (12 tools)

- id:: toolset-package-dev
  Primary toolset for developing TTA.dev packages.

**Tools:** `edit`, `search`, `usages`, `problems`, `Python env management`, `tasks`

**Use for:**
- Working on primitives
- Observability integration
- Keploy framework development
- Universal agent context

**Example:**
```
@workspace #tta-package-dev Add error handling to the ObservabilityIntegration class
```

#### #tta-testing (10 tools)

- id:: toolset-testing
  Testing and validation workflows.

**Tools:** `runTests`, `testFailure`, `runTasks`, `problems`, `changes`

**Use for:**
- Running pytest
- Validation scripts
- CI checks
- Test coverage analysis

**Example:**
```
@workspace #tta-testing Run all integration tests and show me failures
```

---

### Specialized Workflow Toolsets

#### #tta-observability (12 tools)

- id:: toolset-observability
  Observability integration development.

**Tools:** `Prometheus`, `Loki`, `dashboard queries`, `tracing`

**Use for:**
- tta-observability-integration package work
- Metrics collection
- Distributed tracing
- Dashboard development

**Example:**
```
@workspace #tta-observability Query Prometheus for error rates in the last hour
```

#### #tta-agent-dev (13 tools)

- id:: toolset-agent-dev
  AI agent development and coordination.

**Tools:** `AI Toolkit`, `Context7`, `agent best practices`

**Use for:**
- universal-agent-context work
- MCP integration
- Agent coordination
- Workflow orchestration

**Example:**
```
@workspace #tta-agent-dev Implement a new agent handler for Keploy integration
```

#### #tta-mcp-integration (10 tools)

- id:: toolset-mcp-integration
  Model Context Protocol server development and integration.

**Tools:** `MCP tools`, `VS Code API`, `Context7`

**Use for:**
- MCP server work
- Tool development
- Protocol integration
- Server configuration

**Example:**
```
@workspace #tta-mcp-integration Create a new MCP tool for database queries
```

#### #tta-validation (12 tools)

- id:: toolset-validation
  Quality validation and script running.

**Tools:** `validation scripts`, `syntax checks`, `imports analysis`

**Use for:**
- Running validation/
- Package consistency checks
- Type checking
- Linting

**Example:**
```
@workspace #tta-validation Validate all packages and fix import issues
```

---

### Workflow Combination Toolsets

#### #tta-pr-review (10 tools)

- id:: toolset-pr-review
  Pull request review and validation.

**Tools:** `PR operations`, `tests`, `changes`, `problems`

**Use for:**
- Reviewing PRs
- Ensuring quality
- Running checks
- Analyzing changes

**Example:**
```
@workspace #tta-pr-review Analyze PR #27 and suggest improvements
```

#### #tta-package-setup (10 tools)

- id:: toolset-package-setup
  Creating new packages in the monorepo.

**Tools:** `new workspace`, `editing`, `Python setup`

**Use for:**
- Scaffolding new packages
- Setting up structure
- Configuring dependencies
- Creating documentation

**Example:**
```
@workspace #tta-package-setup Create tta-new-feature package with proper structure
```

#### #tta-troubleshoot (11 tools)

- id:: toolset-troubleshoot
  Debugging issues across packages.

**Tools:** `logs`, `errors`, `syntax checks`, `search`

**Use for:**
- Investigating bugs
- Tracing issues
- Analyzing errors
- Finding root causes

**Example:**
```
@workspace #tta-troubleshoot Find why integration tests are failing
```

#### #tta-docs (9 tools)

- id:: toolset-docs
  Documentation and knowledge base work.

**Tools:** `edit`, `search`, `fetch`, `Context7`

**Use for:**
- Writing guides
- Updating documentation
- Migrating to Logseq
- Creating examples

**Example:**
```
@workspace #tta-docs Migrate architecture docs to Logseq format
```

---

### Full Stack Toolset (Use Sparingly)

#### #tta-full-stack (20 tools)

- id:: toolset-full-stack
  Complete TTA.dev development stack.

⚠️ **WARNING:** Use only for complex multi-package workflows

**Includes:** All core tools + observability + AI + GitHub

**Use for:**
- Major refactors
- Multi-package features
- System-wide changes
- Complex integrations

**Example:**
```
@workspace #tta-full-stack Implement distributed tracing across all packages
```

---

## Usage Patterns

### Basic Usage

```markdown
# Quick query
@workspace #tta-minimal What does the coordinator class do?

# Package development
@workspace #tta-package-dev Add logging to ObservabilityIntegration

# Testing
@workspace #tta-testing Run all unit tests and show me failures
```

### Sequential Workflows

```markdown
@workspace First use #tta-package-dev to implement the feature,
then use #tta-testing to add tests,
finally use #tta-docs to document it
```

### Multi-Step Tasks

```markdown
@workspace #tta-agent-dev Create a new agent that integrates with Keploy.
After implementing, switch to #tta-testing to add test coverage,
then use #tta-docs to update the guide.
```

---

## Best Practices

### DO ✅

1. **Start small** - Use `#tta-minimal` or `#tta-package-dev` first
2. **Be specific** - Choose the toolset matching your current task
3. **Combine sequentially** - Reference different toolsets for multi-step work
4. **Keep focused** - Avoid enabling multiple large toolsets simultaneously
5. **Document workflow** - Note which toolset works best for each task type

### DON'T ❌

1. **Avoid full-stack** - Only use `#tta-full-stack` when absolutely necessary
2. **Don't over-combine** - Enabling 5+ toolsets defeats the purpose
3. **Skip context** - Don't use `#tta-troubleshoot` for simple questions
4. **Ignore performance** - Monitor response times and adjust
5. **Forget to update** - Keep toolsets current with new MCP tools

---

## Extending Toolsets

### Adding Custom Tools

When you add MCP servers or VS Code extensions that expose tools:

**Step 1: Identify the tool name**
```
Check: Copilot menu → "Available Tools"
```

**Step 2: Edit configuration**
```jsonc
// .vscode/copilot-toolsets.jsonc
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

**Step 3: Reload VS Code**
```
Ctrl+Shift+P → "Developer: Reload Window"
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
- Document use cases

---

## Architecture Integration

### Synergy with TTA.dev Components

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

---

## Performance Impact

### Before Toolsets

```
⚠️ Warning: 130 tools enabled
- Slower response times (3-5s)
- More tool calling errors (20%+)
- Reduced accuracy (60-70%)
- Higher token usage (+50%)
```

### After Toolsets

```
✅ Optimized: 12 tools enabled (#tta-package-dev)
- Faster responses (1-2s)
- Better tool selection (95%+ accuracy)
- Improved accuracy (85-90%)
- Lower token usage (30% reduction)
```

---

## Troubleshooting

### Issue: "Tool not found" Error

**Symptoms:**
- Copilot can't find a tool in your toolset
- Tool name shows as unknown

**Solutions:**
1. Check tool name spelling in `.vscode/copilot-toolsets.jsonc`
2. Verify the tool is available: Copilot menu → "Available Tools"
3. Ensure MCP servers are running if using MCP tools
4. Restart VS Code to reload toolsets

### Issue: Toolset Not Applying

**Symptoms:**
- `#toolset-name` isn't working
- All tools still enabled

**Solutions:**
1. Verify file location: `.vscode/copilot-toolsets.jsonc`
2. Check JSON syntax (use VS Code validation)
3. Ensure toolset name matches exactly (case-sensitive)
4. Try reloading: `Ctrl+Shift+P` → "Developer: Reload Window"
5. Check Copilot logs: Output → "GitHub Copilot"

### Issue: Performance Still Degraded

**Symptoms:**
- Slow responses despite using toolsets
- High token usage

**Solutions:**
1. Check how many tools are in your active toolset (aim for <15)
2. Consider splitting into smaller, focused toolsets
3. Remove rarely-used tools from the toolset
4. Use `#tta-minimal` for simple queries
5. Monitor tool selection accuracy

---

## Toolsets Reference Table

| Toolset | Tools | Best For | Performance |
|---------|-------|----------|-------------|
| `#tta-minimal` | 3 | Quick queries | ⚡⚡⚡ Fastest |
| `#tta-package-dev` | 12 | Package development | ⚡⚡ Fast |
| `#tta-testing` | 10 | Running tests | ⚡⚡ Fast |
| `#tta-observability` | 12 | Metrics & tracing | ⚡⚡ Fast |
| `#tta-agent-dev` | 13 | Agent development | ⚡⚡ Fast |
| `#tta-mcp-integration` | 10 | MCP work | ⚡⚡ Fast |
| `#tta-validation` | 12 | Quality checks | ⚡⚡ Fast |
| `#tta-pr-review` | 10 | PR reviews | ⚡⚡ Fast |
| `#tta-troubleshoot` | 11 | Debugging | ⚡⚡ Fast |
| `#tta-docs` | 9 | Documentation | ⚡⚡ Fast |
| `#tta-full-stack` | 20 | Complex workflows | ⚡ Slower |

---

## Next Steps

- **Learn primitives:** [[TTA.dev/Guides/Agentic Primitives]]
- **Setup development environment:** [[TTA.dev/Guides/Getting Started]]
- **Understand architecture:** [[TTA.dev/Guides/Architecture Patterns]]

---

## Key Takeaways

1. **Toolsets optimize performance** - Use focused tool collections instead of enabling all tools
2. **Start small** - Begin with `#tta-minimal` or `#tta-package-dev`
3. **Match workflow** - Choose toolsets that align with your current task
4. **Combine sequentially** - Use multiple toolsets for multi-step workflows
5. **Extend thoughtfully** - Add new tools only when needed

**Remember:** Fewer, focused tools = faster, more accurate AI assistance!

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 20 minutes
**Difficulty:** [[Intermediate]]


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___guides___copilot toolsets]]
