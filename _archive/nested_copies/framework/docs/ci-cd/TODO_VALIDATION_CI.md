# TODO Compliance CI/CD Validation

**Status**: ✅ Active
**Workflow**: `.github/workflows/validate-todos.yml`
**Created**: 2025-10-31
**Purpose**: Enforce 100% TODO compliance on all pull requests

---

## Overview

The TODO Compliance Validation workflow automatically validates that all TODOs in Logseq journals follow the [TODO Management System](../../logseq/pages/TODO%20Management%20System.md) standards.

**Key Features:**
- ✅ Runs on every PR to `main` branch
- ✅ Validates TODO format and required properties
- ✅ Blocks merge if compliance < 100%
- ✅ Posts validation results as PR comment
- ✅ Uploads validation results as artifact

---

## Workflow Triggers

The workflow runs when:

1. **Pull Request** to `main` branch with changes to:
   - `logseq/journals/**`
   - `logseq/pages/**`
   - `scripts/validate-todos.py`

2. **Push** to `main` branch with changes to:
   - `logseq/journals/**`
   - `logseq/pages/**`
   - `scripts/validate-todos.py`

---

## Validation Process

### 1. Setup Environment

```yaml
- Python 3.12
- uv package manager
- Project dependencies (uv sync --all-extras)
```

### 2. Run Validation

```bash
uv run python scripts/validate-todos.py --json
```

**Output format:**
```json
{
  "total_todos": 116,
  "compliant_todos": 116,
  "compliance_rate": 100.0,
  "issues_count": 0,
  "missing_kb_pages_count": 0
}
```

### 3. Check Compliance

- **Pass**: `compliance_rate == 100.0`
- **Fail**: `compliance_rate < 100.0`

### 4. Post PR Comment

The workflow automatically posts a comment on the PR with validation results:

**Example (Passing):**
```markdown
## ✅ TODO Compliance Validation - PASSED

**Compliance Rate:** 100.0%
**TODOs:** 116/116 compliant

✅ All TODOs are properly formatted with required tags and properties!
```

**Example (Failing):**
```markdown
## ❌ TODO Compliance Validation - FAILED

**Compliance Rate:** 85.5%
**TODOs:** 94/110 compliant
**Issues Found:** 16

❌ Some TODOs are missing required tags or properties.

Please run `uv run python scripts/validate-todos.py` locally to see detailed issues.

**Required for all TODOs:**
- Category tag: `#dev-todo` or `#user-todo`
- For `#dev-todo`: `type::`, `priority::`, `package::` properties
- For `#user-todo`: `type::`, `audience::`, `difficulty::` properties
```

---

## Required TODO Format

### For `#dev-todo` (Development Work)

```markdown
- TODO Implement feature #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/FeatureName]]
```

**Required properties:**
- `type::` - One of: architecture, implementation, documentation, testing, infrastructure, investigation, code-review, issue-tracking
- `priority::` - One of: critical, high, medium, low
- `package::` - Package name (e.g., tta-dev-primitives, infrastructure)
- `related::` - KB page links using `[[Page Name]]` syntax

### For `#user-todo` (Learning/Documentation)

```markdown
- TODO Create guide #user-todo
  type:: learning
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[TTA.dev/Guides/GuideName]]
  time-estimate:: 30 minutes
```

**Required properties:**
- `type::` - One of: learning, milestone
- `audience::` - One of: new-users, intermediate-users, advanced-users, developers, ai-developers, expert-users, all-users
- `difficulty::` - One of: beginner, intermediate, advanced, expert
- `related::` - KB page links

---

## Local Validation

Before pushing changes, validate TODOs locally:

```bash
# Run validation
uv run python scripts/validate-todos.py

# Expected output (passing):
📋 Scanning 2 journal files...

================================================================================
📊 TODO VALIDATION RESULTS
================================================================================

✅ Total TODOs found: 116
✅ Compliant TODOs: 116
❌ Non-compliant TODOs: 0
📈 Compliance rate: 100.0%

================================================================================
```

**If validation fails:**
```bash
# See detailed issues
uv run python scripts/validate-todos.py

# Fix issues in journal files
# Re-run validation until 100% compliance
```

---

## Common Validation Errors

### 1. Missing Category Tag

❌ **Error:**
```markdown
- TODO Fix bug in router
```

✅ **Fix:**
```markdown
- TODO Fix bug in router #dev-todo
  type:: bug-fix
  priority:: high
  package:: tta-dev-primitives
```

### 2. Missing Required Properties

❌ **Error:**
```markdown
- TODO Add tests #dev-todo
```

✅ **Fix:**
```markdown
- TODO Add tests #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Testing]]
```

### 3. Wrong Property Values

❌ **Error:**
```markdown
- TODO Implement feature #dev-todo
  type:: feature  # Invalid type
  priority:: urgent  # Invalid priority
```

✅ **Fix:**
```markdown
- TODO Implement feature #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
```

### 4. Missing KB Page Reference

❌ **Error:**
```markdown
- TODO Create guide #user-todo
  type:: learning
  audience:: new-users
  difficulty:: beginner
  # Missing related:: property
```

✅ **Fix:**
```markdown
- TODO Create guide #user-todo
  type:: learning
  audience:: new-users
  difficulty:: beginner
  related:: [[TTA.dev/Guides/GuideName]]
```

---

## Workflow Configuration

**File**: `.github/workflows/validate-todos.yml`

**Key settings:**
- **Python version**: 3.12
- **Package manager**: uv
- **Validation script**: `scripts/validate-todos.py`
- **Artifact retention**: 30 days

**Permissions required:**
- `contents: read` - Read repository contents
- `pull-requests: write` - Post PR comments

---

## Troubleshooting

### Workflow Fails with "uv: command not found"

**Cause**: uv installation failed or PATH not set correctly

**Fix**: Check workflow logs for uv installation errors. The workflow should:
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Add to PATH: `echo "$HOME/.cargo/bin" >> $GITHUB_PATH`

### Workflow Fails with "Module not found"

**Cause**: Dependencies not installed

**Fix**: Ensure `uv sync --all-extras` runs successfully before validation

### Validation Passes Locally but Fails in CI

**Cause**: Different journal files or KB pages between local and remote

**Fix**:
1. Ensure all changes are committed and pushed
2. Check that KB page files exist in `logseq/pages/`
3. Verify file naming: Logseq uses `___` for `/` in page names

---

## Maintenance

### Updating Validation Rules

1. Modify `scripts/validate-todos.py`
2. Test locally: `uv run python scripts/validate-todos.py`
3. Commit and push changes
4. Workflow will use updated script on next run

### Disabling Validation (Not Recommended)

To temporarily disable validation:

1. Add `continue-on-error: true` to validation step
2. Or comment out the workflow file

**Note**: This is NOT recommended as it defeats the purpose of enforcing quality standards.

---

## Metrics

**Current Status** (as of 2025-10-31):
- **Total TODOs**: 116
- **Compliant TODOs**: 116
- **Compliance Rate**: 100.0%
- **Issues**: 0
- **Missing KB Pages**: 0

**Historical Compliance:**
- 2025-10-30: 31.5% (35/111 TODOs)
- 2025-10-31: 100.0% (116/116 TODOs) ✅

**Improvement**: +68.5% compliance in 1 day

---

## Related Documentation

- [TODO Management System](../../logseq/pages/TODO%20Management%20System.md) - Complete TODO standards
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines
- [README.md](../../README.md) - Project overview

---

**Last Updated**: 2025-10-31
**Maintained By**: TTA.dev Team
**Status**: ✅ Active and Enforced



---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Ci-cd/Todo_validation_ci]]
