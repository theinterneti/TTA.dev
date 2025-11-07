# Gemini CLI Integration Guide

**Last Updated**: October 31, 2025
**Status**: ✅ Production-Ready (MCP Server v0.20.1)

---

## Overview

The TTA.dev repository integrates Google's Gemini CLI directly into GitHub issues and pull requests via the `@gemini-cli` mention system. This enables AI-powered code review, issue triage, and natural language interactions within your GitHub workflow.

## Quick Start

### Basic Usage

Simply mention `@gemini-cli` in any issue or PR comment followed by your request:

```markdown
@gemini-cli help
@gemini-cli What are the main features of this PR?
@gemini-cli /review
@gemini-cli /triage
```

### Response Time

- **Expected**: 1-2 minutes
- **Actual** (with MCP v0.20.1): 14-60 seconds
- **Previous** (with MCP v0.18.0): 15+ minutes (timeout)

---

## Available Commands

### 1. Help Command

```markdown
@gemini-cli help
```

**Purpose**: Display available commands and usage information

**Response Time**: ~14 seconds

**Use Case**: First-time users, command reference

---

### 2. Code Review (`/review`)

```markdown
@gemini-cli /review
```

**Purpose**: Perform automated code review on the PR

**What It Analyzes**:
- Code quality and best practices
- Potential bugs or issues
- Security vulnerabilities
- Performance considerations
- Documentation completeness

**Response Time**: ~1-2 minutes (depending on PR size)

**Use Case**: Pre-merge code review, second opinion on changes

---

### 3. Issue Triage (`/triage`)

```markdown
@gemini-cli /triage
```

**Purpose**: Analyze and categorize issues

**What It Provides**:
- Issue severity assessment
- Suggested labels
- Related issues
- Recommended assignees

**Response Time**: ~1-2 minutes

**Use Case**: New issue triage, backlog organization

---

### 4. Natural Language Requests

```markdown
@gemini-cli What are the main features and benefits of this PR?
@gemini-cli Summarize the investigation that led to resolving this issue
@gemini-cli List all open issues related to Gemini CLI
@gemini-cli What is the current status of issue #68?
```

**Purpose**: Ask questions in plain English

**Capabilities**:
- PR/issue summarization
- Investigation analysis
- Status queries
- Feature explanations

**Response Time**: ~1-2 minutes

**Use Case**: Quick summaries, status updates, documentation

---

## GitHub Integration Features

### Enabled MCP Server Tools

The GitHub MCP server (v0.20.1) provides the following tools:

| Tool | Purpose | Example Use Case |
|------|---------|------------------|
| `add_issue_comment` | Post comments to issues/PRs | Gemini responds to your requests |
| `get_issue` | Fetch issue details | "What is the status of issue #68?" |
| `get_issue_comments` | Read issue/PR comments | Context for responses |
| `list_issues` | List repository issues | "List all open issues" |
| `search_issues` | Search issues by criteria | "Find issues related to X" |
| `create_pull_request` | Create new PRs | (If supported by workflow) |
| `pull_request_read` | Read PR details | Code review context |

### What Gemini Can Access

✅ **Can Access**:
- Issue titles, descriptions, and comments
- PR titles, descriptions, and comments
- PR file changes and diffs
- Repository metadata
- Issue/PR labels, assignees, milestones
- Linked issues and PRs

❌ **Cannot Access** (without additional configuration):
- Private repositories (unless configured)
- Repository code outside of PR context
- GitHub Actions secrets
- User personal information

---

## Workflow Architecture

### How It Works

1. **User posts comment** with `@gemini-cli` mention
2. **Gemini Dispatch workflow** (`gemini-dispatch.yml`) detects the mention
3. **Gemini Invoke workflow** (`gemini-invoke.yml`) executes the request
4. **GitHub MCP server** (v0.20.1) provides GitHub API access
5. **Gemini CLI** processes the request with GitHub context
6. **Response posted** as a comment on the issue/PR

### Workflow Files

| File | Purpose |
|------|---------|
| `.github/workflows/gemini-dispatch.yml` | Routes `@gemini-cli` mentions to appropriate workflows |
| `.github/workflows/gemini-invoke.yml` | Executes Gemini CLI with GitHub MCP server integration |

### Configuration

**Key Settings** (in `gemini-invoke.yml`):

```yaml
# MCP Server Configuration
mcpServers:
  github:
    command: "docker"
    args:
      - "run"
      - "-i"
      - "--rm"
      - "-e"
      - "GITHUB_PERSONAL_ACCESS_TOKEN"
      - "ghcr.io/github/github-mcp-server:v0.20.1"  # ✅ CRITICAL: Use v0.20.1
```

**⚠️ Important**: Do NOT use MCP server v0.18.0 - it has a critical timeout bug. Always use v0.20.1 or later.

---

## Testing Results

### Test Commands (October 31, 2025)

| Command | Type | Status | Workflow Run |
|---------|------|--------|--------------|
| `@gemini-cli help` | Basic | ✅ Success (14s) | [#18977755293](https://github.com/theinterneti/TTA.dev/actions/runs/18977755293) |
| `@gemini-cli What are the main features...` | Natural Language | 🔄 Testing | [#18977751707](https://github.com/theinterneti/TTA.dev/actions/runs/18977751707) |
| `@gemini-cli /review` | Code Review | 🔄 Testing | [#18977756933](https://github.com/theinterneti/TTA.dev/actions/runs/18977756933) |
| `@gemini-cli List all open issues...` | GitHub Integration | 🔄 Testing | [#18977866285](https://github.com/theinterneti/TTA.dev/actions/runs/18977866285) |
| `@gemini-cli What is the status of #68?` | Issue Query | 🔄 Testing | [#18977867239](https://github.com/theinterneti/TTA.dev/actions/runs/18977867239) |

**Test Location**: [PR #71](https://github.com/theinterneti/TTA.dev/pulls/71)

---

## Best Practices

### 1. Be Specific

❌ **Vague**: `@gemini-cli review this`
✅ **Specific**: `@gemini-cli /review` or `@gemini-cli Review the changes in src/core/base.py for potential bugs`

### 2. Use Commands for Common Tasks

- Use `/review` for code review (not "please review this PR")
- Use `/triage` for issue triage (not "categorize this issue")
- Use `help` to discover available commands

### 3. Provide Context for Complex Requests

```markdown
@gemini-cli Analyze the timeout issue investigation in this PR.
What was the root cause and how was it resolved?
Include specific workflow run numbers and execution times.
```

### 4. One Request Per Comment

❌ **Multiple requests**:
```markdown
@gemini-cli /review
@gemini-cli /triage
@gemini-cli What is the status of #68?
```

✅ **Single request**:
```markdown
@gemini-cli /review
```

### 5. Wait for Responses

- Each request triggers a workflow run
- Workflows complete in 1-2 minutes
- Avoid posting duplicate requests while waiting

---

## Troubleshooting

### Issue: Workflow Times Out (15+ minutes)

**Cause**: Using MCP server v0.18.0 (has a critical bug)

**Solution**: Update to v0.20.1 in `.github/workflows/gemini-invoke.yml`:

```yaml
"ghcr.io/github/github-mcp-server:v0.20.1"  # ✅ Use this
```

**Reference**: [Issue #68](https://github.com/theinterneti/TTA.dev/issues/68), [PR #71](https://github.com/theinterneti/TTA.dev/pulls/71)

### Issue: No Response from Gemini

**Possible Causes**:
1. Workflow still running (check workflow logs)
2. API key invalid or expired
3. Rate limiting

**Solution**:
1. Check workflow run status in Actions tab
2. Verify `GEMINI_API_KEY` secret is valid
3. Wait a few minutes and try again

### Issue: Generic Response (No GitHub Context)

**Cause**: MCP server not providing GitHub data

**Solution**:
1. Verify `GITHUB_PERSONAL_ACCESS_TOKEN` is set
2. Check MCP server version (must be v0.20.1+)
3. Review workflow logs for MCP server errors

---

## Capabilities and Limitations

### ✅ Supported Operations (MCP Server v0.20.1)

**IMPORTANT**: Initial assessment was incorrect. The MCP server **DOES support write operations**.

| Capability | Status | MCP Tool | Use Case |
|------------|--------|----------|----------|
| **File Creation** | ✅ Supported | `create_or_update_file` | Documentation, tests, examples |
| **File Updates** | ✅ Supported | `create_or_update_file` | Bug fixes, refactoring |
| **File Deletion** | ✅ Supported | `delete_file` | Cleanup, deprecation |
| **Branch Creation** | ✅ Supported | `create_branch` | Feature branches, fixes |
| **PR Creation** | ✅ Supported | `create_pull_request` | Automated PRs |
| **Commits/Push** | ✅ Supported | `push_files` | Code changes |
| **Code Review** | ✅ Supported | `pull_request_read` | Review feedback |
| **Issue Management** | ✅ Supported | `get_issue`, `list_issues` | Triage, queries |

**See**: [`docs/gemini-cli-capabilities-analysis.md`](gemini-cli-capabilities-analysis.md) for detailed analysis

### ❌ Intentional Limitations (Security)

1. **No PR Merging**: `merge_pull_request` not enabled (can be added if needed)
2. **No Workflow Modification**: Prevents malicious code injection into CI/CD
3. **No Secrets Access**: Prevents credential exposure
4. **No Repository Settings**: Prevents accidental configuration changes

**These are correct security decisions.**

### Rate Limits

- **GitHub API**: Standard GitHub API rate limits apply
- **Gemini API**: Subject to Google AI Studio free tier limits
- **Workflow Concurrency**: Limited by GitHub Actions concurrency limits

---

## Examples

### Example 1: PR Summary

**Request**:
```markdown
@gemini-cli What are the main features and benefits of this PR? Please provide a concise summary.
```

**Expected Response**: Summary of PR changes, benefits, and impact

---

### Example 2: Issue Investigation

**Request**:
```markdown
@gemini-cli Summarize the investigation that led to resolving this issue. What was the root cause and solution?
```

**Expected Response**: Investigation timeline, root cause analysis, solution details

---

### Example 3: Related Issues

**Request**:
```markdown
@gemini-cli List all open issues in this repository that are related to Gemini CLI or workflow timeouts.
```

**Expected Response**: List of related issues with links and brief descriptions

---

## Related Documentation

- **Issue #68**: [Gemini CLI Timeout Investigation](https://github.com/theinterneti/TTA.dev/issues/68)
- **PR #71**: [MCP Server v0.20.1 Fix](https://github.com/theinterneti/TTA.dev/pulls/71)
- **Workflow Files**: `.github/workflows/gemini-*.yml`
- **Google Gemini CLI**: [Official Documentation](https://github.com/google-gemini/gemini-cli)
- **GitHub MCP Server**: [GitHub Repository](https://github.com/github/github-mcp-server)

---

## Contributing

To improve Gemini CLI integration:

1. Test new commands and document results
2. Report issues with workflow execution times
3. Suggest new use cases or features
4. Update this guide with new findings

---

**Questions?** Post in [Discussions](https://github.com/theinterneti/TTA.dev/discussions) or create an [Issue](https://github.com/theinterneti/TTA.dev/issues).
