---
title: Codecov Integration - Changes Summary
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .github/workflows/CODECOV_CHANGES_SUMMARY.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Codecov Integration - Changes Summary]]

## Quick Reference

This document summarizes the changes made to fix Codecov integration in GitHub Actions workflows.

## Changes Made

### 1. monorepo-ci.yml
**Lines Modified**: 119, 184, 278

**Changes**:
- Added `--cov-branch` flag to all three test jobs:
  - `test-tta-ai-framework` (line 119)
  - `test-tta-narrative-engine` (line 184)
  - `test-tta-app` (line 278)

**Before**:
```yaml
--cov=packages/tta-ai-framework/src/tta_ai \
--cov-report=xml \
```

**After**:
```yaml
--cov=packages/tta-ai-framework/src/tta_ai \
--cov-branch \
--cov-report=xml \
```

### 2. tests.yml
**Lines Modified**: 47, 112

**Changes**:
- Added `--cov-branch` flag to both test jobs:
  - `unit` job (line 47)
  - `integration` job (line 112)

**Before**:
```yaml
--cov=src --cov-report=xml:coverage-unit.xml
```

**After**:
```yaml
--cov=src --cov-branch --cov-report=xml:coverage-unit.xml
```

### 3. keploy-tests.yml
**Lines Modified**: 109

**Changes**:
- Added `--cov-branch` flag to `unit-tests` job (line 109)

**Before**:
```yaml
uv run pytest tests/unit/ -v --cov=src --cov-report=xml
```

**After**:
```yaml
uv run pytest tests/unit/ -v --cov=src --cov-branch --cov-report=xml
```

### 4. comprehensive-test-battery.yml
**Lines Modified**: 87-93, 104-108, 260-267, 289-293, 414-421, 447-451

**Changes**:
- Added pytest coverage commands to three jobs:
  - `pr-validation` job
  - `comprehensive-testing` job (matrix)
  - `manual-testing` job

**Added to each job**:
```yaml
# Run pytest with coverage first
uv run pytest tests/comprehensive_battery/ \
  --cov=src \
  --cov-branch \
  --cov-report=xml \
  --cov-report=term \
  -v

# ... existing test commands ...

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    flags: comprehensive-[job-name]
    name: comprehensive-[job-name]
```

### 5. coverage.yml
**No Changes Required**

This workflow already had:
- ✅ `--cov-branch` flag (line 98)
- ✅ Proper Codecov upload with token (lines 108-116)

## Verification Checklist

Use this checklist to verify Codecov integration is working:

- [ ] All test workflows run successfully
- [ ] Coverage reports are generated (`coverage.xml` files)
- [ ] Codecov receives uploads (check Codecov dashboard)
- [ ] Branch coverage is tracked (check Codecov reports)
- [ ] Coverage badges update correctly
- [ ] PR comments show coverage changes

## Testing the Changes

### Local Testing

Test coverage generation locally:

```bash
# Test monorepo packages
uv run pytest packages/tta-ai-framework/tests/ \
  --cov=packages/tta-ai-framework/src/tta_ai \
  --cov-branch \
  --cov-report=xml \
  --cov-report=term

# Test main application
uv run pytest tests/unit/ \
  --cov=src \
  --cov-branch \
  --cov-report=xml \
  --cov-report=term

# Test comprehensive battery
uv run pytest tests/comprehensive_battery/ \
  --cov=src \
  --cov-branch \
  --cov-report=xml \
  --cov-report=term
```

### CI/CD Testing

1. Create a test PR
2. Verify all workflows run successfully
3. Check workflow logs for coverage output
4. Verify Codecov receives uploads
5. Check PR for Codecov comment

## Codecov Configuration

### Required Secrets

Ensure these secrets are configured in GitHub repository settings:

- `CODECOV_TOKEN` - Required for authenticated uploads (used in `coverage.yml`)

### Codecov Flags

The following flags are used to segment coverage:

| Flag | Workflow | Purpose |
|------|----------|---------|
| `tta-ai-framework` | monorepo-ci.yml | AI framework package |
| `tta-narrative-engine` | monorepo-ci.yml | Narrative engine package |
| `tta-app` | monorepo-ci.yml | Main application |
| `unit,integration` | coverage.yml | Combined coverage |
| `comprehensive-pr-validation` | comprehensive-test-battery.yml | PR validation |
| `comprehensive-Core Tests` | comprehensive-test-battery.yml | Core test suite |
| `comprehensive-Performance Tests` | comprehensive-test-battery.yml | Performance suite |
| `comprehensive-Integration Tests` | comprehensive-test-battery.yml | Integration suite |
| `comprehensive-manual` | comprehensive-test-battery.yml | Manual runs |

## Troubleshooting

### Coverage Not Uploading

1. Check workflow logs for Codecov upload step
2. Verify `coverage.xml` file is generated
3. Check Codecov token is configured (for `coverage.yml`)
4. Verify network connectivity to Codecov

### Branch Coverage Not Showing

1. Verify `--cov-branch` flag is present in pytest command
2. Check `coverage.xml` contains branch coverage data
3. Verify Codecov is configured to show branch coverage

### Coverage Percentage Incorrect

1. Verify `--cov=` path matches source code location
2. Check for excluded files in `.coveragerc` or `pyproject.toml`
3. Verify all test files are being executed

## Related Documentation

- [Codecov Documentation](https://docs.codecov.com/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [[TTA/Workflows/CODECOV_AUDIT_REPORT|Full Audit Report]]

## Rollback Instructions

If issues arise, revert changes with:

```bash
git revert <commit-hash>
```

Or manually remove `--cov-branch` flags from the modified workflows.

---

**Last Updated**: 2025-10-29
**Status**: ✅ Complete
**Workflows Modified**: 4
**Test Jobs Updated**: 10


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.github workflows codecov changes summary document]]
