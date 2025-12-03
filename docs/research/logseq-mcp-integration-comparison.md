# Logseq MCP Integration Options - Comprehensive Comparison

> **Research Date:** December 3, 2025  
> **Context:** TTA.dev workspace integration with VS Code Copilot

## Executive Summary

This document compares five approaches for integrating Logseq with MCP (Model Context Protocol) to enable AI assistants like GitHub Copilot to interact with Logseq knowledge bases.

### Quick Comparison Table

| Option | Type | Language | Tools Count | Best For | VS Code Copilot Compatible |
|--------|------|----------|-------------|----------|---------------------------|
| **ergut/mcp-logseq** | MCP Server | Python | 6 | Basic CRUD operations | ✅ Yes |
| **joelhooks/logseq-mcp-tools** | MCP Server | TypeScript | 15+ | Advanced analysis & insights | ✅ Yes |
| **Logseq as MCP Client** | Client Integration | JavaScript | N/A | Plugin-based AI features | ⚠️ Not directly |
| **JavaScript in Logseq** | Native Scripting | JavaScript | Custom | DIY customization | ⚠️ Indirect only |
| **Skywork MCP Server** | MCP Server | Unknown | Unknown | Enterprise deployment | ❓ Research needed |

**Recommendation for TTA.dev:** Use **`joelhooks/logseq-mcp-tools`** for its comprehensive toolset and advanced graph analysis capabilities, or **`ergut/mcp-logseq`** for a simpler Python-native approach that integrates well with your existing `uv`-based workflow.

---

## 1. Logseq as MCP Client

**Source:** [Logseq Forum Discussion](https://discuss.logseq.com/t/utilizing-logseq-as-an-mcp-client/32299)

### Overview
This approach proposes making Logseq itself act as an MCP client, allowing it to connect to external MCP servers and use their tools directly within the Logseq application.

### How It Works
- Logseq would connect to MCP servers (like Claude's built-in servers, or custom servers)
- Users could invoke MCP tools from within Logseq blocks
- Results would be integrated directly into the knowledge graph

### Capabilities
- **Vision:** Native AI integration in Logseq UI
- **Potential Tools:** Access any MCP server's capabilities
- **Bidirectional:** Both read from and write to Logseq

### Installation/Setup
- ⚠️ **Status:** Conceptual/Proposal stage (not yet implemented)
- Would require Logseq plugin or core feature development
- No current installation path available

### Pros
- ✅ Native Logseq integration
- ✅ Could access any MCP server
- ✅ Unified UI experience

### Cons
- ❌ Not yet implemented
- ❌ Requires Logseq development
- ❌ Not usable with VS Code Copilot (inverted direction)

### Best Use Cases
- Future native AI features in Logseq
- Users who primarily work inside Logseq
- Plugin developers exploring new capabilities

### VS Code Copilot Compatibility
**⚠️ Not directly compatible** - This approach makes Logseq a client, whereas VS Code Copilot needs Logseq exposed as an MCP server. The direction of integration is inverted.

---

## 2. JavaScript in Logseq

**Source:** [Logseq Forum Discussion](https://discuss.logseq.com/t/edit-and-run-javascript-code-inside-logseq-itself/20763)

### Overview
Logseq allows running JavaScript code directly inside blocks using the built-in JS execution capability. This enables custom automation and scripting within your knowledge base.

### How It Works
- Use `{{renderer :js}}` or code blocks to execute JavaScript
- Access Logseq's plugin API from within blocks
- Create custom macros and automations

### Capabilities
- **Custom Scripting:** Write inline JS for automation
- **API Access:** Call Logseq's internal APIs
- **Block Manipulation:** Create, update, search blocks programmatically
- **Macro Creation:** Build reusable code templates

### Example Usage
```javascript
// Inside a Logseq block
{{renderer :js, 
  const pages = await logseq.Editor.getAllPages();
  return pages.filter(p => p.name.includes('project'));
}}
```

### Installation/Setup
- Built into Logseq (enable developer mode)
- No additional installation required
- Requires JavaScript knowledge

### Pros
- ✅ Built-in feature, no external dependencies
- ✅ Full access to Logseq Plugin API
- ✅ Highly customizable
- ✅ Can create custom MCP bridges

### Cons
- ❌ Requires JavaScript expertise
- ❌ Code runs inside Logseq (not exposed externally)
- ❌ Not an MCP server on its own
- ❌ Security considerations for running arbitrary code

### Best Use Cases
- Power users building custom automations
- Creating bridges between Logseq and external services
- Building custom MCP servers that call Logseq's HTTP API

### VS Code Copilot Compatibility
**⚠️ Indirect only** - You could use JS in Logseq to build automation, but to expose data to VS Code Copilot, you need an external MCP server that connects via Logseq's HTTP API. This approach is complementary, not a direct solution.

---

## 3. @joelhooks/logseq-mcp-tools

**Source:** [Glama.ai](https://glama.ai/mcp/servers/@joelhooks/logseq-mcp-tools) | [GitHub](https://github.com/joelhooks/logseq-mcp-tools)

### Overview
A comprehensive TypeScript-based MCP server providing extensive tools for interacting with Logseq, including advanced graph analysis, journal management, and AI-powered connection suggestions.

### How It Works
- Connects to Logseq's HTTP API (port 12315)
- Implements MCP protocol using TypeScript SDK
- Provides 15+ specialized tools for knowledge management
- Supports natural language queries via DataScript

### Available Tools

| Tool | Purpose | Features |
|------|---------|----------|
| `getAllPages` | List all pages | Basic page enumeration |
| `getPage` | Get page content | Retrieve specific page |
| `getJournalSummary` | Journal analysis | Date range summaries, linked page extraction |
| `createPage` | Create new pages | With optional initial content |
| `searchPages` | Search by name | Pattern matching |
| `getBacklinks` | Find references | Bidirectional link discovery |
| `addJournalEntry` | Add to journal | Today or specific date, block formatting |
| `addNoteContent` | Add to any page | With formatting preservation |
| `analyzeGraph` | Graph analysis | Frequent references, clusters, tasks |
| `findKnowledgeGaps` | Gap analysis | Missing pages, orphans, underdeveloped |
| `analyzeJournalPatterns` | Pattern analysis | Mood, topics, habits, progress |
| `smartQuery` | Natural language queries | DataScript integration, semantic search |
| `suggestConnections` | AI suggestions | Connection discovery, synthesis opportunities |
| `addFormattedJournalContent` | Rich journal content | Markdown preservation |

### Installation/Setup

**Via Smithery (Easiest):**
```bash
npx -y @smithery/cli install @joelhooks/logseq-mcp-tools --client claude
```

**Manual Installation:**
```bash
# Clone repository
git clone https://github.com/joelhooks/logseq-mcp-tools.git
cd logseq-mcp-tools

# Install dependencies
pnpm install

# Configure environment
cp .env.template .env
# Add your LOGSEQ_TOKEN to .env
```

**VS Code Copilot Configuration:**
```json
{
  "mcp.servers": {
    "logseq": {
      "command": "npx",
      "args": ["tsx", "/path/to/logseq-mcp-tools/index.ts"],
      "env": {
        "LOGSEQ_TOKEN": "${env:LOGSEQ_TOKEN}",
        "LOGSEQ_HOST": "localhost"
      }
    }
  }
}
```

### Prerequisites
- Node.js (system-wide, not nvm)
- Logseq with HTTP API enabled
- API token from Logseq settings
- Port 12315 accessible

### Pros
- ✅ Extensive toolset (15+ tools)
- ✅ Advanced graph analysis capabilities
- ✅ Natural language query support
- ✅ Journal pattern analysis (mood, habits)
- ✅ AI-powered connection suggestions
- ✅ Well-documented with examples
- ✅ Active development
- ✅ Smithery distribution available

### Cons
- ❌ Requires Node.js (TypeScript)
- ❌ Larger codebase than alternatives
- ❌ Node version manager issues with Claude Desktop
- ❌ More complex setup than Python alternatives

### Best Use Cases
- **Advanced knowledge management** with AI assistance
- **Journal analysis and habit tracking**
- **Knowledge gap identification**
- **Cross-page connection discovery**
- **Users who want comprehensive graph insights**

### VS Code Copilot Compatibility
**✅ Fully Compatible**

Add to `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "logseq": {
      "command": "npx",
      "args": ["tsx", "${workspaceFolder}/path/to/index.ts"],
      "env": {
        "LOGSEQ_TOKEN": "${env:LOGSEQ_TOKEN}"
      }
    }
  }
}
```

Or via the existing Hypertool configuration in TTA.dev:
```json
{
  "logseq-mcp-tools": {
    "command": "/usr/bin/npx",
    "args": ["-y", "@joelhooks/logseq-mcp-tools"],
    "env": {
      "LOGSEQ_TOKEN": "${LOGSEQ_API_TOKEN}"
    },
    "description": "Advanced Logseq knowledge graph integration",
    "tags": ["knowledge", "notes", "journal", "analysis"]
  }
}
```

---

## 4. mcp-logseq by ergut

**Source:** [GitHub](https://github.com/ergut/mcp-logseq)

### Overview
A Python-based MCP server focused on clean CRUD operations for Logseq pages. Built with `uv` package manager, making it ideal for Python-centric workflows like TTA.dev.

### How It Works
- Connects to Logseq's HTTP API
- Uses JSON-RPC protocol for API communication
- Implements MCP using Python SDK
- Provides 6 core tools for page management

### Available Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `create_page` | Create new page | `title`, `content` (required) |
| `list_pages` | List all pages | `include_journals` (optional) |
| `get_page_content` | Get page content | `page_name`, `format` (text/json) |
| `delete_page` | Delete page | `page_name` |
| `update_page` | Update page | `page_name`, `content`, `properties` |
| `search` | Full-text search | `query`, filters for pages/blocks/files |

### Installation/Setup

**Via uv (Recommended for TTA.dev):**
```bash
# Add to Claude Code
claude mcp add mcp-logseq \
  --env LOGSEQ_API_TOKEN=your_token \
  --env LOGSEQ_API_URL=http://localhost:12315 \
  -- uv run --with mcp-logseq mcp-logseq
```

**For Development:**
```bash
git clone https://github.com/ergut/mcp-logseq.git
cd mcp-logseq
uv sync --dev
```

**VS Code Copilot Configuration:**
```json
{
  "mcp.servers": {
    "mcp-logseq": {
      "command": "uv",
      "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
      "env": {
        "LOGSEQ_API_TOKEN": "${env:LOGSEQ_API_TOKEN}",
        "LOGSEQ_API_URL": "http://localhost:12315"
      }
    }
  }
}
```

### Prerequisites
- Python 3.11+
- `uv` package manager
- Logseq with HTTP API enabled
- API token generated in Logseq

### Pros
- ✅ Python-native (matches TTA.dev stack)
- ✅ Uses `uv` package manager (TTA.dev standard)
- ✅ Clean, focused API (6 essential tools)
- ✅ Good test coverage (50+ tests)
- ✅ Well-documented error handling
- ✅ Simpler codebase, easier to extend
- ✅ PyPI distribution available

### Cons
- ❌ Fewer tools than joelhooks version
- ❌ No advanced analysis features
- ❌ No natural language query support
- ❌ No journal pattern analysis
- ❌ No AI-powered suggestions

### Best Use Cases
- **Basic knowledge management operations**
- **Python-centric workflows (like TTA.dev)**
- **Users wanting simple, reliable CRUD**
- **Projects where you'll build custom analysis on top**
- **Integration with existing Python tooling**

### VS Code Copilot Compatibility
**✅ Fully Compatible**

For TTA.dev's Hypertool configuration (`.hypertool/mcp_servers.json`):
```json
{
  "mcp-logseq": {
    "command": "/home/thein/.local/bin/uv",
    "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
    "env": {
      "LOGSEQ_API_TOKEN": "${LOGSEQ_API_TOKEN}",
      "LOGSEQ_API_URL": "http://127.0.0.1:12315"
    },
    "description": "Logseq knowledge base CRUD operations",
    "tags": ["knowledge", "notes", "crud", "logseq"]
  }
}
```

---

## 5. Skywork Logseq MCP Server

**Source:** [Skywork AI](https://skywork.ai/skypage/en/logseq-mcp-server-engineer-dive/1981188879861121024)

### Overview
A commercial/enterprise MCP server implementation for Logseq integration, part of the Skywork AI platform.

### What We Know
- Part of Skywork's AI agent ecosystem
- Targets enterprise deployment scenarios
- Likely offers managed infrastructure

### Installation/Setup
- ⚠️ **Limited public documentation**
- Appears to require Skywork platform account
- Commercial licensing likely required

### Pros
- ✅ Potentially managed/hosted solution
- ✅ Enterprise support available
- ✅ May include additional integrations

### Cons
- ❌ Limited public documentation
- ❌ Commercial/enterprise focused
- ❌ Not open source
- ❌ Unknown feature set
- ❌ Vendor lock-in concerns

### Best Use Cases
- Enterprise teams needing managed solutions
- Organizations already using Skywork platform
- Users willing to pay for support

### VS Code Copilot Compatibility
**❓ Unknown** - Insufficient public documentation to determine integration path.

---

## Feature Comparison Matrix

| Feature | joelhooks | ergut | Logseq Client | JS in Logseq | Skywork |
|---------|-----------|-------|---------------|--------------|---------|
| **CRUD Operations** | ✅ | ✅ | ❓ | ✅* | ❓ |
| **Search** | ✅ | ✅ | ❓ | ✅* | ❓ |
| **Journal Management** | ✅ | ❌ | ❓ | ✅* | ❓ |
| **Graph Analysis** | ✅ | ❌ | ❓ | ✅* | ❓ |
| **Knowledge Gaps** | ✅ | ❌ | ❓ | ❌ | ❓ |
| **Pattern Analysis** | ✅ | ❌ | ❓ | ❌ | ❓ |
| **AI Suggestions** | ✅ | ❌ | ❓ | ❌ | ❓ |
| **Natural Language** | ✅ | ❌ | ❓ | ❌ | ❓ |
| **Python Native** | ❌ | ✅ | ❌ | ❌ | ❓ |
| **TypeScript** | ✅ | ❌ | ❌ | ❌ | ❓ |
| **uv Compatible** | ⚠️ | ✅ | N/A | N/A | ❓ |
| **Open Source** | ✅ | ✅ | N/A | N/A | ❌ |
| **Active Development** | ✅ | ✅ | N/A | N/A | ❓ |

*Requires custom implementation

---

## Recommendation for TTA.dev

### Primary Recommendation: **Dual Setup**

Given TTA.dev's focus on both developer productivity and knowledge management, I recommend implementing **both** MCP servers:

#### 1. Use `ergut/mcp-logseq` for Day-to-Day Operations
- Matches TTA.dev's Python/`uv` workflow
- Simple, reliable CRUD operations
- Easy to extend with custom TTA primitives
- Lower overhead for basic operations

#### 2. Use `joelhooks/logseq-mcp-tools` for Analysis
- Advanced graph insights
- Knowledge gap identification
- Pattern analysis for productivity tracking
- Connection discovery for knowledge synthesis

### Implementation Plan

**Phase 1: Basic Integration (ergut/mcp-logseq)**

Add to `.hypertool/mcp_servers.json`:
```json
{
  "logseq-basic": {
    "command": "/home/thein/.local/bin/uv",
    "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
    "env": {
      "LOGSEQ_API_TOKEN": "${LOGSEQ_API_TOKEN}",
      "LOGSEQ_API_URL": "http://127.0.0.1:12315"
    },
    "description": "Logseq basic CRUD operations (Python/uv)",
    "tags": ["knowledge", "notes", "logseq", "crud"]
  }
}
```

**Phase 2: Advanced Analysis (joelhooks/logseq-mcp-tools)**

Add to `.hypertool/mcp_servers.json`:
```json
{
  "logseq-advanced": {
    "command": "/usr/bin/npx",
    "args": ["-y", "@joelhooks/logseq-mcp-tools"],
    "env": {
      "LOGSEQ_TOKEN": "${LOGSEQ_API_TOKEN}",
      "LOGSEQ_HOST": "localhost"
    },
    "description": "Logseq advanced analysis and insights (TypeScript)",
    "tags": ["knowledge", "analysis", "insights", "patterns"]
  }
}
```

### Prerequisites Checklist

- [ ] Enable Logseq HTTP API (Settings → Features → HTTP APIs)
- [ ] Start Logseq API server (🔌 button → "Start server")
- [ ] Generate API token (API panel → Authorization tokens)
- [ ] Add `LOGSEQ_API_TOKEN` to environment (`.env` or shell)
- [ ] Verify port 12315 is accessible

### Testing the Integration

```bash
# Test ergut/mcp-logseq
uv run --with mcp-logseq python -c "
from mcp_logseq.logseq import LogSeq
api = LogSeq(api_key='your_token')
print(f'Connected! Found {len(api.list_pages())} pages')
"

# Test joelhooks/logseq-mcp-tools
npx tsx /path/to/logseq-mcp-tools/index.ts
# Then interact via MCP client
```

---

## Security Considerations

### API Token Management
- Store `LOGSEQ_API_TOKEN` in `.env` (already in `.gitignore`)
- Never log tokens, even partially
- Use environment variable references in configs

### Network Security
- Default API runs on localhost only (127.0.0.1:12315)
- Don't expose Logseq API externally
- Consider firewall rules if needed

### Data Privacy
- All Logseq data stays local
- MCP servers don't send data to external services
- Review tool permissions before enabling

---

## References

1. [ergut/mcp-logseq GitHub](https://github.com/ergut/mcp-logseq)
2. [joelhooks/logseq-mcp-tools GitHub](https://github.com/joelhooks/logseq-mcp-tools)
3. [Logseq Plugin API Documentation](https://plugins-doc.logseq.com)
4. [Model Context Protocol Specification](https://spec.modelcontextprotocol.io)
5. [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
6. [Logseq Forum - MCP Client Discussion](https://discuss.logseq.com/t/utilizing-logseq-as-an-mcp-client/32299)
7. [Logseq Forum - JavaScript in Logseq](https://discuss.logseq.com/t/edit-and-run-javascript-code-inside-logseq-itself/20763)
8. [Skywork AI Platform](https://skywork.ai)

---

## Appendix: Logseq HTTP API Reference

Both MCP servers use Logseq's HTTP API, which provides these capabilities:

### Page Operations
- `logseq.Editor.getAllPages()` - List all pages
- `logseq.Editor.getPage(pageName)` - Get page details
- `logseq.Editor.createPage(name, properties)` - Create page
- `logseq.Editor.deletePage(name)` - Delete page

### Block Operations
- `logseq.Editor.getPageBlocksTree(pageId)` - Get all blocks
- `logseq.Editor.insertBlock(pageId, content)` - Add block
- `logseq.Editor.updateBlock(blockId, content)` - Update block
- `logseq.Editor.removeBlock(blockId)` - Delete block

### Search & Query
- `logseq.DB.datascriptQuery(query)` - DataScript queries
- Full-text search across blocks, pages, files

### Graph Operations
- `logseq.App.getCurrentGraph()` - Get current graph info
- Properties management via page/block properties

---

*Last Updated: December 3, 2025*
*Author: GitHub Copilot (Claude Opus 4.5 Preview)*
