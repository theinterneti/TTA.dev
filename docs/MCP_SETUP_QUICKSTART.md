# MCP Servers Setup - Quick Reference

## Status Overview

| MCP Server | Status | Action Required |
|------------|--------|-----------------|
| **Sequential Thinking** | ✅ **ENABLED** | None - already working! |
| **Serena** | 🔧 **NEEDS ENABLING** | Run setup script |
| **LogSeq** | ⚠️ **NEEDS SETUP** | Manual configuration required |

---

## Quick Setup Commands

### Option 1: Automated Setup (Recommended)

```bash
cd /home/thein/repos/TTA.dev-copilot
./scripts/setup-mcp-servers.sh
```

This will:
- ✅ Verify Sequential Thinking is enabled
- ✅ Enable Serena in MCP config
- ✅ Create Serena project configuration
- ⚠️ Provide instructions for LogSeq setup

### Option 2: Manual Setup

#### Enable Serena

```bash
# 1. Edit MCP settings
nano ~/.config/mcp/mcp_settings.json

# 2. Find the "serena" section and change:
"disabled": true  →  "disabled": false

# 3. Reload VS Code
# Ctrl+Shift+P → "Developer: Reload Window"
```

#### Setup LogSeq

```bash
# 1. Start LogSeq
logseq &

# 2. In LogSeq UI:
#    - Settings → Advanced → Enable "Developer mode"
#    - Settings → Features → Enable "Enable HTTP APIs server"
#    - Restart LogSeq
#    - Click API button (🔌) → Start server
#    - API panel → Authorization → Add token → Copy token

# 3. Add to MCP settings (~/.config/mcp/mcp_settings.json):
{
  "mcpServers": {
    "mcp-logseq": {
      "command": "/usr/bin/npx",
      "args": ["-y", "@ergut/mcp-logseq"],
      "env": {
        "LOGSEQ_API_TOKEN": "paste-your-token-here",
        "LOGSEQ_API_URL": "http://127.0.0.1:12315"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}

# 4. Test API
curl http://127.0.0.1:12315/api
```

---

## Verification

After setup, test each server:

```bash
# Sequential Thinking (should already work)
npx -y mcp-sequentialthinking-tools --version

# Serena
serena-mcp-server --version
# OR
uv run serena-mcp-server --version

# LogSeq API
curl http://127.0.0.1:12315/api
```

---

## Using the MCP Servers

### Sequential Thinking

Use for complex problem solving:

```
@workspace Use sequential thinking to analyze the architecture of the
CachePrimitive and suggest optimizations
```

Features:
- Multi-step reasoning
- Thought persistence (max 1000)
- Context recall across sessions

### Serena

Get project context and task management:

```
@workspace Show me all tasks for the tta-dev-primitives package

@workspace What's the current project status?

@workspace Get dependencies for the observability package
```

Features:
- Project-aware task tracking
- Package-specific queries
- Dependency management
- Workflow automation

### LogSeq

Interact with your knowledge base:

```
@workspace Search my LogSeq for notes about RetryPrimitive patterns

@workspace Create a LogSeq page summarizing today's implementation work

@workspace Show me all TODOs from my LogSeq graph
```

Features:
- Knowledge base search
- Page creation/updates
- TODO management
- Zero-context switching

---

## Troubleshooting

### Sequential Thinking not working

```bash
# Check if enabled in MCP settings
grep -A 5 '"sequential-thinking"' ~/.config/mcp/mcp_settings.json

# Should show: "disabled": false

# Test directly
npx -y mcp-sequentialthinking-tools
```

### Serena not found

```bash
# Install with uv
uv pip install serena-mcp-server

# OR with pip
pip install serena-mcp-server

# Verify installation
which serena-mcp-server
```

### LogSeq API not responding

```bash
# Check if LogSeq is running
ps aux | grep -i logseq

# Check if API server is started
curl http://127.0.0.1:12315/api

# Check port availability
netstat -tln | grep 12315

# Start LogSeq and enable API (see setup steps above)
```

### VS Code not detecting servers

```bash
# 1. Verify MCP settings syntax
cat ~/.config/mcp/mcp_settings.json | python -m json.tool

# 2. Reload VS Code
# Ctrl+Shift+P → "Developer: Reload Window"

# 3. Check Copilot extension is installed
# Extensions → Search "Copilot"
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.config/mcp/mcp_settings.json` | Main MCP configuration |
| `.serena/project.yml` | Serena project definition |
| `/tmp/mcp_setup_guide.md` | Detailed setup guide |
| `scripts/setup-mcp-servers.sh` | Automated setup script |

---

## Next Steps

1. **Run the setup script:**
   ```bash
   ./scripts/setup-mcp-servers.sh
   ```

2. **Complete LogSeq setup** (follow manual steps above)

3. **Reload VS Code:**
   - Command Palette → "Developer: Reload Window"

4. **Test in Copilot:**
   ```
   @workspace Test sequential thinking by breaking down this problem...
   @workspace Query Serena for project status
   @workspace Search LogSeq for architecture notes
   ```

5. **Review documentation:**
   - Full guide: `/tmp/mcp_setup_guide.md`
   - MCP Servers reference: `MCP_SERVERS.md`

---

**Last Updated:** November 14, 2025
**Status:** Sequential Thinking ✅ | Serena 🔧 | LogSeq ⚠️
