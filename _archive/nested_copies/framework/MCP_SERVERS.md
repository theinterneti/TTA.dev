# MCP Server Integration Registry

## 🖥️ LOCAL ONLY: GitHub Copilot VS Code Extension

**⚠️ IMPORTANT CONTEXT:**

- **VS Code Extension?** ✅ This documentation is FOR YOU
- **Coding Agent (GitHub Actions)?** ❌ You do NOT have access to MCP servers
- **GitHub CLI?** ❌ MCP servers not available in terminal

---

## What is MCP?

**Model Context Protocol (MCP)** is an open standard for connecting AI applications to external data sources and tools. MCP servers expose capabilities that AI agents can use to:

- Query documentation
- Access databases
- Monitor systems
- Analyze code
- Execute operations

**Official Documentation:** <https://modelcontextprotocol.io>

### Context-Specific Availability

| MCP Feature | VS Code Extension (LOCAL) | Cline (LOCAL) | Coding Agent (CLOUD) | GitHub CLI |
|-------------|---------------------------|---------------|----------------------|------------|
| Context7 | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| AI Toolkit | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| Grafana | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| Pylance | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| Database Client | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| GitHub PR Tools | ✅ Yes | ✅ Yes | ⚠️ Different | ❌ No |
| Sift (Docker) | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| LogSeq | ✅ Yes | ✅ Yes | ❌ No | ❌ No |

**Why MCP isn't available in GitHub Actions:**

- MCP servers run on your local machine with VS Code
- GitHub Actions runs in ephemeral cloud containers
- No VS Code extension system in GitHub Actions
- Coding Agent uses installed tools (uv, pytest, ruff) instead

**Cline Integration:**

- Cline is a VS Code extension that natively supports MCP
- All TTA.dev MCP servers work seamlessly with Cline
- Cline can collaborate with Copilot using shared MCP infrastructure
- See [CLINE_INTEGRATION_GUIDE.md](docs/integrations/CLINE_INTEGRATION_GUIDE.md) for details

---

## Available MCP Servers

### 1. Context7 - Library Documentation

**Purpose:** Query up-to-date documentation for any programming library

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_context7_resolve-library-id` | Find library ID from name | `@workspace #tta-agent-dev` then ask about resolving library |
| `mcp_context7_get-library-docs` | Get documentation for library | `@workspace #tta-agent-dev` then ask for docs |

**Example Usage:**

```
@workspace #tta-agent-dev

How do I use async/await with httpx library?
```

**Configuration:**

- Integrated in `.vscode/copilot-toolsets.jsonc`
- Available in `#tta-agent-dev` toolset

**Use Cases:**

- Learning new libraries
- API reference lookup
- Best practices research
- Integration patterns

---

### 2. AI Toolkit - Agent Development

**Purpose:** Best practices and guidance for AI application development

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `aitk_get_agent_code_gen_best_practices` | Agent development patterns | Ask about agent architecture |
| `aitk_get_ai_model_guidance` | Model selection advice | Ask about choosing models |
| `aitk_get_tracing_code_gen_best_practices` | Tracing implementation | Ask about observability |
| `aitk_evaluation_planner` | Evaluation metrics planning | Ask about testing AI apps |
| `aitk_get_evaluation_code_gen_best_practices` | Evaluation code patterns | Ask about evaluation code |

**Example Usage:**

```
@workspace #tta-agent-dev

What are best practices for creating an AI agent that uses multiple LLMs?
```

**Configuration:**

- Available in `#tta-agent-dev` toolset
- Complements TTA.dev primitives

**Use Cases:**

- Agent architecture decisions
- Model selection
- Tracing and observability
- Evaluation frameworks

---

### 3. Grafana - Observability

**Purpose:** Query Prometheus metrics and Loki logs

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `list_alert_rules` | List Grafana alert rules | `@workspace #tta-observability` |
| `get_alert_rule_by_uid` | Get specific alert rule | Ask about specific alert |
| `get_dashboard_by_uid` | Retrieve dashboard config | Ask about dashboard |
| `query_prometheus` | Execute PromQL query | Ask about metrics |
| `query_loki_logs` | Execute LogQL query | Ask about logs |
| `list_contact_points` | List notification endpoints | Ask about alerts |

**Example Usage:**

```
@workspace #tta-observability

Show me the error rate for the last hour
```

**Configuration:**

- Available in `#tta-observability` toolset
- Requires `docker-compose.test.yml` running

**Use Cases:**

- Debugging production issues
- Analyzing metrics
- Investigating errors
- Dashboard creation

---

### 4. Pylance - Python Tools

**Purpose:** Python-specific development tools

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_pylance_mcp_s_pylanceDocuments` | Python documentation search | General Python development |
| `mcp_pylance_mcp_s_pylanceFileSyntaxErrors` | File syntax checking | Code validation |
| `mcp_pylance_mcp_s_pylanceImports` | Import analysis | Dependency management |
| `mcp_pylance_mcp_s_pylanceRunCodeSnippet` | Execute Python code | Testing snippets |
| `mcp_pylance_mcp_s_pylancePythonEnvironments` | Environment info | Environment setup |

**Example Usage:**

```
@workspace #tta-package-dev

Check for syntax errors in this file
```

**Configuration:**

- Integrated automatically with Pylance extension
- Available across all toolsets

**Use Cases:**

- Syntax validation
- Import resolution
- Environment management
- Quick code testing

---

### 5. Database Client - SQL Operations

**Purpose:** Execute database queries and manage schemas

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `dbclient-get-databases` | List available databases | Database exploration |
| `dbclient-get-tables` | Get table schemas | Schema analysis |
| `dbclient-execute-query` | Run SQL queries | Data retrieval |

**Example Usage:**

```
@workspace #tta-full-stack

Show me the schema for the users table
```

**Configuration:**

- Available in `#tta-full-stack` toolset
- Requires database connection config

**Use Cases:**

- Schema exploration
- Data analysis
- Query testing
- Database documentation

---

### 6. GitHub Pull Request - Code Review

**Purpose:** PR information and coding agent coordination

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `github-pull-request_activePullRequest` | Get current PR details | PR context |
| `github-pull-request_openPullRequest` | Get visible PR details | Review workflow |
| `github-pull-request_copilot-coding-agent` | Async agent task execution | Complex implementations |

**Example Usage:**

```
@workspace #tta-pr-review

Summarize the changes in this PR
```

**Configuration:**

- Available in `#tta-pr-review` toolset
- Automatically discovers PRs

**Use Cases:**

- PR reviews
- Change analysis
- Async agent tasks
- Context gathering

---

### 7. Sift (Docker) - Investigation Analysis

**Purpose:** Retrieve and analyze investigations

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_mcp_docker_list_sift_investigations` | List investigations | Investigation discovery |
| `mcp_mcp_docker_get_sift_investigation` | Get specific investigation | Detailed analysis |
| `mcp_mcp_docker_get_sift_analysis` | Get analysis results | Investigation results |

**Example Usage:**

```
@workspace #tta-troubleshoot

Show me recent investigations
```

**Configuration:**

- Available in `#tta-troubleshoot` toolset
- Requires Docker MCP integration

**Use Cases:**

- Debugging workflows
- Investigation tracking
- Analysis review
- Historical context

---

### 8. LogSeq - Knowledge Base Integration

**Purpose:** Interact with LogSeq knowledge base - read, create, search, and manage pages

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `list_pages` | Browse your LogSeq graph | List all pages in knowledge base |
| `get_page_content` | Read page content | Retrieve specific page content |
| `create_page` | Add new pages | Create new knowledge base pages |
| `update_page` | Modify existing pages | Update page content |
| `delete_page` | Remove pages | Delete pages from graph |
| `search` | Find content across graph | Search for terms across all pages |

**Example Usage:**

```text
@workspace #tta-docs

Show me all pages related to TTA Primitives in my LogSeq graph
```

```text
@workspace #tta-mcp-integration

Create a new LogSeq page called "Meeting Notes 2025-11-01" with the summary from this conversation
```

**Configuration:**

- Location: `~/.config/mcp/mcp_settings.json`
- Status: Disabled by default (requires LogSeq setup)
- Required environment variables:
  - `LOGSEQ_API_TOKEN` - Your LogSeq API token
  - `LOGSEQ_API_URL` - LogSeq API endpoint (default: <http://localhost:12315>)

**Setup Steps:**

1. **Enable Developer Mode (Required):**
   - Open LogSeq → Settings → Advanced
   - Enable "Developer mode"
   - Click Apply

2. **Enable LogSeq HTTP API:**
   - Settings → Features
   - Check "Enable HTTP APIs server"
   - **Restart LogSeq** (required)

3. **Start API Server:**
   - Click the API button (🔌) in LogSeq
   - Select "Start server"
   - Server runs on <http://127.0.0.1:12315>

4. **Generate API Token:**
   - In API panel → "Authorization"
   - Click "Add" to create new token
   - Copy token value (not the name)

5. **Update MCP Configuration:**

   ```bash
   # Edit ~/.config/mcp/mcp_settings.json
   # Find "mcp-logseq" section
   # Replace YOUR_TOKEN_HERE with your actual token
   # Change URL to http://127.0.0.1:12315
   # Set "disabled": false
   ```

6. **Reload VS Code:**
   - Command Palette → "Developer: Reload Window"

**API Details:**

- **Base URL:** `http://127.0.0.1:12315/api`
- **Method:** POST with JSON body
- **Auth:** Bearer token in Authorization header
- **API Docs:** <http://127.0.0.1:12315/> (when server running)
- **Full API:** [LogSeq Plugins API](https://plugins-doc.logseq.com/)
- **CORS:** Enabled for browser extensions and web pages

**Use Cases:**

- Zero-context switching between code and notes
- AI-powered knowledge organization
- Automated page creation from conversations
- Smart search across your knowledge base
- Task and TODO management from Copilot
- Meeting notes integration
- Documentation generation from code analysis

**TTA.dev Integration:**

- Query TODO dashboards from LogSeq
- Access architecture decision records
- Search learning materials
- Update daily journals
- Manage development tasks
- Link code changes to knowledge pages

**Example Workflows:**

```text
# Search your LogSeq knowledge base
@workspace Find all my notes about RetryPrimitive patterns

# Create documentation from conversation
@workspace Create a LogSeq page summarizing this implementation discussion

# Update existing pages
@workspace Add today's progress to my LogSeq project journal

# Task management
@workspace Show me high-priority TODOs from my LogSeq graph
```

**Repository:** <https://github.com/ergut/mcp-logseq>

---

## MCP Tools by Toolset

### Core Development Toolsets

| Toolset | MCP Tools Included |
|---------|-------------------|
| `#tta-minimal` | None (lightweight) |
| `#tta-package-dev` | Pylance tools (automatic) |
| `#tta-testing` | Pylance tools (automatic) |
| `#tta-observability` | Grafana (Prometheus, Loki, alerts) |

### Specialized Toolsets

| Toolset | MCP Tools Included |
|---------|-------------------|
| `#tta-agent-dev` | Context7, AI Toolkit |
| `#tta-mcp-integration` | All available MCP tools |
| `#tta-docs` | Context7 |
| `#tta-pr-review` | GitHub PR tools |
| `#tta-troubleshoot` | Sift, Grafana |
| `#tta-full-stack` | Database, Grafana, Context7 |

---

## Using MCP Tools

### In Copilot Chat

```
# Specify toolset with hashtag
@workspace #tta-observability

# Ask natural language question
Show me CPU usage for the last 30 minutes

# Copilot automatically invokes appropriate MCP tools
```

### Direct Tool Invocation

You can also request specific tools:

```
@workspace Use the query_prometheus tool to get error rates
```

---

## Adding New MCP Servers

### Step 1: Configure MCP Server

Add to your MCP configuration file (location depends on your setup):

```json
{
  "mcpServers": {
    "my-custom-server": {
      "command": "node",
      "args": ["/path/to/server.js"]
    }
  }
}
```

### Step 2: Add to Toolsets

Edit `.vscode/copilot-toolsets.jsonc`:

```jsonc
"my-custom-toolset": {
  "tools": [
    "edit",
    "search",
    "mcp_my_custom_server_tool1",
    "mcp_my_custom_server_tool2"
  ],
  "description": "Custom workflow using my server",
  "icon": "tools"
}
```

### Step 3: Document Here

Add entry to this file with:

- Purpose
- Tools provided
- Example usage
- Configuration details

### Step 4: Test Integration

```bash
# Reload VS Code
# Open Copilot chat
@workspace #my-custom-toolset

Test the new MCP integration
```

---

## Troubleshooting

### MCP Tool Not Found

**Symptom:** Tool name shows as invalid in toolset

**Solutions:**

1. Check MCP server is running:

   ```bash
   # For Docker-based services
   docker-compose -f docker-compose.test.yml ps
   ```

2. Verify tool name format:
   - Should be `mcp_servername_toolname`
   - Check exact name in MCP server documentation

3. Reload VS Code window:
   - Command Palette → "Developer: Reload Window"

### MCP Server Not Responding

**Symptom:** Tools available but return errors

**Solutions:**

1. Check server logs
2. Verify network connectivity
3. Restart MCP server
4. Check authentication/credentials

### Tool Not Available in Toolset

**Symptom:** Tool exists but not showing up

**Solutions:**

1. Verify toolset includes tool name
2. Check `.vscode/copilot-toolsets.jsonc` syntax
3. Reload VS Code
4. Try `#tta-mcp-integration` (includes all MCP tools)

---

## Best Practices

### 1. Choose Right Toolset

- Use **focused toolsets** for specific tasks
- Prefer `#tta-observability` over `#tta-full-stack` for metrics
- Combine toolsets only when necessary

### 2. Natural Language Queries

```
# ✅ Good - Natural and specific
@workspace #tta-observability
Show me error logs from the last hour containing "timeout"

# ❌ Bad - Too technical
@workspace Execute LogQL: {job="app"} |= "timeout" [1h]
```

### 3. Understand Tool Capabilities

- Read tool descriptions in this document
- Check examples before complex queries
- Start simple, add complexity as needed

### 4. Performance Considerations

- Focused toolsets load faster
- MCP calls may have latency
- Cache-able results are better

---

## Integration with TTA.dev Primitives

MCP tools complement TTA.dev primitives:

### Observability Workflow

```python
from tta_dev_primitives import WorkflowPrimitive
from observability_integration import initialize_observability

# Use primitives for workflow
workflow = step1 >> step2 >> step3

# Use MCP tools to query results
# @workspace #tta-observability
# Show me metrics for this workflow
```

### Documentation Lookup

```python
# When building agent with new library:
# @workspace #tta-agent-dev
# How do I use the langchain library for embeddings?

# Then implement using primitives
from tta_dev_primitives import SequentialPrimitive
```

### Database Operations

```python
# Use MCP to explore schema:
# @workspace #tta-full-stack
# What's the schema for analytics table?

# Then use primitives for workflow
db_query_workflow = (
    validate_input >>
    query_database >>
    transform_results
)
```

---

## MCP Server Development

Want to create your own MCP server for TTA.dev?

### Resources

- **MCP Specification:** <https://spec.modelcontextprotocol.io>
- **Example Servers:** `scripts/mcp/` directory
- **Integration Guide:** `.vscode/README.md`

### Template

```typescript
// Basic MCP server structure
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({
  name: "tta-custom-server",
  version: "1.0.0"
});

server.tool("my_tool", "Tool description", {
  // Tool schema
}, async (args) => {
  // Tool implementation
  return result;
});

server.start();
```

---

## Related Documentation

- **Copilot Toolsets:** [`docs/guides/Copilot_Toolsets_Guide.md`](docs/guides/Copilot_Toolsets_Guide.md)
- **Toolset Guide:** [`docs/guides/copilot-toolsets-guide.md`](docs/guides/copilot-toolsets-guide.md)
- **Integration README:** [`docs/guides/VSCODE_INTEGRATION.md`](docs/guides/VSCODE_INTEGRATION.md)
- **MCP Documentation:** [`docs/mcp/`](docs/mcp/)

---

## Quick Reference

### Get Documentation

```
@workspace #tta-agent-dev
Find documentation for [library name]
```

### Query Metrics

```
@workspace #tta-observability
Show [metric name] for last [time period]
```

### Analyze Code

```
@workspace #tta-package-dev
Check syntax errors in current file
```

### Review PR

```
@workspace #tta-pr-review
Summarize changes in this pull request
```

### Execute Query

```
@workspace #tta-full-stack
Run query: [SQL query]
```

---

**Last Updated:** October 29, 2025
**Maintained by:** TTA.dev Team
**MCP Version:** 1.0
**VS Code Integration:** Stable
