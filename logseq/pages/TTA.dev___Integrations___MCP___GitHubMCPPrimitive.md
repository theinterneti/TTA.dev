# TTA.dev/Integrations/MCP/GitHubMCPPrimitive

**Type-safe interface for GitHub MCP operations with adaptive configuration detection**

## Overview

`GitHubMCPPrimitive` provides programmatic access to GitHub repositories via Model Context Protocol, enabling workflows to create issues, search code, manage PRs, and more.

**Package:** `tta-dev-primitives`
**Module:** `tta_dev_primitives.integrations.github_mcp_primitive`
**Base Class:** [[TTA.dev/Primitives/WorkflowPrimitive]]

## Import

```python
from tta_dev_primitives.integrations import GitHubMCPPrimitive
```

## Operations

### `create_issue()`

Create a new GitHub issue in a repository.

**Parameters:**
- `repo: str` - Repository in format "owner/name"
- `title: str` - Issue title
- `body: str` - Issue description (Markdown supported)
- `labels: list[str] | None` - Optional labels
- `assignees: list[str] | None` - Optional assignees
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with created issue details

**Example:**
```python
github = GitHubMCPPrimitive()
result = await github.create_issue(
    repo="theinterneti/TTA.dev",
    title="Add caching to LLM calls",
    body="Implement CachePrimitive for LLM responses",
    labels=["enhancement", "performance"],
    context=context
)
print(f"Created issue #{result['number']}")
```

### `search_code()`

Search for code across GitHub repositories.

**Parameters:**
- `query: str` - Search query (GitHub code search syntax)
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with search results

**Example:**
```python
results = await github.search_code(
    query="CachePrimitive language:python org:theinterneti",
    context=context
)
for item in results['items']:
    print(f"{item['path']} in {item['repository']}")
```

### `get_pr()`

Retrieve pull request details.

**Parameters:**
- `repo: str` - Repository in format "owner/name"
- `pr_number: int` - Pull request number
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with PR details

**Example:**
```python
pr = await github.get_pr(
    repo="theinterneti/TTA.dev",
    pr_number=42,
    context=context
)
print(f"PR: {pr['title']}")
print(f"State: {pr['state']}")
print(f"Mergeable: {pr['mergeable']}")
```

### `list_issues()`

List issues in a repository.

**Parameters:**
- `repo: str` - Repository in format "owner/name"
- `state: str` - "open", "closed", or "all"
- `labels: list[str] | None` - Filter by labels
- `context: WorkflowContext` - Execution context

**Returns:** `dict` with list of issues

**Example:**
```python
issues = await github.list_issues(
    repo="theinterneti/TTA.dev",
    state="open",
    labels=["bug", "high-priority"],
    context=context
)
print(f"Found {len(issues['items'])} issues")
```

## Configuration

### Adaptive Detection

`GitHubMCPConfig.detect()` auto-discovers configuration:

1. **VS Code Copilot:** `.vscode/mcp.json`
2. **Cline:** `~/.config/cline/mcp_settings.json`

**Returns:** `GitHubMCPConfig` with:
- `config_path: str` - Detected config file path
- `agent_type: str` - "copilot" or "cline"
- `github_token: str | None` - GITHUB_TOKEN from environment

### Validation

`GitHubMCPConfigValidator` checks:
- ✅ `GITHUB_TOKEN` environment variable set
- ✅ MCP configuration file exists
- ✅ GitHub server configured in MCP settings

**Example:**
```python
from tta_dev_primitives.integrations import GitHubMCPConfigValidator

validator = GitHubMCPConfigValidator()
result = await validator.execute(None, context)

if not result["valid"]:
    for issue in result["issues"]:
        print(f"❌ {issue}")
```

### Setup Instructions

If configuration is missing, primitive provides actionable errors:

```
GitHub MCP not configured. Fix options:

1. Set GITHUB_TOKEN:
   export GITHUB_TOKEN=$(gh auth token)

2. Create .vscode/mcp.json:
   {
     "mcpServers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_TOKEN": "${GITHUB_TOKEN}"
         }
       }
     }
   }

3. Get setup guide:
   python examples/mcp_integration_workflow.py --setup github
```

## Usage Patterns

### Pattern 1: Issue Creation from Feedback

```python
from tta_dev_primitives import SequentialPrimitive

workflow = (
    analyze_user_feedback >>
    extract_feature_request >>
    github.create_issue >>
    notify_product_team
)
```

### Pattern 2: Code Search for Examples

```python
# Find implementation examples
results = await github.search_code(
    query="RetryPrimitive language:python",
    context=context
)

# Learn from existing code
for result in results['items']:
    code_snippet = result['text_matches'][0]['fragment']
    # Use in LLM prompt for code generation
```

### Pattern 3: PR Review Workflow

```python
# Get PR details
pr = await github.get_pr(
    repo="theinterneti/TTA.dev",
    pr_number=pr_number,
    context=context
)

# Analyze changes
if pr['changed_files'] > 50:
    # Large PR - needs extra review
    await github.create_issue(
        repo="theinterneti/TTA.dev",
        title=f"Large PR review needed: #{pr_number}",
        body=f"PR has {pr['changed_files']} changed files",
        labels=["review-needed"],
        context=context
    )
```

## Error Handling

### Configuration Errors

```python
try:
    result = await github.create_issue(...)
except Exception as e:
    if "GITHUB_TOKEN not found" in str(e):
        # Provide setup instructions
        print("Set GITHUB_TOKEN: export GITHUB_TOKEN=$(gh auth token)")
    elif "MCP configuration not found" in str(e):
        # Guide to create config file
        print("Create .vscode/mcp.json with GitHub server")
```

### Rate Limiting

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Add retry for rate limit errors
resilient_github = RetryPrimitive(
    primitive=github,
    max_retries=3,
    backoff_strategy="exponential"
)
```

## Observability

All operations automatically create OpenTelemetry spans:

```python
# Span: github_mcp.create_issue
# Attributes:
#   - repo: "theinterneti/TTA.dev"
#   - issue_title: "..."
#   - labels: ["enhancement"]
#   - result_issue_number: 123
```

**Metrics:**
- `github_mcp_operation_duration_seconds{operation="create_issue"}`
- `github_mcp_operation_total{operation="create_issue", status="success"}`

## Testing

### Unit Test with Mock

```python
from tta_dev_primitives.testing import MockPrimitive

# Mock GitHub operations
mock_github = MockPrimitive(
    return_value={"number": 123, "title": "Test issue"}
)

workflow = analyze_feedback >> mock_github >> notify_team
result = await workflow.execute(data, context)

assert mock_github.call_count == 1
```

### Integration Test (Requires Setup)

```python
import pytest

@pytest.mark.integration
async def test_github_create_issue_real():
    # Requires GITHUB_TOKEN and MCP configuration
    github = GitHubMCPPrimitive()
    result = await github.create_issue(
        repo="theinterneti/TTA.dev-test",
        title="Integration test issue",
        body="Created by automated test",
        labels=["test"],
        context=WorkflowContext()
    )
    assert result["number"] > 0
```

## Related Pages

- [[TTA.dev/Integrations/MCP]] - MCP integration overview
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base primitive class
- [[MCP_SERVERS.md#GitHub MCP Server]] - MCP server documentation

## Source Code

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/integrations/github_mcp_primitive.py`

**Key Classes:**
- `GitHubMCPPrimitive` - Main primitive
- `GitHubMCPConfig` - Configuration detection
- `GitHubMCPConfigValidator` - Validation primitive

## Tags

#github #mcp-integration #workflow-primitive #integrations
