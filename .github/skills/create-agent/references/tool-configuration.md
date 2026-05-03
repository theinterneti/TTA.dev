# Tool Configuration

## Built-in Tool Aliases

All aliases are case-insensitive:

| Alias | Also known as | Description |
|-------|--------------|-------------|
| `execute` | shell, Bash, powershell | Shell command execution |
| `read` | Read, NotebookRead, view | Read file contents |
| `edit` | Edit, MultiEdit, Write | Edit and modify files |
| `search` | Grep, Glob | Search for files or text |
| `agent` | custom-agent, Task | Invoke other agents |
| `web` | WebSearch, WebFetch | Web content access |

## MCP Server Tools

Reference MCP tools with namespace syntax:

```yaml
# All tools from a server
tools: ['github/*']

# Specific tools
tools: ['github/get_file_contents', 'playwright/navigate']
```

### TTA.dev MCP Servers

| Server | Namespace | Tools | Use Case |
|--------|-----------|-------|----------|
| Context7 | `context7` | Library doc lookup | Any agent needing API docs |
| GitHub | `github` | Repo/PR/issue access | CI, review, planning |
| Serena | `serena` | Symbol-level navigation | Code analysis, refactoring |
| GitMCP | `gitmcp` | Git history analysis | Archaeology, blame |
| Sequential Thinking | `sequential-thinking` | Structured reasoning | Complex problem solving |
| Grafana | `grafana` | Dashboard/metrics | Observability agents |
| Playwright | `playwright` | Browser automation | UI testing, screenshots |
| CodeGraph (CGC) | `codegraphcontext` | Dependency graphs | Impact analysis |

## Tool Selection Strategies

**Enable all** (avoid in production agents):
```yaml
tools: ['*']
```

**Specific tools** (recommended):
```yaml
tools: ['read', 'edit', 'search', 'context7', 'github']
```

**Read-only agent** (for reviewers):
```yaml
tools: ['read', 'search']
```

**No tools** (pure advisory):
```yaml
tools: []
```

### Principle of Least Privilege

- Start with `read` + `search` and add only what's needed
- Limit `execute` to agents that genuinely need shell access
- `agent` tool only for orchestrators — not every agent
- `web` only for research-oriented agents
- Unrecognized tool names are silently ignored (safe for cross-environment)
