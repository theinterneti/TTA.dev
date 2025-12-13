# MCP Server Integration Registry

## What is MCP?

**Model Context Protocol (MCP)** is an open standard for connecting AI applications to external data sources and tools. MCP servers expose capabilities that AI agents can use to:

- Query documentation
- Access databases
- Monitor systems
- Analyze code
- Execute operations

**Official Documentation:** <https://modelcontextprotocol.io>

**IMPORTANT:** MCP servers are only available in a local development environment (e.g., VS Code with Cline or GitHub Copilot extensions). They are not accessible in cloud-based environments like GitHub Actions.

For more details on agent context and tooling, refer to [`AGENTS.md`](AGENTS.md).

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
**Logseq:** [[TTA.dev/Mcp_tool_registry]]
