# GitHub Workflows Organization Guide

## Overview

This document describes the organization of GitHub workflows in the TTA.dev repository.

## Directory Structure

```
.github/workflows/
├── experimental/          # Experimental agent integration workflows
│   ├── README.md         # Experimental workflows documentation
│   └── gemini/           # Gemini AI workflows (testing)
├── production/           # (Future) Production-ready workflows
└── *.yml                 # Active workflows in main/refactor branches
```

## Active Workflows (Main Branch)

These workflows run on the main repository branches:

### CI/CD Workflows
- **ci.yml** - Main continuous integration pipeline
- **quality-check.yml** - Code quality checks (ruff, pyright)
- **tests-split.yml** - Split test execution for parallelization

### Validation Workflows
- **kb-validation.yml** - Knowledge base validation
- **mcp-validation.yml** - MCP server validation
- **secrets-validation.yml** - Secrets validation
- **validate-todos.yml** - TODO management validation

### PR Management
- **pr-validation-v2.yml** - Pull request validation (v2)
- **pr-validation.yml** - Pull request validation (v1)
- **pr-health-monitoring.yml** - PR health monitoring
- **merge-validation-v2.yml** - Merge validation (v2)
- **merge-validation.yml** - Merge validation (v1)
- **orchestration-pr-review.yml** - Orchestrated PR review

### Copilot Automation
- **auto-assign-copilot.yml** - Auto-assign GitHub Copilot to issues
- **copilot-setup-steps.yml** - Copilot setup automation

### Reusable Workflows
- **reusable-build-package.yml** - Reusable package build
- **reusable-quality-checks.yml** - Reusable quality checks
- **reusable-run-tests.yml** - Reusable test runner

### Utility Workflows
- **test-quality-checks.yml** - Test quality check workflows
- **test-mcp-versions.yml** - Test MCP version compatibility
- **auto-lazy-dev-setup.yml** - Lazy dev environment setup

## Experimental Workflows

**Branch:** `experimental/workflow-agent-integrations`

Workflows for testing AI agent integrations (Gemini, Copilot, Cline, etc.)

### Gemini Workflows (Experimental)

All Gemini-related workflows have been moved to `experimental/gemini/`:

1. **gemini-dispatch.yml** - Dispatch workflow for Gemini actions
2. **gemini-invoke-advanced.yml** - Advanced Gemini invocation with MCP
3. **gemini-invoke.yml** - Basic Gemini invocation
4. **gemini-review.yml** - Gemini code review automation
5. **gemini-test-minimal.yml** - Minimal Gemini test
6. **gemini-triage.yml** - Issue triage with Gemini
7. **list-gemini-models.yml** - List available Gemini models
8. **test-gemini-api-key.yml** - Validate Gemini API key
9. **test-gemini-cli-no-mcp.yml** - Test Gemini CLI without MCP
10. **test-gemini-keys.yml** - Test multiple Gemini API keys

**Status:** These workflows are experimental and should NOT be merged to main until:
- ✅ Thoroughly tested and validated
- ✅ Documented with clear usage guidelines
- ✅ Approved by repository maintainers
- ✅ Necessary secrets configured in production
- ✅ Rate limits and costs understood

See `experimental/README.md` for full details.

## Branch Policy

### Main/Refactor Branches
- Only production-ready workflows
- Must pass all quality checks
- Require maintainer approval

### Experimental Branch
- Test new agent integrations
- Validate workflow behaviors
- Document findings before promotion

## Adding New Workflows

### For Production Use
1. Create in `.github/workflows/`
2. Add comprehensive documentation
3. Test in experimental branch first
4. Submit PR with approval requirements

### For Experimental Testing
1. Create in `.github/workflows/experimental/`
2. Commit to `experimental/workflow-agent-integrations` branch
3. Document purpose and status
4. Test and iterate
5. Promote to production when stable

## Workflow Dependencies

### Secrets Required
- `GEMINI_API_KEY` - For Gemini workflows (experimental)
- Standard GitHub tokens for Copilot workflows
- Additional secrets documented in workflow files

### Actions Used
- `google-github-actions/run-gemini-cli@main` - Gemini CLI
- Standard GitHub Actions
- Custom actions in `.github/actions/`

## Troubleshooting

### Token Scope Issues
If pushing workflow files fails:
1. Verify GitHub token has `workflow` scope
2. Update token in git credentials
3. Or add workflows via GitHub Web UI

### Workflow Not Running
1. Check branch protection rules
2. Verify trigger conditions in workflow file
3. Check workflow permissions in repository settings

---

**Last Updated:** 2025-11-17
**Maintained by:** TTA.dev Team
**Status:** Active - Production and Experimental Workflows Separated
