# GitHub Actions Workflow Migration Plan

## Overview
This document tracks the consolidation of 30+ GitHub Actions workflows into 4 core workflows for improved performance, maintainability, and reliability.

## New Consolidated Workflows

### 1. `consolidated-pr-validation.yml` - Fast PR Feedback (~5 min)
**Purpose:** Quick validation for pull requests
**Triggers:** PR opened, synchronized, reopened
**Jobs:**
- Quality checks (format, lint, types)
- Unit tests (Python 3.12, Ubuntu only)
- PR summary

**Replaces:**
- `pr-validation.yml`
- `pr-validation-v2.yml`
- `quality-check.yml` (for PRs)

### 2. `consolidated-merge-gate.yml` - Comprehensive Validation (~15-20 min)
**Purpose:** Complete validation before merge to main
**Triggers:** Push to main/develop
**Jobs:**
- Quality validation
- Comprehensive tests (Python 3.11, 3.12)
- Integration tests (main branch only)
- Documentation validation
- Package validation
- Security scans

**Replaces:**
- `merge-validation.yml`
- `merge-validation-v2.yml`
- `ci.yml` (for main branch)
- `tests-split.yml` (partially)

### 3. `consolidated-platform-compatibility.yml` - Matrix Testing (~20-30 min)
**Purpose:** Cross-platform compatibility validation
**Triggers:** Nightly schedule, workflow_dispatch, push to main (core packages)
**Jobs:**
- Matrix builds (Ubuntu, macOS, Windows × Python 3.11, 3.12)
- Platform compatibility summary

**Replaces:**
- `ci.yml` (matrix builds)

### 4. `consolidated-ai-review.yml` - AI Code Review (~5-10 min)
**Purpose:** Automated code review with fallback
**Triggers:** PR opened, synchronized, reopened
**Jobs:**
- Check Gemini availability
- Gemini review (with retry and timeout)
- Fallback static analysis
- Review summary

**Replaces:**
- `gemini-review.yml`
- `gemini-dispatch.yml`
- `gemini-triage.yml`
- `orchestration-pr-review.yml`

## Workflows to Keep (Reusable/Utility)

These workflows remain as they are either reusable or serve specific utility purposes:

### Reusable Workflows
- `reusable-run-tests.yml` - Generic test runner
- `reusable-quality-checks.yml` - Generic quality checker
- `reusable-build-package.yml` - Package builder

### Utility/Testing Workflows
- `test-gemini-api-key.yml` - Manual Gemini API testing
- `test-gemini-cli-no-mcp.yml` - Gemini CLI testing
- `test-gemini-keys.yml` - API key validation
- `test-mcp-versions.yml` - MCP server version testing
- `test-quality-checks.yml` - Workflow testing
- `list-gemini-models.yml` - List available models

### Validation Workflows
- `kb-validation.yml` - Knowledge base validation
- `mcp-validation.yml` - MCP validation
- `secrets-validation.yml` - Secrets validation
- `validate-todos.yml` - TODO compliance

### Monitoring Workflows
- `pr-health-monitoring.yml` - PR health tracking

### Setup Workflows
- `auto-assign-copilot.yml` - Auto-assign reviewer
- `copilot-setup-steps.yml` - Copilot setup

## Workflows to Deprecate/Archive

These workflows are redundant and will be moved to archive:

### Deprecated (Replaced by Consolidated Workflows)
- `pr-validation.yml` → `consolidated-pr-validation.yml`
- `pr-validation-v2.yml` → `consolidated-pr-validation.yml`
- `merge-validation.yml` → `consolidated-merge-gate.yml`
- `merge-validation-v2.yml` → `consolidated-merge-gate.yml`
- `quality-check.yml` → `consolidated-pr-validation.yml` + `consolidated-merge-gate.yml`
- `ci.yml` → `consolidated-pr-validation.yml` + `consolidated-platform-compatibility.yml`
- `gemini-invoke.yml` → `consolidated-ai-review.yml`
- `gemini-invoke-advanced.yml` → `consolidated-ai-review.yml`
- `gemini-test-minimal.yml` → `test-gemini-api-key.yml` (consolidated with testing workflows)

## Migration Timeline

### Phase 1: Create Consolidated Workflows (Current)
- [x] Create `consolidated-pr-validation.yml`
- [x] Create `consolidated-merge-gate.yml`
- [x] Create `consolidated-platform-compatibility.yml`
- [x] Create `consolidated-ai-review.yml`
- [ ] Test consolidated workflows in parallel with existing ones

### Phase 2: Gradual Migration (Week 1)
- [ ] Add deprecation notices to old workflows
- [ ] Monitor consolidated workflows for issues
- [ ] Adjust timeouts and caching based on performance

### Phase 3: Cleanup (Week 2)
- [ ] Disable deprecated workflows (rename to .yml.disabled)
- [ ] Archive deprecated workflows to `.github/workflows/archive/`
- [ ] Update documentation references
- [ ] Clean up unused secrets and variables

### Phase 4: Optimization (Week 3)
- [ ] Fine-tune caching strategies
- [ ] Optimize job dependencies and parallelization
- [ ] Implement selective test execution based on changed files
- [ ] Add performance metrics tracking

## Performance Improvements

### Before Consolidation
- **PR Validation:** 15-20 minutes (full matrix + multiple redundant workflows)
- **Merge Validation:** 20-30 minutes (redundant checks)
- **Total Workflows:** 30+ files
- **GitHub Actions Minutes:** ~50 minutes per PR

### After Consolidation
- **PR Validation:** ~5 minutes (Ubuntu + Python 3.12 only)
- **Merge Validation:** ~15-20 minutes (comprehensive but optimized)
- **Platform Testing:** Nightly only (not blocking PRs)
- **Total Core Workflows:** 4 files
- **GitHub Actions Minutes:** ~10-15 minutes per PR
- **Estimated Savings:** 70% reduction in PR validation time

## Reliability Improvements

1. **Circuit Breaker Pattern:** AI review falls back to static analysis
2. **Retry Mechanisms:** Gemini review has built-in retry with timeout
3. **Graceful Degradation:** Missing services don't block PRs
4. **Better Error Handling:** Continue-on-error for non-critical steps
5. **Comprehensive Summaries:** Clear status indicators in job summaries

## Security Improvements

1. **Minimal Permissions:** Each workflow has least-privilege permissions
2. **Token Scoping:** Separate tokens for different purposes
3. **Secret Validation:** Dedicated workflows for secret checking
4. **Audit Trail:** Comprehensive logging and summaries

## Rollback Plan

If issues arise with consolidated workflows:

1. **Immediate:** Re-enable specific old workflow by renaming `.yml.disabled` → `.yml`
2. **Short-term:** Keep old workflows disabled but available for 2 weeks
3. **Long-term:** Archive old workflows after successful migration

## Success Metrics

Track these metrics to validate the consolidation:

- [ ] PR validation time < 10 minutes (target: 5 minutes)
- [ ] Merge validation time < 25 minutes (target: 15-20 minutes)
- [ ] Workflow success rate > 95% (target: 99%)
- [ ] GitHub Actions minutes reduction > 60% (target: 70%)
- [ ] Maintenance files reduced from 30 → 10 (target: 4 core + 6 utilities)

## Next Steps

1. Test consolidated workflows in parallel
2. Monitor for edge cases and failures
3. Collect feedback from team
4. Iterate on improvements
5. Execute deprecation plan
