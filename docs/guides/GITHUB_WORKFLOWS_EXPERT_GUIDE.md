# GitHub Workflows Expert Guide

**Your comprehensive guide to managing TTA.dev GitHub Actions workflows**

## Quick Summary

✅ **COMPLETED:**
- Created `experimental/workflow-agent-integrations` branch
- Moved all 10 Gemini workflows to `.github/workflows/experimental/gemini/`
- Organized workflow documentation
- Separated experimental from production workflows

## Branch Organization

### experimental/workflow-agent-integrations
**Purpose:** Test AI agent integrations (@gemini, @copilot, @cline, etc.)

**Location:** `.github/workflows/experimental/`

**Gemini Workflows Moved:**
1. `gemini-dispatch.yml`
2. `gemini-invoke-advanced.yml`
3. `gemini-invoke.yml`
4. `gemini-review.yml`
5. `gemini-test-minimal.yml`
6. `gemini-triage.yml`
7. `list-gemini-models.yml`
8. `test-gemini-api-key.yml`
9. `test-gemini-cli-no-mcp.yml`
10. `test-gemini-keys.yml`

### main / refactor/repo-reorg
**Purpose:** Production workflows only

**Active Workflows:**
- CI/CD: `ci.yml`, `quality-check.yml`, `tests-split.yml`
- Validation: `kb-validation.yml`, `mcp-validation.yml`, `secrets-validation.yml`
- PR Management: `pr-validation-v2.yml`, `pr-health-monitoring.yml`
- Copilot: `auto-assign-copilot.yml`, `copilot-setup-steps.yml`
- Reusable: `reusable-build-package.yml`, `reusable-quality-checks.yml`

## Workflow Categories Explained

### 1. CI/CD Workflows
**Purpose:** Continuous integration and delivery automation

- `ci.yml` - Main pipeline (build, test, deploy)
- `quality-check.yml` - Ruff formatting, Pyright type checking
- `tests-split.yml` - Parallel test execution for speed

**When to use:** Automatically triggered on push/PR

### 2. Validation Workflows
**Purpose:** Validate repository integrity and standards

- `kb-validation.yml` - Check LogSeq knowledge base links
- `mcp-validation.yml` - Validate MCP server configurations
- `secrets-validation.yml` - Ensure required secrets exist
- `validate-todos.yml` - Validate TODO format and properties

**When to use:** Pre-merge checks, scheduled maintenance

### 3. PR Management Workflows
**Purpose:** Automate pull request review and validation

- `pr-validation-v2.yml` - Latest PR validation (replaces v1)
- `pr-health-monitoring.yml` - Monitor PR health metrics
- `merge-validation-v2.yml` - Pre-merge quality gates
- `orchestration-pr-review.yml` - Coordinate multi-step reviews

**When to use:** Automatically on PR open/update

### 4. Copilot Automation
**Purpose:** GitHub Copilot integration

- `auto-assign-copilot.yml` - Auto-assign Copilot to issues
- `copilot-setup-steps.yml` - Setup Copilot environment

**When to use:** Issue creation, development environment setup

### 5. Experimental Workflows (NEW!)
**Purpose:** Test AI agent integrations safely

- All Gemini workflows
- Future: Cline integration workflows
- Future: Custom agent workflows

**When to use:** Testing new agent features, debugging agent behavior

## Expert Tips

### Testing New Workflows

1. **Always start in experimental branch:**
   ```bash
   git checkout experimental/workflow-agent-integrations
   # Create new workflow in .github/workflows/experimental/
   git add .github/workflows/experimental/my-new-workflow.yml
   git commit -m "test: Add experimental workflow for X"
   git push origin experimental/workflow-agent-integrations
   ```

2. **Monitor workflow runs:**
   - Go to: https://github.com/theinterneti/TTA.dev/actions
   - Filter by branch: `experimental/workflow-agent-integrations`
   - Check logs for errors

3. **Iterate quickly:**
   - Make changes
   - Push to experimental branch
   - Observe results
   - Repeat until stable

### Promoting Workflows to Production

**Checklist before promotion:**
- [ ] Workflow tested successfully in experimental branch
- [ ] Documentation updated (inline comments, README)
- [ ] Secrets configured in repository settings
- [ ] Rate limits understood (especially for AI APIs)
- [ ] Cost implications reviewed
- [ ] Maintainer approval obtained
- [ ] Added to `.github/workflows/WORKFLOW_FILE_NOTE.md`

**Promotion process:**
```bash
# 1. Ensure you're on experimental branch
git checkout experimental/workflow-agent-integrations

# 2. Copy workflow to main workflows directory
cp .github/workflows/experimental/my-workflow.yml .github/workflows/

# 3. Create PR to main/refactor branch
git checkout refactor/repo-reorg
git checkout -b feature/promote-my-workflow
git add .github/workflows/my-workflow.yml
git commit -m "feat: Promote my-workflow from experimental"
git push origin feature/promote-my-workflow

# 4. Create PR and request review
```

### Workflow Debugging

**Common Issues:**

1. **Workflow not triggering:**
   - Check `on:` conditions match your branch/event
   - Verify branch protection rules
   - Check workflow permissions in repo settings

2. **Secret not found:**
   - Go to Settings → Secrets and variables → Actions
   - Add required secret (e.g., `GEMINI_API_KEY`)
   - Ensure secret name matches workflow exactly

3. **Token scope issues:**
   - If pushing workflows fails, token needs `workflow` scope
   - Update token or add workflow via GitHub Web UI

4. **Rate limiting:**
   - Check API rate limits for external services
   - Add delays between calls
   - Use caching where possible

### Best Practices

1. **Use reusable workflows** for common tasks:
   ```yaml
   jobs:
     quality:
       uses: ./.github/workflows/reusable-quality-checks.yml
   ```

2. **Add concurrency controls** to prevent duplicate runs:
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

3. **Set timeouts** to prevent hanging workflows:
   ```yaml
   jobs:
     test:
       timeout-minutes: 30
   ```

4. **Document everything:**
   - Add comments explaining complex logic
   - Update WORKFLOW_FILE_NOTE.md
   - Include usage examples

5. **Test locally when possible:**
   - Use `act` tool to test workflows locally
   - Validate YAML syntax before pushing

## AI Agent Integration Strategy

### Current State
- **Gemini:** 10 workflows in experimental branch
- **Copilot:** 2 production workflows
- **Cline:** Not yet integrated

### Recommended Approach

1. **Gemini Integration:**
   - Test all 10 workflows in experimental branch
   - Document successful patterns
   - Identify 1-2 most valuable workflows
   - Promote those to production
   - Archive or delete remaining experimental workflows

2. **Copilot Integration:**
   - Current workflows are stable
   - Consider enhancing with more automation
   - Add review comment workflows

3. **Cline Integration:**
   - Start with simple workflow in experimental branch
   - Test dispatch triggers
   - Document API interaction patterns
   - Promote when stable

### Future Plans

**Phase 1: Stabilize Gemini (Current)**
- Test all Gemini workflows
- Choose best 1-2 for production
- Document learnings

**Phase 2: Enhance Copilot**
- Add automated code review comments
- Integrate with PR health monitoring
- Auto-fix common issues

**Phase 3: Add Cline**
- Create experimental Cline workflows
- Test MCP integration in CI/CD
- Evaluate value vs complexity

**Phase 4: Multi-Agent Orchestration**
- Coordinate Gemini + Copilot + Cline
- Route tasks to best agent
- Centralized orchestration workflow

## Quick Commands

### Switch to experimental branch:
```bash
git checkout experimental/workflow-agent-integrations
```

### List all workflows:
```bash
ls -1 .github/workflows/
ls -1 .github/workflows/experimental/gemini/
```

### Check workflow status:
```bash
gh workflow list
gh run list --workflow=ci.yml
```

### View workflow logs:
```bash
gh run view <run-id> --log
```

### Trigger manual workflow:
```bash
gh workflow run <workflow-name>
```

## Resources

### Documentation
- **Main Guide:** `.github/workflows/WORKFLOW_FILE_NOTE.md`
- **Experimental Guide:** `.github/workflows/experimental/README.md`
- **GitHub Actions Docs:** https://docs.github.com/actions

### Related Files
- **Agent Instructions:** `AGENTS.md`
- **Copilot Setup:** `.github/COPILOT_SETUP_SUMMARY.md`
- **MCP Integration:** `MCP_SERVERS.md`

### Tools
- **GitHub CLI:** https://cli.github.com/
- **act (local testing):** https://github.com/nektos/act
- **YAML validator:** https://www.yamllint.com/

## Summary of Changes

**What we did:**
1. ✅ Created `experimental/workflow-agent-integrations` branch
2. ✅ Moved 10 Gemini workflows to `.github/workflows/experimental/gemini/`
3. ✅ Updated workflow documentation
4. ✅ Separated experimental from production workflows
5. ✅ Created comprehensive expert guide (this file)

**What's next:**
1. Test Gemini workflows in experimental branch
2. Document results and findings
3. Choose best workflows for production promotion
4. Archive or delete remaining experimental workflows
5. Plan Cline and enhanced Copilot integrations

**Your current branch:**
```bash
# You are now on: experimental/workflow-agent-integrations
# Gemini workflows are in: .github/workflows/experimental/gemini/
# Production workflows remain in: .github/workflows/
```

---

**Last Updated:** 2025-11-17
**Your Role:** GitHub Workflows Expert for TTA.dev
**Status:** Experimental branch created, Gemini workflows organized
