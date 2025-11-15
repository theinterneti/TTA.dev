# TTA.dev Hypertool Integration

## Overview

This directory contains Hypertool MCP configuration for TTA.dev's persona-based tool orchestration.

## Structure

```
.hypertool/
├── README.md                    # This file
├── mcp_servers.json            # MCP server definitions with tags
└── personas/                    # Persona definitions
    ├── tta-backend-engineer.json
    ├── tta-frontend-engineer.json
    ├── tta-devops-engineer.json
    ├── tta-testing-specialist.json
    ├── tta-observability-expert.json
    └── tta-data-scientist.json
```

## Personas

### 🔧 TTA Backend Engineer
**Token Budget:** 2000
**Focus:** Python backend, primitives, workflow orchestration
**MCP Servers:** context7, github, sequential-thinking, gitmcp, serena, mcp-logseq
**Use For:**
- Implementing TTA.dev primitives
- Backend API development
- Async workflow patterns
- Type-safe Python code

### 🎨 TTA Frontend Engineer
**Token Budget:** 1800
**Focus:** React, TypeScript, UI development
**MCP Servers:** context7, playwright, github, gitmcp, serena, mcp-logseq
**Use For:**
- UI component development
- Browser testing
- Frontend performance
- Accessibility

### 🚀 TTA DevOps Engineer
**Token Budget:** 1500
**Focus:** CI/CD, infrastructure, deployment
**MCP Servers:** github, grafana, gitmcp, sequential-thinking, mcp-logseq
**Use For:**
- GitHub Actions workflows
- Infrastructure as Code
- Monitoring setup
- Deployment automation

### 🧪 TTA Testing Specialist
**Token Budget:** 1800
**Focus:** Test development, QA, validation
**MCP Servers:** context7, playwright, github, gitmcp, serena, sequential-thinking, mcp-logseq
**Use For:**
- Unit/integration tests
- Test coverage improvement
- Test automation
- Quality metrics

### 📊 TTA Observability Expert
**Token Budget:** 1500
**Focus:** Monitoring, tracing, metrics
**MCP Servers:** grafana, github, gitmcp, sequential-thinking, mcp-logseq
**Use For:**
- OpenTelemetry integration
- Prometheus metrics
- Grafana dashboards
- Alert configuration

### 🔬 TTA Data Scientist
**Token Budget:** 2000
**Focus:** Data analysis, ML workflows, research
**MCP Servers:** context7, github, gitmcp, sequential-thinking, mcp-logseq
**Use For:**
- Data analysis workflows
- ML model development
- Jupyter notebooks
- Research experiments

## Usage with Hypertool

### Installation

```bash
# Install Hypertool MCP server
npm install -g @toolprint/hypertool-mcp@latest
```

### Configuration

Update `~/.config/mcp/mcp_settings.json`:

```json
{
  "mcpServers": {
    "hypertool": {
      "command": "npx",
      "args": [
        "-y",
        "@toolprint/hypertool-mcp@latest",
        "mcp",
        "run",
        "--persona", "tta-backend-engineer"
      ],
      "env": {
        "HYPERTOOL_CONFIG_DIR": "/home/thein/repos/TTA.dev/.hypertool",
        "HYPERTOOL_SERVERS_FILE": "/home/thein/repos/TTA.dev/.hypertool/mcp_servers.json"
      }
    }
  }
}
```

### Hot-Swapping Personas

```bash
# Switch to frontend engineer
hypertool persona switch tta-frontend-engineer

# Switch to devops engineer
hypertool persona switch tta-devops-engineer

# List available personas
hypertool persona list
```

### Integration with .chatmode.md

Add persona to Chat Mode frontmatter:

```yaml
---
persona: tta-backend-engineer
tools_via_hypertool: true
security:
  restricted_paths: ["apps/**/frontend/**"]
---
```

## Token Budget Optimization

| Persona | Token Budget | Reduction |
|---------|-------------|-----------|
| Backend Engineer | 2000 | -75% |
| Frontend Engineer | 1800 | -77.5% |
| DevOps Engineer | 1500 | -81.25% |
| Testing Specialist | 1800 | -77.5% |
| Observability Expert | 1500 | -81.25% |
| Data Scientist | 2000 | -75% |

**Average Reduction:** 77.9% (from 8000 tokens to ~1767 tokens)

## Security Features

### Automatic Tool Filtering
Each persona only sees relevant tools - no policy needed!

### Path Restrictions
Personas have restricted file access:
- Backend: No frontend access
- Frontend: No backend/test access
- DevOps: No src code access
- Testing: No secrets/workflows access

### Environment Variable Control
Fine-grained env var access per persona:
- Backend: `GITHUB_TOKEN`, `OPENAI_API_KEY`
- DevOps: `GITHUB_TOKEN`, `GRAFANA_URL`, `PROMETHEUS_URL`
- Others: Minimal or no access

### Approval Requirements
Sensitive operations require approval:
- File deletion
- System commands
- Workflow execution

## Workflow Integration

### Multi-Persona Workflows

Example: Package Release Workflow

```yaml
# .prompt.md
---
workflow: package-release
personas:
  - dev: tta-backend-engineer
  - test: tta-testing-specialist
  - deploy: tta-devops-engineer
---

1. [tta-backend-engineer] Implement feature
2. [tta-testing-specialist] Validate tests pass
3. [tta-devops-engineer] Deploy to production
```

### APM Integration

```yaml
# apm.yml
dependencies:
  - name: hypertool-mcp
    version: "^0.0.45"
    personas:
      - tta-backend-engineer
      - tta-devops-engineer
```

## Monitoring

### Persona Usage Metrics

```bash
# View persona usage stats
hypertool analytics personas

# View token usage by persona
hypertool analytics tokens --persona tta-backend-engineer

# View tool invocation frequency
hypertool analytics tools --persona tta-devops-engineer
```

## Best Practices

1. **Choose the Right Persona**
   - Use backend engineer for Python/primitives work
   - Use frontend engineer for React/UI work
   - Use devops for CI/CD and infrastructure

2. **Token Budget Awareness**
   - Each persona has optimized token budget
   - Context stays under 2000 tokens
   - 75-81% reduction from baseline

3. **Security First**
   - Personas enforce security boundaries automatically
   - No manual policy configuration needed
   - Path restrictions prevent accidental access

4. **Workflow Composition**
   - Multi-persona workflows for complex tasks
   - Hand off between specialists
   - Each step uses focused context

## Troubleshooting

### Persona Not Found

```bash
# Verify persona files exist
ls -la .hypertool/personas/

# Check persona JSON validity
cat .hypertool/personas/tta-backend-engineer.json | jq .
```

### MCP Server Not Loading

```bash
# Verify server configuration
cat .hypertool/mcp_servers.json | jq .

# Check server availability
hypertool servers list
```

### Token Budget Exceeded

```bash
# View current token usage
hypertool analytics tokens --current

# Switch to persona with higher budget
hypertool persona switch tta-backend-engineer  # 2000 tokens
```

## Related Documentation

- [Hypertool Strategic Integration](../../docs/mcp/HYPERTOOL_STRATEGIC_INTEGRATION.md)
- [Hypertool Quick Start](../../docs/mcp/HYPERTOOL_QUICKSTART.md)
- [TTA.dev Chat Modes](../.tta/chatmodes/)
- [MCP Servers Documentation](../../MCP_SERVERS.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/theinterneti/TTA.dev/issues
- Hypertool Docs: https://github.com/toolprint/hypertool-mcp
- MCP Protocol: https://modelcontextprotocol.io

---

**Last Updated:** 2025-11-14
**Hypertool Version:** 0.0.45+
**Status:** Phase 1 Implementation Complete ✅
