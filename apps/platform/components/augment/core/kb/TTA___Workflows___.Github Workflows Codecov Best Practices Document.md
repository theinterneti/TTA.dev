---
title: Codecov Best Practices - Based on Official Documentation
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .github/workflows/CODECOV_BEST_PRACTICES.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Codecov Best Practices - Based on Official Documentation]]

**Date**: 2025-10-29
**Status**: ✅ IMPLEMENTATION VERIFIED AGAINST OFFICIAL DOCS

## Summary

After reviewing the official Codecov documentation, our implementation follows best practices. This document highlights key recommendations and optional enhancements.

## ✅ What We're Doing Right

### 1. Using codecov-action v4/v5 ✅
**Official Recommendation**: Use `codecov/codecov-action@v5` for latest features

**Our Implementation**:
- `coverage.yml`: Uses v5 ✅
- Other workflows: Use v4 ✅ (still supported)

**Recommendation**: Consider upgrading all workflows to v5 for consistency

### 2. Token Authentication ✅
**Official Requirement**: Private repos MUST use `CODECOV_TOKEN`

**Our Implementation**:
```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}  # ✅ Now included in all workflows
```

**Status**: ✅ FIXED - All workflows now include token

### 3. Coverage Report Generation ✅
**Official Recommendation**: Use `pytest --cov --cov-branch --cov-report=xml`

**Our Implementation**:
```bash
pytest --cov=src --cov-branch --cov-report=xml
```

**Status**: ✅ CORRECT - Matches official documentation

### 4. Flags for Coverage Segmentation ✅
**Official Recommendation**: Use flags to isolate coverage by component

**Our Implementation**:
```yaml
flags: unit
flags: integration
flags: tta-ai-framework
flags: tta-narrative-engine
```

**Status**: ✅ EXCELLENT - We have 12 distinct flags for granular tracking

### 5. Fail Gracefully ✅
**Official Recommendation**: Use `fail_ci_if_error: false` to prevent blocking

**Our Implementation**:
```yaml
fail_ci_if_error: false  # ✅ Prevents CI failures on Codecov issues
```

**Status**: ✅ CORRECT - All workflows now include this

## 📋 Optional Enhancements

### 1. Create codecov.yml Configuration File

**Purpose**: Centralize Codecov configuration for all workflows

**Recommended Location**: `codecov.yml` (repository root)

**Example Configuration**:
```yaml
# codecov.yml
codecov:
  require_ci_to_pass: yes  # Wait for CI to pass before processing
  notify:
    wait_for_ci: true  # Wait for all CI checks

coverage:
  precision: 2  # Coverage precision (e.g., 85.23%)
  round: down  # Round down coverage percentages
  range: "70...100"  # Green at 100%, red at 70%

  status:
    project:
      default:
        target: auto  # Compare to base commit
        threshold: 1%  # Allow 1% drop
        informational: false  # Block if coverage drops
    patch:
      default:
        target: 80%  # Require 80% coverage on new code
        threshold: 0%  # No tolerance for drops

comment:
  layout: "diff, flags, files"
  behavior: default
  require_changes: false
  require_base: false
  require_head: true
  hide_project_coverage: false

ignore:
  - "tests/**/*"  # Ignore test files
  - "**/__pycache__/**"
  - "**/venv/**"
  - "**/.venv/**"
  - "**/migrations/**"
  - "scripts/**/*"

flags:
  unit:
    paths:
      - src/
  integration:
    paths:
      - src/
  tta-ai-framework:
    paths:
      - packages/tta-ai-framework/src/
  tta-narrative-engine:
    paths:
      - packages/tta-narrative-engine/src/
```

**Benefits**:
- Centralized configuration
- Status checks on PRs
- Customized PR comments
- Path-based flag definitions
- Ignore patterns for test files

### 2. Add Status Checks to Block PRs

**Purpose**: Prevent merging PRs that decrease coverage

**Configuration** (in `codecov.yml`):
```yaml
coverage:
  status:
    project:
      default:
        target: auto  # Must maintain or improve coverage
        threshold: 1%  # Allow 1% tolerance
        informational: false  # Block PR if fails
    patch:
      default:
        target: 80%  # New code must be 80% covered
        informational: false  # Block PR if fails
```

**Result**: GitHub will show status checks like:
- ✅ codecov/project — Coverage maintained
- ✅ codecov/patch — New code is 80% covered

### 3. Customize PR Comments

**Purpose**: Show only relevant coverage information

**Configuration** (in `codecov.yml`):
```yaml
comment:
  layout: "diff, flags, files"  # Show diff, flags, and file list
  behavior: default
  require_changes: true  # Only comment if coverage changes
```

**Result**: Cleaner PR comments with focused information

### 4. Add Coverage Badges

**Purpose**: Display coverage status in README

**Badge URL**:
```markdown
[![codecov](https://codecov.io/gh/theinterneti/TTA/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/theinterneti/TTA)
```

**Example**:
```markdown
# TTA (Therapeutic Text Adventure)

[![codecov](https://codecov.io/gh/theinterneti/TTA/branch/main/graph/badge.svg)](https://codecov.io/gh/theinterneti/TTA)
[![Tests](https://github.com/theinterneti/TTA/workflows/Tests/badge.svg)](https://github.com/theinterneti/TTA/actions)

AI-powered therapeutic text adventure platform...
```

### 5. Use Carryforward Flags (Advanced)

**Purpose**: Reuse coverage from previous commits when tests don't run

**Use Case**: Skip expensive integration tests on docs-only changes

**Configuration** (in `codecov.yml`):
```yaml
flags:
  integration:
    carryforward: true  # Reuse previous coverage if not uploaded
```

**Workflow Example**:
```yaml
- name: Check if integration tests needed
  id: check
  run: |
    if git diff --name-only HEAD^ | grep -q "^src/"; then
      echo "run_tests=true" >> $GITHUB_OUTPUT
    else
      echo "run_tests=false" >> $GITHUB_OUTPUT
    fi

- name: Run integration tests
  if: steps.check.outputs.run_tests == 'true'
  run: pytest tests/integration/ --cov=src --cov-branch --cov-report=xml
```

## 🔍 Verification Steps

### 1. Validate codecov.yml (If Created)

**Command**:
```bash
curl -X POST --data-binary @codecov.yml https://codecov.io/validate
```

**Expected Output**:
```
Valid!
```

### 2. Check Codecov Dashboard

**URL**: https://codecov.io/gh/theinterneti/TTA

**Verify**:
- ✅ Latest commits show coverage data
- ✅ All flags are visible (unit, integration, etc.)
- ✅ Coverage graphs display correctly
- ✅ File browser shows line-by-line coverage

### 3. Check PR Comments

**On New PRs**:
- ✅ Codecov bot comments with coverage diff
- ✅ Coverage changes are highlighted
- ✅ Links to detailed reports work

### 4. Check Status Checks (If Configured)

**On PRs**:
- ✅ `codecov/project` status appears
- ✅ `codecov/patch` status appears
- ✅ Status checks block merge if coverage drops

## 📊 Current Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Token authentication | ✅ IMPLEMENTED | All workflows use token |
| Coverage generation | ✅ IMPLEMENTED | All workflows use `--cov-branch` |
| Codecov uploads | ✅ IMPLEMENTED | All test workflows upload |
| Flags | ✅ IMPLEMENTED | 12 distinct flags |
| Fail gracefully | ✅ IMPLEMENTED | All uploads use `fail_ci_if_error: false` |
| codecov.yml | ⚠️ OPTIONAL | Not required but recommended |
| Status checks | ⚠️ OPTIONAL | Requires codecov.yml |
| Coverage badges | ⚠️ OPTIONAL | Can add to README |
| Carryforward flags | ⚠️ OPTIONAL | Advanced feature |

## 🎯 Recommended Next Steps

### Immediate (Optional)
1. Create `codecov.yml` for centralized configuration
2. Add coverage badges to README.md
3. Configure status checks to block low-coverage PRs

### Future (Advanced)
1. Implement carryforward flags for expensive tests
2. Set up coverage notifications (Slack, email)
3. Configure component-based coverage tracking

## 📚 Official Documentation References

- **GitHub Tutorial**: https://docs.codecov.com/docs/github-tutorial
- **Python Coverage**: https://docs.codecov.com/docs/code-coverage-with-python
- **Common Configurations**: https://docs.codecov.com/docs/common-recipe-list
- **codecov.yml Reference**: https://docs.codecov.com/docs/codecov-yaml
- **Flags Documentation**: https://docs.codecov.com/docs/flags
- **Status Checks**: https://docs.codecov.com/docs/commit-status

## 🔧 Example codecov.yml (Complete)

Here's a complete `codecov.yml` tailored for TTA:

```yaml
# codecov.yml - Codecov configuration for TTA
codecov:
  require_ci_to_pass: yes
  notify:
    wait_for_ci: true

coverage:
  precision: 2
  round: down
  range: "70...100"

  status:
    project:
      default:
        target: auto
        threshold: 1%
        informational: false
    patch:
      default:
        target: 80%
        threshold: 0%
        informational: false

comment:
  layout: "diff, flags, files"
  behavior: default
  require_changes: false
  require_base: false
  require_head: true
  hide_project_coverage: false

ignore:
  - "tests/**/*"
  - "**/__pycache__/**"
  - "**/venv/**"
  - "**/.venv/**"
  - "**/migrations/**"
  - "scripts/**/*"
  - "**/*.md"

flags:
  unit:
    paths:
      - src/
  integration:
    paths:
      - src/
  tta-ai-framework:
    paths:
      - packages/tta-ai-framework/src/
  tta-narrative-engine:
    paths:
      - packages/tta-narrative-engine/src/
  tta-app:
    paths:
      - src/
```

---

**Status**: ✅ IMPLEMENTATION VERIFIED
**Compliance**: Follows official Codecov best practices
**Optional Enhancements**: Available for future implementation


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.github workflows codecov best practices document]]
