# Workflow Rebuild - Phase 3.1: Parallel Execution

**Status**: Implementation In Progress  
**Date**: 2025-11-20  
**Phase**: 3.1 - Parallel Execution Infrastructure

---

## Overview

Phase 3.1 establishes the infrastructure for running v1 and v2 workflows in parallel to validate v2 performance and results before migration.

## Deliverables

### ✅ Monitoring Infrastructure

#### `scripts/workflow/workflow-monitor.py`
**Purpose**: Automated comparison of v1 and v2 workflow performance

**Features**:
- Fetches workflow runs via GitHub API
- Compares execution times and success rates
- Detects unique v2 failures (failures not present in v1)
- Generates markdown reports
- Alerts on anomalies (>10% performance degradation)

**Usage**:
```bash
export GITHUB_TOKEN="your_token_here"
python scripts/workflow/workflow-monitor.py --days 1 --output report.md
```

**Dependencies**:
- PyGithub library
- GitHub token with `repo` and `actions:read` scopes

---

#### `.github/workflows/workflow-comparison.yml`
**Purpose**: Daily automated workflow comparison

**Triggers**:
- **Schedule**: Daily at 00:00 UTC
- **Manual**: `workflow_dispatch` for on-demand reports

**Jobs**:
1. **Compare Workflows**: Run monitoring script
2. **Upload Report**: Save as workflow artifact
3. **Post Summary**: Add to GitHub Actions summary
4. **Create Issue**: If alerts detected, create tracking issue with P1 label

**Permissions**:
- `contents: read` - Checkout code
- `actions: read` - Fetch workflow runs
- `issues: write` - Create alert issues

---

### ✅ V2 Workflow Updates

**Modified Files**:
- `.github/workflows/pr-validation-v2.yml`
  - Updated name: "PR Validation v2 (Parallel Execution)"
  - Concurrency group: `pr-v2-${{ github.event.pull_request.number }}`
  
- `.github/workflows/merge-validation-v2.yml`
  - Updated name: "Merge Validation v2 (Parallel Execution)"

**Rationale**: Clear labeling helps distinguish v1 vs v2 in GitHub UI during parallel execution period

---

## Validation

### Workflow Syntax
```bash
# Validate all workflow files
actionlint .github/workflows/workflow-comparison.yml
actionlint .github/workflows/pr-validation-v2.yml
actionlint .github/workflows/merge-validation-v2.yml
```

### Monitoring Script
```bash
# Test monitoring script (requires GITHUB_TOKEN)
python scripts/workflow/workflow-monitor.py --days 1
```

### Expected Behavior
- Both v1 and v2 workflows trigger on new PRs
- Comparison workflow runs daily at 00:00 UTC
- Reports show performance metrics and success rates
- Issues created automatically if anomalies detected

---

## Next Steps

### Immediate
- [ ] Merge Phase 3.1 implementation3.1 to main
- [ ] Verify monitoring workflow runs successfully
- [ ] Begin 7-day parallel execution period

### Week 1 (Days 1-7)
- [ ] Monitor daily comparison reports
- [ ] Review any alert issues
- [ ] Collect team feedback
- [ ] Document any differences

### Decision Point (End of Week 1)
- If stable: Proceed to Phase 3.2 (V2-only execution)
- If issues: Extend parallel execution or rollback

---

## Monitoring Metrics

### Success Criteria
- ✅ Both v1 and v2 workflows complete successfully
- ✅ Performance variance <10%
- ✅ Zero unique v2 failures
- ✅ Success rates match (both v1 and v2)

### Alert Triggers
- 🚨 Unique v2 failures (PRs that fail in v2 but pass in v1)
- ⚠️  Performance degradation >10%
- ⚠️  Success rate mismatch

---

## Rollback

If issues during Phase 3.1:
- **No rollback needed** - v1 workflows continue running
- Investigate v2 issues
- Fix v2 workflows
- Continue parallel execution

---

## References

- [Implementation Plan](file:///home/thein/.gemini/antigravity/brain/e4e7aabd-c6f4-4292-a6c3-19fd96becc25/implementation_plan.md)
- [Issue #79](https://github.com/theinterneti/TTA.dev/issues/79)
- [Phase 2 Complete](file:///home/thein/repos/TTA.dev/docs/status-reports/ci-cd/WORKFLOW_REBUILD_PHASE2_COMPLETE.md)

---

**Last Updated**: 2025-11-20  
**Status**: Ready for deployment
