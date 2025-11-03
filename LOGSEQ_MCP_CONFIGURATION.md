# LogSeq MCP Server Configuration Summary

**Date:** November 1, 2025
**Status:** ✅ Configuration Complete - Requires User Token Setup

---

## What Was Done

### 1. MCP Configuration Updated

**File:** `~/.config/mcp/mcp_settings.json`

Added the `mcp-logseq` server configuration:

```json
"mcp-logseq": {
  "command": "uv",
  "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
  "env": {
    "LOGSEQ_API_TOKEN": "YOUR_TOKEN_HERE",
    "LOGSEQ_API_URL": "http://localhost:12315"
  },
  "description": "LogSeq knowledge base integration - read, create, and manage LogSeq pages",
  "disabled": true,
  "notes": "Enable after: 1) LogSeq HTTP API enabled in Settings->Features, 2) API server started (🔌 button), 3) API token generated and added above"
}
```

**Status:** Disabled by default - requires your LogSeq API token to activate

### 2. Documentation Created

#### MCP Server Registry Updated

**File:** `MCP_SERVERS.md`

Added comprehensive documentation for the LogSeq MCP server including:
- Available tools (list_pages, get_page_content, create_page, update_page, delete_page, search)
- Example usage patterns
- Configuration details
- TTA.dev-specific integration examples

#### Setup Guide Created

**File:** `docs/mcp/LOGSEQ_MCP_SETUP.md`

Created detailed step-by-step setup guide covering:
- Prerequisites
- LogSeq API setup
- Token generation
- Configuration steps
- Troubleshooting
- Advanced usage patterns
- Security notes

---

## What You Need to Do

### Step 1: Enable Developer Mode (Required)

⚠️ **Important:** Developer mode must be enabled first!

1. Open LogSeq
2. Settings → Advanced
3. Enable "Developer mode"
4. Click Apply

### Step 2: Enable LogSeq HTTP API

1. Settings → Features
2. Check "Enable HTTP APIs server"
3. **Restart LogSeq** (required for API to activate)

### Step 3: Start API Server

1. After restarting, click the API button (🔌) in LogSeq
2. Select "Start server"
3. Server runs on `http://127.0.0.1:12315`
4. API docs available at <http://127.0.0.1:12315/>

### Step 4: Generate API Token

1. In API panel (🔌) → "Authorization"
2. Click "Add" to create new token
3. Give it a name (e.g., "Copilot MCP")
4. **Copy the token value** (not the name)

### Step 5: Update Configuration

1. Edit `~/.config/mcp/mcp_settings.json`
2. Find the `mcp-logseq` section
3. Replace `"YOUR_TOKEN_HERE"` with your actual token
4. Change URL to `"http://127.0.0.1:12315"`
5. Change `"disabled": true` to `"disabled": false"`
6. Save the file

### Step 6: Reload VS Code

Command Palette → "Developer: Reload Window"

### Step 7: Test It

```text
@workspace Show me all pages in my LogSeq graph
```

---

## MCP Configuration Location

GitHub Copilot in VS Code uses MCP configurations from:

**Primary:** `~/.config/mcp/mcp_settings.json`

This is a universal configuration that works with:
- VS Code with GitHub Copilot
- Claude Desktop
- Other MCP-compatible clients

The configuration has been added but is **disabled by default** until you provide your LogSeq API token.

---

## Available Tools

Once enabled, these LogSeq tools will be available in Copilot:

| Tool | Description |
|------|-------------|
| `list_pages` | Browse your LogSeq graph |
| `get_page_content` | Read page content |
| `create_page` | Add new pages |
| `update_page` | Modify existing pages |
| `delete_page` | Remove pages |
| `search` | Find content across graph |

---

## Integration with TTA.dev

The LogSeq MCP server is particularly powerful for TTA.dev because:

1. **TODO Management:** Access your LogSeq TODO Management System from Copilot
   - Query high-priority development tasks
   - Update task status
   - Create new TODOs from conversations

2. **Architecture Documentation:** Store and retrieve architecture decisions
   - Access ADRs from LogSeq
   - Update documentation automatically
   - Link code changes to knowledge pages

3. **Daily Journals:** Seamless journal integration
   - Update daily progress
   - Query past entries
   - Generate summaries

4. **Learning Materials:** Access your knowledge base
   - Query flashcards and learning notes
   - Find examples and patterns
   - Create new learning resources

---

## Example Workflows

### Morning Standup

```text
@workspace Show me today's high-priority TODOs from my LogSeq graph
```

### After Implementation

```text
@workspace Update my LogSeq daily journal with:
- Implemented CachePrimitive metrics export
- Added tests for edge cases
- Updated documentation
```

### Documentation Generation

```text
@workspace Create a LogSeq page called "CachePrimitive Implementation Notes"
with the key decisions from this conversation
```

### Knowledge Search

```text
@workspace Search my LogSeq graph for all notes about retry patterns
```

---

## Verification Commands

### Check uv is installed

```bash
which uv
# Should show: /home/thein/.local/bin/uv or similar
```

### Verify LogSeq API is running

```bash
curl http://localhost:12315
# Should return API information
```

### Test MCP configuration syntax

```bash
cat ~/.config/mcp/mcp_settings.json | python3 -m json.tool
# Should show valid JSON without errors
```

---

## Troubleshooting

### If MCP Server Doesn't Appear

1. ✅ Check `disabled: false` in config
2. ✅ Verify token is set correctly
3. ✅ Reload VS Code window
4. ✅ Check LogSeq API server is running

### If Connection Fails

1. ✅ Verify LogSeq is running
2. ✅ Check API server started (not just enabled)
3. ✅ Test with `curl http://localhost:12315`
4. ✅ Verify token is valid in LogSeq

### For More Help

See detailed troubleshooting in:
- [`docs/mcp/LOGSEQ_MCP_SETUP.md`](docs/mcp/LOGSEQ_MCP_SETUP.md)
- [`MCP_SERVERS.md`](../../MCP_SERVERS.md) - Section 8: LogSeq

---

## Security Reminder

⚠️ **Important:** Your LogSeq API token provides full access to your knowledge base.

- Don't commit tokens to git
- Use different tokens for different purposes
- Revoke unused tokens in LogSeq API panel
- Keep your `mcp_settings.json` file secure

---

## Related Files

- **MCP Configuration:** `~/.config/mcp/mcp_settings.json`
- **MCP Server Registry:** [`MCP_SERVERS.md`](../../MCP_SERVERS.md)
- **Setup Guide:** [`docs/mcp/LOGSEQ_MCP_SETUP.md`](docs/mcp/LOGSEQ_MCP_SETUP.md)
- **TODO System:** [`logseq/pages/TODO Management System.md`](../../logseq/pages/TODO%20Management%20System.md)
- **LogSeq Features:** [`logseq/ADVANCED_FEATURES.md`](../../logseq/ADVANCED_FEATURES.md)

---

## Next Steps

1. ✅ Configuration added to `~/.config/mcp/mcp_settings.json`
2. ✅ Documentation created
3. ⏳ **You need to:** Add your LogSeq API token
4. ⏳ **You need to:** Enable the server (`disabled: false`)
5. ⏳ **You need to:** Reload VS Code
6. ⏳ **You need to:** Test with a simple query

**Ready to enable?** See [`docs/mcp/LOGSEQ_MCP_SETUP.md`](docs/mcp/LOGSEQ_MCP_SETUP.md) for step-by-step instructions.

---

**Last Updated:** November 1, 2025
**Status:** Configuration Ready - Awaiting User Activation
**Repository:** <https://github.com/ergut/mcp-logseq>
