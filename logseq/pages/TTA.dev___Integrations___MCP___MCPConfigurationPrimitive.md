# TTA.dev/Integrations/MCP/MCPConfigurationPrimitive

**Comprehensive MCP server configuration validation with adaptive detection**

## Overview

`MCPConfigurationPrimitive` validates all configured MCP servers, checking authentication requirements and providing actionable fix suggestions.

**Package:** `tta-dev-primitives`
**Module:** `tta_dev_primitives.integrations.mcp_config`
**Base Class:** [[TTA.dev/Primitives/WorkflowPrimitive]]

## Import

```python
from tta_dev_primitives.integrations import MCPConfigurationPrimitive
```

## Operation

### `execute()`

Validate all MCP servers in configuration.

**Parameters:**
- `input_data: None` - Not used (set to None)
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with validation results:
- `total_servers: int` - Number of MCP servers detected
- `valid_servers: int` - Number of valid configurations
- `invalid_servers: int` - Number with issues
- `all_valid: bool` - True if all servers valid
- `issues: dict[str, list[str]]` - Issues by server name
- `suggestions: list[str]` - Actionable fix suggestions

**Example:**
```python
validator = MCPConfigurationPrimitive()
result = await validator.execute(None, context)

print(f"Total servers: {result['total_servers']}")
print(f"Valid: {result['valid_servers']}")
print(f"Invalid: {result['invalid_servers']}")

if not result["all_valid"]:
    print("\n🚨 Issues Found:")
    for server, issues in result["issues"].items():
        print(f"\n{server}:")
        for issue in issues:
            print(f"  ❌ {issue}")
    
    print("\n💡 Suggestions:")
    for suggestion in result["suggestions"]:
        print(f"  - {suggestion}")
```

## Adaptive Detection

### `detect_all_mcp_servers()`

Utility function that scans both VS Code Copilot and Cline configurations.

**Scans:**
1. `.vscode/mcp.json` (VS Code Copilot)
2. `~/.config/cline/mcp_settings.json` (Cline)

**Returns:** `list[MCPServerInfo]` with:
- `name: str` - Server name
- `agent_type: str` - "copilot" or "cline"
- `config_path: str` - Path to config file
- `requires_auth: bool` - Whether authentication needed
- `auth_env_var: str | None` - Required environment variable

**Example:**
```python
from tta_dev_primitives.integrations import detect_all_mcp_servers

servers = detect_all_mcp_servers()

for server in servers:
    print(f"{server.name} ({server.agent_type})")
    print(f"  Config: {server.config_path}")
    if server.requires_auth:
        print(f"  Auth: {server.auth_env_var}")
```

## Validation Checks

### Per-Server Checks

For each detected MCP server:

1. **Configuration File Exists**
   - ✅ `.vscode/mcp.json` or `~/.config/cline/mcp_settings.json` present
   - ❌ Missing → "Create [config file path]"

2. **Authentication (if required)**
   - ✅ Required environment variable set (e.g., `GITHUB_TOKEN`)
   - ❌ Missing → "Set [ENV_VAR]: export [ENV_VAR]=..."

3. **Server Configuration**
   - ✅ Server defined in config file
   - ❌ Missing → "Add [server] to [config file]"

### Authentication Requirements

Currently validated servers and their auth requirements:

| Server | Auth Required | Environment Variable |
|--------|---------------|---------------------|
| **github** | ✅ Yes | `GITHUB_TOKEN` |
| **context7** | ❌ No | None (public API) |
| **grafana** | ✅ Yes | `GRAFANA_TOKEN` |
| **database** | ⚠️ Varies | `DATABASE_URL` (if used) |

**Adaptive:** New servers added to config files are auto-detected.

## Usage Patterns

### Pattern 1: CI/CD Health Check

```python
# In CI pipeline
validator = MCPConfigurationPrimitive()
result = await validator.execute(None, WorkflowContext())

if not result["all_valid"]:
    print("❌ MCP configuration invalid")
    for suggestion in result["suggestions"]:
        print(f"  {suggestion}")
    sys.exit(1)

print("✅ All MCP servers configured correctly")
```

### Pattern 2: Developer Onboarding

```python
# Onboarding script
print("Checking MCP configuration...")

validator = MCPConfigurationPrimitive()
result = await validator.execute(None, context)

if result["total_servers"] == 0:
    print("No MCP servers configured yet.")
    print("Run: python examples/mcp_integration_workflow.py --help")
elif not result["all_valid"]:
    print(f"Found {result['invalid_servers']} configuration issues:")
    for suggestion in result["suggestions"]:
        print(f"  • {suggestion}")
else:
    print(f"✅ All {result['total_servers']} MCP servers configured!")
```

### Pattern 3: Pre-Workflow Validation

```python
from tta_dev_primitives import SequentialPrimitive

# Validate MCP before running workflow
workflow = (
    mcp_config_validator >>
    github_operations >>
    context7_lookup >>
    final_processing
)

# Workflow fails fast if MCP not configured
result = await workflow.execute(data, context)
```

### Pattern 4: Self-Healing Configuration

```python
# Attempt auto-fix for common issues
result = await validator.execute(None, context)

if not result["all_valid"]:
    for suggestion in result["suggestions"]:
        if "Set GITHUB_TOKEN" in suggestion:
            # Try to get token from gh CLI
            token = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            if token:
                os.environ["GITHUB_TOKEN"] = token
                print("✅ Auto-configured GITHUB_TOKEN")
```

## Output Format

### Success Case

```json
{
  "total_servers": 2,
  "valid_servers": 2,
  "invalid_servers": 0,
  "all_valid": true,
  "issues": {},
  "suggestions": []
}
```

### Failure Case

```json
{
  "total_servers": 2,
  "valid_servers": 1,
  "invalid_servers": 1,
  "all_valid": false,
  "issues": {
    "github": [
      "GITHUB_TOKEN environment variable not set",
      "GitHub server not in MCP configuration"
    ]
  },
  "suggestions": [
    "Set GITHUB_TOKEN: export GITHUB_TOKEN=$(gh auth token)",
    "Create .vscode/mcp.json with GitHub server configuration",
    "Run: python examples/mcp_integration_workflow.py --setup github"
  ]
}
```

## Observability

Creates OpenTelemetry span with validation metrics:

```python
# Span: mcp_config.validate
# Attributes:
#   - total_servers: 2
#   - valid_servers: 1
#   - invalid_servers: 1
#   - checked_servers: ["github", "context7"]
```

**Metrics:**
- `mcp_config_total_servers` - Number of configured servers
- `mcp_config_valid_servers` - Number passing validation
- `mcp_config_validation_duration_seconds`

## Future-Proofing

### Adaptive Server Detection

No hardcoded server list - scans actual config files:

```python
# Automatically finds new servers
servers = detect_all_mcp_servers()

# Works with:
# - New AI agents (beyond Copilot/Cline)
# - Community MCP servers
# - Custom servers
```

### Authentication Inference

Uses heuristics to detect auth requirements:

```python
def _server_requires_auth(server_name: str) -> bool:
    """Infer if server needs authentication."""
    known_auth_servers = {"github", "grafana", "gitlab", ...}
    
    # Adaptive: Check against known list
    if server_name.lower() in known_auth_servers:
        return True
    
    # Heuristic: API/cloud services usually need auth
    if any(keyword in server_name.lower() 
           for keyword in ["api", "cloud", "auth"]):
        return True
    
    return False  # Default: assume no auth
```

## Testing

### Unit Test

```python
def test_mcp_config_validation_no_servers(tmp_path):
    """Test with no MCP servers configured."""
    validator = MCPConfigurationPrimitive()
    result = await validator.execute(None, WorkflowContext())
    
    assert result["total_servers"] == 0
    assert result["all_valid"] == True  # No servers = valid
```

### Integration Test

```python
@pytest.mark.integration
async def test_mcp_config_validation_real():
    """Test with actual MCP configuration."""
    validator = MCPConfigurationPrimitive()
    result = await validator.execute(None, WorkflowContext())
    
    # Should detect configured servers
    assert result["total_servers"] > 0
    
    # Print issues if any
    if not result["all_valid"]:
        print("Issues found:")
        for server, issues in result["issues"].items():
            print(f"{server}: {issues}")
```

## Related Pages

- [[TTA.dev/Integrations/MCP]] - MCP integration overview
- [[TTA.dev/Integrations/MCP/MCPSetupGuidePrimitive]] - Setup guide generator
- [[detect_all_mcp_servers]] - Detection utility

## Source Code

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/integrations/mcp_config.py`

**Key Functions:**
- `MCPConfigurationPrimitive` - Validation primitive
- `detect_all_mcp_servers()` - Server detection
- `_server_requires_auth()` - Auth inference
- `_get_auth_env_var()` - Env var mapping

## Tags

#mcp-integration #configuration #validation #adaptive-workflows #devops
