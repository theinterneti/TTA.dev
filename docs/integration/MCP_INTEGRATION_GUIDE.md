# TTA.dev MCP Integration Guide

**Complete guide for using Model Context Protocol (MCP) servers with Gemini CLI in GitHub Actions**

---

## Overview

This guide documents how TTA.dev integrates MCP servers using the Agent Package Manager (APM) framework to provide advanced AI agent capabilities in automated workflows.

### What is MCP?

**Model Context Protocol (MCP)** is an open standard for connecting AI applications to external tools and data sources. MCP servers expose capabilities that AI agents can use to:

- Read and write files
- Query databases
- Interact with APIs (GitHub, Azure DevOps, etc.)
- Execute specialized operations
- Access external context

### Why APM?

**Agent Package Manager (APM)** provides:

- ✅ Automatic MCP dependency resolution
- ✅ Configuration management for MCP servers
- ✅ Seamless integration with Gemini CLI
- ✅ Environment-aware authentication
- ✅ Workflow orchestration

---

## Architecture

### Dual-Track Approach

TTA.dev uses **two workflow modes**:

#### 1. **Simple Mode** (gemini-invoke.yml)
- **Purpose**: Fast, basic queries
- **Execution**: ~40 seconds
- **MCP**: Disabled
- **Tools**: None
- **Use Cases**: Quick questions, simple analysis

#### 2. **Advanced Mode** (gemini-invoke-advanced.yml)
- **Purpose**: Complex tasks requiring tools
- **Execution**: ~2-3 minutes (includes MCP setup)
- **MCP**: Enabled via APM
- **Tools**: GitHub API, file system, custom tools
- **Use Cases**: PR reviews, test generation, code analysis

### Integration Flow

```
User mentions @gemini-cli-advanced in issue/PR
    ↓
gemini-dispatch.yml (routes to advanced workflow)
    ↓
gemini-invoke-advanced.yml
    ↓
APM installs MCP dependencies (from apm.yml)
    ↓
Gemini CLI executes with MCP tools available
    ↓
Agent uses tools (create_issue, search_code, etc.)
    ↓
Response posted to issue/PR
```

---

## Configuration Files

### 1. apm.yml (Repository Root)

Defines MCP dependencies and agent workflows:

```yaml
name: tta-dev
version: 1.0.0

# MCP Server Dependencies
dependencies:
  mcp:
    - github/github-mcp-server  # GitHub API tools
    # Add more MCP servers as needed

# Predefined Workflows
scripts:
  pr-review: "gemini --yolo -p .github/prompts/pr-review.prompt.md"
  generate-tests: "gemini --yolo -p .github/prompts/generate-tests.prompt.md"
  triage-issue: "gemini --yolo -p .github/prompts/triage-issue.prompt.md"

# Agent Configuration
config:
  gemini:
    model: "gemini-2.5-flash"
    temperature: 0.7
```

### 2. .github/workflows/gemini-invoke-advanced.yml

GitHub Actions workflow using APM:

```yaml
- name: 'Run Agent with APM (MCP Enabled)'
  uses: 'danielmeppiel/action-apm-cli@v1'
  with:
    script: '${{ inputs.apm_script }}'
  env:
    GITHUB_COPILOT_CHAT: '${{ secrets.GITHUB_COPILOT_CHAT }}'
    GEMINI_API_KEY: '${{ secrets.GOOGLE_AI_STUDIO_API_KEY }}'
```

### 3. .github/prompts/*.prompt.md

Specialized agent instructions:

- `pr-review.prompt.md`: Code review guidelines
- `generate-tests.prompt.md`: Test generation instructions
- `triage-issue.prompt.md`: Issue classification logic

---

## Setup Instructions

### Step 1: Create GitHub PAT

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Create new **fine-grained token** with:
   - Resource owner: [your organization/user]
   - Repository access: Select TTA.dev repository
   - Permissions:
     - Contents: Read and write
     - Issues: Read and write
     - Pull requests: Read and write
     - Metadata: Read-only (automatic)
3. Copy token value

### Step 2: Add Repository Secret

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GITHUB_COPILOT_CHAT`
4. Value: [paste token]
5. Click "Add secret"

### Step 3: Verify Configuration

Files should exist:
- ✅ `apm.yml` (repository root)
- ✅ `.github/workflows/gemini-invoke-advanced.yml`
- ✅ `.github/prompts/pr-review.prompt.md`
- ✅ `.github/prompts/generate-tests.prompt.md`
- ✅ `.github/prompts/triage-issue.prompt.md`

### Step 4: Test Integration

Post comment in issue:
```
@gemini-cli-advanced analyze this issue
```

Expected: Agent responds with analysis using GitHub API tools

---

## Available MCP Tools

### GitHub MCP Server Tools

When GitHub MCP Server is enabled, the agent can use:

| Tool | Description | Example Use Case |
|------|-------------|------------------|
| `create_issue` | Create new GitHub issue | Generate follow-up tasks |
| `search_code` | Search repository code | Find similar patterns |
| `create_pull_request` | Open new PR | Automated refactoring |
| `create_or_update_file` | Modify files | Documentation updates |
| `get_file_contents` | Read file content | Code review analysis |
| `list_issues` | List repository issues | Find related issues |
| `push_files` | Commit changes | Automated fixes |

**Example Tool Usage in Prompt:**

```markdown
# In pr-review.prompt.md

## Available Tools

Use these MCP tools to gather information:

- `get_file_contents`: Read PR files
- `search_code`: Find similar patterns
- `create_issue`: Create follow-up tasks

## Instructions

1. Use `get_file_contents` to read changed files
2. Use `search_code` to find existing patterns
3. If you find issues, use `create_issue` to track them
```

---

## Usage Patterns

### Pattern 1: Automated PR Review

**Trigger:**
```
@gemini-cli-advanced review this PR
```

**What Happens:**
1. APM loads GitHub MCP Server
2. Agent reads PR files using `get_file_contents`
3. Searches codebase using `search_code`
4. Analyzes against TTA.dev standards
5. Posts comprehensive review
6. Creates follow-up issues if needed

**Expected Response Time:** 2-3 minutes

### Pattern 2: Test Generation

**Trigger:**
```
@gemini-cli-advanced generate tests for platform/primitives/src/tta_dev_primitives/core/router.py
```

**What Happens:**
1. Reads target file using MCP tools
2. Analyzes code structure
3. Generates comprehensive tests
4. Creates PR with test file
5. Posts summary in issue

**Expected Response Time:** 3-4 minutes

### Pattern 3: Issue Triage

**Trigger:**
```
@gemini-cli-advanced triage this issue
```

**What Happens:**
1. Reads issue content
2. Searches for related issues
3. Classifies and labels
4. Suggests action plan
5. Updates issue labels

**Expected Response Time:** 1-2 minutes

### Pattern 4: Documentation Sync

**Trigger:**
```
@gemini-cli-advanced sync docs for CachePrimitive
```

**What Happens:**
1. Reads primitive source code
2. Reads current documentation
3. Identifies discrepancies
4. Updates docs via `create_or_update_file`
5. Posts summary of changes

**Expected Response Time:** 2-3 minutes

---

## Prompt Engineering for MCP

### Effective Prompt Structure

```markdown
# Agent Role Definition
You are an expert [role] for TTA.dev...

## Context
Read GEMINI.md and AGENTS.md for project-specific guidance.

## Your Task
[Specific instructions]

## Available Tools
Use these MCP tools:
- `tool_name`: [description]
- `tool_name`: [description]

## Output Format
[Structured format for response]

## Standards
[Project-specific requirements]
```

### Tool Usage Guidelines

**DO:**
- ✅ Specify which tools to use
- ✅ Provide tool usage context
- ✅ Set expectations for tool results
- ✅ Handle tool failures gracefully

**DON'T:**
- ❌ Assume tools are available without APM config
- ❌ Use tools for operations requiring human review
- ❌ Expect instant tool execution (allow time)
- ❌ Ignore tool permissions/limitations

---

## Performance Considerations

### Execution Times

| Mode | MCP Enabled | Typical Duration | Use Case |
|------|-------------|------------------|----------|
| Simple | No | 40 seconds | Basic queries |
| Advanced | Yes | 2-3 minutes | Tool-enabled tasks |
| Complex | Yes + Multiple Tools | 3-5 minutes | Multi-step workflows |

### Optimization Tips

1. **Use Simple Mode When Possible**
   - No MCP overhead
   - Faster responses
   - Good for basic questions

2. **Batch Operations**
   - Group related tool calls
   - Reduce workflow invocations
   - Use predefined scripts

3. **Cache Results**
   - Store analysis results as artifacts
   - Reuse across workflow steps
   - Avoid redundant tool calls

4. **Selective MCP Loading**
   - Only load required MCP servers
   - Configure in apm.yml dependencies
   - Disable unused servers

---

## Troubleshooting

### Issue: APM Action Not Finding MCP Server

**Symptom:**
```
Error: MCP server 'github/github-mcp-server' not found
```

**Solutions:**
1. Verify apm.yml syntax:
   ```yaml
   dependencies:
     mcp:
       - github/github-mcp-server  # Correct format
   ```

2. Check APM action version:
   ```yaml
   uses: 'danielmeppiel/action-apm-cli@v1'  # Use v1 or latest
   ```

3. Ensure PAT secret exists:
   ```bash
   gh secret list | grep GITHUB_COPILOT_CHAT
   ```

### Issue: Tool Calls Failing

**Symptom:**
```
Tool 'create_issue' execution failed: 401 Unauthorized
```

**Solutions:**
1. Verify PAT permissions:
   - Requires `repo` scope
   - Check token expiration

2. Ensure environment variable:
   ```yaml
   env:
     GITHUB_COPILOT_CHAT: '${{ secrets.GITHUB_COPILOT_CHAT }}'
   ```

3. Check workflow permissions:
   ```yaml
   permissions:
     issues: 'write'
     pull-requests: 'write'
   ```

### Issue: Response Not Posted

**Symptom:**
Agent executes but doesn't post to issue

**Solutions:**
1. Check issue_number input:
   ```yaml
   issue_number: '${{ inputs.issue_number || github.event.issue.number }}'
   ```

2. Verify Post Response step:
   ```yaml
   - name: 'Post Response to Issue/PR'
     if: always()  # Ensure this runs
   ```

3. Check GitHub token:
   ```yaml
   github-token: '${{ secrets.GITHUB_TOKEN }}'  # Has issue write permission
   ```

### Issue: Slow Execution (> 5 minutes)

**Symptom:**
Workflow takes too long

**Solutions:**
1. **Reduce MCP servers**: Only load what you need
2. **Use caching**: Store intermediate results
3. **Optimize prompts**: Be specific about tool usage
4. **Check tool performance**: Some tools are slower than others

---

## Advanced Usage

### Custom MCP Servers

Add your own MCP servers:

```yaml
# apm.yml
dependencies:
  mcp:
    - github/github-mcp-server
    - your-org/custom-mcp-server  # Your custom MCP
```

### Multi-Step Workflows

Chain multiple agent operations:

```yaml
# apm.yml
scripts:
  full-review:
    - analyze-code
    - generate-tests
    - update-docs
    - create-summary
```

### Conditional MCP Loading

Enable MCP only when needed:

```yaml
# In workflow
- name: 'Determine MCP Need'
  id: 'check_mcp'
  run: |
    if [[ "${{ inputs.command }}" == "review" ]]; then
      echo "enable_mcp=true" >> $GITHUB_OUTPUT
    else
      echo "enable_mcp=false" >> $GITHUB_OUTPUT
    fi

- name: 'Run with APM'
  if: steps.check_mcp.outputs.enable_mcp == 'true'
  uses: 'danielmeppiel/action-apm-cli@v1'
  # ...
```

---

## Security Best Practices

### Secret Management

1. **Use Repository Secrets**
   - Never hardcode PATs
   - Rotate tokens regularly
   - Use least-privilege scopes

2. **Scope Limitation**
   ```yaml
   # Minimal required scopes
   PAT Scopes:
     - repo (full repository access)
     - write:discussion (if needed)
   ```

3. **Token Rotation**
   - Set expiration on PATs
   - Automate rotation workflow
   - Monitor for unauthorized use

### Permission Controls

```yaml
# apm.yml - Define what agent can/cannot do
permissions:
  read:
    - packages/**/*.py
    - docs/**/*.md

  write:
    - docs/**/*.md  # Can update docs

  restricted:
    - .github/workflows/**/*.yml  # Cannot modify workflows
```

### Audit Logging

```yaml
# Enable telemetry in apm.yml
telemetry:
  enabled: true
  metrics:
    - tool_calls
    - execution_time
    - success_rate
```

---

## Resources

### Documentation

- **APM Framework**: [danielmeppiel/action-apm-cli](https://github.com/danielmeppiel/action-apm-cli)
- **MCP Specification**: [Model Context Protocol](https://modelcontextprotocol.io)
- **Gemini CLI**: [@google/gemini-cli](https://www.npmjs.com/package/@google/gemini-cli)
- **GitHub MCP Server**: [github/github-mcp-server](https://github.com/github/github-mcp-server)

### TTA.dev Files

- `GEMINI.md`: Project context for agent
- `AGENTS.md`: Agent-specific instructions
- `PRIMITIVES_CATALOG.md`: Primitive reference
- `.github/instructions/*.instructions.md`: Coding standards

### Related Guides

- [Gemini CLI Integration Success](GEMINI_CLI_INTEGRATION_SUCCESS.md)
- [GitHub Blog Implementation](docs/guides/GITHUB_BLOG_IMPLEMENTATION.md)
- [Copilot Toolsets Guide](docs/guides/copilot-toolsets-guide.md)

---

## Next Steps

### For Basic Usage

1. ✅ Test simple mode: `@gemini-cli What is TTA.dev?`
2. ⏳ Add PAT secret for advanced mode
3. ⏳ Test advanced mode: `@gemini-cli-advanced analyze this issue`

### For Production Deployment

1. ⏳ Create GEMINI.md context file
2. ⏳ Configure additional MCP servers
3. ⏳ Set up monitoring/telemetry
4. ⏳ Define custom workflows in apm.yml
5. ⏳ Train team on prompt patterns

### For Advanced Features

1. ⏳ Add custom MCP server for TTA.dev-specific tools
2. ⏳ Implement multi-step workflows
3. ⏳ Configure conditional MCP loading
4. ⏳ Set up result caching
5. ⏳ Integrate with CI/CD pipelines

---

**Last Updated:** November 1, 2025
**Status:** Implementation Complete - Awaiting PAT Configuration
**Next Action:** Add GITHUB_COPILOT_CHAT secret for advanced mode testing
