# TTA.dev/Integrations/MCP

**Model Context Protocol (MCP) integration primitives for TTA.dev workflows**

## Overview

MCP Integration Primitives provide type-safe, adaptive interfaces to Model Context Protocol servers, enabling workflows to:

- Query library documentation (Context7)
- Manage GitHub repositories (GitHub MCP)
- Access development tools (Grafana, Pylance, etc.)
- Validate MCP server configurations
- Generate contextual setup guides

## Architecture

### Adaptive Configuration Detection

**Problem Solved:** MCP servers configure differently across AI agents (VS Code Copilot, Cline, etc.), causing documentation to drift.

**Solution:** Primitives auto-detect configuration paths and validate setup, providing actionable error messages.

```python
# Auto-detects VS Code or Cline configuration
github_config = GitHubMCPConfig.detect()

# Validates GITHUB_TOKEN and config file
validation = await GitHubMCPConfigValidator().execute(None, context)

# Provides specific fix suggestions
# "Set GITHUB_TOKEN: export GITHUB_TOKEN=$(gh auth token)"
# "Create .vscode/mcp.json with GitHub server configuration"
```

## Core Primitives

### [[TTA.dev/Integrations/MCP/GitHubMCPPrimitive]]

Type-safe interface for GitHub operations via MCP.

**Operations:**
- `create_issue()` - Create GitHub issues
- `search_code()` - Search code across repositories
- `get_pr()` - Retrieve pull request details
- `list_issues()` - List repository issues

**Configuration:**
- Auto-detects: `.vscode/mcp.json` (Copilot) or `~/.config/cline/mcp_settings.json` (Cline)
- Requires: `GITHUB_TOKEN` environment variable
- Validates: Token presence, config file structure

### [[TTA.dev/Integrations/MCP/Context7MCPPrimitive]]

Query library documentation via Context7/Upstash MCP.

**Operations:**
- `get_docs()` - Retrieve library documentation
- `resolve_library()` - Map library names to Context7 IDs

**Configuration:**
- Auto-detects: Same config files as GitHub MCP
- No authentication required (public API)
- Provides setup guidance when not configured

### [[TTA.dev/Integrations/MCP/MCPConfigurationPrimitive]]

Comprehensive health check for all configured MCP servers.

**Features:**
- Detects all MCP servers in configuration
- Validates authentication requirements
- Reports issues with actionable fixes
- Adapts to new servers automatically

### [[TTA.dev/Integrations/MCP/MCPSetupGuidePrimitive]]

Generate contextual setup instructions for specific MCP server.

**Features:**
- Agent-specific guidance (Copilot vs Cline)
- Server-specific authentication steps
- Current, accurate instructions
- Prevents documentation drift

## Utility Functions

### `detect_all_mcp_servers()`

Scans both VS Code Copilot and Cline configuration files to discover all configured MCP servers.

**Returns:** List of `MCPServerInfo` objects with:
- Server name
- Agent type (copilot/cline)
- Config file path
- Authentication requirements

## Usage Patterns

### Pattern 1: GitHub Workflow Integration

```python
from tta_dev_primitives.integrations import GitHubMCPPrimitive
from tta_dev_primitives import WorkflowContext

github = GitHubMCPPrimitive()
context = WorkflowContext(trace_id="issue-creation")

# Create issue from workflow
result = await github.create_issue(
    repo="theinterneti/TTA.dev",
    title="Feature request from user feedback",
    body="User requested: ...",
    labels=["enhancement", "user-feedback"],
    context=context
)

# Use in composed workflow
workflow = (
    analyze_user_feedback >>
    github_create_issue >>
    notify_team
)
```

### Pattern 2: Documentation Lookup in Agent Workflows

```python
from tta_dev_primitives.integrations import Context7MCPPrimitive

context7 = Context7MCPPrimitive()

# Resolve library before querying
library_id = await context7.resolve_library(
    library_name="httpx",
    context=context
)

# Get relevant documentation
docs = await context7.get_docs(
    library=library_id,
    topic="async client usage patterns",
    tokens=5000,
    context=context
)

# Use in learning agent workflow
workflow = (
    identify_unknown_library >>
    context7_lookup_docs >>
    generate_code_with_docs >>
    validate_code
)
```

### Pattern 3: MCP Health Check in CI/CD

```python
from tta_dev_primitives.integrations import MCPConfigurationPrimitive

validator = MCPConfigurationPrimitive()

# Validate all MCP servers
result = await validator.execute(None, context)

if not result["all_valid"]:
    # CI fails with actionable errors
    for server, issues in result["issues"].items():
        print(f"❌ {server}:")
        for issue in issues:
            print(f"  - {issue}")
    raise Exception("MCP configuration invalid")
```

### Pattern 4: Adaptive Setup Guidance

```python
from tta_dev_primitives.integrations import MCPSetupGuidePrimitive

guide = MCPSetupGuidePrimitive()

# Generate agent-specific instructions
result = await guide.execute(
    {"server": "github", "agent": "copilot"},
    context
)

print(result["guide"])
# Outputs step-by-step setup for VS Code Copilot
```

## Design Principles

### 1. Adaptive Configuration

MCP configuration varies by AI agent and evolves over time. Primitives adapt to:
- New AI agents (future tools beyond Copilot/Cline)
- New MCP servers (community-created servers)
- Configuration format changes

### 2. Actionable Errors

Never say "configuration invalid" without explaining how to fix:
```python
# ❌ Bad error
"GitHub MCP not configured"

# ✅ Good error (what we provide)
"GitHub MCP not configured. Fix options:
1. Set GITHUB_TOKEN: export GITHUB_TOKEN=$(gh auth token)
2. Create .vscode/mcp.json with GitHub server configuration
3. Run: python examples/mcp_integration_workflow.py --setup github"
```

### 3. Future-Proof Detection

`detect_all_mcp_servers()` scans config files instead of hardcoding server lists, adapting to new servers automatically.

### 4. Type-Safe Operations

All MCP operations use Pydantic/dataclasses for validation:
```python
@dataclass
class GitHubMCPConfig:
    config_path: str
    agent_type: str
    github_token: str | None
```

## Testing

### Unit Tests

Test adaptive detection with mock configurations:
```python
def test_github_config_detection_copilot(tmp_path):
    # Create mock .vscode/mcp.json
    config = tmp_path / ".vscode" / "mcp.json"
    config.parent.mkdir(parents=True)
    config.write_text('{"github": {...}}')
    
    detected = GitHubMCPConfig.detect()
    assert detected.agent_type == "copilot"
```

### Integration Tests

Test with real MCP servers (requires configuration):
```bash
# Set up test environment
export GITHUB_TOKEN="your-token"

# Run integration tests
uv run python examples/mcp_integration_workflow.py
```

### Example Workflow

See `examples/mcp_integration_workflow.py` for comprehensive demonstration.

## Related Documentation

- [[MCP_SERVERS.md]] - Registry of all MCP servers
- [[docs/ADAPTIVE_MCP_WORKFLOWS_COMPLETE.md]] - Implementation details
- [[PRIMITIVES_CATALOG.md#MCP Integration Primitives]] - API reference

## Future Enhancements

- TODO Add more MCP primitives (Grafana, Pylance, Playwright)
- TODO Create .vscode/mcp.json.example template
- TODO Add Cline-specific setup validation tests
- TODO Implement MCP server health monitoring primitive

## Tags

#mcp-integration #integrations #adaptive-workflows #github #context7
