# MCP_SERVERS

**Model Context Protocol (MCP) server integrations for TTA.dev**

---

## Overview

This page documents the MCP servers integrated with TTA.dev for enhanced AI agent capabilities. MCP provides a standard way for AI applications to access external data sources, tools, and services.

**Root Documentation:** See `MCP_SERVERS.md` in repository root for complete details
**Official Site:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## Available MCP Servers

### 1. Context7 - Library Documentation

**Purpose:** Query up-to-date documentation for any programming library

**Tools:**
- `mcp_context7_resolve-library-id` - Find library ID from name
- `mcp_context7_get-library-docs` - Get documentation for library

**Usage:**
```
@workspace #tta-agent-dev
How do I use async/await with httpx library?
```

**Configuration:** Integrated in `.vscode/copilot-toolsets.jsonc`

### 2. AI Toolkit - Agent Development

**Purpose:** Best practices and guidance for AI application development

**Tools:**
- `aitk_get_agent_code_gen_best_practices` - Agent development patterns
- `aitk_get_ai_model_guidance` - Model selection advice
- `aitk_get_tracing_code_gen_best_practices` - Tracing implementation
- `aitk_evaluation_planner` - Evaluation metrics planning
- `aitk_get_evaluation_code_gen_best_practices` - Evaluation code patterns

**Usage:**
```
@workspace #tta-agent-dev
What are best practices for creating an AI agent that uses multiple LLMs?
```

### 3. Grafana - Observability

**Purpose:** Query Prometheus metrics and Loki logs

**Tools:**
- `list_alert_rules` - List Grafana alert rules
- `get_alert_rule_by_uid` - Get specific alert rule
- `get_dashboard_by_uid` - Retrieve dashboard config
- `query_prometheus` - Execute PromQL query
- `query_loki_logs` - Execute LogQL query
- `list_contact_points` - List notification endpoints

**Usage:**
```
@workspace #tta-observability
Show me the error rate for the last hour
```

**Configuration:** Available in `#tta-observability` toolset

### 4. Pylance - Python Tools

**Purpose:** Python-specific development tools

**Tools:**
- `mcp_pylance_mcp_s_pylanceDocuments` - Python documentation search
- `mcp_pylance_mcp_s_pylanceFileSyntaxErrors` - File syntax checking
- `mcp_pylance_mcp_s_pylanceImports` - Import analysis
- `mcp_pylance_mcp_s_pylanceRunCodeSnippet` - Execute Python code
- `mcp_pylance_mcp_s_pylancePythonEnvironments` - Environment info

**Usage:**
```
@workspace #tta-package-dev
Check for syntax errors in this file
```

### 5. Database Client - SQL Operations

**Purpose:** Execute database queries and manage schemas

**Tools:**
- `dbclient-get-databases` - List available databases
- `dbclient-get-tables` - Get table schemas
- `dbclient-execute-query` - Run SQL queries

**Usage:**
```
@workspace #tta-full-stack
Show me the schema for the users table
```

### 6. GitHub Pull Request - Code Review

**Purpose:** PR information and coding agent coordination

**Tools:**
- `github-pull-request_activePullRequest` - Get current PR details
- `github-pull-request_openPullRequest` - Get visible PR details
- `github-pull-request_copilot-coding-agent` - Async agent task execution

**Usage:**
```
@workspace #tta-pr-review
Summarize the changes in this PR
```

### 7. Sift (Docker) - Investigation Analysis

**Purpose:** Retrieve and analyze investigations

**Tools:**
- `mcp_mcp_docker_list_sift_investigations` - List investigations
- `mcp_mcp_docker_get_sift_investigation` - Get specific investigation
- `mcp_mcp_docker_get_sift_analysis` - Get analysis results

**Usage:**
```
@workspace #tta-troubleshoot
Show me recent investigations
```

### 8. LogSeq - Knowledge Base Integration

**Purpose:** Interact with LogSeq knowledge base

**Tools:**
- `list_pages` - Browse LogSeq graph
- `get_page_content` - Read page content
- `create_page` - Add new pages
- `update_page` - Modify existing pages
- `delete_page` - Remove pages
- `search` - Find content across graph

**Usage:**
```
@workspace #tta-docs
Show me all pages related to TTA Primitives in my LogSeq graph
```

**Configuration:** Disabled by default, requires LogSeq HTTP API setup

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

## Using MCP Tools in TTA.dev Workflows

### Pattern 1: Documentation Lookup During Development

```python
# When building agent with new library, query Context7:
# @workspace #tta-agent-dev
# How do I use the langchain library for embeddings?

# Then implement using TTA.dev primitives
from tta_dev_primitives import SequentialPrimitive

workflow = (
    input_processor >>
    langchain_embeddings >>  # Implemented based on Context7 docs
    vector_store >>
    output_formatter
)
```

### Pattern 2: Observability During Debugging

```python
# Use Grafana MCP to query metrics:
# @workspace #tta-observability
# Show me metrics for CachePrimitive over the last hour

# Then optimize based on metrics
from tta_dev_primitives.performance import CachePrimitive

# Adjust TTL based on metrics
optimized_cache = CachePrimitive(
    primitive=expensive_operation,
    ttl_seconds=3600,  # Adjusted based on cache hit rate
    max_size=1000
)
```

### Pattern 3: Database Schema Exploration

```python
# Use Database Client MCP to explore schema:
# @workspace #tta-full-stack
# What's the schema for analytics table?

# Then build workflow with discovered schema
workflow = (
    validate_input >>
    query_database >>  # Using discovered schema
    transform_results
)
```

---

## Configuration

### Enabling MCP Servers

MCP servers are configured in:
- `.vscode/settings.json` - VS Code integration
- `.vscode/copilot-toolsets.jsonc` - Toolset assignments
- `~/.config/mcp/mcp_settings.json` - MCP server config (if applicable)

### Adding Custom MCP Servers

1. **Configure MCP Server**:
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

2. **Add to Toolset**:
   ```jsonc
   "my-custom-toolset": {
     "tools": [
       "edit",
       "search",
       "mcp_my_custom_server_tool1"
     ],
     "description": "Custom workflow",
     "icon": "tools"
   }
   ```

3. **Document in KB**: Add page for the new server

---

## Troubleshooting

### MCP Tool Not Found

1. Check MCP server is running (Docker-based services)
2. Verify tool name format: `mcp_servername_toolname`
3. Reload VS Code: Command Palette → "Developer: Reload Window"

### MCP Server Not Responding

1. Check server logs
2. Verify network connectivity
3. Restart MCP server
4. Check authentication/credentials

### Tool Not Available in Toolset

1. Verify toolset includes tool name in `.vscode/copilot-toolsets.jsonc`
2. Check JSON syntax
3. Reload VS Code
4. Try `#tta-mcp-integration` (includes all MCP tools)

---

## Integration with TTA.dev Primitives

MCP tools complement TTA.dev primitives by providing external context and capabilities:

```python
# MCP for documentation lookup → TTA.dev primitives for implementation
# 1. Query Context7 for library usage
# 2. Implement workflow using primitives
# 3. Query Grafana MCP for metrics
# 4. Optimize based on observability data

from tta_dev_primitives import WorkflowPrimitive
from tta_observability_integration import initialize_observability

# Initialize observability (queryable via Grafana MCP)
initialize_observability(
    service_name="tta-app",
    enable_prometheus=True
)

# Build workflow (informed by Context7 MCP)
workflow = step1 >> step2 >> step3

# Execute and monitor (queryable via MCP)
result = await workflow.execute(data, context)
```

---

## Related Documentation

- **Root Document:** `MCP_SERVERS.md` (complete details)
- [[TTA.dev/MCP Integration]] - MCP integration patterns
- [[.vscode/copilot-toolsets]] - Toolset configuration
- [[TTA.dev/Observability]] - Observability setup

---

## Related Packages

- [[tta-observability-integration]] - Works with Grafana MCP
- [[universal-agent-context]] - Agent coordination
- [[tta-dev-primitives]] - Core primitives

---

## External Resources

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io)
- [MCP Server Examples](https://github.com/modelcontextprotocol/servers)
- [VS Code Copilot Docs](https://code.visualstudio.com/docs/copilot)

---

**Status:** Production-ready
**Context:** Local VS Code only (not available in GitHub Actions)
**Full Documentation:** `MCP_SERVERS.md` in repository root


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Mcp_servers]]
