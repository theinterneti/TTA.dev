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

### 2. CodeGraphContext - Code Graph Analysis

**Purpose:** Query repository structure, symbol relationships, call chains, and indexed code context

**Core Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `find_code` | Search for functions, classes, and symbols | Locate implementation targets before editing |
| `analyze_code_relationships` | Explore callers, callees, and dependencies | Understand impact before changes |
| `get_repository_stats` | Inspect repository indexing status and graph coverage | Confirm the graph is current |
| `list_indexed_repositories` | Show repositories available in the graph store | Verify indexed projects |

**Setup:**

CodeGraphContext is started locally through the installed `cgc` CLI:

```bash
cgc mcp start
```

**Configuration:**

- Integrated in `.mcp/config.json` as `codegraphcontext`
- Uses the local `cgc mcp start` stdio MCP server
- Can also be configured with `cgc mcp setup` for supported IDEs and CLIs

**Use Cases:**

- Understanding call chains and dependencies
- Finding code by symbol or pattern
- Exploring class hierarchies and architecture
- Verifying repository indexing before AI-assisted edits

### 3. E2B - Secure Code Execution

**Purpose:** Run code and commands in isolated cloud sandboxes for safe execution and testing

**Core Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `run_code` | Execute generated code in a secure sandbox | Validate snippets without touching the host |
| `run_command` | Execute shell commands in an isolated environment | Test tooling workflows safely |
| `write_file` | Create files inside the sandbox | Prepare multi-file experiments |
| `read_file` | Inspect sandbox outputs and artifacts | Retrieve generated results |

**Setup:**

E2B uses the official MCP server package:

```bash
npx -y @e2b/mcp-server
```

**Configuration:**

- Integrated in `.mcp/config.json` as `e2b`
- Requires `E2B_API_KEY` in the environment
- Uses the published `@e2b/mcp-server` package over stdio

**Use Cases:**

- Executing untrusted or generated code safely
- Running isolated experiments and repros
- Testing commands without modifying the host system
- Providing disposable sandboxes to coding agents

### 4. AI Toolkit - Agent Development

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

### 5. Grafana - Observability

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

### 6. Hindsight - Long-Term Memory

**Purpose:** Persistent agent memory for retaining, recalling, and reflecting on project knowledge

**Core Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `retain` | Store information in long-term memory | Save decisions, preferences, or findings |
| `recall` | Retrieve relevant memories | Ask for prior context or known facts |
| `reflect` | Synthesize memories into a reasoned answer | Summarize learned patterns or guidance |

**Setup:**

Start the local Hindsight MCP server before connecting clients:

```bash
HINDSIGHT_API_LLM_API_KEY=sk-... uvx --from hindsight-api hindsight-local-mcp
```

For local models with Ollama:

```bash
HINDSIGHT_API_LLM_PROVIDER=ollama HINDSIGHT_API_LLM_MODEL=llama3.2 uvx --from hindsight-api hindsight-local-mcp
```

**Configuration:**

- Integrated in `.mcp/config.json` as `hindsight`
- Uses the local HTTP MCP endpoint at `http://localhost:8888/mcp/`
- Requires the Hindsight local server to already be running

**Use Cases:**

- Preserving cross-session agent memory
- Remembering user and project preferences
- Capturing decisions, discoveries, and historical context
- Building personalized or learning-oriented agents

### 7. Pylance - Python Tools

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

### 8. Database Client - SQL Operations

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
