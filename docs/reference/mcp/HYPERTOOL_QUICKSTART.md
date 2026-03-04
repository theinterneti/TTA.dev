# Hypertool MCP Quick Start

**Try Hypertool in 5 minutes**

## 🚀 Instant Setup

### Step 1: Backup Current Config

```bash
# In TTA.dev root
cp .mcp.json .mcp.json.backup
```

### Step 2: Copy Config for Hypertool

```bash
# Hypertool reads from separate config
cp .mcp.json .mcp.hypertool.json
```

### Step 3: Point to Hypertool

Replace `.mcp.json` with:

```json
{
  "mcpServers": {
    "hypertool": {
      "command": "npx",
      "args": [
        "-y",
        "@toolprint/hypertool-mcp",
        "mcp",
        "run",
        "--mcp-config",
        ".mcp.hypertool.json"
      ]
    }
  }
}
```

### Step 4: Reload VS Code

```
Cmd/Ctrl + Shift + P → "Developer: Reload Window"
```

## ✨ Try It Out

### Create Your First Toolset

In Copilot Chat:

```
@workspace Create a toolset called "dev-essentials" with git, filesystem, and search tools
```

**Expected response:**
```
Created "dev-essentials" toolset with 8 tools:
- mcp_github_github_create_pull_request
- mcp_filesystem_read_file
- search
- edit
- ...

Token usage: ~1200 tokens (optimized!)
```

### Switch Toolsets (Hot-Swap!)

```
@workspace Switch to "dev-essentials" toolset
```

**No restart needed!** This is the magic.

### Check What's Active

```
@workspace Show active toolset with token costs
```

**Expected response:**
```
Active Toolset: dev-essentials

Tools:
1. search (180 tokens, 15%)
2. edit (220 tokens, 18%)
3. mcp_github_github_create_pull_request (450 tokens, 37%)
...

Total: 1200 tokens
```

### See All Available Tools

```
@workspace List all available tools with token estimates
```

**This shows EVERYTHING across all MCP servers with token costs!**

## 🎯 TTA.dev Recommended Toolsets

### For Package Development

```
@workspace Create toolset "tta-package-dev" with:
- edit
- search
- usages
- problems
- mcp_pylance_mcp_s_pylanceRunCodeSnippet
- mcp_pylance_mcp_s_pylanceFileSyntaxErrors
- configure_python_environment
- run_task
```

**Goal:** <2000 tokens, focused on Python package work

### For Observability

```
@workspace Create toolset "tta-observability" with:
- mcp_grafana_query_prometheus
- mcp_grafana_query_loki_logs
- mcp_grafana_list_alert_rules
- search
- problems
- think
```

**Goal:** <1500 tokens, metrics and debugging

### For Agent Development

```
@workspace Create toolset "tta-agent-dev" with:
- mcp_context7_get-library-docs
- mcp_aitk_get_agent_code_gen_best_practices
- mcp_e2b_execute_code
- edit
- search
- run_task
```

**Goal:** <1800 tokens, AI agent development

## 📊 Measure Context Usage

### Before Optimization

```
@workspace Show active toolset
```

**Might see:** 20 tools, 6000 tokens (too much!)

### After Optimization

Remove heavy/unnecessary tools:

```
@workspace Remove tool "mcp_heavy_tool_name" from active toolset
```

**Result:** 12 tools, 2200 tokens (63% reduction!)

## 🔥 Hot-Swap Demo

Try this workflow:

```
# Start with coding
@workspace Switch to "tta-package-dev" toolset
@workspace Edit file X to add feature Y

# Need observability data
@workspace Switch to "tta-observability" toolset
@workspace Query Prometheus for error rates

# Write incident report
@workspace Create toolset "writing" with edit, search, think
@workspace Switch to "writing" toolset
@workspace Create documentation for the incident
```

**All without restarting VS Code!**

## 🎭 Try a Persona (Optional)

Personas are pre-configured bundles:

```bash
# In terminal
npx -y @toolprint/hypertool-mcp mcp run --persona web-dev

# Or in .mcp.json:
{
  "mcpServers": {
    "hypertool": {
      "command": "npx",
      "args": [
        "-y",
        "@toolprint/hypertool-mcp",
        "mcp",
        "run",
        "--persona",
        "web-dev"
      ]
    }
  }
}
```

Available personas:
- `web-dev` - Git, Docker, Filesystem, Browser
- `data-scientist` - Python, Jupyter, Database
- `devops` - Docker, Kubernetes, AWS
- `researcher` - Perplexity, Arxiv, Wikipedia

## 🧪 Validation

Verify it's working:

```bash
# Check Hypertool is running
@workspace List available tools

# Should show ALL your MCP tools from ALL servers
# with token estimates for each
```

## 🐛 Troubleshooting

### "Hypertool not found"

```bash
# Install globally
npm install -g @toolprint/hypertool-mcp

# Or always use npx (downloads on-demand)
npx -y @toolprint/hypertool-mcp --version
```

### "No tools available"

1. Check `.mcp.hypertool.json` has your servers
2. Verify MCP servers are running (e.g., Docker containers)
3. Reload VS Code

### "Toolset switch doesn't work"

- **In Cursor/VSCode:** Should work instantly
- **In Claude Desktop:** Requires app restart (limitation)
- **In Claude Code:** Coming soon (track progress)

## ↩️ Rollback

If something breaks:

```bash
# Restore original config
cp .mcp.json.backup .mcp.json

# Reload VS Code
# Cmd/Ctrl + Shift + P → "Developer: Reload Window"
```

## 📚 Learn More

- **Full Integration Plan:** `docs/mcp/HYPERTOOL_INTEGRATION_PLAN.md`
- **Hypertool Docs:** https://github.com/toolprint/hypertool-mcp
- **TTA.dev MCP Guide:** `MCP_SERVERS.md`

## 🎯 Next Steps

1. ✅ Try quick start above
2. 📊 Measure your current tool usage
3. 🎯 Create 2-3 focused toolsets
4. 🔥 Experience hot-swapping
5. 📝 Share feedback in team discussion

---

**Created:** 2025-11-14
**Estimated Time:** 5 minutes to try
**Impact:** Immediate - See the difference right away!


---
**Logseq:** [[TTA.dev/Docs/Mcp/Hypertool_quickstart]]
