# TTA.dev MCP Servers Integration

**Model Context Protocol Servers for Enhanced Development Capabilities**

---

## Overview

MCP (Model Context Protocol) servers extend TTA.dev's development environment with context-aware tools for documentation lookup, code analysis, monitoring, and repository operations. These servers only work in local development environments and are not available in production or cloud-based workflows.

**Status:** ✅ Active
**Environment:** Development only (local VS Code)
**Configuration Level:** High

---

## Development vs Production Usage

### Development Environment (✅ Available)
- **Primary Use:** Enhanced coding assistance in VS Code
- **Tools:** Context7, AI Toolkit, Grafana monitoring, Pylance, Database Client, GitHub, Sift, LogSeq
- **Benefits:** Real-time documentation access, code analysis, local monitoring, repository tools
- **Setup:** Local MCP configuration (`~/.config/mcp/mcp_settings.json`)

### Production Environment (❌ Not Available)
- **Availability:** Cannot be used in production deployments
- **Reason:** Requires local development environment and interactive tools
- **Alternative:** Use built-in observability and external APIs directly
- **Workaround:** Development data can be collected and used in production monitoring

---

## Available MCP Servers

### Context7 - Library Documentation (✅ Core)
**Purpose:** Query up-to-date library documentation
**Dev Usage:** Instant documentation lookup during development
**Prod Usage:** N/A - documentation embedded in code
**Setup:** Included in `#tta-agent-dev` toolset
**Dependencies:** None

### AI Toolkit - Agent Development (✅ Core)
**Purpose:** Best practices for AI application development
**Dev Usage:** Architecture planning, model selection, tracing setup
**Prod Usage:** N/A - patterns applied at build time
**Setup:** `#tta-agent-dev` toolset
**Dependencies:** None

### Grafana - Observability (✅ Environment)
**Purpose:** Query Prometheus metrics and Loki logs
**Dev Usage:** Debug local development, analyze performance
**Prod Usage:** Indirect via [[TTA.dev/Integrations/Observability Stack]]
**Setup:** Docker-compose environment required
**Dependencies:** [[TTA.dev/Integrations/Observability Stack]]

### Pylance - Python Tools (✅ Automatic)
**Purpose:** Python-specific development assistance
**Dev Usage:** Syntax checking, imports, code snippets
**Prod Usage:** N/A - development-time only
**Setup:** Automatic with Pylance extension
**Dependencies:** VS Code Pylance extension

### Database Client - SQL Operations (✅ Development)
**Purpose:** Execute database queries and schema exploration
**Dev Usage:** Schema exploration, query testing, data analysis
**Prod Usage:** Connections configured in application code
**Setup:** Database connection configuration
**Dependencies:** Database credentials

### GitHub - Repository Operations (✅ Development)
**Purpose:** Comprehensive GitHub repository management
**Dev Usage:** PR reviews, issue management, repository analysis
**Prod Usage:** Limited to CI/CD operations via GitHub Actions
**Setup:** GitHub Personal Access Token
**Dependencies:** GitHub API access

### Sift (Docker) - Investigation Analysis (⚠️ Specialized)
**Purpose:** Retrieve and analyze Docker investigations
**Dev Usage:** Container debugging in development
**Prod Usage:** N/A - container orchestration uses different tools
**Setup:** Sift in Docker environment
**Dependencies:** Docker environment

### LogSeq - Knowledge Base Integration (🚧 New)
**Purpose:** Interact with LogSeq knowledge base
**Dev Usage:** Knowledge discovery, documentation lookup
**Prod Usage:** N/A - development knowledge base
**Setup:** LogSeq API server running
**Dependencies:** LogSeq installation and API enablement

---

## Configuration & Setup

### Automatic Setup

Most MCP servers are configured automatically through VS Code toolsets. The key configuration is in:

```bash
~/.config/mcp/mcp_settings.json
```

### Manual Setup for Advanced Users

1. **Edit MCP Configuration:**
   ```bash
   # Open or create MCP settings
   code ~/.config/mcp/mcp_settings.json
   ```

2. **Verify Configuration:**
   ```json
   {
     "mcpServers": {
       "context7": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-context7"]
       },
       "grafana": {
         "command": "node",
         "args": ["path/to/grafana-mcp-server"]
       }
     }
   }
   ```

3. **Test Connectivity:**
   - Reload VS Code window
   - Try MCP tools in toolset

### Environment Requirements

- **Node.js:** Required for most MCP servers
- **Docker:** Required for Grafana, Sift, Database Client
- **VS Code:** Primary development environment
- **API Keys:** GitHub tokens, database credentials

---

## Usage Patterns in TTA.dev Workflow

### Development Workflow Integration

```
Planning Phase:
├── Copilot + LogSeq (architecture)
├── AI Toolkit (model selection)
└── Context7 (library research)

Implementation Phase:
├── VS Code + Pylance (coding)
├── MCP Database Client (schema work)
└── Cline + E2B (code generation)

Testing Phase:
├── Grafana (metrics monitoring)
├── Sift (container debugging)
└── GitHub (PR reviews)
```

### Toolset Mapping

| TTA.dev Toolset | MCP Servers Included | Use Case |
|----------------|---------------------|----------|
| `#tta-agent-dev` | Context7, AI Toolkit | AI application development |
| `#tta-observability` | Grafana | Monitoring and debugging |
| `#tta-full-stack` | Database, Grafana | Full-stack development |
| `#tta-pr-review` | GitHub | Code review |
| `#tta-troubleshoot` | Sift, Grafana | Container and system debugging |

---

## Cross-References & Integration Points

### Related Integrations
- **[[TTA.dev/Integrations/Cline]]**: Uses all MCP servers for autonomous tasks
- **[[TTA.dev/Integrations/Observability Stack]]**: Data source for Grafana MCP
- **[[TTA.dev/Integrations/Git]]**: Complements GitHub MCP operations

### TTA.dev Components
- **[[tta-observability-integration]]**: Native observability (production)
- **[[TTA.dev/Primitives]]**: Workflow primitives (development and production)
- **[[TTA.dev/DevOps Studio]]**: Development environment

### External Documentation
- [[MCP_SERVERS]] - Repository MCP documentation
- [[docs/guides/copilot-toolsets-guide]]
- [MCP Specification](https://modelcontextprotocol.io)

---

## Health & Status Monitoring

### Current Status
- **Overall:** ✅ Active and fully functional
- **Maintenance:** Monthly updates for new server versions
- **Documentation:** Complete and up-to-date

### Health Checks
- Configuration file validity
- Server process status (when running)
- Tool availability in VS Code
- API connectivity (where applicable)

### Known Limitations
- Local development only
- No production deployment
- VS Code dependency
- API rate limits for external services

---

## Troubleshooting

### MCP Server Not Available

**Symptoms:**
- Tools not showing in toolset
- "MCP server not found" errors

**Solutions:**
1. Check MCP configuration file exists
2. Verify server dependencies installed
3. Reload VS Code: Cmd+Shift+P → "Developer: Reload Window"
4. Check VS Code console for errors

### Authentication Issues

**Symptoms:**
- API-related tools failing

**Solutions:**
1. Verify API keys set in environment
2. Check token permissions/scopes
3. Test API access outside VS Code
4. Check rate limits and account status

### Performance Issues

**Symptoms:**
- Slow tool responses
- Timeout errors

**Solutions:**
1. Check network connectivity
2. Verify external service status
3. Reduce concurrent tool usage
4. Update to latest server versions

---

## Future Enhancements

### Planned Improvements
- [ ] Custom TTA.dev MCP server for primitives workflow
- [ ] Enhanced LogSeq integration for knowledge discovery
- [ ] Automated MCP server health monitoring
- [ ] Integration with additional AI toolkits

### Research Areas
- Container-based MCP server deployment
- Production-safe MCP server subsets
- MCP server auto-configuration

---

## Related Pages

- [[TTA.dev/Integrations/Cline]] - Autonomous development agent
- [[TTA.dev/Integrations/Observability Stack]] - Production monitoring
- [[TTA.dev/DevOps Studio/Infrastructure as Code]] - Infrastructure setup

---

**Last Updated:** 2025-11-17
**Configuration Reference:** [[MCP_SERVERS]]
**Tags:** integration:: mcp, environment:: dev-only, tools:: available


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___integrations___mcp servers]]
