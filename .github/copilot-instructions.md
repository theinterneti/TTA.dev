# GitHub Copilot Instructions for TTA.dev

This document provides specific guidance for GitHub Copilot users working on the TTA.dev repository.

## 🎯 Know Your Copilot Context

**CRITICAL:** If you're GitHub Copilot, understand which context you're in:

- **🖥️ VS Code Extension (LOCAL):** You have MCP servers, toolsets, local filesystem
- **☁️ Coding Agent (CLOUD):** You run in GitHub Actions, NO MCP/toolsets
- **💻 GitHub CLI (TERMINAL):** You run in terminal via `gh copilot`

**Why this matters:** Configuration, tools, and capabilities differ by context. Don't assume LOCAL features are available in CLOUD environment or vice versa.

## Copilot Toolsets

TTA.dev leverages Copilot toolsets for specialized development tasks. Refer to [`.vscode/copilot-toolsets.jsonc`](.vscode/copilot-toolsets.jsonc) for the full configuration.

- Use `#tta-package-dev` for primitive development
- Use `#tta-testing` for test development
- Use `#tta-observability` for tracing/metrics work
- Use `#tta-agent-dev` for general agent development (includes Context7, AI Toolkit)
- Use `#tta-mcp-integration` for all available MCP tools
- Use `#tta-docs` for documentation-related tasks (includes Context7)
- Use `#tta-pr-review` for GitHub PR reviews (includes GitHub PR tools)
- Use `#tta-troubleshoot` for investigation and analysis (includes Sift, Grafana)
- Use `#tta-full-stack` for database operations (includes Database, Grafana, Context7)

## Using MCP Tools in Copilot Chat

```
# Specify toolset with hashtag
@workspace #tta-observability

# Ask natural language question
Show me CPU usage for the last 30 minutes

# Copilot automatically invokes appropriate MCP tools
```

## Related Documentation

- **MCP Server Integration Registry:** [`MCP_SERVERS.md`](MCP_SERVERS.md)
- **Copilot Toolsets Configuration:** [`.vscode/copilot-toolsets.jsonc`](.vscode/copilot-toolsets.jsonc)
- **Toolset Guide:** [`docs/guides/copilot-toolsets-guide.md`](docs/guides/copilot-toolsets-guide.md)
