---
type: [[Reference]], [[Registry]]
category: [[MCP]], [[Tools]], [[Integration]]
difficulty: [[Beginner]]
estimated-time: 15 minutes
target-audience: [[Developers]], [[AI Agents]]
---

# MCP Server Integration Registry

**Model Context Protocol (MCP) servers available in TTA.dev**

---

## What is MCP?
id:: mcp-servers-what-is-mcp

**Model Context Protocol (MCP)** is an open standard for connecting AI applications to external data sources and tools.

**MCP servers expose capabilities that AI agents can use to:**

- Query documentation
- Access databases
- Monitor systems
- Analyze code
- Execute operations

**Official Documentation:** <https://modelcontextprotocol.io>

---

## Available MCP Servers
id:: mcp-servers-available

### 1. Context7 - Library Documentation
id:: mcp-servers-context7

**Purpose:** Query up-to-date documentation for any programming library

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_context7_resolve-library-id` | Find library ID from name | Ask about resolving library |
| `mcp_context7_get-library-docs` | Get documentation for library | Ask for library docs |

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
id:: mcp-servers-ai-toolkit

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
id:: mcp-servers-grafana

**Purpose:** Query Prometheus metrics and Loki logs

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `list_alert_rules` | List Grafana alert rules | Ask about alerts |
| `get_alert_rule_by_uid` | Get specific alert rule | Ask about specific alert |
| `get_dashboard_by_uid` | Retrieve dashboard config | Ask about dashboard |
| `query_prometheus` | Execute PromQL query | Ask about metrics |
| `query_loki_logs` | Execute LogQL query | Ask about logs |
| `list_contact_points` | List notification endpoints | Ask about notifications |

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
id:: mcp-servers-pylance

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
id:: mcp-servers-database

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
id:: mcp-servers-github-pr

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
id:: mcp-servers-sift

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

## MCP Tools by Toolset
id:: mcp-servers-by-toolset

### Core Development Toolsets
id:: mcp-servers-core-toolsets

| Toolset | MCP Tools Included |
|---------|-------------------|
| `#tta-minimal` | None (lightweight) |
| `#tta-package-dev` | Pylance tools (automatic) |
| `#tta-testing` | Pylance tools (automatic) |
| `#tta-observability` | Grafana (Prometheus, Loki, alerts) |

### Specialized Toolsets
id:: mcp-servers-specialized-toolsets

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
id:: mcp-servers-usage

### In Copilot Chat
id:: mcp-servers-copilot-usage

**Specify toolset with hashtag:**

```
@workspace #tta-observability

Show me CPU usage for the last 30 minutes
```

**Copilot automatically invokes appropriate MCP tools.**

### Direct Tool Invocation
id:: mcp-servers-direct-invocation

**Request specific tools:**

```
@workspace Use the query_prometheus tool to get error rates
```

---

## Adding New MCP Servers
id:: mcp-servers-adding-new

### Step 1: Configure MCP Server
id:: mcp-servers-adding-configure

**Add to MCP configuration file:**

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
id:: mcp-servers-adding-toolsets

**Edit `.vscode/copilot-toolsets.jsonc`:**

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
id:: mcp-servers-adding-document

**Add entry to this page with:**

- Purpose
- Tools provided
- Example usage
- Configuration details

### Step 4: Test Integration
id:: mcp-servers-adding-test

```bash
# Reload VS Code
# Open Copilot chat
@workspace #my-custom-toolset

Test the new MCP integration
```

---

## Troubleshooting
id:: mcp-servers-troubleshooting

### MCP Tool Not Found
id:: mcp-servers-troubleshooting-not-found

**Symptom:** Tool name shows as invalid in toolset

**Solutions:**

**1. Check MCP server is running:**

```bash
# For Docker-based services
docker-compose -f docker-compose.test.yml ps
```

**2. Verify tool name format:**

- Should be `mcp_servername_toolname`
- Check exact name in MCP server documentation

**3. Reload VS Code window:**

- Command Palette → "Developer: Reload Window"

### MCP Server Not Responding
id:: mcp-servers-troubleshooting-not-responding

**Symptom:** Tools available but return errors

**Solutions:**

1. Check server logs
2. Verify network connectivity
3. Restart MCP server
4. Check authentication/credentials

### Tool Not Available in Toolset
id:: mcp-servers-troubleshooting-not-available

**Symptom:** Tool exists but not showing up

**Solutions:**

1. Verify toolset includes tool name
2. Check `.vscode/copilot-toolsets.jsonc` syntax
3. Reload VS Code
4. Try `#tta-mcp-integration` (includes all MCP tools)

---

## Best Practices
id:: mcp-servers-best-practices

### 1. Choose Right Toolset
id:: mcp-servers-best-practices-toolset

- Use **focused toolsets** for specific tasks
- Prefer `#tta-observability` over `#tta-full-stack` for metrics
- Combine toolsets only when necessary

### 2. Natural Language Queries
id:: mcp-servers-best-practices-natural

**✅ Good - Natural and specific:**

```
@workspace #tta-observability
Show me error logs from the last hour containing "timeout"
```

**❌ Bad - Too technical:**

```
@workspace Execute LogQL: {job="app"} |= "timeout" [1h]
```

### 3. Understand Tool Capabilities
id:: mcp-servers-best-practices-understand

- Read tool descriptions in this document
- Check examples before complex queries
- Start simple, add complexity as needed

### 4. Performance Considerations
id:: mcp-servers-best-practices-performance

- Focused toolsets load faster
- MCP calls may have latency
- Cache-able results are better

---

## Integration with TTA.dev Primitives
id:: mcp-servers-primitive-integration

### Observability Workflow
id:: mcp-servers-observability-workflow

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
id:: mcp-servers-documentation-lookup

```python
# When building agent with new library:
# @workspace #tta-agent-dev
# How do I use the langchain library for embeddings?

# Then implement using primitives
from tta_dev_primitives import SequentialPrimitive
```

### Database Operations
id:: mcp-servers-database-operations

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
id:: mcp-servers-development

**Want to create your own MCP server for TTA.dev?**

### Resources
id:: mcp-servers-development-resources

- **MCP Specification:** <https://spec.modelcontextprotocol.io>
- **Example Servers:** `scripts/mcp/` directory
- **Integration Guide:** `.vscode/README.md`
- **TTA MCP Guide:** [[TTA.dev/MCP/Extending]]

### Template
id:: mcp-servers-development-template

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

## Quick Reference
id:: mcp-servers-quick-reference

### Get Documentation
id:: mcp-servers-quick-docs

```
@workspace #tta-agent-dev
Find documentation for [library name]
```

### Query Metrics
id:: mcp-servers-quick-metrics

```
@workspace #tta-observability
Show [metric name] for last [time period]
```

### Analyze Code
id:: mcp-servers-quick-analyze

```
@workspace #tta-package-dev
Check syntax errors in current file
```

### Review PR
id:: mcp-servers-quick-pr

```
@workspace #tta-pr-review
Summarize changes in this pull request
```

### Execute Query
id:: mcp-servers-quick-query

```
@workspace #tta-full-stack
Run query: [SQL query]
```

---

## Key Takeaways
id:: mcp-servers-summary

**Available Servers:**

1. **Context7** - Library documentation lookup
2. **AI Toolkit** - Agent development best practices
3. **Grafana** - Prometheus metrics and Loki logs
4. **Pylance** - Python development tools
5. **Database Client** - SQL operations
6. **GitHub PR** - Pull request and coding agent
7. **Sift** - Investigation analysis

**Using MCP Tools:**

- Use `@workspace #toolset-name` in Copilot chat
- Natural language queries preferred
- Tools automatically invoked based on context
- Combine with TTA primitives for workflows

**Adding New Servers:**

1. Configure MCP server
2. Add to toolsets
3. Document in this registry
4. Test integration

**Best Practices:**

- Choose focused toolsets for tasks
- Use natural language queries
- Understand tool capabilities
- Consider performance implications

---

## Related Documentation

- [[TTA.dev/MCP/README]] - MCP overview and architecture
- [[TTA.dev/MCP/Usage]] - Running and using servers
- [[TTA.dev/MCP/Extending]] - Creating custom servers
- [[TTA.dev/MCP/Integration]] - Integration patterns
- [[TTA.dev/MCP/AI Assistant Guide]] - AI assistant usage
- [[TTA.dev/Guides/Copilot Toolsets]] - Toolsets guide
- [`.vscode/copilot-toolsets.jsonc`](/.vscode/copilot-toolsets.jsonc) - Toolset configuration

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team
**MCP Version:** 1.0


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___mcp___servers]]
