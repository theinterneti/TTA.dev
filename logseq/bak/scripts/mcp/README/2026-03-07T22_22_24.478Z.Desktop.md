# MCP Auto-Integration Scripts

**Automatic MCP server configuration and persona activation for TTA.dev agents**

---

## Quick Start

```bash
# Run complete setup (recommended)
bash setup_auto_integration.sh

# Reload VS Code
# Command Palette → 'Developer: Reload Window'

# Test
# Copilot: @workspace #tta-agent-dev Show me docs for RetryPrimitive
```

---

## Scripts Overview

### 1. `setup_auto_integration.sh`
**Purpose:** One-command complete setup for MCP auto-integration

**What it does:**
1. Validates prerequisites (.hypertool/mcp_servers.json, Python 3)
2. Runs config_parser.py to generate MCP configs
3. Runs persona_activator.py to generate persona configs
4. Validates file discovery paths
5. Shows configuration summary
6. Provides next steps

**Usage:**
```bash
bash setup_auto_integration.sh
```

**Output:**
- `~/.config/mcp/mcp_settings.json` - MCP server configurations
- `.vscode/copilot-persona.json` - Copilot persona config
- `.cline/persona-config.json` - Cline persona config

---

### 2. `config_parser.py`
**Purpose:** Parse and convert MCP server configurations

**Features:**
- Parse `.hypertool/mcp_servers.json`
- Parse repository URIs (GitHub, GitMCP, NPM, Docker)
- Convert to VS Code/Cline format
- Write to `~/.config/mcp/mcp_settings.json`
- Support adding new MCP servers

**Usage:**

```bash
# Generate all configs from Hypertool
python config_parser.py --workspace /path/to/TTA.dev --generate

# Generate VS Code config only
python config_parser.py --workspace /path/to/TTA.dev --vscode-only

# Generate Cline config only
python config_parser.py --workspace /path/to/TTA.dev --cline-only

# Add MCP server from GitHub repo
python config_parser.py \
  --add-repo "https://github.com/owner/repo" \
  --name "custom-server"

# Add MCP server from GitMCP
python config_parser.py \
  --add-repo "https://gitmcp.io/owner/repo" \
  --name "gitmcp-server"

# Add MCP server from NPM package
python config_parser.py \
  --add-repo "npm:@scope/package" \
  --name "npm-server"

# Add MCP server from Docker image
python config_parser.py \
  --add-repo "docker:image-name" \
  --name "docker-server"

# Show current configuration (no changes)
python config_parser.py --workspace /path/to/TTA.dev
```

**Supported Repo URI Formats:**

| Format | Example | Output |
|--------|---------|--------|
| GitMCP | `https://gitmcp.io/owner/repo` | URL-based config |
| GitHub | `https://github.com/owner/repo` | NPX-based config |
| NPM | `npm:@scope/package` | NPX-based config |
| Docker | `docker:image-name` | Docker-based config |

---

### 3. `persona_activator.py`
**Purpose:** Auto-select persona and generate activation configs

**Features:**
- Analyze workspace context (detect backend, frontend, testing, etc.)
- Select appropriate persona based on patterns
- Map MCP tools to personas
- Generate `.vscode/copilot-persona.json`
- Generate `.cline/persona-config.json`
- Integrate with `AGENTS.md`

**Usage:**

```bash
# Analyze workspace and show recommended persona
python persona_activator.py --workspace /path/to/TTA.dev --analyze

# Generate all persona configs
python persona_activator.py --workspace /path/to/TTA.dev --generate

# Generate VS Code config only
python persona_activator.py --workspace /path/to/TTA.dev --vscode

# Generate Cline config only
python persona_activator.py --workspace /path/to/TTA.dev --cline
```

**Workspace Pattern Detection:**

| Pattern | Indicator Files | Selected Persona |
|---------|-----------------|------------------|
| Backend Development | `packages/tta-dev-primitives` | tta-backend-engineer |
| Frontend Development | `apps/observability-ui` | tta-frontend-engineer |
| Testing | `tests/` | tta-testing-specialist |
| Observability | Files with "observability" | tta-observability-expert |
| DevOps | `docker-compose.yml` | tta-devops-engineer |

---

## Configuration Files Generated

### 1. `~/.config/mcp/mcp_settings.json`

**Used by:** VS Code Copilot + Cline

**Format:**
```json
{
  "mcpServers": {
    "context7": {
      "command": "/usr/bin/npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "__description": "Library documentation search"
    },
    "github": {
      "command": "/usr/bin/docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
    // ... 6 more servers
  },
  "cline": {
    "preferredServers": ["context7", "sequential-thinking", "github"],
    "autoConnect": true,
    "maxConcurrentConnections": 3
  }
}
```

---

### 2. `.vscode/copilot-persona.json`

**Used by:** VS Code Copilot

**Format:**
```json
{
  "auto_activate": true,
  "selected_persona": "tta-backend-engineer",
  "context": {
    "detected_patterns": ["backend-development", "testing"],
    "recommended_persona": "tta-backend-engineer"
  },
  "mcp_tools": ["context7", "github", "sequential-thinking"],
  "instructions": {
    "primary": "/path/to/AGENTS.md",
    "persona_specific": null
  },
  "available_personas": [
    "tta-dev-primitives",
    "tta-observability-integration",
    "universal-agent-context"
  ]
}
```

---

### 3. `.cline/persona-config.json`

**Used by:** Cline

**Format:** Same structure as `.vscode/copilot-persona.json`

---

## Persona-to-MCP-Tool Mapping

### tta-backend-engineer
**Tools:** context7, github, sequential-thinking  
**Use Cases:** Python package development, primitives, API design

### tta-frontend-engineer
**Tools:** context7, playwright, github  
**Use Cases:** UI development, React, TypeScript

### tta-testing-specialist
**Tools:** playwright, github, sequential-thinking  
**Use Cases:** Test automation, E2E testing

### tta-observability-expert
**Tools:** grafana, github, context7  
**Use Cases:** Metrics, dashboards, tracing

### tta-devops-engineer
**Tools:** github, grafana, sequential-thinking  
**Use Cases:** CI/CD, infrastructure, Docker

### tta-data-scientist
**Tools:** context7, sequential-thinking  
**Use Cases:** Data analysis, ML integration

---

## Examples

### Example 1: Complete Setup
```bash
# Run from TTA.dev workspace root
bash scripts/mcp/setup_auto_integration.sh

# Expected output:
# ✅ Found 8 MCP servers
# ✅ VS Code config written to: ~/.config/mcp/mcp_settings.json
# ✅ VS Code persona config written to: .vscode/copilot-persona.json
# ✅ Cline persona config written to: .cline/persona-config.json
```

### Example 2: Add Custom MCP Server
```bash
# Add NotebookLM MCP server from GitHub
python scripts/mcp/config_parser.py \
  --workspace . \
  --add-repo "https://github.com/upstash/notebooklm-mcp" \
  --name "notebooklm"

# Result: NotebookLM server added to .hypertool/mcp_servers.json
# and configs regenerated
```

### Example 3: Override Persona Selection
```bash
# First, analyze current workspace
python scripts/mcp/persona_activator.py --workspace . --analyze

# Output shows: recommended_persona: "tta-backend-engineer"

# Override by editing .vscode/copilot-persona.json:
{
  "selected_persona": "tta-observability-expert"
}

# Reload VS Code
```

### Example 4: Validate Configuration
```bash
# Check MCP servers
cat ~/.config/mcp/mcp_settings.json | jq '.mcpServers | keys'

# Check selected persona
cat .vscode/copilot-persona.json | jq '.selected_persona'

# Check MCP tools for persona
cat .vscode/copilot-persona.json | jq '.mcp_tools'
```

---

## Troubleshooting

### Issue: MCP Servers Not Loading

**Symptoms:** Copilot doesn't show MCP tools

**Solution:**
```bash
# Verify config exists
cat ~/.config/mcp/mcp_settings.json

# Regenerate if missing
python scripts/mcp/config_parser.py --workspace . --generate

# Check for syntax errors
jq '.' ~/.config/mcp/mcp_settings.json

# Reload VS Code
```

### Issue: Wrong Persona Selected

**Symptoms:** Copilot assumes incorrect persona

**Solution:**
```bash
# Analyze workspace
python scripts/mcp/persona_activator.py --workspace . --analyze

# Check detected patterns
cat .vscode/copilot-persona.json | jq '.context.detected_patterns'

# Manually override persona
# Edit .vscode/copilot-persona.json and change selected_persona

# Reload VS Code
```

### Issue: Cline Can't Connect to MCP Servers

**Symptoms:** Cline sidebar doesn't show servers

**Solution:**
```bash
# Check Cline preferences
cat ~/.config/mcp/mcp_settings.json | jq '.cline'

# Verify:
# - autoConnect is true
# - preferredServers lists valid servers
# - maxConcurrentConnections is reasonable (3)

# Regenerate if incorrect
python scripts/mcp/config_parser.py --workspace . --generate

# Reload VS Code
```

---

## Development

### Running Tests

```bash
# No formal tests yet, but you can validate:

# 1. Config parser
python scripts/mcp/config_parser.py --workspace . --generate
cat ~/.config/mcp/mcp_settings.json | jq '.mcpServers | length'
# Expected: 8

# 2. Persona activator
python scripts/mcp/persona_activator.py --workspace . --analyze
# Expected: JSON output with selected_persona

# 3. Complete setup
bash scripts/mcp/setup_auto_integration.sh
# Expected: All validation checks pass
```

### Extending Scripts

To add a new persona:

1. Edit `persona_activator.py`:
```python
pattern_to_persona = {
    "backend-development": "tta-backend-engineer",
    "frontend-development": "tta-frontend-engineer",
    # Add new mapping
    "ml-development": "tta-ml-engineer",
}
```

2. Add MCP tool mapping:
```python
persona_tools = {
    "tta-backend-engineer": ["context7", "github", "sequential-thinking"],
    # Add new persona
    "tta-ml-engineer": ["context7", "jupyter-mcp", "mlflow-mcp"],
}
```

3. Test:
```bash
python scripts/mcp/persona_activator.py --workspace . --analyze
```

---

## Dependencies

- **Python 3.x** (standard library only, no external packages)
- **Bash** (for setup script)
- **jq** (optional, for validation)

---

## Related Documentation

- **Complete Implementation Guide:** `../../docs/mcp/AUTO_INTEGRATION_IMPLEMENTATION.md`
- **Status Report:** `../../docs/mcp/AUTO_INTEGRATION_STATUS_REPORT.md`
- **Quick Reference:** `../../docs/mcp/AUTO_INTEGRATION_QUICKREF.md`
- **MCP Servers Registry:** `../../MCP_SERVERS.md`
- **Agent Instructions:** `../../AGENTS.md`

---

## License

Part of TTA.dev - See repository root for license information

---

**Last Updated:** 2025-01-XX  
**Maintained by:** TTA.dev Team  
**Status:** Production-Ready ✅
