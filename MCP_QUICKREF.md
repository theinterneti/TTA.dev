# MCP Quick Reference Card

**Quick lookup for MCP servers and their capabilities**

---

## 🚀 Quick Access

| Server | Command | Purpose |
|--------|---------|---------|
| **Context7** | `npx @upstash/context7-mcp` | Library documentation |
| **Playwright** | `npx @playwright/mcp` | Browser automation |
| **GitHub** | Docker: `ghcr.io/github/github-mcp-server` | GitHub API |
| **Sequential Thinking** | `npx mcp-sequentialthinking-tools` | Problem solving |
| **GitMCP** | Web API: `gitmcp.io` | Git analysis |
| **Grafana** | Docker: `mcp-grafana` | Observability |

---

## 💬 Usage Patterns

### Library Research
```text
@workspace How do I use [library-name] for [task]?
```

### Browser Testing
```text
@workspace Navigate to [url] and [action]
@workspace Take a screenshot of [url]
```

### GitHub Operations
```text
@workspace Create an issue for [description]
@workspace List all PRs with label [label-name]
@workspace Show me commits from [author]
```

### Problem Solving
```text
@workspace Use sequential thinking to solve [problem]
@workspace Break down this architecture decision step-by-step
```

### Git Analysis
```text
@workspace Analyze the diff for [commit/PR]
@workspace Find commits that modified [file/function]
@workspace Compare branches [branch1] and [branch2]
```

### Observability
```text
@workspace #tta-observability
Show me [metric-name] for the last [time-period]
Query logs for [error-pattern]
```

---

## 🎯 Toolset Mapping

| Toolset | Use For | MCP Servers |
|---------|---------|-------------|
| `#tta-agent-dev` | AI development | Context7, Sequential Thinking |
| `#tta-pr-review` | Code review | GitHub, GitMCP |
| `#tta-observability` | Monitoring | Grafana |
| `#tta-browser` | Web testing | Playwright |
| `#tta-troubleshoot` | Debugging | Sequential Thinking, Grafana |

---

## 🔧 Environment Setup

```bash
# Required for GitHub server
export GITHUB_TOKEN="ghp_your_token_here"

# Optional for NotebookLM
export GEMINI_API_KEY="your_key_here"

# Verify configuration
cat ~/.config/mcp/mcp_settings.json | jq '.mcpServers | keys'
```

---

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Server not found | Reload VS Code window |
| Docker error | `docker ps` - ensure Docker running |
| Auth failed | Check `GITHUB_TOKEN` environment variable |
| Tool timeout | Increase timeout in server config |
| NPX error | `npx --version` - ensure npx installed |

---

## 📋 Checklist

- [ ] MCP config at `~/.config/mcp/mcp_settings.json`
- [ ] `GITHUB_TOKEN` environment variable set
- [ ] Docker running (for GitHub, Grafana)
- [ ] VS Code reloaded after config changes
- [ ] Test with simple query: `@workspace Test Context7`

---

**Full Documentation:** `MCP_SERVERS.md`
**Setup Guide:** `MCP_CONFIGURATION_UPDATE.md`
