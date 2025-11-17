# MCP Configuration Update Summary

**Date:** November 14, 2025
**Action:** Updated MCP server configuration for GitHub Copilot

---

## ✅ Changes Made

### 1. Updated MCP Configuration

**Location:** `~/.config/mcp/mcp_settings.json`

**Backup Created:** `~/.config/mcp/mcp_settings.json.backup.YYYYMMDD_HHMMSS`

### 2. Added MCP Servers

The following MCP servers have been configured based on the Cline setup:

#### Production-Ready Servers (Enabled)

1. **Context7** - Library documentation lookup
   - Package: `@upstash/context7-mcp@latest`
   - Command: `npx`
   - Purpose: Query up-to-date library docs

2. **Playwright** - Browser automation
   - Package: `@playwright/mcp@latest`
   - Browser: Chromium (headless)
   - Capabilities: Vision, PDF generation
   - Output: `./browser-outputs/`

3. **GitHub** - GitHub API integration
   - Image: `ghcr.io/github/github-mcp-server`
   - Docker-based for isolation
   - Toolsets: default, projects, labels, orgs
   - Requires: `GITHUB_TOKEN` environment variable

4. **Sequential Thinking** - Structured reasoning
   - Package: `mcp-sequentialthinking-tools`
   - Max history: 1000 thoughts
   - Purpose: Multi-step problem solving

5. **GitMCP** - Enhanced Git operations
   - URL: `https://gitmcp.io/theinterneti/TTA.dev`
   - Web API (no local setup required)
   - Purpose: Advanced commit/diff analysis

6. **Grafana** - Observability queries
   - Docker-based
   - Prometheus URL: `http://localhost:9090`
   - Grafana URL: `http://localhost:3000`

#### Optional Servers (Disabled by Default)

7. **Serena** - Project context management
   - Command: `uv run serena-mcp-server`
   - Project file: `.serena/project.yml`
   - Status: Disabled (requires setup)

8. **NotebookLM** - AI-powered note-taking
   - Command: `node /home/thein/mcp-servers/notebooklm-mcp/dist/index.js`
   - Requires: `GEMINI_API_KEY`
   - Status: Disabled (optional)

### 3. Updated Documentation

**File:** `MCP_SERVERS.md`

**Updates:**
- Added sections for Playwright, Sequential Thinking, GitHub, GitMCP, Serena
- Updated availability table
- Updated toolset mapping
- Added usage examples for each server

---

## 🔧 Configuration Details

### Command Paths (IMPORTANT)

**All commands use absolute paths** to avoid PATH issues when MCP servers start:

```bash
# Node.js tools
/usr/bin/npx      # Package executor
/usr/bin/node     # Node runtime

# Container tools
/usr/bin/docker   # Docker CLI

# Python tools
/home/thein/.local/bin/uv  # UV package manager
```

**Why absolute paths?** MCP server processes don't inherit your shell's PATH environment variable, so relative commands like `npx` or `uv` won't work.

### Environment Variables Required

```bash
# GitHub API access (required for github server)
export GITHUB_TOKEN="your_github_token_here"

# Gemini API (optional, for notebooklm)
export GEMINI_API_KEY="your_gemini_key_here"
```

### Server Status

| Server | Status | Requirements |
|--------|--------|--------------|
| Context7 | ✅ Enabled | npx available |
| Playwright | ✅ Enabled | npx, chromium auto-installed |
| GitHub | ✅ Enabled | Docker, GITHUB_TOKEN env var |
| Sequential Thinking | ✅ Enabled | npx available |
| GitMCP | ✅ Enabled | Internet connection |
| Grafana | ✅ Enabled | Docker, services running |
| Serena | ⚠️ Disabled | Requires .serena/project.yml setup |
| NotebookLM | ⚠️ Disabled | Requires GEMINI_API_KEY |

---

## 📋 Usage Examples

### Context7 - Library Documentation

```text
@workspace How do I use async/await with httpx library?
```

### Playwright - Browser Automation

```text
@workspace Navigate to https://tta.dev and take a screenshot
```

### GitHub - Repository Management

```text
@workspace Create a GitHub issue for the bug we just found
@workspace Show me all open PRs in this repository
```

### Sequential Thinking - Problem Solving

```text
@workspace Use sequential thinking to analyze this architecture decision
@workspace Break down this problem step-by-step
```

### GitMCP - Git Analysis

```text
@workspace Analyze the diff for the last 5 commits
@workspace Find all commits that modified the retry logic
```

### Grafana - Observability

```text
@workspace #tta-observability
Show me CPU usage for the last 30 minutes
```

---

## 🎯 Toolset Integration

### Recommended Toolsets

| Toolset | When to Use | MCP Servers Included |
|---------|-------------|---------------------|
| `#tta-agent-dev` | AI agent development | Context7, Sequential Thinking |
| `#tta-pr-review` | PR review workflow | GitHub, GitMCP |
| `#tta-observability` | Monitoring/debugging | Grafana |
| `#tta-browser` | Web testing | Playwright |
| `#tta-troubleshoot` | Problem solving | Sequential Thinking, Grafana |

### Example Workflow

```text
# 1. Research a library
@workspace #tta-agent-dev
How does the langchain library handle embeddings?

# 2. Analyze commits
@workspace #tta-pr-review
Show me all commits related to cache implementation

# 3. Check metrics
@workspace #tta-observability
What's the error rate for CachePrimitive?

# 4. Test in browser
@workspace #tta-browser
Navigate to our demo site and verify the form works
```

---

## 🔍 Verification

### Check MCP Configuration

```bash
# Verify configuration is valid JSON
cat ~/.config/mcp/mcp_settings.json | jq '.'

# List all configured servers
cat ~/.config/mcp/mcp_settings.json | jq '.mcpServers | keys'
```

### Test Individual Servers

1. **Reload VS Code** - Required to pick up MCP configuration changes
   - Command Palette → "Developer: Reload Window"

2. **Test in Copilot Chat**
   ```text
   @workspace Test Context7 by looking up FastAPI documentation
   ```

3. **Check MCP Server Logs** - Look for connection errors in VS Code Output panel
   - View → Output → "MCP Servers"

---

## 🚨 Troubleshooting

### PATH Issues with npx/uv

**Symptom:** MCP servers fail to start with "command not found" errors

**Cause:** MCP server processes don't inherit shell PATH

**Solution:** Use absolute paths in configuration

```bash
# Find absolute paths
which npx   # Usually /usr/bin/npx
which uv    # Usually ~/.local/bin/uv
which docker # Usually /usr/bin/docker

# Update ~/.config/mcp/mcp_settings.json to use absolute paths
```

**Diagnostic Script:** Run `./scripts/test-mcp-servers.sh` to verify all paths

### Server Not Responding

**Symptom:** MCP tool calls fail or timeout

**Solutions:**

1. **Check Docker is running** (for GitHub, Grafana)
   ```bash
   docker ps
   ```

2. **Verify environment variables**
   ```bash
   echo $GITHUB_TOKEN
   echo $GEMINI_API_KEY
   ```

3. **Check npx packages can be installed**
   ```bash
   npx -y @upstash/context7-mcp@latest --version
   ```

4. **Review MCP server logs**
   - VS Code → Output → "MCP Servers"

### Tool Not Available in Chat

**Symptom:** MCP tools don't appear in Copilot suggestions

**Solutions:**

1. **Reload VS Code window**
   - Command Palette → "Developer: Reload Window"

2. **Check toolset includes MCP tools**
   - Verify `.vscode/copilot-toolsets.jsonc` references MCP tools

3. **Try default toolset**
   ```text
   @workspace (without hashtag - uses all tools)
   ```

### GitHub Token Issues

**Symptom:** GitHub MCP server fails to authenticate

**Solutions:**

1. **Set environment variable**
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

2. **Add to shell profile**
   ```bash
   echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Verify token has correct scopes**
   - Required: `repo`, `workflow`, `write:packages`

---

## 📝 Next Steps

### Enable Optional Servers

#### Serena (Project Context)

1. Create project file:
   ```bash
   mkdir -p .serena
   cat > .serena/project.yml << 'EOF'
   name: TTA.dev-copilot
   packages:
     - tta-dev-primitives
     - tta-observability-integration
     - universal-agent-context
   EOF
   ```

2. Enable in MCP config:
   ```bash
   # Edit ~/.config/mcp/mcp_settings.json
   # Set "disabled": false for serena
   ```

3. Reload VS Code

#### NotebookLM (AI Note-Taking)

1. Get Gemini API key from Google AI Studio

2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your_key_here"
   ```

3. Enable in MCP config:
   ```bash
   # Edit ~/.config/mcp/mcp_settings.json
   # Set "disabled": false for notebooklm
   ```

4. Reload VS Code

### Add Custom MCP Servers

See `MCP_SERVERS.md` section "Adding New MCP Servers" for detailed instructions.

---

## 🔗 Related Documentation

- **MCP Servers Guide:** `MCP_SERVERS.md`
- **Toolsets Guide:** `docs/guides/copilot-toolsets-guide.md`
- **Cline Integration:** `docs/integrations/CLINE_INTEGRATION_GUIDE.md`
- **MCP Specification:** https://modelcontextprotocol.io

---

**Configuration Status:** ✅ Complete
**Restart Required:** ✅ Reload VS Code window to activate
**Last Updated:** November 14, 2025
