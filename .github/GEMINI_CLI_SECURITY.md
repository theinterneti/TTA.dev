# Gemini CLI Security Model

This document explains the security model and safeguards for the Gemini CLI workflow that requires `contents: write` permission.

## Overview

The Gemini CLI workflow requires elevated `contents: write` permission to perform automated code changes through pull requests. This document explains why this permission is necessary, what safeguards are in place, and what alternatives were considered.

## Why `contents: write` is Required

The workflow uses the [GitHub MCP Server](https://github.com/github/github-mcp-server) which provides tools for repository automation. The following operations require `contents: write` permission:

| Tool | Purpose | Permission Required |
|------|---------|-------------------|
| `create_or_update_file` | Create or modify files in feature branches | `contents: write` |
| `push_files` | Commit and push changes to branches | `contents: write` |
| `create_branch` | Create feature branches for PRs | `contents: write` |
| `delete_file` | Remove files (cleanup operations) | `contents: write` |
| `create_pull_request` | Create PRs from feature branches | `contents: write` + `pull-requests: write` |

### Why Not `contents: read`?

GitHub's REST API requires `contents: write` for ANY modification to repository files, including:
- Creating new files
- Updating existing files
- Creating branches
- Pushing commits

There is no intermediate permission level between `read` and `write` for repository contents.

## Security Safeguards

Multiple layers of security protect against misuse of write permissions:

### 1. Explicit Tool Whitelist

The workflow configuration (lines 108-127 in `gemini-invoke.yml`) explicitly lists the 17 allowed MCP tools:

```yaml
includeTools:
  - add_issue_comment
  - get_issue
  - get_issue_comments
  - list_issues
  - search_issues
  - create_pull_request
  - pull_request_read
  - list_pull_requests
  - search_pull_requests
  - create_branch
  - create_or_update_file
  - delete_file
  - fork_repository
  - get_commit
  - get_file_contents
  - list_commits
  - push_files
  - search_code
```

**Only these 17 tools are available to the AI agent.** Any other GitHub API operations are blocked.

### 2. Protected Paths Restriction

The workflow prompt (lines 195-205) explicitly forbids modifications to security-critical paths:

- `.github/workflows/` - Workflow files
- `.github/actions/` - Custom actions  
- `.github/scripts/` - Workflow scripts
- `CODEOWNERS` - Code ownership rules
- Any files containing secrets or credentials

**The AI agent is instructed to refuse any requests to modify these paths.**

### 3. Branch Protection Rules

All changes must go through pull requests. Direct pushes to `main` are prevented by:
- GitHub branch protection rules (configured in repository settings)
- Workflow creates feature branches (e.g., `copilot/feature-name`)
- Pull request review required before merge

**No changes can reach `main` without human review.**

### 4. Human Approval Requirement

The workflow prompt (lines 218-226) requires explicit human approval:

1. AI agent analyzes the request and posts a plan
2. Human reviewer must comment `/approve` to proceed
3. AI agent monitors for approval before executing
4. If approval is denied or issue is closed, workflow terminates

**No automated changes occur without explicit `/approve` command.**

### 5. Timeout Protection

The workflow has a 15-minute timeout (line 22):

```yaml
timeout-minutes: 15
```

**This prevents runaway operations and limits resource consumption.**

### 6. Audit Trail

All operations are fully auditable:
- Git commits show what was changed and when
- Pull requests show the full diff before merge
- Workflow logs show all API calls made
- GitHub audit log tracks all permission usage

**Every change is traceable and reviewable.**

### 7. Token Scope Limitation

When using GitHub App authentication (optional), permissions are explicitly scoped:

```yaml
permission-contents: 'write'
permission-issues: 'write'
permission-pull-requests: 'write'
```

**The token only has the minimum required permissions, not full admin access.**

## What Cannot Be Done

Even with `contents: write`, the workflow **cannot**:

❌ Modify workflow files (`.github/workflows/`) - blocked by prompt  
❌ Access repository secrets - not granted in permissions  
❌ Push directly to `main` - blocked by branch protection  
❌ Bypass PR review - branch protection requires review  
❌ Delete the repository - requires admin permission (not granted)  
❌ Modify repository settings - requires admin permission (not granted)  
❌ Access other repositories - token is scoped to current repo only  
❌ Execute arbitrary shell commands as repository operations - tool whitelist enforced  

## Alternatives Considered

### Alternative 1: Separate Service Account

**Approach**: Use a dedicated GitHub App or service account with restricted permissions.

**Pros**:
- Clearer separation of concerns
- Could use more granular permissions if available

**Cons**:
- GitHub doesn't offer more granular permissions than `contents: write/read`
- Additional complexity in token management
- Same permission level ultimately required

**Decision**: Not implemented because it doesn't reduce the permission scope, only adds complexity.

### Alternative 2: Manual PR Creation

**Approach**: Have AI agent post code changes as comments, require human to create PR.

**Pros**:
- No write permissions needed

**Cons**:
- Defeats the purpose of automation
- Poor user experience
- Human still needs to review PR before merge anyway

**Decision**: Not implemented because it removes the value of automation while providing minimal security benefit (PR review still required).

### Alternative 3: Restricted File Patterns

**Approach**: Only allow modifications to specific file patterns (e.g., `src/**`, `docs/**`).

**Pros**:
- Slightly reduces attack surface

**Cons**:
- GitHub API doesn't support path-based permission restrictions
- Would require custom middleware to enforce
- Protected paths restriction (in prompt) provides similar benefit

**Decision**: Not implemented at GitHub API level (not supported), but implemented via prompt instructions.

## Security Incident Response

If suspicious activity is detected:

1. **Immediate Response**:
   - Close the issue/PR to stop the workflow
   - Revoke the GitHub App token (if using App authentication)
   - Review the Git history and workflow logs

2. **Investigation**:
   - Check what files were modified
   - Review the workflow logs for unusual API calls
   - Examine the prompt that triggered the behavior

3. **Remediation**:
   - Revert any malicious commits
   - Update the tool whitelist or prompt if needed
   - Force-push to remove malicious commits (if necessary)
   - Report to GitHub Security if MCP server vulnerability found

4. **Prevention**:
   - Update security controls in workflow configuration
   - Enhance prompt instructions to prevent similar issues
   - Consider additional tool restrictions

## Compliance & Audit

For compliance auditing:

1. **Permission Justification**: See "Why `contents: write` is Required" section
2. **Control Documentation**: See "Security Safeguards" section
3. **Audit Logs**: Available in GitHub audit log (Settings → Security → Audit log)
4. **Change History**: All changes tracked in Git history
5. **Review Records**: PR review history shows human approval

## Monitoring Recommendations

To monitor for misuse:

1. **Review Workflow Runs**: Check [Actions tab] for unusual patterns
2. **Monitor PR Activity**: Watch for unexpected feature branches or PRs
3. **Check Audit Log**: Review GitHub audit log for permission usage
4. **Enable Alerts**: Set up GitHub notifications for:
   - New workflow runs
   - New pull requests from `copilot/*` branches
   - Changes to `.github/workflows/`

## Questions & Answers

**Q: Why not use `contents: read` and require human to commit changes?**  
A: That defeats the automation purpose. PR review before merge provides the same security benefit with better UX.

**Q: Can the AI agent modify workflow files?**  
A: No. The prompt explicitly forbids it, and branch protection requires human PR review for such changes anyway.

**Q: What if the AI agent ignores the prompt restrictions?**  
A: 1) Changes still require PR review before merge, 2) Tool whitelist prevents many dangerous operations, 3) Timeout limits damage, 4) Audit trail allows rollback.

**Q: Can we use more granular permissions?**  
A: No. GitHub's REST API only offers `contents: read` or `contents: write`. There's no intermediate level.

**Q: Why trust the MCP server with write access?**  
A: 1) It's developed and maintained by GitHub, 2) Tool whitelist limits what it can do, 3) All operations are auditable, 4) PR review required before merge.

## References

- [GitHub REST API Permissions](https://docs.github.com/en/rest/overview/permissions-required-for-github-apps)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)

## Changelog

- **2025-10-31**: Initial security model documentation
- **2025-10-31**: Added protected paths restriction and enhanced safeguards

---

**Last Updated**: 2025-10-31  
**Owner**: @theinterneti  
**Review Required**: On any changes to permission model
