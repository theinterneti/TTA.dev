# LogSeq MCP Server Setup Guide

**Quick setup guide for integrating LogSeq with GitHub Copilot in VS Code**

---

## Overview

The LogSeq MCP server enables GitHub Copilot to interact directly with your LogSeq knowledge base - reading, creating, updating, and searching pages without leaving VS Code.

**Repository:** <https://github.com/ergut/mcp-logseq>

---

## Prerequisites

- ✅ LogSeq installed and running
- ✅ `uv` package manager installed
- ✅ GitHub Copilot active in VS Code

---

## Step-by-Step Setup

### 1. Enable Developer Mode (Required)

**⚠️ Important:** Developer mode must be enabled first.

1. Open LogSeq
2. Go to **Settings → Advanced**
3. Enable **"Developer mode"**
4. Click **Apply**

### 2. Enable LogSeq HTTP API

1. Go to **Settings → Features**
2. Check **"Enable HTTP APIs server"**
3. Click **Apply**
4. **Restart LogSeq** (required for HTTP API to activate)

### 3. Start LogSeq API Server

1. After restarting, look for the API button (🔌) in LogSeq's interface
2. Click it and select **"Start server"**
3. The server will start on `http://127.0.0.1:12315` by default
4. API documentation is available at <http://127.0.0.1:12315/>

### 4. Generate API Token

1. In the API panel (🔌 button), click **"Authorization"**
2. Click **"Add"** to create a new authorization token
3. Give it a descriptive name (e.g., "Copilot MCP")
4. **Copy the token value** (the long string) - you'll need it in the next step
5. ⚠️ **Note:** Only the token value (not the name) is used in API requests

### 5. Configure MCP Server

The configuration has already been added to `~/.config/mcp/mcp_settings.json`. You just need to:

1. Open the file:

   ```bash
   code ~/.config/mcp/mcp_settings.json
   ```

2. Find the `"mcp-logseq"` section:

   ```json
   "mcp-logseq": {
     "command": "uv",
     "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
     "env": {
       "LOGSEQ_API_TOKEN": "YOUR_TOKEN_HERE",
       "LOGSEQ_API_URL": "http://127.0.0.1:12315"
     },
     "description": "LogSeq knowledge base integration",
     "disabled": true,
     "notes": "..."
   }
   ```

3. Replace `"YOUR_TOKEN_HERE"` with your actual token from Step 4

4. Change `"disabled": true` to `"disabled": false`

5. ⚠️ **Note:** URL is `http://127.0.0.1:12315` (not localhost)

6. Save the file

### 6. Reload VS Code

1. Open Command Palette: `Ctrl+Shift+P` (Linux/Windows) or `Cmd+Shift+P` (Mac)
2. Type: **"Developer: Reload Window"**
3. Press Enter
4. The LogSeq MCP server should now be active

### 7. Verify Installation

Test that the MCP server is working:

```text
@workspace Show me all pages in my LogSeq graph
```

If successful, Copilot will list your LogSeq pages!

---

## Available Tools

Once configured, you have access to these LogSeq tools:

| Tool | What It Does | Example |
|------|--------------|---------|
| `list_pages` | Browse your LogSeq graph | "Show me all my pages" |
| `get_page_content` | Read page content | "What's in my [[TTA Primitives]] page?" |
| `create_page` | Add new pages | "Create a page called 'Meeting Notes 2025-11-01'" |
| `update_page` | Modify pages | "Add today's progress to my journal" |
| `delete_page` | Remove pages | "Delete the old draft page" |
| `search` | Find content | "Search for 'retry patterns'" |

---

## Usage Examples

### Search Your Knowledge Base

```text
@workspace Find all my notes about RetryPrimitive patterns
```

### Create Documentation from Conversation

```text
@workspace Create a LogSeq page summarizing this implementation discussion
```

### Update Daily Journal

```text
@workspace Add today's progress to my LogSeq project journal
```

### Task Management

```text
@workspace Show me high-priority TODOs from my LogSeq graph
```

### Architecture Documentation

```text
@workspace Get my architecture decision records from LogSeq about caching strategies
```

---

## TTA.dev Integration

The LogSeq MCP server is particularly powerful for TTA.dev workflows:

### Development Workflow

1. **Plan in LogSeq:** Design features in your knowledge base
2. **Implement in VS Code:** Use Copilot with code context
3. **Document automatically:** Copilot updates LogSeq pages with results
4. **Track TODOs:** Manage tasks across both systems

### Example Workflow

```text
# Morning: Review TODOs
@workspace Show me today's development TODOs from LogSeq

# During implementation
# (Normal coding with Copilot)

# End of day: Update journal
@workspace Update my LogSeq daily journal with today's completed tasks
```

---

## Troubleshooting

### "LOGSEQ_API_TOKEN environment variable required"

**Fix:**

- ✅ Verify token is in `~/.config/mcp/mcp_settings.json`
- ✅ Check it's set in the `env` section
- ✅ No quotes or extra spaces in the token value
- ✅ Reload VS Code after changes

### "Connection refused" or "Cannot connect to LogSeq"

**Fix:**

- ✅ Confirm LogSeq is running
- ✅ Verify API server is started (🔌 button → "Start server")
- ✅ Check port 12315 is not blocked
- ✅ Try accessing <http://localhost:12315> in browser (should show API info)

### "spawn uv ENOENT"

**Fix:**

- ✅ Verify `uv` is installed: `which uv`
- ✅ If not found, use full path in config:

  ```json
  "command": "/home/thein/.local/bin/uv",
  ```

- ✅ Reload VS Code after changes

### Tool Not Available in Copilot

**Fix:**

- ✅ Check `"disabled": false` in config
- ✅ Reload VS Code window
- ✅ Verify LogSeq API server is running
- ✅ Test with simple query: `@workspace Show me my LogSeq pages`

---

## Configuration Reference

### Full MCP Configuration

```json
{
  "mcpServers": {
    "mcp-logseq": {
      "command": "uv",
      "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
      "env": {
        "LOGSEQ_API_TOKEN": "your_actual_token_here",
        "LOGSEQ_API_URL": "http://localhost:12315"
      },
      "description": "LogSeq knowledge base integration",
      "disabled": false
    }
  }
}
```

### Environment Variables

- `LOGSEQ_API_TOKEN` (required): Your API token from LogSeq
- `LOGSEQ_API_URL` (optional): API endpoint, defaults to `http://localhost:12315`

---

## LogSeq HTTP API Details

### API Endpoint

- **Base URL:** `http://127.0.0.1:12315/api`
- **Documentation:** <http://127.0.0.1:12315/> (when server is running)
- **Method:** POST with JSON body
- **Authorization:** Bearer token in header

### API Functionality

The LogSeq HTTP API exposes the full [LogSeq Plugins API](https://plugins-doc.logseq.com/):

- **Database Operations:** Query blocks, pages, and properties
- **Editor Operations:** Insert, update, delete blocks and pages
- **Graph Operations:** Navigate and manipulate the knowledge graph
- **CORS Support:** Can be called from browser extensions or web pages

### Example API Calls

**Insert a block:**

```bash
curl -X POST http://127.0.0.1:12315/api \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method": "logseq.Editor.insertBlock", "args": ["Test page", "This is a new block", {"isPageBlock": true}]}'
```

**Query TODOs:**

```bash
curl -X POST http://127.0.0.1:12315/api \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method": "logseq.db.q", "args": ["(task TODO)"]}'
```

### MCP Integration

The `mcp-logseq` server wraps these API calls in MCP tool format, making them accessible to GitHub Copilot and other MCP clients.

---

## Advanced Usage

### Custom API URL

If LogSeq is running on a different port or host:

```json
"env": {
  "LOGSEQ_API_TOKEN": "your_token",
  "LOGSEQ_API_URL": "http://localhost:8080"
}
```

### Multiple LogSeq Graphs

To switch between graphs, create different MCP configurations:

```json
"mcp-logseq-work": {
  "command": "uv",
  "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
  "env": {
    "LOGSEQ_API_TOKEN": "work_token",
    "LOGSEQ_API_URL": "http://localhost:12315"
  },
  "disabled": false
},
"mcp-logseq-personal": {
  "command": "uv",
  "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
  "env": {
    "LOGSEQ_API_TOKEN": "personal_token",
    "LOGSEQ_API_URL": "http://localhost:12316"
  },
  "disabled": true
}
```

Enable/disable as needed and reload VS Code.

---

## Security Notes

- ✅ API token gives full access to your LogSeq graph
- ✅ Keep token secure - don't commit to git
- ✅ Use different tokens for different purposes
- ✅ Revoke tokens when no longer needed (in LogSeq API panel)

---

## Related Documentation

- **MCP Server Registry:** [`MCP_SERVERS.md`](../../MCP_SERVERS.md)
- **Copilot Toolsets:** [`docs/guides/copilot-toolsets-guide.md`](../guides/copilot-toolsets-guide.md)
- **LogSeq TODO System:** [`logseq/pages/TODO Management System.md`](../../logseq/pages/TODO%20Management%20System.md)
- **LogSeq Advanced Features:** [`logseq/ADVANCED_FEATURES.md`](../../logseq/ADVANCED_FEATURES.md)

---

## Next Steps

Once configured, explore these workflows:

1. **Daily Journals:** Use Copilot to read/update your LogSeq daily journals
2. **TODO Management:** Query and manage tasks from your LogSeq TODO system
3. **Documentation:** Auto-generate LogSeq pages from code conversations
4. **Knowledge Search:** Find information across your entire knowledge base
5. **Architecture Decisions:** Store and retrieve ADRs from LogSeq

---

**Last Updated:** November 1, 2025
**Status:** Active
**Maintainer:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Docs/Mcp/Logseq_mcp_setup]]
